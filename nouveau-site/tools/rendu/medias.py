"""La préparation des images et des documents avant publication.

Les couvertures, portraits, illustrations et emblèmes sont recompressés en WebP à deux
tailles ; les PDF sont copiés et allégés. Ce fichier ne contient aucun HTML : il ne
produit que les fichiers déposés dans dist/assets/media/.

Recompresser les 447 images prend une quarantaine de secondes, soit la quasi-totalité
du temps de génération. Le résultat est donc conservé dans .cache-medias/ : une image
dont le fichier source n'a pas changé est reprise telle quelle. Ce dossier peut être
supprimé à tout moment sans conséquence, il se reconstruit tout seul.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import PIL
from PIL import Image, ImageFile, ImageOps

from content_data import media_path

from .outils import slugify

ImageFile.LOAD_TRUNCATED_IMAGES = True

PDFINFO_BINARY = "/usr/bin/pdfinfo" if Path("/usr/bin/pdfinfo").is_file() else shutil.which("pdfinfo")
GHOSTSCRIPT_BINARY = "/usr/bin/gs" if Path("/usr/bin/gs").is_file() else shutil.which("gs")

# Réglages d'encodage des images, isolés ici parce qu'ils entrent dans la clé du cache.
QUALITE_WEBP = 83
METHODE_WEBP = 6

# À incrémenter à la main si save_webp change de traitement — rotation, conversion,
# redimensionnement. Sans cela, le cache resservirait des images fabriquées à l'ancienne.
VERSION_RECETTE = 1


class Medias:
    def empreinte_image(self, source: Path, max_size: tuple[int, int]) -> Path:
        """Le fichier du cache correspondant à cette image et à cette taille.

        La clé couvre tout ce qui influe sur le résultat : les octets de la source — sa
        date ne compte pas, recopier un fichier ne doit rien invalider —, la taille
        demandée, les réglages d'encodage, la version de Pillow qui peut encoder
        autrement d'une version à l'autre, et le numéro de recette.
        """
        recette = (
            f"{VERSION_RECETTE}|{max_size[0]}x{max_size[1]}"
            f"|q{QUALITE_WEBP}|m{METHODE_WEBP}|pillow{PIL.__version__}"
        )
        empreinte = hashlib.sha256()
        empreinte.update(source.read_bytes())
        empreinte.update(recette.encode("utf-8"))
        return self.cache_medias / f"{empreinte.hexdigest()}.webp"

    def save_webp(self, source: Path, destination: Path, max_size: tuple[int, int]) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        cache = self.empreinte_image(source, max_size)

        if cache.is_file():
            shutil.copyfile(cache, destination)
            self.media_stats["images"] += 1
            self.media_stats["imagesReprises"] += 1
            return

        with Image.open(source) as raw_image:
            raw_image.seek(0)
            image = ImageOps.exif_transpose(raw_image)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            if image.mode not in {"RGB", "RGBA"}:
                image = image.convert("RGBA" if "transparency" in image.info else "RGB")
            image.save(destination, "WEBP", quality=QUALITE_WEBP, method=METHODE_WEBP)
        self.media_stats["images"] += 1

        # Dépôt en deux temps : une génération interrompue ne doit pas laisser dans le
        # cache une image tronquée, qui serait ensuite resservie telle quelle.
        cache.parent.mkdir(parents=True, exist_ok=True)
        provisoire = cache.with_name(f"{cache.name}.{os.getpid()}.partiel")
        shutil.copyfile(destination, provisoire)
        provisoire.replace(cache)

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

        # Les emblèmes des collections viennent de l’ancien site : de petits dessins
        # transparents, affichés au plus à 180 pixels. Une seule taille suffit.
        for collection in self.collections:
            logo_path = collection.get("logo")
            if not logo_path:
                continue
            destination = (
                self.temp_output / "assets" / "media" / "collections" / f"{collection['slug']}.webp"
            )
            self.save_webp(self.root / logo_path, destination, (360, 360))
            self.collection_logo_media[collection["slug"]] = (
                f"/assets/media/collections/{destination.name}"
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
