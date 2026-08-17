"""Load and validate the editable JSON content used by the site builder."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any


STATUSES = {"archive", "brouillon", "publie"}
ROLES = ("auteur", "illustrateur", "prefacier")
ROLE_SET = set(ROLES)
NEWS_TYPES = {"salon", "parution", "rencontre", "maison"}
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_PATTERN = re.compile(r"^https?://", re.I)
PAYPAL_BUTTON_PATTERN = re.compile(r"^[A-Z0-9]{13}$")
MEDIA_SUFFIXES = {".bmp", ".gif", ".jpeg", ".jpg", ".pdf", ".png", ".tif", ".tiff", ".webp"}
MAX_MEDIA_BYTES = 20 * 1024 * 1024
SEO_TITLE_MAX = 60
SEO_DESCRIPTION_MAX = 160
# Valeur neutre de ordreAccueil : les livres non mis en avant la partagent tous.
HOME_ORDER_UNSET = 999
SETTING_FILES = ("site", "navigation", "footer", "accueil", "pages", "paiement")

# Champs facultatifs dans l’administration : Decap ne les écrit pas quand ils
# restent vides. Le générateur les lit en accès direct, donc un contenu créé
# depuis l’administration ferait échouer la génération sur un KeyError. On leur
# donne ici la valeur vide attendue, une fois pour toutes.
OPTIONAL_FIELDS: dict[str, dict[str, Any]] = {
    "books": {
        "ageMinimum": None,
        "anciensSlugs": [],
        "auteurs": [],
        "description": None,
        "extraits": [],
        "format": None,
        "illustrateurs": [],
        "illustrations": [],
        "isbn": None,
        "nombrePages": None,
        "prefaciers": [],
        "reliure": None,
        "typeOuvrage": None,
    },
    "people": {
        "anciensSlugs": [],
        "biographie": "",
        "images": [],
        "liensExternes": [],
    },
    "collections": {"anciensSlugs": []},
    "pages": {
        "anciensSlugs": [],
        "documents": [],
        "images": [],
        "liens": [],
    },
    "news": {
        "anciensSlugs": [],
        "document": None,
        "image": None,
        "imageAlt": None,
        "lienExterne": None,
    },
    "projects": {
        "auteurs": [],
        "auteursHorsFiche": [],
        "collection": None,
        "description": None,
        "illustrateurs": [],
        "illustrateursHorsFiche": [],
        "sortiePrevue": None,
    },
}


class ContentError(ValueError):
    """Raised when editable content cannot safely be published."""


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContentError(f"JSON invalide : {path}: {error}") from error


def load_folder(content_dir: Path, folder: str) -> list[dict[str, Any]]:
    records = []
    seen: set[str] = set()
    for path in sorted((content_dir / folder).glob("*.json")):
        record = read_json(path)
        if not isinstance(record, dict):
            raise ContentError(f"{path} doit contenir un objet JSON")
        slug = record.get("slug")
        if not isinstance(slug, str) or not SLUG_PATTERN.fullmatch(slug):
            raise ContentError(f"Slug invalide dans {path}: {slug!r}")
        if path.stem != slug:
            raise ContentError(f"Le fichier {path.name} doit s’appeler {slug}.json")
        if slug in seen:
            raise ContentError(f"Slug dupliqué dans content/{folder}: {slug}")
        seen.add(slug)
        records.append(record)
    return records


def load_settings(content_dir: Path) -> dict[str, dict[str, Any]]:
    settings_dir = content_dir / "reglages"
    return {
        name: read_json(settings_dir / f"{name}.json")
        for name in SETTING_FILES
    }


def require_text(record: dict[str, Any], field: str, kind: str) -> None:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ContentError(f"{kind} {record.get('slug')}: champ {field} obligatoire")


def validate_status(record: dict[str, Any], kind: str) -> None:
    if record.get("statut") not in STATUSES:
        raise ContentError(
            f"{kind} {record.get('slug')}: statut attendu parmi {sorted(STATUSES)}"
        )


def validate_media(root: Path, value: str | None, owner: str) -> None:
    if not value:
        return
    if not isinstance(value, str) or not value.startswith("content/media/"):
        raise ContentError(f"{owner}: chemin média invalide: {value!r}")
    path = root / value
    if not path.is_file():
        raise ContentError(f"{owner}: média introuvable: {value}")
    if path.suffix.lower() not in MEDIA_SUFFIXES:
        raise ContentError(f"{owner}: format média non autorisé: {value}")
    if path.stat().st_size > MAX_MEDIA_BYTES:
        raise ContentError(f"{owner}: média supérieur à 20 Mo: {value}")


def media_path(value: Any) -> str | None:
    """Return a media path from the current object format or a legacy string."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        path = value.get("image")
        return path if isinstance(path, str) else None
    return None


