# Mode d’emploi de l’administration

Ce document s’adresse à la personne qui écrit les contenus. Il ne demande aucune
connaissance technique. Pour le fonctionnement interne — dépôt, génération, déploiement —
voir [ADMINISTRATION.md](ADMINISTRATION.md).

## Comment se lit un formulaire

Chaque fiche se lit de haut en bas, découpée par de grands intertitres :

- **L’essentiel** ouvre toujours le formulaire : le titre, la publication, le texte et
  l’image principale. C’est souvent tout ce qu’il y a à remplir.
- Viennent ensuite les blocs propres à la rubrique — **Vente**, **Caractéristiques du
  livre**, **Images, liens et documents**…
- **Réglages techniques** ferme le formulaire : l’adresse de la page, son rang dans les
  listes, les anciennes adresses et le référencement. On n’y touche qu’en cas de besoin.

Le volet de droite montre la page **telle qu’elle apparaîtra sur le site**, avec sa mise
en page, ses couvertures et ses prix, et change pendant la frappe. Les noms, couvertures
et prix des autres fiches y sont ceux de la dernière publication : un livre créé depuis
apparaît sous son adresse jusqu’à la publication suivante.

## Se connecter

Ouvrir <https://chantdorties.pages-perso.free.fr/admin/>, puis **Se connecter avec GitHub**. Une
fenêtre s’ouvre, demande l’autorisation une première fois, puis se referme seule.

Il faut un compte GitHub ayant accès au dépôt. Si la fenêtre reste sur « Connexion en
cours… », c’est un problème technique et non une erreur de saisie : le signaler.

## Rien n’est publié sans votre second geste

Enregistrer ne met rien en ligne. Chaque modification passe par un tableau, le **flux
éditorial**, avec trois colonnes : *Brouillons*, *En cours de révision*, *Prêt*. Une fiche
enregistrée arrive dans la première ; on la fait glisser jusqu’à *Prêt*, et c’est le
bouton **Publier** qui la met en ligne.

Entre les deux, le site est reconstruit et vérifié à blanc. Si une règle est enfreinte,
la publication est refusée avec un message : rien n’est cassé, il suffit de corriger.

⚠️ **Deux mots « brouillon » cohabitent, et ils ne veulent pas dire la même chose.**

| Où | Ce que ça veut dire |
|---|---|
| Les colonnes du flux éditorial | Où en est votre modification dans le circuit de validation |
| Le champ **Publication** dans la fiche | Si le contenu doit apparaître sur le site une fois publié |

Une fiche peut donc être publiée (elle rejoint le site) tout en portant le statut
*Brouillon* (elle n’y sera pas visible). C’est utile pour préparer un livre à l’avance.

Le champ **Publication** offre trois choix :

- **Publié** — visible sur le site ;
- **Brouillon** — préparé, invisible du public, visible dans l’aperçu ;
- **Archivé** — retiré du site sans être effacé, et ses anciennes adresses continuent de
  fonctionner en renvoyant vers la rubrique parente.

## Où se règle quel texte

C’est la question qui revient le plus souvent. La règle : **chaque partie du site se
règle à un seul endroit**. Les pages qui rassemblent des contenus (catalogue, auteurs,
collections, actualités, projets) sont fabriquées automatiquement : leur texte
d’en-tête ne se modifie pas sur la page elle-même, mais dans les Réglages du site.

| Ce que vous voulez changer | Où aller |
|---|---|
| Un livre, une personne, une collection, un projet | La rubrique du même nom |
| Un article d’actualité | Rubrique **Actualités** |
| **Tout** ce qu’affiche la page d’accueil : grand titre, boutons, bloc d’information, textes des libraires et des particuliers, boutons de don et d’offres, présentation des collections, bandeau « Suivre la maison » | **Réglages du site › Page d’accueil**, de haut en bas dans l’ordre de la page |
| Le titre et l’introduction du catalogue, des auteurs, des collections, des actualités, de la maison et des projets | **Réglages du site › Introductions des pages** |
| Le référencement et les anciennes adresses de l’accueil, des actualités ou des projets | Le même écran, dans ses réglages techniques |
| Le menu, le pied de page, l’adresse courriel, la page Facebook | **Réglages du site** |
| Les mots du parcours d’achat (« Ajouter au panier », « Nous contacter »…) | **Réglages du site › Paiement et dons** |
| Les couleurs et les polices du site | **Réglages du site › Apparence** |
| Les pages Commandes, Librairies, Soutien, Amis… et les mentions légales | **Pages de la maison** |

