# Site des Éditions Chant d’orties

Refonte statique du site des Éditions Chant d’orties en HTML, CSS et JavaScript natifs.

## Installation

```bash
python3 -m pip install -r requirements.txt
```

La génération des extraits PDF utilise également `poppler-utils` et `ghostscript`
lorsqu’ils sont installés sur la machine.

## Développement

```bash
make dev
```

Le site est alors disponible sur <http://127.0.0.1:8766/> avec actualisation automatique.

## Génération

```bash
make build
```

Les fichiers prêts à publier sont générés dans `dist/`.

## Tests

```bash
make test
```

Les sources du nouveau site se trouvent dans `frontend/`, les données affinées dans
`migration/front-data/` et les médias utilisés dans `migration/front-assets/`.

Le dossier `dist/` contient la version statique prête à publier.
