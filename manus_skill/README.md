# Skill juridique — déclinaison Manus

Déclinaison **Manus** de la méthodologie de recherche juridique portée par ce
dépôt. Contrairement à Grok et Vibe, qui n'ont accès qu'à leur propre capacité
web native, Manus accepte des **serveurs MCP personnalisés** — ce qui permet
de connecter directement le serveur MCP de ce dépôt, avec des outils dont le
nom et le comportement sont vérifiés dans le code source, plutôt que devinés.

## Ce qui la distingue du noyau

Le noyau ([`skill/`](../skill)) suppose une voie outillée : connecteur MCP en
priorité, sinon `scripts/legifrance.py` sur les API PISTE. Manus n'a pas accès
à `scripts/legifrance.py` (scripts Python locaux du dépôt), mais **peut**
avoir accès au connecteur MCP :

| Noyau (`skill/`) | Déclinaison Manus |
|---|---|
| Connecteur MCP Légifrance/Judilibre | **Identique** — serveur MCP personnalisé (Settings → Integrations → Custom MCP Servers) |
| `scripts/legifrance.py` (API PISTE) | Non disponible ; sans objet si le connecteur MCP est utilisé |
| Repli `web_search` / `web_fetch` | Capacité web native de Manus, nom d'outil non supposé (voir plus bas) |

## Deux voies de récupération, dans cet ordre

**1. Connecteur MCP dédié (priorité).** Le serveur de ce dépôt
([`mcp_server/`](../mcp_server)) expose six outils, dont les noms et
paramètres exacts sont vérifiés dans
[`mcp_server/server.py`](../mcp_server/server.py) :

| Outil | Paramètres | Usage |
|---|---|---|
| `search` | `query` | Routeur générique (article si la requête en contient un, jurisprudence sinon) |
| `fetch` | `id` (un identifiant renvoyé par `search`, pas une URL) | Lecture du résultat désigné |
| `search_articles` | `number`, `code`, `date` | Recherche d'article ciblée |
| `get_article` | `id`, `date` | Lecture par identifiant `LEGIARTI`, évalue `applicable_at_as_of_date` |
| `search_case_law` | `query`, `jurisdiction`, `date_start`, `date_end` | Recherche de jurisprudence |
| `get_decision` | `id` | Lecture d'une décision |

C'est la voie qui donne les garanties les plus fortes : provenance officielle,
distinction entre authenticité de la source et applicabilité à la date
évaluée (v3.3.0), datation explicite.

**2. Capacité web native de Manus (repli), si aucun connecteur MCP n'est
disponible.** Manus ne publie pas le nom exact de cet outil dans sa
documentation publique — contrairement au registre ouvert de Vibe Code, où le
nom des outils a pu être vérifié dans le code source. Le skill n'en suppose
donc aucun : il demande de constater les outils réellement proposés dans la
session en cours plutôt que d'en deviner le nom. C'est la leçon retenue d'une
déclinaison Vibe antérieure, poussée avec des noms d'outils qui n'existaient
pas — voir `skill/CHANGELOG.md`.

**3. Abstention** si aucune des deux voies n'aboutit.

## Installation

Manus installe un skill par upload direct — pas de dossier `.vibe/skills/`
ni d'emplacement fixe à respecter :

1. Récupérer ce dossier `manus_skill/` (avec `SKILL.md` et `references/`),
   par exemple en le compressant en `.zip`.
2. Dans Manus : onglet **Skills** (menu de gauche) → **+ Add** → **Upload a
   skill** → sélectionner le `.zip`, le `.skill` ou le dossier.
3. Le skill apparaît dans la liste accessible en tapant `/` dans le chat.

Pour la voie prioritaire (connecteur MCP), connecter séparément le serveur de
ce dépôt : **Settings → Integrations → Custom MCP Servers**, en pointant vers
une instance auto-hébergée (`python mcp_server/server.py --transport
streamable-http`, voir [`docs/mcp-app.md`](../docs/mcp-app.md)) ou vers
l'instance déployée documentée dans
[`docs/deployment.md`](../docs/deployment.md). Cette dernière exige une
authentification OAuth 2.1 ([`docs/oauth.md`](../docs/oauth.md),
[`docs/validation-chatgpt.md`](../docs/validation-chatgpt.md) pour l'obtention
d'un jeton) — vérifier que la configuration des connecteurs personnalisés de
Manus prend en charge un jeton porteur avant de s'y fier ; ce point n'est pas
confirmé par la documentation publique de Manus au moment de l'écriture.

## Ce qui est repris du noyau

Les 7 principes invariants, la traçabilité proportionnée, la distinction
provenance officielle / applicabilité temporelle, la triangulation ciblée sur
les interprétations discutables, les six modules activables — fidèle à la
3.3.0.

## Arborescence

```
manus_skill/
├── SKILL.md                      ← noyau condensé, échelle de récupération à deux voies
├── references/
│   ├── sources-autorisees.md     ← ordre de recherche et autorité (P3)
│   └── modules.md                ← six modules activables, détail
└── README.md                     ← ce document
```

## Versionnement

Le frontmatter porte `version: 3.3.0-manus` et `base_version: 3.3.0`. Une
évolution du noyau qui touche les principes ou l'échelle de récupération
appelle une reprise ici — les deux ne se synchronisent pas d'eux-mêmes.
