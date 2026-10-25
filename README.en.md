[🇫🇷 Français](README.md) | [🇬🇧 English](README.en.md)

<p align="center"><img src="assets/banner.svg" width="800" alt="Line drawing: a municipal police officer, a French lawyer in her gown with six fireflies in the colours of Claude, ChatGPT, Gemini, Mistral, Grok and Perplexity circling her head, and a law student revising at his desk, next to a courthouse flying the French flag. Six fireflies, one single source: Légifrance."></p>

# Droit français: verified French legal research

**Check every French legal reference against Légifrance and Judilibre before writing it.**

[![CI](https://github.com/brissonjo-sudo/droit-francais-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/brissonjo-sudo/droit-francais-skill/actions/workflows/ci.yml)
[![Skill](https://img.shields.io/github/v/tag/brissonjo-sudo/droit-francais-skill?filter=skill-v*&label=skill)](https://github.com/brissonjo-sudo/droit-francais-skill/releases)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/license-CC%20BY--SA%204.0-blue)](LICENSE)

AI assistants readily cite articles that do not exist, misnumbered rulings or
repealed versions. This skill makes the assistant (Claude, ChatGPT, Codex,
Gemini…) follow a research method based on official sources: every reference
comes from a lookup made during the session, with its applicability date, and
anything that could not be verified is flagged as such.

> A research aid, not legal advice. Only the signed publications of the
> Journal officiel are authoritative; no guarantee of error-free output is made.

## Example

Question: *"What are the mayor's general police powers?"*

The skill cites the article only after retrieving it. Actual connector result
on 25/10/2026, formatted:

```text
Article L2212-2 — Code général des collectivités territoriales
Identifier     : LEGIARTI000029946370
Status         : in force, version of 22/12/2014
Applicable on  : 25/10/2026 — yes
Source         : Légifrance API, retrieved on 25/10/2026
Link           : https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000029946370
```

When no source confirms a reference, the answer says so instead of filling it
in from memory:

> ⚠️ *I will not provide these appeal numbers without checking them in a
> primary source (Judilibre / Légifrance) — I do not make them up.*

## Why

The danger comes from plausible references: well formatted, yet false. Any
recent model rejects the absurd ones. In an isolated test on 5 July 2026,
Gemini 3.5 extended answered a request for three Cour de cassation rulings as
follows:

| AI answer | Reality (Légifrance) | Verdict |
|---|---|---|
| Gabillet — Civ. 2e, 19 févr. 1992, n° 90-19.493 | Ass. plén., 9 mai 1984, n° 80-14.994 | ❌ Chamber, date **and** number wrong |
| Anxiété — Soc., 11 mai 2010, n° 09-42.241 | Soc., 11 mai 2010, n° 09-42.241 | ✅ Correct |
| Rupture brutale — Com., 20 mars 2012, n° 11-13.245 | No ruling with this number | ⚠️ Not found |

The Orléans Administrative Court, in its
[judgment of 29/12/2025, no. 2506461](https://opendata.justice-administrative.fr/recherche/shareFile/TA45/DTA_2506461_20251229),
notes cited decisions that do not exist and asks counsel to check their
references. Neither case measures the effect of this skill: see
[Measuring quality](#measuring-quality).

## Quick start

### In claude.ai or the Claude app (tools included)

1. Add a custom connector at
   `https://droit-francais-skill.onrender.com/mcp`.
2. In its *Advanced settings*, enter `UydR0hHVgqArHoQpoonkYUN1vSLfaptD`
   as the "OAuth Client ID" and leave the secret empty.
3. Sign in, then ask a legal question.

Nothing to install: the service holds its own official keys, with a per-user
quota. Details and troubleshooting: [OAuth guide (in French)](docs/oauth.md).

### In Claude Code (the method)

```bash
npx skills add https://github.com/brissonjo-sudo/droit-francais-skill/tree/main/skill --skill recherche-juridique
```

No key is required: without the API, research goes through the official
websites (Légifrance, Cour de cassation, Conseil d'État…). A free PISTE
key makes retrieval deterministic: see
[PISTE configuration (in French)](skill/scripts/README.md).

### Other installations

Claude Code or Codex plugin, local MCP server, manual copy, automatic updates:
see the [installation guide (in French)](docs/installation.md).

Adaptations for other assistants, each documented in its own folder:

| Assistant | Folder |
|---|---|
| Gemini (Google) | [`gemini_skill/`](gemini_skill) and [`gemini_agent/`](gemini_agent) |
| Grok (xAI) | [`grok_skill/`](grok_skill) |
| Vibe (Mistral) | [`vibe_skill/`](vibe_skill) |
| Manus | [`manus_skill/`](manus_skill) |

`skill/` remains the single source of truth: the adaptations do not sync with
it on their own.

## What you get

- Every official identifier (article, NOR, appeal number…) comes from a
  lookup in the session, never from memory; otherwise it is marked
  "unverified".
- Each text is cited in the version applicable on the date of the facts, with
  its force of law and its history.
- Case law covers the Cour de cassation and the ordinary courts (Judilibre),
  the Conseil d'État and the administrative courts of appeal, the Conseil
  constitutionnel and the financial courts.
- The reasoning goes through legal classification and how norms fit together,
  then an adversarial self-review before answering.
- The skill reviews a single act or a set of acts and flags outdated
  references and inconsistencies.
- The output fits the need: quick answer, in-depth note, citation for an act,
  exam-style note.

## Choose a profile

The skill adapts to your profession through a `profil.md` file. Each profile
adds a critical perspective specific to that profession:

| Profile | For | Added critical perspective |
|--------|----------|------------------------|
| `collectivites` | Local authority directors, town clerks, local government lawyers | The prefect's legality review |
| `avocat` | Lawyers (advisory, litigation) | Opposing counsel |
| `juriste-entreprise` | Legal department, compliance | The regulator or auditor |
| `police-gendarmerie` | National police, gendarmerie, municipal police | Defence counsel (procedural nullities) |
| `etudiant-concours` | Students, civil service exam candidates | The examiner |

Activation, after installation:

```bash
cd ~/.claude/skills/recherche-juridique
cp profils/avocat.md profil.md      # replace with your profile
# then fill in the [à compléter] fields of profil.md
```

Without `profil.md`, the skill assumes no context and asks the question when
it matters.

## Usage

The skill activates on its own when you cite or request a legal text, a legal
classification, case law, whether a text is in force, the drafting of an act
or the legal review of a document. Tags adjust the answer:

| Tag | Effect |
|---|---|
| `[lookup]` | Single reference, minimal answer |
| `[express]` | Lighter answer |
| `[complet]` | Exhaustive analysis |
| `[syllogisme]` | Major premise, minor premise, conclusion (exams) |
| `[opérationnel]` | Detailed practical consequences |

## FAQ

**Is it free?** The skill is open (CC BY-SA 4.0) and the PISTE key is free.
The hosted service is open after sign-in, with a per-user quota.

**Do I need an API key?** No. The PISTE key is optional; without it, research
goes through the official websites.

**Where do my questions go?** See the [privacy policy](docs/privacy-policy.md).

**Who is liable for an error?** Users remain responsible for what they write.
Official data are not legally binding; only the signed publications of the
Journal officiel are authoritative. See the [terms of use](docs/terms-of-use.md).

## Project status

| Component | Status on 25 October 2026 | Detail |
|---|---|---|
| Skill | 3.6.0, published (tag `skill-v3.6.0`) | Stable method, can be installed on its own |
| Hosted service | Twelve tools exposed to the Claude connector | OAuth sign-in verified in claude.ai |
| Claude Code and Codex plugins | Candidate 0.9.0, unpublished | Claude Code and ChatGPT OAuth in progress ([#88](https://github.com/brissonjo-sudo/droit-francais-skill/issues/88), [#89](https://github.com/brissonjo-sudo/droit-francais-skill/issues/89)) |

## Measuring quality

The [18 failure modes campaign (in French)](docs/campagne-18-modes.md) compares
three settings: the model alone, the method alone, and the method with its
tools. It checks that every cited identifier really comes from a tool call. No
figures have been published yet. The protocol is described in
[`tests/README.md`](tests/README.md).

## Further reading

All linked guides are in French.

- [Repository tree and maintenance](docs/arborescence.md)
- [Skill, library and plugin architecture](docs/architecture-plugin.md)
- [MCP tools and their contract](docs/mcp-app.md)
- [Service deployment](docs/deployment.md)
- [Légifrance and Judilibre terms of use obligations](docs/obligations-cgu.md)
- [Version history](skill/CHANGELOG.md)

## License and contributing

[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](LICENSE).
© 2026 @brissonjo-sudo.

Questions, errors, suggestions: open an
[issue](https://github.com/brissonjo-sudo/droit-francais-skill/issues).
