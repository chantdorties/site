"""L'assemblage d'une page complète.

`render_page` prend le contenu d'une page, y ajoute l'en-tête et le pied de page, et
glisse le tout dans le squelette commun frontend/templates/base.html — c'est là que se
trouve le <head> du site : titre, description, icône, appel de la feuille de style.

`seo_values` choisit le titre et la description vus par les moteurs de recherche :
ceux saisis dans l'administration s'ils existent, sinon ceux de la page.
"""

from __future__ import annotations

import json
from typing import Any

from .outils import absolute_url, e, truncate


class Gabarit:
    def render_page(
        self,
        *,
        title: str,
        description: str,
        route: str,
        content: str,
        active: str,
        body_class: str = "",
        draft: bool = False,
        scripts: list[str] | None = None,
        og_type: str = "website",
        og_image: str | None = None,
        structured_data: dict[str, Any] | None = None,
    ) -> str:
        page_title = title if route == "/" else f"{title} | {self.site_settings['nom']}"
        canonical_url = absolute_url(self.base_url, route)
        canonical = f'<link rel="canonical" href="{e(canonical_url)}">'
        robots = '<meta name="robots" content="noindex, nofollow">' if draft else ""
        og_image_tag = ""
        if og_image:
            og_image_tag = f'<meta property="og:image" content="{e(absolute_url(self.base_url, og_image))}">'
        structured = ""
        if structured_data:
            structured = (
                '<script type="application/ld+json">'
                + json.dumps(structured_data, ensure_ascii=False).replace("</", "<\\/")
                + "</script>"
            )
        page_scripts = "".join(
            f'<script type="module" src="{e(script)}"></script>' for script in (scripts or [])
        )
        draft_notice = ""
        if draft:
            draft_notice = (
                '<div class="draft-notice"><div class="container">'
                "Prévisualisation : ce contenu doit être validé avant publication."
                "</div></div>"
            )

        replacements = {
            "{{page_title}}": e(page_title),
            "{{description}}": e(truncate(self.texte_brut(description))),
            "{{robots}}": robots,
            "{{canonical}}": canonical,
            "{{og_type}}": e(og_type),
            "{{og_image}}": og_image_tag,
            "{{structured_data}}": structured,
            "{{body_class}}": e(body_class),
            "{{asset_version}}": self.asset_version,
            "{{header}}": self.render_header(active),
            "{{content}}": draft_notice + content,
            "{{footer}}": self.render_footer(),
            "{{page_scripts}}": page_scripts,
        }
        result = self.template
        for placeholder, replacement in replacements.items():
            result = result.replace(placeholder, replacement)
        return result


    def seo_values(
        self,
        record: dict[str, Any],
        *,
        default_title: str,
        default_description: str,
        default_image: str | None = None,
    ) -> tuple[str, str, str | None]:
        seo = record.get("seo") or {}
        image_path = seo.get("image")
        return (
            seo.get("titre") or default_title,
            seo.get("description") or default_description,
            self.seo_image_media.get(image_path) if image_path else default_image,
        )

