---
objective: "Chaque partie du site se règle à un seul endroit de l’administration, avec les mêmes composants d’une rubrique à l’autre, sans changement visible sur le site."
status: in-progress
---

# Plan : Cohérence de l’administration et composants communs

## Overview

| Field      | Value |
| ---------- | ----- |
| **Goal**   | Supprimer les doublons d’écrans (accueil, actualités, pages principales), harmoniser les composants de formulaire répétés et factoriser le HTML recopié dans le générateur. |
| **Source** | Analyses du 8 octobre 2026 : « Textes de l’accueil » et « Pages principales › Accueil » font doublon ; composants identiques définis différemment d’une rubrique à l’autre. |
| **Prérequis** | PR #22 (refonte de l’ergonomie) fusionnée : ce plan part de sa branche ou de `main` après fusion. |
| **Garde-fou** | Le site généré doit rester identique octet pour octet, sauf écarts listés et voulus. Chaque phase compare `dist/` avant/après. |

## Constat

### Un même élément du site réglé à plusieurs endroits

| # | Élément | Aujourd’hui | Cible |
| --- | --- | --- | --- |
| A | Page d’accueil | 3 écrans : « Réglages › Textes de l’accueil » (titres), « Pages principales › Accueil » (6 textes repérés par des identifiants modifiables), « Réglages › Paiement » (libellés des boutons de don et d’offres) | Un seul écran « Page d’accueil », 4 blocs numérotés, chacun complet ; référencement et anciennes adresses dans ses réglages techniques |
| B | Page Actualités | « Introductions des pages › Actualités » (titre, texte, description SEO) + « Pages principales › Actualités » (SEO complet, anciennes adresses) : deux descriptions SEO, la seconde l’emporte | Un seul écran dans « Introductions des pages », une seule description SEO |
| C | Mentions légales | Dans « Pages principales », avec le formulaire d’une page de la maison mais sans sa mise en forme | Dans « Pages de la maison », protégée comme aujourd’hui |
| D | Présentation de la maison | « Identité › Description générale » (référencement de l’accueil) et « Pied de page › Présentation » sans explication | Libellés et aides qui disent à quoi sert chacune |
| E | Introduction de la page Projets | Dans « Pages de la maison », alors que les autres pages générées ont la leur dans « Introductions » | À trancher (voir Points à valider) |

### Un même composant de formulaire défini plusieurs fois

| # | Composant | Variantes | Cible |
| --- | --- | --- | --- |
| F | Adresse de la page | « Adresse de la page » / « Identifiant » | Un seul bloc partagé, même nom, même aide |
| G | Auteurs, illustrateurs, collection | Aides et obligations différentes entre Livres et Projets | Définitions partagées ; seule l’obligation diffère, explicitement |
| H | Liste de liens « libellé + adresse » | Menu, pied de page, recherche : 3 définitions | Un bloc partagé |
| I | Identifiant de bouton PayPal | Fiche livre, sections, don : motif et aides différents | Un bloc partagé (motif, aide, avertissement) |
| J | Barres d’outils de texte | Deux jeux, appliqués sans règle claire | Règle écrite : texte long = jeu complet, texte court = jeu réduit |
| K | Intertitres et ordre | Absents de Menu, Pied de page, Introductions, Mentions légales | Partout |
| L | Image + texte alternatif | 4 paires de champs séparés et des blocs « image + alt » dans les listes | Même libellé et même aide partout ; forme des données inchangée (voir Décisions) |

### Du HTML recopié dans le générateur

| # | Élément | Situation | Cible |
| --- | --- | --- | --- |
| M | En-tête de page (fil d’Ariane, surtitre, titre, introduction) | Écrit dans 7 fichiers de `tools/rendu/pages/` | Une fonction `render_page_heading` |
| N | Formulaire PayPal | Recopié dans 4 fichiers | Une fonction `render_paypal_form` |
| O | Aperçus de l’administration | `preview.js` recopie le HTML du site | Un test qui vérifie que chaque classe utilisée par les aperçus existe dans le HTML généré |

## Phases

