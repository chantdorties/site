"""La page Collections et la page de chaque collection.

`build_collections_index` dessine /collections/ : titre puis la vitrine partagée
(composants/vitrine_collections.py).

`build_collection_pages` dessine une page par collection : emblème, description, puis
la grille des livres qui la composent, via la carte partagée
(composants/carte_livre.py).

Le style correspondant est dans frontend/assets/css/site.css :
règles .page-heading, .collection-emblem, .collection-showcase, .book-grid
"""

from __future__ import annotations

from ..outils import e


class PagesCollections:
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


    def build_collection_pages(self) -> None:
        for collection in self.collections:
            books = [self.books_by_slug[slug] for slug in collection["livres"]]
            cards = "".join(self.render_book_card(book) for book in books)
            logo = ""
            if collection["slug"] in self.collection_logo_media:
                logo_source = self.collection_logo_media[collection["slug"]]
                logo_alt = collection["logoAlt"] or f"Emblème de la collection {collection['titre']}"
                logo = (
                    f'<img class="collection-emblem" src="{logo_source}" '
                    f'alt="{e(logo_alt)}" width="180" height="180">'
                )
            content = f"""
<header class="page-heading"><div class="container">
  {self.render_breadcrumbs([('Accueil', '/'), ('Collections', '/collections/'), (collection['titre'], None)])}
  {logo}
  <p class="eyebrow">{collection['nombreLivres']} {'livres' if collection['nombreLivres'] > 1 else 'livre'}</p><h1>{e(collection['titre'])}</h1><p class="lead">{e(collection['description'])}</p>
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

