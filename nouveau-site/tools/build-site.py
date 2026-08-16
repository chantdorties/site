#!/usr/bin/env python3
"""Generate the public Chant d'orties website from the editable JSON content."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import html
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from PIL import Image, ImageFile, ImageOps

from content_data import load_content, media_alt, media_path


ImageFile.LOAD_TRUNCATED_IMAGES = True


PDFINFO_BINARY = "/usr/bin/pdfinfo" if Path("/usr/bin/pdfinfo").is_file() else shutil.which("pdfinfo")
GHOSTSCRIPT_BINARY = "/usr/bin/gs" if Path("/usr/bin/gs").is_file() else shutil.which("gs")

ROLE_LABELS = {
    "auteur": "Auteur",
    "illustrateur": "Illustrateur",
    "prefacier": "Préfacier",
}

TYPE_LABELS = {
    "album": "Album",
    "album-jeunesse": "Album jeunesse",
    "mini-roman": "Mini roman",
    "mini-roman-jeunesse": "Mini roman jeunesse",
    "nouvelles": "Nouvelles",
    "recueil-de-nouvelles": "Recueil de nouvelles",
    "roman": "Roman",
    "roman-jeunesse": "Roman jeunesse",
    "texte-illustre": "Texte illustré",
}

NEWS_TYPE_LABELS = {
    "salon": "Salon",
    "parution": "Parution",
    "rencontre": "Rencontre",
    "maison": "Vie de la maison",
}

ICONS = {
    "arrow-right": '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
    "arrow-up": '<path d="m18 15-6-6-6 6"/>',
    "external": '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    "file": '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5z"/><polyline points="14 2 14 8 20 8"/>',
    "heart": '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
    "mail": '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    "menu": '<line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "shopping-cart": '<circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h7.78a2 2 0 0 0 1.95-1.57L20.05 7H5.12"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
}


def e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def slugify(value: str) -> str:
    normalized = value.lower().replace("’", "'")
    normalized = "".join(
        character
        for character in __import__("unicodedata").normalize("NFKD", normalized)
        if not __import__("unicodedata").combining(character)
    )
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-") or "fichier"


def icon(name: str, *, label: str | None = None) -> str:
    title = f"<title>{e(label)}</title>" if label else ""
    hidden = "" if label else ' aria-hidden="true"'
    return (
        f'<svg class="icon" viewBox="0 0 24 24"{hidden} '
        f'focusable="false">{title}{ICONS[name]}</svg>'
    )


def monogram(name: str) -> str:
    words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+", name)
    return "".join(word[0].upper() for word in words[:2]) or "?"


def format_price(cents: int | None) -> str | None:
    if cents is None:
        return None
    euros, remainder = divmod(cents, 100)
    return f"{euros} €" if remainder == 0 else f"{euros},{remainder:02d} €"


def truncate(value: str, maximum: int = 158) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= maximum:
        return value
    return value[: maximum - 1].rsplit(" ", 1)[0] + "…"


def absolute_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


class SiteBuilder:
    def __init__(
        self,
        root: Path,
        output: Path,
        *,
        include_drafts: bool,
        base_url: str | None,
    ) -> None:
        self.root = root.resolve()
        self.output = output.resolve()
        self.temp_output = self.output.with_name(f".{self.output.name}-build")
        self.include_drafts = include_drafts
        self.content_dir = self.root / "content"
        self.frontend_dir = self.root / "frontend"
        report_name = "site-build-preview.json" if include_drafts else "site-build.json"
        self.report_path = self.root / "reports" / report_name
        self.template = (self.frontend_dir / "templates" / "base.html").read_text(encoding="utf-8")
        asset_digest = hashlib.sha256()
        for asset in ("assets/css/site.css", "assets/js/site.js"):
            asset_digest.update((self.frontend_dir / asset).read_bytes())
        self.asset_version = asset_digest.hexdigest()[:12]

        content = load_content(self.root, include_drafts=include_drafts)
        self.books = content["books"]
        self.people = content["people"]
        self.collections = content["collections"]
        self.pages = content["pages"]
        self.news = content["news"]
        self.raw = content["raw"]
        self.legacy = content["legacy"]
        self.settings = content["settings"]
        self.site_settings = self.settings["site"]
        self.navigation_settings = self.settings["navigation"]
        self.footer_settings = self.settings["footer"]
        self.home_settings = self.settings["accueil"]
        self.page_settings = self.settings["pages"]
        self.payment_settings = self.settings["paiement"]
        self.resolve_page_counts()
        self.base_url = (base_url or self.site_settings["domaine"]).rstrip("/")
        self.books_by_slug = {book["slug"]: book for book in self.books}
        self.people_by_slug = {person["slug"]: person for person in self.people}
        self.collections_by_slug = {item["slug"]: item for item in self.collections}
        self.pages_by_slug = {page["slug"]: page for page in self.pages}

        self.cover_media: dict[str, dict[str, str]] = {}
        self.person_media: dict[str, dict[str, str]] = {}
        self.person_gallery_media: dict[str, str] = {}
        self.illustration_media: dict[str, str] = {}
        self.page_image_media: dict[str, str] = {}
        self.news_image_media: dict[str, str] = {}
        self.seo_image_media: dict[str, str] = {}
        self.document_media: dict[str, str] = {}
        self.pdf_hashes: dict[str, str] = {}
        self.skipped_documents: list[str] = []
        self.generated_routes: list[str] = []
        self.media_stats = {
            "images": 0,
            "documents": 0,
            "compressedDocuments": 0,
            "skippedDocuments": 0,
        }

    def resolve_page_counts(self) -> None:
        """Remplace le jeton {nombre} des réglages par le compte réel.

        Les libellés de rubrique annoncent des quantités (« 64 ouvrages »). Les
        figer dans les réglages les rendrait faux dès le premier ajout depuis
        l’administration, sans que personne ne s’en aperçoive.
        """
        counts = {
            "catalogue": len(self.books),
            "personnes": len(self.people),
            "collections": len(self.collections),
            "actualites": len(self.news),
            "maison": len(self.published_editorial_pages()),
        }
        for block, count in counts.items():
            labels = self.page_settings[block]
            for field, value in labels.items():
                if isinstance(value, str) and "{nombre}" in value:
                    labels[field] = value.replace("{nombre}", str(count))

    def validate_source(self) -> None:
        for required_page in ("accueil", "actualites"):
            if required_page not in self.pages_by_slug:
                raise ValueError(f"Page obligatoire absente : {required_page}")
        for book in self.books:
            if not (self.root / book["couverture"]).is_file():
                raise FileNotFoundError(book["couverture"])

    def acquire_lock(self) -> None:
        """Interdit deux générations simultanées vers la même sortie.

        Le serveur de développement régénère le site à chaque enregistrement et
        partage ce dossier temporaire avec « make build ». Sans verrou, les deux
        générations se détruisent mutuellement en pleine écriture.
        """
        self.lock_path = self.temp_output.with_name(f"{self.temp_output.name}.lock")
        self.lock_file = self.lock_path.open("w")
        try:
            fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.lock_file.close()
            raise SystemExit(
                f"Une génération est déjà en cours vers {self.output.name}/. "
                "Arrêter « make dev » ou « make admin » avant de relancer la génération."
            ) from None

    def release_lock(self) -> None:
        fcntl.flock(self.lock_file, fcntl.LOCK_UN)
        self.lock_file.close()
        self.lock_path.unlink(missing_ok=True)

    def prepare_output(self) -> None:
        if self.temp_output.exists():
            shutil.rmtree(self.temp_output)
        self.temp_output.mkdir(parents=True)
        shutil.copytree(
            self.frontend_dir / "assets" / "css",
            self.temp_output / "assets" / "css",
        )
        shutil.copytree(
            self.frontend_dir / "assets" / "js",
            self.temp_output / "assets" / "js",
        )
        shutil.copytree(
            self.frontend_dir / "assets" / "images",
            self.temp_output / "assets" / "images",
        )
        shutil.copytree(
            self.frontend_dir / "admin",
            self.temp_output / "admin",
        )

    def finish_output(self) -> None:
        if self.output.exists():
            shutil.rmtree(self.output)
        self.temp_output.replace(self.output)

    def save_webp(self, source: Path, destination: Path, max_size: tuple[int, int]) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as raw_image:
            raw_image.seek(0)
            image = ImageOps.exif_transpose(raw_image)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            if image.mode not in {"RGB", "RGBA"}:
                image = image.convert("RGBA" if "transparency" in image.info else "RGB")
            image.save(destination, "WEBP", quality=83, method=6)
        self.media_stats["images"] += 1

    def optimize_images(self) -> None:
        for book in self.books:
            source = self.root / book["couverture"]
            small = self.temp_output / "assets" / "media" / "covers" / f"{book['slug']}-480.webp"
            large = self.temp_output / "assets" / "media" / "covers" / f"{book['slug']}-900.webp"
            self.save_webp(source, small, (480, 900))
            self.save_webp(source, large, (900, 1400))
            self.cover_media[book["slug"]] = {
                "small": f"/assets/media/covers/{small.name}",
                "large": f"/assets/media/covers/{large.name}",
            }

            for index, item in enumerate(book["illustrations"], start=1):
                path = media_path(item)
                if not path:
                    continue
                source = self.root / path
                destination = (
                    self.temp_output
                    / "assets"
                    / "media"
                    / "illustrations"
                    / book["slug"]
                    / f"{index:02d}.webp"
                )
                self.save_webp(source, destination, (1600, 1600))
                self.illustration_media[path] = (
                    f"/assets/media/illustrations/{book['slug']}/{destination.name}"
                )

        for person in self.people:
            image_path = person.get("imagePrincipale")
            if image_path:
                source = self.root / image_path
                small = self.temp_output / "assets" / "media" / "people" / f"{person['slug']}-480.webp"
                large = self.temp_output / "assets" / "media" / "people" / f"{person['slug']}-900.webp"
                self.save_webp(source, small, (480, 720))
                self.save_webp(source, large, (900, 1200))
                self.person_media[person["slug"]] = {
                    "small": f"/assets/media/people/{small.name}",
                    "large": f"/assets/media/people/{large.name}",
                }
            for index, item in enumerate(person["images"], start=1):
                path = media_path(item)
                if not path:
                    continue
                destination = (
                    self.temp_output
                    / "assets"
                    / "media"
                    / "people"
                    / person["slug"]
                    / f"{index:02d}.webp"
                )
                self.save_webp(self.root / path, destination, (1400, 1400))
                self.person_gallery_media[path] = (
                    f"/assets/media/people/{person['slug']}/{destination.name}"
                )

        for page in self.pages:
            if page["slug"] == "actualites":
                continue
            if page["aVerifier"] and not self.include_drafts:
                continue
            for index, item in enumerate(page["images"], start=1):
                path = media_path(item)
                if not path:
                    continue
                source = self.root / path
                destination = (
                    self.temp_output
                    / "assets"
                    / "media"
                    / "pages"
                    / page["slug"]
                    / f"{index:02d}.webp"
                )
                self.save_webp(source, destination, (1400, 1400))
                self.page_image_media[path] = f"/assets/media/pages/{page['slug']}/{destination.name}"

        for item in self.news:
            image_path = item.get("image")
            if not image_path:
                continue
            source = self.root / image_path
            destination = self.temp_output / "assets" / "media" / "news" / f"{item['slug']}.webp"
            self.save_webp(source, destination, (1200, 900))
            self.news_image_media[item["slug"]] = f"/assets/media/news/{destination.name}"

        seo_records = [*self.books, *self.people, *self.collections, *self.pages, *self.news]
        for item in seo_records:
            source_path = item.get("seo", {}).get("image")
            if not source_path or source_path in self.seo_image_media:
                continue
            source = self.root / source_path
            digest = hashlib.sha256(source_path.encode("utf-8")).hexdigest()[:10]
            destination = self.temp_output / "assets" / "media" / "social" / f"{item['slug']}-{digest}.webp"
            self.save_webp(source, destination, (1200, 630))
            self.seo_image_media[source_path] = f"/assets/media/social/{destination.name}"

    def copy_pdf(self, relative_path: str) -> str | None:
        if relative_path in self.document_media:
            return self.document_media[relative_path]
        source = self.root / relative_path
        if not PDFINFO_BINARY:
            raise RuntimeError("pdfinfo est nécessaire pour valider les documents PDF")
        validation = subprocess.run(
            [PDFINFO_BINARY, str(source)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
        )
        if validation.returncode != 0:
            self.media_stats["skippedDocuments"] += 1
            self.skipped_documents.append(relative_path)
            return None
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        if source_hash in self.pdf_hashes:
            url = self.pdf_hashes[source_hash]
            self.document_media[relative_path] = url
            return url

        stem = slugify(source.stem.replace("documents-", ""))[:58]
        filename = f"{stem}-{source_hash[:10]}.pdf"
        destination = self.temp_output / "assets" / "media" / "documents" / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        candidate = destination.with_suffix(".compressed.pdf")
        chosen_source = source

        if source.stat().st_size > 8 * 1024 * 1024:
            previous = self.output / destination.relative_to(self.temp_output)
            if previous.is_file() and previous.stat().st_size < source.stat().st_size:
                previous_validation = subprocess.run(
                    [PDFINFO_BINARY, str(previous)],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=30,
                )
                if previous_validation.returncode == 0:
                    chosen_source = previous
            if chosen_source == source:
                if not GHOSTSCRIPT_BINARY:
                    raise RuntimeError("Ghostscript est nécessaire pour compresser les PDF lourds")
                command = [
                    GHOSTSCRIPT_BINARY,
                    "-sDEVICE=pdfwrite",
                    "-dCompatibilityLevel=1.4",
                    "-dPDFSETTINGS=/ebook",
                    "-dDetectDuplicateImages=true",
                    "-dCompressFonts=true",
                    "-dNOPAUSE",
                    "-dQUIET",
                    "-dBATCH",
                    f"-sOutputFile={candidate}",
                    str(source),
                ]
                result = subprocess.run(command, check=False, timeout=180)
                if result.returncode == 0 and candidate.is_file() and candidate.stat().st_size < source.stat().st_size:
                    chosen_source = candidate
            if chosen_source != source:
                self.media_stats["compressedDocuments"] += 1

        shutil.copy2(chosen_source, destination)
        candidate.unlink(missing_ok=True)
        url = f"/assets/media/documents/{filename}"
        self.pdf_hashes[source_hash] = url
        self.document_media[relative_path] = url
        self.media_stats["documents"] += 1
        return url

    def prepare_documents(self) -> None:
        for book in self.books:
            for path in book["extraits"]:
                self.copy_pdf(path)
        for page in self.pages:
            if page["aVerifier"] and not self.include_drafts:
                continue
            for path in page["documents"]:
                self.copy_pdf(path)
        for item in self.news:
            if item.get("document"):
                self.copy_pdf(item["document"])

    def person_names(self, slugs: list[str]) -> list[str]:
        return [self.people_by_slug[slug]["nom"] for slug in slugs]

    def write_public_data(self) -> None:
        public_books = []
        for book in self.books:
            public_books.append(
                {
                    "slug": book["slug"],
                    "titre": book["titre"],
                    "ordre": book["ordre"],
                    "collection": book["collection"],
                    "collectionOrdre": self.collections_by_slug[book["collection"]]["ordre"],
                    "typeOuvrage": book["typeOuvrage"],
                    "ageMinimum": book["ageMinimum"],
                    "auteurNoms": self.person_names(book["auteurs"]),
                    "illustrateurNoms": self.person_names(book["illustrateurs"]),
                    "prixCentimes": book["prixCentimes"],
                    "disponible": book["disponible"],
                    "couverture": self.cover_media[book["slug"]]["small"],
                    "couvertureAlt": book.get("couvertureAlt") or f"Couverture de {book['titre']}",
                }
            )

        public_people = []
        for person in self.people:
            related = {
                book_slug
                for role_books in person["livres"].values()
                for book_slug in role_books
            }
            public_people.append(
                {
                    "slug": person["slug"],
                    "nom": person["nom"],
                    "ordre": person["ordre"],
                    "roles": person["roles"],
                    "imagePrincipale": self.person_media.get(person["slug"], {}).get("small"),
                    "imagePrincipaleAlt": person.get("imagePrincipaleAlt") or f"Portrait de {person['nom']}",
                    "monogram": monogram(person["nom"]),
                    "nombreLivres": len(related),
                }
            )

        public_collections = [
            {
                "slug": item["slug"],
                "titre": item["titre"],
                "description": item["description"],
                "nombreLivres": item["nombreLivres"],
            }
            for item in self.collections
        ]
        write_json(self.temp_output / "data" / "livres.json", public_books)
        write_json(self.temp_output / "data" / "personnes.json", public_people)
        write_json(self.temp_output / "data" / "collections.json", public_collections)

    def render_nav(self, active: str, *, mobile: bool = False) -> str:
        links = []
        navigation = sorted(
            (item for item in self.navigation_settings["liens"] if item["visible"]),
            key=lambda item: (item["ordre"], item["id"]),
        )
        for item in navigation:
            current = ' aria-current="page"' if item["id"] == active else ""
            links.append(
                f'<a class="nav-link" href="{e(item["url"])}"{current}>'
                f'{e(item["libelle"])}</a>'
            )
        search_settings = self.navigation_settings["recherche"]
        search = (
            f'<a class="nav-link" href="{e(search_settings["url"])}">'
            f'{e(search_settings["libelle"])}</a>'
            if mobile
            else (
                f'<a class="icon-button" href="{e(search_settings["url"])}" '
                f'title="{e(search_settings["libelle"])}" '
                f'aria-label="{e(search_settings["libelle"])}">'
                f'{icon("search")}</a>'
            )
        )
        return "".join(links) + search

    def render_header(self, active: str) -> str:
        short_name = self.site_settings["nomCourt"]
        if " " in short_name:
            name_start, name_accent = short_name.rsplit(" ", 1)
        else:
            name_start, name_accent = short_name, ""
        return f"""
