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
masqué. Un contenu `brouillon` n’apparaît jamais sur le site public.

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

La publication est refusée si un slug, une relation, un ISBN, un prix, une date ou
un média est invalide. Les médias doivent peser au plus 20 Mo. Une actualité avec
image doit posséder un texte alternatif. Les PDF sont contrôlés avant publication.

Les identifiants FTP ne sont jamais accessibles depuis l’administration ou le site.
