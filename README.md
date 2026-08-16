# Site des Éditions Chant d’orties

Refonte statique du site des Éditions Chant d’orties en HTML, CSS et JavaScript natifs.

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