La maison a deux textes de présentation, qui ne servent pas au même endroit :
**Identité et contact › Description pour les moteurs de recherche** n’est lu que par
Google et les réseaux sociaux ; **Pied de page › Présentation de la maison** s’affiche
en bas de chaque page.

Les mentions légales se modifient comme les autres pages de la maison, mais elles sont
obligatoires : elles ne peuvent être ni dépubliées ni changer d’adresse.

Chaque entrée des **Réglages du site** montre à droite un aperçu : une maquette de la
zone du site où ses textes apparaissent (en-tête, pied de page, accueil, en-têtes des
pages, boutons d’achat). Il suit la saisie, avant tout enregistrement.

### Le menu et les liens du pied de page

Dans **Réglages du site › Menu principal** et **› Pied de page**, chaque lien tient sur
une ligne, « Libellé — adresse ». L’ordre affiché sur le site est celui de la liste :
pour déplacer un lien, le saisir par sa poignée (≡) et le glisser à sa place. Décocher
« Visible » retire un lien du menu sans l’effacer. Un nouveau lien ne demande qu’un
libellé et une adresse.

Deux textes ne se saisissent nulle part, parce qu’ils se déduisent : les catégories
annoncées en bas de la page Actualités sont celles des articles réellement publiés, et le
jeton `{nombre}` écrit dans une introduction est remplacé par le compte réel — écrire
« {nombre} ouvrages » évite un chiffre faux au prochain ajout.

## Modifier l’apparence

Les couleurs et les polices de tout le site se règlent à un seul endroit :

1. Ouvrir **Réglages du site › Apparence**.
2. Modifier une couleur : cliquer sur la pastille et choisir la teinte, ou taper son
   code (`#` suivi de six chiffres ou lettres, par exemple `#c63f32`). Choisir une
   police dans sa liste.
3. Vérifier la miniature **Aperçu du thème**, à droite : elle change pendant la saisie.
4. Enregistrer, puis publier comme pour tout autre contenu. Le site se reconstruit
   avec le nouveau thème.

| Champ | Ce qu’il colore | Valeur d’origine |
|---|---|---|
| Fond du site | Le fond des pages et de l’en-tête | `#f7f7f4` |
| Fond des cartes | Les cartes, les bandeaux blancs, les champs de recherche | `#ffffff` |
| Texte principal | Le texte courant et les titres | `#171a18` |
| Texte secondaire | Les textes discrets : fil d’Ariane, légendes, dates | `#626862` |
| Couleur principale | « d’orties », l’onglet actif du menu, les filets, la 1re collection | `#c63f32` |
| Couleur principale foncée | Le survol des liens et des boutons | `#963128` |
| Couleur secondaire | Les surtitres, les citations, « Disponible », la 2e collection | `#3e6b50` |
| Liens | Les liens dans les textes, la 3e collection | `#275c7a` |
| Boutons | Le fond des boutons pleins ; leur texte reste blanc | `#171a18` |
| Police des titres | Les titres et le nom de la maison | Classique à empattements (Georgia) |
| Police des textes | Le texte courant, les menus, les boutons | Moderne sans empattements (Inter) |

Pour revenir à l’apparence d’origine, recopier les valeurs du tableau dans les champs.

