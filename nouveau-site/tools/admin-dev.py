#!/usr/bin/env python3
"""Start the local content editor and the live-reloading site together."""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--proxy-port", type=int, default=8082)
    return parser.parse_args()


def stop(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    if not shutil.which("npx"):
        raise SystemExit("npx est nécessaire pour démarrer l’administration locale")

    repository_root = Path(
        subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=root,
            text=True,
        ).strip()
    )

    commands = [
        (["npx", "--yes", "decap-server@3.10.0"], {
            **os.environ,
            "PORT": str(args.proxy_port),
            "BIND_HOST": "127.0.0.1",
            "ORIGIN": f"http://127.0.0.1:{args.port}",
        }, repository_root),
        ([
            sys.executable,
            str(root / "tools" / "dev-server.py"),
            "--root",
            str(root),
            "--port",
            str(args.port),
        ], None, root),
    ]
    processes = [
        subprocess.Popen(command, cwd=cwd, env=environment, start_new_session=True)
        for command, environment, cwd in commands
    ]
    print(f"[admin] Administration : http://127.0.0.1:{args.port}/admin/", flush=True)
    try:
        while all(process.poll() is None for process in processes):
            time.sleep(0.5)
        failed = next((process.returncode for process in processes if process.returncode), 0)
        raise SystemExit(failed)
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes:
            stop(process)


if __name__ == "__main__":
    main()
