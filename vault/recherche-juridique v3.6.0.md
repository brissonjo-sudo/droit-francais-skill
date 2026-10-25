---
tags: [skill/recherche-juridique, changelog, v3.6.0]
date: 2026-10-25
version: 3.6.0
plugin: 0.9.0
---

# recherche-juridique v3.6.0

Refonte du 2026-10-21, publiée le 2026-10-25 (étiquette `skill-v3.6.0`).
Voir [[index-recherche-juridique]].

## Type : réorganisation (MINEUR)

Principes P1–P7, neuf étapes, modules, 18 modes et déclencheurs d'abstention
inchangés. Le noyau est raccourci ; ses développements passent dans des
références chargées selon le besoin.

## Apports

| Point | Exigence |
|-------|----------|
| Noyau court | Développements déplacés dans trois nouvelles références : `procedure-detaillee.md`, `techniques-raisonnement.md`, `modes-et-profils.md` ; huit références enrichies |
| Étape 2 — routage | Ordre normé : MCP officiel disponible, sinon script, puis web officiel, enfin abstention ; P1 y renvoie |
| Renvois | « module PÉNAL §6 » corrigé en §5 |
| Citations internes | Gabarits : fichiers de skill cités par le nom du skill et la section, sans lien ni chemin |
| Hors réseau | Manifeste du paquet d'instructions disponible sans réseau |

## Limites

Aucune mesure modèle n'accompagne cette version. Les dates de vérification
juridique embarquées ne sont pas actualisées par la refonte.

## Fichiers modifiés

- `skill/SKILL.md`, `skill/CHANGELOG.md` et les références de `skill/references/`
  (PR #132) ; publication : `skill/CHANGELOG.md`, `README.md`, `README.en.md`,
  `docs/installation.md`.
- `vault/index-recherche-juridique.md`, `vault/recherche-juridique v3.5.1.md`.

## Fichiers créés

- `vault/recherche-juridique v3.6.0.md` (cette note).

## Liens (maillage Graphify)

- [[index-recherche-juridique]] — navigation principale
- [[recherche-juridique v3.5.1]] — version précédente
- [[procedure-compacte]] — étapes et critères de sortie
