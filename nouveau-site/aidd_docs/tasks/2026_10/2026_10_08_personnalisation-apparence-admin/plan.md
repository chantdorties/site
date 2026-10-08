---
objective: "Béatrice peut modifier des couleurs et des polices sûres depuis Decap CMS, avec un aperçu fidèle, sans CSS libre et sans régression visuelle du site actuel."
status: in-progress
---

# Plan: Personnalisation de l’apparence depuis l’administration

## Overview

| Field      | Value |
| ---------- | ----- |
| **Goal**   | Centraliser le thème visuel, le rendre configurable et l’exposer dans Decap CMS sans permettre de casser la mise en page. |
| **Source** | Demande utilisateur formulée dans la tâche Codex du 8 octobre 2026. |

## Phases

| # | Phase | File |
| --- | --- | --- |
| 1 | Figer la référence visuelle | [`phase-1.md`](./phase-1.md) |
| 2 | Centraliser les couleurs et les polices | [`phase-2.md`](./phase-2.md) |
| 3 | Créer le contrat de données Apparence | [`phase-3.md`](./phase-3.md) |
| 4 | Valider et sécuriser les réglages | [`phase-4.md`](./phase-4.md) |
| 5 | Générer le thème CSS | [`phase-5.md`](./phase-5.md) |
| 6 | Finaliser l’interface Decap | [`phase-6.md`](./phase-6.md) |
| 7 | Synchroniser l’aperçu Apparence | [`phase-7.md`](./phase-7.md) |
| 8 | Ajouter l’identité des rubriques | [`phase-8.md`](./phase-8.md) |
| 9 | Tester le comportement et le rendu | [`phase-9.md`](./phase-9.md) |
| 10 | Documenter et préparer la livraison | [`phase-10.md`](./phase-10.md) |

## Decisions

| Decision | Why |
| -------- | --- |
| Conserver le générateur statique et les fichiers JSON | La fonctionnalité doit prolonger l’architecture existante sans base de données. |
| Exposer seulement des couleurs et des polices prédéfinies | Du CSS libre permettrait de casser l’affichage, le responsive ou l’accessibilité. |
| Préserver les valeurs visuelles actuelles comme valeurs par défaut | La création du réglage ne doit provoquer aucune modification visible. |
| Utiliser des variables CSS sémantiques | Les noms décrivent le rôle visuel plutôt qu’une couleur particulière et restent compréhensibles quand la palette change. |
| Garder les tailles, espacements et règles responsive dans le code | Ces réglages ont des dépendances de mise en page trop fragiles pour être confiés à l’administration. |
| Traiter le logo principal après le thème de couleurs et polices | Le logo dépend du pipeline de médias et du HTML, pas seulement du thème CSS. |
| Ne pas inventer de logos de rubriques | Les assets et leur usage doivent être fournis ou validés par le client avant implémentation. |
| Ne pas déployer pendant l’exécution de ce plan sans autorisation séparée | Les tests locaux et la préparation du code ne valent pas autorisation de modifier le site public. |
