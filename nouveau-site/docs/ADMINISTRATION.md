# Administration des contenus

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
- les livres, personnes, collections et actualités ;
- les trois pages principales et les pages de la maison ;
- l’ordre des collections, livres, personnes et pages ;
- les livres mis en avant sur l’accueil et les suggestions « À découvrir aussi » ;
- les textes alternatifs, les titres SEO, les descriptions SEO et les images sociales ;
- les anciennes adresses à rediriger et le bouton PayPal général de don.

De nouvelles pages de la maison peuvent être créées. La suppression reste
désactivée : utiliser le statut `Archivé` pour retirer un contenu sans perdre son
historique. Un contenu archivé disparaît du site mais **conserve ses anciennes
adresses**, qui renvoient alors vers sa rubrique parente plutôt que vers une page
inexistante. Les pages Accueil, Actualités et Mentions légales doivent toujours
rester publiées : leur adresse et leur statut ne sont pas modifiables.

Une adresse (`slug`) ne doit plus être changée après la première publication. Si
un changement est indispensable, ajouter l’adresse précédente dans « Anciennes
adresses » afin que le générateur crée la redirection.

## Règles vérifiées avant publication

La génération refuse un contenu qui casserait le site, avec un message explicite :

- deux contenus classés au même rang (`ordre`) — pour les livres, le rang est
  propre à chaque collection, il peut donc resservir d’une collection à l’autre ;
- deux livres mis en avant partageant le même rang d’accueil ;
- un titre SEO de plus de 60 caractères ou une description SEO de plus de 160 ;
- une relation vers un contenu inexistant, en brouillon ou archivé ;
- plus de quatre suggestions « À découvrir aussi » ;
- un identifiant de bouton PayPal mal formé, ou absent sur un livre disponible ;
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

L’hébergement Free ne propose pas HTTPS pour ce site. L’administration doit donc
être servie séparément en HTTPS afin de ne pas exposer le jeton GitHub.

1. Dans Netlify, créer un projet depuis le dépôt privé `chantdorties/site`.
2. Choisir le nom de site `chantdorties-admin`. Le fichier `netlify.toml` publie
   uniquement les sources statiques nécessaires ; aucun build Netlify n’est requis.
3. Dans GitHub, créer une OAuth App avec :
   - Homepage URL : `https://chantdorties-admin.netlify.app`
   - Authorization callback URL : `https://api.netlify.com/auth/done`
4. Dans Netlify, ouvrir `Project configuration > Access & security > OAuth`, puis
   installer le fournisseur GitHub avec le Client ID et le Client Secret de l’app.
5. Ouvrir <https://chantdorties-admin.netlify.app/admin/> et se connecter avec un
   compte GitHub collaborateur du dépôt.

Si Netlify attribue un autre nom, remplacer `chantdorties-admin.netlify.app` dans
`frontend/admin/config.yml`, puis pousser la modification.

## Contrôles appliqués

La publication est refusée si un slug, une relation, un ordre, un ISBN, un prix,
une date ou un média est invalide. Chaque collection publiée doit avoir exactement
un livre disponible mis en avant sur l’accueil. Les médias doivent peser au plus
20 Mo. Une actualité avec image doit posséder un texte alternatif. Les PDF sont
contrôlés avant publication.

Les identifiants FTP ne sont jamais accessibles depuis l’administration ou le site.
