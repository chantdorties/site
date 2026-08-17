# Déploiement et restauration

## Validation automatique

À chaque pull request et à chaque envoi sur `main`, le workflow
`.github/workflows/site.yml` :

1. installe Python, Ghostscript et Poppler ;
2. valide les contenus et génère `dist/` ;
3. lance tous les tests ;
4. conserve le site généré comme artefact GitHub pendant 30 jours.

Un échec arrête la publication et laisse la version en ligne intacte.

## Déploiement Free

Free limite les connexions FTP selon leur provenance géographique. La tâche de
publication utilise donc un runner GitHub auto-hébergé, placé sur une machine en
France et portant les labels `self-hosted`, `linux` et `free-deploy`.

Dans `Settings > Secrets and variables > Actions`, configurer :

- variable `FREE_DEPLOY_ENABLED` : `true` ;
- secret `FREE_FTP_USER` : identifiant des pages personnelles ;
- secret `FREE_FTP_PASSWORD` : mot de passe FTP ;
- secret optionnel `FREE_FTP_HOST` : `ftpperso.free.fr` par défaut ;
- secret optionnel `FREE_FTP_PATH` : `/` par défaut.

Créer aussi l’environnement GitHub `production`. Une approbation obligatoire peut
y être activée avant chaque transfert.

Le runner doit disposer de Git, Python 3 et d’une connexion autorisée par Free. Son
installation se fait depuis `Settings > Actions > Runners > New self-hosted runner` ;
GitHub fournit les commandes et le jeton temporaire propres au dépôt. Ajouter le
label personnalisé `free-deploy`, puis installer le runner comme service.

Le script `tools/deploy-ftp.py --target free` utilise le FTP passif. Il exclut `/admin/`,
envoie les médias avant les pages, remplace chaque fichier par renommage et conserve un
manifeste distant. Seuls les anciens fichiers enregistrés dans ce manifeste peuvent
être supprimés.

## Le fichier `.htaccess`

Free lit bien le `.htaccess`, mais n’accepte qu’une partie des directives Apache.
`mod_rewrite` en particulier est absent : ne jamais ajouter de `RewriteEngine` ni de
`RewriteRule`. Sont acceptés `Options`, `ErrorDocument`, `Redirect` et `RedirectMatch`,
`AddType`, `Order/Allow/Deny`, un seul bloc `<Files>` par fichier.

Le fichier est produit à chaque génération par `tools/build-site.py` : il désactive le
listing des répertoires, déclare la page 404 du site, fixe les types MIME du WebP, du
JSON, du PDF et du JavaScript, puis liste les redirections 301 des anciennes adresses.
Il est indispensable : les anciennes pages `.html` restent présentes sur le serveur
(elles ne figurent pas dans le manifeste), et ce sont ces redirections qui les
remplacent.

Après le premier transfert, vérifier en ligne :

```bash
curl -sI http://chantdorties.free.fr/monhlm.html    # 301 vers /livres/mon-hlm/
curl -s http://chantdorties.free.fr/page-absente    # la page 404 du site, pas celle de Free
```

Si la page 404 affichée reste celle de Free, remplacer le chemin relatif par l’adresse
complète : `ErrorDocument 404 http://chantdorties.free.fr/404.html`.

## Aperçu client (OVH)

Avant la mise en ligne chez le client, le site est montré sur
<https://orties.varascundo.com/>, hébergement OVH personnel. Le site Free n’est jamais
touché par cette publication.

### Préparation, une seule fois

1. Dans l’espace client OVH, en multisite, faire pointer le sous-domaine
   `orties.varascundo.com` vers un dossier dédié, avec le certificat Let’s Encrypt :
   l’adresse d’aperçu doit être en `https`. La racine retenue est `orties/dist`.
2. Créer le fichier des comptes autorisés **un cran au-dessus** du dossier publié, dans
   `orties/` : il n’est ainsi jamais servi aux visiteurs. Il n’est pas versionné, et le
   script de déploiement ne le supprimera jamais, puisqu’il n’efface que les fichiers
   inscrits dans son propre manifeste.

   ```bash
   htpasswd -cbB ~/orties/.htpasswd apercu '<mot de passe>'
   chmod 644 ~/orties/.htpasswd
   ```

