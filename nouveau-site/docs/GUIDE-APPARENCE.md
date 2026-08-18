# Mode d’emploi de l’apparence du site

Ce document s’adresse à la personne qui modifie le HTML et le CSS du site. Pour écrire
les contenus — livres, personnes, actualités, textes des pages — voir plutôt le
[Guide de rédaction](GUIDE-REDACTION.md) : ces contenus ne se touchent pas ici.

## Le principe

Le site est *fabriqué*. Il n’existe pas de fichier `catalogue.html` que l’on modifierait
directement : une commande lit les contenus, les verse dans des modèles, et écrit les
169 pages finales dans `dist/`.

**Ne jamais modifier `dist/` : ce dossier est effacé et refait à chaque génération.**

Deux dossiers à connaître, et deux seulement :

- `tools/rendu/` — le **HTML**, un fichier par page et par composant ;
- `frontend/assets/css/` — le **CSS**, découpé de la même façon.

Les fichiers de `tools/rendu/` sont des fichiers Python, mais le HTML y est écrit tel
quel, d’un seul bloc, et se reconnaît au premier coup d’œil :

```python
        return f"""
<article class="book-card">
  <a class="book-card__cover-link" href="/livres/{e(book['slug'])}/">
    ...
  <h3><a href="/livres/{e(book['slug'])}/">{e(book['titre'])}</a></h3>
</article>"""
```

## Quel fichier ouvrir

### Les morceaux communs à plusieurs pages

| Ce que je veux changer | Fichier |
|---|---|
| Le bandeau du haut : logo, nom, menu, loupe, menu mobile | `tools/rendu/composants/en_tete.py` |
| Le bas de page : logo, présentation, liens, contact, retour en haut | `tools/rendu/composants/pied_de_page.py` |
| La carte d’un livre (catalogue, accueil, collections) | `tools/rendu/composants/carte_livre.py` |
| Les tuiles de collections avec leurs couvertures en éventail | `tools/rendu/composants/vitrine_collections.py` |
| Le fil d’Ariane « Accueil / Catalogue / … » | `tools/rendu/composants/fil_ariane.py` |
| La galerie d’images et sa fenêtre d’agrandissement | `tools/rendu/composants/galerie.py` |
| Les cartes des livres à paraître | `tools/rendu/composants/cartes_projets.py` |
| Les icônes au trait : flèches, loupe, enveloppe, cœur, croix | `tools/rendu/icones.py` |
| Le `<head>` : titre de l’onglet, favicon, appel du CSS | `frontend/templates/base.html` |

### Les pages

| Page du site | Fichier |
|---|---|
| L’accueil | `tools/rendu/pages/accueil.py` |
| `/catalogue/` | `tools/rendu/pages/catalogue.py` |
| Une page de livre, `/livres/…/` | `tools/rendu/pages/livres.py` |
| `/personnes/` et la fiche d’une personne | `tools/rendu/pages/personnes.py` |
| `/collections/` et la page d’une collection | `tools/rendu/pages/collections.py` |
| `/actualites/` | `tools/rendu/pages/actualites.py` |
| `/la-maison/` | `tools/rendu/pages/maison.py` |
| Les pages de texte : `/commandes/`, `/soutien/`, `/manuscrits/`, `/amis/`, `/projets/`, `/offres-speciales/`, `/atelier-ecriture/`, `/librairies-partenaires/`, `/mentions-legales/` | `tools/rendu/pages/editoriales.py` |
| `/plan-du-site/` | `tools/rendu/pages/plan_du_site.py` |
| La page « introuvable » | `tools/rendu/pages/erreur_404.py` |

### Le style : `frontend/assets/css/`

Le CSS est découpé de la même façon que le HTML. Tous les fichiers sont dans
`frontend/assets/css/` ; la génération les recolle en un seul `site.css`, donc le
visiteur ne télécharge toujours qu’une seule feuille.

**Les fondations** — ce qui touche tout le site :

| Ce que je veux changer | Fichier |
|---|---|
| Couleurs, polices, espacements généraux | `00-variables.css` |
| Comportement des images, liens, champs, contour de mise au point | `01-base.css` |
| Titres et paragraphes | `02-typographie.css` |
| Largeur du contenu et marges latérales | `03-mise-en-page.css` |

**Les morceaux communs** :

| Ce que je veux changer | Fichier |
|---|---|
| Le bandeau du haut et la navigation | `10-en-tete.css` |
| Les boutons ronds et les icônes | `11-icones.css` |
| Le bouton et le menu des petits écrans | `12-menu-mobile.css` |
| Les boutons d’action | `13-boutons.css` |
| Les rubriques en capitales et les chapeaux | `14-textes-mis-en-avant.css` |
| Le bloc de titre des pages intérieures | `15-titre-de-page.css` |
| Le fil d’Ariane | `16-fil-ariane.css` |
| Les bandeaux clairs, blancs et sombres | `21-sections.css` |
| Le titre d’un bandeau | `23-titre-de-section.css` |
| Les tuiles de collections | `25-vitrine-collections.css` |
| Les cartes de livre et de personne | `30-cartes-livre-personne.css` |
| Les filtres et la ligne de résultats | `31-filtres-et-resultats.css` |
| La galerie et sa fenêtre d’agrandissement | `33-galerie.css` |
| Les cartes des livres à paraître | `37-projets.css` |
| Le bas de page | `40-pied-de-page.css` |

**Les pages** :

