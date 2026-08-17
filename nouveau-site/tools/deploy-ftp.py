#!/usr/bin/env python3
"""Deploy the generated public site over passive FTP.

Deux cibles : « free », l'hébergement du client, et « ovh », l'aperçu montré avant
la mise en ligne. Chaque cible lit ses propres variables d'environnement.
"""

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

# Free n'expose qu'un seul hôte FTP ; chez OVH il dépend du cluster attribué au
# compte, il n'y a donc pas de valeur par défaut raisonnable. La cible « ovh-admin »
# publie l'administration, qui vit sur son propre sous-domaine.
DEFAULT_HOSTS = {"free": "ftpperso.free.fr", "ovh": None, "ovh-admin": None}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--target", choices=sorted(DEFAULT_HOSTS), default="free")
    parser.add_argument(
        "--tls",
        action="store_true",
        help="Chiffre la connexion (FTPS explicite). Accepté par OVH, pas par Free.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def connection_settings(target: str) -> dict[str, str]:
    """Lit les variables d'environnement propres à la cible, par exemple OVH_FTP_USER."""

    prefix = target.upper().replace("-", "_")

    def read(name: str) -> str | None:
        return os.environ.get(f"{prefix}_FTP_{name}") or None

    host = read("HOST") or DEFAULT_HOSTS[target]
    user = read("USER")
    password = read("PASSWORD")
    if not host:
        raise SystemExit(f"{prefix}_FTP_HOST est obligatoire pour la cible « {target} »")
    if not user or not password:
        raise SystemExit(f"{prefix}_FTP_USER et {prefix}_FTP_PASSWORD sont obligatoires")
    return {"host": host, "user": user, "password": password, "base": read("PATH") or "/"}


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

    settings = connection_settings(args.target)
    base = settings["base"]
    client = ftplib.FTP_TLS if args.tls else ftplib.FTP

    with client(settings["host"], timeout=45) as ftp:
        ftp.login(user=settings["user"], passwd=settings["password"])
        if args.tls:
            ftp.prot_p()
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

    print(
        f"Déploiement {args.target} terminé : "
        f"{len(changed)} fichier(s) envoyé(s), {len(stale)} retiré(s)."
    )


if __name__ == "__main__":
    main()
