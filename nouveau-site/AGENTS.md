# Consignes pour les agents — site des Éditions Chant d’orties

À lire en entier au début de chaque session. Ce fichier résume l’architecture, le style
et les règles du site ; le détail est dans `docs/`. **Après chaque changement validé et
poussé, ajouter une ligne au Journal en bas de ce fichier**, et corriger les parties
plus haut que le changement rend fausses. **Après un changement significatif pour la
rédaction, mettre à jour le tutoriel et le pousser en ligne** (voir « Le tutoriel »).

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
- **Admin** `frontend/admin/` : `config.yml` (Decap 3.15.1 embarqué dans `vendor/`, aucun CDN), `preview.js` (aperçus + widgets maison : `groupe` repliable, description SEO), `blocs.js` (blocs de mise en forme de l’éditeur), `vignettes.js` (miniatures des listes), `menu-pages.js` (groupe « Pages » du menu), `tutoriel.js`, `admin.css`, `preview.css`. CSP stricte dans `index.html` : pas de script en ligne.
- **CI** `../.github/workflows/` : `site.yml` valide (`make validate`) chaque PR et **publie sur Free à chaque push sur `main`** ; `admin.yml` publie l’admin/relais sur OVH ; `apercu.yml`, `restore.yml`.

## Fonctionnement de l’admin (choix déjà tranchés)

- Chaque partie du site se règle à **un seul endroit**. Menu : Réglages du site · Pages ▾ (Mes pages, Pages principales) · Livres · Auteurs et illustrateurs · Collections · Actualités · Projets.
- Formulaires : « L’essentiel » en tête, blocs propres ensuite, « ▸ Réglages techniques » replié à la fin. Composants partagés par ancres YAML (une seule définition chacun ; une ancre doit précéder ses alias dans le fichier).
- Créer une page = Mes pages › + Page › titre › texte › Publier ; adresse tirée du titre, ordre automatique, sections typées (`texte`/`livres`/`offre`), liens typés.
- Supprimer : bouton actif partout (sauf réglages et pages principales). Une suppression ne doit jamais bloquer la publication : liens d’agrément retirés à la génération, liens de structure gardés par `suppression.js` (`data/suppression.json`), médias inutilisés tolérés. Voir `docs/ADMINISTRATION.md` › « Suppression ».
- Masquer plutôt que supprimer : cases « Masquer ce bloc » (accueil, bloc Facebook) et « Masquer cette section », décochées par défaut. Les pages principales reçoivent les mêmes sections que Mes pages dans « Sections ajoutées » (`sectionsLibres`, avec un `emplacement`) ; les champs des sections sont définis une fois, dans la fiche Accueil de `config.yml`.
- Livres mis en avant : cochés dans la fiche, filtre « ★ » dans la liste ; nombre de couvertures dans Pages principales › Accueil.
- Les aperçus sont choisis par nom de rubrique **et** d’entrée : noms d’entrée uniques (préfixe `page_` dans Pages principales).
- Mise en forme : barré partout ; dans les textes longs (pages, actualités), blocs « Texte mis en valeur » (centré, couleur de la palette, souligné), « Encadré », « Séparateur », écrits `::: valeur …` / `::: encadre …` / `---` `***`. Options en liste blanche (`OPTIONS_BLOCS`, `tools/rendu/texte.py`), jamais de couleur libre ni de mise en forme mot à mot.
- Masquer / laisser vide : cases « Masquer ce bloc » (accueil : information, collections, suivre ; actualités : Facebook) et « Masquer cette section » (Mes pages), toujours au sens « masquer », décochées par défaut (une case « Afficher » absente apparaîtrait décochée dans Decap). Accueil : seul le grand titre est obligatoire, un champ vide n’est pas dessiné.
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
9. Après un changement **significatif** pour la personne qui administre (écran ajouté, renommé ou déplacé, parcours modifié, nouvelle règle de saisie) : **mettre à jour le tutoriel et le pousser en ligne** (section suivante). Un correctif invisible dans l’admin n’en demande pas.

## Le tutoriel

