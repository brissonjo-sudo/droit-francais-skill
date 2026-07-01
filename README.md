# droit-francais-skill

**Skill LLM — méthodologie de recherche en droit français (v2.4.0)**

Un skill pensé pour **Claude Code** (le format `SKILL.md` et les outils
`WebFetch`/`WebSearch`/`scripts/legifrance.py` en relèvent), et **portable**
à d'autres assistants moyennant l'adaptation des noms d'outils. Il encode une
méthodologie rigoureuse de recherche juridique en droit français, conçue pour
résister aux quatorze modes d'erreur typiques des LLM appliqués au droit.

---

## Public visé

- Cadres territoriaux (police municipale, administration locale)
- Juristes praticiens
- Candidats aux concours de catégorie A de la sécurité intérieure
  (Commissaire de Police, etc.)
- Tout utilisateur ayant besoin de références juridiques fiables dans
  un acte officiel ou un document institutionnel

---

## Ce que fait ce skill

Quand Claude détecte une requête juridique (article de loi, qualification
pénale, jurisprudence, rédaction d'acte, vérification d'un texte en
vigueur…), ce skill active une procédure en 9 étapes incluant :

- **7 principes** anti-hallucination (primarité des sources, date de
  référence, hiérarchie des normes, citation traçable, séparation des
  registres, légalité criminelle, abstention informée)
- **9 étapes** avec critères de sortie explicites : qualification (0) →
  **arbitrage informations manquantes (0 bis, v2.1.0)** → cartographie (1) →
  récupération (2) → fraîcheur (3) → jurisprudence (4) → articulation (5) →
  rédaction (6) → auto-critique (7)
- **4 techniques** de raisonnement (qualification adversariale,
  triangulation, archéologie textuelle, distinction)
- **5 modules activables** selon la requête (PÉNAL, ACTE-ADMIN, PA-PJ,
  FOND, CONTENTIEUX)
- **Double mode opératoire** A (noyau + modules) / B (exhaustif avec
  balise `[complet]`)
- **Gabarits de sortie** normalisés (express, fond, citation pour acte,
  note de concours)
- **Règle de provenance** (v2.3.0) : tout identifiant officiel
  (`LEGIARTI`, `NOR`, n° de pourvoi…) doit provenir d'un appel d'outil
  de la session, jamais de la mémoire — sinon marqué « non vérifié »
- **Voie rapide `[lookup]`** (v2.3.0) : sortie minimale pour une
  référence ponctuelle non controversée, sans dégrader le fond
- **Récupération outillée** (v2.3.0, jurisprudence en v2.4.0) :
  `skill/scripts/legifrance.py` interroge l'API Légifrance/PISTE (articles de
  code + décisions Cass./CE/CC) pour fiabiliser l'étape 2

---

## Installation

> **Installation :** empaqueter uniquement le dossier `skill/` — il contient le
> noyau (`SKILL.md`), l'historique (`CHANGELOG.md`), les références
> (`references/`) et l'outillage (`scripts/`). Le dossier `vault/` est
> réservé aux notes Obsidian et ne fait pas partie du paquet skill.

### Windows

```powershell
# Cloner puis copier uniquement skill/ dans le dossier skills Claude Code
git clone https://github.com/brissonjo-sudo/droit-francais-skill
Copy-Item -Recurse droit-francais-skill\skill "$env:USERPROFILE\.claude\skills\recherche-juridique"
```

### macOS / Linux

```bash
git clone https://github.com/brissonjo-sudo/droit-francais-skill
cp -r droit-francais-skill/skill ~/.claude/skills/recherche-juridique
```

### Installation manuelle

Copier le dossier `skill/` (contenu, pas le dossier lui-même) dans
`~/.claude/skills/recherche-juridique/`. Le champ `name:` dans
`skill/SKILL.md` doit correspondre au nom du dossier d'installation.

---

## Déclenchement

Le skill s'active automatiquement quand vous :
- citez ou demandez un article de loi, de code, un décret, un arrêté
- demandez une qualification juridique (pénale, administrative, civile)
- vérifiez si un texte est en vigueur, abrogé ou modifié
- demandez une jurisprudence (Cass., CE, CC, CJUE, CEDH)
- rédigez un arrêté municipal, une note au Maire, un mémoire
- préparez un oral ou écrit de concours

**Balises de contrôle :**
- `[complet]` — mode exhaustif, tous modules activés
- `[express]` — mode allégé (PÉNAL toujours actif)
- `[syllogisme]` — structure majeure / mineure / conclusion (concours)
- `[opérationnel]` — section implications opérationnelles activée
- `[lookup]` — voie rapide : référence ponctuelle, sortie minimale

---

## Arborescence (v2.4.0)

```
droit-francais-skill/
├── skill/                          ← seul dossier empaqueté pour installation
│   ├── SKILL.md                    ← noyau méthodologique
│   ├── CHANGELOG.md                ← historique des versions
│   ├── references/
│   │   ├── gabarits-sortie.md      ← gabarits A/B/C + syllogisme (détail §6)
│   │   ├── modules.md              ← 5 modules activables (détail §5)
│   │   ├── modes-erreur.md         ← détail des 14 modes d'erreur (détail §1)
│   │   ├── gabarits-requetes.md    ← requêtes Légifrance optimisées
│   │   ├── checklist-vigueur.md    ← checklist 14 points vérification
│   │   ├── maintenance.md          ← procédure de revue annuelle
│   │   ├── sources-autorisees.md   ← hiérarchie des sources (complément P3)
│   │   └── format-citation.md      ← formats de citation normalisés (complément P4)
│   └── scripts/                    ← outillage Palier 3
│       ├── legifrance.py           ← API Légifrance/PISTE (articles + jurisprudence)
│       ├── .env.example            ← gabarit de configuration (BYOK)
│       └── README.md               ← configuration PISTE + usage
├── .github/workflows/ci.yml        ← CI (py_compile + liens + éval hors-ligne)
├── vault/                          ← notes Obsidian (hors paquet)
├── tests/                          ← évals (14 modes + balises + Copilot) + runners
├── README.md
└── LICENSE
```

---

## Maintenance

Revue annuelle recommandée le **1er septembre** (rentrée juridique).
Procédure détaillée → [`skill/references/maintenance.md`](skill/references/maintenance.md).

> **Note de synchronisation :** à chaque release, mettre à jour `README.md`
> (version, arborescence) et `skill/CHANGELOG.md` (entrée Ajouté/Modifié/Conservé)
> avant de pousser le tag.

---

## Licence

[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](LICENSE)

© 2026 @brissonjo-sudo

---

## Contribution

Issues et pull requests bienvenues sur GitHub.
