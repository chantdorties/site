---
objective: "Une éditrice non technicienne modifie n’importe quel contenu du site sans hésiter : des textes lisibles, des formulaires courts dans l’ordre où l’on pense, et un aperçu qui ressemble au site."
status: implemented
---

# Plan : Refonte de l’ergonomie de l’administration

## Overview

| Field      | Value |
| ---------- | ----- |
| **Goal**   | Rendre l’administration Decap lisible et rassurante pour une utilisatrice peu habituée aux interfaces complexes, sur toutes les rubriques. |
| **Source** | Retour utilisateur du 8 octobre 2026 : « le format est peu lisible, il faut penser que le client est non dev ». Captures : Offres spéciales, Librairies partenaires. |
| **Persona** | L’éditrice : écrit bien, connaît ses livres, ne connaît ni Markdown, ni « slug », ni « SEO ». Travaille sur un ordinateur portable. |

## Constat

| # | Problème | Exemple | Gravité |
| --- | --- | --- | --- |
| 1 | Textes migrés collés en un seul bloc | Librairies partenaires : adresses, téléphones et liens bout à bout. 49 contenus touchés (39 livres, 6 pages, accueil, mentions légales, 1 personne, paiement) | Bloquant |
| 2 | Aperçu sans rapport avec le site | Offres spéciales : ni boutons PayPal, ni couvertures, ni liens, ni mise en page du site | Fort |
| 3 | Champs techniques au milieu des champs utiles | « Adresse de la page », « Ordre d’affichage », « Anciennes adresses », « Type » | Fort |
| 4 | Libellés et vocabulaire de développeur | Petites étiquettes en majuscules, « 1 sections », « Ajouter sections », « No titre », « SEO », « slug » | Moyen |
| 5 | Identifiants tapés à la main | Lien vers un livre : taper `gaia-conte-de-la-montagne-bleue` | Moyen |
| 6 | Contenu d’une même idée éclaté | Une offre = texte dans Sections + couvertures dans Images + liens dans Liens | Moyen |
| 7 | Barre d’outils trop riche | Barré, code, insertion de bloc de code | Faible |

## Phases

| # | Phase | Contenu | Livrable vérifiable |
| --- | --- | --- | --- |
| 1 | Référence avant/après | Captures de chaque écran d’édition (11 rubriques + 7 réglages), liste de tâches type : ajouter un livre, modifier une offre, publier une actualité, changer une adresse de librairie | `reports/admin-ux/avant/` |
| 2 | Remettre les textes en forme | Réextraire paragraphes, listes, gras et liens depuis l’ancien HTML pour les 49 contenus aplatis ; relecture une à une des pages éditoriales ; un test refuse un texte long sans paragraphe | Plus aucun bloc de plus de 400 caractères sans saut de ligne |
| 3 | Thème visuel de l’administration | `admin.css` : libellés en clair (plus de petits badges en majuscules), texte à 16 px, champs aérés, aide lisible, couleurs de la maison, boutons Enregistrer/Publier bien visibles | Captures comparées à la phase 1 |
| 4 | Formulaires dans l’ordre où l’on pense | Pour chaque rubrique : l’essentiel d’abord (titre, texte, image, prix…), les réglages techniques en bas, repliés et annoncés comme « à ne pas toucher » ; libellés et aides réécrits sans jargon ; `label_singular` partout (« Ajouter une section ») ; résumés de blocs repliés qui ne disent jamais « No titre » ; barre d’outils réduite à gras, italique, lien, intertitre, listes | Relecture des libellés, test « aucun champ technique avant les champs utiles » |
| 5 | Choisir au lieu de taper | Liens vers un livre ou une page : listes déroulantes (relations Decap) au lieu d’identifiants ; adresse de page proposée à partir du titre | Plus aucun champ « identifiant » à saisir pour un lien interne |
| 6 | Offres et pages : un bloc par idée | Une section peut désigner des livres : leurs couvertures, auteurs et prix viennent de leurs fiches ; plus besoin de recopier images et liens ailleurs | Offres spéciales éditée en un seul bloc par offre |
| 7 | Aperçus fidèles au site | L’aperçu charge la feuille de style du site et reproduit la vraie mise en page de chaque rubrique : livre, personne, collection, actualité, page (sections, boutons d’achat, encadré de liens, galerie), accueil | Comparaison aperçu / page en ligne pour chaque rubrique |
| 8 | Accueil et listes | Descriptions de rubriques en langage simple, tri et groupes utiles dans les listes (brouillons d’abord, ordre du site) | Captures des listes |
| 9 | Essai avec les tâches type et documentation | Dérouler les tâches de la phase 1 sur l’admin finale ; mettre à jour `GUIDE-REDACTION.md` avec captures | Rapport `reports/admin-ux/apres/` + guide |

## Decisions

| Decision | Why |
| -------- | --- |
| Commencer par les textes (phase 2) | C’est la première cause d’illisibilité ; une belle interface autour d’un bloc de texte collé reste illisible. |
| Rester sur Decap CMS | Il fonctionne déjà avec le circuit de validation, GitHub et Free ; un autre outil remettrait en cause l’hébergement. |
| Ne pas changer la forme des données sans migration testée | Phases 5 et 6 modifient le schéma : chaque changement est accompagné de sa conversion des fichiers existants et de tests du générateur. |
| Aperçu = feuille de style du site | Une seule source de vérité visuelle : l’aperçu ne peut plus diverger du site. |
| Ne rien publier pendant l’exécution sans accord séparé | Mêmes règles que les plans précédents : tests et captures en local, mise en ligne sur demande. |

## Points à valider avant de commencer

1. L’ordre des phases : textes → thème → formulaires → relations → offres → aperçus.
2. Phase 2 : la remise en forme écrase le texte de 49 contenus. Aucun n’a été modifié depuis l’admin, sauf l’accueil (5 fois en août), qui sera fusionné à la main.
3. Phase 6 : le changement de structure des Offres spéciales est-il souhaité, ou seulement de meilleurs aperçus et relations ?
