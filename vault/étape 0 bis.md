---
tags: [skill/recherche-juridique, procédure, v2.1.0]
version_introduite: 2.1.0
date: 2026-06-02
---

# Étape 0 bis — Arbitrage des informations manquantes

Ajoutée en [[recherche-juridique v2.1.0]]. S'insère entre [[étape 0]] et [[étape 1]]. **Visible dans la réponse finale.**

## Rôle

Garde procédurale d'entrée : empêche de déclencher [[mode 10]] et [[mode 14]] en analysant le mauvais régime ou le mauvais champ territorial sur une hypothèse décisionnelle non levée. Prolonge [[P2]] et [[P7]] au stade de l'entrée.

## Mécanisme : test décisionnel

Pour chaque information manquante identifiée après [[étape 0]] :

| La réponse change-t-elle selon la valeur ? | Qualification | Conduite |
|---|---|---|
| Oui (conclusion, régime, qualification ou procédure bascule) | **Décisionnelle** | Question obligatoire à l'utilisateur — recherche suspendue |
| Non | **Non décisionnelle** | Hypothèse déclarée explicite, puis poursuite |

## Clause anti-échappatoire (impérative)

La déclaration d'hypothèse ne peut **jamais** se substituer à la question sur un point décisionnel.

**Signal d'alarme** : si le skill écrit qu'un point est « déterminant », « central », « commande toute la réponse » ou « point pivot » → c'est le marqueur d'une question obligatoire, pas d'une hypothèse à déclarer.

## Économie du questionnement

- Pas de question si l'[[étape 0]] est complète et qu'aucun point décisionnel ne manque.
- Une seule question par défaut (plafond : trois).
- Question fermée ou à choix si possible.
- Réservée à ce que seul l'utilisateur détient — si vérifiable sur Légifrance, chercher soi-même.

## Esquisse conditionnelle bornée

Tant qu'un point décisionnel n'est pas tranché : au plus un « si (a) … / si (b) … » de quelques lignes. Jamais un gabarit B complet sur une branche présumée.

## 10e déclencheur d'abstention

Cette étape fonde le 10e cas des [[déclencheurs d'abstention]] : information décisionnelle détenue par le seul utilisateur, manquante. Format dédié : **« Question préalable nécessaire »**.

## Liens

- [[P2]] — régime/date applicables
- [[P7]] — abstention informée (pendant côté sortie)
- [[étape 0]] — désambiguïsation factuelle (amont)
- [[étape 1]] — cartographie des sources (aval)
- [[mode 10]] — oubli du champ d'application territorial
- [[mode 14]] — faux positif textuel / mauvaise fonction juridique
- [[déclencheurs d'abstention]] — 10e déclencheur