def media_alt(value: Any, fallback: str) -> str:
    if isinstance(value, dict) and isinstance(value.get("alt"), str):
        return value["alt"].strip() or fallback
    return fallback


def validate_media_item(root: Path, value: Any, owner: str) -> None:
    path = media_path(value)
    if not path:
        raise ContentError(f"{owner}: image invalide: {value!r}")
    if isinstance(value, dict):
        alt = value.get("alt")
        if alt is not None and not isinstance(alt, str):
            raise ContentError(f"{owner}: texte alternatif invalide")
    validate_media(root, path, owner)


def validate_order(record: dict[str, Any], kind: str, field: str = "ordre") -> None:
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ContentError(f"{kind} {record.get('slug')}: champ {field} invalide")


def validate_seo(root: Path, record: dict[str, Any], kind: str) -> None:
    seo = record.get("seo")
    if seo is None:
        return
    if not isinstance(seo, dict):
        raise ContentError(f"{kind} {record.get('slug')}: référencement SEO invalide")
    for field, limit in (("titre", SEO_TITLE_MAX), ("description", SEO_DESCRIPTION_MAX)):
        value = seo.get(field)
        if value is None:
            continue
        if not isinstance(value, str):
            raise ContentError(f"{kind} {record.get('slug')}: champ SEO {field} invalide")
        if len(value.strip()) > limit:
            raise ContentError(
                f"{kind} {record.get('slug')}: {field} SEO trop long "
                f"({len(value.strip())} caractères, maximum {limit})"
            )
    validate_media(root, seo.get("image"), f"{kind} {record.get('slug')} (SEO)")


def validate_old_slugs(record: dict[str, Any], kind: str) -> None:
    values = record.get("anciensSlugs", [])
    if not isinstance(values, list):
        raise ContentError(f"{kind} {record.get('slug')}: anciensSlugs doit être une liste")
    for value in values:
        if (
            not isinstance(value, str)
            or not value.strip(" /")
            or "://" in value
            or ".." in value
        ):
            raise ContentError(f"{kind} {record.get('slug')}: ancienne adresse invalide {value!r}")


