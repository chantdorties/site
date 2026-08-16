#!/usr/bin/env python3

import json
import shutil
import subprocess
import unittest
from pathlib import Path
from urllib.parse import urlsplit

import yaml
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
        cls.report = load_json(ROOT / "reports" / "site-build.json")
        cls.html_files = list(DIST.rglob("*.html"))
        cls.public_html_files = [path for path in cls.html_files if "admin" not in path.relative_to(DIST).parts]
        cls.books = load_json(DIST / "data" / "livres.json")
        cls.people = load_json(DIST / "data" / "personnes.json")
        cls.collections = load_json(DIST / "data" / "collections.json")

    def test_report_and_public_data_match_output(self):
        self.assertEqual(len(self.html_files), self.report["pagesHtml"])
        self.assertEqual(len(self.books), self.report["livres"])
        self.assertEqual(len(self.people), self.report["personnes"])
        self.assertEqual(len(self.collections), self.report["collections"])
        self.assertEqual(
            {"livres.json", "personnes.json", "collections.json"},
            {path.name for path in (DIST / "data").iterdir()},
        )

    def test_generated_record_pages(self):
        self.assertEqual(len(self.books), len(list((DIST / "livres").glob("*/index.html"))))
        self.assertEqual(len(self.people), len(list((DIST / "personnes").glob("*/index.html"))))
        self.assertEqual(len(self.collections), len(list((DIST / "collections").glob("*/index.html"))))

    def test_draft_pages_are_not_published(self):
        source_pages = [
            load_json(path) for path in (ROOT / "content" / "pages").glob("*.json")
        ]
        sitemap = (DIST / "sitemap.xml").read_text(encoding="utf-8")
        for page in source_pages:
            if page["statut"] != "brouillon":
                continue
            self.assertFalse((DIST / page["slug"]).exists(), page["slug"])
            self.assertNotIn(f"/{page['slug']}/", sitemap)

    def test_every_public_html_page_has_shared_chrome(self):
        for path in self.public_html_files:
            soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
            self.assertIsNotNone(soup.select_one("header.site-header"), path)
            self.assertIsNotNone(soup.select_one("footer.site-footer"), path)
            self.assertEqual(
                "/assets/images/chantdorties-logo.webp",
                soup.select_one("header.site-header .site-logo")["src"],
                path,
            )
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
        self.assertGreater(len(list(DIST.rglob("*.webp"))), 0)

    def test_every_published_pdf_is_readable(self):
        if not PDFINFO_BINARY:
            self.skipTest("pdfinfo absent")
        for path in DIST.rglob("*.pdf"):
            result = subprocess.run(
                [PDFINFO_BINARY, str(path)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
            )
            self.assertEqual(0, result.returncode, path)

    def test_news_page_and_optional_entries(self):
        soup = BeautifulSoup((DIST / "actualites" / "index.html").read_text(encoding="utf-8"), "html.parser")
        self.assertIsNotNone(soup.select_one(".news-callout"))
        self.assertIn("Nos prochaines rencontres", soup.get_text(" ", strip=True))
        self.assertNotIn("En images", soup.get_text(" ", strip=True))
        self.assertEqual(self.report["actualites"], len(soup.select(".news-card")))

    def test_collection_index_has_visual_previews(self):
        soup = BeautifulSoup((DIST / "collections" / "index.html").read_text(encoding="utf-8"), "html.parser")
        tiles = soup.select(".collection-showcase__item")
        self.assertEqual(len(self.collections), len(tiles))
        for tile in tiles:
            self.assertIsNotNone(tile.select_one(".collection-showcase__link"))
            self.assertGreaterEqual(len(tile.select(".collection-showcase__covers img")), 1)
            self.assertLessEqual(len(tile.select(".collection-showcase__covers img")), 3)

    def test_admin_is_present_but_not_indexed(self):
        index = DIST / "admin" / "index.html"
        config_path = DIST / "admin" / "config.yml"
        soup = BeautifulSoup(index.read_text(encoding="utf-8"), "html.parser")
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        self.assertEqual("noindex, nofollow", soup.select_one('meta[name="robots"]')["content"])
        self.assertEqual("github", config["backend"]["name"])
        self.assertEqual("chantdorties/site", config["backend"]["repo"])
        self.assertEqual("http://127.0.0.1:8082/api/v1", config["local_backend"]["url"])
        self.assertNotIn("/admin/", (DIST / "sitemap.xml").read_text(encoding="utf-8"))

    def test_no_draft_warning_in_production(self):
        for path in self.public_html_files:
            content = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("prévisualisation :", content, path)

    def test_available_books_use_the_original_paypal_buttons(self):
        source_books = [load_json(path) for path in (ROOT / "content" / "livres").glob("*.json")]
        for book in source_books:
            path = DIST / "livres" / book["slug"] / "index.html"
            soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
            form = soup.select_one('form.paypal-form[action="https://www.paypal.com/cgi-bin/webscr"]')
            if book["disponible"]:
                self.assertIsNotNone(form, book["slug"])
                self.assertEqual("_s-xclick", form.select_one('input[name="cmd"]')["value"])
                self.assertEqual(
                    book["paypalHostedButtonId"],
                    form.select_one('input[name="hosted_button_id"]')["value"],
                )
            else:
                self.assertIsNone(form, book["slug"])

    def test_validated_commercial_content_is_published(self):
        for slug in ("commandes", "offres-speciales", "soutien", "mentions-legales"):
            path = DIST / slug / "index.html"
            self.assertTrue(path.is_file(), slug)
            soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
            self.assertIsNone(soup.select_one('meta[name="robots"]'), slug)

        home = BeautifulSoup((DIST / "index.html").read_text(encoding="utf-8"), "html.parser")
        commercial = home.select_one(".home-commercial")
        self.assertIsNotNone(commercial)
        commercial_text = commercial.get_text(" ", strip=True)
        self.assertIn("40 % de remise", commercial_text)
        self.assertIn("Mondial Relay", commercial_text)
        self.assertEqual(
            ["Libraires", "Particuliers"],
            [heading.get_text(strip=True) for heading in commercial.select(".commercial-audience h4")],
        )
        self.assertEqual(1, len(commercial.select('a[href="/soutien/"]')))
        donation_form = commercial.select_one(
            'form.donation-form[action="https://www.paypal.com/donate"]'
        )
        self.assertIsNotNone(donation_form)
        self.assertEqual(
            "G4GQ22SF6LMW6",
            donation_form.select_one('input[name="hosted_button_id"]')["value"],
        )
        self.assertEqual(
            "Faire un don avec PayPal",
            donation_form.select_one("button").get_text(" ", strip=True),
        )
        self.assertIsNotNone(commercial.select_one('a[href="/offres-speciales/"]'))

    def test_redirects_cover_every_old_book_page(self):
        redirects = (DIST / ".htaccess").read_text(encoding="utf-8")
        legacy = load_json(ROOT / "config" / "legacy-redirects.json")["livres"]
        for slug, source in legacy.items():
            self.assertIn(f'"/{source}" "/livres/{slug}/"', redirects)

    def test_javascript_syntax(self):
        for path in DIST.rglob("*.js"):
            result = subprocess.run(
                ["node", "--check", str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
