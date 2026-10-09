# Consignes pour les agents — site des Éditions Chant d’orties

À lire en entier au début de chaque session. Ce fichier résume l’architecture, le style
et les règles du site ; le détail est dans `docs/`. **Après chaque changement validé et
poussé, ajouter une ligne au Journal en bas de ce fichier**, et corriger les parties
plus haut que le changement rend fausses.

## Le site en bref

Site statique d’une maison d’édition jeunesse : 64 livres, auteurs et illustrateurs,
collections, actualités, projets, pages de la maison. Vente par boutons PayPal (panier
tenu chez PayPal). La rédaction écrit dans une administration Decap CMS ; chaque
enregistrement est un commit JSON sur GitHub, qui régénère et publie le site.

| Élément | Où |
|---|---|
| Dépôt | `chantdorties/site` (GitHub). Racine Git = dossier parent ; tout le code est dans `nouveau-site/` (l’ancien site reste local, ignoré). |
| Site public | pages perso Free, `https://chantdorties.pages-perso.free.fr/` (admin aussi sous `/admin/`) |
| Administration + relais OAuth | OVH du prestataire, `https://orties-admin.varascundo.com/` |
| Aperçus des PR | Netlify `deploy-preview-<n>--chantdorties-admin.netlify.app` |
| Tutoriel de l’admin | `https://tuto-des-orties.varascundo.com/` (lien « Tutoriel » dans la barre de l’admin) |

## Architecture

- **Contenus** `content/` — un JSON par fiche :
  - `livres/`, `personnes/`, `collections/`, `actualites/`, `projets/`, `pages/` (« Mes pages », adresse = nom du fichier) ;
  - `pages-du-site/` (« Pages principales ») : `accueil.json` et une fiche par page engendrée (catalogue, personnes, collections, actualites, maison, projets) ;
  - `reglages/` : `site`, `navigation`, `footer`, `paiement`, `apparence` ;
  - `media/` : images et PDF ; `schema.json`.
- **Chargement et validation** `tools/content_data.py` : `load_content` lit tout, applique les valeurs par défaut, **refuse** les formes anciennes (fichiers déplacés, champs renommés) avec un message qui dit où aller. `load_settings` expose `settings["accueil"]` et `settings["pages"][nom]`.
- **Générateur** `tools/build-site.py` → `tools/rendu/` :
  - `constructeur.py` assemble, `pages/*.py` une page par fichier, `composants/*.py` les morceaux partagés (en-tête, titre de page `render_page_heading`, formulaire PayPal `render_paypal_form`, cartes…) ;
  - `medias.py` (images, PDF), `sortie.py` (fichiers et `data/*.json` publics lus par l’admin), `technique.py` (redirections, sitemap, `.htaccess`).
- **Front** `frontend/` : `templates/`, `assets/css/` (fichiers numérotés par zone : `0x` base, `1x` composants, `2x`–`4x` pages, `9x` points de rupture), `assets/js/`.
- **Admin** `frontend/admin/` : `config.yml` (Decap 3.15.1 embarqué dans `vendor/`, aucun CDN), `preview.js` (aperçus + widgets maison : `groupe` repliable, description SEO), `vignettes.js` (miniatures des listes), `menu-pages.js` (groupe « Pages » du menu), `tutoriel.js`, `admin.css`, `preview.css`. CSP stricte dans `index.html` : pas de script en ligne.
- **CI** `../.github/workflows/` : `site.yml` valide (`make validate`) chaque PR et **publie sur Free à chaque push sur `main`** ; `admin.yml` publie l’admin/relais sur OVH ; `apercu.yml`, `restore.yml`.

## Fonctionnement de l’admin (choix déjà tranchés)

