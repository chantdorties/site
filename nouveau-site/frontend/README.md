# Frontend du nouveau site

Ce dossier contient les sources communes du site :

- `templates/base.html` : le `<head>` et la carcasse des pages publiques ;
- `assets/css/site.css` : mise en page et composants visuels ;
- `assets/js/site.js` : menu mobile, retour en haut et galeries ;
- `assets/js/catalogue.js` : recherche et filtres du catalogue ;
- `assets/js/people.js` : recherche et filtres de l’annuaire ;
- `admin/` : interface Decap CMS et formulaires de gestion des contenus.

Le HTML des pages elles-mêmes n’est pas ici : il est dans `tools/rendu/`, un fichier
par page dans `pages/` et un fichier par morceau réutilisé dans `composants/`. Pour
savoir quel fichier ouvrir, voir le [Guide de l’apparence](../docs/GUIDE-APPARENCE.md).

Les pages finales ne doivent pas être modifiées directement dans `dist/`.

## Développement

```bash
make dev
```

Ouvrir <http://127.0.0.1:8766/>. Les modifications des sources et des contenus
déclenchent une nouvelle génération et l’actualisation du navigateur.

Pour changer le port :

```bash
make dev DEV_PORT=8767
```

## Administration locale

```bash
make admin
```

Ouvrir <http://127.0.0.1:8766/admin/>. Les changements sont écrits directement
dans `content/` sans passer par GitHub.

## Brouillons

```bash
make preview
```

La prévisualisation contient aussi les enregistrements dont le champ `statut` vaut
`brouillon`. La génération normale ne les publie pas.