<header class="site-header">
  <div class="container header-inner">
    <a class="wordmark" href="/" aria-label="{e(self.site_settings['nom'])}, accueil">
      <img class="site-logo" src="/assets/images/chantdorties-logo.webp" alt="" width="245" height="241">
      <span class="wordmark__text">{e(name_start)} <span class="wordmark__accent">{e(name_accent)}</span></span>
    </a>
    <nav class="primary-nav" aria-label="Navigation principale">
      {self.render_nav(active)}
    </nav>
    <button class="icon-button menu-button" type="button" data-menu-button
      aria-expanded="false" aria-controls="navigation-mobile" aria-label="Ouvrir le menu" title="Ouvrir le menu">
      <span class="menu-button__open">{icon("menu")}</span>
      <span class="menu-button__close">{icon("x")}</span>
    </button>
  </div>
</header>
<nav class="mobile-nav" id="navigation-mobile" data-mobile-nav aria-label="Navigation mobile" hidden>
  {self.render_nav(active, mobile=True)}
</nav>""".strip()

    def render_footer(self) -> str:
        legal_link = ""
        legal_page = self.pages_by_slug.get("mentions-legales")
        if legal_page and (self.include_drafts or not legal_page["aVerifier"]):
            legal_link = (
                '<li><a href="/mentions-legales/">'
                f'{e(self.footer_settings["libelleMentions"])}</a></li>'
            )
        navigation_links = "".join(
            f'<li><a href="{e(item["url"])}">{e(item["libelle"])}</a></li>'
            for item in sorted(
                self.footer_settings["liensNavigation"],
                key=lambda item: (item["ordre"], item["url"]),
            )
        )
        email = self.site_settings["courriel"]
        facebook = self.site_settings["facebook"]
        return f"""
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-identity">
        <img class="footer-logo" src="/assets/images/chantdorties-logo.webp" alt="" width="245" height="241" loading="lazy">
        <div>
          <p class="footer-brand">{e(self.site_settings['nom'])}</p>
          <p class="footer-intro">{e(self.footer_settings['presentation'])}</p>
        </div>
      </div>
      <div>
        <h2 class="footer-title">{e(self.footer_settings['titreNavigation'])}</h2>
        <ul class="footer-links">
          {navigation_links}
        </ul>
      </div>
      <div>
        <h2 class="footer-title">{e(self.footer_settings['titreInformations'])}</h2>
        <ul class="footer-links">
          <li><a href="mailto:{e(email)}">{e(email)}</a></li>
          <li><a href="{e(facebook)}" target="_blank" rel="noopener noreferrer">{e(self.footer_settings['libelleFacebook'])} {icon("external")}</a></li>
          <li><a href="/manuscrits/">{e(self.footer_settings['libelleManuscrits'])}</a></li>
          <li><a href="/plan-du-site/">{e(self.footer_settings['libellePlan'])}</a></li>
          {legal_link}
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© {datetime.now().year} {e(self.site_settings['nom'])}</span>
      <button class="icon-button back-to-top" type="button" data-back-to-top hidden title="Revenir en haut">
        {icon("arrow-up", label="Revenir en haut")}
      </button>
    </div>
  </div>
