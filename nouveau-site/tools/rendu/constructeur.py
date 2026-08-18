"""L'assemblage général : la classe qui réunit tous les fichiers de rendu.

Elle ne contient aucun HTML. Elle charge le contenu, tient les tableaux partagés
(livres par identifiant, images optimisées…), et appelle chaque page dans l'ordre.

Pour trouver le HTML d'une page ou d'un composant, ouvrir le fichier correspondant
dans pages/ ou composants/ — voir docs/GUIDE-APPARENCE.md.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from content_data import load_content

from .composants.carte_livre import CarteLivre
from .composants.cartes_projets import CartesProjets
from .composants.en_tete import EnTete
from .composants.fil_ariane import FilAriane
from .composants.galerie import Galerie
from .composants.pied_de_page import PiedDePage
from .composants.vitrine_collections import VitrineCollections
from .feuille_de_style import assembler_css
from .gabarit import Gabarit
from .medias import Medias
from .pages.accueil import PageAccueil
from .pages.actualites import PageActualites
from .pages.catalogue import PageCatalogue
from .pages.collections import PagesCollections
from .pages.editoriales import PagesEditoriales
from .pages.erreur_404 import Page404
from .pages.livres import PagesLivres
from .pages.maison import PageMaison
from .pages.personnes import PagesPersonnes
from .pages.plan_du_site import PagePlanDuSite
from .sortie import Sortie
from .technique import FichiersTechniques
from .texte import OutilsTexte


class SiteBuilder(
    # Le socle : contenu, sortie, médias, texte, gabarit commun.
    Sortie,
    Medias,
    OutilsTexte,
    Gabarit,
    FichiersTechniques,
    # Les composants réutilisés par plusieurs pages.
    EnTete,
    PiedDePage,
    FilAriane,
    CarteLivre,
    VitrineCollections,
    Galerie,
    CartesProjets,
    # Une page du site par classe.
    PageAccueil,
    PageCatalogue,
    PagesLivres,
    PagesPersonnes,
    PagesCollections,
    PageActualites,
    PagesEditoriales,
    PageMaison,
    PagePlanDuSite,
    Page404,
):
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
        # Les images optimisées sont conservées d'une génération à l'autre. Ce dossier
        # est délibérément hors de dist/ et de .dist-build/, qui sont effacés à chaque
        # fois. Le supprimer est sans conséquence : il se reconstruit tout seul.
        self.cache_medias = self.root / ".cache-medias"
        self.frontend_dir = self.root / "frontend"
        report_name = "site-build-preview.json" if include_drafts else "site-build.json"
        self.report_path = self.root / "reports" / report_name
        self.template = (self.frontend_dir / "templates" / "base.html").read_text(encoding="utf-8")
        # L'empreinte force le navigateur à recharger le style et le script après une
        # modification. Le CSS n'existe plus comme fichier unique : c'est le résultat
        # du recollage qui est pris en compte, sinon retoucher un morceau passerait
        # inaperçu et les visiteurs garderaient l'ancienne feuille en cache.
        asset_digest = hashlib.sha256()
        asset_digest.update(assembler_css(self.frontend_dir).encode("utf-8"))
        asset_digest.update((self.frontend_dir / "assets/js/site.js").read_bytes())
        self.asset_version = asset_digest.hexdigest()[:12]

        content = load_content(self.root, include_drafts=include_drafts)
        self.books = content["books"]
        self.people = content["people"]
        self.collections = content["collections"]
        self.pages = content["pages"]
        self.news = content["news"]
        self.projects = content["projects"]
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
        self.collection_logo_media: dict[str, str] = {}
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
            # Parmi elles, celles reprises du cache faute d'avoir changé.
            "imagesReprises": 0,
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
