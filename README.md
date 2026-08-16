# Site des Éditions Chant d’orties

Site statique en HTML, CSS et JavaScript natifs. Les contenus sont enregistrés dans
des fichiers JSON versionnés par Git ; aucune base de données n’est nécessaire.

## Organisation

- `content/` : livres, personnes, collections, pages, actualités et médias modifiables ;
- `frontend/` : modèle HTML, styles, scripts et interface d’administration ;
- `tools/` : validation, génération, serveur local et déploiement ;
- `config/` : redirections des anciennes adresses ;
- `dist/` : résultat généré, ignoré par Git et prêt à publier ;
- `.github/workflows/` : validation, publication et restauration automatiques.

Ne pas modifier `dist/` directement : il est recréé à chaque génération.

## Installation

```bash
python3 -m pip install -r requirements.txt
```

La génération des PDF nécessite aussi `poppler-utils` et `ghostscript`.

## Développement

```bash
make dev
```

Le site est disponible sur <http://127.0.0.1:8766/> et se recharge après une
modification dans `content/`, `frontend/` ou `config/`.

Pour modifier les contenus avec l’interface locale :

```bash
make admin
```

L’administration est alors disponible sur <http://127.0.0.1:8766/admin/>.
Cette commande nécessite Node.js et lance automatiquement le proxy local Decap.

Sans `make`, les commandes équivalentes sont :

```bash
python3 tools/dev-server.py --root . --port 8766
python3 tools/build-site.py --root .
python3 -m unittest tools/test_content_data.py tools/test_built_site.py tools/test_deploy.py -v
```

## Production

```bash
make validate
```

Cette commande valide les JSON et médias, génère `dist/`, puis contrôle les pages,
liens, scripts, images, PDF, brouillons et redirections.

Les modes d’emploi complets sont dans [Administration](docs/ADMINISTRATION.md) et
[Déploiement](docs/DEPLOIEMENT.md).
