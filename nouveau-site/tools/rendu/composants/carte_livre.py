"""La carte d'un livre.

Elle apparaît dans le catalogue, sur l'accueil et sur les pages de collection :
la couverture cliquable, le nom de la collection, le titre, puis le type d'ouvrage,
l'âge minimum et le prix réunis sur une seule ligne séparée par des points médians.

Le style correspondant est dans frontend/assets/css/site.css :
règles .book-card, .book-card__cover, .book-card__collection, .book-card__meta
"""

from __future__ import annotations

from typing import Any

from ..libelles import TYPE_LABELS
from ..outils import e, format_price


class CarteLivre:
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

