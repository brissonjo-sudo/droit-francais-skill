---
tags: [skill/recherche-juridique, changelog, v3.3.0]
date: 2026-09-05
version: 3.3.0
plugin: 0.8.2
---

# recherche-juridique v3.3.0

Mise à jour du 2026-09-05. Voir [[index-recherche-juridique]].

## Type : alignement du noyau et fiabilisation des outils (MINEUR)

Les garanties annoncées — provenance, vigueur, routage — deviennent
effectives côté outils. Le noyau méthodologique rend l'affichage des
contrôles proportionné au livrable, sans en retirer aucun.

## Apports méthodologiques (skill)

| Axe | Apport |
|-----|--------|
| Traçabilité | Contrôles obligatoires, **affichage proportionné** : réponse simple sans récitation des étapes 0 / 0 bis / 7 ni auto-critique vide ; encart complet en note de fond, audit et `[complet]` |
| P3 | **Ordre de recherche** distingué de l'authenticité de la source, du rang de la norme et de l'effet d'une décision |
| Étape 2 | Échelle de récupération : **connecteur MCP** d'abord s'il est exposé, puis `scripts/legifrance.py`, puis repli web officiel |
| Étape 4 | Triangulation renforcée réservée aux **interprétations discutables** ; l'absence de jurisprudence localisable ne rend plus incertain un texte clair |

## Corrections outils (plugin 0.8.2)

| Défaut | Correction |
|--------|------------|
| Version historique présentée comme applicable | `get_article` expose `version_start_date`, `version_end_date`, `applicable_at_as_of_date`, `as_of_date`, `date_basis` ; `verified: true` n'atteste plus que la réponse officielle |
| Identifiant fourni renvoyé sans vérification | `search` appelle réellement `get_article` ; un `LEGIARTI` mal formé est refusé et n'atteint pas Judilibre |
| Routage perdant le code et la date | `search` conserve numéro, code (libellé officiel, sans approximation d'un code inconnu) et date ; `L. 2212-2 CGCT` route vers Légifrance |

## Fichiers créés

- `vault/recherche-juridique v3.3.0.md` (cette note).

## Fichiers modifiés

- `skill/SKILL.md` (traçabilité, P3, étapes 2, 4, 7, frontmatter).
- `skill/references/sources-autorisees.md`, `skill/CHANGELOG.md`.
- `skill/scripts/droit_francais/tools.py`, `mcp_server/server.py`.
- `tests/{test_mcp_app.py,check_live_tools.py}`.
- `README.md`, `docs/mcp-app.md`, `chatgpt-app-submission.json`.
- Manifestes `.claude-plugin/`, `.codex-plugin/`.
- `vault/{index-recherche-juridique,procedure-compacte,matrice-modes}.md`.

## Liens

- [[index-recherche-juridique]] — navigation principale
- [[procedure-compacte]] — étapes, triangulation, balises
- [[matrice-modes]] — P3 revu
