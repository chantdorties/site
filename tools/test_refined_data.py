#!/usr/bin/env python3

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "migration" / "front-data"


def load_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class RefinedDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.books = load_json("livres.json")
        cls.people = load_json("personnes.json")
        cls.collections = load_json("collections.json")
        cls.pages = load_json("pages.json")
        cls.catalogue = load_json("catalogue.json")
        cls.books_by_slug = {book["slug"]: book for book in cls.books}
        cls.people_by_slug = {person["slug"]: person for person in cls.people}

    def test_expected_catalogue_size(self):
        self.assertEqual(64, len(self.books))
        self.assertEqual(6, len(self.collections))
        self.assertEqual(81, len(self.people))
        self.assertEqual(12, len(self.pages))
        self.assertEqual(2, self.catalogue["versionSchema"])

    def test_every_book_has_one_author(self):
        for book in self.books:
            self.assertEqual(1, len(book["auteurs"]), book["slug"])

    def test_special_contributor_relations(self):
        aquarium = self.books_by_slug["debout-dans-l-aquarium"]
        self.assertEqual(["eric-lemaire"], aquarium["auteurs"])
        self.assertEqual(["eric-lemaire"], aquarium["illustrateurs"])

        memoires = self.books_by_slug["memoires-d-un-nouveau-ne"]
        self.assertEqual(
            ["marion-claeys", "catherine-senaffe"],
            memoires["illustrateurs"],
        )

        marius = self.books_by_slug["marius-gardebois"]
        self.assertEqual([], marius["illustrateurs"])
        self.assertEqual(["claire-auzias"], marius["prefaciers"])

    def test_no_extraction_fragments_as_people(self):
        forbidden = re.compile(r"l['’]auteu|roman suivi|album de|et moi", re.I)
        for person in self.people:
            self.assertIsNone(forbidden.search(person["nom"]), person["nom"])

    def test_relations_point_to_existing_records(self):
        people_slugs = set(self.people_by_slug)
        book_slugs = set(self.books_by_slug)
        for book in self.books:
            for role in ("auteurs", "illustrateurs", "prefaciers"):
                self.assertLessEqual(set(book[role]), people_slugs, book["slug"])
        for person in self.people:
            for role_books in person["livres"].values():
                self.assertLessEqual(set(role_books), book_slugs, person["slug"])

    def test_descriptions_have_no_leading_metadata(self):
        metadata = re.compile(r"^(ISSN|Format|A partir|À partir)", re.I)
        for book in self.books:
            if book["description"]:
                self.assertIsNone(metadata.search(book["description"]), book["slug"])

    def test_all_referenced_media_exist(self):
        media = []
        for book in self.books:
            media.extend([book["couverture"], *book["illustrations"], *book["extraits"]])
        for person in self.people:
            media.extend(person["images"])
        for page in self.pages:
            media.extend([*page["images"], *page["documents"]])
        for path in filter(None, media):
            self.assertTrue(path.startswith("migration/front-assets/"), path)
            self.assertTrue((ROOT / path).is_file(), path)

    def test_front_folders_contain_only_expected_files(self):
        self.assertEqual(
            {"catalogue.json", "collections.json", "livres.json", "pages.json", "personnes.json"},
            {path.name for path in DATA.iterdir() if path.is_file()},
        )
        referenced = {
            path
            for book in self.books
            for path in [book["couverture"], *book["illustrations"], *book["extraits"]]
            if path
        }
        referenced.update(
            path
            for person in self.people
            for path in person["images"]
        )
        referenced.update(
            path
            for page in self.pages
            for path in [*page["images"], *page["documents"]]
        )
        assets = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "migration" / "front-assets").rglob("*")
            if path.is_file()
        }
        self.assertEqual(referenced, assets)

    def test_editorial_pages_are_clean(self):
        self.assertNotIn("auteurs.html", {page["source"]["anciennePage"] for page in self.pages})
        self.assertNotIn("illustrateurs.html", {page["source"]["anciennePage"] for page in self.pages})
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
