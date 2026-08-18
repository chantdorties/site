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

- l’identité, le contact, le menu, le pied de page et les principaux textes du site ;
- les livres, personnes, collections, actualités et projets ;
- les trois pages principales et les pages de la maison ;
- l’ordre des collections, livres, personnes et pages ;
- les livres mis en avant sur l’accueil et les suggestions « À découvrir aussi » ;
- l’emblème de chaque collection — le petit dessin repris de l’ancien site, qui
  s’affiche sur la page de la collection et sur les vignettes de l’accueil ;
- les textes alternatifs, les titres SEO, les descriptions SEO et les images sociales ;
- les anciennes adresses à rediriger, le bouton PayPal général de don et les mots du
  parcours d’achat — « Ajouter au panier », « Voir mon panier », « Actuellement
  indisponible », « Nous contacter », « Voir les offres », « Lire l’extrait », réunis
  dans « Réglages du site > Paiement et dons » ;
- les boutons d’achat propres à une page — offre groupée, adhésion, don, titre soldé —
  saisis section par section dans la page concernée. Un livre vendu à son prix normal
  garde le sien dans sa fiche.

Les pages engendrées se règlent ailleurs que là où elles s’affichent. Le titre,
l’introduction et l’encart Facebook de la page **Actualités** viennent de « Réglages
du site > Introductions des pages > Actualités » — l’entrée « Actualités » des Pages
principales ne porte que son référencement. Il en va de même du catalogue, des
auteurs, des collections et de la maison. Les catégories annoncées en bas de la page
Actualités ne s’écrivent pas : ce sont celles des articles réellement publiés.

De nouvelles pages de la maison peuvent être créées.

La suppression est désactivée partout sauf dans la rubrique **Projets** : un projet
n’a pas d’adresse à lui, donc rien à rediriger, et un livre paru n’a plus à encombrer
la liste — le dépôt en garde de toute façon l’historique. Ailleurs, le statut
`Archivé` retire un contenu du site sans l’effacer. Un contenu archivé **conserve ses
anciennes adresses**, qui renvoient alors vers sa rubrique parente plutôt que vers une
page inexistante.

Les pages Accueil, Actualités et Mentions légales doivent toujours rester publiées :
leur adresse et leur statut ne sont pas modifiables.

Une adresse (`slug`) ne doit plus être changée après la première publication. Si
un changement est indispensable, ajouter l’adresse précédente dans « Anciennes
adresses » afin que le générateur crée la redirection.

## Les projets

La rubrique **Projets** tient les livres à paraître. Ils n’ont pas de page à eux :
ils s’affichent sur la page Projets, sous son introduction, du plus petit rang au
plus grand. L’introduction, elle, s’écrit dans « Pages de la maison > Projets ».

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
- une adresse (`slug`) invalide, ou une ancienne adresse déclarée deux fois.

Les champs laissés vides dans l’administration ne bloquent jamais la génération :
ils reçoivent automatiquement une valeur vide.

Dans les rubriques « Introductions des pages », le jeton `{nombre}` est remplacé
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

L’hébergement Free ne propose pas HTTPS pour ce site. L’administration est donc
servie séparément en HTTPS, afin de ne pas exposer le jeton GitHub.

Elle vit sur <https://orties-admin.varascundo.com/>, sur l’hébergement OVH du
prestataire. Le workflow `.github/workflows/admin.yml` l’y publie à chaque
modification de `frontend/admin/` ou `frontend/admin-serveur/` — un contenu
enregistré par un rédacteur ne déclenche donc rien ici.

La connexion passe par un relais d’authentification maison, deux fichiers PHP
servis sur ce même domaine, qui échangent le code d’autorisation GitHub contre un
jeton. L’OAuth App du compte `chantdorties` porte pour cela l’URL de rappel
`https://orties-admin.varascundo.com/callback.php`, et le Client Secret reste sur
le serveur, hors du dossier publié. Tout est décrit dans
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