Ce qui ne se change pas ici : la mise en page, les tailles de texte, les espacements
et l’affichage sur téléphone. Le pied de page sombre, les teintes propres à chaque
collection et l’avertissement des brouillons restent aussi fixes, pour que le texte
reste lisible. Une couleur mal saisie (pas au format `#` + six caractères) est refusée
à l’enregistrement. Penser à la lisibilité : un texte clair sur un fond clair reste
possible, l’administration ne le bloque pas.

Les emblèmes des collections ne sont pas dans Apparence : ils se changent dans chaque
fiche de la rubrique **Collections**.

## Ajouter une actualité

1. Rubrique **Actualités**, bouton **＋ Actualité** en haut de la liste.
2. Titre, puis **Identifiant** : le titre en minuscules avec des tirets, sans accent
   (`rencontre-a-lyon`). Il ne sert qu’au classement, l’article n’a pas de page à lui.
3. **Date** : elle décide de la place dans la liste, la plus récente en premier.
4. **Catégorie** : salon, parution, rencontre ou vie de la maison.
5. **Résumé** en une ou deux phrases, puis **Contenu**. Laisser une ligne vide entre deux
   paragraphes.
6. Une image est facultative — mais si vous en mettez une, **son texte alternatif devient
   obligatoire**, sinon la publication est refusée.

## Ajouter un livre

Le formulaire est long parce qu’un livre a beaucoup de facettes. Il suit l’ordre dans
lequel on décrit un ouvrage ; seuls le titre, l’adresse, la collection, au moins un auteur
et la couverture sont indispensables.

**Ce qui mérite attention :**

- **Adresse de la page** — elle devient l’adresse publique du livre. À ne plus changer
  après la première publication : si c’est indispensable, reporter l’ancienne dans
  « Anciennes adresses », tout en bas, pour que le lien continue de fonctionner.
- **Auteurs** — on choisit dans les fiches existantes. Une personne absente de la liste
  doit d’abord être créée dans *Auteurs et illustrateurs*, avec le rôle correspondant :
  les champs Auteurs, Illustrateurs et Préfaciers ne proposent que les personnes portant
  ce rôle.
- **Disponible** — décoché, le livre affiche « Actuellement indisponible » et un bouton de
  contact au lieu du bouton d’achat.
- **Identifiant du bouton PayPal** — obligatoire dès que le livre est disponible. Sans
  lui, la publication est refusée.
- **Mis en avant sur l’accueil** — chaque collection en met exactement un en avant. En
  cocher un second dans la même collection bloque la publication : décocher l’ancien
  d’abord.
- **Ordre d’affichage** — du plus petit au plus grand, à l’intérieur de la collection.
  Deux livres d’une même collection ne peuvent pas partager le même rang.

## Ajouter, modifier ou retirer un projet

La rubrique **Projets** tient les livres à paraître. Ils s’affichent sur la page Projets,
sous son introduction.

Pour les intervenants, deux champs cohabitent volontairement : **Auteurs** pour ceux qui
ont déjà une fiche — leur nom devient un lien — et **Auteurs sans fiche** pour les autres,
dont le nom s’affiche simplement. C’est le cas courant avant une parution. Le jour où la
fiche existe, déplacer le nom d’un champ à l’autre.

C’est la seule rubrique où la **suppression** est possible : un projet n’a pas d’adresse
propre, donc rien à rediriger. Le jour de la parution, supprimer le projet et créer le
livre.

## Créer une page

1. **Pages de la maison › + Page**.
2. Écrire le **titre**, puis le **texte** dans la section déjà ouverte.
3. **Publier › Publier maintenant**.

C’est tout. L’adresse de la page vient du titre (« Atelier dessin » devient
`/atelier-dessin/`) et ne change plus ensuite, même si le titre est modifié. La page
prend place à la fin de « La maison » et entre dans le plan du site. Pour l’ajouter au
menu du haut : **Réglages du site › Menu principal**.

Tout le reste du formulaire est facultatif :