</footer>""".strip()

    def render_page(
        self,
        *,
        title: str,
        description: str,
        route: str,
        content: str,
        active: str,
        body_class: str = "",
        draft: bool = False,
        scripts: list[str] | None = None,
        og_type: str = "website",
        og_image: str | None = None,
        structured_data: dict[str, Any] | None = None,
    ) -> str:
        page_title = title if route == "/" else f"{title} | {self.site_settings['nom']}"
        canonical_url = absolute_url(self.base_url, route)
        canonical = f'<link rel="canonical" href="{e(canonical_url)}">'
        robots = '<meta name="robots" content="noindex, nofollow">' if draft else ""
        og_image_tag = ""
        if og_image:
            og_image_tag = f'<meta property="og:image" content="{e(absolute_url(self.base_url, og_image))}">'
        structured = ""
        if structured_data:
            structured = (
                '<script type="application/ld+json">'
                + json.dumps(structured_data, ensure_ascii=False).replace("</", "<\\/")
                + "</script>"
            )
        page_scripts = "".join(
            f'<script type="module" src="{e(script)}"></script>' for script in (scripts or [])
        )
        draft_notice = ""
        if draft:
            draft_notice = (
                '<div class="draft-notice"><div class="container">'
                "Prévisualisation : ce contenu doit être validé avant publication."
                "</div></div>"
            )

        replacements = {
            "{{page_title}}": e(page_title),
            "{{description}}": e(truncate(description)),
            "{{robots}}": robots,
            "{{canonical}}": canonical,
            "{{og_type}}": e(og_type),
            "{{og_image}}": og_image_tag,
            "{{structured_data}}": structured,
            "{{body_class}}": e(body_class),
            "{{asset_version}}": self.asset_version,
            "{{header}}": self.render_header(active),
            "{{content}}": draft_notice + content,
            "{{footer}}": self.render_footer(),
            "{{page_scripts}}": page_scripts,
        }
        result = self.template
        for placeholder, replacement in replacements.items():
            result = result.replace(placeholder, replacement)
        return result

    def write_route(self, route: str, page_html: str) -> None:
        if route == "/":
            destination = self.temp_output / "index.html"
        elif route == "/404.html":
            destination = self.temp_output / "404.html"
        else:
            destination = self.temp_output / route.strip("/") / "index.html"
        write_text(destination, page_html)
        if route != "/404.html":
            self.generated_routes.append(route)

    def seo_values(
        self,
        record: dict[str, Any],
        *,
        default_title: str,
        default_description: str,
        default_image: str | None = None,
    ) -> tuple[str, str, str | None]:
        seo = record.get("seo") or {}
        image_path = seo.get("image")
        return (
            seo.get("titre") or default_title,
            seo.get("description") or default_description,
            self.seo_image_media.get(image_path) if image_path else default_image,
        )

    def render_breadcrumbs(self, items: list[tuple[str, str | None]]) -> str:
        parts = []
        for label, href in items:
            if href:
                parts.append(f'<a href="{href}">{e(label)}</a><span aria-hidden="true">/</span>')
            else:
                parts.append(f'<span aria-current="page">{e(label)}</span>')
        return f'<nav class="breadcrumbs" aria-label="Fil d’Ariane">{"".join(parts)}</nav>'

    def render_book_card(self, book: dict[str, Any], *, eager: bool = False) -> str:
        collection = self.collections_by_slug[book["collection"]]
        details = []
        if book["typeOuvrage"]:
            details.append(TYPE_LABELS.get(book["typeOuvrage"], book["typeOuvrage"].replace("-", " ").title()))
        if book["ageMinimum"]:
            details.append(f"Dès {book['ageMinimum']} ans")
        price = format_price(book["prixCentimes"])
        if price:
            details.append(price)
        loading = "eager" if eager else "lazy"
        return f"""