- Dossier `../tuto/` (à côté de `nouveau-site/`), **dépôt Git séparé** `chantdorties/tuto-des-orties`, branche `main`. Servi tel quel (Apache, OVH) sur `https://tuto-des-orties.varascundo.com/`. **Pousser sur `main` le met en ligne, avec un délai** : le serveur récupère le dépôt de lui-même, pas tout de suite (constaté le 2026-10-09 : 15 à 40 min). Pendant la mise à jour, le site affiche quelques minutes la page OVH « Site not installed » : c’est normal. Vérifier plus tard, sans conclure trop tôt à un échec.
- Captures : 1440 × 900 (émulation du navigateur), admin locale à jour, menu « Pages » déplié, **attendre que l’aperçu et les vignettes soient chargés** avant de capturer, puis relire chaque image avec sa légende. La médiathèque s’ouvre par le bouton Media (pas d’adresse propre).
- Fichiers : `index.html` (le guide, chapitres et encadrés), `assets/` (CSS, JS, captures `assets/images/*.webp`), `README.md` (version illustrée : commit de référence du site), `sources/` (`version-reference.md`, `matrice-captures.md`, `captures-a-refaire.md`), `skill.md` (référence détaillée du site, à garder cohérente avec ce fichier).
- Mise à jour : corriger les textes de `index.html` touchés par le changement (noms d’écrans, chemins « Rubrique → Entrée », étapes) ; noter dans `sources/captures-a-refaire.md` les captures devenues fausses ; mettre à jour le commit de référence dans `README.md` et la date « Guide vérifié le … » ; puis `git -C ../tuto add <fichiers> && git commit && git push`.
- Vérifier la mise en ligne : `curl -s https://tuto-des-orties.varascundo.com/ | sha1sum` doit égaler `sha1sum ../tuto/index.html`.
- Captures : jamais de mot de passe, jeton, compte GitHub ni donnée privée ; prises dans l’admin locale, sans rien enregistrer.

## Pièges connus

- Decap efface à l’enregistrement les champs absents du formulaire ; un widget `hidden` conserve la valeur.
- `gh pr edit` échoue (Projects classic) : utiliser `gh api -X PATCH repos/chantdorties/site/pulls/<n>`.
- Les PDF générés ne sont pas reproductibles octet pour octet : comparer sur une copie de la référence.
- Les éléments du menu Decap appartiennent à React : les décorer (classes, ajout) sans les déplacer.
- Les tests tournent sur le contenu réel à chaque publication : **ne jamais y nommer une fiche** (livre, page, personne…) ni figer un compte. La rédaction peut la modifier ou la supprimer, et la publication serait bloquée (#35). Utiliser `exemple()` ou calculer l’attendu depuis le contenu.

## Journal

Une ligne par changement poussé : date · PR · ce qui change pour la rédaction ou le site.

- 2026-10-08 · #22 · Refonte de l’ergonomie de l’admin.
- 2026-10-08 · #23 · Cohérence : chaque partie du site réglée à un seul endroit, composants partagés, `render_page_heading`, `render_paypal_form`, `compare-dist.py`.
- 2026-10-08 · #24, #25 · Nombre de couvertures de l’accueil réglable ; aperçu de l’accueil avec les vraies couvertures.
- 2026-10-09 · #26, #27 · Vignettes dans les listes de l’admin : couvertures, emblèmes des collections, portraits ou initiales.
- 2026-10-09 · #28 · Création de page simplifiée (titre + texte), sections et liens typés ; « Pages principales » (`content/pages-du-site/`) ; « Mes pages » ; groupe « Pages ▾ » dans le menu.
- 2026-10-09 · #29 · Lien « Tutoriel » dans la barre du haut de l’admin.
- 2026-10-09 · #30 · Ce fichier `AGENTS.md` (et `CLAUDE.md` qui l’importe) : consignes lues à chaque session, journal des changements, règle de mise à jour du tutoriel. Tutoriel : chapitre Réglages corrigé (les pages n’y sont plus).
- 2026-10-09 · #31 · Admin : titres des sections typées qui chevauchaient le nom du type ; ancien nom « Pages du site » oublié. Tutoriel : les 20 captures refaites sur `main`, 4 nouvelles (menu Pages, Pages principales, nouvelle page).
- 2026-10-09 · #34 · Mise en forme : barré partout ; blocs « Texte mis en valeur » (centré, couleur de la palette, souligné), « Encadré », « Séparateur » dans les pages et les actualités.
- 2026-10-09 · #36 · Test de l’accueil : les conditions de vente sont comparées au contenu saisi, plus à une formulation figée (elle bloquait la publication après la mise à jour du client, #35).
- 2026-10-09 · #37 · Cases « Masquer ce bloc » (accueil, bloc Facebook) et « Masquer cette section » (Mes pages) ; accueil : seul le grand titre est obligatoire, un champ vide disparaît ; petite ligne et introduction facultatives sur les pages principales.
- 2026-10-09 · #38 · « Sections ajoutées » sur chaque page principale : les mêmes sections que Mes pages (texte, livres, offre PayPal), placées à un emplacement choisi (entre les blocs de l’accueil, au-dessus ou sous la liste ailleurs) et masquables.
- 2026-10-09 · #39 · « Anciennes adresses » cachées dans l’admin (widget `hidden`, valeur gardée à l’enregistrement) : les redirections de l’ancien site restent actives, à compléter au besoin dans le JSON.
- 2026-10-09 · #40 · Bouton « Supprimer » sur livres, personnes, collections, actualités et pages : ce qui citait la fiche s’en passe (liens retirés, livre mis en avant choisi d’office), fiches dont d’autres dépendent gardées dans l’admin avec la raison, médias inutilisés tolérés ; tests indépendants des fiches réelles.
