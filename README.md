# Chant d’orties

Ce dépôt conserve l’ancien site à la racine et isole sa nouvelle version dans
[`nouveau-site/`](nouveau-site/README.md).

## Nouvelle version

```bash
cd nouveau-site
make dev
```

Le dossier contient tout ce qui est utilisé par la V2 :

- `content/` : données éditoriales et médias ;
- `frontend/` : modèles, styles, scripts et administration ;
- `config/` : configuration fonctionnelle et anciennes redirections ;
- `tools/` : génération, validation, développement et déploiement ;
- `docs/` : documentation d’administration et de déploiement ;
- `dist/`, `dist-preview/` et `reports/` : résultats générés et ignorés par Git.

Les autres dossiers présents à la racine appartiennent à l’ancien site ou à sa
migration. Ils ne sont pas utilisés pour générer la nouvelle version.
