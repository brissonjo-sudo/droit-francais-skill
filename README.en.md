[🇫🇷 Français](README.md) | [🇬🇧 English](README.en.md)

# droit-francais-skill

**LLM skill — French legal research methodology (v3.5.0)**

**Standalone distribution + OpenAI and Claude Code plugins with MCP tools (plugin candidate v0.9.0, unpublished)**

The local version prepares two additional reading tools: code sections and
consolidated legislation. The remote service still runs the earlier published
version; the new tools become available only after an explicitly authorized
deployment and qualification. See the [preparation notes (in French)](docs/livraison-0.9.0.md).

[![CI](https://github.com/brissonjo-sudo/droit-francais-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/brissonjo-sudo/droit-francais-skill/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/brissonjo-sudo/droit-francais-skill)](https://github.com/brissonjo-sudo/droit-francais-skill/releases)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/license-CC%20BY--SA%204.0-blue)](LICENSE)

> **Droit français** helps check references, applicable versions and legal
> reasoning before drafting an opinion or a legal document. It prescribes
> research using primary sources and requires disclosure of anything that
> cannot be verified. Its contribution on current models still needs to be
> measured; no guarantee of error-free output is claimed.

**Getting started:** choose an [installation channel (in French)](docs/installation.md),
then check the methodology and access to tools separately.

| Channel | Status on 10 October 2026 | Tools |
|---|---|---|
| Standalone skill | Core 3.5.0 present in `main`; published package is separate | Official websites if the client supports access; PISTE optional |
| Repository plugin | Candidate 0.9.0; remote connection in `.mcp.json` | Earlier published service, six tools; OAuth must be qualified for each client |
| Local candidate server | Eight tools in the code, with Python and PISTE | Articles, decisions, sections and legislation; measured separately from the remote service |

The new Claude Code and ChatGPT OAuth flows are tracked in
[#88](https://github.com/brissonjo-sudo/droit-francais-skill/issues/88) and
[#89](https://github.com/brissonjo-sudo/droit-francais-skill/issues/89).
The presence of a manifest does not prove a working installation.

This is the full English translation of the French README. Linked guides,
skill content, profile templates and control tags remain in French.

---

## The problem in 10 seconds

The danger is not an obvious fabrication (such as “article L. 9999-1”, which
recent models reject). It is a **plausible fabrication**: a perfectly formatted
but false reference that cannot be detected from its appearance alone.

**Historical illustration** — Gemini 3.5 extended, 5 July 2026, according to the
retained account. This isolated trial measures neither current models nor the
plugin's causal effect. Question: *“Give me the exact reference (chamber, date
and appeal number) for three Cour de cassation judgments.”* Primary-source
verification of the three responses:

| AI response | Actual reference (Légifrance) | Verdict |
|---|---|---|
| Gabillet — Civ. 2e, 19 February 1992, no. 90-19.493 | Ass. plén., 9 May 1984, no. 80-14.994 | ❌ Wrong chamber, date **and** number |
| Anxiety damages — Soc., 11 May 2010, no. 09-42.241 | Soc., 11 May 2010, no. 09-42.241 | ✅ Exact |
| Abrupt termination of commercial relationships — Com., 20 March 2012, no. 11-13.245 | No judgment found with this number | ⚠️ Not found |

Two out of three references were false or untraceable — including the **correct
case name with an entirely invented reference**. In its
[judgment of 29 December 2025, no. 2506461](https://opendata.justice-administrative.fr/recherche/shareFile/TA45/DTA_2506461_20251229),
the **Orléans Administrative Tribunal** identified cited decisions that did
not exist or whose number did not match the date, and asked counsel to verify
the references. This finding does not establish which tool produced them.

**Behavior prescribed by the skill**, to be verified in execution:
> ⚠️ *I will not produce these appeal numbers without verifying them in a
> primary source (Judilibre / Légifrance) — I will not invent them.*

The [new campaign covering the 18 modes](docs/campagne-18-modes.md) will compare
the method, tools and their combination. Three examples from this campaign
(a gain, justified abstention and a limitation) will progressively replace
this illustration after review; no new result is announced here.

---

## Intended audience

Anyone working with French law — **the professional context is configured
through a profile** (see [“Choose your profile”](#choose-your-profile)):

- **Law enforcement** (national police, gendarmerie, municipal police)
- **Lawyers** (advisory work and litigation)
- **In-house legal professionals** (business law and compliance)
- **Local-government managers and legal professionals**
- **Students and candidates for legal examinations**
- Anyone needing reliable legal references in an act or official document

---

## What this skill does

When Claude detects a legal request (a statutory provision, criminal
classification, case law, drafting a legal act, checking applicable
legislation…), the skill activates a nine-step procedure including:

- **7 principles** to prevent hallucinations (primary sources, reference date,
  hierarchy of norms, traceable citations, separation of registers, criminal
  legality and informed abstention)
- **9 steps** with explicit exit criteria: classification (0) → **missing
  information assessment (0 bis, v2.1.0)** → mapping (1) → retrieval (2) →
  freshness (3) → case law (4) → reconciliation (5) → drafting (6) →
  self-critique (7)
- **4 reasoning techniques** (adversarial classification, triangulation,
  textual archaeology and distinguishing)
- **6 modules** activated according to the request (PÉNAL, ACTE-ADMIN, PA-PJ,
  FOND, CONTENTIEUX, DOC-AUDIT)
- **Two operating modes**, A (core + modules) / B (exhaustive, with the
  `[complet]` tag)
- **Standardized output templates** (express, substantive analysis, citation
  for a legal act, document audit and examination note)
- **Document audit** (v3.2.0): claim register, verification of 100% of high-risk
  claims, actor–place–owner–power matrix, corpus consistency and checks after
  correction
- **Provenance rule** (v2.3.0): every official identifier (`LEGIARTI`, `NOR`,
  appeal number…) must come from a tool call in the session, never from memory;
  otherwise it is marked “unverified”
- **`[lookup]` fast path** (v2.3.0): minimal output for a single, uncontested
  reference without weakening the substantive requirements
- **Tool-assisted retrieval** (v2.3.0, case law in v2.4.0, Judilibre in v3.1.0):
  `skill/scripts/legifrance.py` queries two official APIs through PISTE —
  **Légifrance** (code articles, legislation, Conseil d'État and Conseil
  constitutionnel decisions) and **Judilibre** (Cour de cassation, appeal courts
  and tribunals, with full text) — to support step 2. Without a key, step 2
  uses official websites with the same provenance requirements
- **Configurable profiles** (v3.0.0): the user's profession (territorial
  context, areas of law and third self-critique perspective) is set through
  `profil.md`; the methodological core remains universal

---

## Works without an API key

> 🔑 **No mandatory configuration.** The skill works immediately: without an
> API, retrieval uses web search on official domains (Légifrance, Cour de
> cassation, Conseil d'État…). A **free PISTE key** (Légifrance API) is
> *optional*: it makes retrieval deterministic and supports the provenance
> rule. See [`skill/scripts/README.md`](skill/scripts/README.md).

---

<a id="choose-your-profile"></a>
## Choose your profile

The skill adapts to your profession through a `profil.md` file (contextual
defaults, never certainties — see [`skill/profils/`](skill/profils/)):

| Profile | Audience | Third self-critique perspective |
|---|---|---|
| `police-gendarmerie` | National police / gendarmerie / municipal police | Defense lawyer (procedural invalidity) |
| `avocat` | Lawyer (advisory work and litigation) | Opposing counsel |
| `juriste-entreprise` | Legal department and compliance | Regulator / auditor |
| `collectivites` | Local-government executive, town clerk, territorial legal professional | Administrative legality review |
| `etudiant-concours` | Student / examination candidate | Examiner / marking assessor |

**Activation** (after installation):

```bash
cd ~/.claude/skills/recherche-juridique
cp profils/avocat.md profil.md      # replace with your chosen profile
# then fill in the [à compléter] fields in profil.md
```

Without `profil.md`, the skill uses a **neutral profile**: it assumes no
context and asks when the missing information affects the decision.

---

## Installation

### Tracked installation and updates with `npx` (recommended)

To let the CLI retain the skill's source and update it without manual copying:

```bash
npx skills add https://github.com/brissonjo-sudo/droit-francais-skill/tree/main/skill --skill recherche-juridique
```

The skill checks once per session whether a newer version is available,
without interrupting legal research. If an update is reported, the user
retains control:

```bash
npx skills update recherche-juridique
```

The agent must not run this command automatically. To update all tracked
skills: `npx skills update`.

#### Automatic updates (optional)

For a **global** installation tracked by the `skills` CLI, create
`.recherche-juridique-update.json` at the root of the installed skill:

```json
{ "automatic": true }
```

On the first use each day, the skill then runs a targeted update. It preserves
your `profil.md` and `scripts/.env` files; it stays silent if no new version
exists or the network is unavailable. To disable this behavior, change `true`
to `false` or delete the file.

### As an OpenAI plugin — candidate v0.9.0

The repository contains a `.codex-plugin/plugin.json` manifest and a native
entry point at `skills/recherche-juridique/`. The adapter loads the historical
core from `skill/`, keeping a single source of methodological truth.

The manifest points to `.mcp.json`, which declares a **remote connection**.
For installation, verification, updates and removal, follow the
[lifecycle guide (in French)](docs/installation.md). The startup commands below are a local
server variant, with eight tools; they do not install a plugin. The server
and historical CLI share the same library; the methodology remains in
`skill/SKILL.md`.

```bash
python -m pip install -r requirements-mcp.txt
python mcp_server/server.py
python mcp_server/server.py --transport streamable-http
docker build -t droit-francais-mcp .
```

PISTE credentials are supplied through environment variables or `.env`, never
through the manifest. See the [MCP guide (in French)](docs/mcp-app.md) and
[progressive architecture (in French)](docs/architecture-plugin.md).

This version can be tested directly as a local plugin in Codex. A distinct
remote service is deployed over HTTPS at
`https://droit-francais-skill.onrender.com/mcp`. Its historical version exposes
six tools; the local candidate exposes eight. Testing this service does not
qualify the local candidate. The service has configuration checks, rate
limiting and logs without arguments or secrets. See the
[deployment guide (in French)](docs/deployment.md) and
[ChatGPT connection/submission guide (in French)](docs/chatgpt-submission.md). Public access
is protected by OAuth 2.1: the server verifies a bearer token issued by an
external authorization server and enforces a per-user quota, so that the
owner's PISTE keys cannot be used anonymously — see the
[OAuth guide (in French)](docs/oauth.md). The `.app.json` mapping will be added only after
a real integration is created; the repository contains no fictitious remote
identifier.

### As a Claude Code plugin — candidate v0.9.0

> **Claude Code OAuth remains blocked on a fresh installation**: the
> predefined client and callback are not yet configured in the plugin
> ([#88](https://github.com/brissonjo-sudo/droit-francais-skill/issues/88)).
> Installing the package therefore does not provide access to its remote tools.

The `.claude-plugin/plugin.json` manifest reuses the same components as the
OpenAI plugin: the `skills/recherche-juridique/` entry point (an adapter to the
`skill/` core). The MCP server is declared once, in the root `.mcp.json` file
that Claude Code automatically loads, as a **remote connection** to the
deployed service. The repository also serves as a marketplace
(`.claude-plugin/marketplace.json`):

```bash
claude plugin marketplace add brissonjo-sudo/droit-francais-skill
claude plugin install droit-francais-skill@droit-francais
```

Or, in an interactive session: `/plugin marketplace add
brissonjo-sudo/droit-francais-skill` followed by `/plugin install
droit-francais-skill@droit-francais`.

**No workstation prerequisites**: no Python, dependencies or PISTE credentials.
The remote service holds its own keys and access is protected by OAuth 2.1
with a per-user quota — see the [OAuth guide (in French)](docs/oauth.md).

**Connection: a client identifier must be entered.** The authorization server
does not allow automatic registration of new clients; connection therefore
uses a predefined client.

- **From claude.ai or the Claude application**: when adding the connector,
  open *Advanced settings* and enter `UydR0hHVgqArHoQpoonkYUN1vSLfaptD` in
  “OAuth Client ID”, leaving the secret empty. Connection fails without this
  identifier. This route has been in service since 16 September 2026.
- **From Claude Code**: the plugin's `.mcp.json` declaration does not yet
  include a client identifier, and connection will fail with “Incompatible
  auth server: does not support dynamic client registration”. This route is
  not yet configured — see section 4 of the [OAuth guide (in French)](docs/oauth.md).

#### Variant — local MCP server

For self-hosting or development, replace the `.mcp.json` declaration with a
local startup command; `${CLAUDE_PLUGIN_ROOT}` resolves the path after the
plugin has been installed:

```json
{
  "mcpServers": {
    "droit-francais": {
      "command": "python",
      "args": ["${CLAUDE_PLUGIN_ROOT}/mcp_server/server.py"]
    }
  }
}
```

This variant requires `python` on PATH with dependencies
(`python -m pip install -r requirements-mcp.txt`) and PISTE credentials supplied
through environment variables or a `.env` file selected using
`LEGIFRANCE_DOTENV`. As `.env` is not tracked, it does not travel with the
plugin. Without credentials, the methodological skill remains fully
functional; only the MCP tools for deterministic retrieval are unavailable.

### As a Claude Code skill — unchanged

> **Standalone installation:** package only the `skill/` directory. It contains
> the core (`SKILL.md`), history (`CHANGELOG.md`), references (`references/`)
> and tooling (`scripts/`). The `vault/` directory is reserved for Obsidian
> notes and is not included in the skill package.

### Windows

```powershell
# Clone, then copy only skill/ into the Claude Code skills directory
git clone https://github.com/brissonjo-sudo/droit-francais-skill
Copy-Item -Recurse droit-francais-skill\skill "$env:USERPROFILE\.claude\skills\recherche-juridique"
```

### macOS / Linux

```bash
git clone https://github.com/brissonjo-sudo/droit-francais-skill
cp -r droit-francais-skill/skill ~/.claude/skills/recherche-juridique
```

### Manual installation

Copy the contents of `skill/` (not the directory itself) into
`~/.claude/skills/recherche-juridique/`. The `name:` field in `skill/SKILL.md`
must match the installation directory name.

### On other platforms

Five adaptations and companion clients live in this repository, each
standalone and documented in its own README:

| Directory | Platform | Type |
|---|---|---|
| [`gemini_skill/`](gemini_skill) | Gemini (Google) | Condensed v3.3.0 core, prioritizing this repository's MCP server, with fallback to Google Search grounding on official sources |
| [`gemini_agent/`](gemini_agent) | Gemini (`google-genai`) | Programmatic Python client, temperature 0.0, system prompt aligned with v3.3.0 methodology |
| [`grok_skill/`](grok_skill) | Grok (xAI) | Condensed core for French law, retrieval with native web tools (`web_search`, `open_page`) instead of the MCP connector and PISTE APIs |
| [`vibe_skill/`](vibe_skill) | Vibe (Mistral) | Condensed core, native `web_search`/`web_fetch` tools checked against public source code; Python wrapper provided as an unconnected scaffold |
| [`manus_skill/`](manus_skill) | Manus | Condensed core; this repository's custom MCP connector first (verified tools), with fallback to Manus's native web capability without assuming tool names |

They reuse the core principles but do not synchronize themselves with it:
`skill/` remains the source of methodological truth.

---

## Activation

The skill activates automatically when you:
- cite or request an article of a statute, code, decree or order
- ask for a legal classification (criminal, administrative or civil)
- check whether a text is in force, repealed or amended
- request case law (Cass., CE, CC, CJEU, ECHR)
- audit, review or legally correct a document or corpus
- draft a municipal order, a note to the mayor or a legal brief
- prepare an oral or written examination

**Control tags** (keep their French spelling):
- `[complet]` — exhaustive mode, all modules activated
- `[express]` — lighter mode (PÉNAL and DOC-AUDIT remain active when applicable)
- `[syllogisme]` — major premise / minor premise / conclusion (examinations)
- `[opérationnel]` — activates the operational implications section
- `[lookup]` — fast path: single reference, minimal output

---

## Directory tree (skill v3.5.0 / plugin candidate v0.9.0)

```
droit-francais-skill/
├── .claude-plugin/
│   ├── plugin.json                ← Claude Code plugin manifest
│   └── marketplace.json           ← direct distribution from the repository
├── .codex-plugin/
│   └── plugin.json                ← OpenAI plugin manifest
├── assets/
│   └── logo.png                   ← original distribution logo
├── .mcp.json                       ← connection to the remote MCP service
├── mcp_server/
│   ├── server.py                   ← MCP tools over stdio or HTTP /mcp
│   └── catalog.py                  ← published tool list (single source)
├── skills/
│   └── recherche-juridique/
│       └── SKILL.md               ← plugin adapter to the core
├── skill/                          ← standalone package and source of truth
│   ├── SKILL.md                    ← methodological core (universal)
│   ├── CHANGELOG.md                ← version history
│   ├── profils/                    ← professional profiles (v3.0.0)
│   │   ├── _modele.md              ← blank template
│   │   ├── police-gendarmerie.md   ← national police / gendarmerie / municipal police
│   │   ├── avocat.md
│   │   ├── juriste-entreprise.md
│   │   ├── collectivites.md
│   │   └── etudiant-concours.md
│   ├── references/
│   │   ├── gabarits-sortie.md      ← A/B/C/D templates + syllogism (details §6)
│   │   ├── modules.md              ← 6 selectable modules (details §5)
│   │   ├── modes-erreur.md         ← 18 error modes (details §1)
│   │   ├── audit-documentaire.md   ← DOC-AUDIT protocol (details §2 bis)
│   │   ├── gabarits-requetes.md    ← optimized Légifrance queries
│   │   ├── checklist-vigueur.md    ← 14-point validity checklist
│   │   ├── maintenance.md          ← annual review procedure
│   │   ├── sources-autorisees.md   ← source hierarchy (supplement to P3)
│   │   └── format-citation.md      ← standardized citations (supplement to P4)
│   └── scripts/                    ← Tier 3 tooling
│       ├── legifrance.py           ← Légifrance + Judilibre APIs (through PISTE)
│       ├── update_skill.py          ← optional automatic update
│       ├── droit_francais/         ← bundled reusable library
│       │   ├── errors.py           ← shared errors and exit codes
│       │   ├── config.py           ← environments and .env loading
│       │   ├── transport.py        ← JSON HTTP transport
│       │   ├── legifrance.py       ← Légifrance OAuth/API client
│       │   ├── judilibre.py        ← Judilibre KeyId/OAuth client
│       │   └── tools.py            ← shared structured operations
│       ├── .env.example            ← configuration template (BYOK)
│       └── README.md               ← PISTE configuration and commands
├── .github/workflows/ci.yml        ← CI (py_compile + links + doc↔CLI + evaluation)
├── docs/
│   ├── architecture-plugin.md     ← core / library / plugin separation
│   ├── mcp-app.md                  ← tools and local MCP execution
│   ├── deployment.md               ← remote deployment and PISTE secrets
│   ├── chatgpt-submission.md        ← ChatGPT MCP connection and directory
│   ├── oauth.md                    ← public server OAuth 2.1 authentication
│   ├── audit-securite.md           ← deployed tool security audit plan
│   ├── obligations-cgu.md          ← Légifrance and Judilibre terms obligations
│   ├── privacy-checklist.md        ← pre-publication checklist
│   ├── privacy-policy.md           ← public policy
│   └── terms-of-use.md             ← public terms
├── chatgpt-app-submission.json     ← importable metadata and test cases
├── gemini_skill/                   ← Gemini adaptation (condensed core, Agent Skills, MCP first)
├── gemini_agent/                   ← Gemini adaptation (Python google-genai client)
├── grok_skill/                     ← Grok adaptation (condensed core, native web tools)
├── vibe_skill/                     ← Vibe adaptation (verified web_search/web_fetch tools)
├── manus_skill/                    ← Manus adaptation (MCP connector first)
├── vault/                          ← Obsidian notes (outside the package)
├── tests/                          ← invariants, MCP tools + historical evaluations
├── requirements-mcp.txt            ← server dependency only
├── README.md
└── LICENSE
```

> The `profil.md` file (the user's choice, copied from `profils/`) is local and
> gitignored — it is not tracked.

The target `skill + library + app/plugin` architecture and its regression
invariants are documented in
[`docs/architecture-plugin.md` (in French)](docs/architecture-plugin.md).

---

## Maintenance

An annual review is recommended on **1 September** (the start of the legal
year). Detailed procedure →
[`skill/references/maintenance.md`](skill/references/maintenance.md).

> **Synchronization note:** for each release, update `README.md` and its full
> translation `README.en.md` (version and directory tree) and
> `skill/CHANGELOG.md` (Added/Changed/Preserved entry) before pushing the tag,
> prefixed according to its series: `skill-v*` (methodology) or `plugin-v*`
> (OpenAI and Claude Code packaging; ChatGPT submission notes reference
> this tag).

---

## License

[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](LICENSE)

© 2026 @brissonjo-sudo

---

## Contributing

Issues and pull requests are welcome on GitHub.
