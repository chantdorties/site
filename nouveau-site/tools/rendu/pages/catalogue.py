"""La page Catalogue.

Elle se compose d'un titre, d'un panneau de filtres (recherche, collection, type,
disponibilité), puis d'une grille vide au chargement. Les livres eux-mêmes sont
déposés par frontend/assets/js/catalogue.js, qui lit /data/livres.json : le HTML
ci-dessous ne contient donc aucun livre, seulement le décor et les champs.

Le style correspondant est dans frontend/assets/css/site.css :
règles .page-heading, .filter-panel, .filter-grid, .field, .results-bar, .book-grid
"""

from __future__ import annotations

from ..outils import e


class PageCatalogue:
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

