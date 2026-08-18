#!/usr/bin/env python3
"""Serve the generated site and rebuild it when source files change."""

from __future__ import annotations

import argparse
import errno
import os
import shutil
import subprocess
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


RELOAD_SCRIPT = """
<script>
(() => {
  const events = new EventSource('/_dev/events');
  events.onmessage = (event) => {
    if (event.data === 'reload') window.location.reload();
  };
})();
</script>
""".strip()


def source_files(root: Path) -> list[Path]:
    watched_roots = [
        root / "config",
        root / "content",
        root / "frontend",
        # Le HTML des pages et des composants vit ici : sans cette ligne, la
        # modification d'un composant ne déclencherait aucune régénération.
        root / "tools" / "rendu",
    ]
    files = [
        root / "tools" / "build-site.py",
        root / "tools" / "content_data.py",
    ]
    for watched_root in watched_roots:
        files.extend(
            path
            for path in watched_root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
    return files


def snapshot(root: Path) -> dict[Path, tuple[int, int]]:
    result = {}
    for path in source_files(root):
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue
        result[path] = (stat.st_mtime_ns, stat.st_size)
    return result


def run_build(root: Path) -> bool:
    print("\n[dev] Régénération du site…", flush=True)
    result = subprocess.run(
        [sys.executable, str(root / "tools" / "build-site.py"), "--root", str(root)],
        cwd=root,
        check=False,
    )
    if result.returncode:
        print("[dev] Échec de la génération. La dernière version valide reste servie.", flush=True)
        return False
    print("[dev] Site régénéré.", flush=True)
    return True


def needs_initial_build(root: Path) -> bool:
    index = root / "dist" / "index.html"
    if not index.is_file():
        return True
    built_at = index.stat().st_mtime_ns
    return any(path.stat().st_mtime_ns > built_at for path in source_files(root))


def copy_frontend_assets(root: Path, changed: set[Path]) -> bool:
    assets_root = root / "frontend" / "assets"
    if not changed or not all(path.is_file() and path.is_relative_to(assets_root) for path in changed):
        return False
    for path in changed:
        destination = root / "dist" / "assets" / path.relative_to(assets_root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        print(f"[dev] Mis à jour : {path.relative_to(root)}", flush=True)
    return True


class DevServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], handler, directory: Path):
        super().__init__(address, handler)
        self.directory = directory
        self.reload_version = 0
        self.reload_condition = threading.Condition()

    def notify_reload(self) -> None:
        with self.reload_condition:
            self.reload_version += 1
            self.reload_condition.notify_all()


class DevHandler(SimpleHTTPRequestHandler):
    server: DevServer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(kwargs.pop("directory")), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def guess_type(self, path: str) -> str:
        if path.endswith((".yml", ".yaml")):
            return "text/yaml"
        return super().guess_type(path)

    def do_GET(self) -> None:
        if urlsplit(self.path).path == "/_dev/events":
            self.serve_events()
            return
        requested = Path(self.translate_path(urlsplit(self.path).path))
        if requested.is_dir():
            requested /= "index.html"
        if requested.is_file() and requested.suffix.lower() == ".html":
            self.serve_html(requested)
            return
        super().do_GET()

    def serve_html(self, path: Path) -> None:
        content = path.read_text(encoding="utf-8")
        content = content.replace("</body>", f"  {RELOAD_SCRIPT}\n</body>")
        payload = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def serve_events(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        version = self.server.reload_version
        try:
            while True:
                with self.server.reload_condition:
                    self.server.reload_condition.wait_for(
                        lambda: self.server.reload_version != version,
                        timeout=15,
                    )
                    changed = self.server.reload_version != version
                    version = self.server.reload_version
                message = b"data: reload\n\n" if changed else b": keep-alive\n\n"
                self.wfile.write(message)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            return


def watch_sources(root: Path, server: DevServer, stop: threading.Event) -> None:
    previous = snapshot(root)
    while not stop.wait(0.6):
        current = snapshot(root)
        changed = {
            path
            for path in set(previous) | set(current)
            if previous.get(path) != current.get(path)
        }
        previous = current
        if not changed:
            continue
        if copy_frontend_assets(root, changed) or run_build(root):
            server.notify_reload()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    os.chdir(root)
    if needs_initial_build(root) and not run_build(root):
        raise SystemExit(1)

    handler = lambda *handler_args, **handler_kwargs: DevHandler(  # noqa: E731
        *handler_args,
        directory=root / "dist",
        **handler_kwargs,
    )
    try:
        server = DevServer((args.host, args.port), handler, root / "dist")
    except OSError as error:
        if error.errno == errno.EADDRINUSE:
            print(
                f"[dev] Le port {args.port} est déjà utilisé. "
                f"Essayez : make dev DEV_PORT={args.port + 1}",
                flush=True,
            )
            raise SystemExit(2) from None
        raise
    stop = threading.Event()
    watcher = threading.Thread(target=watch_sources, args=(root, server, stop), daemon=True)
    watcher.start()
    print(f"[dev] Site disponible sur http://{args.host}:{args.port}/", flush=True)
    print("[dev] Les modifications sont surveillées. Ctrl+C pour arrêter.", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()


if __name__ == "__main__":
    main()
