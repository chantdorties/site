# Mode d’emploi de l’apparence du site

Ce document s’adresse à la personne qui modifie le HTML et le CSS du site. Pour écrire
les contenus — livres, personnes, actualités, textes des pages — voir plutôt le
[Guide de rédaction](GUIDE-REDACTION.md) : ces contenus ne se touchent pas ici.

## Le principe

Le site est *fabriqué*. Il n’existe pas de fichier `catalogue.html` que l’on modifierait
directement : une commande lit les contenus, les verse dans des modèles, et écrit les
169 pages finales dans `dist/`.

**Ne jamais modifier `dist/` : ce dossier est effacé et refait à chaque génération.**

Les modèles, eux, sont dans `tools/rendu/`. Ce sont des fichiers Python, mais le HTML y
est écrit tel quel, d’un seul bloc, et se reconnaît au premier coup d’œil :

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

### L’habillage

| Ce que je veux changer | Fichier |
|---|---|
| Couleurs, polices, tailles, marges, mise en page, affichage sur téléphone | `frontend/assets/css/site.css` |
| Ouverture du menu, galerie, bouton de retour en haut | `frontend/assets/js/site.js` |
| Filtres et tri du catalogue | `frontend/assets/js/catalogue.js` |
| Filtres de l’annuaire des personnes | `frontend/assets/js/people.js` |

Chaque fichier de `composants/` et de `pages/` commence par un commentaire qui dit ce
qu’il dessine **et quelles règles CSS l’habillent**. C’est le plus court chemin entre
un fichier et l’autre.

### Les fichiers à laisser tranquilles

Ceux-ci ne contiennent aucun HTML et n’ont aucun effet sur l’apparence :
`constructeur.py`, `sortie.py`, `medias.py`, `technique.py`, `gabarit.py`, `outils.py`,
`libelles.py`, `texte.py`, et tout `tools/content_data.py`.

## La règle des accolades

C’est la seule chose à retenir avant de modifier un fichier de `tools/rendu/`.

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
