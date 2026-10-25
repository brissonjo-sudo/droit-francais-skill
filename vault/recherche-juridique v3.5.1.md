---
tags: [skill/recherche-juridique, changelog, v3.5.1]
date: 2026-10-21
version: 3.5.1
plugin: 0.9.0
---

# recherche-juridique v3.5.1

Mise à jour du 2026-10-21. Voir [[index-recherche-juridique]].

## Type : ajustement de référence (PATCH)

Principes P1–P7, étapes, modules, modes et déclencheurs d'abstention
inchangés. La méthode s'appuie sur le nouvel outil MCP `get_article_history`
et précise les citations internes.

## Apports

| Point | Exigence |
|-------|----------|
| Étape 3 — fraîcheur | Voie outillée `get_article_history` : versions datées, texte modificateur de chacune, version applicable à la date de référence |
| États de version | `VIGUEUR_DIFF` = vacatio legis ; `ABROGE_DIFF` = abrogation programmée ; `_MORT_NE` = jamais en vigueur, à ne jamais citer |
| Preuve négative | `modifications_available: false` ne prouve pas l'absence de modification : contrôler la fiche Légifrance |
| T3 — archéologie textuelle | Version initiale et modificateurs datés fournis par l'outil ; le motif de la réforme reste à rechercher |
| Citations internes | Fichiers de skill cités par le nom du skill et la section, sans lien ni chemin |

## Origine

Inventaire testé des 68 points d'accès de l'API Légifrance (21/10/2026) et
outil livré par la PR #126 ; états vérifiés sur le CGI, art. 200 quater A.

## Test fonctionnel (maintenance §7)

Quatre requêtes témoins passées le 2026-10-21 : référence d'article (version
applicable et modificateurs obtenus par l'outil), PÉNAL + ACTE-ADMIN, mode B
`[complet]` (modules « sans objet » justifiés, encart présent), DOC-AUDIT
(registre, 100 % du risque élevé, matrice, exécution d'office testée à part,
montants distingués, pas de « conforme »). Correction issue du test : voie de
repli explicite quand l'outil n'est pas exposé. Constats hors périmètre,
consignés pour la suite : conduite à tenir face au quota du connecteur, seuil
de l'étape 0 bis pour une demande générale.

## Fichiers créés

- `vault/recherche-juridique v3.5.1.md` (cette note).

## Fichiers modifiés

- `skill/SKILL.md` (frontmatter, étape 3, T3), `skill/CHANGELOG.md`,
  `skill/references/checklist-vigueur.md`, `skill/references/gabarits-requetes.md`.
- `vault/index-recherche-juridique.md`, `vault/recherche-juridique v3.5.0.md`.

## Liens (maillage Graphify)

- [[index-recherche-juridique]] — navigation principale
- [[recherche-juridique v3.5.0]] — version précédente
- [[recherche-juridique v3.6.0]] — version suivante
- [[procedure-compacte]] — étape 3 et critère de sortie
- [[modules-declencheurs]] — technique T3