<article class="book-card">
  <a class="book-card__cover-link" href="/livres/{e(book['slug'])}/">
    <img class="book-card__cover" src="{self.cover_media[book['slug']]['small']}"
      alt="{e(book.get('couvertureAlt') or f'Couverture de {book["titre"]}')}" loading="{loading}" width="480" height="720">
  </a>
  <p class="book-card__collection">{e(collection['titre'])}</p>
  <h3><a href="/livres/{e(book['slug'])}/">{e(book['titre'])}</a></h3>
  <p class="book-card__meta">{e(' · '.join(details))}</p>
</article>""".strip()

    def render_collection_showcase(self, *, heading_level: int = 2) -> str:
        if heading_level not in {2, 3}:
            raise ValueError("Le niveau de titre des collections doit être 2 ou 3")
        tiles = []
        for index, item in enumerate(self.collections, start=1):
            book_slugs = [slug for slug in item["livres"] if slug in self.cover_media]
            if len(book_slugs) > 3:
                book_slugs = [book_slugs[0], book_slugs[len(book_slugs) // 2], book_slugs[-1]]
            covers = "".join(
                f'<img src="{self.cover_media[slug]["small"]}" alt="" loading="lazy" width="480" height="720">'
                for slug in book_slugs
            )
            count = f"{item['nombreLivres']} {'livres' if item['nombreLivres'] > 1 else 'livre'}"
            tiles.append(
                f"""
<a class="collection-showcase__item" href="/collections/{e(item['slug'])}/">
  <span class="collection-showcase__copy">
    <span class="collection-showcase__number">Collection {index:02d}</span>
    <h{heading_level}>{e(item['titre'])}</h{heading_level}>
    <span class="collection-showcase__description">{e(item['description'])}</span>
    <span class="collection-showcase__link">Découvrir {e(count)} {icon('arrow-right')}</span>
  </span>
  <span class="collection-showcase__covers" aria-hidden="true">{covers}</span>
</a>""".strip()
            )
        return '<div class="collection-showcase">' + "".join(tiles) + "</div>"

    def featured_books(self) -> list[dict[str, Any]]:
        selected = [
            book
            for book in self.books
            if book["miseEnAvantAccueil"] and book["disponible"]
        ]
        return sorted(selected, key=lambda book: (book["ordreAccueil"], book["ordre"], book["slug"]))

    def build_home(self) -> None:
        home_sections = self.pages_by_slug["accueil"]["sections"]
        sections_by_id = {section.get("id"): section for section in home_sections}
        intro = sections_by_id["presentation"]["contenu"]
        house_update = sections_by_id["information"]
        commercial_info = sections_by_id["soutien-commandes"]
        booksellers_info = sections_by_id["libraires"]
        individuals_info = sections_by_id["particuliers"]
        support_info = sections_by_id["soutien"]
        labels = self.home_settings
        featured = self.featured_books()
        covers = "".join(
            f"""
<a href="/livres/{e(book['slug'])}/" aria-label="Découvrir {e(book['titre'])}">
  <img src="{self.cover_media[book['slug']]['small']}"
    srcset="{self.cover_media[book['slug']]['small']} 480w, {self.cover_media[book['slug']]['large']} 900w"
    sizes="(max-width: 760px) 30vw, 15vw" alt="{e(book.get('couvertureAlt') or f'Couverture de {book["titre"]}')}"
    loading="{'eager' if index < 3 else 'lazy'}" width="480" height="720">
</a>""".strip()
            for index, book in enumerate(featured)
        )
        content = f"""
<section class="hero">
  <div class="container">
    <div class="hero-copy">
      <p class="eyebrow">{e(labels['heroRubrique'])}</p>
      <h1>{e(labels['heroTitre'])} <span>{e(labels['heroAccent'])}</span></h1>
      <p class="lead">{e(labels['heroAccroche'])}</p>
      <div class="hero-actions">
        <a class="button" href="/catalogue/">{e(labels['boutonCatalogue'])} <span aria-hidden="true">→</span></a>
        <a class="button button--secondary" href="/collections/">{e(labels['boutonCollections'])}</a>
      </div>
    </div>
    <div class="cover-ribbon">{covers}</div>
  </div>
</section>
<section class="section home-commercial">
  <div class="container home-commercial__layout">
    <div>
      <p class="eyebrow">{e(house_update['titre'])}</p>
      <h2>{e(labels['titreInformation'])}</h2>
      <p class="lead">{e(house_update['contenu'])}</p>
    </div>
    <div class="home-commercial__details">
      <h3>{e(commercial_info['titre'])}</h3>
      <p>{self.linkify_text(commercial_info['contenu'])}</p>
      <div class="commercial-audiences">
        <section class="commercial-audience">
          <h4>{e(booksellers_info['titre'])}</h4>
          <p>{self.linkify_text(booksellers_info['contenu'])}</p>
        </section>
        <section class="commercial-audience">
          <h4>{e(individuals_info['titre'])}</h4>
          <p>{self.linkify_text(individuals_info['contenu'])}</p>
        </section>
      </div>
      <p class="commercial-support">{self.linkify_text(support_info['contenu'], internal_links={'page de soutien': '/soutien/'})}</p>
      <div class="hero-actions">
        <form class="paypal-form donation-form" action="https://www.paypal.com/donate" method="post" target="_blank">
          <input type="hidden" name="hosted_button_id" value="{e(self.payment_settings['donationHostedButtonId'])}">
          <button class="button" type="submit">{icon('heart')} {e(self.payment_settings['libelleDon'])}</button>
        </form>
        <a class="button button--secondary" href="/offres-speciales/">Voir les offres</a>
      </div>
    </div>
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="section-heading">
      <div><p class="eyebrow">{e(labels['collectionsRubrique'])}</p><h2>{e(labels['collectionsTitre'])}</h2></div>
      <p>{e(intro)}</p>
    </div>
    {self.render_collection_showcase(heading_level=3)}
  </div>
</section>
<section class="section section--ink">
  <div class="container">
    <div class="section-heading">
      <div><p class="eyebrow">{e(labels['suivreRubrique'])}</p><h2>{e(labels['suivreTitre'])}</h2></div>
    </div>
    <div class="split-callout">
      <a href="/actualites/"><p class="eyebrow">{e(labels['actualitesRubrique'])}</p><h3>{e(labels['actualitesTitre'])}</h3><span>{e(labels['actualitesAction'])} <span aria-hidden="true">→</span></span></a>
      <a href="/manuscrits/"><p class="eyebrow">{e(labels['manuscritsRubrique'])}</p><h3>{e(labels['manuscritsTitre'])}</h3><span>{e(labels['manuscritsAction'])} <span aria-hidden="true">→</span></span></a>
    </div>
  </div>
