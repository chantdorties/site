"""L'écriture du dossier dist/ : vérifications, verrou, copie des ressources, rapport.

Ce fichier ne contient aucun HTML. Il décide seulement où chaque page est déposée
(`write_route`), recolle la feuille de style, recopie les scripts et les images de
frontend/assets/, et publie les données lues par le catalogue et l'annuaire.
"""

from __future__ import annotations

import fcntl
import shutil

from .feuille_de_style import assembler_css
from .outils import monogram, write_json, write_text


class Sortie:
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
        # Les morceaux de frontend/assets/css/ sont recollés en un seul fichier :
        # le site publié n'en contient qu'un, le navigateur ne fait qu'une requête.
        write_text(
            self.temp_output / "assets" / "css" / "site.css",
            assembler_css(self.frontend_dir),
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
                "description": item["description"] and self.texte_brut(item["description"]),
                "nombreLivres": item["nombreLivres"],
            }
            for item in self.collections
        ]
        write_json(self.temp_output / "data" / "livres.json", public_books)
        write_json(self.temp_output / "data" / "personnes.json", public_people)
        write_json(self.temp_output / "data" / "collections.json", public_collections)

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
            "projets": len(self.projects),
            "medias": self.media_stats,
            "documentsIgnores": self.skipped_documents,
        }
        write_json(self.report_path, report)

