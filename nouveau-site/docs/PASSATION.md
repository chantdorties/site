# Passation : qui possède quoi

Ce document existe pour une seule raison : permettre à quelqu’un d’autre de reprendre le
site sans rien deviner. Il recense les comptes dont dépend la publication, ce qui casse
si l’un d’eux disparaît, et comment s’en remettre.

## Inventaire

| Élément | Compte propriétaire | Rôle |
|---|---|---|
| Dépôt `chantdorties/site` | compte GitHub **chantdorties** | contenus, code, secrets, automatisations |
| Hébergement du site | pages perso **Free** du client | le site public |
| Administration (Decap) | site Netlify **chantdorties-admin**, compte personnel du prestataire | interface de saisie |
| Relais d’authentification | OAuth App GitHub du compte **chantdorties**, relayée par `api.netlify.com/auth` | connexion à l’administration |
| Aperçu client | hébergement OVH du prestataire | temporaire, disparaît à la mise en ligne |

Le compte GitHub `chantdorties` est destiné au client : il est propriétaire du dépôt, et
c’est lui qui signe les modifications faites depuis l’administration. Le prestataire y est
collaborateur en écriture, ce qui suffit à intervenir sans détenir le compte.

## Ce qui casse si un maillon disparaît

| Si… | Alors | Gravité |
|---|---|---|
| le compte GitHub `chantdorties` est perdu | plus de dépôt, plus de contenus versionnés | **critique** |
| le compte Netlify du prestataire est perdu | plus d’administration ; le site en ligne continue de fonctionner | sérieux, réparable |
| l’OAuth App GitHub est supprimée | plus de connexion à l’administration | réparable en 10 minutes |
| `api.netlify.com/auth` ferme | plus de connexion à l’administration | à surveiller, voir plus bas |
| l’hébergement Free ferme | le site n’est plus servi | le dépôt suffit à republier ailleurs |

Aucun de ces incidents ne fait perdre les contenus : ils vivent dans Git, avec leur
historique complet.

## Point de fragilité connu

**L’administration dépend du compte Netlify personnel du prestataire.** C’est un choix
assumé tant qu’il reste en charge du site. Le client doit le savoir : sans ce compte,
l’interface de saisie s’arrête — le site public, lui, continue de fonctionner et reste
modifiable en éditant les fichiers JSON du dépôt.

La réparation ne dépend de personne, et prend une dizaine de minutes :

1. Créer un compte Netlify, `Add new site > Import an existing project`, choisir le dépôt
   `chantdorties/site`. Les réglages viennent du `netlify.toml` : base `nouveau-site`,
   publication `frontend`, branche `main`.
2. Créer une OAuth App sur `github.com/settings/developers`, depuis le compte
   `chantdorties` : URL de rappel `https://api.netlify.com/auth/done`, sans expiration
   des jetons. Une application existante se transfère d’un compte à l’autre par
   `Transfer ownership`, sans que le Client ID ni le Client Secret ne changent — rien
   n’est alors à reporter dans Netlify.
3. Dans Netlify, `Project configuration > Access & security > OAuth > Install provider`,
   y coller le Client ID et le Client Secret.
4. **Reporter le nouveau domaine Netlify dans `frontend/admin/config.yml`**, clé
   `backend.site_domain`. Sans cela l’authentification échoue silencieusement.

Le service `api.netlify.com/auth` est un vestige que Netlify retire progressivement — la
section OAuth a déjà disparu de certaines interfaces. S’il ferme, il faudra le remplacer
par un relais d’authentification autonome (une petite fonction serveur). Le reste de la
chaîne n’en dépend pas.

## À faire pour achever la passation

1. **Transmettre les identifiants du compte GitHub `chantdorties`** au client, par un
   canal sûr, puis y activer l’authentification à deux facteurs et une adresse de
   récupération à son nom.
2. **Changer le mot de passe FTP Free**, puis mettre à jour le secret `FREE_FTP_PASSWORD`
   du dépôt.
3. **Décider de la publication** : la variable `FREE_DEPLOY_ENABLED` reste absente tant
   que le nouveau site ne doit pas écraser l’ancien. La créer à `true` déclenche la
   publication réelle au prochain contenu validé.

## Ce qui ne dépend d’aucun compte

Le site publié est du HTML statique : ni base de données, ni langage serveur, ni
dépendance à un service tiers. L’administration elle-même embarque son code, elle ne
charge rien depuis un CDN. Un `git clone` du dépôt, `make build`, et le dossier `dist/`
est prêt à être déposé sur n’importe quel hébergement — c’est le filet de sécurité
ultime, et il ne demande qu’un accès au dépôt.
