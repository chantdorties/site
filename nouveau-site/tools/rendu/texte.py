"""Le traitement des textes libres saisis dans l'administration.

`linkify_text` transforme en liens cliquables les adresses internet et les courriels
écrits au fil du texte. `editorial_link` fabrique le lien d'un bouton ou d'une entrée
de liste, selon qu'il pointe vers un document, un livre, une page ou un site externe.
"""

from __future__ import annotations

import re
from typing import Any

from .icones import icon
from .outils import e


class OutilsTexte:
    def linkify_text(self, value: str, *, internal_links: dict[str, str] | None = None) -> str:
        escaped = e(value)
        escaped = re.sub(
            r"(?<![\w@])(https?://[^\s&lt;]+)",
            lambda match: f'<a href="{match.group(1)}" target="_blank" rel="noopener noreferrer">{match.group(1)}</a>',
            escaped,
        )
        escaped = re.sub(
            r"(?<![\w@])([\w.+-]+@[\w.-]+\.[A-Za-z]{2,})",
            lambda match: f'<a href="mailto:{match.group(1)}">{match.group(1)}</a>',
            escaped,
        )
        for label, href in (internal_links or {}).items():
            escaped = escaped.replace(e(label), f'<a href="{e(href)}">{e(label)}</a>')
        return escaped

    def editorial_link(self, link: dict[str, Any]) -> str | None:
        link_type = link["type"]
        label = link.get("texte") or "Consulter le lien"
        if link_type == "document":
            href = self.document_media.get(link["href"])
            if not href:
                return None
            return f'<a href="{href}" target="_blank">{icon("file")} {e(label)}</a>'
        if link_type == "livre":
            return f'<a href="/livres/{e(link["slug"])}/">{e(label)}</a>'
        if link_type == "page":
            href = "/" if link["slug"] == "accueil" else f'/{link["slug"]}/'
            return f'<a href="{href}">{e(label)}</a>'
        href = link.get("href")
        if not href:
            return None
        if link_type == "externe":
            display = link.get("texte") or re.sub(r"^https?://(?:www\.)?", "", href).rstrip("/")
            return f'<a href="{e(href)}" target="_blank" rel="noopener noreferrer">{e(display)} {icon("external")}</a>'
        return f'<a href="{e(href)}">{e(label)}</a>'

