# Skill juridique — déclinaison Manus

Déclinaison Manus de la méthodologie de recherche juridique du dépôt, actualisée sur la base 3.5.0. Elle conserve le contrôle des sources dans la session et n'assume ni la présence d'un connecteur MCP juridique, ni celle de scripts PISTE locaux.

## Fonctionnement dans Manus

Le noyau demande d'abord de repérer les sources officielles avec `search`, puis d'ouvrir et lire la ressource avec `fetch`. Si l'extraction échoue ou si la page est interactive, il demande de découvrir les outils de navigateur ou MCP réellement accessibles et leur schéma avant de les utiliser. Il impose l'abstention sur toute conclusion qui dépend d'une source insuffisamment vérifiée.

Le serveur MCP de ce dépôt peut être utilisé s'il est effectivement connecté et exposé dans la session. Ses noms et paramètres restent ceux de `mcp_server/server.py`; l'adaptation n'en présume pas la disponibilité et n'invente aucun appel. L'accès web natif de Manus constitue la voie générale de recherche lorsque ses outils sont présents.

## Évolutions intégrées de la v3.5.0

Le module DOC-AUDIT impose désormais un contrôle distinct de l'exécution forcée d'office lorsqu'un document recommande de couper, retirer, évacuer, détruire, confisquer ou attribuer à la personne publique un bien privé. Il demande de vérifier le fondement, les circonstances, le régime sectoriel et la jurisprudence avant de conclure. Il distingue également la classe de contravention, le maximum légal encouru et l'amende forfaitaire éventuelle.

Ces contrôles ne déterminent pas automatiquement la légalité d'une opération : les textes et la jurisprudence doivent être consultés pour le cas concret.

## Ressources

| Fichier | Rôle |
|---|---|
| [`SKILL.md`](SKILL.md) | Noyau condensé, principes, procédure et voie de consultation Manus |
| [`references/modules.md`](references/modules.md) | Déclencheurs et contrôles des six modules |
| [`references/sources-autorisees.md`](references/sources-autorisees.md) | Sources officielles et ordre de recherche |
| [`references/audit-documentaire.md`](references/audit-documentaire.md) | Protocole DOC-AUDIT complet, notamment les deux contrôles v3.5.0 |
| [`references/modes-erreur.md`](references/modes-erreur.md) | Dix-huit erreurs juridiques à prévenir |

## Installation dans Manus

Manus accepte un skill par import : sélectionner le dossier `manus_skill/` ou le compresser en `.zip`, puis dans **Skills → + Add → Upload a skill**, choisir le fichier ou dossier. Le skill apparaît ensuite dans la liste des skills disponibles.

L'installation du skill et la connexion du serveur MCP sont deux opérations distinctes. Pour connecter le serveur, suivre les consignes du dépôt dans `docs/mcp-app.md` et `docs/deployment.md`. Ne pas présumer que l'authentification ou le transport d'un serveur externe est disponible dans la configuration de chaque compte Manus.

## Versionnement

Le frontmatter de `SKILL.md` porte `version: 3.5.0-manus` et `base_version: 3.5.0`. Le portage Manus est maintenu séparément du noyau `skill/` ; les changements du noyau ne se propagent pas automatiquement. Cette version incorpore le noyau condensé et les contrôles v3.5.0, avec ses références Manus.
