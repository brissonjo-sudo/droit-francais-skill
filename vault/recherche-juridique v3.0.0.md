---
tags: [skill/recherche-juridique, changelog, v3.0.0]
date: 2026-07-02
version: 3.0.0
---

# recherche-juridique v3.0.0

Mise à jour du 2026-07-02. Voir [[index-recherche-juridique]].

## Type : refonte structurelle (MAJEUR)

Le **noyau devient universel**, le **métier devient un paramètre** (profil).
Motivation : adoption. Le skill était visiblement personnel (Saint-Ouen / DGA /
Commissaire), ce qui bloquait l'usage par le reste de l'audience juridique.
Aucun contenu méthodologique retiré.

## Apports

| Axe | Apport |
|-----|--------|
| Profils | `skill/profils/` — 5 profils + `_modele` ; `profil.md` fixe des **défauts** (territorial, domaines, rôle (c)) |
| §0 chargement | Lecture de `profil.md` ; défauts jamais des certitudes ; sans profil → **neutre** (étape 0 bis pose la question) |
| §8 | « Cas particuliers PM » → renvoi à la section 5 du profil actif ; contenu PM déplacé dans `police-gendarmerie.md` |
| Vitrine | README : TL;DR EN, démo avant/après, badges, « sans clé API », « choisir son profil » |
| Licence | LICENSE = legalcode canonique CC BY-SA 4.0 (détection GitHub) |
| Éval | Sonde `N` (profil neutre) anti-régression |

## Profils fournis

`police-gendarmerie` (PN / gendarmerie / PM, distinction OPJ/APJ/APJA),
`avocat`, `juriste-entreprise`, `collectivites`, `etudiant-concours`, `_modele`.

## Fichiers créés

- `skill/profils/*.md` (6 fichiers).
- `vault/recherche-juridique v3.0.0.md` (cette note).

## Fichiers modifiés

- `skill/SKILL.md` (frontmatter, §0, §8, étape 7, §10, header).
- `skill/references/{maintenance,gabarits-sortie}.md`.
- `tests/{eval-modes-erreur.csv,README.md}`.
- `README.md`, `LICENSE`, `skill/CHANGELOG.md`, `.gitignore`.
- `vault/{index-recherche-juridique,procedure-compacte}.md`.

## Liens

- [[index-recherche-juridique]] — navigation principale
- [[recherche-juridique v2.4.0]] — version précédente
