"""L'écriture du dossier dist/ : vérifications, verrou, copie des ressources, rapport.

Ce fichier ne contient aucun HTML. Il décide seulement où chaque page est déposée
(`write_route`), recolle la feuille de style, recopie les scripts et les images de
frontend/assets/, et publie les données lues par le catalogue et l'annuaire.
"""

from __future__ import annotations

import fcntl
import shutil
from typing import Any

from content_data import referenced_media_paths

from .outils import monogram, write_json, write_text


class Sortie:
    def validate_source(self) -> None:
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
        # La chaîne vient du constructeur, celle-là même qui a servi à l'empreinte.
        write_text(self.temp_output / "assets" / "css" / "site.css", self.site_css)
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
        # Le rang dans le bandeau de l’accueil, pour son aperçu dans l’administration ;
        # null pour un livre qui n’y figure pas.
        home_rank = {book["slug"]: rank for rank, book in enumerate(self.featured_books())}
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
                    "rangAccueil": home_rank.get(book["slug"]),
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
                # L’emblème, pour la vignette de la liste dans l’administration.
                "logo": self.collection_logo_media.get(item["slug"]),
            }
            for item in self.collections
        ]
        write_json(self.temp_output / "data" / "livres.json", public_books)
        write_json(self.temp_output / "data" / "personnes.json", public_people)
        write_json(self.temp_output / "data" / "collections.json", public_collections)
        write_json(self.temp_output / "data" / "suppression.json", self.deletion_guard())

    def deletion_guard(self) -> dict[str, dict[str, str]]:
        """Les fiches que l’administration ne laisse pas supprimer, avec la raison.

        Lu par frontend/admin/suppression.js, qui désactive alors « Supprimer » et
        affiche la raison. Ce sont les liens de structure, que la génération ne peut pas
        retirer d’elle-même (voir prune_missing_references, content_data.py) : une
        personne qui signe un livre ou un projet, une collection qui en contient, le
        dernier livre d’une collection publiée ou son seul livre disponible, et les
        mentions légales. Tous les statuts comptent, puisque la validation les vérifie
        tous. Seuls les titres publiés sont nommés : ce fichier est public.
        """
        raw = self.raw

        def citing(records: list[dict[str, Any]], what: str) -> str:
            what = what if len(records) > 1 else what.removesuffix("s")
            published = [record["titre"] for record in records if record.get("statut") == "publie"]
            others = len(records) - len(published)
            names = ", ".join(f"« {title} »" for title in published[:5])
            if len(published) > 5:
                names += f" et {len(published) - 5} autres"
            if others:
                names += (" ; " if names else "") + (f"{others} fiches non publiées" if others > 1 else "1 fiche non publiée")
            return f"{len(records)} {what} ({names})"

        people: dict[str, str] = {}
        for person in raw["people"]:
            slug = person["slug"]
            books = [b for b in raw["books"] if slug in (*b.get("auteurs", []), *b.get("illustrateurs", []), *b.get("prefaciers", []))]
            projects = [p for p in raw["projects"] if slug in (*p.get("auteurs", []), *p.get("illustrateurs", []))]
            parts = [citing(books, "livres")] if books else []
            parts += [citing(projects, "projets")] if projects else []
            if parts:
                people[slug] = (
                    f"Cette personne figure dans {' et '.join(parts)}. Retirez-la d’abord de ces "
                    "fiches, ou choisissez plutôt Publication : Archivé."
                )
        collections: dict[str, str] = {}
        for collection in raw["collections"]:
            slug = collection["slug"]
            books = [b for b in raw["books"] if b.get("collection") == slug]
            projects = [p for p in raw["projects"] if p.get("collection") == slug]
            parts = [citing(books, "livres")] if books else []
            parts += [citing(projects, "projets")] if projects else []
            if parts:
                collections[slug] = (
                    f"Cette collection contient {' et '.join(parts)}. Rangez-les d’abord dans une "
                    "autre collection, ou choisissez plutôt Publication : Archivé."
                )
        books: dict[str, str] = {}
        for collection in raw["collections"]:
            if collection.get("statut") != "publie":
                continue
            published = [b for b in raw["books"] if b.get("collection") == collection["slug"] and b.get("statut") == "publie"]
            available = [b for b in published if b.get("disponible")]
            if len(published) == 1:
                books[published[0]["slug"]] = (
                    f"C’est le dernier livre publié de la collection « {collection['titre']} », qui "
                    "doit en garder au moins un. Publiez d’abord un autre livre dans cette "
                    "collection."
                )
            elif len(available) == 1:
                books[available[0]["slug"]] = (
                    f"C’est le seul livre disponible de la collection « {collection['titre']} » : "
                    "l’accueil en montre toujours un par collection. Choisissez plutôt "
                    "Publication : Archivé, ou rendez d’abord un autre livre disponible."
                )
        pages = {
            "mentions-legales": "Les mentions légales sont obligatoires : cette page ne peut pas être supprimée.",
        }
        return {"personnes": people, "collections": collections, "livres": books, "pages": pages}

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
        referenced = referenced_media_paths(self.raw)
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
            # Ce qu’une suppression depuis l’administration a laissé derrière elle :
            # rien n’y bloque la publication, tout y est à relire à l’occasion.
            "referencesRetirees": self.raw.get("referencesRetirees", []),
            "liensRetires": [f"{owner}: {href}" for owner, href in self.liens_retires],
            "mediasInutilises": sorted(
                path.relative_to(self.root).as_posix()
                for path in (self.root / "content" / "media").rglob("*")
                if path.is_file() and path.relative_to(self.root).as_posix() not in referenced
            ),
        }
        write_json(self.report_path, report)

