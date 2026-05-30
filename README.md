# droit-francais-skill

**Skill LLM — méthodologie de recherche en droit français (v3.0.0)**

Un skill pour Claude Code, fonctionnant avec toutes les IA, qui encode une méthodologie rigoureuse de
recherche juridique en droit français, conçue pour résister aux
quatorze modes d'erreur typiques des LLM appliqués au droit.

---

## Public visé

- Juristes et praticiens du droit
- Rédacteurs d'actes administratifs ou de notes juridiques
- Tout utilisateur ayant besoin de références juridiques fiables dans
  un acte officiel ou un document institutionnel

---

## Ce que fait ce skill

Quand Claude détecte une requête juridique (article de loi, qualification
pénale, jurisprudence, rédaction d'acte, vérification d'un texte en
vigueur…), ce skill active une procédure en 7 étapes incluant :

- **7 principes** anti-hallucination (primarité des sources, date de
  référence, hiérarchie des normes, citation traçable, séparation des
  registres, légalité criminelle, abstention informée)
- **7 étapes** avec critères de sortie explicites (qualification →
  cartographie → récupération → fraîcheur → jurisprudence → rédaction
  → auto-critique)
- **4 techniques** de raisonnement (qualification adversariale,
  triangulation, archéologie textuelle, distinction)
- **4 modules activables** selon la requête (PÉNAL, ACTE-ADMIN,
  FOND, CONTENTIEUX)
- **Double mode opératoire** A (noyau + modules) / B (exhaustif avec
  balise `[complet]`)
- **Gabarits de sortie** normalisés (express, fond, citation pour acte,
  raisonnement syllogistique)

---

## Installation

### Windows

```powershell
# Cloner dans le dossier skills global Claude Code
git clone https://github.com/brissonjo-sudo/droit-francais-skill "$env:USERPROFILE\.claude\skills\recherche-juridique"
```

### macOS / Linux

```bash
git clone https://github.com/brissonjo-sudo/droit-francais-skill ~/.claude/skills/recherche-juridique
```

### Installation manuelle

Copier le dossier entier dans `~/.claude/skills/recherche-juridique/`
(le nom du dossier doit correspondre au champ `nom:` dans le SKILL.md).

---

## Déclenchement

Le skill s'active automatiquement quand vous :
- citez ou demandez un article de loi, de code, un décret, un arrêté
- demandez une qualification juridique (pénale, administrative, civile)
- vérifiez si un texte est en vigueur, abrogé ou modifié
- demandez une jurisprudence (Cass., CE, CC, CJUE, CEDH)
- rédigez un acte administratif, une note juridique, un mémoire ou une
  consultation

**Balises de contrôle :**
- `[complet]` — mode exhaustif, tous modules activés
- `[express]` — mode allégé (PÉNAL toujours actif)
- `[syllogisme]` — structure majeure / mineure / conclusion
- `[opérationnel]` — section implications opérationnelles activée

---

## Fichiers

```
droit-francais-skill/
├── SKILL.md                  # Cœur méthodologique
├── checklist-vigueur.md      # Checklist 14 points vérification Légifrance
├── gabarits-requetes.md      # Requêtes web_fetch/web_search optimisées
└── docs/
    └── maintenance.md        # Procédure de revue annuelle (1er septembre)
```

---

## Maintenance

Revue annuelle recommandée le **1er septembre** (rentrée juridique).
Procédure détaillée → [`docs/maintenance.md`](docs/maintenance.md).

---

## Licence

[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](LICENSE)

© 2026 @brissonjo-sudo

---

## Contribution

Issues et pull requests bienvenues sur GitHub.
