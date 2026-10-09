# Administration des contenus

Ce document décrit le fonctionnement, les règles et l’hébergement de l’administration.
Pour la personne qui saisit les contenus, le mode d’emploi est
[GUIDE-REDACTION.md](GUIDE-REDACTION.md).

## Fonctionnement

L’interface Decap CMS modifie les fichiers JSON et les médias du dépôt privé
`chantdorties/site`. Le client ne manipule ni HTML, ni CSS, ni JSON.

Le mode éditorial suit ce parcours :

1. « Enregistrer » crée un brouillon dans une branche Git et une pull request.
2. La validation GitHub construit et teste le site sans toucher à la production.
3. « Publier » fusionne le contenu dans `main`.
4. GitHub Actions reconstruit le site et déclenche le déploiement Free.

Le champ `statut` permet en plus de conserver sur `main` un contenu volontairement
masqué. Un contenu `brouillon` n’apparaît pas sur le site public. Un contenu
`archive` n’apparaît ni sur le site public ni dans la prévisualisation.

## Contenus modifiables

L’administration permet de modifier :

- l’identité, le contact, le menu, le pied de page et les principaux textes du site.
  Chaque entrée des Réglages a un aperçu (maquette de la zone concernée,
  `frontend/admin/preview.js`). Les liens du menu et du pied de page s’affichent dans
  l’ordre de leur liste, réglé par glisser-déposer ; l’identifiant d’un lien du menu
  est caché et, pour un nouveau lien, déduit de son adresse (`navigation_id`) ;
- l’apparence : neuf couleurs et deux polices, dans « Réglages du site > Apparence »
  (contrat : [CONTRAT-APPARENCE.md](CONTRAT-APPARENCE.md)). L’entrée a sa propre
  miniature d’aperçu, qui suit la couleur et la police en cours ; les autres aperçus
  gardent le thème par défaut ;
- les livres, personnes, collections, actualités et projets ;
- la page d’accueil et les autres pages engendrées, une fiche chacune dans « Pages du
  site », et les pages écrites à la main dans « Mes pages » ;
- l’ordre des collections, livres, personnes et pages ;
- les livres mis en avant sur l’accueil (cochés dans chaque fiche ; « Pages principales > Accueil » fixe
  combien de couvertures s’affichent) et les suggestions « À découvrir aussi » ;
- l’emblème de chaque collection — le petit dessin repris de l’ancien site, qui
  s’affiche sur la page de la collection et sur les vignettes de l’accueil ;
- les textes alternatifs, les titres SEO, les descriptions SEO et les images sociales ;
- les anciennes adresses à rediriger, l’identifiant PayPal du don et les mots du
  parcours d’achat — « Ajouter au panier », « Voir mon panier », « Actuellement
  indisponible », « Nous contacter », « Lire l’extrait », réunis dans « Réglages du
  site > Paiement et dons ». Les boutons « Faire un don » et « Voir les offres »,
  affichés sur l’accueil seulement, se libellent dans « Pages principales > Accueil » ;
- les boutons d’achat propres à une page — offre groupée, adhésion, don, titre soldé —
  saisis section par section dans la page concernée. Un livre vendu à son prix normal
  garde le sien dans sa fiche. Le bouton « voir mon panier », lui, est posé
  automatiquement dans le menu de chaque page : seul son libellé se règle.

Chaque partie du site se règle à un seul endroit. L’accueil se règle entièrement
dans « Pages principales > Accueil » (`content/pages-du-site/accueil.json`), son
référencement et ses anciennes adresses compris. Les pages engendrées — catalogue,
auteurs, collections, actualités, maison et projets — ont chacune leur fiche dans
« Pages principales » (`content/pages-du-site/<page>.json`) ; pour les actualités et les
projets, référencement et anciennes adresses y sont aussi. `load_settings` les
présente au générateur sous `settings["accueil"]` et `settings["pages"][<page>]`, et
refuse les anciens `content/reglages/accueil.json` et `pages.json`. La page
Projets est rebâtie depuis sa fiche par `projects_page` (`tools/content_data.py`) :
pour le reste du site, c’est une page de la maison ordinaire. Le dossier
`content/pages-fixes/` n’existe plus, et sa réapparition est refusée par la
validation. Les catégories annoncées en bas de la page Actualités ne s’écrivent pas :
ce sont celles des articles réellement publiés.

