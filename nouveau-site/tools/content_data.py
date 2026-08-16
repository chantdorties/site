"""Load and validate the editable JSON content used by the site builder."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any


STATUSES = {"brouillon", "publie"}
ROLES = ("auteur", "illustrateur", "prefacier")
ROLE_SET = set(ROLES)
NEWS_TYPES = {"salon", "parution", "rencontre", "maison"}
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_PATTERN = re.compile(r"^https?://", re.I)
PAYPAL_BUTTON_PATTERN = re.compile(r"^[A-Z0-9]{13}$")
MEDIA_SUFFIXES = {".bmp", ".gif", ".jpeg", ".jpg", ".pdf", ".png", ".tif", ".tiff", ".webp"}
MAX_MEDIA_BYTES = 20 * 1024 * 1024


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


def validate_content(root: Path, raw: dict[str, list[dict[str, Any]]]) -> None:
    books = raw["books"]
    people = raw["people"]
    collections = raw["collections"]
    pages = raw["pages"]
    news = raw["news"]
    people_by_slug = {item["slug"]: item for item in people}
    collections_by_slug = {item["slug"]: item for item in collections}
    books_by_slug = {item["slug"]: item for item in books}
    pages_by_slug = {item["slug"]: item for item in pages}

    for collection in collections:
        validate_status(collection, "Collection")
        require_text(collection, "titre", "Collection")
        require_text(collection, "description", "Collection")

    for person in people:
        validate_status(person, "Personne")
        require_text(person, "nom", "Personne")
        roles = person.get("roles")
        if not isinstance(roles, list) or not roles or not set(roles) <= ROLE_SET:
            raise ContentError(f"Personne {person['slug']}: rôles invalides")
        validate_media(root, person.get("imagePrincipale"), f"Personne {person['slug']}")
        for path in person.get("images", []):
            validate_media(root, path, f"Personne {person['slug']}")

    for book in books:
        validate_status(book, "Livre")
        require_text(book, "titre", "Livre")
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
        for path in [*book.get("illustrations", []), *book.get("extraits", [])]:
            validate_media(root, path, f"Livre {book['slug']}")

    for collection in collections:
        if collection["statut"] == "publie" and not any(
            book["statut"] == "publie" and book["collection"] == collection["slug"]
            for book in books
        ):
            raise ContentError(f"Collection publiée {collection['slug']}: aucun livre publié")

    for page in pages:
        validate_status(page, "Page")
        require_text(page, "titre", "Page")
        sections = page.get("sections")
        if not isinstance(sections, list) or not sections:
            raise ContentError(f"Page {page['slug']}: au moins une section est obligatoire")
        for section in sections:
            if not isinstance(section, dict) or not isinstance(section.get("contenu"), str) or not section["contenu"].strip():
                raise ContentError(f"Page {page['slug']}: contenu de section obligatoire")
        for path in [*page.get("images", []), *page.get("documents", [])]:
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

    for required_slug in ("accueil", "actualites"):
        if pages_by_slug.get(required_slug, {}).get("statut") != "publie":
            raise ContentError(f"Page structurelle {required_slug}: le statut publie est obligatoire")

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


def load_content(root: Path, *, include_drafts: bool) -> dict[str, Any]:
    content_dir = root / "content"
    raw = {
        "books": load_folder(content_dir, "livres"),
        "people": load_folder(content_dir, "personnes"),
        "collections": load_folder(content_dir, "collections"),
        "pages": load_folder(content_dir, "pages"),
        "news": load_folder(content_dir, "actualites"),
    }
    validate_content(root, raw)
    legacy = read_json(root / "config" / "legacy-redirects.json")

    visible = lambda item: include_drafts or item["statut"] == "publie"
    books = [deepcopy(item) for item in raw["books"] if visible(item)]
    people = [deepcopy(item) for item in raw["people"] if visible(item)]
    collections = [deepcopy(item) for item in raw["collections"] if visible(item)]
    pages = [deepcopy(item) for item in raw["pages"]]
    news = [deepcopy(item) for item in raw["news"] if visible(item)]

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

    news.sort(key=lambda item: (item["datePublication"], item["slug"]), reverse=True)
    return {
        "books": books,
        "people": people,
        "collections": collections,
        "pages": pages,
        "news": news,
        "raw": raw,
    }
