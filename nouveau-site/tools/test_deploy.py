#!/usr/bin/env python3

import ftplib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("deploy-free.py")
SPEC = importlib.util.spec_from_file_location("deploy_free", MODULE_PATH)
deploy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deploy)


class FakeFTP:
    def __init__(self):
        self.files = {}
        self.directories = {"/"}

    def mkd(self, path):
        if path in self.directories:
            raise ftplib.error_perm("550 already exists")
        self.directories.add(path)

    def delete(self, path):
        if path not in self.files:
            raise ftplib.error_perm("550 not found")
        del self.files[path]

    def rename(self, source, destination):
        if source not in self.files:
            raise ftplib.error_perm("550 not found")
        self.files[destination] = self.files.pop(source)

    def storbinary(self, command, source, blocksize=8192):
        del blocksize
        self.files[command.removeprefix("STOR ")] = source.read()

    def retrbinary(self, command, callback):
        path = command.removeprefix("RETR ")
        if path not in self.files:
            raise ftplib.error_perm("550 not found")
        callback(self.files[path])


class DeployTest(unittest.TestCase):
    def test_local_files_exclude_online_admin(self):
        with tempfile.TemporaryDirectory() as directory:
            dist = Path(directory)
            (dist / "admin").mkdir()
            (dist / "admin" / "index.html").write_text("admin", encoding="utf-8")
            (dist / "index.html").write_text("site", encoding="utf-8")
            self.assertEqual(["index.html"], list(deploy.local_files(dist)))

    def test_publication_order_puts_pages_after_assets(self):
        paths = ["index.html", "assets/site.css", "robots.txt", "assets/cover.webp"]
        self.assertEqual(
            ["assets/cover.webp", "assets/site.css", "index.html", "robots.txt"],
            sorted(paths, key=deploy.publication_order),
        )

    def test_atomic_upload_replaces_previous_file(self):
        ftp = FakeFTP()
        ftp.files["/index.html"] = b"old"
        deploy.upload_atomic(ftp, io.BytesIO(b"new"), "/index.html")
        self.assertEqual(b"new", ftp.files["/index.html"])
        self.assertNotIn("/index.html.previous", ftp.files)
        self.assertNotIn("/index.html.uploading", ftp.files)

    def test_remote_manifest_is_read(self):
        ftp = FakeFTP()
        ftp.files["/.chantdorties-deploy.json"] = json.dumps(
            {"version": 1, "files": {"index.html": "abc"}}
        ).encode("utf-8")
        self.assertEqual(
            {"index.html": "abc"},
            deploy.read_remote_manifest(ftp, "/.chantdorties-deploy.json"),
        )

    def test_remote_base_path_is_normalized(self):
        self.assertEqual("assets/site.css", deploy.remote_path("/", "assets/site.css"))
        self.assertEqual("public/assets/site.css", deploy.remote_path("/public/", "assets/site.css"))


if __name__ == "__main__":
    unittest.main()
