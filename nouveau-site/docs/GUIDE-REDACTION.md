# Mode d’emploi de l’administration

Ce document s’adresse à la personne qui écrit les contenus. Il ne demande aucune
connaissance technique. Pour le fonctionnement interne — dépôt, génération, déploiement —
voir [ADMINISTRATION.md](ADMINISTRATION.md).

## Se connecter

Ouvrir <https://orties-admin.varascundo.com/>, puis **Se connecter avec GitHub**. Une
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

C’est la question qui revient le plus souvent. Les pages qui rassemblent des contenus
sont fabriquées automatiquement : leur texte d’en-tête ne se modifie pas sur la page
elle-même.

| Ce que vous voulez changer | Où aller |
|---|---|
| Un livre, une personne, une collection, un projet | La rubrique du même nom |
| Un article d’actualité | Rubrique **Actualités** |
| Le titre et l’introduction de la page Actualités, du catalogue, des auteurs, des collections, de la maison | **Réglages du site › Introductions des pages** |
| Les textes de la page d’accueil (grand titre, accroche, boutons, intertitres) | **Réglages du site › Textes de l’accueil** |
| Le texte des blocs de l’accueil (situation de la maison, soutien, commandes) | **Pages principales › Accueil** |
| Le menu, le pied de page, l’adresse courriel, la page Facebook | **Réglages du site** |
| Les mots du parcours d’achat (« Ajouter au panier », « Nous contacter »…) | **Réglages du site › Paiement et dons** |
| L’introduction de la page Projets | **Pages de la maison › Projets** |
| Les pages Commandes, Librairies, Soutien, Amis… | **Pages de la maison** |
| Les mentions légales | **Pages principales › Mentions légales** |

Deux textes ne se saisissent nulle part, parce qu’ils se déduisent : les catégories
annoncées en bas de la page Actualités sont celles des articles réellement publiés, et le
jeton `{nombre}` écrit dans une introduction est remplacé par le compte réel — écrire
« {nombre} ouvrages » évite un chiffre faux au prochain ajout.

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

## Vendre depuis une page

Un livre se vend depuis sa fiche : c’est là que se saisit son bouton PayPal, et nulle part
ailleurs. Mais certaines ventes n’appartiennent à aucun livre — une offre groupée à deux
tomes, une adhésion, un don, un titre soldé. Pour celles-là, chaque **section** d’une page
de la maison peut porter ses propres **boutons d’achat PayPal**.

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

Le bouton « voir mon panier » s’ajoute tout seul à côté : rien à saisir.

## Créer une personne

Une fiche par auteur, illustrateur ou préfacier. Le **rôle** coché décide des champs de
livre où la personne sera proposée : sans le rôle Illustrateur, elle n’apparaîtra pas dans
la liste des illustrateurs. Une personne peut cumuler les trois.

Une fiche publiée apparaît sur la page Auteurs & illustrateurs même sans livre associé —
elle y affiche alors « 0 livre ». Mieux vaut donc la garder en *Brouillon* tant que son
premier ouvrage n’est pas publié.

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

Rien n’est perdu : la modification reste dans le flux éditorial jusqu’à ce qu’elle passe.

## Ce que l’administration ne permet pas

- **Supprimer** un livre, une personne, une collection, une page ou une actualité :
  utiliser le statut *Archivé*. Seuls les projets s’effacent vraiment.
- **Changer l’adresse** d’un contenu déjà publié sans reporter l’ancienne : les liens
  existants et les moteurs de recherche pointeraient dans le vide.
- **Dépublier** les pages Accueil, Actualités et Mentions légales : elles sont
  structurelles.
- **Changer la mise en page**, les couleurs, les polices ou l’ordre des rubriques du menu
  au-delà de ce que proposent les Réglages.