- **Une autre section** : le bouton « Ajouter une entrée de type section » propose trois
  sortes de section — un **texte**, un **texte et des livres du catalogue** (montrés en
  cartes sous le texte), ou une **offre à vendre** avec ses boutons PayPal (voir
  ci-dessous). Chacune ne montre que ses propres champs.
- **Des liens** : le bouton « Ajouter une entrée de type lien » propose un site web, une
  adresse courriel, un document PDF, un livre ou une autre page du site. Un PDF se dépose
  directement dans son lien.
- **Des images** : une galerie au bas de la page.
- **La carte sur « La maison »** : sa petite ligne et le texte de son lien.
- **L’ordre** : pour placer la carte ailleurs qu’à la fin, donner un nombre plus petit
  que celui des pages qui doivent la suivre.

## Vendre depuis une page

Un livre se vend depuis sa fiche : c’est là que se saisit son bouton PayPal, et nulle part
ailleurs. Mais certaines ventes n’appartiennent à aucun livre — une offre groupée à deux
tomes, une adhésion, un don, un titre soldé. Pour celles-là, ajouter à la page une section
de sorte **« Offre à vendre (bouton PayPal) »** : elle porte ses propres **boutons d’achat
PayPal**.

Un bouton demande deux choses : le texte que lira le visiteur, et l’**identifiant à
13 caractères** fourni par PayPal au moment où le bouton y a été créé — par exemple
`6A3X7AW598RVA`, et non l’adresse complète. C’est cet identifiant, et lui seul, qui décide
de l’article et du montant facturés.

Deux précautions valent d’être répétées :

- **Ne jamais recopier l’identifiant de la fiche d’un livre** dans une page qui annonce un
  prix réduit. La page afficherait la remise, et PayPal ferait payer le plein tarif. Un
  prix soldé ou groupé exige son propre bouton, créé pour lui dans PayPal.
- **Vérifier le bouton après publication** en cliquant dessus : PayPal affiche l’article et
  le montant réels. C’est la seule vérification qui compte.

**Montrer les livres d’une offre.** Une section « Offre à vendre » ou « Texte et livres
du catalogue » a un champ **Livres à montrer** : on y choisit les livres dans une liste. Ils s’affichent sous le texte avec leur
couverture, leurs auteurs et leur prix, tirés de leur fiche — rien à recopier, rien à
mettre à jour deux fois. C’est ainsi qu’est faite la page Offres spéciales : une section
par offre, ses deux livres, son bouton.

Le bouton « voir mon panier » n’est à saisir nulle part : il se tient en permanence
dans le menu du site, et se répète sur la fiche d’un livre à côté de « Ajouter au
panier », là où l’on veut vérifier sa commande. Seul son libellé se règle, dans
« Réglages du site > Paiement et dons ».

## Créer une personne

Une fiche par auteur, illustrateur ou préfacier. Le **rôle** coché décide des champs de
livre où la personne sera proposée : sans le rôle Illustrateur, elle n’apparaîtra pas dans
la liste des illustrateurs. Une personne peut cumuler les trois.

Une fiche publiée apparaît sur la page Auteurs & illustrateurs même sans livre associé —
elle y affiche alors « 0 livre ». Mieux vaut donc la garder en *Brouillon* tant que son
premier ouvrage n’est pas publié.

## Mettre en forme un texte

Les zones de texte ne sont plus de simples cadres gris : une petite barre d’outils
apparaît au-dessus quand on clique dedans. Elle sert à **mettre en gras**, en *italique*,
à poser un lien, à faire une liste à puces ou numérotée, un intertitre, une citation.

Rien n’oblige à s’en servir. Un texte tapé au fil de la plume s’affiche exactement comme
avant.

**Ce qu’il faut savoir :**

- **Une ligne vide sépare deux paragraphes.** C’était déjà la règle pour le corps d’une
  actualité ; elle vaut maintenant partout, y compris dans les sections des pages de la
  maison, où les lignes vides étaient jusqu’ici ignorées à l’affichage.
