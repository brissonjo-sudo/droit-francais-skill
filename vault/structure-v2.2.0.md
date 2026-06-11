---
tags: [skill/recherche-juridique, structure, v2.2.0]
date: 2026-06-11
version: 2.2.0
---

# Structure v2.2.0 — découpage modulaire

Voir [[index-recherche-juridique]] pour la navigation.

## Arborescence du paquet

```
skill/
├── SKILL.md          ← noyau invariant (tous les §, gabarits stubés)
├── CHANGELOG.md      ← historique des versions
└── references/
    ├── gabarits-sortie.md      ← §6 complet extrait du noyau
    ├── modules.md              ← §5 complet extrait du noyau
    ├── gabarits-requetes.md    ← requêtes Légifrance (ex-racine)
    ├── checklist-vigueur.md    ← checklist 14 points (ex-racine)
    ├── maintenance.md          ← revue annuelle (ex-docs/)
    ├── sources-autorisees.md   ← hiérarchie sources P3 (ex-docs/)
    └── format-citation.md      ← formats citation P4 (ex-docs/)
```

## Logique de découpage

| Critère | Noyau (`SKILL.md`) | Références (`references/`) |
|---------|-------------------|---------------------------|
| Contenu | Procédure, principes, modes, étapes, techniques, déclencheurs, cas particuliers | Gabarits complets, modules détaillés, outils auxiliaires |
| Fréquence de lecture | Chaque requête (activation du skill) | À la demande (module actif, rédaction livrable) |
| Modification | Rare (révisions méthodologiques) | Ponctuelle (ajout gabarit, format citation) |
| Iso-fond | Noyau invariant entre versions mineures | Peut évoluer sans toucher le noyau |

## Flux de navigation (mode A)

```
Requête utilisateur
    ↓
SKILL.md §0 – Déclenchement → activation
    ↓
SKILL.md §0/0bis – Qualification + arbitrage
    ↓
SKILL.md §1–§4 – Modes / Principes / Étapes / Techniques
    ↓
SKILL.md §5 stub → references/modules.md (si module actif)
    ↓
SKILL.md §7 – Déclencheurs d'abstention
    ↓
SKILL.md §6 stub → references/gabarits-sortie.md (rédaction livrable)
    ↓
Livrable + encart récapitulatif
```

## Liens (maillage Graphify)

- [[SKILL.md]] → [[structure-v2.2.0]] (ce fichier)
- [[structure-v2.2.0]] → [[recherche-juridique v2.2.0]] (changelog)
- [[structure-v2.2.0]] → [[procedure-compacte]] (étapes en table)
- [[structure-v2.2.0]] → [[matrice-modes]] (modes × garde-fous)
- [[structure-v2.2.0]] → [[modules-declencheurs]] (modules + abstention)
- [[structure-v2.2.0]] → [[étape 0 bis]] (détail garde procédurale)
