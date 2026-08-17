#!/usr/bin/env python3

import json
import re
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


def settings(name):
    """Les libellés viennent des réglages : les recopier ici rendrait la suite
    rouge dès que le client édite un texte, sans aucune régression réelle."""
    return load_json(ROOT / "content" / "reglages" / f"{name}.json")


def local_target(value, directory):
    """Le fichier visé par une adresse locale, relative au document qui la porte."""
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or value.startswith(("mailto:", "tel:", "#")):
        return None
    path = parsed.path
    if not path:
        return None
    target = DIST / path.lstrip("/") if path.startswith("/") else directory / path
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
        self.assertEqual(169, self.report["pagesHtml"])
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
            load_json(path)
            for folder in ("pages", "pages-fixes")
            for path in (ROOT / "content" / folder).glob("*.json")
        ]
        sitemap = (DIST / "sitemap.xml").read_text(encoding="utf-8")
        for page in source_pages:
            if page["statut"] == "publie":
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
                    target = local_target(value, path.parent)
                    if target is not None and not target.is_file():
                        missing.append((path.relative_to(DIST).as_posix(), value))
            for image in soup.find_all("img", srcset=True):
                for candidate in image["srcset"].split(","):
                    value = candidate.strip().split()[0]
                    target = local_target(value, path.parent)
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

    def test_every_referenced_raster_image_is_processed(self):
        source_books = [load_json(path) for path in (ROOT / "content" / "livres").glob("*.json")]
        source_people = [load_json(path) for path in (ROOT / "content" / "personnes").glob("*.json")]
        source_pages = [
            load_json(path)
            for folder in ("pages", "pages-fixes")
            for path in (ROOT / "content" / folder).glob("*.json")
        ]
        source_news = [load_json(path) for path in (ROOT / "content" / "actualites").glob("*.json")]
        source_collections = [load_json(path) for path in (ROOT / "content" / "collections").glob("*.json")]
        seo_images = {
            item.get("seo", {}).get("image")
            for item in [*source_books, *source_people, *source_pages, *source_news, *source_collections]
            if item.get("seo", {}).get("image")
        }
        expected = (
            2 * len(source_books)
            + sum(len(book["illustrations"]) for book in source_books)
            + 2 * sum(bool(person["imagePrincipale"]) for person in source_people)
            + sum(len(person["images"]) for person in source_people)
            + sum(len(page["images"]) for page in source_pages if page["slug"] != "actualites")
            + sum(bool(item.get("image")) for item in source_news)
            + sum(bool(item.get("logo")) for item in source_collections)
            + len(seo_images)
        )
        self.assertEqual(expected, self.report["medias"]["images"])

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
        self.assertIn(settings("pages")["actualites"]["appelTitre"], soup.get_text(" ", strip=True))
        self.assertNotIn("En images", soup.get_text(" ", strip=True))
        self.assertEqual(self.report["actualites"], len(soup.select(".news-card")))

    def test_announced_news_topics_are_really_published(self):
        """Les pastilles annonçaient des rencontres même quand il n’y en avait aucune."""
        published = {
            json.loads(path.read_text(encoding="utf-8"))["type"]
            for path in (ROOT / "content" / "actualites").glob("*.json")
            if json.loads(path.read_text(encoding="utf-8"))["statut"] == "publie"
        }
        labels = {"salon": "Salon", "parution": "Parution", "rencontre": "Rencontre", "maison": "Vie de la maison"}
        soup = BeautifulSoup((DIST / "actualites" / "index.html").read_text(encoding="utf-8"), "html.parser")
        topics = {span.get_text(strip=True) for span in soup.select(".news-topics span")}
        self.assertEqual({labels[key] for key in published}, topics)

    def test_commercial_labels_come_from_the_settings(self):
        """Ces mots suivent les offres et le mode de vente : ils doivent rester éditables."""
        payment = settings("paiement")
        available = next(book for book in self.books if book["disponible"])
        unavailable = next(book for book in self.books if not book["disponible"])
        for slug, expected in (
            (available["slug"], (payment["libellePanier"], payment["libelleDisponible"])),
            (unavailable["slug"], (payment["libelleContact"], payment["libelleIndisponible"])),
        ):
            text = BeautifulSoup(
                (DIST / "livres" / slug / "index.html").read_text(encoding="utf-8"), "html.parser"
            ).get_text(" ", strip=True)
            for label in expected:
                self.assertIn(label, text, slug)
        home = BeautifulSoup((DIST / "index.html").read_text(encoding="utf-8"), "html.parser")
        self.assertIn(payment["libelleOffres"], home.get_text(" ", strip=True))

    def test_every_collection_shows_its_emblem(self):
        """Les emblèmes viennent de l’ancien site : leur perte passerait inaperçue."""
        for collection in self.collections:
            soup = BeautifulSoup(
                (DIST / "collections" / collection["slug"] / "index.html").read_text(encoding="utf-8"),
                "html.parser",
            )
            emblem = soup.select_one(".collection-emblem")
            self.assertIsNotNone(emblem, collection["slug"])
            self.assertTrue(emblem["alt"].strip(), collection["slug"])
            self.assertTrue((DIST / emblem["src"].lstrip("/")).is_file(), emblem["src"])
        index = BeautifulSoup((DIST / "collections" / "index.html").read_text(encoding="utf-8"), "html.parser")
        self.assertEqual(len(self.collections), len(index.select(".collection-showcase__emblem")))

    def test_projects_page_lists_the_projects(self):
        soup = BeautifulSoup((DIST / "projets" / "index.html").read_text(encoding="utf-8"), "html.parser")
        cards = soup.select(".project-card")
        self.assertEqual(self.report["projets"], len(cards))
        for card in cards:
            self.assertIsNotNone(card.select_one("h2"), card)
        text = soup.get_text(" ", strip=True)
        # L’introduction reste éditable sur la page, la liste vient de la rubrique.
        self.assertIn("Trois projets pour fin 2026-début 2027", text)
        # Un intervenant qui a une fiche devient un lien, les autres restent du texte.
        self.assertIn("/personnes/sebastien-boscus/", str(soup))
        self.assertIn("Najat Azira", text)

    def test_archived_projects_are_absent_from_the_projects_page(self):
        published = {
            json.loads(path.read_text(encoding="utf-8"))["titre"]
            for path in (ROOT / "content" / "projets").glob("*.json")
            if json.loads(path.read_text(encoding="utf-8"))["statut"] == "publie"
        }
        titles = {
            card.select_one("h2").get_text(strip=True)
            for card in BeautifulSoup(
                (DIST / "projets" / "index.html").read_text(encoding="utf-8"), "html.parser"
            ).select(".project-card")
        }
        self.assertEqual(published, titles)

    def test_collection_index_has_visual_previews(self):
        pages = {
            "home": BeautifulSoup((DIST / "index.html").read_text(encoding="utf-8"), "html.parser"),
            "collections": BeautifulSoup(
                (DIST / "collections" / "index.html").read_text(encoding="utf-8"),
                "html.parser",
            ),
        }
        for page_name, soup in pages.items():
            tiles = soup.select(".collection-showcase__item")
            self.assertEqual(len(self.collections), len(tiles), page_name)
            for tile in tiles:
                self.assertIsNotNone(tile.select_one(".collection-showcase__link"), page_name)
                self.assertGreaterEqual(len(tile.select(".collection-showcase__covers img")), 1, page_name)
                self.assertLessEqual(len(tile.select(".collection-showcase__covers img")), 3, page_name)

        self.assertTrue(all(tile.select_one("h3") for tile in pages["home"].select(".collection-showcase__item")))
        self.assertTrue(all(tile.select_one("h2") for tile in pages["collections"].select(".collection-showcase__item")))

    def test_house_page_uses_editorial_cards(self):
        soup = BeautifulSoup((DIST / "la-maison" / "index.html").read_text(encoding="utf-8"), "html.parser")
        cards = soup.select(".house-card")
        self.assertEqual(9, len(cards))
        self.assertEqual([], soup.select(".collection-tile"))
        for card in cards:
            self.assertIsNotNone(card.select_one(".house-card__action"))
            self.assertIsNotNone(card.select_one("h2"))

    def test_admin_is_present_but_not_indexed(self):
        index = DIST / "admin" / "index.html"
        config_path = DIST / "admin" / "config.yml"
        soup = BeautifulSoup(index.read_text(encoding="utf-8"), "html.parser")
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        self.assertEqual("noindex, nofollow", soup.select_one('meta[name="robots"]')["content"])
        self.assertEqual("github", config["backend"]["name"])
        self.assertEqual("chantdorties/site", config["backend"]["repo"])
        self.assertEqual("http://127.0.0.1:8082/api/v1", config["local_backend"]["url"])
        collections = {item["name"]: item for item in config["collections"]}
        self.assertIn("reglages", collections)
        self.assertIn("pages_fixes", collections)
        self.assertTrue(collections["pages"]["create"])
        self.assertFalse(collections["pages"]["delete"])
        # Seuls les projets s’effacent vraiment : ils n’ont pas d’adresse à rediriger.
        self.assertTrue(collections["projets"]["create"])
        self.assertTrue(collections["projets"]["delete"])
        self.assertEqual("nouveau-site/content/projets", collections["projets"]["folder"])
        self.assertEqual("nouveau-site/content/pages", collections["pages"]["folder"])
        self.assertEqual(
            {"page_accueil", "page_actualites", "page_mentions_legales"},
            {item["name"] for item in collections["pages_fixes"]["files"]},
        )
        self.assertNotIn("/admin/", (DIST / "sitemap.xml").read_text(encoding="utf-8"))

    def test_admin_config_satisfies_decap_required_properties(self):
        """Un YAML valide peut rester refusé par Decap et bloquer toute
        l’administration : ces clés obligatoires ne s’en déduisent pas."""
        config = yaml.safe_load((DIST / "admin" / "config.yml").read_text(encoding="utf-8"))
        for section in ("backend", "media_library"):
            if section in config:
                self.assertIn("name", config[section], section)
        self.assertIn("media_folder", config)
        for collection in config["collections"]:
            self.assertIn("name", collection)
            self.assertIn("label", collection)
            # Une rubrique est soit un dossier, soit une liste de fichiers.
            self.assertNotEqual(
                "folder" in collection,
                "files" in collection,
                collection["name"],
            )
            entries = collection.get("files") or [collection]
            for entry in entries:
                for field in entry["fields"]:
                    self.assertIn("name", field, f"{collection['name']}/{entry.get('name')}")
                    self.assertIn("widget", field, f"{collection['name']}/{field.get('name')}")

    def test_no_preview_template_can_be_applied_to_the_wrong_entry(self):
        """Decap retrouve un aperçu par nom de rubrique ET par nom de fichier.

        Un fichier de réglages nommé comme une rubrique de contenu reçoit donc
        son aperçu, qui plante sur des champs qu’il n’a pas.
        """
        config = yaml.safe_load((DIST / "admin" / "config.yml").read_text(encoding="utf-8"))
        registered = set(
            re.findall(
                r"registerPreviewTemplate\(\s*['\"]([^'\"]+)['\"]",
                (DIST / "admin" / "preview.js").read_text(encoding="utf-8"),
            )
        )
        self.assertTrue(registered, "aucun gabarit d’aperçu détecté")
        for collection in config["collections"]:
            if (collection.get("editor") or {}).get("preview") is False:
                continue
            for entry in collection.get("files") or []:
                self.assertNotIn(
                    entry["name"],
                    registered - {collection["name"]},
                    f"{collection['name']}/{entry['name']} recevrait un aperçu étranger",
                )

    def test_admin_exposes_every_editable_json_field(self):
        config = yaml.safe_load((DIST / "admin" / "config.yml").read_text(encoding="utf-8"))
        collections = {item["name"]: item for item in config["collections"]}
        source_folders = {
            "livres": ROOT / "content" / "livres",
            "personnes": ROOT / "content" / "personnes",
            "collections": ROOT / "content" / "collections",
            "actualites": ROOT / "content" / "actualites",
            "pages": ROOT / "content" / "pages",
        }
        for name, folder in source_folders.items():
            source_fields = {
                key
                for path in folder.glob("*.json")
                for key in load_json(path)
            }
            admin_fields = {field["name"] for field in collections[name]["fields"]}
            self.assertLessEqual(source_fields, admin_fields, name)

        settings_files = {
            item["name"]: item for item in collections["reglages"]["files"]
        }
        for path in (ROOT / "content" / "reglages").glob("*.json"):
            self.assertEqual(
                set(load_json(path)),
                {field["name"] for field in settings_files[path.stem]["fields"]},
                path.name,
            )

        fixed_files = {
            item["file"].rsplit("/", 1)[-1].removesuffix(".json"): item
            for item in collections["pages_fixes"]["files"]
        }
        for path in (ROOT / "content" / "pages-fixes").glob("*.json"):
            self.assertLessEqual(
                set(load_json(path)),
                {field["name"] for field in fixed_files[path.stem]["fields"]},
                path.name,
            )

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
        payment = settings("paiement")
        self.assertEqual(
            payment["donationHostedButtonId"],
            donation_form.select_one('input[name="hosted_button_id"]')["value"],
        )
        self.assertEqual(
            payment["libelleDon"],
            donation_form.select_one("button").get_text(" ", strip=True),
        )
        self.assertIsNotNone(commercial.select_one('a[href="/offres-speciales/"]'))

    def test_redirects_cover_every_old_book_page(self):
        redirects = (DIST / ".htaccess").read_text(encoding="utf-8")
        legacy = load_json(ROOT / "config" / "legacy-redirects.json")["livres"]
        for slug, source in legacy.items():
            self.assertIn(f'"/{source}" "/livres/{slug}/"', redirects)
        source_records = [
            (record, f"/livres/{record['slug']}/")
            for record in (load_json(path) for path in (ROOT / "content" / "livres").glob("*.json"))
        ]
        source_records += [
            (record, f"/{record['slug']}/")
            for folder in ("pages", "pages-fixes")
            for record in (load_json(path) for path in (ROOT / "content" / folder).glob("*.json"))
            if record["slug"] not in {"accueil"}
        ]
        for record, target in source_records:
            for source in record["anciensSlugs"]:
                self.assertIn(f'"/{source.lstrip("/")}" "{target}"', redirects)

    def test_explicit_home_selection_and_alternative_texts_are_rendered(self):
        source_books = [load_json(path) for path in (ROOT / "content" / "livres").glob("*.json")]
        selected = sorted(
            (book for book in source_books if book["miseEnAvantAccueil"] and book["disponible"]),
            key=lambda book: (book["ordreAccueil"], book["ordre"], book["slug"]),
        )
        home = BeautifulSoup((DIST / "index.html").read_text(encoding="utf-8"), "html.parser")
        self.assertEqual(
            [f"/livres/{book['slug']}/" for book in selected],
            [link["href"] for link in home.select(".cover-ribbon > a")],
        )
        for book in source_books:
            page = BeautifulSoup(
                (DIST / "livres" / book["slug"] / "index.html").read_text(encoding="utf-8"),
                "html.parser",
            )
            self.assertEqual(book["couvertureAlt"], page.select_one(".book-detail__cover")["alt"])
            self.assertEqual(
                [item["alt"] for item in book["illustrations"]],
                [image["alt"] for image in page.select(".gallery-grid img")],
            )

    def test_custom_seo_fields_override_the_automatic_fallbacks(self):
        book = load_json(ROOT / "content" / "livres" / "a-quelques-pas-de-l-usine.json")
        soup = BeautifulSoup(
            (DIST / "livres" / book["slug"] / "index.html").read_text(encoding="utf-8"),
            "html.parser",
        )
        self.assertEqual(
            f"{book['seo']['titre']} | {settings('site')['nom']}",
            soup.title.get_text(strip=True),
        )
        self.assertEqual(book["seo"]["description"], soup.select_one('meta[name="description"]')["content"])
        self.assertIn("/assets/media/social/", soup.select_one('meta[property="og:image"]')["content"])

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
