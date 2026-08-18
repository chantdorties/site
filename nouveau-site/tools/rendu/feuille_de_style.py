"""Le recollage de la feuille de style.

Le CSS du site est découpé en fichiers courts dans frontend/assets/css/, un par
thème et par composant. La génération les remet bout à bout en un seul
dist/assets/css/site.css : le navigateur ne fait donc qu'une seule requête, comme
avant le découpage.

L'ordre compte : en CSS, à spécificité égale, c'est la dernière règle écrite qui
gagne. Les fichiers sont recollés par ordre alphabétique de nom, et le numéro en tête
de chaque nom fait coïncider cet ordre avec celui voulu. Renommer un fichier, c'est
donc déplacer ses règles dans la cascade — à ne pas faire à la légère.
"""

from __future__ import annotations

from pathlib import Path


def morceaux_css(frontend_dir: Path) -> list[Path]:
    """Les morceaux de la feuille de style, dans leur ordre d'application."""
    return sorted((frontend_dir / "assets" / "css").glob("*.css"))


def assembler_css(frontend_dir: Path) -> str:
    """Les morceaux remis bout à bout, tels quels.

    Chaque morceau se termine par une ligne vide, sauf le dernier : aucun séparateur
    n'est ajouté ici, sous peine de décaler le contenu d'origine.
    """
    return "".join(
        morceau.read_text(encoding="utf-8") for morceau in morceaux_css(frontend_dir)
    )