De nouvelles pages de la maison peuvent être créées avec un titre et un texte seulement.
Decap tire le nom du fichier du titre (`slug: "{{slug}}"`) ; le chargeur en fait l’adresse
de la page quand le champ `slug` manque (`load_folder(..., slug_from_filename=True)`), et
range après les autres une page sans `ordre`. Sections et liens sont des listes à types
(`type` : `texte`, `livres`, `offre` ; `externe`, `email`, `document`, `livre`, `page`) ;
la validation refuse une section sans type. Un PDF se dépose dans son lien
« Document PDF » : `documents` n’est plus proposé, mais encore lu s’il existe.

La suppression est désactivée partout sauf dans la rubrique **Projets** : un projet
n’a pas d’adresse à lui, donc rien à rediriger, et un livre paru n’a plus à encombrer
la liste — le dépôt en garde de toute façon l’historique. Ailleurs, le statut
`Archivé` retire un contenu du site sans l’effacer. Un contenu archivé **conserve ses
anciennes adresses**, qui renvoient alors vers sa rubrique parente plutôt que vers une
page inexistante.

Les mentions légales, rangées parmi les pages de la maison, doivent toujours rester
publiées à l’adresse `/mentions-legales/` : la validation refuse tout autre statut et
tout changement d’adresse.

Une adresse (`slug`) ne doit plus être changée après la première publication. Si
un changement est indispensable, ajouter l’adresse précédente dans « Anciennes
adresses » afin que le générateur crée la redirection.

## Les projets

La rubrique **Projets** tient les livres à paraître. Ils n’ont pas de page à eux :
ils s’affichent sur la page Projets, sous son introduction, du plus petit rang au
plus grand. L’introduction, elle, s’écrit dans « Pages principales > Projets ».

Un auteur ou un illustrateur qui possède déjà une fiche se choisit dans « Auteurs »
ou « Illustrateurs », et son nom devient un lien vers elle. Celui qui n’en a pas
encore — c’est fréquent pour un livre à paraître — s’écrit à la main dans le champ
« sans fiche » voisin, et son nom s’affiche sans lien. Le jour où sa fiche existe,
il suffit de déplacer le nom d’un champ à l’autre.

Le jour de la parution, le projet se supprime et le livre prend sa place au
catalogue.

## Règles vérifiées avant publication

La génération refuse un contenu qui casserait le site, avec un message explicite :

- deux contenus classés au même rang (`ordre`) — pour les livres, le rang est
  propre à chaque collection, il peut donc resservir d’une collection à l’autre ;
- deux livres mis en avant partageant le même rang d’accueil ;
- un titre SEO de plus de 60 caractères ou une description SEO de plus de 160 ;
- une relation vers un contenu inexistant, en brouillon ou archivé ;
- plus de quatre suggestions « À découvrir aussi » ;
- un identifiant de bouton PayPal mal formé, ou absent sur un livre disponible, que le
  bouton soit celui d’une fiche ou celui d’une section de page ;
- le bloc signé du bouton « voir mon panier » modifié ou effacé ;
- une adresse (`slug`) invalide, ou une ancienne adresse déclarée deux fois ;
- un réglage Apparence hors contrat : couleur autre que `#RRGGBB`, police absente de
  la liste, clé manquante ou inconnue. Le message commence par « Réglage apparence: »
  et nomme le champ.

Les champs laissés vides dans l’administration ne bloquent jamais la génération :
ils reçoivent automatiquement une valeur vide.

