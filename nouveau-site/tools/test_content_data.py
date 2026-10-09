#!/usr/bin/env python3

import collections
import contextlib
import html
import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tools.rendu.texte import OutilsTexte
from tools.content_data import (
    APPEARANCE_FONTS,
    ContentError,
    inline_document_paths,
    section_media_paths,
    inline_media_paths,
    load_content,
    media_path,
    navigation_id,
    referenced_media_paths,
    valid_isbn,
    validate_appearance_settings,
)


ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"

# Le générateur lit ces clés en accès direct : si le chargement ne leur donne
# pas de valeur vide, un contenu créé depuis l’administration fait échouer la
# génération sur un KeyError.
GENERATOR_REQUIRED_FIELDS = {
    "books": (
        "ageMinimum", "auteurs", "collection", "couverture", "description", "disponible",
        "extraits", "format", "illustrateurs", "illustrations", "isbn", "miseEnAvantAccueil",
        "nombrePages", "ordre", "ordreAccueil", "prefaciers", "reliure", "titre", "typeOuvrage",
    ),
    "people": ("biographie", "images", "liensExternes", "nom", "ordre", "roles"),
    "pages": ("documents", "images", "liens", "ordre", "sections", "titre"),
    "collections": ("description", "ordre", "titre"),
    "news": ("contenu", "datePublication", "document", "lienExterne"),
    "projects": (
        "auteurs", "auteursHorsFiche", "collection", "description", "illustrateurs",
        "illustrateursHorsFiche", "ordre", "sortiePrevue", "titre",
    ),
}


# Les clés du réglage Apparence, telles que les fixe docs/CONTRAT-APPARENCE.md.
APPEARANCE_KEYS = {
    "couleurFond", "couleurSurface", "couleurTexte", "couleurTexteSecondaire",
    "couleurPrincipale", "couleurPrincipaleFoncee", "couleurSecondaire", "couleurLiens",
    "couleurBoutons", "policeTitres", "policeTexte",
}

