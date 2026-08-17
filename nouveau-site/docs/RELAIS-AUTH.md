# Le relais d’authentification de l’administration

## À quoi il sert

Decap édite le dépôt GitHub au nom de la personne connectée. Pour obtenir un jeton
d’écriture, il faut échanger un code d’autorisation contre ce jeton en présentant le
Client Secret de l’application GitHub — une opération qu’un navigateur ne peut pas faire
sans exposer le secret. D’où ce relais : deux pages PHP, sur l’hébergement OVH.

Il remplace `api.netlify.com/auth`, un service que Netlify retire progressivement — la
page permettant de l’installer a déjà disparu de plusieurs interfaces.

## Où vivent les pièces

| Fichier | Rôle |
|---|---|
| `frontend/admin/` | l’interface, script Decap embarqué compris |
| `frontend/admin-serveur/auth.php` | redirige vers GitHub avec un jeton anti-rejeu |
| `frontend/admin-serveur/callback.php` | échange le code contre un jeton, le remet à Decap |
| `frontend/admin-serveur/htaccess.conf` | déposé sous le nom `.htaccess`, en-têtes de sécurité |
| `~/orties-admin-secret.php` **sur le serveur** | Client ID et Client Secret, hors du dossier publié, jamais versionné |

En ligne : `https://orties-admin.varascundo.com/`, servi par le dossier `orties-admin`
du compte OVH. Le déploiement est assuré par `.github/workflows/admin.yml`, déclenché
seulement quand `frontend/admin/` ou `frontend/admin-serveur/` changent.

## Déposer ou renouveler le Client Secret

Un secret se renouvelle sans rien casser d’autre : il ne concerne que le relais.

1. Sur `github.com/settings/developers`, connecté avec le compte **chantdorties**,
   ouvrir l’application, puis **Generate a new client secret**. Ne pas supprimer
   l’ancien tant que le nouveau n’a pas été éprouvé.
2. Le déposer sur le serveur, au choix.

   **À la main**, directement :

   ```bash
   ssh ovh
   nano orties-admin-secret.php     # remplacer la valeur de client_secret
   ```

   **Sans que le secret transite par une conversation ou un journal** — méthode à
   privilégier si quelqu’un d’autre opère à votre place :

   ```bash
   # 1. écrire le secret seul, sur une ligne, dans un fichier local
   #    ~/secret-github.txt  (avec son propre éditeur)

   # 2. l’injecter sans jamais l’afficher
   S=$(cat ~/secret-github.txt) && \
     ssh ovh "sed -i 's|client_secret\" => \"[^\"]*|client_secret\" => \"$S|' orties-admin-secret.php"

   # 3. vérifier sans révéler : la valeur d’origine a disparu, la longueur est plausible
   ssh ovh 'grep -c REMPLACER orties-admin-secret.php; \
            php -r "\$r = require \"orties-admin-secret.php\"; " 2>/dev/null; \
            awk -F\" "/client_secret/ {print length(\$4) \" caracteres\"}" orties-admin-secret.php'

   # 4. effacer le fichier local
   shred -u ~/secret-github.txt
   ```

3. Vérifier que le fichier reste inaccessible depuis le web :

   ```bash
   curl -sI https://orties-admin.varascundo.com/orties-admin-secret.php   # 404 attendu
   ```

Le fichier doit rester en permissions `600` et **hors** du dossier `orties-admin`.

## Basculer l’administration sur ce relais

Deux valeurs, et rien d’autre.

Dans `frontend/admin/config.yml` :

```yaml
backend:
  base_url: https://orties-admin.varascundo.com
  auth_endpoint: auth.php
  # site_domain disparaît : il ne servait qu’au relais Netlify
```

Et sur l’OAuth App GitHub, **ajouter** l’URL de rappel
`https://orties-admin.varascundo.com/callback.php`. L’application en accepte plusieurs :
conserver celle de Netlify tant que la bascule n’est pas éprouvée.

**Retour en arrière** : remettre `base_url` à `https://api.netlify.com`, `auth_endpoint`
à `auth` et `site_domain` à `chantdorties-admin.netlify.app`. Tant que le site Netlify
existe, l’ancien chemin fonctionne toujours.

## Vérifier

```bash
curl -sI https://orties-admin.varascundo.com/            # 200, en-têtes de sécurité
curl -sI https://orties-admin.varascundo.com/auth.php    # 302 vers github.com, client_id et state présents
curl -sI https://orties-admin.varascundo.com/magicieuse/ # 404 : rien d’autre du compte n’est servi
```

Puis, dans un navigateur : se connecter, créer une actualité, vérifier qu’une pull
request apparaît sur le dépôt.

## Pièges rencontrés, à ne pas refaire

**Le sous-domaine doit viser `orties-admin`, jamais la racine du compte.** Lors de la
création, il pointait sur le répertoire personnel : tous les projets et les fichiers
cachés du compte devenaient navigables. Vérifier après toute modification du multisite :

```bash
curl -s https://orties-admin.varascundo.com/ | grep -c "Index of"   # doit valoir 0
```

**Ne jamais écrire `Options -ExecCGI`** dans le `.htaccess` de ce dossier : PHP cesserait
de s’exécuter et `auth.php` renverrait son propre code source, secret compris s’il y
figurait — raison de plus pour le garder hors du dossier publié.

**`DirectoryIndex index.html` est nécessaire** : sans cette ligne, OVH renvoie 403 à la
racine du sous-domaine puisque le listing est désactivé.

**Un `.htaccess` à la racine du compte est hérité** par les sites dont la racine est un
sous-dossier. Une règle globale y coupe l’aperçu du site en même temps que le reste ; la
restreindre par `<If "%{HTTP_HOST} == '…'">`.

**L’origine du `postMessage` doit être nommée**, jamais `'*'`. Avec `'*'`, n’importe
quelle page ouvrant le relais repart avec un jeton autorisant l’écriture dans le dépôt.

## Reconstruire ailleurs

Le relais ne dépend que de PHP et de cURL. Tout hébergement exécutant du PHP et
autorisant les connexions sortantes convient — **sauf les pages perso de Free, qui
bloquent toute sortie réseau** : mesuré, refus immédiat en 0 ms. Il suffit alors de
déposer les deux fichiers, d’adapter `origine` dans le fichier de secrets, l’URL de
rappel côté GitHub, et `base_url` dans `config.yml`.
