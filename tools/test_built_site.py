#!/usr/bin/env python3

import json
import shutil
import subprocess
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
PDFINFO_BINARY = "/usr/bin/pdfinfo" if Path("/usr/bin/pdfinfo").is_file() else shutil.which("pdfinfo")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def local_target(value):
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or value.startswith(("mailto:", "tel:", "#")):
        return None
    path = parsed.path
    if not path:
        return None
    target = DIST / path.lstrip("/")
    if path.endswith("/"):
        target /= "index.html"
    return target


class BuiltSiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = load_json(ROOT / "migration" / "rapports" / "site-build.json")
        cls.html_files = list(DIST.rglob("*.html"))
        cls.books = load_json(DIST / "data" / "livres.json")
        cls.people = load_json(DIST / "data" / "personnes.json")
        cls.collections = load_json(DIST / "data" / "collections.json")

    def test_expected_pages_and_public_data(self):
        self.assertEqual(164, len(self.html_files))
        self.assertEqual(64, len(self.books))
        self.assertEqual(81, len(self.people))
        self.assertEqual(6, len(self.collections))
        self.assertEqual(
            {"livres.json", "personnes.json", "collections.json"},
            {path.name for path in (DIST / "data").iterdir()},
        )

    def test_generated_record_pages(self):
        self.assertEqual(64, len(list((DIST / "livres").glob("*/index.html"))))
        self.assertEqual(81, len(list((DIST / "personnes").glob("*/index.html"))))
        self.assertEqual(6, len(list((DIST / "collections").glob("*/index.html"))))

    def test_draft_pages_are_not_published(self):
        for slug in ("commandes", "mentions-legales", "soutien", "offres-speciales"):
            self.assertFalse((DIST / slug).exists(), slug)
            self.assertNotIn(f"/{slug}/", (DIST / "sitemap.xml").read_text(encoding="utf-8"))

    def test_every_html_page_has_shared_chrome(self):
        for path in self.html_files:
            soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
            self.assertIsNotNone(soup.select_one("header.site-header"), path)
            self.assertIsNotNone(soup.select_one("footer.site-footer"), path)
            self.assertIsNotNone(soup.select_one("a.skip-link"), path)
            self.assertEqual(1, len(soup.select("main#contenu")), path)

    def test_all_local_html_references_resolve(self):
        missing = []
        for path in self.html_files:
            soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
            for tag, attribute in (("a", "href"), ("img", "src"), ("script", "src"), ("link", "href")):
                for element in soup.find_all(tag):
                    value = element.get(attribute)
                    if not value:
                        continue
                    target = local_target(value)
                    if target is not None and not target.is_file():
                        missing.append((path.relative_to(DIST).as_posix(), value))
            for image in soup.find_all("img", srcset=True):
                for candidate in image["srcset"].split(","):
                    value = candidate.strip().split()[0]
                    target = local_target(value)
                    if target is not None and not target.is_file():
                        missing.append((path.relative_to(DIST).as_posix(), value))
        self.assertEqual([], missing)

    def test_public_json_is_trimmed_and_safe(self):
        for book in self.books:
            self.assertNotIn("paiement", book)
            self.assertNotIn("source", book)
            self.assertNotIn("anomalies", book)
            self.assertTrue(book["couverture"].startswith("/assets/media/covers/"))
        for person in self.people:
            self.assertNotIn("biographie", person)
            self.assertNotIn("source", person)

    def test_output_contains_only_optimized_raster_images(self):
        raster_suffixes = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}
        unexpected = [path for path in DIST.rglob("*") if path.suffix.lower() in raster_suffixes]
        self.assertEqual([], unexpected)
        self.assertGreater(len(list(DIST.rglob("*.webp"))), 300)

    def test_every_published_pdf_is_readable(self):
        for path in DIST.rglob("*.pdf"):
            result = subprocess.run(
                [PDFINFO_BINARY, str(path)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
            )
            self.assertEqual(0, result.returncode, path)

    def test_news_page_uses_the_focused_facebook_callout(self):
        soup = BeautifulSoup((DIST / "actualites" / "index.html").read_text(encoding="utf-8"), "html.parser")
        self.assertIsNotNone(soup.select_one(".news-callout"))
        self.assertIn("Nos prochaines rencontres", soup.get_text(" ", strip=True))
        self.assertNotIn("En images", soup.get_text(" ", strip=True))
        self.assertEqual([], soup.select("main img"))

    def test_collection_index_has_visual_previews(self):
        soup = BeautifulSoup((DIST / "collections" / "index.html").read_text(encoding="utf-8"), "html.parser")
        tiles = soup.select(".collection-showcase__item")
        self.assertEqual(6, len(tiles))
        for tile in tiles:
            self.assertIsNotNone(tile.select_one(".collection-showcase__link"))
            self.assertGreaterEqual(len(tile.select(".collection-showcase__covers img")), 1)
            self.assertLessEqual(len(tile.select(".collection-showcase__covers img")), 3)

    def test_no_paypal_or_draft_warning_in_production(self):
        for path in self.html_files:
            content = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("paypal", content, path)
            self.assertNotIn("prévisualisation :", content, path)

    def test_redirects_cover_every_old_book_page(self):
        redirects = (DIST / ".htaccess").read_text(encoding="utf-8")
        source_books = load_json(ROOT / "migration" / "front-data" / "livres.json")
        for book in source_books:
            source = book["source"]["anciennePage"]
            self.assertIn(f'"/{source}" "/livres/{book["slug"]}/"', redirects)

    def test_frontend_javascript_syntax(self):
        for path in (DIST / "assets" / "js").glob("*.js"):
            result = subprocess.run(
                ["node", "--check", str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
