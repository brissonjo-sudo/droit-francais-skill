# droit-francais-skill

**Skill LLM — méthodologie de recherche en droit français (v3.2.0)**

**Distribution autonome + plugin OpenAI avec outils MCP (plugin v0.5.0)**

[![CI](https://github.com/brissonjo-sudo/droit-francais-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/brissonjo-sudo/droit-francais-skill/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/brissonjo-sudo/droit-francais-skill)](https://github.com/brissonjo-sudo/droit-francais-skill/releases)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/license-CC%20BY--SA%204.0-blue)](LICENSE)

> **TL;DR (EN).** An LLM skill that stops the model from *making up
> French law.* It forces every statute, case, or citation through a 9-step
> verification procedure built against **18 known LLM failure modes** in legal
> reasoning — primary sources only (Légifrance/PISTE), currency checks, and
> *traceable* citations. When it can't verify, it says so instead of inventing.
> Configurable per practitioner via a **profile**. Works without any API key;
> a free PISTE key unlocks deterministic retrieval. It remains installable as
> a standalone Claude Code skill and is now packaged as an OpenAI plugin
> foundation without duplicating the legal methodology.

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
- **6 modules activables** selon la requête (PÉNAL, ACTE-ADMIN, PA-PJ,
  FOND, CONTENTIEUX, DOC-AUDIT)
- **Double mode opératoire** A (noyau + modules) / B (exhaustif avec
  balise `[complet]`)
- **Gabarits de sortie** normalisés (express, fond, citation pour acte,
  audit documentaire, note de concours)
- **Audit documentaire** (v3.2.0) : registre des affirmations, vérification
  de 100 % du risque élevé, matrice acteur–lieu–propriétaire–pouvoir,
  cohérence d'un corpus et contrôle post-correction
- **Règle de provenance** (v2.3.0) : tout identifiant officiel
  (`LEGIARTI`, `NOR`, n° de pourvoi…) doit provenir d'un appel d'outil
  de la session, jamais de la mémoire — sinon marqué « non vérifié »
- **Voie rapide `[lookup]`** (v2.3.0) : sortie minimale pour une
  référence ponctuelle non controversée, sans dégrader le fond
- **Récupération outillée** (v2.3.0, jurisprudence en v2.4.0, Judilibre en
  v3.1.0) : `skill/scripts/legifrance.py` interroge deux API officielles via
  PISTE — **Légifrance** (articles de code, textes, décisions CE et CC) et
  **Judilibre** (Cour de cassation, cours d'appel, tribunaux, avec texte
  intégral) — pour fiabiliser l'étape 2. Sans clé, l'étape 2 bascule sur la
  voie web sans rien perdre en exigence de provenance
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

### Comme plugin OpenAI — outils MCP locaux v0.5.0

Le dépôt contient désormais un manifeste `.codex-plugin/plugin.json` et un
point d'entrée natif `skills/recherche-juridique/`. L'adaptateur charge le
noyau historique depuis `skill/` : il n'existe donc qu'une seule source de
vérité méthodologique.

Le plugin déclare maintenant un serveur MCP local, sans interface graphique.
Il expose les outils standard `search` et `fetch`, ainsi que quatre opérations
juridiques spécialisées pour rechercher et lire articles et décisions. Le
serveur appelle la même bibliothèque que le CLI historique ; la méthode et les
règles de provenance restent dans l'unique noyau `skill/SKILL.md`.

```bash
python -m pip install -r requirements-mcp.txt
python mcp_server/server.py
python mcp_server/server.py --transport streamable-http
docker build -t droit-francais-mcp .
```

Les identifiants PISTE restent fournis par variables d'environnement ou `.env`,
jamais dans le manifeste. Voir le [guide MCP](docs/mcp-app.md) et
l'[architecture progressive](docs/architecture-plugin.md).

Cette version est directement testable comme plugin local dans Codex. Le même
serveur est déployé en HTTPS à l'adresse
`https://droit-francais-skill.onrender.com/mcp`, avec contrôle de configuration,
limitation de charge et journaux sans arguments ni secrets. Voir le
[guide de déploiement](docs/deployment.md) et le
[guide de connexion/soumission ChatGPT](docs/chatgpt-submission.md). L'accès
public est protégé par OAuth 2.1 : le serveur vérifie un jeton porteur émis par
un serveur d'autorisation externe et applique un quota par utilisateur, afin
que les clés PISTE du titulaire ne soient jamais consommées anonymement — voir
le [guide OAuth](docs/oauth.md). Le mapping
`.app.json` ne sera ajouté qu'après création d'une intégration réelle ; aucun
identifiant distant fictif n'est placé dans le dépôt.

### Comme skill Claude Code — inchangé

> **Installation autonome :** empaqueter uniquement le dossier `skill/` — il contient le
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
- auditez, relisez ou corrigez juridiquement un document ou un corpus
- rédigez un arrêté municipal, une note au Maire, un mémoire
- préparez un oral ou écrit de concours

**Balises de contrôle :**
- `[complet]` — mode exhaustif, tous modules activés
- `[express]` — mode allégé (PÉNAL et DOC-AUDIT restent actifs lorsqu'applicables)
- `[syllogisme]` — structure majeure / mineure / conclusion (concours)
- `[opérationnel]` — section implications opérationnelles activée
- `[lookup]` — voie rapide : référence ponctuelle, sortie minimale

---

## Arborescence (skill v3.2.0 / plugin v0.5.0)

```
droit-francais-skill/
├── .codex-plugin/
│   └── plugin.json                ← manifeste du plugin
├── assets/
│   └── logo.png                   ← logo original de distribution
├── .mcp.json                       ← lancement local du serveur MCP
├── mcp_server/
│   ├── server.py                   ← outils MCP stdio ou HTTP /mcp
│   └── catalog.py                  ← liste des outils publiés (source unique)
├── skills/
│   └── recherche-juridique/
│       └── SKILL.md               ← adaptateur plugin vers le noyau
├── skill/                          ← paquet autonome et source de vérité
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
│   │   ├── gabarits-sortie.md      ← gabarits A/B/C/D + syllogisme (détail §6)
│   │   ├── modules.md              ← 6 modules activables (détail §5)
│   │   ├── modes-erreur.md         ← détail des 18 modes d'erreur (détail §1)
│   │   ├── audit-documentaire.md   ← protocole DOC-AUDIT (détail §2 bis)
│   │   ├── gabarits-requetes.md    ← requêtes Légifrance optimisées
│   │   ├── checklist-vigueur.md    ← checklist 14 points vérification
│   │   ├── maintenance.md          ← procédure de revue annuelle
│   │   ├── sources-autorisees.md   ← hiérarchie des sources (complément P3)
│   │   └── format-citation.md      ← formats de citation normalisés (complément P4)
│   └── scripts/                    ← outillage Palier 3
│       ├── legifrance.py           ← API Légifrance + Judilibre (via PISTE)
│       ├── droit_francais/         ← bibliothèque réutilisable embarquée
│       │   ├── errors.py           ← erreurs et codes de sortie communs
│       │   ├── config.py           ← environnements et chargement .env
│       │   ├── transport.py        ← transport HTTP JSON
│       │   ├── legifrance.py       ← client OAuth/API Légifrance
│       │   ├── judilibre.py        ← client KeyId/OAuth Judilibre
│       │   └── tools.py            ← opérations structurées partagées
│       ├── .env.example            ← gabarit de configuration (BYOK)
│       └── README.md               ← configuration PISTE + usage
├── .github/workflows/ci.yml        ← CI (py_compile + liens + doc↔CLI + éval)
├── docs/
│   ├── architecture-plugin.md      ← audit, cible et étapes de migration
│   ├── mcp-app.md                  ← configuration et contrat des outils
│   ├── deployment.md               ← exploitation de l'endpoint Render
│   ├── chatgpt-submission.md       ← connexion et soumission OpenAI
│   ├── oauth.md                    ← authentification OAuth 2.1 du serveur
│   ├── audit-securite.md           ← plan d'audit sécurité de l'outil déployé
│   ├── obligations-cgu.md          ← obligations CGU Légifrance et Judilibre
│   ├── privacy-checklist.md        ← checklist avant publication
│   ├── privacy-policy.md           ← politique publique
│   └── terms-of-use.md             ← conditions publiques
├── chatgpt-app-submission.json     ← métadonnées et cas de test importables
├── vault/                          ← notes Obsidian (hors paquet)
├── tests/                          ← invariants, outils MCP + évals historiques
├── requirements-mcp.txt            ← dépendance du serveur uniquement
├── README.md
└── LICENSE
```

> Le fichier `profil.md` (choix de l'utilisateur, copié depuis `profils/`)
> est local et gitignoré — il n'est pas versionné.

Le détail de l'architecture cible `skill + bibliothèque + app/plugin` et de ses
invariants de non-régression est documenté dans
[`docs/architecture-plugin.md`](docs/architecture-plugin.md).

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