def load_site_builder():
    """Le module s’appelle build-site.py : il ne s’importe pas directement.

    Il est prévu pour être lancé comme script, avec tools/ sur le chemin de
    recherche : on reproduit cette condition le temps du chargement.
    """
    tools = str(ROOT / "tools")
    added = tools not in sys.path
    if added:
        sys.path.insert(0, tools)
    try:
        spec = importlib.util.spec_from_file_location("build_site", ROOT / "tools" / "build-site.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if added:
            sys.path.remove(tools)


@contextlib.contextmanager
def content_sandbox():
    """Copie éditable du contenu réel, médias partagés par lien symbolique."""
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        shutil.copytree(CONTENT, root / "content", ignore=shutil.ignore_patterns("media"))
        (root / "content" / "media").symlink_to(CONTENT / "media", target_is_directory=True)
        shutil.copytree(ROOT / "config", root / "config")
        yield root


def exemple(dossier, condition=lambda record: True):
    """Une fiche réelle qui convient au test, choisie dans le contenu du moment.

    Les tests ne nomment jamais une fiche de la rédaction : elle peut la modifier ou la
    supprimer depuis l’administration, et un test qui en dépendrait bloquerait alors
    toute publication (c’est arrivé, #35). Faute de fiche qui convienne, le test est
    sauté plutôt qu’en échec.
    """
    for path in sorted((CONTENT / dossier).glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        record["slug"] = path.stem
        if condition(record):
            return record
    raise unittest.SkipTest(f"aucune fiche de content/{dossier}/ ne convient à ce test")


def page_libre(record):
    """Une page de Mes pages que l’on peut modifier à loisir : pas les mentions légales."""
    return record["slug"] not in ("mentions-legales", "entree")


def edit(root, relative, **changes):
    path = root / relative
    record = json.loads(path.read_text(encoding="utf-8"))
    record.update(changes)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def render_pages(root, *builders):
    """Les pages HTML rendues par les méthodes demandées, sans préparer les images :
    les couvertures reçoivent une adresse factice, suffisante pour lire la structure."""
    build_site = load_site_builder()
    shutil.copytree(ROOT / "frontend", root / "frontend")
    builder = build_site.SiteBuilder(root, root / "dist", include_drafts=False, base_url=None)
    builder.cover_media = collections.defaultdict(lambda: {"small": "c.webp", "large": "c.webp"})
    pages = {}
    builder.write_route = lambda route, html: pages.__setitem__(route, html)
    for name in builders:
        getattr(builder, name)()
    return pages


def referenced_media(raw):
    return referenced_media_paths(raw)


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
        self.assertEqual(4, schema["version"])
        self.assertEqual({"archive", "brouillon", "publie"}, set(schema["statuts"]))
        self.assertGreater(len(self.books), 0)
        self.assertGreater(len(self.people), 0)
        self.assertGreater(len(self.collections), 0)
        self.assertIn("mentions-legales", {page["slug"] for page in self.pages})
        self.assertFalse({"accueil", "actualites"} & {page["slug"] for page in self.pages})

    def test_records_use_one_json_file_each(self):
        for folder, records in (
            ("livres", self.books),
            ("personnes", self.people),
            ("collections", self.collections),
            ("actualites", self.raw["news"]),
            ("projets", self.raw["projects"]),
        ):
            files = {path.stem for path in (CONTENT / folder).glob("*.json")}
            self.assertEqual({record["slug"] for record in records}, files)
        page_files = {path.stem for path in (CONTENT / "pages").glob("*.json")}
        # La page Projets n’a pas de fichier de page : elle est rebâtie depuis pages-du-site/projets.json.
        self.assertEqual({record["slug"] for record in self.pages}, page_files | {"projets"})

    def test_projects_page_comes_from_its_introduction(self):
        intro = self.raw["settings"]["pages"]["projets"]
        page = next(record for record in self.pages if record["slug"] == "projets")
        self.assertEqual(intro["introduction"], page["sections"][0]["contenu"])
        self.assertEqual((intro["titre"], intro["ordre"]), (page["titre"], page["ordre"]))
        with content_sandbox() as root:
            (root / "content/pages/projets.json").write_text(
                json.dumps({"slug": "projets", "titre": "Projets", "statut": "publie", "ordre": 90, "sections": [{"type": "texte", "titre": None, "contenu": "Texte"}]}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContentError, "introduction se règle désormais"):
                load_content(root, include_drafts=True)

    def test_settings_and_fixed_pages_are_present(self):
        self.assertEqual(
            {"accueil", "apparence", "footer", "navigation", "pages", "paiement", "site"},
            set(self.raw["settings"]),
        )
        self.assertFalse((CONTENT / "pages-fixes").exists())
        self.assertIn("mentions-legales", {page["slug"] for page in self.pages})

    def test_appearance_setting_holds_exactly_the_contract_keys(self):
        appearance = self.raw["settings"]["apparence"]
        self.assertIsInstance(appearance, dict)
        self.assertEqual(APPEARANCE_KEYS, set(appearance))

    def test_missing_appearance_setting_is_reported_by_path(self):
        with content_sandbox() as root:
            (root / "content" / "reglages" / "apparence.json").unlink()
            with self.assertRaisesRegex(ContentError, r"JSON invalide : .*reglages/apparence\.json"):
                load_content(root, include_drafts=True)

    def test_real_appearance_setting_is_accepted(self):
        validate_appearance_settings(self.raw["settings"]["apparence"])
        for field in ("policeTitres", "policeTexte"):
            self.assertIn(self.raw["settings"]["apparence"][field], APPEARANCE_FONTS)

    def test_appearance_colors_outside_the_contract_are_refused(self):
        refused = {
            "chaîne vide": "",
            "hexadécimal court": "#fff",
            "transparence": "#c63f32cc",
            "nom de couleur": "red",
            "fonction CSS": "rgb(198, 63, 50)",
            "variable CSS": "var(--color-text)",
            "point-virgule": "#c63f32; display: none",
            "accolade": "#c63f32}",
            "saut de ligne final": "#c63f32\n",
            "valeur non chaîne": 12,
        }
        for case, value in refused.items():
            with self.subTest(case), content_sandbox() as root:
                edit(root, "content/reglages/apparence.json", couleurPrincipale=value)
                with self.assertRaisesRegex(ContentError, "Réglage apparence: couleurPrincipale"):
                    load_content(root, include_drafts=True)

    def test_appearance_fonts_outside_the_list_are_refused(self):
        for value in ("comic-sans", 'Georgia, serif', "", None):
            with self.subTest(value), content_sandbox() as root:
                edit(root, "content/reglages/apparence.json", policeTitres=value)
                with self.assertRaisesRegex(ContentError, "Réglage apparence: policeTitres.*serif-classique"):
                    load_content(root, include_drafts=True)

    def test_appearance_keys_must_match_the_contract(self):
        with content_sandbox() as root:
            path = root / "content" / "reglages" / "apparence.json"
            appearance = json.loads(path.read_text(encoding="utf-8"))
            del appearance["couleurLiens"]
            path.write_text(json.dumps(appearance), encoding="utf-8")
            with self.assertRaisesRegex(ContentError, "Réglage apparence: champs manquants couleurLiens"):
                load_content(root, include_drafts=True)
        with content_sandbox() as root:
            edit(root, "content/reglages/apparence.json", css="body { display: none }")
            with self.assertRaisesRegex(ContentError, "Réglage apparence: champs inconnus css"):
                load_content(root, include_drafts=True)

    def test_appearance_setting_must_be_an_object(self):
        with content_sandbox() as root:
            (root / "content" / "reglages" / "apparence.json").write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ContentError, "Réglage apparence: .*objet JSON"):
                load_content(root, include_drafts=True)

    def test_a_menu_link_created_in_the_admin_gets_an_id_from_its_address(self):
        self.assertEqual("home", navigation_id("/"))
        self.assertEqual("agenda", navigation_id("/agenda/"))
        self.assertEqual("la-maison", navigation_id("/la-maison/#equipe"))
        with content_sandbox() as root:
            path = root / "content" / "reglages" / "navigation.json"
            navigation = json.loads(path.read_text(encoding="utf-8"))
            navigation["liens"].insert(0, {"libelle": "Agenda", "url": "/agenda/", "visible": True})
            path.write_text(json.dumps(navigation, ensure_ascii=False), encoding="utf-8")
            links = load_content(root, include_drafts=True)["settings"]["navigation"]["liens"]
            self.assertEqual("agenda", links[0]["id"])
            self.assertEqual("home", links[1]["id"], "un identifiant existant n’est pas recalculé")

    def test_menu_and_footer_links_follow_the_list_order(self):
        build_site = load_site_builder()
        with content_sandbox() as root:
            shutil.copytree(ROOT / "frontend", root / "frontend")
            for relative, key in (
                ("content/reglages/navigation.json", "liens"),
                ("content/reglages/footer.json", "liensNavigation"),
            ):
                path = root / relative
                setting = json.loads(path.read_text(encoding="utf-8"))
                setting[key].reverse()
                path.write_text(json.dumps(setting, ensure_ascii=False), encoding="utf-8")
            builder = build_site.SiteBuilder(root, root / "dist", include_drafts=False, base_url=None)
            menu = re.findall(r'class="nav-link" href="([^"]+)"', builder.render_nav("home"))
            self.assertEqual(
                [item["url"] for item in builder.navigation_settings["liens"] if item["visible"]],
                menu,
            )
            self.assertEqual("/la-maison/", menu[0])
            footer = builder.render_footer()
            self.assertLess(footer.index('href="/actualites/"'), footer.index('href="/catalogue/"'))

    def test_home_shows_as_many_covers_as_asked(self):
        build_site = load_site_builder()
        with content_sandbox() as root:
            shutil.copytree(ROOT / "frontend", root / "frontend")
            edit(root, "content/pages-du-site/accueil.json", nombreCouvertures=3)
            builder = build_site.SiteBuilder(root, root / "dist", include_drafts=False, base_url=None)
            self.assertEqual(builder.featured_books()[:3], builder.home_cover_books())
            self.assertGreater(len(builder.featured_books()), 3)
        for value in (0, "6", True):
            with self.subTest(value), content_sandbox() as root:
                edit(root, "content/pages-du-site/accueil.json", nombreCouvertures=value)
                with self.assertRaisesRegex(ContentError, "nombreCouvertures"):
                    load_content(root, include_drafts=True)

    def test_orders_and_home_selections_are_explicit(self):
        for records in (self.books, self.people, self.collections, self.pages):
            for record in records:
                self.assertIsInstance(record["ordre"], int, record["slug"])
                self.assertGreaterEqual(record["ordre"], 0, record["slug"])
        # Un livre mis en avant par collection publiée (choisi d’office si la rédaction
        # n’en a coché aucun, par exemple après avoir supprimé le livre coché).
        for collection in self.collections:
            if collection["statut"] != "publie":
                continue
            featured = [
                book for book in self.books
                if book["collection"] == collection["slug"] and book["statut"] == "publie"
                and book["miseEnAvantAccueil"] and book["disponible"]
            ]
            self.assertEqual(1, len(featured), collection["slug"])
        for book in self.books:
            self.assertNotIn(book["slug"], book["aDecouvrir"])
            self.assertEqual(len(book["aDecouvrir"]), len(set(book["aDecouvrir"])))

    def test_editable_alternative_texts_are_migrated(self):
        for book in self.books:
            self.assertTrue(book["couvertureAlt"].strip(), book["slug"])
            for image in book["illustrations"]:
                self.assertTrue(image["image"], book["slug"])
                self.assertTrue(image["alt"].strip(), book["slug"])
        for person in self.people:
            if person["imagePrincipale"]:
                self.assertTrue(person["imagePrincipaleAlt"].strip(), person["slug"])
            for image in person["images"]:
                self.assertTrue(image["alt"].strip(), person["slug"])
        for page in self.pages:
            for image in page["images"]:
                self.assertTrue(image["alt"].strip(), page["slug"])

    def test_legacy_addresses_are_editable_on_records(self):
        for kind in ("books", "people", "collections", "pages", "news"):
            for record in self.raw[kind]:
                self.assertIsInstance(record["anciensSlugs"], list, f"{kind}/{record['slug']}")

    def test_archived_content_is_hidden_from_public_and_preview_builds(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(CONTENT, root / "content", ignore=shutil.ignore_patterns("media"))
            (root / "content" / "media").symlink_to(CONTENT / "media", target_is_directory=True)
            shutil.copytree(ROOT / "config", root / "config")
            slug = exemple("pages", page_libre)["slug"]
            edit(root, f"content/pages/{slug}.json", statut="archive")
            for include_drafts in (False, True):
                bundle = load_content(root, include_drafts=include_drafts)
                self.assertNotIn(slug, {item["slug"] for item in bundle["pages"]})

    def test_a_new_editorial_page_is_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(CONTENT, root / "content", ignore=shutil.ignore_patterns("media"))
            (root / "content" / "media").symlink_to(CONTENT / "media", target_is_directory=True)
            shutil.copytree(ROOT / "config", root / "config")
            page = {
                "slug": "nouvelle-page",
                "statut": "brouillon",
                "titre": "Nouvelle page",
                "type": "page",
                "ordre": 999,
                "rubrique": "À découvrir",
                "libelleAction": "Lire la page",
                "sections": [{"type": "texte", "titre": None, "contenu": "Un contenu éditorial suffisamment complet pour être validé."}],
                "liens": [],
                "images": [],
                "documents": [],
                "anciensSlugs": [],
            }
            path = root / "content" / "pages" / "nouvelle-page.json"
            path.write_text(json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8")
            bundle = load_content(root, include_drafts=True)
            self.assertIn("nouvelle-page", {item["slug"] for item in bundle["pages"]})

    def test_generated_pages_refuse_their_former_places(self):
        # L’accueil et les actualités se règlent chacun en un seul écran : les anciennes
        # pages et les anciens libellés de Paiement sont refusés plutôt qu’ignorés.
        former_page = lambda slug: lambda _: {"slug": slug, "titre": slug, "statut": "publie", "ordre": 0, "type": slug, "sections": [{"type": "texte", "titre": None, "contenu": "Texte"}]}
        for name, change, message in (
            ("pages-fixes/accueil.json", former_page("accueil"), "pages-du-site/"),
            ("pages-fixes/actualites.json", former_page("actualites"), "pages-du-site/"),
            ("pages/accueil.json", former_page("accueil"), "pages-du-site/accueil.json"),
            # Les textes des pages ont quitté les réglages pour « Pages principales ».
            ("reglages/accueil.json", lambda _: {}, "reglages/accueil.json n’est plus lu"),
            ("reglages/pages.json", lambda _: {}, "reglages/pages.json n’est plus lu"),
            ("reglages/paiement.json", lambda data: {**data, "libelleDon": "Faire un don"}, "libelleDon se règle désormais"),
        ):
            with self.subTest(name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                shutil.copytree(CONTENT, root / "content", ignore=shutil.ignore_patterns("media"))
                (root / "content" / "media").symlink_to(CONTENT / "media", target_is_directory=True)
                shutil.copytree(ROOT / "config", root / "config")
                path = root / "content" / name
                path.parent.mkdir(exist_ok=True)
                data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
                path.write_text(json.dumps(change(data), ensure_ascii=False), encoding="utf-8")
                with self.assertRaisesRegex(ContentError, message):
                    load_content(root, include_drafts=True)

    def test_text_blocks_are_checked(self):
        # Les blocs « ::: » posés par l’éditeur sont acceptés ; une forme abîmée à la main
        # est refusée avec un message qui dit quoi corriger, au lieu d’une page qui
        # perdrait sa mise en forme en silence.
        valide = "::: valeur centre principale souligne\nTexte\n:::\n\n::: encadre secondaire\n### Titre\n\nTexte\n:::"
        slug = exemple("pages", page_libre)["slug"]
        with content_sandbox() as root:
            edit(root, f"content/pages/{slug}.json", sections=[{"type": "texte", "titre": None, "contenu": valide}])
            load_content(root, include_drafts=True)
        for contenu, message in (
            ("::: cadre\nTexte\n:::", "bloc inconnu « cadre »"),
            ("::: valeur rouge\nTexte\n:::", "option inconnue pour le bloc « valeur » : rouge"),
            ("::: encadre liens\nTexte\n:::", "option inconnue pour le bloc « encadre » : liens"),
            ("::: valeur centre\nTexte", "n'est pas fermé"),
            ("Texte\n:::", "n'a pas été ouvert"),
            ("::: valeur\n::: encadre\nTexte\n:::\n:::", "s'ouvre dans un autre bloc"),
            (":::valeur!\nTexte\n:::", "ligne de bloc non reconnue"),
        ):
            with self.subTest(contenu), content_sandbox() as root:
                edit(root, f"content/pages/{slug}.json", sections=[{"type": "texte", "titre": None, "contenu": contenu}])
                with self.assertRaisesRegex(ContentError, f"Page {slug} \\(section 1\\): .*{re.escape(message)}"):
                    load_content(root, include_drafts=True)

    def test_placed_image_and_button_blocks_are_checked(self):
        # Une image placée et un bouton portent un seul élément ; un PDF lié depuis un
        # texte existe, est un PDF, et compte parmi les médias utilisés.
        image = next(CONTENT.glob("media/**/*.jpg")).relative_to(ROOT).as_posix()
        pdf = next(CONTENT.glob("media/**/*.pdf")).relative_to(ROOT).as_posix()
        valide = (
            f'::: image gauche\n![Une image]({image} "Légende")\n:::\n\n'
            f"::: bouton plein document\n[Télécharger]({pdf})\n:::\n\n"
            "::: bouton discret\n[Sans destination]()\n:::"
        )
        slug = exemple("pages", page_libre)["slug"]
        with content_sandbox() as root:
            edit(root, f"content/pages/{slug}.json", sections=[{"type": "texte", "titre": None, "contenu": valide}])
            raw = load_content(root, include_drafts=True)["raw"]
            self.assertIn(pdf, inline_document_paths(raw))
            self.assertIn(pdf, referenced_media_paths(raw))
        for contenu, message in (
            (f"::: image gauche droite\n![x]({image})\n:::", "une seule option parmi gauche, droite"),
            (f"::: image gauche\nAvant ![x]({image})\n:::", "une seule image, sans texte autour"),
            ("::: bouton plein discret\n[x](/)\n:::", "une seule option parmi plein, discret"),
            ("::: bouton plein\nCommander\n:::", "un seul lien"),
            (f"::: bouton plein document\n[x]({image})\n:::", "seul un document PDF"),
            ("::: bouton plein document\n[x](content/media/uploads/absent.pdf)\n:::", "absent.pdf"),
        ):
            with self.subTest(contenu), content_sandbox() as root:
                edit(root, f"content/pages/{slug}.json", sections=[{"type": "texte", "titre": None, "contenu": contenu}])
                with self.assertRaisesRegex(ContentError, re.escape(message)):
                    load_content(root, include_drafts=True)

    def test_table_and_video_blocks_are_checked(self):
        # Un tableau a quatre colonnes au plus ; une vidéo, une adresse YouTube ou Vimeo
        # reconnue et un titre. Un bloc vidéo laissé sans adresse n'arrête rien.
        valide = (
            "::: tableau entete\nA | B | C | D\n1 | 2\n:::\n\n"
            "::: video\nhttps://youtu.be/abcDEF123_-\nLe salon\n:::\n\n"
            "::: video\n:::"
        )
        slug = exemple("pages", page_libre)["slug"]
        with content_sandbox() as root:
            edit(root, f"content/pages/{slug}.json", sections=[{"type": "texte", "titre": None, "contenu": valide}])
            load_content(root, include_drafts=True)
        for contenu, message in (
            ("::: tableau\nA | B | C | D | E\n:::", "4 colonnes au plus (celui-ci en a 5)"),
            ("::: tableau large\nA\n:::", "option inconnue pour le bloc « tableau »"),
            ("::: video\nhttps://youtube.com.autre-site.tld/watch?v=abcDEF123_-\nTitre\n:::", "adresse de vidéo non reconnue"),
            ("::: video\nhttps://youtu.be/abcDEF123_-\n:::", "une vidéo a besoin d’un titre"),
        ):
            with self.subTest(contenu), content_sandbox() as root:
                edit(root, f"content/pages/{slug}.json", sections=[{"type": "texte", "titre": None, "contenu": contenu}])
                with self.assertRaisesRegex(ContentError, re.escape(message)):
                    load_content(root, include_drafts=True)

    def test_column_gallery_and_quote_sections(self):
        # Les trois sortes à mise en page propre : chargées, rendues avec leurs images
        # préparées comme celles d’un texte, et comptées parmi les médias utilisés.
        image = next(CONTENT.glob("media/**/*.jpg")).relative_to(ROOT).as_posix()
        sections = [
            {"type": "galerie", "titre": "Photos", "photos": [{"image": image, "alt": "Une photo"}]},
            {"type": "colonnes", "titre": None, "contenu": "Le texte à côté.", "image": image, "alt": "Une image", "cote": "droite"},
            {"type": "citation", "titre": None, "contenu": "Une phrase qui *compte*.", "source": "Une autrice"},
        ]
        page = exemple("pages", page_libre)
        with content_sandbox() as root:
            edit(root, f"content/pages/{page['slug']}.json", sections=sections)
            raw = load_content(root, include_drafts=True)["raw"]
            self.assertIn(image, section_media_paths(raw))
            self.assertIn(image, referenced_media_paths(raw))
            build_site = load_site_builder()
            shutil.copytree(ROOT / "frontend", root / "frontend")
            builder = build_site.SiteBuilder(root, root / "dist", include_drafts=False, base_url=None)
            builder.inline_media = {image: "/assets/media/texte/x.webp"}
            loaded = next(item for item in builder.pages if item["slug"] == page["slug"])
            html = builder.render_sections(loaded["sections"], owner=page["slug"])
            # La galerie sans texte, en tête : le résumé saute à la section suivante.
            self.assertEqual("Le texte à côté.", builder.summary_text(loaded))
        self.assertIn('<section class="editorial-section editorial-gallery"><h2>Photos</h2><div class="gallery-grid">', html)
        self.assertIn('data-gallery-src="/assets/media/texte/x.webp" data-gallery-alt="Une photo"', html)
        self.assertIn('editorial-columns editorial-columns--droite', html)
        self.assertIn('<figure class="editorial-columns__image"><img src="/assets/media/texte/x.webp" alt="Une image"', html)
        self.assertIn('<blockquote class="rich-text"><p>Une phrase qui <em>compte</em>.</p></blockquote><figcaption>Une autrice</figcaption>', html)

    def test_column_gallery_and_quote_sections_are_checked(self):
        image = next(CONTENT.glob("media/**/*.jpg")).relative_to(ROOT).as_posix()
        colonnes = {"type": "colonnes", "titre": None, "contenu": "Texte", "image": image, "alt": "Une image", "cote": "gauche"}
        slug = exemple("pages", page_libre)["slug"]
        livre = self.books[0]["slug"]
        for section, message in (
            ({**colonnes, "alt": ""}, "texte alternatif obligatoire pour l’image de la section"),
            ({**colonnes, "image": ""}, "image obligatoire pour l’image de la section"),
            ({**colonnes, "cote": "haut"}, "place de l’image attendue parmi gauche, droite"),
            ({**colonnes, "image": "content/media/uploads/absente.jpg"}, "absente.jpg"),
            ({**colonnes, "contenu": ""}, "contenu de section obligatoire"),
            ({"type": "galerie", "titre": None, "photos": []}, "une galerie contient au moins une photo"),
            ({"type": "galerie", "titre": None, "photos": [{"image": image, "alt": " "}]}, "texte alternatif obligatoire pour la photo 1 de la galerie"),
            ({"type": "citation", "titre": None, "contenu": "Phrase", "livres": [livre]}, "une section « citation » ne porte ni livre ni bouton"),
        ):
            with self.subTest(message), content_sandbox() as root:
                edit(root, f"content/pages/{slug}.json", sections=[section])
                with self.assertRaisesRegex(ContentError, re.escape(message)):
                    load_content(root, include_drafts=True)

    def test_home_blocks_can_be_hidden(self):
        # Les cases « Masquer ce bloc » : absentes, tout s’affiche comme avant.
        with content_sandbox() as root:
            accueil = json.loads((root / "content/pages-du-site/accueil.json").read_text(encoding="utf-8"))
            for switch in ("masquerInformation", "masquerCollections", "masquerSuivre"):
                self.assertNotIn(switch, accueil)
            raw = load_content(root, include_drafts=True)
            self.assertFalse(any(raw["settings"]["accueil"][switch] for switch in ("masquerInformation", "masquerCollections", "masquerSuivre")))
            home = render_pages(root, "build_home")["/"]
            for marker in ("home-commercial", "collection-showcase", "section--ink"):
                self.assertIn(marker, home)
        with content_sandbox() as root:
            edit(root, "content/pages-du-site/accueil.json", masquerInformation=True, masquerCollections=True, masquerSuivre=True)
            home = render_pages(root, "build_home")["/"]
            self.assertNotIn("home-commercial", home)
            self.assertNotIn("section--ink", home)
            self.assertNotIn("donation-form", home)
            self.assertIn('class="hero"', home)
        with content_sandbox() as root:
            edit(root, "content/pages-du-site/accueil.json", masquerInformation="oui")
            with self.assertRaisesRegex(ContentError, "masquerInformation doit être cochée ou décochée"):
                load_content(root, include_drafts=True)

    def test_home_texts_left_empty_disappear(self):
        vides = {
            champ: ""
            for champ in (
                "heroRubrique", "heroAccent", "heroAccroche", "boutonCatalogue", "boutonCollections",
                "commandesTitre", "commandesTexte", "librairesTitre", "librairesTexte", "soutienTexte",
                "libelleDon", "libelleOffres", "collectionsRubrique", "collectionsTitre", "collectionsTexte",
                "manuscritsTitre",
            )
        }
        with content_sandbox() as root:
            edit(root, "content/pages-du-site/accueil.json", **vides)
            home = render_pages(root, "build_home")["/"]
            self.assertNotIn("hero-actions", home.split('class="cover-ribbon"')[0])
            self.assertNotIn("<h4></h4>", home)
            self.assertNotIn('<p class="eyebrow"></p>', home)
            self.assertNotIn("donation-form", home)
            self.assertNotIn('href="/offres-speciales/"', home)
            suivre = home.split("section--ink")[1].split("</section>")[0]
            self.assertNotIn('href="/manuscrits/"', suivre)
            self.assertIn("commercial-audiences--seul", home)
            self.assertIn("split-callout--seule", home)
            self.assertNotIn("<span></span>", home)
        # Tout le bloc vidé : il disparaît, même coché.
        with content_sandbox() as root:
            edit(root, "content/pages-du-site/accueil.json", **vides, informationRubrique="", titreInformation="",
                 informationTexte="", particuliersTitre="", particuliersTexte="")
            self.assertNotIn("home-commercial", render_pages(root, "build_home")["/"])
        with content_sandbox() as root:
            edit(root, "content/pages-du-site/accueil.json", heroTitre="")
            with self.assertRaisesRegex(ContentError, "heroTitre obligatoire"):
                load_content(root, include_drafts=True)

    def test_news_facebook_block_can_be_hidden(self):
        with content_sandbox() as root:
            edit(root, "content/pages-du-site/actualites.json", appelRubrique="", appelTexte="")
            news = render_pages(root, "build_news_page")["/actualites/"]
            self.assertIn("news-callout", news)
            self.assertNotIn('<p class="eyebrow"></p>', news)
        with content_sandbox() as root:
            edit(root, "content/pages-du-site/actualites.json", masquerFacebook=True, appelTitre="", boutonFacebook="")
            self.assertNotIn("news-callout", render_pages(root, "build_news_page")["/actualites/"])
        with content_sandbox() as root:
            edit(root, "content/pages-du-site/actualites.json", appelTitre="")
            with self.assertRaisesRegex(ContentError, "appelTitre obligatoire"):
                load_content(root, include_drafts=True)

    def test_main_page_eyebrow_and_introduction_are_optional(self):
        with content_sandbox() as root:
            edit(root, "content/pages-du-site/maison.json", rubrique="", introduction="")
            house = render_pages(root, "build_house_page")["/la-maison/"]
            heading = house.split('<header class="page-heading">')[1].split("</header>")[0]
            self.assertNotIn("eyebrow", heading)
            self.assertNotIn("lead", heading)

    def test_page_sections_can_be_hidden(self):
        page = exemple(
            "pages",
            lambda record: page_libre(record) and record["statut"] == "publie"
            and len([section for section in record["sections"] if not section.get("masquee")]) > 1,
        )
        slug = page["slug"]
        page["sections"] = [section for section in page["sections"] if not section.get("masquee")]
        with content_sandbox() as root:
            premiere = page["sections"][0]
            premiere["masquee"] = True
            edit(root, f"content/pages/{slug}.json", sections=page["sections"])
            pages = render_pages(root, "build_editorial_pages", "build_house_page")
            self.assertNotIn(OutilsTexte().texte_brut(premiere["contenu"])[:40], pages[f"/{slug}/"])
            # Le résumé sur « La maison » vient de la première section visible.
            suivante = OutilsTexte().texte_brut(page["sections"][1]["contenu"])
            self.assertIn(suivante[:30], html.unescape(pages["/la-maison/"]))
        with content_sandbox() as root:
            for section in page["sections"]:
                section["masquee"] = True
            edit(root, f"content/pages/{slug}.json", sections=page["sections"])
            with self.assertRaisesRegex(ContentError, f"Page {slug}: toutes les sections sont masquées"):
                load_content(root, include_drafts=True)

    @staticmethod
    def free_section(marque, emplacement=None, **champs):
        """Une section ajoutée reconnaissable à sa marque dans la page rendue."""
        section = {"type": "texte", "titre": f"Intertitre {marque}", "contenu": f"Texte {marque}."}
        if emplacement:
            section["emplacement"] = emplacement
        section.update(champs)
        return section

    def test_free_sections_take_their_place_on_the_home(self):
        livre = exemple("livres", lambda record: record["statut"] == "publie")["slug"]
        with content_sandbox() as root:
            edit(root, "content/pages-du-site/accueil.json", sectionsLibres=[
                self.free_section("BAS", "bas"),
                self.free_section("APRES-BANDEAU", "apres-bandeau"),
                self.free_section("PAR-DEFAUT"),
                self.free_section("APRES-COLLECTIONS", "apres-collections"),
                self.free_section("MASQUEE", "bas", masquee=True),
                self.free_section(
                    "OFFRE", "bas", type="offre", livres=[livre],
                    boutonsPaypal=[{"libelle": "Commander le lot", "hostedButtonId": "ABCDEFGHJK234"}],
                ),
            ])
            html = render_pages(root, "build_home")["/"]
            places = [
                html.index('class="hero"'),
                html.index("Texte APRES-BANDEAU."),
                html.index("home-commercial"),
                html.index("Texte PAR-DEFAUT."),
                html.index("collection-showcase__item"),
                html.index("Texte APRES-COLLECTIONS."),
                html.index("section--ink"),
                html.index("Texte BAS."),
                html.index("Texte OFFRE."),
            ]
            self.assertEqual(sorted(places), places)
            self.assertNotIn("MASQUEE", html)
            self.assertIn('<h2>Intertitre BAS</h2>', html)
            # L’offre montre sa carte de livre et son bouton, comme dans Mes pages.
            self.assertIn(f'href="/livres/{livre}/"', html)
            self.assertIn('value="ABCDEFGHJK234"', html)
            self.assertIn("Commander le lot", html)

    def test_free_sections_surround_the_list_of_each_main_page(self):
        listes = {
            "catalogue": ("build_catalogue", "/catalogue/", "data-book-grid"),
            "personnes": ("build_people_index", "/personnes/", "data-person-grid"),
            "collections": ("build_collections_index", "/collections/", "collection-showcase__item"),
            "actualites": ("build_news_page", "/actualites/", "news-grid"),
            "maison": ("build_house_page", "/la-maison/", "house-grid"),
            "projets": ("build_editorial_pages", "/projets/", "project-card"),
        }
        with content_sandbox() as root:
            for nom in listes:
                edit(root, f"content/pages-du-site/{nom}.json", sectionsLibres=[
                    self.free_section(f"SOUS-{nom}", "apres-liste"),
                    self.free_section(f"DESSUS-{nom}"),
                ])
            builders = sorted({builder for builder, _, _ in listes.values()})
            pages = render_pages(root, *builders)
            for nom, (_, route, liste) in listes.items():
                if route not in pages:
                    continue  # page archivée par la rédaction : rien à placer
                html = pages[route]
                # Une liste vide (aucune actualité, par exemple) n’a pas de grille.
                marques = [f"Texte DESSUS-{nom}.", liste, f"Texte SOUS-{nom}."] if liste in html else [f"Texte DESSUS-{nom}.", f"Texte SOUS-{nom}."]
                places = [html.index(marque) for marque in marques]
                self.assertEqual(sorted(places), places, nom)
            # Sous la liste des actualités, mais au-dessus du bloc Facebook.
            html = pages["/actualites/"]
            if "news-callout" in html:
                self.assertLess(html.index("Texte SOUS-actualites."), html.index("news-callout"))

    def test_free_sections_follow_the_rules_of_page_sections(self):
        livre = exemple("livres", lambda record: record["statut"] == "publie")["slug"]
        cas = (
            ({"emplacement": "apres-liste"}, "accueil", "emplacement de section inconnu « apres-liste »"),
            ({"emplacement": "bas"}, "catalogue", "emplacement de section inconnu « bas »"),
            ({"contenu": " "}, "maison", "Page principale maison: contenu de section obligatoire"),
            ({"type": "texte", "livres": [livre]}, "accueil", "une section « texte » ne porte ni livre"),
            (
                {"type": "offre", "boutonsPaypal": [{"libelle": "Lot", "hostedButtonId": "https://paypal"}]},
                "projets",
                "identifiant du bouton PayPal « Lot » invalide",
            ),
            ({"contenu": "![](content/media/inconnu.webp)"}, "personnes", "texte alternatif obligatoire"),
            ({"contenu": "::: valeur clignotant\nTexte\n:::"}, "collections", "option inconnue"),
        )
        for champs, page, message in cas:
            with self.subTest(page=page, message=message), content_sandbox() as root:
                edit(root, f"content/pages-du-site/{page}.json", sectionsLibres=[self.free_section("X", **champs)])
                with self.assertRaisesRegex(ContentError, re.escape(message)):
                    load_content(root, include_drafts=True)

    # ---- Supprimer une fiche --------------------------------------------------------
    #
    # Decap supprime une fiche publiée directement sur la branche publiée : ce qui la
    # citait encore ne doit pas bloquer la publication suivante.

    def test_deleting_a_book_drops_the_links_to_it(self):
        raw = self.raw
        available = lambda book: book["statut"] == "publie" and book["disponible"]
        # Un livre mis en avant dont la collection a un autre livre disponible.
        candidates = [
            book for book in raw["books"]
            if available(book) and book["miseEnAvantAccueil"]
            and any(other["slug"] != book["slug"] and other["collection"] == book["collection"] and available(other) for other in raw["books"])
        ]
        if not candidates:
            self.skipTest("aucune collection n’a deux livres disponibles")
        book = candidates[0]["slug"]
        page = exemple("pages", lambda record: page_libre(record) and record["statut"] == "publie")
        voisin = exemple("livres", lambda record: record["slug"] != book and record["statut"] == "publie")["slug"]
        with content_sandbox() as root:
            sections = page["sections"]
            sections[0] = {**sections[0], "type": "livres", "livres": [book], "boutonsPaypal": []}
            edit(root, f"content/pages/{page['slug']}.json", sections=sections,
                 liens=[{"type": "livre", "slug": book, "texte": "Le livre"}])
            edit(root, f"content/livres/{voisin}.json", aDecouvrir=[book])
            (root / "content" / "livres" / f"{book}.json").unlink()
            bundle = load_content(root, include_drafts=False)
            retirees = "\n".join(bundle["raw"]["referencesRetirees"])
            self.assertIn(f"Page {page['slug']}: livre supprimé « {book} » retiré", retirees)
            self.assertIn(f"lien vers une livre supprimé « {book} » retiré", retirees)
            self.assertIn(f"Livre {voisin} (À découvrir): livre supprimé « {book} » retiré", retirees)
            # Sa collection garde un livre mis en avant, choisi d’office.
            self.assertIn("aucun livre mis en avant", retirees)
            pages = render_pages(root, "build_editorial_pages")
            self.assertNotIn(f"/livres/{book}/", pages[f"/{page['slug']}/"])

    def test_deleting_a_page_drops_the_links_to_it(self):
        cible = exemple("pages", lambda record: page_libre(record) and record["statut"] == "publie")["slug"]
        autre = exemple("pages", lambda record: page_libre(record) and record["statut"] == "publie" and record["slug"] != cible)
        with content_sandbox() as root:
            sections = autre["sections"]
            sections[0] = {**sections[0], "contenu": f"Voir [la page](/{cible}/)."}
            edit(root, f"content/pages/{autre['slug']}.json", sections=sections,
                 liens=[{"type": "page", "pageCible": cible, "texte": "Lien"}])
            navigation = json.loads((root / "content/reglages/navigation.json").read_text(encoding="utf-8"))
            navigation["liens"].append({"id": "cible", "libelle": "Cible", "url": f"/{cible}/", "visible": True})
            edit(root, "content/reglages/navigation.json", liens=navigation["liens"])
            edit(root, "content/reglages/footer.json", liensNavigation=[{"libelle": "Cible", "url": f"/{cible}/"}])
            (root / "content" / "pages" / f"{cible}.json").unlink()
            pages = render_pages(root, "build_home", "build_editorial_pages", "build_house_page")
            for route, page_html in pages.items():
                self.assertNotIn(f'href="/{cible}/"', page_html, route)
            # Le texte du lien reste, sans lien.
            self.assertIn("Voir la page", pages[f"/{autre['slug']}/"])

    def test_deleted_media_owner_leaves_unused_files_without_blocking(self):
        page = exemple("pages", lambda record: page_libre(record) and record.get("images"))
        image = media_path(page["images"][0])
        with content_sandbox() as root:
            (root / "content" / "pages" / f"{page['slug']}.json").unlink()
            bundle = load_content(root, include_drafts=False)
            self.assertNotIn(image, referenced_media_paths(bundle["raw"]))

    def test_records_others_depend_on_are_guarded(self):
        build_site = load_site_builder()
        with content_sandbox() as root:
            shutil.copytree(ROOT / "frontend", root / "frontend")
            builder = build_site.SiteBuilder(root, root / "dist", include_drafts=False, base_url=None)
            guard = builder.deletion_guard()
        auteur = next(slug for book in self.books for slug in book["auteurs"])
        self.assertIn(auteur, guard["personnes"])
        self.assertIn("Retirez-la d’abord", guard["personnes"][auteur])
        collection = self.books[0]["collection"]
        self.assertIn(collection, guard["collections"])
        self.assertIn("mentions-legales", guard["pages"])
        # Une personne citée par aucun livre ni projet se supprime librement.
        cited = {slug for book in self.books for field in ("auteurs", "illustrateurs", "prefaciers") for slug in book[field]}
        cited |= {slug for project in self.raw["projects"] for field in ("auteurs", "illustrateurs") for slug in project[field]}
        for person in self.people:
            if person["slug"] not in cited:
                self.assertNotIn(person["slug"], guard["personnes"])
        # Sans la garde, la validation refuse toujours un livre sans son auteur.
        with content_sandbox() as root:
            (root / "content" / "personnes" / f"{auteur}.json").unlink()
            with self.assertRaisesRegex(ContentError, f"personne inconnue {auteur}"):
                load_content(root, include_drafts=False)

    def test_legal_page_cannot_be_unpublished(self):
        with content_sandbox() as root:
            edit(root, "content/pages/mentions-legales.json", statut="brouillon")
            with self.assertRaisesRegex(ContentError, "statut publie est obligatoire"):
                load_content(root, include_drafts=True)

    def test_legal_page_keeps_its_address(self):
        # Elle est éditée comme une page de la maison, mais son adresse est figée.
        with content_sandbox() as root:
            # Decap renomme le fichier avec l’adresse.
            edit(root, "content/pages/mentions-legales.json", slug="mentions")
            (root / "content/pages/mentions-legales.json").rename(root / "content/pages/mentions.json")
            with self.assertRaisesRegex(ContentError, "mentions-legales: obligatoire, son adresse est figée"):
                load_content(root, include_drafts=True)

    def test_optional_fields_are_filled_for_the_generator(self):
        for kind, fields in GENERATOR_REQUIRED_FIELDS.items():
            for record in self.bundle[kind]:
                missing = [field for field in fields if field not in record]
                self.assertEqual([], missing, f"{kind}/{record['slug']}")

    def test_a_page_created_with_only_required_fields_can_be_generated(self):
        # Ce qu’écrit l’administration pour « titre, texte, Publier » : ni adresse ni
        # ordre. L’adresse vient du nom de fichier, l’ordre range la page en dernier.
        with content_sandbox() as root:
            page = {
                "titre": "Page minimale",
                "statut": "publie",
                "type": "page",
                "sections": [{"type": "texte", "titre": "", "contenu": "Le contenu minimal saisi depuis l’administration."}],
            }
            (root / "content" / "pages" / "page-minimale.json").write_text(
                json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            bundle = load_content(root, include_drafts=False)
            created = next(item for item in bundle["pages"] if item["slug"] == "page-minimale")
            others = [item["ordre"] for item in bundle["pages"] if item["slug"] != "page-minimale"]
            self.assertGreater(created["ordre"], max(others))
            for field in GENERATOR_REQUIRED_FIELDS["pages"]:
                self.assertIn(field, created)
            self.assertEqual([], created["images"])
            self.assertEqual([], created["liens"])
            self.assertEqual([], created["documents"])

    def test_page_sections_and_links_follow_their_type(self):
        slug = exemple("pages", page_libre)["slug"]
        livre = exemple("livres")["slug"]
        with content_sandbox() as root:
            edit(root, f"content/pages/{slug}.json", liens=[{"type": "email", "texte": "Écrire", "href": "contact@exemple.fr"}])
            page = next(item for item in load_content(root, include_drafts=True)["pages"] if item["slug"] == slug)
            self.assertEqual("mailto:contact@exemple.fr", page["liens"][0]["href"])
        for sections, message in (
            ([{"contenu": "Sans type"}], "type de section attendu"),
            ([{"type": "texte", "contenu": "Texte", "livres": [livre]}], "ne porte ni livre ni bouton"),
        ):
            with self.subTest(message), content_sandbox() as root:
                edit(root, f"content/pages/{slug}.json", sections=sections)
                with self.assertRaisesRegex(ContentError, message):
                    load_content(root, include_drafts=True)

    def test_duplicate_order_is_refused_inside_a_collection(self):
        with content_sandbox() as root:
            books = [json.loads(path.read_text(encoding="utf-8")) for path in (root / "content" / "livres").glob("*.json")]
            listed = [book for book in books if book["statut"] != "archive"]
            pairs = [
                (book, twin) for book in listed for twin in listed
                if book["collection"] == twin["collection"] and book["slug"] != twin["slug"]
            ]
            if not pairs:
                self.skipTest("aucune collection n’a deux livres")
            target, twin = pairs[0]
            edit(root, f"content/livres/{target['slug']}.json", ordre=twin["ordre"])
            with self.assertRaisesRegex(ContentError, "ordre .* utilisé deux fois"):
                load_content(root, include_drafts=False)

    def test_the_same_order_is_allowed_in_two_collections(self):
        with content_sandbox() as root:
            books = [json.loads(path.read_text(encoding="utf-8")) for path in (root / "content" / "livres").glob("*.json")]
            target = next(book for book in books if book["statut"] == "publie")
            taken = {book["ordre"] for book in books if book["collection"] == target["collection"]}
            elsewhere = {book["ordre"] for book in books if book["collection"] != target["collection"]}
            if not elsewhere - taken:
                self.skipTest("aucun rang d’une autre collection n’est libre dans celle-ci")
            free = min(elsewhere - taken)
            edit(root, f"content/livres/{target['slug']}.json", ordre=free)
            bundle = load_content(root, include_drafts=False)
            moved = next(book for book in bundle["books"] if book["slug"] == target["slug"])
            self.assertEqual(free, moved["ordre"])

    def test_duplicate_home_order_is_refused(self):
        with content_sandbox() as root:
            featured = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in (root / "content" / "livres").glob("*.json")
            ]
            first, second = [book for book in featured if book["miseEnAvantAccueil"]][:2]
            edit(root, f"content/livres/{second['slug']}.json", ordreAccueil=first["ordreAccueil"])
            with self.assertRaisesRegex(ContentError, "ordreAccueil .* utilisé deux fois"):
                load_content(root, include_drafts=False)

    def test_a_project_created_with_only_required_fields_can_be_generated(self):
        """Un projet saisi à la va-vite ne doit pas casser la génération.

        Decap n’écrit pas les champs laissés vides : le générateur les lit pourtant
        en accès direct.
        """
        with content_sandbox() as root:
            project = {
                "slug": "un-projet-minimal",
                "titre": "Un projet minimal",
                "statut": "publie",
                "ordre": 500,
            }
            (root / "content" / "projets" / "un-projet-minimal.json").write_text(
                json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            bundle = load_content(root, include_drafts=False)
            created = next(item for item in bundle["projects"] if item["slug"] == "un-projet-minimal")
            for field in ("auteurs", "auteursHorsFiche", "illustrateurs", "illustrateursHorsFiche"):
                self.assertEqual([], created[field])
            self.assertIsNone(created["collection"])
            self.assertIsNone(created["sortiePrevue"])

    def test_a_project_cannot_point_at_an_unknown_person(self):
        projet = exemple("projets")["slug"]
        with content_sandbox() as root:
            edit(root, f"content/projets/{projet}.json", auteurs=["personne-inexistante"])
            with self.assertRaisesRegex(ContentError, "personne inconnue"):
                load_content(root, include_drafts=False)

    def test_a_project_refuses_a_contributor_in_the_wrong_role(self):
        projet = exemple("projets")["slug"]
        personne = exemple("personnes", lambda record: "illustrateur" not in record["roles"])["slug"]
        with content_sandbox() as root:
            edit(root, f"content/projets/{projet}.json", illustrateurs=[personne])
            with self.assertRaisesRegex(ContentError, "n’a pas le rôle illustrateur"):
                load_content(root, include_drafts=False)

    def test_a_contributor_without_a_record_is_accepted_as_plain_text(self):
        projet = exemple("projets", lambda record: record["statut"] == "publie")["slug"]
        illustrateur = exemple(
            "personnes", lambda record: "illustrateur" in record["roles"] and record["statut"] == "publie"
        )["slug"]
        with content_sandbox() as root:
            edit(root, f"content/projets/{projet}.json", auteurs=[], auteursHorsFiche=["Najat Azira"], illustrateurs=[illustrateur])
            bundle = load_content(root, include_drafts=False)
            project = next(item for item in bundle["projects"] if item["slug"] == projet)
            self.assertEqual(["Najat Azira"], project["auteursHorsFiche"])
            self.assertEqual([illustrateur], project["illustrateurs"])

    def test_duplicate_project_order_is_refused(self):
        projets = [
            record for record in map(lambda path: json.loads(path.read_text(encoding="utf-8")), sorted((CONTENT / "projets").glob("*.json")))
            if record["statut"] != "archive"
        ]
        if len(projets) < 2:
            self.skipTest("il faut deux projets")
        with content_sandbox() as root:
            edit(root, f"content/projets/{projets[0]['slug']}.json", ordre=projets[1]["ordre"])
            with self.assertRaisesRegex(ContentError, "ordre .* utilisé deux fois"):
                load_content(root, include_drafts=False)

    def test_an_archived_project_leaves_the_site(self):
        projet = exemple("projets")["slug"]
        with content_sandbox() as root:
            edit(root, f"content/projets/{projet}.json", statut="archive")
            bundle = load_content(root, include_drafts=True)
            self.assertNotIn(projet, {item["slug"] for item in bundle["projects"]})

    def test_seo_text_length_is_bounded(self):
        livre = exemple("livres", lambda record: record["statut"] == "publie")["slug"]
        for field, length in (("titre", 61), ("description", 161)):
            with self.subTest(field=field), content_sandbox() as root:
                edit(root, f"content/livres/{livre}.json", seo={field: "x" * length})
                with self.assertRaisesRegex(ContentError, f"{field} SEO trop long"):
                    load_content(root, include_drafts=False)

    def test_seo_text_at_the_limit_is_accepted(self):
        livre = exemple("livres", lambda record: record["statut"] == "publie")["slug"]
        with content_sandbox() as root:
            edit(root, f"content/livres/{livre}.json", seo={"titre": "x" * 60, "description": "y" * 160})
            bundle = load_content(root, include_drafts=False)
            book = next(item for item in bundle["books"] if item["slug"] == livre)
            self.assertEqual(60, len(book["seo"]["titre"]))

    def test_archived_content_keeps_its_old_addresses(self):
        build_site = load_site_builder()
        with content_sandbox() as root:
            shutil.copytree(ROOT / "frontend", root / "frontend")
            books = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in (root / "content" / "livres").glob("*.json")
            ]
            # Retirer un livre mis en avant, ou le dernier de sa collection,
            # relève d’une autre règle : le témoin doit être un livre ordinaire.
            sizes = collections.Counter(book["collection"] for book in books)
            archived = next(
                book
                for book in books
                if not book["miseEnAvantAccueil"]
                and book["anciensSlugs"]
                and sizes[book["collection"]] > 1
            )
            # Un livre archivé n’est plus référencé par les suggestions des autres.
            for path in (root / "content" / "livres").glob("*.json"):
                record = json.loads(path.read_text(encoding="utf-8"))
                if archived["slug"] in record.get("aDecouvrir", []):
                    record["aDecouvrir"] = [
                        slug for slug in record["aDecouvrir"] if slug != archived["slug"]
                    ]
                    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            edit(root, f"content/livres/{archived['slug']}.json", statut="archive")
            builder = build_site.SiteBuilder(
                root, root / "dist", include_drafts=False, base_url=None
            )
            builder.temp_output.mkdir(parents=True, exist_ok=True)
            builder.build_redirects()
            redirects = (builder.temp_output / ".htaccess").read_text(encoding="utf-8")

            self.assertNotIn(
                archived["slug"], {book["slug"] for book in builder.books}, "le livre reste archivé"
            )
            for old in archived["anciensSlugs"]:
                self.assertIn(f'"/{old.lstrip("/")}" "/catalogue/"', redirects)

    def test_two_generations_cannot_share_the_same_output(self):
        build_site = load_site_builder()
        with content_sandbox() as root:
            shutil.copytree(ROOT / "frontend", root / "frontend")
            first = build_site.SiteBuilder(root, root / "dist", include_drafts=False, base_url=None)
            second = build_site.SiteBuilder(root, root / "dist", include_drafts=False, base_url=None)
            first.acquire_lock()
            try:
                with self.assertRaises(SystemExit) as refused:
                    second.acquire_lock()
                self.assertIn("génération est déjà en cours", str(refused.exception))
            finally:
                first.release_lock()
            # Le verrou libéré, la génération suivante repart normalement.
            second.acquire_lock()
            second.release_lock()

    def test_a_preview_build_is_not_blocked_by_a_production_build(self):
        build_site = load_site_builder()
        with content_sandbox() as root:
            shutil.copytree(ROOT / "frontend", root / "frontend")
            production = build_site.SiteBuilder(root, root / "dist", include_drafts=False, base_url=None)
            preview = build_site.SiteBuilder(
                root, root / "dist-preview", include_drafts=True, base_url=None
            )
            production.acquire_lock()
            try:
                preview.acquire_lock()
                preview.release_lock()
            finally:
                production.release_lock()

    def test_theme_block_declares_only_known_tokens_in_a_stable_order(self):
        load_site_builder()
        feuille = sys.modules["rendu.feuille_de_style"]
        appearance = dict(self.raw["settings"]["apparence"], couleurPrincipale="#0A7A5B", policeTexte="serif-livre")
        self.assertEqual(
            "/* Le thème choisi dans l'administration : content/reglages/apparence.json */\n"
            ":root {\n"
            "  --color-background: #f7f7f4;\n"
            "  --color-surface: #ffffff;\n"
            "  --color-text: #171a18;\n"
            "  --color-muted: #626862;\n"
            "  --color-primary: #0a7a5b;\n"
            "  --color-primary-dark: #963128;\n"
            "  --color-secondary: #3e6b50;\n"
            "  --color-link: #275c7a;\n"
            "  --color-button: #171a18;\n"
            '  --font-heading: Georgia, "Times New Roman", serif;\n'
            '  --font-body: "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;\n'
            "}\n\n",
            feuille.bloc_du_theme(appearance),
        )

    def test_every_allowed_font_is_accepted_and_resolved_by_the_code(self):
        load_site_builder()
        feuille = sys.modules["rendu.feuille_de_style"]
        for font, stack in APPEARANCE_FONTS.items():
            with self.subTest(font):
                appearance = dict(self.raw["settings"]["apparence"], policeTitres=font, policeTexte=font)
                validate_appearance_settings(appearance)
                block = feuille.bloc_du_theme(appearance)
                self.assertIn(f"  --font-heading: {stack};\n", block)
                self.assertIn(f"  --font-body: {stack};\n", block)
                self.assertNotIn(font, block)

    def test_theme_settings_reach_site_css_and_the_asset_version(self):
        build_site = load_site_builder()
        with content_sandbox() as root:
            shutil.copytree(ROOT / "frontend", root / "frontend")
            default = build_site.SiteBuilder(root, root / "dist", include_drafts=False, base_url=None)
            again = build_site.SiteBuilder(root, root / "dist", include_drafts=False, base_url=None)
            self.assertEqual(default.asset_version, again.asset_version, "même thème, même empreinte")

            edit(
                root, "content/reglages/apparence.json",
                couleurPrincipale="#0a7a5b", policeTitres="sans-serif-humaniste",
            )
            themed = build_site.SiteBuilder(root, root / "dist", include_drafts=False, base_url=None)
            themed.prepare_output()
            css = (themed.temp_output / "assets" / "css" / "site.css").read_text(encoding="utf-8")

            self.assertEqual(themed.site_css, css, "l’empreinte et le fichier publié ont la même source")
            self.assertNotEqual(default.asset_version, themed.asset_version)
            self.assertIn("  --color-primary: #0a7a5b;\n", css)
            self.assertIn("  --font-heading: Optima, Candara,", css)
            self.assertNotIn("couleurPrincipale", css)
            self.assertNotIn("policeTitres", css)
            # Le thème suit les valeurs par défaut des tokens et précède les règles.
            self.assertLess(css.index("--color-primary: #c63f32;"), css.index("--color-primary: #0a7a5b;"))
            self.assertLess(css.index("--color-primary: #0a7a5b;"), css.index("box-sizing: border-box;"))

    def test_a_refused_theme_stops_before_anything_is_written(self):
        build_site = load_site_builder()
        with content_sandbox() as root:
            shutil.copytree(ROOT / "frontend", root / "frontend")
            edit(root, "content/reglages/apparence.json", couleurFond="#fff} body { display: none")
            with self.assertRaisesRegex(ValueError, "Réglage apparence: couleurFond"):
                build_site.SiteBuilder(root, root / "dist", include_drafts=False, base_url=None)
            self.assertFalse((root / "dist").exists())
            self.assertFalse((root / ".dist-build").exists())

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

    def test_page_paypal_buttons_are_well_formed(self):
        for page in self.pages:
            for section in page["sections"]:
                for button in section["boutonsPaypal"]:
                    self.assertTrue(button["libelle"].strip(), page["slug"])
                    self.assertRegex(button["hostedButtonId"], r"^[A-Z0-9]{13}$", page["slug"])

    def test_discounted_buttons_never_reuse_a_full_price_one(self):
        """Un bouton de page soldée doit facturer le prix réduit, jamais celui de la fiche.

        L'ancienne page prévenait : « pour bénéficier du prix réduit, vous devez
        impérativement passer commande sur cette page de solde et non sur la page du
        titre. » Confondre les deux ferait payer le plein tarif.
        """
        book_buttons = {
            book["paypalHostedButtonId"]
            for book in self.books
            if book.get("paypalHostedButtonId")
        }
        for page in self.pages:
            for section in page["sections"]:
                for button in section["boutonsPaypal"]:
                    self.assertNotIn(button["hostedButtonId"], book_buttons, page["slug"])

    def test_the_cart_button_carries_its_signed_block(self):
        payment = self.raw["settings"]["paiement"]
        self.assertTrue(payment["libelleVoirPanier"].strip())
        self.assertTrue(payment["panierEncrypted"].startswith("-----BEGIN PKCS7-----"))
        self.assertTrue(payment["panierEncrypted"].endswith("-----END PKCS7-----"))

    def test_every_referenced_media_exists(self):
        # Un fichier cité doit exister. L’inverse ne bloque plus : une fiche supprimée
        # laisse son image et ses PDF, jamais publiés et listés au rapport
        # (« mediasInutilises »).
        referenced = referenced_media(self.raw)
        assets = {
            path.relative_to(ROOT).as_posix()
            for path in (CONTENT / "media").rglob("*")
            if path.is_file()
        }
        self.assertLessEqual(referenced, assets)
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
        # Deux pages n’ont qu’une introduction : leur corps est engendré à partir
        # d’une rubrique. Le plancher de longueur, lui, traque les pages tronquées
        # par la migration de l’ancien site.
        generated = {"actualites", "projets"}
        for page in self.pages:
            self.assertTrue(page["sections"], page["slug"])
            content = " ".join(section["contenu"] for section in page["sections"])
            if page["slug"] not in generated:
                self.assertGreater(len(content), 40, page["slug"])
            self.assertIsNone(forbidden.search(content), page["slug"])



class TextesLisiblesTest(unittest.TestCase):
    def test_aucun_texte_long_sans_paragraphe(self):
        """La migration avait collé des pages entières en un seul bloc — adresses,
        téléphones et liens bout à bout. Un texte de plus de 450 caractères doit
        désormais compter au moins un saut de ligne."""
        content = Path(__file__).resolve().parent.parent / "content"
        champs = {"livres": "description", "personnes": "biographie", "collections": "description",
                  "actualites": "contenu"}
        fautifs = []
        for dossier in ("livres", "personnes", "collections", "actualites", "pages"):
            for fichier in sorted((content / dossier).glob("*.json")):
                data = json.loads(fichier.read_text(encoding="utf-8"))
                textes = [data.get(champs.get(dossier, ""))]
                textes += [section.get("contenu") for section in data.get("sections") or []]
                for texte in textes:
                    if isinstance(texte, str) and len(texte) > 450 and "\n" not in texte:
                        fautifs.append(f"{dossier}/{fichier.stem}")
        self.assertEqual([], fautifs)


if __name__ == "__main__":
    unittest.main()