</section>"""
        seo_title, seo_description, seo_image = self.seo_values(
            self.pages_by_slug["accueil"],
            default_title=self.site_settings["nom"],
            default_description=self.site_settings["description"],
        )
        page = self.render_page(
            title=seo_title,
            description=seo_description,
            route="/",
            content=content,
            active="home",
            body_class="home-page",
            og_image=seo_image,
        )
        self.write_route("/", page)

    def build_catalogue(self) -> None:
        labels = self.page_settings["catalogue"]
        content = f"""
<header class="page-heading">
  <div class="container">
    {self.render_breadcrumbs([('Accueil', '/'), ('Catalogue', None)])}
    <p class="eyebrow">{e(labels['rubrique'])}</p>
    <h1>{e(labels['titre'])}</h1>
    <p class="lead">{e(labels['introduction'])}</p>
  </div>
</header>
<section class="filter-panel" id="recherche" aria-label="Filtres du catalogue">
  <div class="container filter-grid">
    <div class="field"><label for="book-search">Titre, auteur ou illustrateur</label><input id="book-search" type="search" placeholder="Rechercher…" autocomplete="off"></div>
    <div class="field"><label for="book-collection">Collection</label><select id="book-collection"><option value="">Toutes</option></select></div>
    <div class="field"><label for="book-type">Type</label><select id="book-type"><option value="">Tous</option></select></div>
    <div class="field"><label for="book-availability">Disponibilité</label><select id="book-availability"><option value="">Tous</option><option value="true">Disponibles</option><option value="false">Indisponibles</option></select></div>
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="results-bar"><p class="results-status" data-results-status aria-live="polite">Chargement du catalogue…</p><div class="field"><label for="book-sort">Trier</label><select id="book-sort"><option value="order">Ordre du catalogue</option><option value="title">Titre</option><option value="price-asc">Prix croissant</option><option value="price-desc">Prix décroissant</option></select></div></div>
    <div class="book-grid" data-book-grid aria-busy="true"><p class="loading-state">Chargement des livres…</p></div>
    <noscript><p class="error-state">JavaScript est nécessaire pour filtrer le catalogue. Les livres restent accessibles depuis les pages des collections.</p></noscript>
  </div>
</section>"""
        page = self.render_page(
            title=labels["titre"],
            description=labels["descriptionSeo"],
            route="/catalogue/",
            content=content,
            active="catalogue",
            scripts=["/assets/js/catalogue.js"],
        )
        self.write_route("/catalogue/", page)

    def build_people_index(self) -> None:
        labels = self.page_settings["personnes"]
        content = f"""
<header class="page-heading">
  <div class="container">
    {self.render_breadcrumbs([('Accueil', '/'), ('Auteurs & illustrateurs', None)])}
    <p class="eyebrow">{e(labels['rubrique'])}</p>
    <h1>{e(labels['titre'])}</h1>
    <p class="lead">{e(labels['introduction'])}</p>
  </div>
</header>
<section class="filter-panel" id="recherche" aria-label="Filtres de l’annuaire">
  <div class="container filter-grid filter-grid--people">
    <div class="field"><label for="person-search">Rechercher un nom</label><input id="person-search" type="search" placeholder="Rechercher…" autocomplete="off"></div>
    <div class="field"><label for="person-role">Rôle</label><select id="person-role"><option value="">Tous les rôles</option><option value="auteur">Auteurs</option><option value="illustrateur">Illustrateurs</option><option value="prefacier">Préfaciers</option></select></div>
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="results-bar"><p class="results-status" data-results-status aria-live="polite">Chargement de l’annuaire…</p></div>
    <div class="person-grid" data-person-grid aria-busy="true"><p class="loading-state">Chargement des personnes…</p></div>
  </div>
</section>"""
        page = self.render_page(
            title=labels["titre"],
            description=labels["descriptionSeo"],
            route="/personnes/",
            content=content,
            active="people",
            scripts=["/assets/js/people.js"],
        )
        self.write_route("/personnes/", page)

    def build_collections_index(self) -> None:
        labels = self.page_settings["collections"]
        content = f"""
<header class="page-heading"><div class="container">
  {self.render_breadcrumbs([('Accueil', '/'), ('Collections', None)])}
  <p class="eyebrow">{e(labels['rubrique'])}</p><h1>{e(labels['titre'])}</h1>
  <p class="lead">{e(labels['introduction'])}</p>
</div></header>
<section class="section"><div class="container">{self.render_collection_showcase()}</div></section>"""
        page = self.render_page(
            title=labels["titre"],
            description=labels["descriptionSeo"],
            route="/collections/",
            content=content,
            active="collections",
        )
        self.write_route("/collections/", page)

    def contributor_links(self, slugs: list[str]) -> str:
        return ", ".join(
            f'<a href="/personnes/{e(slug)}/">{e(self.people_by_slug[slug]["nom"])}</a>'
            for slug in slugs
        )

    def render_gallery(self, images: list[tuple[str, str]]) -> str:
        if not images:
            return ""
        items = "".join(
            f"""
<button class="gallery-item" type="button" data-gallery-src="{e(path)}" data-gallery-alt="{e(alt)}" aria-label="Agrandir : {e(alt)}">
  <img src="{e(path)}" alt="{e(alt)}" loading="lazy">
</button>""".strip()
            for path, alt in images
        )
        return f"""
<div class="gallery-grid">{items}</div>
<dialog class="gallery-dialog" data-gallery-dialog aria-label="Image agrandie">
  <button class="icon-button dialog-close" type="button" data-dialog-close title="Fermer">{icon('x', label='Fermer')}</button>
  <img alt="">
</dialog>""".strip()

    def build_book_pages(self) -> None:
        for book in self.books:
            collection = self.collections_by_slug[book["collection"]]
            contributors = []
            if book["auteurs"]:
                contributors.append(f"Écrit par {self.contributor_links(book['auteurs'])}")
            if book["illustrateurs"]:
                contributors.append(f"Illustré par {self.contributor_links(book['illustrateurs'])}")
            if book["prefaciers"]:
                contributors.append(f"Préfacé par {self.contributor_links(book['prefaciers'])}")

            facts: list[tuple[str, str]] = []
            if book["typeOuvrage"]:
                facts.append(("Type", TYPE_LABELS.get(book["typeOuvrage"], book["typeOuvrage"].replace("-", " ").title())))
            if book["ageMinimum"]:
                facts.append(("Âge", f"À partir de {book['ageMinimum']} ans"))
            if book["nombrePages"]:
                facts.append(("Pages", str(book["nombrePages"])))
            if book["format"]:
                facts.append(("Format", book["format"]))
            if book["reliure"]:
                facts.append(("Reliure", book["reliure"]))
            if book["isbn"] and book["isbnValide"]:
                facts.append(("ISBN", book["isbn"]))
            facts_html = "".join(f"<div><dt>{e(label)}</dt><dd>{e(value)}</dd></div>" for label, value in facts)

            price = format_price(book["prixCentimes"])
            price_html = f'<span class="price">{e(price)}</span>' if price else ""
            availability_class = "" if book["disponible"] else " availability--unavailable"
            availability_label = "Disponible" if book["disponible"] else "Actuellement indisponible"
            subject = quote(f"Question — {book['titre']}")
            if book["disponible"]:
                purchase_action = f"""
<form class="paypal-form" action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_blank">
  <input type="hidden" name="cmd" value="_s-xclick">
  <input type="hidden" name="hosted_button_id" value="{e(book['paypalHostedButtonId'])}">
  <button class="button" type="submit">{icon('shopping-cart')} Ajouter au panier avec PayPal</button>
</form>"""
            else:
                purchase_action = f'<a class="button" href="mailto:{e(self.site_settings["courriel"])}?subject={subject}">{icon("mail")} Nous contacter</a>'
            purchase = f"""
<div class="purchase-line">
  {price_html}<span class="availability{availability_class}">{availability_label}</span>
  {purchase_action}
