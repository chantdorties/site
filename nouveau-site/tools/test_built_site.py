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

from tools.content_data import (
    APPEARANCE_COLOR_FIELDS,
    APPEARANCE_FONT_FIELDS,
    APPEARANCE_FONTS,
    inline_media_paths,
    load_settings,
)


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
            for folder in ("pages",)
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
            for folder in ("pages",)
            for path in (ROOT / "content" / folder).glob("*.json")
        ]
        source_news = [load_json(path) for path in (ROOT / "content" / "actualites").glob("*.json")]
        source_collections = [load_json(path) for path in (ROOT / "content" / "collections").glob("*.json")]
        seo_images = {
            item.get("seo", {}).get("image")
            for item in [*source_books, *source_people, *source_pages, *source_news, *source_collections]
            if item.get("seo", {}).get("image")
        }
        # Le même recensement que la génération, pris à sa source : recopier la règle
        # ici la laisserait diverger au premier champ passé en markdown.
        inline_images = inline_media_paths(
            {
                "books": source_books,
                "people": source_people,
                "collections": source_collections,
                "news": source_news,
                "pages": [
                    page
                    for page in source_pages
                    if page["slug"] != "actualites" and not page.get("aVerifier")
                ],
                "settings": load_settings(ROOT / "content"),
            }
        )
        expected = (
            2 * len(source_books)
            + sum(len(book["illustrations"]) for book in source_books)
            + 2 * sum(bool(person["imagePrincipale"]) for person in source_people)
            + sum(len(person["images"]) for person in source_people)
            + sum(len(page["images"]) for page in source_pages if page["slug"] != "actualites")
            + sum(bool(item.get("image")) for item in source_news)
            + sum(bool(item.get("logo")) for item in source_collections)
            + len(seo_images)
            + len(inline_images)
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
        self.assertIn(settings("accueil")["libelleOffres"], home.get_text(" ", strip=True))

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

    def test_published_stylesheet_carries_the_saved_theme(self):
        css = (DIST / "assets" / "css" / "site.css").read_text(encoding="utf-8")
        appearance = settings("apparence")
        theme = css[css.index(":root {", css.index("content/reglages/apparence.json")):]
        theme = theme[: theme.index("}")]
        for key, token in (
            ("couleurFond", "--color-background"),
            ("couleurTexte", "--color-text"),
            ("couleurPrincipale", "--color-primary"),
            ("couleurBoutons", "--color-button"),
        ):
            self.assertIn(f"  {token}: {appearance[key].lower()};", theme, key)
        self.assertNotRegex(theme, r"couleur|police")
        # La feuille est appelée avec l’empreinte qui tient compte du thème.
        home = (DIST / "index.html").read_text(encoding="utf-8")
        self.assertRegex(home, r"/assets/css/site\.css\?v=[0-9a-f]{12}")

    def test_pages_send_secondary_addresses_to_the_official_one(self):
        """Free sert les mêmes fichiers en http://chantdorties.free.fr, sans HTTPS : chaque
        page renvoie d’emblée vers l’adresse officielle, celle du réglage domaine."""
        domaine = load_settings(ROOT / "content")["site"]["domaine"]
        self.assertEqual("https://chantdorties.pages-perso.free.fr", domaine)
        for route in ("index.html", "catalogue/index.html", "404.html"):
            soup = BeautifulSoup((DIST / route).read_text(encoding="utf-8"), "html.parser")
            first = soup.head.find_all(recursive=False)[1]
            self.assertEqual("script", first.name, route)
            self.assertIn('"chantdorties.free.fr"', first.string)
            self.assertIn('location.replace("https://chantdorties.pages-perso.free.fr"+', first.string)
        home = BeautifulSoup((DIST / "index.html").read_text(encoding="utf-8"), "html.parser")
        self.assertEqual(domaine + "/", home.select_one('link[rel="canonical"]')["href"])
        self.assertIn(f"<loc>{domaine}/</loc>", (DIST / "sitemap.xml").read_text(encoding="utf-8"))

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
        # L’accueil et les actualités sont dans les réglages, les mentions légales
        # parmi les pages : plus de rubrique « Pages principales ».
        self.assertNotIn("pages_fixes", collections)
        self.assertTrue(collections["pages"]["create"])
        self.assertFalse(collections["pages"]["delete"])
        # Seuls les projets s’effacent vraiment : ils n’ont pas d’adresse à rediriger.
        self.assertTrue(collections["projets"]["create"])
        self.assertTrue(collections["projets"]["delete"])
        self.assertEqual("nouveau-site/content/projets", collections["projets"]["folder"])
        self.assertEqual("nouveau-site/content/pages", collections["pages"]["folder"])
        self.assertNotIn("/admin/", (DIST / "sitemap.xml").read_text(encoding="utf-8"))

    def test_admin_protects_itself_where_no_header_can_be_set(self):
        """Chez Free, l’administration n’a ni en-tête de sécurité ni .htaccess : la page
        porte elle-même la politique d’OVH, et garde.js passe avant Decap."""
        soup = BeautifulSoup((DIST / "admin" / "index.html").read_text(encoding="utf-8"), "html.parser")
        meta = soup.select_one('meta[http-equiv="Content-Security-Policy"]')["content"]
        htaccess = (ROOT / "frontend" / "admin-serveur" / "htaccess.conf").read_text(encoding="utf-8")
        header = re.search(r'Content-Security-Policy "([^"]+)"', htaccess).group(1)
        self.assertEqual(header, meta.replace(" http://127.0.0.1:8082", ""))
        scripts = [script["src"] for script in soup.find_all("script")]
        self.assertEqual("garde.js", scripts[0])
        self.assertTrue((DIST / "admin" / "garde.js").is_file())
        self.assertIn("https://chantdorties.pages-perso.free.fr", (DIST / "admin" / "garde.js").read_text(encoding="utf-8"))

    def test_auth_relay_hands_the_token_to_named_origins_only(self):
        relay = ROOT / "frontend" / "admin-serveur"
        php = (relay / "callback.php").read_text(encoding="utf-8")
        script = (relay / "callback.js").read_text(encoding="utf-8")
        self.assertIn("ORIGINES_ADMINISTRATION = ['https://chantdorties.pages-perso.free.fr']", php)
        self.assertNotRegex(script, r"postMessage\([^)]*'\*'")
        self.assertIn("origines.indexOf(evenement.origin) === -1", script)
        self.assertIn("window.opener.postMessage(message, evenement.origin)", script)

    def test_every_editable_collection_has_a_preview_and_a_description(self):
        """Sans aperçu déclaré, Decap affiche un empilement de champs bruts ; sans
        description, rien ne dit à quoi sert la rubrique ni ce qu’elle interdit."""
        config = yaml.safe_load((DIST / "admin" / "config.yml").read_text(encoding="utf-8"))
        registered = set(
            re.findall(
                r"registerPreviewTemplate\('([^']+)'",
                (DIST / "admin" / "preview.js").read_text(encoding="utf-8"),
            )
        )
        for collection in config["collections"]:
            name = collection["name"]
            self.assertTrue(str(collection.get("description", "")).strip(), name)
            if collection.get("editor", {}).get("preview") is False:
                continue
            if "files" in collection and name == "reglages":
                # Une rubrique de fichiers voit son aperçu choisi entrée par entrée.
                for entry in collection["files"]:
                    self.assertIn(entry["name"], registered, f"{name}/{entry['name']}")
                continue
            self.assertIn(name, registered, name)

    def test_select_options_cover_every_stored_value(self):
        """Une valeur absente de la liste déroulante disparaîtrait au premier
        enregistrement de la fiche."""
        config = yaml.safe_load((DIST / "admin" / "config.yml").read_text(encoding="utf-8"))
        folders = {
            collection["name"]: collection
            for collection in config["collections"]
            if "folder" in collection
        }
        for name, collection in folders.items():
            selects = {
                field["name"]: {option["value"] for option in field["options"]}
                for field in collection["fields"]
                if field.get("widget") == "select" and isinstance(field.get("options"), list)
                and all(isinstance(option, dict) for option in field["options"])
            }
            for path in (ROOT / "content" / collection["folder"].split("/")[-1]).glob("*.json"):
                record = json.loads(path.read_text(encoding="utf-8"))
                for field, allowed in selects.items():
                    stored = record.get(field)
                    for item in stored if isinstance(stored, list) else [stored]:
                        if item is None:
                            continue
                        self.assertIn(item, allowed, f"{path.name} · {field}")

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

    def test_relation_filters_never_target_a_multiple_value_field(self):
        """Decap compare la valeur filtrée par values.includes(valeur) : sur un champ
        à plusieurs valeurs (roles), aucune fiche ne passe et la liste reste vide."""
        config = yaml.safe_load((DIST / "admin" / "config.yml").read_text(encoding="utf-8"))
        collections = {item["name"]: item for item in config["collections"]}

        def fields_of(container):
            for field in container.get("fields", []):
                yield field
                yield from fields_of(field)
                if "field" in field:
                    yield field["field"]

        for collection in config["collections"]:
            for entry in collection.get("files") or [collection]:
                for field in fields_of(entry):
                    if field.get("widget") != "relation":
                        continue
                    target = {item["name"]: item for item in collections[field["collection"]]["fields"]}
                    for rule in field.get("filters", []):
                        filtered = target[rule["field"].split(".")[0]]
                        self.assertFalse(
                            filtered.get("widget") == "list" or filtered.get("multiple"),
                            f"{collection['name']}/{field['name']} filtre sur {rule['field']}",
                        )

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
        # Chaque fichier de réglages a son gabarit, à son nom d’entrée.
        reglages = next(item for item in config["collections"] if item["name"] == "reglages")
        owned = {("reglages", entry["name"]): entry["name"] for entry in reglages["files"]}
        self.assertLessEqual(set(owned.values()), registered)
        for collection in config["collections"]:
            collection_preview = (collection.get("editor") or {}).get("preview")
            for entry in collection.get("files") or []:
                entry_preview = (entry.get("editor") or {}).get("preview")
                preview = collection_preview if entry_preview is None else entry_preview
                if preview is False:
                    continue
                allowed = {collection["name"], owned.get((collection["name"], entry["name"]))}
                self.assertNotIn(
                    entry["name"],
                    registered - allowed,
                    f"{collection['name']}/{entry['name']} recevrait un aperçu étranger",
                )
        self.assertNotEqual(False, (reglages.get("editor") or {}).get("preview"))
        for entry in reglages["files"]:
            self.assertNotEqual(False, (entry.get("editor") or {}).get("preview"), entry["name"])

    def test_appearance_preview_follows_the_python_contract(self):
        script = (DIST / "admin" / "preview.js").read_text(encoding="utf-8")
        fonts = dict(re.findall(r"^    '([a-z-]+)': '([^']+)',?$", script, re.M))
        self.assertEqual(dict(APPEARANCE_FONTS), fonts)
        colors = re.findall(r"\['(couleur\w+)', '(--color-[\w-]+)', '(#[0-9a-f]{6})'\]", script)
        self.assertEqual(list(APPEARANCE_COLOR_FIELDS), [key for key, _, _ in colors])
        variables = (ROOT / "frontend" / "assets" / "css" / "00-variables.css").read_text(encoding="utf-8")
        stylesheet = (DIST / "admin" / "preview.css").read_text(encoding="utf-8")
        for _, token, default in colors:
            # Même valeur par défaut dans le site, l’aperçu Apparence et les autres aperçus.
            self.assertIn(f"  {token}: {default};", variables, token)
            self.assertIn(f"  {token}: {default};", stylesheet, token)

    def test_an_offer_shows_its_books_as_catalogue_cards(self):
        soup = BeautifulSoup((DIST / "offres-speciales" / "index.html").read_text(encoding="utf-8"), "html.parser")
        sections = soup.select(".editorial-section")
        self.assertEqual(3, len(sections))
        for section in sections:
            cards = section.select(".book-grid--section .book-card")
            self.assertEqual(2, len(cards))
            self.assertTrue(all(card.select_one("img.book-card__cover") for card in cards))
            self.assertRegex(section.select_one(".book-card__meta").get_text(), r"\d+ €")

    def test_admin_forms_put_the_essentials_first(self):
        """Chaque rubrique s’ouvre sur « L’essentiel » ; l’adresse de la page et les
        autres réglages techniques viennent en dernier, sous leur propre intertitre.
        Un intertitre n’est jamais obligatoire : Decap refuserait d’enregistrer."""
        config = yaml.safe_load((DIST / "admin" / "config.yml").read_text(encoding="utf-8"))
        collections = {item["name"]: item for item in config["collections"]}
        for name in ("livres", "personnes", "collections", "actualites", "projets", "pages"):
            fields = collections[name]["fields"]
            groups = [field for field in fields if field.get("widget") == "groupe"]
            self.assertEqual("L’essentiel", fields[0]["label"], name)
            self.assertTrue(all(group.get("required") is False for group in groups), name)
            names = [field["name"] for field in fields]
            technique = max(i for i, field in enumerate(fields) if field.get("widget") == "groupe")
            self.assertEqual("Réglages techniques", fields[technique]["label"], name)
            self.assertGreater(names.index("slug"), technique, name)

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
            item["file"].rsplit("/", 1)[-1].removesuffix(".json"): item
            for item in collections["reglages"]["files"]
        }
        for path in (ROOT / "content" / "reglages").glob("*.json"):
            # Les intertitres (widget « groupe ») n’écrivent rien dans le fichier ; un
            # champ facultatif (référencement, anciennes adresses) peut y manquer.
            fields = [
                field for field in settings_files[path.stem]["fields"] if field.get("widget") != "groupe"
            ]
            stored = set(load_json(path))
            self.assertLessEqual(stored, {field["name"] for field in fields}, path.name)
            self.assertLessEqual(
                {field["name"] for field in fields if field.get("required", True)}, stored, path.name
            )

    def test_admin_appearance_entry_only_offers_contract_values(self):
        config = yaml.safe_load((DIST / "admin" / "config.yml").read_text(encoding="utf-8"))
        reglages = next(item for item in config["collections"] if item["name"] == "reglages")
        entry = next(item for item in reglages["files"] if item["name"] == "apparence")
        self.assertEqual("nouveau-site/content/reglages/apparence.json", entry["file"])
        fields = {field["name"]: field for field in entry["fields"]}
        self.assertEqual(set(APPEARANCE_COLOR_FIELDS) | set(APPEARANCE_FONT_FIELDS), set(fields))

        for name in APPEARANCE_COLOR_FIELDS:
            field = fields[name]
            self.assertEqual("color", field["widget"], name)
            self.assertFalse(field.get("enableAlpha", False), name)
            self.assertEqual("^#[0-9A-Fa-f]{6}$", field["pattern"][0], name)
        for name in APPEARANCE_FONT_FIELDS:
            field = fields[name]
            self.assertEqual("select", field["widget"], name)
            self.assertEqual(
                list(APPEARANCE_FONTS), [option["value"] for option in field["options"]], name
            )
        # Les libellés parlent à la rédaction, jamais en noms de tokens CSS.
        for field in entry["fields"]:
            self.assertNotRegex(field["label"], r"--|color|font|css", field["name"])
        # Sensible à la casse : « couleurLiens » contient « urL » sans être une adresse.
        forbidden = re.compile(r"[cC]ss|[sS]tyle|^url|Url|[tT]aille|[eE]spacement|[fF]ichier")
        for name in fields:
            self.assertNotRegex(name, forbidden)

    def test_menu_and_footer_links_hide_technical_fields(self):
        config = yaml.safe_load((DIST / "admin" / "config.yml").read_text(encoding="utf-8"))
        reglages = next(item for item in config["collections"] if item["name"] == "reglages")
        files = {item["name"]: item for item in reglages["files"]}
        for entry, list_name in (("navigation", "liens"), ("footer", "liensNavigation")):
            links = next(field for field in files[entry]["fields"] if field["name"] == list_name)
            subfields = {field["name"]: field for field in links["fields"]}
            # L’ordre est celui de la liste : aucun numéro à saisir.
            self.assertNotIn("ordre", subfields, entry)
            self.assertTrue(links.get("collapsed"), entry)
            self.assertIn("{{fields.url}}", links["summary"], entry)
        menu = next(field for field in files["navigation"]["fields"] if field["name"] == "liens")
        self.assertEqual("hidden", {field["name"]: field for field in menu["fields"]}["id"]["widget"])

    def test_previews_only_use_classes_the_site_still_produces(self):
        # Les aperçus recopient le HTML du site pour en reprendre la feuille de style.
        # Une classe renommée dans le générateur laisserait l’aperçu sans style, sans
        # erreur visible : chaque classe doit exister dans les pages produites, sauf
        # celles propres à l’administration, définies dans preview.css ou admin.css.
        script = (ROOT / "frontend" / "admin" / "preview.js").read_text(encoding="utf-8")
        own_styles = "".join(
            (ROOT / "frontend" / "admin" / name).read_text(encoding="utf-8")
            for name in ("preview.css", "admin.css")
        )
        used = {
            name
            for match in re.finditer(r"className:\s*(['`])(.*?)\1", script)
            for name in match.group(2).split()
            if not re.search(r"[${}]", name)
        }
        produced = {
            name
            for path in self.public_html_files
            for value in re.findall(r'class="([^"]*)"', path.read_text(encoding="utf-8"))
            for name in value.split()
        }
        # Le bandeau des brouillons n’apparaît que dans « make preview » ; « compteur »
        # n’est qu’une enveloppe, seules ses lignes ont un style.
        known_exceptions = {"draft-notice", "compteur"}
        self.assertIn('class="draft-notice"', (ROOT / "tools" / "rendu" / "gabarit.py").read_text(encoding="utf-8"))
        self.assertGreater(len(used), 50)
        missing = sorted(
            name
            for name in used - produced - known_exceptions
            if not re.search(rf"\.{re.escape(name)}(?![\w-])", own_styles)
        )
        self.assertEqual([], missing)

    def test_shared_form_components_are_defined_once(self):
        # Un composant recopié finit par diverger : son motif et son plafond ne
        # s’écrivent qu’une fois, les autres champs y renvoient par une ancre YAML.
        source = (DIST / "admin" / "config.yml").read_text(encoding="utf-8")
        for motif in ("max_file_size", "^[A-Z0-9]{13}$", "^[a-z0-9]+(?:-[a-z0-9]+)*$"):
            self.assertEqual(1, source.count(motif), motif)
        self.assertEqual(1, source.count('name: alt, widget: string'))

        config = yaml.safe_load(source)

        def fields_of(fields):
            for field in fields:
                yield field
                yield from fields_of(field.get("fields", []))
                if "field" in field:
                    yield field["field"]

        every_field = []
        for collection in config["collections"]:
            every_field += list(fields_of(collection.get("fields", [])))
            for entry in collection.get("files", []):
                every_field += list(fields_of(entry["fields"]))
        # Un champ repris par une ancre est le même objet : on ne le compte qu’une fois.
        every_field = list({id(field): field for field in every_field}.values())
        slugs = [field for field in every_field if field["name"] == "slug" and field["widget"] == "string"]
        self.assertEqual(6, len(slugs))
        # « Identifiant » pour les actualités et les projets, qui n’ont pas de page.
        self.assertEqual({"Adresse de la page", "Identifiant"}, {field["label"] for field in slugs})
        paypal = [field for field in every_field if field["name"].lower().endswith("hostedbuttonid")]
        self.assertEqual(3, len(paypal))
        for field in paypal:
            self.assertIn("Les 13 caractères fournis par PayPal", field["hint"], field["name"])
        for field in every_field:
            if field["name"].endswith("Alt") or field["name"] == "alt":
                self.assertIn("lue par les personnes qui ne la voient pas", field["hint"], field["name"])

    def test_no_draft_warning_in_production(self):
        for path in self.public_html_files:
            content = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("prévisualisation :", content, path)

    def test_available_books_use_the_original_paypal_buttons(self):
        source_books = [load_json(path) for path in (ROOT / "content" / "livres").glob("*.json")]
        for book in source_books:
            path = DIST / "livres" / book["slug"] / "index.html"
            soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
            form = soup.select_one(
                '.purchase-line form.paypal-form[action="https://www.paypal.com/cgi-bin/webscr"]'
            )
            if book["disponible"]:
                self.assertIsNotNone(form, book["slug"])
                self.assertEqual("_s-xclick", form.select_one('input[name="cmd"]')["value"])
                self.assertEqual(
                    book["paypalHostedButtonId"],
                    form.select_one('input[name="hosted_button_id"]')["value"],
                )
            else:
                self.assertIsNone(form, book["slug"])

    def test_editorial_pages_carry_the_paypal_buttons_that_were_entered(self):
        for path in (ROOT / "content" / "pages").glob("*.json"):
            page = load_json(path)
            if page["statut"] != "publie":
                continue
            expected = [
                button["hostedButtonId"]
                for section in page["sections"]
                for button in section.get("boutonsPaypal", [])
            ]
            built = DIST / page["slug"] / "index.html"
            soup = BeautifulSoup(built.read_text(encoding="utf-8"), "html.parser")
            found = [
                field["value"]
                for field in soup.select('.section-actions input[name="hosted_button_id"]')
            ]
            self.assertEqual(expected, found, page["slug"])

    def test_every_page_offers_the_cart_from_its_menu(self):
        """Le panier est au menu, donc joignable de partout — y compris sur téléphone."""
        payment = settings("paiement")
        for path in self.public_html_files:
            soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
            forms = soup.select("form.nav-cart")
            # Un seul formulaire par page : le bloc signé est trop lourd pour être répété.
            self.assertEqual(1, len(forms), path)
            self.assertEqual(
                payment["panierEncrypted"],
                forms[0].select_one('input[name="encrypted"]')["value"],
                path,
            )
            # Deux boutons le commandent : celui du menu principal, celui du menu mobile.
            buttons = soup.select(f'button[form="{forms[0]["id"]}"]')
            self.assertEqual(2, len(buttons), path)

    def test_selling_sections_do_not_repeat_the_cart(self):
        for path in (ROOT / "content" / "pages").glob("*.json"):
            page = load_json(path)
            if page["statut"] != "publie":
                continue
            soup = BeautifulSoup(
                (DIST / page["slug"] / "index.html").read_text(encoding="utf-8"), "html.parser"
            )
            self.assertEqual([], soup.select('.section-actions input[name="encrypted"]'), page["slug"])

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
            settings("accueil")["libelleDon"],
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
        # Une page encore en brouillon n'a pas d'adresse publique : son ancienne
        # adresse mène à « La maison », d'où le visiteur retrouvera son chemin.
        # Voir tools/rendu/technique.py.
        source_records += [
            (record, f"/{record['slug']}/" if record["statut"] == "publie" else "/la-maison/")
            for folder in ("pages",)
            for record in (load_json(path) for path in (ROOT / "content" / folder).glob("*.json"))
        ]
        # L’accueil et les actualités gardent leurs anciennes adresses dans les réglages.
        source_records += [
            (settings("accueil"), "/"),
            (settings("pages")["actualites"], "/actualites/"),
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