- **Passer à la ligne sans changer de paragraphe** — **Maj + Entrée**. Utile pour une
  adresse postale, une ligne par information :
  « Publico ⏎ 145 rue Amelot ⏎ 75011 Paris ».
- **Les liens** — sélectionner les mots, puis le bouton lien. Une adresse écrite en
  entier (`https://…`) ou un courriel deviennent cliquables tout seuls, sans rien faire.
- **Les intertitres** s’insèrent sous le titre de la page : ils ne peuvent pas le
  concurrencer, le site s’en assure.
- **Les images au fil du texte** — le bouton image du corps d’un article ou d’une section
  de page. Seule dans son paragraphe, l’image s’affiche en grand avec sa légende ; au
  milieu d’une phrase, elle reste petite. **Le texte alternatif y est obligatoire**, sans
  exception : sans lui la publication est refusée.
- **Les descriptions de référencement** n’ont pas de barre d’outils, et c’est voulu :
  elles ne servent qu’aux moteurs de recherche, qui n’affichent ni gras ni lien. Un
  compteur sous le champ indique où l’on en est des 160 caractères.
- **Voir le résultat** — le volet de droite montre le texte mis en forme pendant la
  frappe. Le bouton « Voir sur le site » ouvre la vraie page.

## Les images

- 20 Mo maximum par fichier ; le site les convertit et les allège tout seul.
- Le **texte alternatif** décrit l’image pour les personnes qui ne la voient pas, et pour
  les moteurs de recherche. Il est obligatoire sur une actualité illustrée et sur
  l’emblème d’une collection ; ailleurs, le laisser vide produit une formulation
  automatique (« Couverture de… », « Portrait de… »).
- L’**emblème** d’une collection est le petit dessin de l’ancien site — coquelicot, ortie,
  églantine, arbre, herbes folles, chardon. Il s’affiche en tête de la collection et sur
  les vignettes de l’accueil.

## Quand la publication est refusée

Le message dit ce qui coince et sur quelle fiche. Les cas les plus fréquents :

| Message | Ce qu’il faut faire |
|---|---|
| *ordre … utilisé deux fois* | Deux contenus se disputent le même rang : en changer un |
| *bouton PayPal obligatoire si disponible* | Renseigner l’identifiant, ou décocher « Disponible » |
| *identifiant du bouton PayPal « … » invalide* | Coller les 13 caractères fournis par PayPal, sans l’adresse autour |
| *le bouton « voir mon panier » attend le bloc signé par PayPal* | Le bloc technique des réglages de paiement a été modifié : y remettre celui d’origine |
| *texte alternatif … obligatoire* | Décrire l’image ajoutée |
| *sélectionner exactement un livre disponible pour l’accueil* | Une collection a zéro ou deux livres mis en avant |
| *personne en brouillon* / *livre lié non publié* | Un contenu publié pointe vers un contenu qui ne l’est pas : publier l’autre, ou retirer le lien |
| *titre SEO trop long* | 60 caractères pour le titre, 160 pour la description |
| *texte alternatif obligatoire pour l’image* | Une image posée au fil d’un texte n’a pas été décrite |
| *média introuvable* | Une image citée dans un texte a été retirée de la médiathèque |
| *lien introuvable* | Un lien interne écrit à la main mène à une page qui n’existe pas |

Rien n’est perdu : la modification reste dans le flux éditorial jusqu’à ce qu’elle passe.

## Ce que l’administration ne permet pas

- **Supprimer** un livre, une personne, une collection, une page ou une actualité :
  utiliser le statut *Archivé*. Seuls les projets s’effacent vraiment.
- **Changer l’adresse** d’un contenu déjà publié sans reporter l’ancienne : les liens
  existants et les moteurs de recherche pointeraient dans le vide.
- **Dépublier** les pages Accueil, Actualités et Mentions légales : elles sont
  structurelles.
- **Changer la mise en page** ou les tailles ; l’ordre du menu se règle par
  glisser-déposer, couleurs et polices se limitent aux choix de
  **Réglages du site › Apparence**.
