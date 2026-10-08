# Contrat du réglage Apparence

Ce document fixe ce que l’administration a le droit de changer dans l’apparence du
site, et rien d’autre. Il fait foi pour le fichier `content/reglages/apparence.json`,
sa validation (`tools/content_data.py`), sa traduction en CSS
(`tools/rendu/feuille_de_style.py`) et son formulaire dans Decap
(`frontend/admin/config.yml`). Si l’un d’eux change, les autres et ce document
changent avec lui.

## Principe

L’administration choisit des **valeurs** ; le code décide **où** elles s’appliquent.
Chaque clé du fichier correspond à un token CSS déclaré dans
`frontend/assets/css/00-variables.css`. Le fichier ne contient jamais de CSS : ni
propriété, ni règle, ni sélecteur, ni pile de polices.

## Champs

Le fichier est un objet JSON qui contient **exactement** les clés ci-dessous : une clé
manquante ou inconnue arrête la génération.

### Couleurs

Domaine autorisé : une chaîne `#RRGGBB`, six chiffres hexadécimaux, minuscules ou
majuscules (expression `^#[0-9A-Fa-f]{6}$`).

| Clé | Token CSS | Rôle | Valeur par défaut |
| --- | --- | --- | --- |
| `couleurFond` | `--color-background` | Fond général des pages et de l’en-tête | `#f7f7f4` |
| `couleurSurface` | `--color-surface` | Fond des cartes, des bandeaux blancs, des champs | `#ffffff` |
| `couleurTexte` | `--color-text` | Texte courant et titres | `#171a18` |
| `couleurTexteSecondaire` | `--color-muted` | Textes discrets : fil d’Ariane, légendes, dates | `#626862` |
| `couleurPrincipale` | `--color-primary` | Accent de la maison : « d’orties », onglet actif, filets, 1re collection | `#c63f32` |
| `couleurPrincipaleFoncee` | `--color-primary-dark` | Survol des liens et boutons, texte de l’onglet actif | `#963128` |
| `couleurSecondaire` | `--color-secondary` | Surtitres, citations, mention « disponible », 2e collection | `#3e6b50` |
| `couleurLiens` | `--color-link` | Liens dans le texte, champ de saisie actif, 3e collection | `#275c7a` |
| `couleurBoutons` | `--color-button` | Fond et bordure des boutons pleins | `#171a18` |

### Polices

Domaine autorisé : un identifiant de la liste ci-dessous. La pile CSS correspondante
est écrite dans le code, jamais dans le fichier. Aucune police n’est téléchargée :
toutes les piles s’appuient sur des polices installées sur les appareils.

| Clé | Token CSS | Rôle | Valeur par défaut |
| --- | --- | --- | --- |
| `policeTitres` | `--font-heading` | Titres, nom de la maison, chiffres mis en avant | `serif-classique` |
| `policeTexte` | `--font-body` | Texte courant, menus, boutons | `sans-serif-moderne` |

| Identifiant | Libellé dans l’administration | Pile CSS |
| --- | --- | --- |
| `serif-classique` | Classique à empattements (Georgia) | `Georgia, "Times New Roman", serif` |
| `serif-livre` | Livre à empattements (Palatino) | `"Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif` |
| `sans-serif-moderne` | Moderne sans empattements (Inter) | `Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif` |
| `sans-serif-humaniste` | Humaniste sans empattements | `Optima, Candara, "Gill Sans", "Trebuchet MS", ui-sans-serif, sans-serif` |

## Interdits

Le fichier, la validation et l’administration refusent :

- toute couleur hors `#RRGGBB` : nom de couleur, `#rgb` court, transparence (`#RRGGBBAA`),
  fonctions (`rgb()`, `hsl()`, `var()`, `url()`…), chaîne vide, valeur non textuelle ;
- tout caractère `;`, `{`, `}` ou toute valeur ressemblant à du CSS ;
- toute pile de polices, URL de police ou fichier de police saisi par l’administration ;
- toute propriété de mise en page : taille, espacement, largeur, rayon, point de
  rupture, ombre. Ces réglages restent dans `frontend/assets/css/` ;
- tout logo ou média : les emblèmes des collections restent dans chaque fiche Collection.

## Ce qui reste fixe

Certaines couleurs ne sont pas administrables, pour préserver la lisibilité :

- les zones sombres (pied de page, bandeau « Suivre et participer », visionneuse
  d’images) et leur texte clair : `--color-dark`, `--color-on-dark` et leurs nuances ;
- le texte des boutons pleins (`--color-on-dark`, blanc) ;
- les filets (`--color-border`), le fond doux secondaire (`--color-secondary-soft`)
  et le contour de mise au point au clavier (`--color-highlight`) ;
- les teintes propres à chaque collection et l’avertissement des brouillons.

## Décision en attente : identité des rubriques

Des couleurs ou des logos propres à chaque rubrique (accueil, catalogue, personnes,
collections, actualités, maison, pages éditoriales) ne sont **pas** implémentés. Avant
de les ajouter, le client doit valider :

- la liste exacte des rubriques, et si les pages éditoriales partagent une couleur ;
- le sens du mot « logo » : image fournie, icône existante ou simple couleur.

Une fois ces réponses obtenues, l’ajout suit le même contrat : un objet fermé
`couleursRubriques` (une clé par rubrique validée, valeur `#RRGGBB`), des tokens
`--color-section-<rubrique>` produits depuis une table interne, branchés sur les
classes existantes ; jamais de sélecteur venu du JSON. Des logos, s’ils sont
fournis, passeraient par `content/media/` et le pipeline d’optimisation existant.

Les emblèmes des collections ne sont pas concernés : ils restent dans chaque fiche
Collection (`logo`, `logoAlt`).

## Liste figée

À la livraison du 8 octobre 2026 : neuf couleurs (tableau « Couleurs »), deux polices
choisies parmi quatre identifiants (tableau « Polices »), aucune couleur ni logo de
rubrique. Toute extension passe par une mise à jour de ce document.

## Responsabilités

| Étape | Fichier | Rôle |
| --- | --- | --- |
| Données | `content/reglages/apparence.json` | Valeurs choisies |
| Validation | `tools/content_data.py` | Refuse toute valeur hors contrat avant la génération |
| Génération | `tools/rendu/feuille_de_style.py` | Traduit les valeurs en déclarations des tokens connus |
| Administration | `frontend/admin/config.yml` | Ne propose que des valeurs du contrat |
| Aperçu | `frontend/admin/preview.js`, `preview.css` | Miniature Apparence ; mêmes clés, tokens et polices |
