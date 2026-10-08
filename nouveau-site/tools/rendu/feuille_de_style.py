"""Le recollage de la feuille de style.

Le CSS du site est découpé en fichiers courts dans frontend/assets/css/, un par
thème et par composant. La génération les remet bout à bout en un seul
dist/assets/css/site.css : le navigateur ne fait donc qu'une seule requête, comme
avant le découpage.

L'ordre compte : en CSS, à spécificité égale, c'est la dernière règle écrite qui
gagne. Les fichiers sont recollés par ordre alphabétique de nom, et le numéro en tête
de chaque nom fait coïncider cet ordre avec celui voulu. Renommer un fichier, c'est
donc déplacer ses règles dans la cascade — à ne pas faire à la légère.

Le thème choisi dans l'administration (content/reglages/apparence.json) s'ajoute
sous la forme d'un bloc :root glissé juste après 00-variables.css : il remplace les
valeurs par défaut des tokens, avant toute règle qui les utilise. Contrat complet :
docs/CONTRAT-APPARENCE.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from content_data import APPEARANCE_FONTS, validate_appearance_settings


# Le fichier qui déclare les valeurs par défaut des tokens : le bloc du thème le suit.
FICHIER_DES_TOKENS = "00-variables.css"

# Chaque clé du réglage Apparence et le token qu'elle alimente, dans l'ordre d'écriture.
# Seules ces clés deviennent du CSS : une clé inconnue n'est jamais recopiée.
COULEURS_DU_THEME = (
    ("couleurFond", "--color-background"),
    ("couleurSurface", "--color-surface"),
    ("couleurTexte", "--color-text"),
    ("couleurTexteSecondaire", "--color-muted"),
    ("couleurPrincipale", "--color-primary"),
    ("couleurPrincipaleFoncee", "--color-primary-dark"),
    ("couleurSecondaire", "--color-secondary"),
    ("couleurLiens", "--color-link"),
    ("couleurBoutons", "--color-button"),
)
POLICES_DU_THEME = (
    ("policeTitres", "--font-heading"),
    ("policeTexte", "--font-body"),
)


def morceaux_css(frontend_dir: Path) -> list[Path]:
    """Les morceaux de la feuille de style, dans leur ordre d'application."""
    return sorted((frontend_dir / "assets" / "css").glob("*.css"))


def bloc_du_theme(apparence: dict[str, Any]) -> str:
    """Les tokens du thème, traduits du réglage Apparence.

    Les valeurs sont revalidées ici : ce bloc est le seul endroit où une donnée
    éditable entre dans le CSS. Les polices passent par leur identifiant, la pile
    vient du code. Le bloc se termine par une ligne vide, comme chaque morceau.
    """
    validate_appearance_settings(apparence)
    declarations = [f"  {token}: {apparence[cle].lower()};" for cle, token in COULEURS_DU_THEME]
    declarations += [
        f"  {token}: {APPEARANCE_FONTS[apparence[cle]]};" for cle, token in POLICES_DU_THEME
    ]
    return (
        "/* Le thème choisi dans l'administration : content/reglages/apparence.json */\n"
        ":root {\n" + "\n".join(declarations) + "\n}\n\n"
    )


def feuille_de_style_complete(frontend_dir: Path, apparence: dict[str, Any]) -> str:
    """La feuille de style publiée : les morceaux tels quels, et le thème après les tokens.

    C'est la seule source du CSS final : l'empreinte de cache et le fichier écrit
    dans dist/ en proviennent tous deux. Chaque morceau se termine par une ligne
    vide, sauf le dernier : aucun séparateur n'est ajouté ici, sous peine de décaler
    le contenu d'origine.
    """
    morceaux = morceaux_css(frontend_dir)
    if not any(morceau.name == FICHIER_DES_TOKENS for morceau in morceaux):
        raise FileNotFoundError(frontend_dir / "assets" / "css" / FICHIER_DES_TOKENS)
    textes = []
    for morceau in morceaux:
        textes.append(morceau.read_text(encoding="utf-8"))
        if morceau.name == FICHIER_DES_TOKENS:
            textes.append(bloc_du_theme(apparence))
    return "".join(textes)
