# Skill juridique — déclinaison Manus

Déclinaison Manus de la méthodologie de recherche juridique du dépôt, actualisée sur la base 3.5.0. Elle conserve les garde-fous de provenance et d'applicabilité du portage Manus, sans supposer la présence d'un connecteur ou d'un outil qui ne serait pas exposé dans la session.

## Échelle de récupération en trois voies

**1. Connecteur MCP du dépôt, s'il est exposé dans la session.** Le serveur MCP de ce dépôt expose six outils, dont les noms et paramètres sont définis dans `mcp_server/server.py` : `search(query)`, `fetch(id)` — l'identifiant renvoyé par `search`, et non une URL —, `search_articles(number, code, date)`, `get_article(id, date)`, `search_case_law(query, jurisdiction, date_start, date_end)` et `get_decision(id)`. Lorsqu'un numéro d'article est identifié, préférer `search_articles` → `get_article` à `search` → `fetch`.

**2. Capacité web native de Manus.** Si le connecteur dédié n'est pas disponible, constater les outils effectivement proposés dans la session sans en supposer le nom ni les paramètres. Restreindre la recherche aux sources officielles de [`references/sources-autorisees.md`](references/sources-autorisees.md) et lire la page officielle, pas le seul extrait de recherche.

**3. Abstention.** Si aucune voie ne permet de confirmer la source ou l'applicabilité, s'abstenir sur la proposition concernée, conformément à P7.

Ne pas considérer `search` et `fetch` comme des noms génériques des capacités web de Manus : ce sont les noms des outils du connecteur MCP de ce dépôt. Dans ce connecteur, `fetch` attend l'identifiant renvoyé par `search`, pas une URL. Ne présumer ni l'installation du connecteur ni la disponibilité d'outils de navigateur ; vérifier leur exposition avant de les appeler.

## Contrôles intégrés de la v3.5.0

DOC-AUDIT examine séparément la légalité d'une exécution forcée d'office visant un bien privé (couper, retirer, évacuer, détruire, confisquer ou attribuer à la personne publique). Il distingue aussi la classe de contravention, le maximum légal et l'amende forfaitaire éventuelle. Ces contrôles déclenchent une vérification, mais ne préjugent pas de la conclusion applicable au dossier.

## Ressources

| Fichier | Rôle |
|---|---|
| [`SKILL.md`](SKILL.md) | Noyau condensé, principes, procédure et échelle de récupération Manus |
| [`references/modules.md`](references/modules.md) | Déclencheurs et contrôles des six modules |
| [`references/sources-autorisees.md`](references/sources-autorisees.md) | Sources officielles et ordre de recherche |
| [`references/audit-documentaire.md`](references/audit-documentaire.md) | Protocole DOC-AUDIT complet, avec contrôles 3.5.0 |
| [`references/modes-erreur.md`](references/modes-erreur.md) | Dix-huit erreurs juridiques à prévenir |

## Installation et mise à jour dans Manus

Importer le dossier `manus_skill/` (avec `SKILL.md` et `references/`) dans **Skills → + Add → Upload a skill**. Pour une mise à jour, réimporter le dossier `manus_skill/`.

L'installation du skill et la connexion du serveur MCP sont distinctes. Pour connecter le serveur, suivre les consignes du dépôt dans `docs/mcp-app.md` et `docs/deployment.md`. Avant de s'appuyer sur l'instance déployée, vérifier que les connecteurs MCP personnalisés de Manus acceptent un jeton porteur OAuth ; cette compatibilité ne doit pas être présumée.

## Versionnement

Le frontmatter de `SKILL.md` porte `version: 3.5.0-manus` et `base_version: 3.5.0`. Le portage Manus est maintenu séparément du noyau `skill/` ; les changements du noyau ne se propagent pas automatiquement.