def validate_settings(root: Path, settings: dict[str, dict[str, Any]]) -> None:
    for name in SETTING_FILES:
        if not isinstance(settings.get(name), dict):
            raise ContentError(f"Réglage content/reglages/{name}.json invalide")

    site = settings["site"]
    for field in ("nom", "nomCourt", "courriel", "facebook", "domaine", "description"):
        require_text(site, field, "Réglage site")
    if "@" not in site["courriel"]:
        raise ContentError("Réglage site: adresse courriel invalide")
    for field in ("facebook", "domaine"):
        if not URL_PATTERN.match(site[field]):
            raise ContentError(f"Réglage site: {field} doit commencer par http:// ou https://")

    navigation = settings["navigation"].get("liens")
    if not isinstance(navigation, list) or not navigation:
        raise ContentError("Réglage navigation: au moins un lien est obligatoire")
    seen_ids: set[str] = set()
    for item in navigation:
        if not isinstance(item, dict):
            raise ContentError("Réglage navigation: lien invalide")
        for field in ("id", "libelle", "url"):
            require_text(item, field, "Lien de navigation")
        validate_order(item, "Lien de navigation")
        if item["id"] in seen_ids:
            raise ContentError(f"Réglage navigation: identifiant dupliqué {item['id']}")
        seen_ids.add(item["id"])
        if not isinstance(item.get("visible"), bool):
            raise ContentError(f"Réglage navigation: visibilité invalide pour {item['id']}")
    search = settings["navigation"].get("recherche")
    if not isinstance(search, dict):
        raise ContentError("Réglage navigation: recherche invalide")
    for field in ("libelle", "url"):
        require_text(search, field, "Recherche")

    footer = settings["footer"]
    for field in (
        "presentation",
        "titreNavigation",
        "titreInformations",
        "libelleFacebook",
        "libelleManuscrits",
        "libellePlan",
        "libelleMentions",
    ):
        require_text(footer, field, "Réglage pied de page")
    links = footer.get("liensNavigation")
    if not isinstance(links, list) or not links:
        raise ContentError("Réglage pied de page: liensNavigation invalide")
    for item in links:
        for field in ("libelle", "url"):
            require_text(item, field, "Lien du pied de page")
        validate_order(item, "Lien du pied de page")

    home = settings["accueil"]
    for field in (
        "heroRubrique",
        "heroTitre",
        "heroAccent",
        "heroAccroche",
        "boutonCatalogue",
        "boutonCollections",
        "titreInformation",
        "collectionsRubrique",
        "collectionsTitre",
        "suivreRubrique",
        "suivreTitre",
        "actualitesRubrique",
        "actualitesTitre",
        "actualitesAction",
        "manuscritsRubrique",
        "manuscritsTitre",
        "manuscritsAction",
    ):
        require_text(home, field, "Réglage accueil")

    page_settings = settings["pages"]
    for name in ("catalogue", "personnes", "collections", "actualites", "maison"):
        value = page_settings.get(name)
        if not isinstance(value, dict):
            raise ContentError(f"Réglage pages: bloc {name} invalide")
        for field in ("rubrique", "titre", "introduction", "descriptionSeo"):
            require_text(value, field, f"Réglage page {name}")
    actualites = page_settings["actualites"]
    for field in ("appelRubrique", "appelTitre", "appelTexte", "boutonFacebook"):
        require_text(actualites, field, "Réglage page actualites")

    payment = settings["paiement"]
    button_id = payment.get("donationHostedButtonId")
    if not isinstance(button_id, str) or not PAYPAL_BUTTON_PATTERN.fullmatch(button_id):
        raise ContentError("Réglage paiement: identifiant du bouton de don PayPal invalide")
    require_text(payment, "libelleDon", "Réglage paiement")


def normalized_isbn(value: str | None) -> str:
    return re.sub(r"[^0-9Xx]", "", value or "").upper()


def valid_isbn(value: str | None) -> bool:
    digits = normalized_isbn(value)
    if not digits:
        return True
    if len(digits) == 10:
        if not re.fullmatch(r"\d{9}[\dX]", digits):
            return False
        total = sum((10 - index) * (10 if digit == "X" else int(digit)) for index, digit in enumerate(digits))
        return total % 11 == 0
    if len(digits) == 13 and digits.isdigit():
        total = sum(int(digit) * (1 if index % 2 == 0 else 3) for index, digit in enumerate(digits[:12]))
        return (10 - total % 10) % 10 == int(digits[-1])
    return False


def validate_unique_orders(raw: dict[str, Any]) -> None:
    """Deux contenus classés au même rang s’afficheraient dans un ordre instable."""

    def check(records: list[dict[str, Any]], kind: str, field: str, scope: str = "") -> None:
        seen: dict[int, str] = {}
        for record in records:
            value = record[field]
            if value in seen:
                where = f" dans {scope}" if scope else ""
                raise ContentError(
                    f"{kind}: {field} {value} utilisé deux fois{where} "
                    f"({seen[value]} et {record['slug']})"
                )
            seen[value] = record["slug"]

    # Un contenu archivé ne s’affiche nulle part : son rang redevient libre.
    def listed(kind: str) -> list[dict[str, Any]]:
        return [record for record in raw[kind] if record["statut"] != "archive"]

    # Les livres sont classés à l’intérieur de leur collection : le même rang
    # peut donc servir une fois par collection.
    by_collection: dict[str, list[dict[str, Any]]] = {}
    for book in listed("books"):
        by_collection.setdefault(book["collection"], []).append(book)
    for collection_slug, books in by_collection.items():
        check(books, "Livre", "ordre", f"la collection {collection_slug}")

    check(
        [book for book in listed("books") if book["miseEnAvantAccueil"]],
        "Livre mis en avant",
        "ordreAccueil",
        "l’accueil",
    )
    check(listed("collections"), "Collection", "ordre")
    check(listed("people"), "Personne", "ordre")
    check(listed("pages"), "Page", "ordre")
    check(listed("projects"), "Projet", "ordre")


