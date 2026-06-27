---
tags: [skill/recherche-juridique, structure, v2.3.0]
date: 2026-06-27
version: 2.3.0
---

# Structure v2.3.0 — découpage modulaire + outillage

Voir [[index-recherche-juridique]] pour la navigation.
Version précédente : [[structure-v2.2.0]].

## Arborescence du paquet

```
skill/
├── SKILL.md          ← noyau invariant (tous les §, gabarits stubés)
├── CHANGELOG.md      ← historique des versions
├── references/
│   ├── gabarits-sortie.md      ← §6 complet extrait du noyau
│   ├── modules.md              ← §5 complet extrait du noyau
│   ├── gabarits-requetes.md    ← requêtes Légifrance (+ pointeur script)
│   ├── checklist-vigueur.md    ← checklist 14 points (+ provenance)
│   ├── maintenance.md          ← revue annuelle
│   ├── sources-autorisees.md   ← hiérarchie sources P3
│   └── format-citation.md      ← formats citation P4 (+ provenance)
└── scripts/                    ← NOUVEAU v2.3.0 — outillage Palier 3
    ├── legifrance.py           ← récupération via API Légifrance/PISTE
    └── README.md               ← config PISTE + usage + codes de sortie
```

## Nouveautés v2.3.0 (évolution fonctionnelle, non iso-fond)

| Axe | Apport | Où |
|-----|--------|----|
| Fiabilité récupération | `scripts/legifrance.py` (API PISTE, stdlib) matérialise le Palier 3 : identifiant, date de vigueur, statut = réponse officielle | `skill/scripts/` ; SKILL §9 ; `gabarits-requetes.md` |
| Anti-simulation | **Règle de provenance** (P1) : identifiant officiel = appel d'outil de la session, sinon « non vérifié » + gabarit C interdit | SKILL P1 + E6 ; `format-citation.md` ; `checklist-vigueur.md` |
| Économie longueur | Balise **`[lookup]`** : sortie minimale (ni en-tête ni encart), sans alléger le fond | SKILL §0 |
| Cohérence | « 9 étapes (0, 0 bis, 1 à 7) » ; `SKILL.md` racine obsolète supprimé ; « 10 déclencheurs » | SKILL ; `maintenance.md` |
| Non-régression | `tests/eval-modes-erreur.csv` (14 modes + provenance + lookup) + `tests/run_eval.py` | `tests/` |

## Logique de découpage

| Critère | Noyau (`SKILL.md`) | Références (`references/`) | Outillage (`scripts/`) |
|---------|-------------------|---------------------------|------------------------|
| Contenu | Procédure, principes, modes, étapes, techniques, déclencheurs | Gabarits, modules, outils auxiliaires | Récupération en source primaire (API) |
| Fréquence de lecture | Chaque requête | À la demande | À l'étape 2 (récupération) |
| Modification | Rare | Ponctuelle | Suivi endpoints (revue annuelle) |
| Iso-fond | Noyau invariant entre versions mineures | Peut évoluer | Hors méthodologie — outil |

## Flux de navigation (mode A)

```
Requête utilisateur
    ↓
SKILL.md §0 – Déclenchement → activation   (balise [lookup] → voie rapide)
    ↓
SKILL.md §0/0bis – Qualification + arbitrage
    ↓
SKILL.md §1–§4 – Modes / Principes / Étapes / Techniques
    ↓
Étape 2 – Récupération → scripts/legifrance.py (provenance P1) [repli : web officiel]
    ↓
SKILL.md §5 stub → references/modules.md (si module actif)
    ↓
SKILL.md §7 – Déclencheurs d'abstention (10)
    ↓
SKILL.md §6 stub → references/gabarits-sortie.md (rédaction livrable)
    ↓
Étape 6 – Contrôle texte-cible + contrôle de provenance
    ↓
Livrable + encart récapitulatif   (omis si [lookup])
```

## Liens (maillage Graphify)

- [[SKILL.md]] → [[structure-v2.3.0]] (ce fichier)
- [[structure-v2.3.0]] → [[recherche-juridique v2.3.0]] (changelog)
- [[structure-v2.3.0]] → [[structure-v2.2.0]] (version précédente)
- [[structure-v2.3.0]] → [[procedure-compacte]] (étapes + balises, dont [lookup])
- [[structure-v2.3.0]] → [[matrice-modes]] (modes × garde-fous)
- [[structure-v2.3.0]] → [[modules-declencheurs]] (modules + abstention)
- [[structure-v2.3.0]] → [[étape 0 bis]] (détail garde procédurale)
