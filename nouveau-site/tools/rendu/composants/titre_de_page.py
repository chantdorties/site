"""Le titre d'une page intérieure : fil d'Ariane, surtitre, titre et introduction.

Toutes les pages autres que l'accueil et les fiches s'ouvrent ainsi : Catalogue,
Auteurs & illustrateurs, Collections et chaque collection, La maison, Actualités,
les pages de texte et le plan du site. Le balisage n'est écrit qu'ici.

Le style correspondant est dans frontend/assets/css/15-titre-de-page.css
"""

from __future__ import annotations

from ..outils import e


class TitreDePage:
    def render_page_heading(
        self,
        breadcrumbs: list[tuple[str, str | None]],
        title: str,
        *,
        eyebrow: str = "",
        introduction: str = "",
        before_title: str = "",
    ) -> str:
        """`introduction` est déjà du HTML (sortie de markdown_html) ; `before_title`
        aussi : le logo d'une collection, posé au-dessus de son surtitre."""
        lines = [self.render_breadcrumbs(breadcrumbs)]
        if before_title:
            lines.append(before_title)
        surtitre = f'<p class="eyebrow">{e(eyebrow)}</p>' if eyebrow else ""
        lines.append(f"{surtitre}<h1>{e(title)}</h1>")
        if introduction:
            lines.append(f'<div class="lead rich-text">{introduction}</div>')
        body = "\n".join(f"  {line}" for line in lines)
        return f'<header class="page-heading"><div class="container">\n{body}\n</div></header>'
