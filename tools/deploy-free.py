#!/usr/bin/env python3
"""Deploy the generated public site to Free over passive FTP."""

from __future__ import annotations

import argparse
import ftplib
import hashlib
import io
import json
import os
import posixpath
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


MANIFEST_NAME = ".chantdorties-deploy.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_files(dist: Path) -> dict[str, Path]:
    files = {}
    for path in sorted(dist.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(dist)
        if relative.parts[0] == "admin":
            continue
        files[relative.as_posix()] = path
    return files


def remote_path(base: str, relative: str) -> str:
    clean_base = base.strip("/")
    return posixpath.join(clean_base, relative)


def ensure_remote_directory(ftp: ftplib.FTP, path: str) -> None:
    current = ""
    for part in PurePosixPath(path).parent.parts:
        if part == "/":
            current = "/"
            continue
        current = posixpath.join(current, part)
        try:
            ftp.mkd(current)
        except ftplib.error_perm as error:
            if not str(error).startswith("550"):
                raise


def delete_if_present(ftp: ftplib.FTP, path: str) -> None:
    try:
        ftp.delete(path)
    except ftplib.error_perm as error:
        if not str(error).startswith("550"):
            raise


def upload_atomic(ftp: ftplib.FTP, local: Path | io.BytesIO, destination: str) -> None:
    ensure_remote_directory(ftp, destination)
    temporary = f"{destination}.uploading"
    previous = f"{destination}.previous"
    delete_if_present(ftp, temporary)
    if isinstance(local, Path):
        with local.open("rb") as source:
            ftp.storbinary(f"STOR {temporary}", source, blocksize=256 * 1024)
    else:
        local.seek(0)
        ftp.storbinary(f"STOR {temporary}", local, blocksize=256 * 1024)

    delete_if_present(ftp, previous)
    had_previous = False
    try:
        ftp.rename(destination, previous)
        had_previous = True
    except ftplib.error_perm as error:
        if not str(error).startswith("550"):
            raise
    try:
        ftp.rename(temporary, destination)
    except Exception:
        if had_previous:
            ftp.rename(previous, destination)
        raise
    if had_previous:
        delete_if_present(ftp, previous)


def read_remote_manifest(ftp: ftplib.FTP, path: str) -> dict[str, str]:
    payload = io.BytesIO()
    try:
        ftp.retrbinary(f"RETR {path}", payload.write)
    except ftplib.error_perm as error:
        if str(error).startswith("550"):
            return {}
        raise
    try:
        data = json.loads(payload.getvalue().decode("utf-8"))
        return data.get("files", {}) if isinstance(data, dict) else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}


def publication_order(relative: str) -> tuple[int, str]:
    suffix = PurePosixPath(relative).suffix.lower()
    return (1 if suffix in {".html", ".xml", ".txt"} or relative == ".htaccess" else 0, relative)


def main() -> None:
    args = parse_args()
    dist = args.dist.resolve()
    if not (dist / "index.html").is_file():
        raise SystemExit(f"Site généré introuvable : {dist}")

    files = local_files(dist)
    hashes = {relative: sha256(path) for relative, path in files.items()}
    if args.dry_run:
        print(f"Déploiement simulé : {len(files)} fichiers publics, administration exclue.")
        return

    host = os.environ.get("FREE_FTP_HOST") or "ftpperso.free.fr"
    user = os.environ.get("FREE_FTP_USER")
    password = os.environ.get("FREE_FTP_PASSWORD")
    base = os.environ.get("FREE_FTP_PATH") or "/"
    if not user or not password:
        raise SystemExit("FREE_FTP_USER et FREE_FTP_PASSWORD sont obligatoires")

    with ftplib.FTP(host, timeout=45) as ftp:
        ftp.login(user=user, passwd=password)
        ftp.set_pasv(True)
        manifest_path = remote_path(base, MANIFEST_NAME)
        previous = read_remote_manifest(ftp, manifest_path)
        changed = [relative for relative in files if previous.get(relative) != hashes[relative]]
        stale = sorted(set(previous) - set(files))

        for relative in sorted(changed, key=publication_order):
            upload_atomic(ftp, files[relative], remote_path(base, relative))
        for relative in stale:
            if ".." not in PurePosixPath(relative).parts:
                delete_if_present(ftp, remote_path(base, relative))

        manifest = {
            "version": 1,
            "deployedAt": datetime.now(timezone.utc).isoformat(),
            "files": hashes,
        }
        payload = io.BytesIO((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
        upload_atomic(ftp, payload, manifest_path)
        ftp.quit()

    print(f"Déploiement terminé : {len(changed)} fichier(s) envoyé(s), {len(stale)} retiré(s).")


if __name__ == "__main__":
    main()
