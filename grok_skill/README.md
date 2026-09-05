# Skill juridique — déclinaison Grok

Déclinaison **Grok** (xAI) de la méthodologie de recherche juridique portée par
ce dépôt. Contrairement à l'agent Gemini ([`gemini_agent/`](../gemini_agent)),
générique et non connecté, cette déclinaison reste **spécifique au droit
français** et conserve les principes du noyau : elle n'en change que la voie de
récupération.

## Ce qui la distingue du noyau

Le noyau ([`skill/`](../skill)) suppose une voie outillée : connecteur MCP
Légifrance/Judilibre, sinon `scripts/legifrance.py` sur les API PISTE. Grok n'a
ni l'un ni l'autre. Cette déclinaison **remplace cette échelle** par les outils
natifs de la plateforme :

| Noyau (`skill/`) | Déclinaison Grok |
|---|---|
| Connecteur MCP Légifrance/Judilibre | `web_search` restreint à `site:legifrance.gouv.fr` |
| `scripts/legifrance.py` (API PISTE) | `open_page` / `open_page_with_find` sur les URL Légifrance |
| Repli `web_search` / `web_fetch` | `browser_tab` quand une interaction est nécessaire |

**L'invariant de provenance ne change pas** : la voie empruntée ne modifie en
rien l'exigence d'un identifiant officiel, d'une URL canonique et d'une date de
version. Une source inaccessible conduit à l'abstention (P7), jamais à une
citation reconstituée.

## Ce qu'elle conserve

- les sept principes invariants **P1 à P7**, dont la formulation v3.3.0 de P3
  qui distingue ordre de recherche, authenticité de la source, rang de la norme
  et effet d'une décision sur l'application ;
- la distinction entre **provenance officielle** et **applicabilité à la date
  évaluée** (`version_start_date`, `version_end_date`,
  `applicable_at_as_of_date`) — une source officielle peut être historique ;
- la **traçabilité proportionnée** : les contrôles restent obligatoires, leur
  affichage suit le livrable ; une réponse simple ne récite pas les étapes ;
- la **triangulation ciblée** sur les interprétations discutables : l'absence
  de jurisprudence localisable ne rend pas incertain un texte clair ;
- les **six modules activables** et la règle conservatrice de déclenchement.

## Ce qu'elle laisse de côté

La condensation est assumée : le noyau tient en une dizaine de fichiers, cette
déclinaison en trois. Ne sont pas repris ici les profils métier, les gabarits
de sortie détaillés, la checklist de vigueur en quatorze points, les gabarits
de requêtes Légifrance ni le détail des dix-huit modes d'erreur. Pour ces
éléments, le noyau reste la source de vérité :
[`skill/SKILL.md`](../skill/SKILL.md) et [`skill/references/`](../skill/references).

## Arborescence

```
grok_skill/
├── SKILL.md                      ← noyau condensé, adapté aux outils Grok
├── references/
│   ├── sources-autorisees.md     ← ordre de recherche et autorité (P3)
│   └── modules.md                ← six modules activables, détail
└── README.md                     ← ce document
```

## Installation

Ce paquet est autonome : il ne lit aucun fichier du reste du dépôt à
l'exécution. Le charger dans Grok comme n'importe quel jeu d'instructions
personnalisées, en conservant l'arborescence — `SKILL.md` renvoie à
`references/` en chemins relatifs.

## Versionnement

Le frontmatter porte `version: 3.3.0-grok`. Le suffixe marque la déclinaison ;
le numéro suit la version du noyau dont elle reprend la méthodologie. Une
évolution du noyau qui touche les principes ou l'échelle de récupération
appelle une reprise ici — les deux ne se synchronisent pas d'eux-mêmes.