3. Relever le chemin absolu **tel qu’Apache le voit**, et non celui qu’affiche le shell.
   Sur le mutualisé OVH, le compte est accessible sous deux noms : `/home/<login>/…`,
   que renvoie `pwd`, et `/homez.<numéro>/<login>/…`, que renvoie `echo $HOME`. **Seul le
   second fonctionne dans `AuthUserFile`** ; avec le premier, l’authentification échoue
   par une erreur 500 une fois le mot de passe saisi. Déposer ce fichier **avant** le
   premier déploiement : sans lui, Apache renvoie également une erreur 500.
4. Dans `Settings > Environments`, créer l’environnement `Apercu` — le nom doit
   correspondre exactement à celui déclaré dans `apercu.yml` — puis y ajouter ces
   secrets d’environnement. Ainsi seul un job déclarant cet environnement peut les
   lire, et une approbation peut y être exigée :

   - `OVH_FTP_HOST` : l’hôte FTP du cluster, indiqué dans l’espace client ;
   - `OVH_FTP_USER` et `OVH_FTP_PASSWORD` : identifiants FTP OVH, de préférence ceux
     d’un utilisateur secondaire limité au dossier d’aperçu ;
   - `OVH_FTP_PATH` : `/orties/dist`, la racine du sous-domaine ;
   - `OVH_HTPASSWD_PATH` : le chemin en `/homez.…` relevé à l’étape 3.

5. Dans `Settings > Secrets and variables > Actions`, onglet `Variables`, ajouter la
   variable **de dépôt** `APERCU_ENABLED` à `true` : chaque contenu validé sur `main`
   régénère alors l’aperçu. Sans elle, seul le lancement manuel fonctionne. Elle ne peut
   pas être rangée dans l’environnement : la condition du job est évaluée avant que
   l’environnement ne soit chargé.

### Publier

Dans l’onglet Actions, lancer `Publish the client preview`. L’adresse et l’inclusion des
brouillons sont demandées au lancement. Le workflow régénère le site avec
`--base-url https://orties.varascundo.com` — l’artefact de `Validate and publish` porte
le domaine Free, ses adresses canoniques et son plan du site seraient faux —, ajoute
`config/apercu-ovh.htaccess` au `.htaccess` généré, remplace `robots.txt` par un refus
d’indexation, puis envoie le tout par FTPS avec `tools/deploy-ftp.py --target ovh`.

Contrairement à Free, OVH ne filtre pas le FTP selon la provenance : ce workflow tourne
sur un runner GitHub standard.

Le script accepte l’option `--tls` pour chiffrer la connexion, mais le FTP de ce cluster
la refuse (`500 This security scheme is not implemented`) : le transfert se fait donc en
clair, comme chez Free. Pour un aperçu temporaire protégé par mot de passe, c’est
acceptable ; utiliser de préférence un compte FTP secondaire limité à ce dossier plutôt
que le compte principal.

Vérifications après publication :

```bash
curl -sI https://orties.varascundo.com/                     # 401 sans identifiants
curl -sI -u apercu:motdepasse https://orties.varascundo.com/   # 200 + X-Robots-Tag: noindex
curl -s -u apercu:motdepasse https://orties.varascundo.com/robots.txt   # Disallow: /
curl -sI http://chantdorties.free.fr/                       # le site du client n’a pas bougé
```

### Administration pendant l’aperçu

L’administration reste publiée par Netlify sur `chantdorties-admin.netlify.app` : elle
n’est jamais transférée avec le site. Seules les clés `site_url` et `display_url` de
`frontend/admin/config.yml` pointent vers l’aperçu, pour que les liens « voir le site »
n’envoient pas le client sur l’ancien site. Les modifications continuent de passer par le
flux éditorial : rien n’est publié sans validation.

### Retour en arrière, le jour de la mise en ligne

1. Remettre `site_url` et `display_url` sur `http://chantdorties.free.fr` dans
   `frontend/admin/config.yml`.
2. Passer la variable `APERCU_ENABLED` à `false`.
3. Supprimer le dossier d’aperçu chez OVH et son sous-domaine.

## Restauration

Dans l’onglet Actions, lancer `Restore a previous version`, saisir le commit, tag ou
nom de branche à restaurer, puis approuver l’environnement `production`. La version
choisie est reconstruite et testée avant tout transfert.

Les artefacts GitHub et l’historique Git permettent également de télécharger ou de
revenir à chaque version publiée.