def apply_optional_defaults(raw: dict[str, Any]) -> None:
    """Give every omitted optional field its empty value before validation."""
    for kind, defaults in OPTIONAL_FIELDS.items():
        for record in raw[kind]:
            for field, empty in defaults.items():
                record.setdefault(field, deepcopy(empty))


def validate_content(root: Path, raw: dict[str, Any]) -> None:
    books = raw["books"]
    people = raw["people"]
    collections = raw["collections"]
    pages = raw["pages"]
    news = raw["news"]
    projects = raw["projects"]
    settings = raw["settings"]
    validate_settings(root, settings)
    people_by_slug = {item["slug"]: item for item in people}
    collections_by_slug = {item["slug"]: item for item in collections}
    books_by_slug = {item["slug"]: item for item in books}
    pages_by_slug = {item["slug"]: item for item in pages}

    for collection in collections:
        validate_status(collection, "Collection")
        require_text(collection, "titre", "Collection")
        require_text(collection, "description", "Collection")
        validate_order(collection, "Collection")
        validate_seo(root, collection, "Collection")
        validate_old_slugs(collection, "Collection")

    for person in people:
        validate_status(person, "Personne")
        require_text(person, "nom", "Personne")
        validate_order(person, "Personne")
        roles = person.get("roles")
        if not isinstance(roles, list) or not roles or not set(roles) <= ROLE_SET:
            raise ContentError(f"Personne {person['slug']}: rôles invalides")
        validate_media(root, person.get("imagePrincipale"), f"Personne {person['slug']}")
        if person.get("imagePrincipaleAlt") is not None and not isinstance(person["imagePrincipaleAlt"], str):
            raise ContentError(f"Personne {person['slug']}: texte alternatif du portrait invalide")
        for item in person.get("images", []):
            validate_media_item(root, item, f"Personne {person['slug']}")
        validate_seo(root, person, "Personne")
        validate_old_slugs(person, "Personne")

    for book in books:
        validate_status(book, "Livre")
        require_text(book, "titre", "Livre")
        validate_order(book, "Livre")
        validate_order(book, "Livre", "ordreAccueil")
        if not isinstance(book.get("miseEnAvantAccueil"), bool):
            raise ContentError(f"Livre {book['slug']}: miseEnAvantAccueil invalide")
        if not isinstance(book.get("disponible"), bool):
            raise ContentError(f"Livre {book['slug']}: champ disponible obligatoire")
        if book.get("description") is not None and not isinstance(book["description"], str):
            raise ContentError(f"Livre {book['slug']}: description invalide")
        if book.get("collection") not in collections_by_slug:
            raise ContentError(f"Livre {book['slug']}: collection inconnue")
        if not isinstance(book.get("auteurs"), list) or not book["auteurs"]:
            raise ContentError(f"Livre {book['slug']}: au moins un auteur est obligatoire")
        for field, role in (("auteurs", "auteur"), ("illustrateurs", "illustrateur"), ("prefaciers", "prefacier")):
            values = book.get(field, [])
            if not isinstance(values, list):
                raise ContentError(f"Livre {book['slug']}: {field} doit être une liste")
            for person_slug in values:
                person = people_by_slug.get(person_slug)
                if not person:
                    raise ContentError(f"Livre {book['slug']}: personne inconnue {person_slug}")
                if role not in person["roles"]:
                    raise ContentError(f"Livre {book['slug']}: {person_slug} n’a pas le rôle {role}")
                if book["statut"] == "publie" and person["statut"] != "publie":
                    raise ContentError(f"Livre publié {book['slug']}: personne en brouillon {person_slug}")
        collection = collections_by_slug[book["collection"]]
        if book["statut"] == "publie" and collection["statut"] != "publie":
            raise ContentError(f"Livre publié {book['slug']}: collection en brouillon")
        price = book.get("prixEuros")
        if price is not None and (isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0):
            raise ContentError(f"Livre {book['slug']}: prix invalide")
        if not valid_isbn(book.get("isbn")):
            raise ContentError(f"Livre {book['slug']}: ISBN invalide")
        paypal_button_id = book.get("paypalHostedButtonId")
        if paypal_button_id is not None and (
            not isinstance(paypal_button_id, str)
            or not PAYPAL_BUTTON_PATTERN.fullmatch(paypal_button_id)
        ):
            raise ContentError(f"Livre {book['slug']}: identifiant bouton PayPal invalide")
        if book.get("disponible") and not paypal_button_id:
            raise ContentError(f"Livre {book['slug']}: bouton PayPal obligatoire si disponible")
        validate_media(root, book.get("couverture"), f"Livre {book['slug']}")
        if not book.get("couverture"):
            raise ContentError(f"Livre {book['slug']}: couverture obligatoire")
        if book.get("couvertureAlt") is not None and not isinstance(book["couvertureAlt"], str):
            raise ContentError(f"Livre {book['slug']}: texte alternatif de couverture invalide")
        for item in book.get("illustrations", []):
            validate_media_item(root, item, f"Livre {book['slug']}")
        for path in book.get("extraits", []):
            validate_media(root, path, f"Livre {book['slug']}")
        related = book.get("aDecouvrir", [])
        if (
            not isinstance(related, list)
            or len(related) > 4
            or len(related) != len(set(related))
        ):
            raise ContentError(f"Livre {book['slug']}: sélection À découvrir invalide")
        for related_slug in related:
            target = books_by_slug.get(related_slug)
            if not target or related_slug == book["slug"]:
                raise ContentError(f"Livre {book['slug']}: livre lié invalide {related_slug}")
            if book["statut"] == "publie" and target["statut"] != "publie":
                raise ContentError(f"Livre publié {book['slug']}: livre lié non publié {related_slug}")
        validate_seo(root, book, "Livre")
        validate_old_slugs(book, "Livre")

    for collection in collections:
        if collection["statut"] != "publie":
            continue
        published_books = [
            book
            for book in books
            if book["statut"] == "publie" and book["collection"] == collection["slug"]
        ]
        if not published_books:
            raise ContentError(f"Collection publiée {collection['slug']}: aucun livre publié")
        featured = [
            book
            for book in published_books
            if book["miseEnAvantAccueil"] and book["disponible"]
        ]
        if len(featured) != 1:
            raise ContentError(
                f"Collection publiée {collection['slug']}: sélectionner exactement un livre disponible pour l’accueil"
            )

    for page in pages:
        validate_status(page, "Page")
        require_text(page, "titre", "Page")
        validate_order(page, "Page")
        sections = page.get("sections")
        if not isinstance(sections, list) or not sections:
            raise ContentError(f"Page {page['slug']}: au moins une section est obligatoire")
        for section in sections:
            if not isinstance(section, dict) or not isinstance(section.get("contenu"), str) or not section["contenu"].strip():
                raise ContentError(f"Page {page['slug']}: contenu de section obligatoire")
        for item in page.get("images", []):
            validate_media_item(root, item, f"Page {page['slug']}")
        for path in page.get("documents", []):
            validate_media(root, path, f"Page {page['slug']}")
        for link in page.get("liens", []):
            link_type = link.get("type")
            if link_type not in {"document", "email", "externe", "livre", "page"}:
                raise ContentError(f"Page {page['slug']}: type de lien invalide")
            if link_type == "document":
                validate_media(root, link.get("href"), f"Page {page['slug']}")
            elif link_type == "externe" and not URL_PATTERN.match(str(link.get("href", ""))):
                raise ContentError(f"Page {page['slug']}: lien externe invalide")
            elif link_type == "email" and not str(link.get("href", "")).startswith("mailto:"):
                raise ContentError(f"Page {page['slug']}: adresse email invalide")
            elif link_type == "livre":
                target = books_by_slug.get(link.get("slug"))
                if not target or (page["statut"] == "publie" and target["statut"] != "publie"):
                    raise ContentError(f"Page {page['slug']}: livre lié indisponible")
            elif link_type == "page":
                target = pages_by_slug.get(link.get("slug"))
                if not target or (page["statut"] == "publie" and target["statut"] != "publie"):
                    raise ContentError(f"Page {page['slug']}: page liée indisponible")
        validate_seo(root, page, "Page")
        validate_old_slugs(page, "Page")

    for required_slug in ("accueil", "actualites", "mentions-legales"):
        if pages_by_slug.get(required_slug, {}).get("statut") != "publie":
            raise ContentError(f"Page structurelle {required_slug}: le statut publie est obligatoire")
    home_section_ids = {section.get("id") for section in pages_by_slug["accueil"]["sections"]}
    required_home_sections = {
        "information",
        "libraires",
        "particuliers",
        "presentation",
        "soutien",
        "soutien-commandes",
    }
    if home_section_ids != required_home_sections:
        raise ContentError(
            "Page structurelle accueil: les six sections attendues doivent être conservées"
        )

    validate_unique_orders(raw)

    old_addresses: dict[str, str] = {}
    for kind, records in (
        ("livre", books),
        ("personne", people),
        ("collection", collections),
        ("page", pages),
        ("actualité", news),
    ):
        for record in records:
            for value in record.get("anciensSlugs", []):
                normalized = value.strip().lstrip("/").casefold()
                owner = f"{kind} {record['slug']}"
                if normalized in old_addresses and old_addresses[normalized] != owner:
                    raise ContentError(
                        f"Ancienne adresse dupliquée {value!r}: {old_addresses[normalized]} et {owner}"
                    )
                old_addresses[normalized] = owner

    for item in news:
        validate_status(item, "Actualité")
        require_text(item, "titre", "Actualité")
        require_text(item, "resume", "Actualité")
        require_text(item, "contenu", "Actualité")
        if item.get("type") not in NEWS_TYPES:
            raise ContentError(f"Actualité {item['slug']}: type invalide")
        if not isinstance(item.get("datePublication"), str) or not DATE_PATTERN.fullmatch(item["datePublication"]):
            raise ContentError(f"Actualité {item['slug']}: datePublication invalide")
        try:
            date.fromisoformat(item["datePublication"])
        except ValueError as error:
            raise ContentError(f"Actualité {item['slug']}: datePublication invalide") from error
        validate_media(root, item.get("image"), f"Actualité {item['slug']}")
        validate_media(root, item.get("document"), f"Actualité {item['slug']}")
        if item.get("image") and not str(item.get("imageAlt", "")).strip():
            raise ContentError(f"Actualité {item['slug']}: texte alternatif de l’image obligatoire")
        if item.get("lienExterne") and not URL_PATTERN.match(item["lienExterne"]):
            raise ContentError(f"Actualité {item['slug']}: lienExterne invalide")
        validate_seo(root, item, "Actualité")
        validate_old_slugs(item, "Actualité")

    for project in projects:
        validate_status(project, "Projet")
        require_text(project, "titre", "Projet")
        validate_order(project, "Projet")
        for field in ("description", "sortiePrevue"):
            value = project.get(field)
            if value is not None and not isinstance(value, str):
                raise ContentError(f"Projet {project['slug']}: champ {field} invalide")
        collection_slug = project.get("collection")
        if collection_slug is not None:
            collection = collections_by_slug.get(collection_slug)
            if not collection:
                raise ContentError(f"Projet {project['slug']}: collection inconnue {collection_slug}")
            if project["statut"] == "publie" and collection["statut"] != "publie":
                raise ContentError(f"Projet publié {project['slug']}: collection non publiée")
        # Un intervenant tient soit à une fiche existante, soit à un simple nom : les
        # auteurs des livres à paraître n’ont pas toujours de fiche au moment du projet.
        for field, role in (("auteurs", "auteur"), ("illustrateurs", "illustrateur")):
            values = project.get(field, [])
            if not isinstance(values, list):
                raise ContentError(f"Projet {project['slug']}: {field} doit être une liste")
            for person_slug in values:
                person = people_by_slug.get(person_slug)
                if not person:
                    raise ContentError(f"Projet {project['slug']}: personne inconnue {person_slug}")
                if role not in person["roles"]:
                    raise ContentError(f"Projet {project['slug']}: {person_slug} n’a pas le rôle {role}")
                if project["statut"] == "publie" and person["statut"] != "publie":
                    raise ContentError(f"Projet publié {project['slug']}: personne non publiée {person_slug}")
        for field in ("auteursHorsFiche", "illustrateursHorsFiche"):
            values = project.get(field, [])
            if not isinstance(values, list):
                raise ContentError(f"Projet {project['slug']}: {field} doit être une liste")
            for name in values:
                if not isinstance(name, str) or not name.strip():
                    raise ContentError(f"Projet {project['slug']}: nom vide dans {field}")


