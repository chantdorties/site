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

Le script `tools/deploy-free.py` utilise le FTP passif. Il exclut `/admin/`, envoie
les médias avant les pages, remplace chaque fichier par renommage et conserve un
manifeste distant. Seuls les anciens fichiers enregistrés dans ce manifeste peuvent
être supprimés.

## Restauration

Dans l’onglet Actions, lancer `Restore a previous version`, saisir le commit, tag ou
nom de branche à restaurer, puis approuver l’environnement `production`. La version
choisie est reconstruite et testée avant tout transfert.

Les artefacts GitHub et l’historique Git permettent également de télécharger ou de
revenir à chaque version publiée.