| Page | Fichier |
|---|---|
| Accueil : la bannière et le ruban de couvertures | `20-accueil-banniere.css` |
| Accueil : le bandeau commercial | `22-accueil-commercial.css` |
| Accueil : le bandeau sombre « Nous suivre » | `41-accueil-suivre.css` |
| La maison : les cartes colorées | `24-cartes-maison.css` |
| La page d’un livre | `32-page-livre.css` |
| La fiche d’une personne | `34-page-personne.css` |
| Les pages de texte et le plan du site | `35-pages-de-texte.css` |
| Les actualités | `36-actualites.css` et `38-encart-actualites.css` |
| Le bandeau de prévisualisation | `39-avertissement-brouillon.css` |
| La page « introuvable » | `42-page-404.css` |

**L’affichage sur petit écran** — ⚠️ ces réglages **ne sont pas** dans le fichier du
composant, mais regroupés par taille d’écran :

| Ce que je veux changer | Fichier |
|---|---|
| Tablettes et petits portables (moins de 1020 px) | `90-tablette-1020px.css` |
| Téléphones en largeur (moins de 760 px) | `91-mobile-760px.css` |
| Téléphones debout (moins de 430 px) | `92-mobile-430px.css` |
| Suppression des animations pour qui l’a demandé | `93-animations-reduites.css` |

**Le numéro en tête du nom donne l’ordre d’application.** En CSS, quand deux règles se
disputent le même élément, c’est la dernière écrite qui gagne — donc celle du fichier
au plus grand numéro. C’est pourquoi les réglages d’écran portent des numéros élevés :
ils doivent pouvoir corriger tout ce qui précède. **Ne pas renommer un fichier** sans
mesurer que cela déplace ses règles dans cet ordre.

### Le comportement

| Ce que je veux changer | Fichier |
|---|---|
| Ouverture du menu, galerie, bouton de retour en haut | `frontend/assets/js/site.js` |
| Filtres et tri du catalogue | `frontend/assets/js/catalogue.js` |
| Filtres de l’annuaire des personnes | `frontend/assets/js/people.js` |

Chaque fichier, HTML comme CSS, commence par un commentaire qui dit ce qu’il dessine
et **nomme son vis-à-vis** : le fichier CSS depuis le HTML, le fichier HTML depuis le
CSS. C’est le plus court chemin entre les deux.

### Les fichiers à laisser tranquilles

Ceux-ci ne contiennent aucun HTML et n’ont aucun effet sur l’apparence :
`constructeur.py`, `sortie.py`, `medias.py`, `technique.py`, `gabarit.py`, `outils.py`,
`libelles.py`, `texte.py`, et tout `tools/content_data.py`.

## La règle des accolades

C’est la seule chose à retenir avant de modifier un fichier de `tools/rendu/`.
**Elle ne concerne pas les fichiers CSS** : ceux-ci sont du CSS pur, sans une ligne de
Python, et s’écrivent tout à fait normalement.

Dans ces fichiers, **ce qui est entre accolades `{ }` est une valeur remplacée au
moment de la fabrication** : le titre du livre, son prix, l’adresse de sa page. Ce
n’est pas du texte, c’est une instruction.

```html
  <h3><a href="/livres/{e(book['slug'])}/">{e(book['titre'])}</a></h3>
                       └──── à ne pas toucher ────┘  └──────┘
```

- ✅ **Libre** : ajouter, supprimer, déplacer des balises ; changer un nom de classe ;
  réordonner les lignes ; modifier le texte écrit en clair.
- ⛔ **À ne pas toucher** : le contenu des accolades, ni les accolades elles-mêmes.
- ⛔ **À ne pas écrire** : une accolade seule dans le HTML. Pour obtenir une `{` à
  l’écran, il faut la doubler : `{{`.
- ⚠️ **Les guillemets** : le bloc de HTML est encadré par trois guillemets doubles,
  `f"""` ou `"""` au début, `"""` à la fin. Ne jamais en écrire trois d’affilée à
  l’intérieur du bloc. Les guillemets isolés, simples ou doubles, ne posent en
  revanche aucun problème : `<a href="/catalogue/">` s’écrit tel quel.

## Travailler sur le site

Ouvrir un terminal dans `nouveau-site/`, puis :

```bash
make dev
```

Ouvrir <http://127.0.0.1:8766/>. À chaque enregistrement d’un fichier — CSS, HTML ou
`tools/rendu/` — le site est refait et la page se recharge toute seule.

⏱️ **Compter une minute et demie à deux minutes par régénération.** Le site refait
l’intégralité des 447 images à chaque fois. C’est long : enregistrer plusieurs
modifications d’un coup plutôt qu’une par une, et attendre le message
`[dev] Site régénéré.` avant de juger le résultat à l’écran.

Avant de proposer les modifications :

```bash
make validate
```

Cette commande refait le site puis lance 73 vérifications automatiques : nombre de
pages, présence de l’en-tête et du pied de page partout, liens qui aboutissent,
images optimisées, boutons de paiement, redirections, référencement.

## En cas d’erreur de frappe

Rien n’est cassé et le site en ligne n’est pas touché.

`make dev` affiche `[dev] Échec de la génération. La dernière version valide reste
servie.` — le navigateur continue d’afficher la version précédente. Le message
au-dessus indique le fichier et le numéro de ligne à corriger. Corriger, enregistrer,
et la génération repart.

Si le message parle d’une `SyntaxError` avec `unterminated string literal` ou
`unexpected EOF`, c’est presque toujours un guillemet ou une accolade en trop ou en
moins dans le bloc que l’on vient de modifier.