- Chaque partie du site se règle à **un seul endroit**. Menu : Réglages du site · Pages ▾ (Mes pages, Pages principales) · Livres · Auteurs et illustrateurs · Collections · Actualités · Projets.
- Formulaires : « L’essentiel » en tête, blocs propres ensuite, « ▸ Réglages techniques » replié à la fin. Composants partagés par ancres YAML (une seule définition chacun ; une ancre doit précéder ses alias dans le fichier).
- Créer une page = Mes pages › + Page › titre › texte › Publier ; adresse tirée du titre, ordre automatique, sections typées (`texte`/`livres`/`offre`), liens typés.
- Livres mis en avant : cochés dans la fiche, filtre « ★ » dans la liste ; nombre de couvertures dans Pages principales › Accueil.
- Les aperçus sont choisis par nom de rubrique **et** d’entrée : noms d’entrée uniques (préfixe `page_` dans Pages principales).
- La rédaction n’est pas technique : libellés et aides en mots simples, jamais de jargon (« slug », « carte », « SEO » seul…).

## Style de code

- Python et JS commentés en **français**, avec la même densité que l’existant : un en-tête qui dit à quoi sert le fichier et pourquoi, des commentaires sur les choix non évidents. Noms en français côté admin/JS et rendu, anglais pour les fonctions Python historiques (`load_content`, `render_*`).
- Typographie française dans les textes visibles : apostrophe ’, guillemets « », espaces.
- Pas de dépendance externe à l’exécution (CSP) ; pas de nouvel outil de build.
- Commits en Conventional Commits anglais : `type(scope): description`.

## Règles de travail

1. Partir d’une branche à jour : `git fetch && git checkout -b <type>/<sujet> origin/main`.
2. **Le site généré ne doit pas changer sans le vouloir** : construire dans un dossier à part puis `python3 tools/compare-dist.py <dist-référence> <dist-nouveau>` ; seuls les écarts voulus sont acceptés.
3. `make test` (ou les 4 modules `tools/test_*.py`) doit être vert. Ajouter un test pour chaque règle de validation nouvelle.
4. Vérifier dans le navigateur ce qui touche l’admin (`make admin`, port 8766).
5. Mettre à jour `docs/GUIDE-REDACTION.md` (rédaction) et `docs/ADMINISTRATION.md` (technique) quand le comportement change.
6. Pousser, ouvrir une PR, attendre le CI vert. **Demander avant de fusionner** : fusionner sur `main` met le site en ligne.
7. Ne jamais : publier/supprimer sur les serveurs (Free, OVH) sans accord ; afficher un secret ; committer des fichiers modifiés par l’utilisateur hors de la tâche (ex. `README.md`) ni `.playwright-cli/` — donc jamais `git commit -a`, toujours `git add <fichiers>` ; arrêter le `make admin` de l’utilisateur (il verrouille `dist/` : construire ailleurs).
8. Après un changement validé et poussé : **ajouter une ligne au Journal ci-dessous** (dans la même PR).

## Pièges connus

- Decap efface à l’enregistrement les champs absents du formulaire ; un widget `hidden` conserve la valeur.
- `gh pr edit` échoue (Projects classic) : utiliser `gh api -X PATCH repos/chantdorties/site/pulls/<n>`.
- Les PDF générés ne sont pas reproductibles octet pour octet : comparer sur une copie de la référence.
- Les éléments du menu Decap appartiennent à React : les décorer (classes, ajout) sans les déplacer.

## Journal

Une ligne par changement poussé : date · PR · ce qui change pour la rédaction ou le site.

- 2026-10-08 · #22 · Refonte de l’ergonomie de l’admin.
- 2026-10-08 · #23 · Cohérence : chaque partie du site réglée à un seul endroit, composants partagés, `render_page_heading`, `render_paypal_form`, `compare-dist.py`.
- 2026-10-08 · #24, #25 · Nombre de couvertures de l’accueil réglable ; aperçu de l’accueil avec les vraies couvertures.
- 2026-10-09 · #26, #27 · Vignettes dans les listes de l’admin : couvertures, emblèmes des collections, portraits ou initiales.
- 2026-10-09 · #28 · Création de page simplifiée (titre + texte), sections et liens typés ; « Pages principales » (`content/pages-du-site/`) ; « Mes pages » ; groupe « Pages ▾ » dans le menu.
- 2026-10-09 · #29 · Lien « Tutoriel » dans la barre du haut de l’admin.
- 2026-10-09 · #30 · Ce fichier `AGENTS.md` (et `CLAUDE.md` qui l’importe) : consignes lues à chaque session, journal des changements.
