---
tags: [skill/recherche-juridique, changelog, v3.4.1]
date: 2026-09-14
version: 3.4.1
plugin: 0.8.3
---

# recherche-juridique v3.4.1

Mise à jour du 2026-09-14. Voir [[index-recherche-juridique]].

## Type : vérité du dépôt (PATCH)

Aucune règle méthodologique ajoutée, retirée ni modifiée. Le dépôt cesse de
se décrire faussement avant la mise sous mesure du noyau. Préparée le
2026-09-06 sous le numéro 3.3.1, renumérotée après la sortie de la 3.4.0.

## Corrections

| Où | Affirmait | Réalité |
|----|-----------|---------|
| `SKILL.md` | renvoi « §0.5 » | section inexistante ; profil au §0 |
| `SKILL.md` §7 | gabarits ouvrant par `##` dans un bloc de code | deux sections fantômes pour un outil lisant `^## ` |
| [[matrice-modes]], index | 14 modes | 18 depuis la v3.2.0 |
| [[modules-declencheurs]] | 5 modules | 6 depuis la v3.2.0 (DOC-AUDIT) |
| [[procedure-compacte]] | rôle (c) = « jury concours » | paramétrable par le profil depuis la v3.0.0 |
| `maintenance.md` §0 | archiver dans `archive/` | dossier inexistant ; archive = Git + note de vault |
| `maintenance.md` §3 | CI = 4 contrôles | 8 |
| `tests/README.md` | 3 requêtes témoins | 4 |

## Ajouté

Les motifs interdits `LEGIARTI[0-9]{6}` des sondes 1 et P ne valent que
**sans outils** : avec les outils, un identifiant récupéré est le comportement
attendu.

## Liens (maillage Graphify)

- [[index-recherche-juridique]] — navigation principale
- [[recherche-juridique v3.4.0]] — version précédente
- [[matrice-modes]] — modes 15 à 18 ajoutés
- [[modules-declencheurs]] — sixième module
- [[procedure-compacte]] — rôle (c) paramétrable
