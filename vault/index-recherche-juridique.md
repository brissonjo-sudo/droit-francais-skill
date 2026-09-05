---
tags: [skill/recherche-juridique, index]
version: 3.3.0
---

# Index — skill recherche-juridique

## Navigation rapide (1 lecture = 1 besoin)

| Besoin | Fichier vault |
|--------|--------------|
| Quel principe/étape bloque quel mode ? | `matrice-modes.md` |
| Critère de sortie / action d'une étape | `procedure-compacte.md` |
| Balises [complet][express][syllogisme][opérationnel][lookup] | `procedure-compacte.md` |
| Règle triangulation (quand obligatoire) | `procedure-compacte.md` |
| Règle de provenance (identifiants) + voie rapide [lookup] | `structure-v2.3.0.md` |
| Déclencheurs d'un module | `modules-declencheurs.md` |
| 10 déclencheurs d'abstention + format | `modules-declencheurs.md` |
| Techniques T1–T4 | `modules-declencheurs.md` |
| Détail étape 0 bis (clause anti-échappatoire, économie questionnement) | `étape 0 bis.md` |
| Profils configurables (métier de l'utilisateur) | `../skill/profils/` |
| Récupération en source primaire (API PISTE, articles + jurisprudence) | `../skill/scripts/README.md` |
| Détail des 14 modes d'erreur | `../skill/references/modes-erreur.md` |
| Changelog v3.3.0 (dernier) | `recherche-juridique v3.3.0.md` |
| Applicabilité d'une version d'article (outils MCP) | `recherche-juridique v3.3.0.md` |
| Changelog v2.4.0 | `recherche-juridique v2.4.0.md` |
| Changelog v2.3.0 | `recherche-juridique v2.3.0.md` |
| Découpage modulaire + outillage v2.3.0 (noyau ↔ références ↔ scripts) | `structure-v2.3.0.md` |
| Noyau complet | `../skill/SKILL.md` |
| Déclinaison Grok (outils web natifs, noyau condensé) | `../grok_skill/README.md` |
| Déclinaison Gemini (agent générique non connecté) | `../gemini_agent/README.md` |
| Gabarits de sortie détaillés | `../skill/references/gabarits-sortie.md` |
| Modules activables détaillés | `../skill/references/modules.md` |

## Fichiers supprimés (remplacés par agrégats)

Les notes individuelles `étape 0`–`étape 7`, `P1`–`P7`, `mode 1`–`mode 14`,
`module PÉNAL`–`module CONTENTIEUX`, `déclencheurs d'abstention` n'existent pas
en fichiers séparés. Leur contenu est dans les 3 agrégats ci-dessus.

Écrites en `code` et non en wikilien : ce paragraphe déclare leur absence, et
les wikiliser créerait dans la vue graphe les nœuds fantômes qu'il annonce
justement comme inexistants. Ailleurs dans le vault, ces mêmes notions restent
en wikilien là où elles servent d'ancre conceptuelle dans une phrase.

## Liens (maillage Graphify)

Ce vault est lu par la vue graphe (Graphify). L'index est le **hub** :
toute note du vault y est reliée, et chaque note renvoie ici.

**Agrégats de méthode**

- [[procedure-compacte]] — étapes, critères de sortie, balises, triangulation
- [[matrice-modes]] — modes d'erreur × garde-fous, P1–P7, formats et registres
- [[modules-declencheurs]] — modules, techniques T1–T4, déclencheurs d'abstention
- [[étape 0 bis]] — garde procédurale d'entrée, détail

**Notes de structure**

- [[structure-v2.3.0]] — découpage noyau ↔ références ↔ scripts (courant)
- [[structure-v2.2.0]] — découpage initial (historique)

**Chaîne des versions** (de la plus récente à la plus ancienne)

- [[recherche-juridique v3.3.0]] — provenance, datation, routage ; déclinaisons
- [[recherche-juridique v3.0.0]] — noyau universel, métier en paramètre
- [[recherche-juridique v2.4.0]]
- [[recherche-juridique v2.3.0]]
- [[recherche-juridique v2.2.0]]
- [[recherche-juridique v2.1.0]]

**Hors vault** (chemins, pas des nœuds du graphe)

- `../skill/SKILL.md` — noyau, source de vérité méthodologique
- `../grok_skill/README.md` — déclinaison Grok
- `../gemini_agent/README.md` — déclinaison Gemini