</div>"""

            excerpts = ""
            valid_excerpts = [path for path in book["extraits"] if path in self.document_media]
            if valid_excerpts:
                excerpt_links = "".join(
                    f'<li><a class="button button--secondary button--small" href="{self.document_media[path]}" target="_blank">{icon("file")} Lire l’extrait {index if len(valid_excerpts) > 1 else ""}</a></li>'
                    for index, path in enumerate(valid_excerpts, start=1)
                )
                excerpts = f'<div><h2>Extraits</h2><ul class="link-list">{excerpt_links}</ul></div>'

            gallery = ""
            if book["illustrations"]:
                gallery_items = [
                    (
                        self.illustration_media[media_path(item)],
                        media_alt(item, f"Illustration intérieure de {book['titre']} — {index}"),
                    )
                    for index, item in enumerate(book["illustrations"], start=1)
                    if media_path(item) in self.illustration_media
                ]
                gallery = f'<section class="section section--white"><div class="container"><div class="section-heading"><div><p class="eyebrow">À l’intérieur</p><h2>Quelques illustrations</h2></div></div>{self.render_gallery(gallery_items)}</div></section>'

            related_slugs = book.get("aDecouvrir")
            if related_slugs is None:
                related_slugs = [slug for slug in collection["livres"] if slug != book["slug"]][:4]
            related = [self.books_by_slug[slug] for slug in related_slugs if slug in self.books_by_slug]
            related_html = "".join(self.render_book_card(item) for item in related)
            related_section = ""
            if related_html:
                related_section = f'<section class="section"><div class="container"><div class="section-heading"><div><p class="eyebrow">Dans la même collection</p><h2>À découvrir aussi</h2></div><a href="/collections/{e(collection["slug"])}/">Toute la collection</a></div><div class="book-grid">{related_html}</div></div></section>'
            content = f"""
<section class="section section--white">
  <div class="container">
    {self.render_breadcrumbs([('Accueil', '/'), ('Catalogue', '/catalogue/'), (collection['titre'], f"/collections/{collection['slug']}/"), (book['titre'], None)])}
    <article class="book-detail">
      <div><img class="book-detail__cover" src="{self.cover_media[book['slug']]['large']}" srcset="{self.cover_media[book['slug']]['small']} 480w, {self.cover_media[book['slug']]['large']} 900w" sizes="(max-width: 760px) 90vw, 390px" alt="{e(book.get('couvertureAlt') or f'Couverture de {book["titre"]}')}" width="900" height="1350"></div>
      <div class="book-detail__content">
        <p class="eyebrow"><a href="/collections/{e(collection['slug'])}/">{e(collection['titre'])}</a></p>
        <h1>{e(book['titre'])}</h1>
        <p class="contributors">{'<br>'.join(contributors)}</p>
        <p class="book-description">{e(book['description'] or 'Description à venir.')}</p>
        <dl class="book-facts">{facts_html}</dl>
        {excerpts}
        {purchase}
      </div>
    </article>
  </div>
</section>
{gallery}
{related_section}"""

            structured = {
                "@context": "https://schema.org",
                "@type": "Book",
                "name": book["titre"],
                "author": [
                    {"@type": "Person", "name": self.people_by_slug[slug]["nom"]}
                    for slug in book["auteurs"]
                ],
                "image": absolute_url(self.base_url, self.cover_media[book["slug"]]["large"]),
                "description": book["description"],
            }
            if book["isbn"] and book["isbnValide"]:
                structured["isbn"] = book["isbn"]
            seo_title, seo_description, seo_image = self.seo_values(
                book,
                default_title=book["titre"],
                default_description=book["description"] or f"Découvrez {book['titre']}.",
                default_image=self.cover_media[book["slug"]]["large"],
            )
            page = self.render_page(
                title=seo_title,
                description=seo_description,
                route=f"/livres/{book['slug']}/",
                content=content,
                active="catalogue",
                body_class="book-page",
                og_type="book",
                og_image=seo_image,
                structured_data=structured,
            )
            self.write_route(f"/livres/{book['slug']}/", page)

    def build_collection_pages(self) -> None:
        for collection in self.collections:
            books = [self.books_by_slug[slug] for slug in collection["livres"]]
            cards = "".join(self.render_book_card(book) for book in books)
            content = f"""
<header class="page-heading"><div class="container">
  {self.render_breadcrumbs([('Accueil', '/'), ('Collections', '/collections/'), (collection['titre'], None)])}
  <p class="eyebrow">{collection['nombreLivres']} livres</p><h1>{e(collection['titre'])}</h1><p class="lead">{e(collection['description'])}</p>
</div></header>
<section class="section"><div class="container"><div class="book-grid">{cards}</div></div></section>"""
            seo_title, seo_description, seo_image = self.seo_values(
                collection,
                default_title=collection["titre"],
                default_description=collection["description"],
            )
            page = self.render_page(
                title=seo_title,
                description=seo_description,
                route=f"/collections/{collection['slug']}/",
                content=content,
                active="collections",
                og_image=seo_image,
            )
            self.write_route(f"/collections/{collection['slug']}/", page)

    def build_person_pages(self) -> None:
        for person in self.people:
            related_slugs = []
            for role_books in person["livres"].values():
                for slug in role_books:
                    if slug not in related_slugs:
                        related_slugs.append(slug)
            cards = "".join(self.render_book_card(self.books_by_slug[slug]) for slug in related_slugs)
            media = self.person_media.get(person["slug"])
            if media:
                portrait_alt = person.get("imagePrincipaleAlt") or f"Portrait de {person['nom']}"
                visual = f'<img src="{media["large"]}" srcset="{media["small"]} 480w, {media["large"]} 900w" sizes="(max-width: 760px) 90vw, 330px" alt="{e(portrait_alt)}" width="900" height="900">'
                og_image = media["large"]
            else:
                visual = f'<span class="monogram" aria-hidden="true">{e(monogram(person["nom"]))}</span>'
                og_image = None
            roles = " · ".join(ROLE_LABELS.get(role, role.title()) for role in person["roles"])
            biography = person["biographie"] or "Cette personne a contribué aux ouvrages présentés ci-dessous."
            gallery_items = [
                (
                    self.person_gallery_media[media_path(item)],
                    media_alt(item, f"{person['nom']} — image {index}"),
                )
                for index, item in enumerate(person["images"], start=1)
                if media_path(item) in self.person_gallery_media
            ]
            gallery = ""
            if gallery_items:
                gallery = (
                    '<section class="section section--white"><div class="container">'
                    '<div class="section-heading"><div><p class="eyebrow">En images</p>'
                    f'<h2>{e(person["nom"])}</h2></div></div>{self.render_gallery(gallery_items)}'
                    '</div></section>'
                )
            external = ""
            if person["liensExternes"]:
                links = "".join(
                    f'<li><a class="button button--secondary button--small" href="{e(url)}" target="_blank" rel="noopener noreferrer">Site personnel {icon("external")}</a></li>'
                    for url in person["liensExternes"]
                )
                external = f'<ul class="link-list">{links}</ul>'
            content = f"""
<section class="section section--white"><div class="container">
  {self.render_breadcrumbs([('Accueil', '/'), ('Auteurs & illustrateurs', '/personnes/'), (person['nom'], None)])}
  <article class="person-detail">
    <div class="person-detail__visual">{visual}</div>
    <div><p class="eyebrow">{e(roles)}</p><h1>{e(person['nom'])}</h1><p class="lead">{e(biography)}</p>{external}</div>
  </article>
