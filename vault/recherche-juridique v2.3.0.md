---
tags: [skill/recherche-juridique, changelog, v2.3.0]
date: 2026-06-27
version: 2.3.0
---

# recherche-juridique v2.3.0

Mise à jour du 2026-06-27. Voir [[index-recherche-juridique]].

## Type : évolution fonctionnelle (non iso-fond)

Issu d'un audit du skill. Contrairement à la v2.2.0 (refactoring iso-fond),
cette version **ajoute des garanties** : récupération outillée, règle de
provenance, voie rapide. Le contenu juridique (14 modes, 7 principes, étapes,
techniques, modules) reste inchangé sur le fond.

## Cinq axes

| Axe | Apport |
|-----|--------|
| 1 — Fiabilité | `scripts/legifrance.py` : API Légifrance/PISTE, récupération déterministe (identifiant, date de vigueur, statut) — Palier 3 du §9 |
| 2 — Anti-simulation | **Règle de provenance** (P1) : identifiant officiel = appel d'outil de la session, sinon « non vérifié » + gabarit C interdit |
| 3 — Économie | Balise **`[lookup]`** : sortie minimale, sans dégrader le fond |
| 4 — Cohérence | « 9 étapes (0, 0 bis, 1 à 7) » ; `SKILL.md` racine supprimé ; « 9 → 10 déclencheurs » |
| 5 — Non-régression | `tests/eval-modes-erreur.csv` + `tests/run_eval.py` (14 modes + provenance + lookup) |

## Fichiers créés

| Fichier | Contenu |
|---------|---------|
| `skill/scripts/legifrance.py` | CLI Python stdlib — `ping` / `article` / `search` via PISTE |
| `skill/scripts/README.md` | Obtention identifiants PISTE, config env, codes de sortie |
| `tests/eval-modes-erreur.csv` | Sonde par mode d'erreur + contrôles provenance (P) et lookup (L) |
| `tests/run_eval.py` | Harnais sans dépendance (hors-ligne / `--live`) |
| `tests/README.md` | Mode d'emploi des deux jeux d'éval |
| `vault/structure-v2.3.0.md` | Découpage + outillage + maillage |
| `vault/recherche-juridique v2.3.0.md` | Cette note |

## Fichiers modifiés

- `skill/SKILL.md` — règle de provenance (P1 + E6), balise `[lookup]`, §9 (script), numérotation « 9 étapes ».
- `skill/references/` — `format-citation.md`, `checklist-vigueur.md`, `gabarits-requetes.md`, `maintenance.md`.
- `README.md`, `skill/CHANGELOG.md`, `.gitignore`.
- `vault/index-recherche-juridique.md`, `vault/procedure-compacte.md`.

## Fichier supprimé

- `SKILL.md` (racine) — pointeur v2.1.0 obsolète, évitait la coexistence de deux `SKILL.md`.

## Liens

- [[index-recherche-juridique]] — navigation principale
- [[structure-v2.3.0]] — arborescence et flux
- [[recherche-juridique v2.2.0]] — version précédente
