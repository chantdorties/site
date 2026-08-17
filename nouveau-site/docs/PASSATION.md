# Passation : qui possède quoi

Ce document existe pour une seule raison : permettre à quelqu’un d’autre de reprendre le
site sans rien deviner. Il recense les comptes dont dépend la publication, ce qui casse
si l’un d’eux disparaît, et comment s’en remettre.

## Inventaire

| Élément | Compte propriétaire | Rôle |
|---|---|---|
| Dépôt `chantdorties/site` | compte GitHub **chantdorties** | contenus, code, secrets, automatisations |
| Hébergement du site | pages perso **Free** du client | le site public |
| Administration (Decap) | hébergement OVH du prestataire, sous-domaine `orties-admin` | interface de saisie |
| Relais d’authentification | deux fichiers PHP sur ce même sous-domaine, adossés à l’OAuth App GitHub du compte **chantdorties** | connexion à l’administration |
| Aperçu client | hébergement OVH du prestataire | temporaire, disparaît à la mise en ligne |

Le compte GitHub `chantdorties` est destiné au client : il est propriétaire du dépôt, et
c’est lui qui signe les modifications faites depuis l’administration. Le prestataire y est
collaborateur en écriture, ce qui suffit à intervenir sans détenir le compte.

## Ce qui casse si un maillon disparaît

| Si… | Alors | Gravité |
|---|---|---|
| le compte GitHub `chantdorties` est perdu | plus de dépôt, plus de contenus versionnés | **critique** |
| l’hébergement OVH du prestataire est perdu | plus d’administration ; le site en ligne continue de fonctionner | sérieux, réparable |
| l’OAuth App GitHub est supprimée | plus de connexion à l’administration | réparable en 10 minutes |
| le fichier de secrets du relais est perdu | plus de connexion à l’administration | réparable, voir `RELAIS-AUTH.md` |
| l’hébergement Free ferme | le site n’est plus servi | le dépôt suffit à republier ailleurs |

Aucun de ces incidents ne fait perdre les contenus : ils vivent dans Git, avec leur
historique complet.

## Point de fragilité connu

**L’administration et son relais dépendent de l’hébergement OVH du prestataire.** C’est
un choix assumé tant qu’il reste en charge du site. Le client doit le savoir : sans cet
hébergement, l’interface de saisie s’arrête — le site public, lui, continue de fonctionner
et reste modifiable en éditant les fichiers JSON du dépôt.

La réparation ne dépend de personne, et prend une dizaine de minutes. Elle est détaillée
dans [RELAIS-AUTH.md](RELAIS-AUTH.md), section « Reconstruire ailleurs » ; en résumé :

1. Déposer sur n’importe quel hébergement servant du PHP — **sauf les pages perso de
   Free, qui bloquent toute sortie réseau** — le contenu de `frontend/admin/` et les deux
   fichiers du relais, `frontend/admin-serveur/`. Le workflow `.github/workflows/admin.yml`
   décrit exactement ce qu’il faut assembler.
2. Recréer hors du dossier publié le fichier de secrets `orties-admin-secret.php`, avec le
   Client ID, le Client Secret et la nouvelle origine.
3. Sur `github.com/settings/developers`, compte `chantdorties`, ajouter l’URL de rappel du
   nouveau relais. Une application existante se transfère d’un compte à l’autre par
   `Transfer ownership`, sans que le Client ID ni le Client Secret ne changent.
4. **Reporter la nouvelle adresse dans `frontend/admin/config.yml`**, clé
   `backend.base_url`. Sans cela l’authentification échoue silencieusement.

## Le relais d’authentification, et pourquoi il est à nous

Le service `api.netlify.com/auth`, dont dépendait l’administration jusqu’ici, est un
vestige que Netlify retire progressivement — la page permettant d’en installer un a déjà
disparu de certaines interfaces. Il a donc été remplacé par un relais maison, décrit dans
[RELAIS-AUTH.md](RELAIS-AUTH.md).

Son rôle tient en trois gestes : rediriger vers `github.com/login/oauth/authorize`,
recevoir le code d’autorisation, l’échanger contre un jeton et le renvoyer à Decap par
`postMessage`. Une soixantaine de lignes. Il détient le Client Secret, d’où la nécessité
d’un serveur.

Les hébergements ont été mesurés avant de choisir, inutile de refaire l’essai :

| Hébergement | PHP | Sorties réseau | Verdict |
|---|---|---|---|
| Free, pages perso du client | 5.6.34 | **bloquées** (refus immédiat) | impossible |
| OVH mutualisé du prestataire | 8.2.31 | libres, GitHub joignable | viable |
| Fonction Netlify, site d’admin | — | libres | viable, et sur le même domaine |

Free est hors jeu : ses pages perso ne peuvent joindre aucun serveur extérieur, ce qui
interdit l’échange du jeton, quelle que soit la version de PHP.

C’est donc le **script PHP sur l’hébergement OVH du prestataire** qui a été retenu, avec
l’administration servie sur le même sous-domaine : maîtrise complète, aucun éditeur ne
peut le déprécier, et la politique de sécurité se resserre puisque tout vient d’une seule
origine. La contrepartie est écrite plus haut — le client en dépend durablement, et la
reconstruction ailleurs ne demande qu’un hébergement PHP.

La bascule a tenu en trois changements, à refaire à l’identique le jour d’un déménagement :
`backend.base_url` et `backend.auth_endpoint` dans `frontend/admin/config.yml`, l’URL de
rappel ajoutée à l’OAuth App, et le Client Secret déposé côté serveur.

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