| # | Phase | Contenu | Livrable vérifiable | Statut |
| --- | --- | --- | --- | --- |
| 1 | Filet de sécurité | `tools/compare-dist.py` : compare deux `dist/` (HTML aux retours à la ligne près, le reste octet pour octet) ; captures des écrans concernés dans `reports/admin-ux/coherence-avant/` | Comparaison vide sur `main` | done |
| 2 | Composants HTML communs (M, N) | `render_page_heading` et `render_paypal_form`, appelés partout ; aucun changement de sortie | Comparaison `dist/` : identique | done |
| 3 | Composants de formulaire partagés (F, G, H, I, J, L) | Ancres YAML uniques pour adresse, relations, liste de liens, identifiant PayPal, image + texte alternatif ; règle des barres d’outils écrite dans `config.yml` | Test : chaque composant n’a qu’une définition ; données inchangées | done |
| 4 | Page d’accueil en un seul écran (A) | Les 6 textes de `pages-fixes/accueil.json` rejoignent `reglages/accueil.json`, rangés par bloc, avec des noms de champs parlants au lieu des identifiants ; libellés des boutons de don et d’offres déplacés de Paiement vers l’accueil (l’identifiant PayPal du don reste dans Paiement) ; référencement et anciennes adresses de l’accueil dans ses réglages techniques ; générateur, validation et aperçu adaptés ; « Pages principales › Accueil » retiré | Comparaison `dist/` : identique ; plus aucun identifiant de section visible | done |
| 5 | Page Actualités en un seul écran (B) | Référencement complet et anciennes adresses dans « Introductions › Actualités » ; une seule description SEO, valeur actuelle conservée selon la règle d’aujourd’hui (celle de la page l’emporte) ; « Pages principales › Actualités » retiré | Comparaison `dist/` : identique | pending |
| 6 | Mentions légales dans « Pages de la maison » (C) | Fichier déplacé dans `content/pages/`, adresse et suppression protégées par la validation ; collection « Pages principales » supprimée | Comparaison `dist/` : identique ; test de protection | pending |
| 7 | Libellés et intertitres restants (D, E, K) | Intertitres pour Menu, Pied de page, Introductions ; libellés et aides des deux présentations ; décision Projets appliquée | Relecture des écrans, captures après | pending |
| 8 | Aperçus sous contrôle (O) | Test : classes des aperçus présentes dans le HTML généré ; aperçu « Page d’accueil » complété avec les textes déplacés | Test vert, captures | pending |
| 9 | Documentation et essai | `GUIDE-REDACTION.md` (« Où se règle quel texte » réécrit), `ADMINISTRATION.md`, tâches types rejouées | Guide à jour, rapport `reports/admin-ux/coherence-apres/` | pending |

## Decisions

| Decision | Why |
| -------- | --- |
| Commencer par les composants HTML (phase 2) | Sans effet visible, ils rendent les déplacements de données suivants plus sûrs et plus courts. |
| Le site ne doit pas changer | Il s’agit de ranger l’administration : toute différence de `dist/` est une régression, sauf écart listé dans la phase. |
| Chaque déplacement de données a sa conversion et son test | Même règle que pour les offres groupées : les fichiers existants sont convertis par script, et la validation refuse l’ancienne forme une fois la conversion faite. |
| Ne pas fusionner les paires image + texte alternatif | Changer `couverture`/`couvertureAlt` en un bloc toucherait 64 livres, les aperçus et le générateur, pour un gain visuel nul : on harmonise libellés et aides seulement. |
| Garder l’identifiant PayPal du don dans Paiement | C’est une donnée technique fournie par PayPal ; seul le texte visible rejoint l’accueil. |
| Pas de nouvel outil pour partager le HTML entre site et aperçus | Générer `preview.js` depuis Python serait lourd ; un test de cohérence des classes suffit à détecter les écarts. |
| Ne rien publier sans accord séparé | Comme les plans précédents. |

## Points validés (8 octobre 2026)

1. Les libellés des boutons de don et d’offres passent dans l’écran Page d’accueil.
2. L’introduction de la page Projets remonte dans « Introductions des pages ».
3. Les mentions légales rejoignent « Pages de la maison », protégées.
4. Branche `feat/coherence-admin`, partie de `main` après la fusion de la PR #22.