def load_content(root: Path, *, include_drafts: bool) -> dict[str, Any]:
    content_dir = root / "content"
    raw = {
        "books": load_folder(content_dir, "livres"),
        "people": load_folder(content_dir, "personnes"),
        "collections": load_folder(content_dir, "collections"),
        "pages": [
            *load_folder(content_dir, "pages-fixes"),
            *load_folder(content_dir, "pages"),
        ],
        "news": load_folder(content_dir, "actualites"),
        "projects": load_folder(content_dir, "projets"),
        "settings": load_settings(content_dir),
    }
    apply_optional_defaults(raw)
    page_slugs = [page["slug"] for page in raw["pages"]]
    if len(page_slugs) != len(set(page_slugs)):
        raise ContentError("Slug de page dupliqué entre pages-fixes et pages")
    validate_content(root, raw)
    legacy = read_json(root / "config" / "legacy-redirects.json")

    visible = lambda item: item["statut"] == "publie" or (
        include_drafts and item["statut"] == "brouillon"
    )
    books = [deepcopy(item) for item in raw["books"] if visible(item)]
    people = [deepcopy(item) for item in raw["people"] if visible(item)]
    collections = [deepcopy(item) for item in raw["collections"] if visible(item)]
    pages = [deepcopy(item) for item in raw["pages"] if visible(item)]
    news = [deepcopy(item) for item in raw["news"] if visible(item)]
    projects = [deepcopy(item) for item in raw["projects"] if visible(item)]

    collections.sort(key=lambda item: (item["ordre"], item["slug"]))
    books.sort(key=lambda item: (item["ordre"], item["titre"].casefold(), item["slug"]))
    people.sort(key=lambda item: (item["ordre"], item["nom"].casefold(), item["slug"]))
    pages.sort(key=lambda item: (item["ordre"], item["titre"].casefold(), item["slug"]))
    projects.sort(key=lambda item: (item["ordre"], item["titre"].casefold(), item["slug"]))

    books_by_slug = {item["slug"]: item for item in books}
    people_by_slug = {item["slug"]: item for item in people}
    for book in books:
        price = book.pop("prixEuros", None)
        book["prixCentimes"] = round(price * 100) if price is not None else None
        book["isbnValide"] = valid_isbn(book.get("isbn"))
        book["aVerifier"] = book["statut"] == "brouillon"
        book["source"] = {"anciennePage": legacy["livres"].get(book["slug"])}

    for person in people:
        person["livres"] = {role: [] for role in ROLES}
        person["aVerifier"] = person["statut"] == "brouillon"
    for book in books:
        for field, role in (("auteurs", "auteur"), ("illustrateurs", "illustrateur"), ("prefaciers", "prefacier")):
            for person_slug in book.get(field, []):
                if person_slug in people_by_slug:
                    people_by_slug[person_slug]["livres"][role].append(book["slug"])

    for collection in collections:
        collection["livres"] = [
            slug for slug, book in books_by_slug.items() if book["collection"] == collection["slug"]
        ]
        collection["nombreLivres"] = len(collection["livres"])
        collection["sourcePage"] = legacy["collections"].get(collection["slug"])

    for page in pages:
        page["aVerifier"] = page["statut"] == "brouillon"
        page["source"] = {"anciennePage": legacy["pages"].get(page["slug"])}

    for project in projects:
        project["aVerifier"] = project["statut"] == "brouillon"

    news.sort(key=lambda item: (item["datePublication"], item["slug"]), reverse=True)
    return {
        "books": books,
        "people": people,
        "collections": collections,
        "pages": pages,
        "news": news,
        "projects": projects,
        "settings": deepcopy(raw["settings"]),
        "legacy": legacy,
        "raw": raw,
    }
