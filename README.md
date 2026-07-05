# droit-francais-skill

**Skill LLM — méthodologie de recherche en droit français (v3.0.0)**

[![CI](https://github.com/brissonjo-sudo/droit-francais-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/brissonjo-sudo/droit-francais-skill/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/brissonjo-sudo/droit-francais-skill)](https://github.com/brissonjo-sudo/droit-francais-skill/releases)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/license-CC%20BY--SA%204.0-blue)](LICENSE)

> **TL;DR (EN).** A Claude Code skill that stops the model from *making up
> French law.* It forces every statute, case, or citation through a 9-step
> verification procedure built against **14 known LLM failure modes** in legal
> reasoning — primary sources only (Légifrance/PISTE), currency checks, and
> *traceable* citations. When it can't verify, it says so instead of inventing.
> Configurable per practitioner via a **profile**. Works without any API key;
> a free PISTE key unlocks deterministic retrieval. Install: copy `skill/`
> into `~/.claude/skills/recherche-juridique/`.

---

## Le problème, en 10 secondes

Le danger n'est pas le mensonge évident (un « article L. 9999-1 » que tout
modèle récent rejette). C'est le **mensonge plausible** : une référence
parfaitement formatée, mais fausse — impossible à repérer à l'œil.

**Test réel** — Gemini 3.5 extended, 5 juillet 2026. Question : *« Donne-moi
la référence exacte (chambre, date, n° de pourvoi) de trois arrêts de la Cour
de cassation. »* Vérification en source primaire des trois réponses :

| Réponse de l'IA | Réalité (Légifrance) | Verdict |
|---|---|---|
| Gabillet — Civ. 2e, 19 févr. 1992, n° 90-19.493 | Ass. plén., 9 mai 1984, n° 80-14.994 | ❌ Chambre, date **et** n° faux |
| Anxiété — Soc., 11 mai 2010, n° 09-42.241 | Soc., 11 mai 2010, n° 09-42.241 | ✅ Exact |
| Rupture brutale — Com., 20 mars 2012, n° 11-13.245 | Aucun arrêt à ce n° | ⚠️ Introuvable |

Deux références sur trois fausses ou fantômes — dont le **bon nom d'arrêt
avec une référence entièrement inventée**. C'est exactement ce qui a valu à
un avocat une mise en garde du **TA d'Orléans** (29 déc. 2025 : « une
quinzaine de références entièrement fausses »).

**Avec le skill**, la même question déclenche la *règle de provenance* :
> ⚠️ *Je ne produis pas ces numéros de pourvoi sans les avoir vérifiés en
> source primaire (Judilibre / Légifrance) — je ne les invente pas.*

C'est toute la promesse : **la rigueur d'un juriste, pas la fluidité d'un
perroquet.** (→ [l'histoire complète](docs/article.md))

---

## Public visé

Tout praticien du droit français — **le métier se configure via un profil**
(voir [« Choisir son profil »](#choisir-son-profil)) :

- **Forces de l'ordre** (police nationale, gendarmerie, police municipale)
- **Avocats** (conseil et contentieux)
- **Juristes d'entreprise** (droit des affaires, conformité)
- **Cadres et juristes territoriaux** (collectivités)
- **Étudiants et candidats aux concours** juridiques
- Toute personne ayant besoin de références juridiques fiables dans un acte
  ou un document officiel

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
- **Profils configurables** (v3.0.0) : le métier de l'utilisateur (contexte
  territorial, domaines, 3ᵉ regard d'auto-critique) se règle via un `profil.md`
  — le noyau méthodologique reste universel

---

## Fonctionne sans clé API

> 🔑 **Aucune configuration obligatoire.** Le skill fonctionne immédiatement :
> à défaut d'API, la récupération passe par la recherche web sur les domaines
> officiels (Légifrance, Cour de cassation, Conseil d'État…). Une **clé PISTE
> gratuite** (API Légifrance) est *optionnelle* : elle rend la récupération
> déterministe et fiabilise la règle de provenance. Voir
> [`skill/scripts/README.md`](skill/scripts/README.md).

---

<a id="choisir-son-profil"></a>
## Choisir son profil

Le skill s'adapte à votre métier via un fichier `profil.md` (défauts de
contexte, jamais des certitudes — voir [`skill/profils/`](skill/profils/)) :

| Profil | Pour qui | 3ᵉ regard d'auto-critique |
|--------|----------|---------------------------|
| `police-gendarmerie` | Police nationale / gendarmerie / police municipale | L'avocat de la défense (nullité de procédure) |
| `avocat` | Avocat (conseil, contentieux) | Le confrère adverse |
| `juriste-entreprise` | Direction juridique, conformité | Le régulateur / l'auditeur |
| `collectivites` | DGS, secrétaire de mairie, juriste territorial | Le contrôle de légalité préfectoral |
| `etudiant-concours` | Étudiant / candidat concours | Le jury / le correcteur |

**Activation** (après installation) :

```bash
cd ~/.claude/skills/recherche-juridique
cp profils/avocat.md profil.md      # remplacer par votre profil
# puis compléter les champs [à compléter] du profil.md
```

Sans `profil.md`, le skill tourne en **profil neutre** : il ne présume aucun
contexte et pose la question quand elle devient décisionnelle.

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

## Arborescence (v3.0.0)

```
droit-francais-skill/
├── skill/                          ← seul dossier empaqueté pour installation
│   ├── SKILL.md                    ← noyau méthodologique (universel)
│   ├── CHANGELOG.md                ← historique des versions
│   ├── profils/                    ← profils métier (v3.0.0)
│   │   ├── _modele.md              ← gabarit vierge
│   │   ├── police-gendarmerie.md   ← PN / gendarmerie / police municipale
│   │   ├── avocat.md
│   │   ├── juriste-entreprise.md
│   │   ├── collectivites.md
│   │   └── etudiant-concours.md
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
├── tests/                          ← évals (14 modes + balises + profil neutre) + runners
├── README.md
└── LICENSE
```

> Le fichier `profil.md` (choix de l'utilisateur, copié depuis `profils/`)
> est local et gitignoré — il n'est pas versionné.

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
