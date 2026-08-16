#!/usr/bin/env python3

import json
import re
import unittest
from pathlib import Path

from tools.content_data import load_content, valid_isbn


ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"


def referenced_media(raw):
    paths = set()
    for book in raw["books"]:
        paths.update(filter(None, [book.get("couverture"), *book.get("illustrations", []), *book.get("extraits", [])]))
    for person in raw["people"]:
        paths.update(filter(None, [person.get("imagePrincipale"), *person.get("images", [])]))
    for page in raw["pages"]:
        paths.update(filter(None, [*page.get("images", []), *page.get("documents", [])]))
        paths.update(
            link.get("href")
            for link in page.get("liens", [])
            if link.get("type") == "document" and link.get("href")
        )
    for item in raw["news"]:
        paths.update(filter(None, [item.get("image"), item.get("document")]))
    return paths


class ContentDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_content(ROOT, include_drafts=True)
        cls.raw = cls.bundle["raw"]
        cls.books = cls.raw["books"]
        cls.people = cls.raw["people"]
        cls.collections = cls.raw["collections"]
        cls.pages = cls.raw["pages"]
        cls.books_by_slug = {book["slug"]: book for book in cls.books}

    def test_content_schema_and_required_records(self):
        schema = json.loads((CONTENT / "schema.json").read_text(encoding="utf-8"))
        self.assertEqual(2, schema["version"])
        self.assertGreater(len(self.books), 0)
        self.assertGreater(len(self.people), 0)
        self.assertGreater(len(self.collections), 0)
        self.assertLessEqual({"accueil", "actualites", "mentions-legales"}, {page["slug"] for page in self.pages})

    def test_records_use_one_json_file_each(self):
        for folder, records in (
            ("livres", self.books),
            ("personnes", self.people),
            ("collections", self.collections),
            ("pages", self.pages),
            ("actualites", self.raw["news"]),
        ):
            files = {path.stem for path in (CONTENT / folder).glob("*.json")}
            self.assertEqual({record["slug"] for record in records}, files)

    def test_special_contributor_relations(self):
        aquarium = self.books_by_slug["debout-dans-l-aquarium"]
        self.assertEqual(["eric-lemaire"], aquarium["auteurs"])
        self.assertEqual(["eric-lemaire"], aquarium["illustrateurs"])

        memoires = self.books_by_slug["memoires-d-un-nouveau-ne"]
        self.assertEqual(["marion-claeys", "catherine-senaffe"], memoires["illustrateurs"])

        marius = self.books_by_slug["marius-gardebois"]
        self.assertEqual([], marius["illustrateurs"])
        self.assertEqual(["claire-auzias"], marius["prefaciers"])

    def test_no_extraction_fragments_as_people(self):
        forbidden = re.compile(r"l['’]auteu|roman suivi|album de|et moi", re.I)
        for person in self.people:
            self.assertIsNone(forbidden.search(person["nom"]), person["nom"])

    def test_source_json_has_no_migration_only_fields(self):
        forbidden = {"aVerifier", "anomalies", "isbnValide", "paiement", "source"}
        for kind in ("books", "people", "collections", "pages", "news"):
            for record in self.raw[kind]:
                self.assertEqual(set(), forbidden & set(record), f"{kind}/{record['slug']}")

    def test_descriptions_have_no_leading_metadata(self):
        metadata = re.compile(r"^(ISSN|Format|A partir|À partir)", re.I)
        for book in self.books:
            if book.get("description"):
                self.assertIsNone(metadata.search(book["description"]), book["slug"])

    def test_isbn_values_are_valid(self):
        for book in self.books:
            self.assertTrue(valid_isbn(book.get("isbn")), book["slug"])

    def test_every_available_book_has_a_paypal_button(self):
        for book in self.books:
            button_id = book.get("paypalHostedButtonId")
            if book["disponible"]:
                self.assertRegex(button_id or "", r"^[A-Z0-9]{13}$", book["slug"])

    def test_all_and_only_referenced_media_are_kept(self):
        referenced = referenced_media(self.raw)
        assets = {
            path.relative_to(ROOT).as_posix()
            for path in (CONTENT / "media").rglob("*")
            if path.is_file()
        }
        self.assertEqual(referenced, assets)
        for path in referenced:
            self.assertTrue(path.startswith("content/media/"), path)
            self.assertTrue((ROOT / path).is_file(), path)

    def test_media_are_small_enough_for_git_and_builds(self):
        too_large = [
            path.relative_to(ROOT).as_posix()
            for path in (CONTENT / "media").rglob("*")
            if path.is_file() and path.stat().st_size > 20 * 1024 * 1024
        ]
        self.assertEqual([], too_large)

    def test_editorial_pages_are_clean(self):
        forbidden = re.compile(
            r"Auteurs Illustrateurs Graines d'orties|octets_nuls|BEGIN PKCS7",
            re.I,
        )
        for page in self.pages:
            self.assertTrue(page["sections"], page["slug"])
            content = " ".join(section["contenu"] for section in page["sections"])
            self.assertGreater(len(content), 40, page["slug"])
            self.assertIsNone(forbidden.search(content), page["slug"])


if __name__ == "__main__":
    unittest.main()
