"""La vitrine des collections.

Une tuile par collection : son emblème, son numéro d'ordre, son titre, sa description,
un lien « Découvrir N livres », et sur la droite jusqu'à trois couvertures en éventail.
Elle sert sur l'accueil (titres de niveau 3) et sur la page Collections (niveau 2).

Le style correspondant est dans frontend/assets/css/25-vitrine-collections.css
"""

from __future__ import annotations

from ..icones import icon
from ..outils import e


class VitrineCollections:
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
            # L’emblème est décoratif ici : le nom de la collection le suit immédiatement.
            logo = ""
            if item["slug"] in self.collection_logo_media:
                logo = f'<img class="collection-showcase__emblem" src="{self.collection_logo_media[item["slug"]]}" alt="" loading="lazy" width="90" height="90">'
            tiles.append(
                f"""
<a class="collection-showcase__item" href="/collections/{e(item['slug'])}/">
  <span class="collection-showcase__copy">
    {logo}
    <span class="collection-showcase__number">Collection {index:02d}</span>
    <h{heading_level}>{e(item['titre'])}</h{heading_level}>
    <span class="collection-showcase__description">{e(self.texte_brut(item['description']))}</span>
    <span class="collection-showcase__link">Découvrir {e(count)} {icon('arrow-right')}</span>
  </span>
  <span class="collection-showcase__covers" aria-hidden="true">{covers}</span>
</a>""".strip()
            )
        return f'<div class="collection-showcase">{"".join(tiles)}</div>'
