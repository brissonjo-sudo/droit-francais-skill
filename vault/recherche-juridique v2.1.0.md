---
tags: [skill/recherche-juridique, changelog, v2.1.0]
date: 2026-06-02
version: 2.1.0
---

# recherche-juridique v2.1.0

Mise à jour du 2026-06-02. Voir [[index-recherche-juridique]].

## Nouveauté principale : [[étape 0 bis]]

Étape insérée entre [[étape 0]] et [[étape 1]]. Visible dans la réponse finale comme les étapes 0 et 7.

### Ce qu'elle apporte

| Mécanisme | Description |
|---|---|
| **Test décisionnel** | Classe chaque information manquante : décisionnelle (question obligatoire) ou non décisionnelle (hypothèse déclarée autorisée) |
| **Clause anti-échappatoire** | Interdit de traiter un point « déterminant » par hypothèse au lieu d'une question |
| **Économie du questionnement** | Max 3 questions, fermées si possible, jamais pour ce que le skill peut chercher seul |
| **Esquisse conditionnelle bornée** | Si(a)/si(b) en quelques lignes tant qu'un point décisionnel est ouvert — jamais d'analyse complète sur une branche présumée |

### Motivation

Deux cas observés où une ambiguïté **décisionnelle** a été traitée par hypothèse — déclarée ou silencieuse — au lieu d'une question, produisant (mode B) une analyse complète sur une fondation non confirmée. Le second cas : le skill avait lui-même qualifié le point de « déterminant » puis avait écrit « je traite ce scénario comme principal ». La clause anti-échappatoire vise ce contournement par transparence.

## Autres modifications v2.1.0

- **[[P7]]** : corollaire d'entrée — l'abstention informée a son pendant au stade de l'entrée (étape 0 bis).
- **§0 Architecture** : aucune balise (`[express]`, `[complet]`) ne dispense de l'étape 0 bis.
- **[[étape 0]]** : critère de sortie renvoie explicitement vers l'étape 0 bis.
- **§7 [[déclencheurs d'abstention]]** : 10e cas ajouté + format « Question préalable nécessaire ».
- **§8 cas particuliers** : nouveau cas « Répartition des compétences intercommunales (MGP/EPT) » — exemple type de point décisionnel (compétence statutaire vs supplémentaire, L. 5211-17 CGCT).
- **§9 Palier 3** : étape 0 bis ajoutée aux étapes essentielles à l'API PISTE.

## Ce qui n'a pas changé

- 14 modes d'erreur (l'étape 0 bis est une garde procédurale, pas un 15e mode).
- 7 principes, procédure en 7 étapes, double mode A/B, 5 modules, 4 techniques, 3 gabarits + sous-gabarit concours.
