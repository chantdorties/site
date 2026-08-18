#!/usr/bin/env python3
"""Generate the public Chant d'orties website from the editable JSON content.

Ce fichier ne fait que lire la ligne de commande et lancer la génération. Le HTML du
site est dans tools/rendu/ : un fichier par page dans rendu/pages/, un fichier par
morceau réutilisé dans rendu/composants/.

Pour savoir quel fichier ouvrir afin de modifier l'apparence du site, voir
docs/GUIDE-APPARENCE.md.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from rendu.constructeur import SiteBuilder
from rendu.outils import read_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", type=Path, default=Path("dist"))
    parser.add_argument("--include-drafts", action="store_true")
    parser.add_argument("--base-url", help="Remplace temporairement le domaine défini dans les réglages")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    builder = SiteBuilder(
        root,
        output,
        include_drafts=args.include_drafts,
        base_url=args.base_url,
    )
    builder.build()
    report = read_json(builder.report_path)
    print(
        f"Site generated in {output}: {report['pagesHtml']} HTML pages, "
        f"{report['medias']['images']} optimized images, "
        f"{report['medias']['documents']} documents."
    )


if __name__ == "__main__":
    main()
