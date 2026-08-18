#!/usr/bin/env python3

import collections
import contextlib
import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tools.content_data import ContentError, load_content, media_path, valid_isbn


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


def edit(root, relative, **changes):
    path = root / relative
    record = json.loads(path.read_text(encoding="utf-8"))
    record.update(changes)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def referenced_media(raw):
    paths = set()
    for book in raw["books"]:
        paths.update(filter(None, [book.get("couverture"), *map(media_path, book.get("illustrations", [])), *book.get("extraits", [])]))
    for person in raw["people"]:
        paths.update(filter(None, [person.get("imagePrincipale"), *map(media_path, person.get("images", []))]))
    for page in raw["pages"]:
        paths.update(filter(None, [*map(media_path, page.get("images", [])), *page.get("documents", [])]))
        paths.update(
            link.get("href")
            for link in page.get("liens", [])
            if link.get("type") == "document" and link.get("href")
        )
    for item in raw["news"]:
        paths.update(filter(None, [item.get("image"), item.get("document")]))
    for collection in raw["collections"]:
        paths.update(filter(None, [collection.get("logo")]))
    for kind in ("books", "people", "collections", "pages", "news"):
        paths.update(
            item.get("seo", {}).get("image")
            for item in raw[kind]
            if item.get("seo", {}).get("image")
        )
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
        self.assertEqual(3, schema["version"])
        self.assertEqual({"archive", "brouillon", "publie"}, set(schema["statuts"]))
        self.assertGreater(len(self.books), 0)
        self.assertGreater(len(self.people), 0)
        self.assertGreater(len(self.collections), 0)
        self.assertLessEqual({"accueil", "actualites", "mentions-legales"}, {page["slug"] for page in self.pages})

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
        page_files = {
            path.stem
            for folder in ("pages", "pages-fixes")
            for path in (CONTENT / folder).glob("*.json")
        }
        self.assertEqual({record["slug"] for record in self.pages}, page_files)

    def test_settings_and_fixed_pages_are_present(self):
        self.assertEqual(
            {"accueil", "footer", "navigation", "pages", "paiement", "site"},
            set(self.raw["settings"]),
        )
        fixed_files = {path.stem for path in (CONTENT / "pages-fixes").glob("*.json")}
        self.assertEqual({"accueil", "actualites", "mentions-legales"}, fixed_files)
        self.assertEqual("publie", next(page for page in self.pages if page["slug"] == "accueil")["statut"])
        self.assertEqual("publie", next(page for page in self.pages if page["slug"] == "actualites")["statut"])

    def test_orders_and_home_selections_are_explicit(self):
        for records in (self.books, self.people, self.collections, self.pages):
            for record in records:
                self.assertIsInstance(record["ordre"], int, record["slug"])
                self.assertGreaterEqual(record["ordre"], 0, record["slug"])
        featured = [book for book in self.books if book["miseEnAvantAccueil"]]
        self.assertEqual(len(self.collections), len(featured))
        self.assertEqual(len(featured), len({book["collection"] for book in featured}))
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
            page_path = root / "content" / "pages" / "amis.json"
            page = json.loads(page_path.read_text(encoding="utf-8"))
            page["statut"] = "archive"
            page_path.write_text(json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8")
            for include_drafts in (False, True):
                bundle = load_content(root, include_drafts=include_drafts)
                self.assertNotIn("amis", {item["slug"] for item in bundle["pages"]})

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
                "sections": [{"titre": None, "contenu": "Un contenu éditorial suffisamment complet pour être validé."}],
                "liens": [],
                "images": [],
                "documents": [],
                "anciensSlugs": [],
            }
            path = root / "content" / "pages" / "nouvelle-page.json"
            path.write_text(json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8")
            bundle = load_content(root, include_drafts=True)
            self.assertIn("nouvelle-page", {item["slug"] for item in bundle["pages"]})

    def test_home_and_news_pages_cannot_be_unpublished(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(CONTENT, root / "content", ignore=shutil.ignore_patterns("media"))
            (root / "content" / "media").symlink_to(CONTENT / "media", target_is_directory=True)
            shutil.copytree(ROOT / "config", root / "config")
            page_path = root / "content" / "pages-fixes" / "accueil.json"
            page = json.loads(page_path.read_text(encoding="utf-8"))
            page["statut"] = "brouillon"
            page_path.write_text(json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8")
            with self.assertRaisesRegex(ContentError, "statut publie est obligatoire"):
                load_content(root, include_drafts=True)

    def test_legal_page_cannot_be_unpublished(self):
        with content_sandbox() as root:
            edit(root, "content/pages-fixes/mentions-legales.json", statut="brouillon")
            with self.assertRaisesRegex(ContentError, "statut publie est obligatoire"):
                load_content(root, include_drafts=True)

    def test_optional_fields_are_filled_for_the_generator(self):
        for kind, fields in GENERATOR_REQUIRED_FIELDS.items():
            for record in self.bundle[kind]:
                missing = [field for field in fields if field not in record]
                self.assertEqual([], missing, f"{kind}/{record['slug']}")

    def test_a_page_created_with_only_required_fields_can_be_generated(self):
        with content_sandbox() as root:
            page = {
                "slug": "page-minimale",
                "titre": "Page minimale",
                "statut": "publie",
                "ordre": 500,
                "sections": [{"contenu": "Le contenu minimal saisi depuis l’administration."}],
            }
            (root / "content" / "pages" / "page-minimale.json").write_text(
                json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            bundle = load_content(root, include_drafts=False)
            created = next(item for item in bundle["pages"] if item["slug"] == "page-minimale")
            for field in GENERATOR_REQUIRED_FIELDS["pages"]:
                self.assertIn(field, created)
            self.assertEqual([], created["images"])
            self.assertEqual([], created["liens"])
            self.assertEqual([], created["documents"])

    def test_duplicate_order_is_refused_inside_a_collection(self):
        with content_sandbox() as root:
            books = [json.loads(path.read_text(encoding="utf-8")) for path in (root / "content" / "livres").glob("*.json")]
            target = next(book for book in books if book["slug"] == "ville-rouge")
            twin = next(
                book
                for book in books
                if book["collection"] == target["collection"] and book["slug"] != target["slug"]
            )
            edit(root, "content/livres/ville-rouge.json", ordre=twin["ordre"])
            with self.assertRaisesRegex(ContentError, "ordre .* utilisé deux fois"):
                load_content(root, include_drafts=False)

    def test_the_same_order_is_allowed_in_two_collections(self):
        with content_sandbox() as root:
            books = [json.loads(path.read_text(encoding="utf-8")) for path in (root / "content" / "livres").glob("*.json")]
            target = next(book for book in books if book["slug"] == "ville-rouge")
            taken = {book["ordre"] for book in books if book["collection"] == target["collection"]}
            elsewhere = {book["ordre"] for book in books if book["collection"] != target["collection"]}
            free = min(elsewhere - taken)
            edit(root, "content/livres/ville-rouge.json", ordre=free)
            bundle = load_content(root, include_drafts=False)
            moved = next(book for book in bundle["books"] if book["slug"] == "ville-rouge")
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
        with content_sandbox() as root:
            edit(root, "content/projets/gaia-tome-3.json", auteurs=["personne-inexistante"])
            with self.assertRaisesRegex(ContentError, "personne inconnue"):
                load_content(root, include_drafts=False)

    def test_a_project_refuses_a_contributor_in_the_wrong_role(self):
        with content_sandbox() as root:
            edit(root, "content/projets/gaia-tome-3.json", illustrateurs=["amanda-belassami-sideris"])
            with self.assertRaisesRegex(ContentError, "n’a pas le rôle illustrateur"):
                load_content(root, include_drafts=False)

    def test_a_contributor_without_a_record_is_accepted_as_plain_text(self):
        with content_sandbox() as root:
            bundle = load_content(root, include_drafts=False)
            project = next(item for item in bundle["projects"] if item["slug"] == "hotel-du-nord")
            self.assertEqual(["Najat Azira"], project["auteursHorsFiche"])
            self.assertEqual(["sebastien-boscus"], project["illustrateurs"])

    def test_duplicate_project_order_is_refused(self):
        with content_sandbox() as root:
            edit(root, "content/projets/gaia-tome-3.json", ordre=10)
            with self.assertRaisesRegex(ContentError, "ordre .* utilisé deux fois"):
                load_content(root, include_drafts=False)

    def test_an_archived_project_leaves_the_site(self):
        with content_sandbox() as root:
            edit(root, "content/projets/gaia-tome-3.json", statut="archive")
            bundle = load_content(root, include_drafts=True)
            self.assertNotIn("gaia-tome-3", {item["slug"] for item in bundle["projects"]})

    def test_seo_text_length_is_bounded(self):
        for field, length in (("titre", 61), ("description", 161)):
            with self.subTest(field=field), content_sandbox() as root:
                edit(root, "content/livres/ville-rouge.json", seo={field: "x" * length})
                with self.assertRaisesRegex(ContentError, f"{field} SEO trop long"):
                    load_content(root, include_drafts=False)

    def test_seo_text_at_the_limit_is_accepted(self):
        with content_sandbox() as root:
            edit(root, "content/livres/ville-rouge.json", seo={"titre": "x" * 60, "description": "y" * 160})
            bundle = load_content(root, include_drafts=False)
            book = next(item for item in bundle["books"] if item["slug"] == "ville-rouge")
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


if __name__ == "__main__":
    unittest.main()
