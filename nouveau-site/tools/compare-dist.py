#!/usr/bin/env python3
r"""Compare deux sites générés : celui de référence et celui qu'on vient de produire.

Sert de filet de sécurité quand on range le générateur ou l'administration sans
vouloir changer le site : toute différence est une régression, sauf écart voulu.

    python3 tools/compare-dist.py /chemin/vers/dist-reference dist

Les fichiers HTML sont comparés après avoir supprimé les retours à la ligne et
l'indentation entre deux balises (`>\n  <` devient `><`) : réindenter un morceau de
HTML ne change pas la page. Une espace seule entre deux balises est gardée, car
entre deux liens elle se voit.

Tous les autres fichiers (sitemap, .htaccess, data/*.json, images…) le sont octet
pour octet. Le script affiche chaque fichier qui diffère et sort en erreur s'il y
en a un.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

BLANCS_ENTRE_BALISES = re.compile(rb">[ \t]*\n\s*<")


def normaliser(chemin: Path) -> bytes:
    contenu = chemin.read_bytes()
    if chemin.suffix == ".html":
        return BLANCS_ENTRE_BALISES.sub(b"><", contenu).strip()
    return contenu


def fichiers(racine: Path) -> set[Path]:
    return {chemin.relative_to(racine) for chemin in racine.rglob("*") if chemin.is_file()}


def comparer(reference: Path, actuel: Path) -> list[str]:
    ecarts = []
    avant, apres = fichiers(reference), fichiers(actuel)
    ecarts += [f"disparu : {chemin}" for chemin in sorted(avant - apres)]
    ecarts += [f"nouveau : {chemin}" for chemin in sorted(apres - avant)]
    for chemin in sorted(avant & apres):
        ancien, nouveau = normaliser(reference / chemin), normaliser(actuel / chemin)
        if ancien == nouveau:
            continue
        ecarts.append(f"modifié : {chemin}")
        if chemin.suffix in {".html", ".json", ".xml", ".txt", ".htaccess"} or chemin.name == ".htaccess":
            lignes_avant = ancien.decode("utf-8", "replace").replace("><", ">\n<").splitlines()
            lignes_apres = nouveau.decode("utf-8", "replace").replace("><", ">\n<").splitlines()
            diff = list(difflib.unified_diff(lignes_avant, lignes_apres, lineterm="", n=1))
            ecarts += [f"    {ligne}" for ligne in diff[2:22]]
    return ecarts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("reference", type=Path)
    parser.add_argument("actuel", type=Path, nargs="?", default=Path("dist"))
    args = parser.parse_args()
    ecarts = comparer(args.reference, args.actuel)
    if ecarts:
        print("\n".join(ecarts))
        return 1
    print("Sites identiques.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
