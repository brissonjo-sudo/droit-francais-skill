---
tags: [skill/recherche-juridique, changelog, v3.4.0]
date: 2026-09-14
version: 3.4.0
plugin: 0.8.3
---

# recherche-juridique v3.4.0

Mise à jour du 2026-09-14. Voir [[index-recherche-juridique]].

## Type : mise à jour du skill installé (MINEUR)

Ajout d'une fonction d'exploitation, sans changement méthodologique : mêmes
principes P1–P7, mêmes étapes, modes, modules et déclencheurs d'abstention.

## Apports

| Axe | Apport |
|-----|--------|
| Contrôle par session | Au premier usage, `npx skills check` si `npx` est disponible ; une version périmée est signalée en une phrase, sans interrompre l'analyse |
| Mode automatique | Désactivé par défaut ; activé par `.recherche-juridique-update.json` (`{ "automatic": true }`), au plus une fois par 24 heures, installation globale seulement |
| Garde-fous | `profil.md` et `scripts/.env` sauvegardés puis restaurés ; silence si réseau, Node ou emplacement indisponible ; les installations par marketplace gardent leur mécanisme |

## Fichiers créés

- `skill/scripts/update_skill.py`.
- `vault/recherche-juridique v3.4.0.md` (cette note).

## Fichiers modifiés

- `skill/SKILL.md` (section « Mise à jour », frontmatter), `skill/CHANGELOG.md`.
- `skills/recherche-juridique/SKILL.md`, `README.md`, `.gitignore`.
- `tests/test_skills.py`.
- `vault/index-recherche-juridique.md`, `vault/recherche-juridique v3.3.0.md`.

## Liens (maillage Graphify)

- [[index-recherche-juridique]] — navigation principale
- [[recherche-juridique v3.3.0]] — version précédente