</div></section>
{gallery}
<section class="section"><div class="container"><div class="section-heading"><div><p class="eyebrow">Bibliographie</p><h2>{len(related_slugs)} {'livres associés' if len(related_slugs) > 1 else 'livre associé'}</h2></div></div><div class="book-grid">{cards}</div></div></section>"""
            structured = {
                "@context": "https://schema.org",
                "@type": "Person",
                "name": person["nom"],
                "description": person["biographie"],
                "url": absolute_url(self.base_url, f"/personnes/{person['slug']}/"),
            }
            seo_title, seo_description, seo_image = self.seo_values(
                person,
                default_title=person["nom"],
                default_description=person["biographie"] or f"Découvrez les livres auxquels {person['nom']} a contribué.",
                default_image=og_image,
            )
            page = self.render_page(
                title=seo_title,
                description=seo_description,
                route=f"/personnes/{person['slug']}/",
                content=content,
                active="people",
                og_image=seo_image,
                structured_data=structured,
            )
            self.write_route(f"/personnes/{person['slug']}/", page)

    def linkify_text(self, value: str, *, internal_links: dict[str, str] | None = None) -> str:
        escaped = e(value)
        escaped = re.sub(
            r"(?<![\w@])(https?://[^\s&lt;]+)",
            lambda match: f'<a href="{match.group(1)}" target="_blank" rel="noopener noreferrer">{match.group(1)}</a>',
            escaped,
        )
        escaped = re.sub(
            r"(?<![\w@])([\w.+-]+@[\w.-]+\.[A-Za-z]{2,})",
            lambda match: f'<a href="mailto:{match.group(1)}">{match.group(1)}</a>',
            escaped,
        )
        for label, href in (internal_links or {}).items():
            escaped = escaped.replace(e(label), f'<a href="{e(href)}">{e(label)}</a>')
        return escaped

    def editorial_link(self, link: dict[str, Any]) -> str | None:
        link_type = link["type"]
        label = link.get("texte") or "Consulter le lien"
        if link_type == "document":
            href = self.document_media.get(link["href"])
            if not href:
                return None
            return f'<a href="{href}" target="_blank">{icon("file")} {e(label)}</a>'
        if link_type == "livre":
            return f'<a href="/livres/{e(link["slug"])}/">{e(label)}</a>'
        if link_type == "page":
            href = "/" if link["slug"] == "accueil" else f'/{link["slug"]}/'
            return f'<a href="{href}">{e(label)}</a>'
        href = link.get("href")
        if not href:
            return None
        if link_type == "externe":
            display = link.get("texte") or re.sub(r"^https?://(?:www\.)?", "", href).rstrip("/")
            return f'<a href="{e(href)}" target="_blank" rel="noopener noreferrer">{e(display)} {icon("external")}</a>'
        return f'<a href="{e(href)}">{e(label)}</a>'

    def build_editorial_pages(self) -> None:
        for page_data in self.pages:
            if page_data["slug"] in {"entree", "accueil"}:
                continue
            if page_data["slug"] == "actualites":
                self.build_news_page(page_data)
                continue
            draft = bool(page_data["aVerifier"])
            if draft and not self.include_drafts:
                continue
            rendered_sections = []
            for section in page_data["sections"]:
                heading = f'<h2>{e(section["titre"])}</h2>' if section["titre"] else ""
                rendered_sections.append(
                    f'<section class="editorial-section">{heading}'
                    f'<p>{self.linkify_text(section["contenu"])}</p></section>'
                )
            sections = "".join(rendered_sections)
            link_items = [self.editorial_link(link) for link in page_data["liens"]]
            link_items = [item for item in link_items if item]
            aside = ""
            if link_items:
                aside = f'<aside class="editorial-aside"><h2>Liens et documents</h2><ul>{"".join(f"<li>{item}</li>" for item in link_items)}</ul></aside>'
            gallery = ""
            if page_data["images"]:
                gallery_items = [
                    (
                        self.page_image_media[media_path(item)],
                        media_alt(item, f"{page_data['titre']} — image {index}"),
                    )
                    for index, item in enumerate(page_data["images"], start=1)
                    if media_path(item) in self.page_image_media
                ]
                gallery = f'<section class="section section--white"><div class="container"><h2>En images</h2>{self.render_gallery(gallery_items)}</div></section>'
            description = page_data["sections"][0]["contenu"]
            active = "actualites" if page_data["slug"] == "actualites" else "maison"
            content = f"""
<header class="page-heading"><div class="container">
  {self.render_breadcrumbs([('Accueil', '/'), (page_data['titre'], None)])}
  <p class="eyebrow">{e(page_data.get('rubrique') or self.site_settings['nom'])}</p><h1>{e(page_data['titre'])}</h1>
</div></header>
<section class="section"><div class="container editorial-layout"><article>{sections}</article>{aside}</div></section>
{gallery}"""
            seo_title, seo_description, seo_image = self.seo_values(
                page_data,
                default_title=page_data["titre"],
                default_description=description,
            )
            page = self.render_page(
                title=seo_title,
                description=seo_description,
                route=f"/{page_data['slug']}/",
                content=content,
                active=active,
                draft=draft,
                og_image=seo_image,
            )
            self.write_route(f"/{page_data['slug']}/", page)

    def build_news_page(self, page_data: dict[str, Any]) -> None:
        labels = self.page_settings["actualites"]
        news_items = []
        for item in self.news:
            image_html = ""
            if item["slug"] in self.news_image_media:
                image_html = (
                    f'<img src="{self.news_image_media[item["slug"]]}" '
                    f'alt="{e(item.get("imageAlt") or item["titre"])}" loading="lazy" width="1200" height="900">'
                )
            date = datetime.strptime(item["datePublication"], "%Y-%m-%d")
            body = "".join(
                f"<p>{self.linkify_text(paragraph)}</p>"
                for paragraph in re.split(r"\n\s*\n", item["contenu"].strip())
                if paragraph.strip()
            )
            actions = []
            if item.get("lienExterne"):
                actions.append(
                    f'<a href="{e(item["lienExterne"])}" target="_blank" rel="noopener noreferrer">'
                    f'En savoir plus {icon("external")}</a>'
                )
            if item.get("document") and item["document"] in self.document_media:
                actions.append(
                    f'<a href="{self.document_media[item["document"]]}" target="_blank">'
                    f'{icon("file")} Télécharger le document</a>'
                )
            actions_html = f'<div class="news-card__actions">{"".join(actions)}</div>' if actions else ""
            news_items.append(
                f"""
<article class="news-card">
  {image_html}
  <div class="news-card__content">
    <p class="news-card__meta"><span>{e(NEWS_TYPE_LABELS[item['type']])}</span><time datetime="{item['datePublication']}">{date.strftime('%d/%m/%Y')}</time></p>
    <h2>{e(item['titre'])}</h2>
    <p class="news-card__summary">{e(item['resume'])}</p>
    <div class="news-card__body">{body}</div>
    {actions_html}
  </div>
</article>""".strip()
            )
        news_listing = ""
        if news_items:
            news_listing = (
                '<section class="section"><div class="container">'
                '<div class="news-grid">' + "".join(news_items) + "</div></div></section>"
            )
        content = f"""
<header class="page-heading"><div class="container">
  {self.render_breadcrumbs([('Accueil', '/'), ('Actualités', None)])}
  <p class="eyebrow">{e(labels['rubrique'])}</p><h1>{e(labels['titre'])}</h1>
  <p class="lead">{e(labels['introduction'])}</p>
</div></header>
{news_listing}
<section class="section news-section"><div class="container">
  <div class="news-callout">
    <p class="eyebrow">{e(labels['appelRubrique'])}</p>
    <h2>{e(labels['appelTitre'])}</h2>
    <p class="lead">{e(labels['appelTexte'])}</p>
    <div class="news-topics" aria-label="Actualités publiées"><span>Salons et rencontres</span><span>Sorties de livres</span><span>Nouvelles de la maison</span></div>
    <a class="button" href="{e(self.site_settings['facebook'])}" target="_blank" rel="noopener noreferrer">{e(labels['boutonFacebook'])} {icon('external')}</a>
  </div>
</div></section>"""
        page = self.render_page(
            title=(page_data.get("seo") or {}).get("titre") or labels["titre"],
            description=(page_data.get("seo") or {}).get("description") or labels["descriptionSeo"],
            route="/actualites/",
            content=content,
            active="actualites",
            og_image=self.seo_image_media.get((page_data.get("seo") or {}).get("image")),
        )
        self.write_route("/actualites/", page)

    def published_editorial_pages(self) -> list[dict[str, Any]]:
        return [
            page
            for page in self.pages
            if page["slug"] not in {"entree", "accueil", "actualites"}
            and (self.include_drafts or not page["aVerifier"])
        ]

    def build_house_page(self) -> None:
        labels = self.page_settings["maison"]
        cards = []
        for page in self.published_editorial_pages():
            eyebrow = page.get("rubrique") or self.site_settings["nomCourt"]
            action = page.get("libelleAction") or f"Découvrir {page['titre']}"
            cards.append(
                f"""
