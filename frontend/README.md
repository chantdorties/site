# Frontend du nouveau site

Ce dossier contient les sources communes du site HTML/CSS/JavaScript :

- `templates/base.html` : structure commune de toutes les pages ;
- `assets/css/site.css` : mise en page et composants visuels ;
- `assets/js/site.js` : menu mobile, retour en haut et galeries ;
- `assets/js/catalogue.js` : recherche et filtres du catalogue ;
- `assets/js/people.js` : recherche et filtres de l'annuaire.

Les pages finales ne doivent pas être modifiées directement dans `dist/`.

## Développement avec actualisation automatique

```bash
make dev
```

Ouvrir `http://localhost:8766/`. Les modifications de CSS et JavaScript sont
recopiées immédiatement. Les modèles HTML, JSON et médias déclenchent une
nouvelle génération, puis le navigateur est actualisé automatiquement.

Si le port 8766 est déjà utilisé :

```bash
make dev DEV_PORT=8767
```

## Génération de production

```bash
python3 tools/build-site.py --root .
```

Les pages marquées `aVerifier` sont exclues de cette version.

## Prévisualisation avec les brouillons

```bash
python3 tools/build-site.py --root . --output dist-preview --include-drafts
```

## Prévisualisation locale

```bash
python3 -m http.server 8000 --directory dist
```

Ouvrir ensuite `http://localhost:8000/`.

## Tests

```bash
python3 -m unittest tools/test_refined_data.py tools/test_built_site.py -v
```