Dans « Pages principales », le jeton `{nombre}` est remplacé
au moment de la génération par le nombre réel de contenus. Écrire
« {nombre} ouvrages » plutôt que « 64 ouvrages » évite un compte faux après chaque
ajout.

## Accès local

Installer les dépendances Python, puis lancer :

```bash
make admin
```

Ouvrir <http://127.0.0.1:8766/admin/>. Le proxy Decap local écrit directement dans
`content/`. Le workflow éditorial n’est pas utilisé dans ce mode.

## Accès en ligne sécurisé

L’administration est servie en HTTPS, afin de ne pas exposer le jeton GitHub :
<https://chantdorties.pages-perso.free.fr/admin/>, chez Free, avec le site. Elle est
publiée avec lui par `.github/workflows/site.yml`. L’ancienne adresse
`http://chantdorties.free.fr/admin/` y renvoie d’office.

La connexion passe par un relais d’authentification maison, deux fichiers PHP chez OVH
(`https://orties-admin.varascundo.com/`) : PHP chez Free ne peut joindre aucun serveur
extérieur, donc pas GitHub. Le relais échange le code d’autorisation GitHub contre un
jeton ; l’OAuth App du compte `chantdorties` porte pour cela l’URL de rappel
`https://orties-admin.varascundo.com/callback.php`, et le Client Secret reste sur le
serveur, hors du dossier publié. `.github/workflows/admin.yml` publie le relais, et lui
seul, quand `frontend/admin-serveur/` change. Tout est décrit dans
[RELAIS-AUTH.md](RELAIS-AUTH.md) : dépôt du secret, vérifications, reconstruction
ailleurs.

Pour s’en servir : ouvrir l’adresse ci-dessus et se connecter avec un compte
GitHub collaborateur du dépôt.

Le site Netlify `chantdorties-admin` existe toujours et sert de repli. Il ne
fonctionne qu’avec l’ancien relais `api.netlify.com/auth` : y revenir suppose
d’annuler la bascule dans `frontend/admin/config.yml`, comme l’explique
RELAIS-AUTH.md.

## Contrôles appliqués

La publication est refusée si un slug, une relation, un ordre, un ISBN, un prix,
une date ou un média est invalide. Chaque collection publiée doit avoir exactement
un livre disponible mis en avant sur l’accueil. Les médias doivent peser au plus
20 Mo. Une actualité avec image, comme une collection avec emblème, doit posséder
un texte alternatif. Les PDF sont
contrôlés avant publication.

Les identifiants FTP ne sont jamais accessibles depuis l’administration ou le site.

## Modifier le formulaire sans changer le site

Les champs qui reviennent d’une rubrique à l’autre sont écrits une seule fois dans
`frontend/admin/config.yml`, à leur première apparition, puis repris par une ancre
YAML : le motif des adresses (`&motif_adresse`), l’identifiant PayPal
(`&motif_paypal`), le plafond de 20 Mo (`&media_20_mo`), les galeries
(`&image_et_alt`), le libellé et l’adresse d’un lien, la publication, l’ordre, les
anciennes adresses et le référencement. Un test vérifie qu’aucun n’est recopié. Les
barres d’outils suivent une règle écrite au même endroit : un texte court prend
`*boutons_courts`, un texte long découpé en parties `*boutons_corps`.

Les aperçus (`preview.js`) recopient le HTML du site pour en reprendre la feuille de
style ; un test vérifie que chacune de leurs classes existe encore dans les pages
produites. Côté générateur, le titre des pages intérieures et le formulaire PayPal
n’existent qu’en un exemplaire (`render_page_heading`, `render_paypal_form`).

Pour ranger le formulaire ou le générateur sans toucher au site, comparer deux
générations :

```sh
cp -a dist /tmp/dist-avant
# … modifications, puis nouvelle génération …
python3 tools/compare-dist.py /tmp/dist-avant dist
```

Le script n’ignore que les retours à la ligne entre deux balises ; toute autre
différence est listée.
