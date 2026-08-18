"""Le fil d'Ariane : « Accueil / Catalogue / Le chien anarchiste ».

Placé en haut des pages intérieures, il rappelle où l'on se trouve. Le dernier élément
n'est pas un lien puisqu'il désigne la page courante.

Le style correspondant est dans frontend/assets/css/site.css, règle .breadcrumbs
"""

from __future__ import annotations

from ..outils import e


class FilAriane:
    def render_breadcrumbs(self, items: list[tuple[str, str | None]]) -> str:
        parts = []
        for label, href in items:
            if href:
                parts.append(f'<a href="{href}">{e(label)}</a><span aria-hidden="true">/</span>')
            else:
                parts.append(f'<span aria-current="page">{e(label)}</span>')
        return f'<nav class="breadcrumbs" aria-label="Fil d’Ariane">{"".join(parts)}</nav>'