<a class="house-card house-card--{e(page['slug'])}" href="/{e(page['slug'])}/">
  <span class="house-card__eyebrow">{e(eyebrow)}</span>
  <h2>{e(page['titre'])}</h2>
  <span class="house-card__summary">{e(truncate(page['sections'][0]['contenu'], 120))}</span>
  <span class="house-card__action">{e(action)} {icon('arrow-right')}</span>
</a>""".strip()
            )
        content = f"""
<header class="page-heading"><div class="container">
  {self.render_breadcrumbs([('Accueil', '/'), ('La maison', None)])}
  <p class="eyebrow">{e(labels['rubrique'])}</p><h1>{e(labels['titre'])}</h1>
  <p class="lead">{e(labels['introduction'])}</p>
</div></header>
<section class="section"><div class="container"><div class="house-grid">{"".join(cards)}</div></div></section>"""
        page = self.render_page(
            title=labels["titre"],
            description=labels["descriptionSeo"],
            route="/la-maison/",
            content=content,
            active="maison",
        )
        self.write_route("/la-maison/", page)

    def build_site_map_page(self) -> None:
        editorial = self.published_editorial_pages()
        editorial_links = "".join(f'<li><a href="/{page["slug"]}/">{e(page["titre"])}</a></li>' for page in editorial)
        collection_links = "".join(f'<li><a href="/collections/{item["slug"]}/">{e(item["titre"])}</a></li>' for item in self.collections)
        content = f"""
<header class="page-heading"><div class="container">{self.render_breadcrumbs([('Accueil', '/'), ('Plan du site', None)])}<h1>Plan du site</h1></div></header>
<section class="section"><div class="container editorial-layout"><div>
  <section class="editorial-section"><h2>Livres et personnes</h2><ul><li><a href="/catalogue/">Catalogue</a></li><li><a href="/personnes/">Auteurs & illustrateurs</a></li></ul></section>
  <section class="editorial-section"><h2>Collections</h2><ul>{collection_links}</ul></section>
  <section class="editorial-section"><h2>La maison</h2><ul><li><a href="/actualites/">Actualités</a></li>{editorial_links}</ul></section>
</div></div></section>"""
        page = self.render_page(
            title="Plan du site",
            description="Plan du site des Éditions Chant d’orties.",
            route="/plan-du-site/",
            content=content,
            active="",
        )
        self.write_route("/plan-du-site/", page)

    def build_404(self) -> None:
        content = """
<section class="error-page"><div><p class="error-code">404</p><h1>Page introuvable</h1><p>Cette page a peut-être changé d’adresse.</p><a class="button" href="/catalogue/">Revenir au catalogue</a></div></section>"""
        page = self.render_page(
            title="Page introuvable",
            description="La page demandée est introuvable.",
            route="/404.html",
            content=content,
            active="",
            body_class="not-found-page",
        )
        self.write_route("/404.html", page)

    def build_redirects(self) -> None:
        redirects: dict[str, str] = {}

        def add_old_addresses(record: dict[str, Any], target: str) -> None:
            for source in record.get("anciensSlugs", []):
                normalized = "/" + source.strip().lstrip("/")
                if normalized != target:
                    redirects[normalized] = target

        # Les redirections sont construites sur le contenu brut : un contenu
        # retiré du site (brouillon ou archivé) doit continuer à rediriger ses
        # anciennes adresses, vers sa rubrique parente à défaut de sa page.
        published = {
            "books": {book["slug"] for book in self.books},
            "people": {person["slug"] for person in self.people},
            "collections": {item["slug"] for item in self.collections},
            "pages": {
                page["slug"]
                for page in self.pages
                if not (page["aVerifier"] and not self.include_drafts)
            },
        }

        for book in self.raw["books"]:
            slug = book["slug"]
            target = f"/livres/{slug}/" if slug in published["books"] else "/catalogue/"
            source = self.legacy["livres"].get(slug)
            if source and source.lower() != "index.html":
                redirects[f"/{source}"] = target
            add_old_addresses(book, target)
        for person in self.raw["people"]:
            slug = person["slug"]
            target = f"/personnes/{slug}/" if slug in published["people"] else "/personnes/"
            add_old_addresses(person, target)
        for collection in self.raw["collections"]:
            slug = collection["slug"]
            target = (
                f"/collections/{slug}/" if slug in published["collections"] else "/collections/"
            )
            source = self.legacy["collections"].get(slug)
            if source:
                redirects[f"/{source}"] = target
            add_old_addresses(collection, target)
        for page in self.raw["pages"]:
            slug = page["slug"]
            if slug in {"entree", "accueil"}:
                continue
            target = f"/{slug}/" if slug in published["pages"] else "/la-maison/"
            source = self.legacy["pages"].get(slug)
            if source:
                redirects[f"/{source}"] = target
            add_old_addresses(page, target)
        for item in self.raw["news"]:
            add_old_addresses(item, "/actualites/")
        redirects.update(
            {
                "/auteurs.html": "/personnes/",
                "/illustrateurs.html": "/personnes/",
                "/accueil.html": "/",
                "/accueil-1.html": "/",
                "/accueil-2.html": "/",
                "/accueil-3.html": "/",
                "/accueil-juillet2026.html": "/",
            }
        )
        lines = ["Options -Indexes", "ErrorDocument 404 /404.html", ""]
        for source, target in sorted(redirects.items(), key=lambda item: item[0].lower()):
            lines.append(f'Redirect 301 "{source}" "{target}"')
        write_text(self.temp_output / ".htaccess", "\n".join(lines) + "\n")

    def build_machine_files(self) -> None:
        routes = sorted(set(self.generated_routes))
        entries = "".join(
            f"  <url><loc>{e(absolute_url(self.base_url, route))}</loc></url>\n"
            for route in routes
        )
        sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}</urlset>\n'
        write_text(self.temp_output / "sitemap.xml", sitemap)
        write_text(
            self.temp_output / "robots.txt",
            f"User-agent: *\nAllow: /\n\nSitemap: {self.base_url}/sitemap.xml\n",
        )

    def build_report(self) -> None:
        html_count = len(list(self.temp_output.rglob("*.html")))
        report = {
            "mode": "preview" if self.include_drafts else "production",
            "pagesHtml": html_count,
            "routesIndexees": len(self.generated_routes),
            "livres": len(self.books),
            "personnes": len(self.people),
            "collections": len(self.collections),
            "actualites": len(self.news),
            "medias": self.media_stats,
            "documentsIgnores": self.skipped_documents,
        }
        write_json(self.report_path, report)

    def build(self) -> None:
        self.validate_source()
        self.acquire_lock()
        try:
            self.build_output()
        finally:
            self.release_lock()

    def build_output(self) -> None:
        self.prepare_output()
        self.optimize_images()
        self.prepare_documents()
        self.write_public_data()
        self.build_home()
        self.build_catalogue()
        self.build_people_index()
        self.build_collections_index()
        self.build_book_pages()
        self.build_collection_pages()
        self.build_person_pages()
        self.build_editorial_pages()
        self.build_house_page()
        self.build_site_map_page()
        self.build_404()
        self.build_redirects()
        self.build_machine_files()
        self.build_report()
        self.finish_output()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", type=Path, default=Path("dist"))
    parser.add_argument("--include-drafts", action="store_true")
    parser.add_argument("--base-url", help="Remplace temporairement le domaine défini dans les réglages")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    builder = SiteBuilder(
        root,
        output,
        include_drafts=args.include_drafts,
        base_url=args.base_url,
    )
    builder.build()
    report = read_json(builder.report_path)
    print(
        f"Site generated in {output}: {report['pagesHtml']} HTML pages, "
        f"{report['medias']['images']} optimized images, "
        f"{report['medias']['documents']} documents."
    )


if __name__ == "__main__":
    main()
