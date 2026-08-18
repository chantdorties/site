"""La galerie d'images des pages de livre et de personne.

Chaque vignette est un bouton ; un clic ouvre l'image en grand dans une fenêtre
superposée. L'ouverture et la fermeture sont assurées par
frontend/assets/js/site.js.

Le style correspondant est dans frontend/assets/css/site.css :
règles .gallery-grid, .gallery-item, .gallery-dialog, .dialog-close
"""

from __future__ import annotations

from ..icones import icon
from ..outils import e


class Galerie:
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

