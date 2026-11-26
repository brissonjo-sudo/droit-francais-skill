---
tags: [skill/recherche-juridique, changelog, v3.7.0]
date: 2026-11-26
version: 3.7.0
---

# recherche-juridique v3.7.0

Publiée le 2026-11-26 (étiquette `skill-v3.7.0`). Voir [[index-recherche-juridique]].

## Type : ajout d'outils et de règles de provenance (MINEUR)

Principes P1–P7, neuf étapes, modules et 18 modes inchangés.

## Apports

| Point | Exigence |
|-------|----------|
| Numéros de texte dans P1 | N° de loi, d'ordonnance et de décret : identifiants officiels, omis ou marqués non vérifiés s'ils ne sont pas récupérés par outil |
| Document fourni | Capture ou PDF : piste de localisation, jamais preuve ; extrait d'un site privé : fait déclaré, hypothèse signalée |
| `search_texts` | Retrouve un texte non codifié par numéro ou NOR (fonds LODA) ; renvoie le `LEGITEXT` |
| `parent_text` | `get_article` indique le texte parent et la section |
| Gabarits §4 bis | Tenter `search_texts` avant le contournement manuel d'un décret non codifié |

## Limites

Aucune mesure modèle n'accompagne cette version. Les dates de vérification
juridique embarquées ne sont pas actualisées par la publication.

## Fichiers modifiés

- `skill/SKILL.md`, `skill/CHANGELOG.md`, `skill/references/gabarits-requetes.md`
  et leurs déclinaisons Gemini, Grok, Manus, Vibe (version 3.7.0).
- `README.md`, `README.en.md`, `docs/installation.md`.
- `vault/index-recherche-juridique.md`, `vault/recherche-juridique v3.6.0.md`.

## Fichiers créés

- `vault/recherche-juridique v3.7.0.md` (cette note).

## Liens (maillage Graphify)

- [[index-recherche-juridique]] — navigation principale
- [[recherche-juridique v3.6.0]] — version précédente
- [[procedure-compacte]] — étapes et critères de sortie
