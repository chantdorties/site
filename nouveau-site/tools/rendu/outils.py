"""Les petits outils partagés par tous les fichiers de rendu.

Le plus important est `e()` : il rend un texte inoffensif avant de l'insérer dans une
page. Tout texte venant du contenu doit passer par lui, sinon un guillemet ou un
chevron dans un titre casserait la page. Ne jamais le retirer d'un `{e(...)}`.
"""

from __future__ import annotations

import html
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

def e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def slugify(value: str) -> str:
    normalized = value.lower().replace("’", "'")
    normalized = "".join(
        character
        for character in unicodedata.normalize("NFKD", normalized)
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-") or "fichier"


def monogram(name: str) -> str:
    words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+", name)
    return "".join(word[0].upper() for word in words[:2]) or "?"


def format_price(cents: int | None) -> str | None:
    if cents is None:
        return None
    euros, remainder = divmod(cents, 100)
    return f"{euros} €" if remainder == 0 else f"{euros},{remainder:02d} €"


def truncate(value: str, maximum: int = 158) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= maximum:
        return value
    return value[: maximum - 1].rsplit(" ", 1)[0] + "…"


def absolute_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"

