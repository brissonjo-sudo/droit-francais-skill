---
tags: [skill/recherche-juridique, changelog, v2.4.0]
date: 2026-06-27
version: 2.4.0
---

# recherche-juridique v2.4.0

Mise à jour du 2026-06-27. Voir [[index-recherche-juridique]].

## Type : consolidation (second audit, non iso-fond)

Traite les tensions introduites par la v2.3.0 et les points restés ouverts.
Fond juridique inchangé.

## Apports

| # | Apport |
|---|--------|
| 1 | **Jurisprudence** dans `legifrance.py` (`juri`/`ceta`/`constit`) — résout l'asymétrie de provenance (la règle vise aussi les n° de pourvoi/requête/décision) |
| 2 | **CI** GitHub Actions : `py_compile` + `check_links.py` + éval hors-ligne |
| 3 | **LLM-juge** (`run_eval.py --judge`) + doc de la limite « appel sans outils » + sondes de balises (Bc/Be/Bs/Bo) |
| 4 | **§1 dégraissé** : 14 modes en table + `references/modes-erreur.md` |
| 5 | Citations d'exemple marquées **illustratives** ; note noms d'outils ; README « Claude Code + portable » |

## Fichiers créés

- `skill/references/modes-erreur.md` — détail des 14 modes (ex-§1).
- `.github/workflows/ci.yml` — intégration continue.
- `tests/check_links.py` — vérificateur de liens Markdown.
- `vault/recherche-juridique v2.4.0.md` — cette note.

## Fichiers modifiés

- `skill/SKILL.md` (v2.4.0, §1 en table), `skill/CHANGELOG.md`.
- `skill/scripts/legifrance.py` + `README.md` (jurisprudence).
- `skill/references/` : `format-citation.md`, `gabarits-requetes.md`, `maintenance.md`.
- `tests/run_eval.py`, `tests/eval-modes-erreur.csv`, `tests/README.md`.
- `README.md`.

## Liens

- [[index-recherche-juridique]] — navigation principale
- [[structure-v2.3.0]] — arborescence (à jour pour l'essentiel)
- [[recherche-juridique v2.3.0]] — version précédente
