---
name: recherche-juridique
description: Méthodologie rigoureuse de recherche en droit français et européen, fondée sur des sources primaires officielles, la vérification de provenance, de vigueur et d’applicabilité à une date donnée, et des citations traçables. Utiliser pour toute demande portant sur des articles, codes, lois, décrets, arrêtés, circulaires, qualifications, jurisprudences, actes, notes, mémoires, audits ou concours juridiques. Ne pas utiliser pour le droit étranger non européen ni pour une question doctrinale sans citation normative.
metadata:
  version: 3.3.0-manus
  base_version: 3.3.0
  langue: français
  adapted_for: Manus
---

# Recherche juridique — portage Manus de la base 3.3.0

## Objet et règle cardinale

Ne produire aucune référence juridique de mémoire : article, décision, identifiant, date, montant ou délai doit être vérifié par un outil ou une source primaire. Vérifier séparément la provenance officielle, la version du texte, sa vigueur et son applicabilité à la date pertinente. Si une source n’est pas confirmée, le signaler et ne pas conclure sur le point concerné.

Les scripts PISTE du dépôt d'origine ne sont pas supposés disponibles dans Manus. Le serveur MCP du dépôt, lui, peut être connecté directement à Manus comme connecteur personnalisé (voir étape 1) : c'est la voie à privilégier plutôt qu'un repli sur la capacité web générale. La règle de provenance reste identique quelle que soit la voie employée.

## Déclenchement et modes

Activer pour toute demande impliquant :

- un article, code, loi, décret, arrêté, ordonnance ou circulaire ;
- une qualification civile, pénale, administrative ou procédurale ;
- la vigueur, l’abrogation, l’entrée en vigueur ou l’applicabilité d’une norme ;
- une décision de la Cour de cassation, du Conseil d’État, du Conseil constitutionnel, de la CJUE ou de la CEDH ;
- la rédaction, l’audit ou la relecture d’un acte, d’une note, d’un mémoire ou de conclusions ;
- un écrit ou oral de concours avec références juridiques.

Le mode par défaut active le noyau et les modules détectés. `[complet]` force tous les contrôles et affiche un encart de synthèse. `[express]` réduit l’affichage et les recherches facultatives, mais ne désactive jamais les contrôles **PÉNAL** et **DOC-AUDIT**. Ne jamais demander rituellement à l’utilisateur une clé API : constater les capacités disponibles et appliquer la voie de repli.

## Principes invariants P1–P7

**P1 — Primauté.** Toute affirmation normative repose sur Légifrance, le JORF, EUR-Lex, HUDOC ou le site officiel de la juridiction. La doctrine privée sert au repérage uniquement.

**P2 — Datation.** Toujours fixer `as_of`, la date d’évaluation. Distinguer `version_start_date`, `version_end_date`, `verified` et `applicable_at_as_of_date`. Une source officielle peut être historique ; `verified: true` signifie seulement que la source officielle a répondu.

**P3 — Autorité et articulation.** Ne pas confondre authenticité de la source, rang de la norme et effet d’une décision. L’ordre de recherche est un ordre pratique, pas une hiérarchie abstraite des normes : textes officiels, jurisprudence officielle, circulaires et instructions, doctrine institutionnelle.

**P4 — Traçabilité.** Toute citation comporte, lorsque disponible, identifiant officiel, intitulé, URL canonique, date de version ou de décision, source et applicabilité.

**P5 — Registres séparés.** Distinguer droit positif, interprétation jurisprudentielle, faits fournis, inférence, hypothèse et opinion.

**P6 — Légalité criminelle stricte.** En pénal, vérifier le texte d’incrimination applicable à la date des faits et les éléments légal, matériel et moral. Ne pas appliquer une analogie défavorable.

**P7 — Abstention informée.** Une source inaccessible, illisible, contradictoire ou non datée entraîne une réserve explicite et l’abstention sur la proposition non vérifiée.

## Procédure obligatoire

### Étape 0 — Qualifier la demande

Déterminer en interne l’objet exact, les faits établis et à établir, les branches du droit, le territoire et la compétence, la date des faits, la date d’application, la date d’audit et le livrable attendu. Poser une question seulement si une ambiguïté bloque réellement l’analyse.

### Étape 1 — Récupérer les sources

Manus accepte des **serveurs MCP personnalisés** (Settings → Integrations → Custom MCP Servers), sans code ni syntaxe particulière une fois connectés. C'est la voie à privilégier : elle donne un accès direct, vérifié et à jour à Légifrance et Judilibre, plutôt que de dépendre de la capacité web générale de Manus.

**1. Connecteur MCP dédié (priorité)** — si le serveur MCP de ce dépôt (`droit-francais`, auto-hébergé ou l'instance déployée) est connecté, ses six outils sont exacts, vérifiés dans `mcp_server/server.py` :

| Outil | Paramètres | Usage |
|---|---|---|
| `search` | `query` | Routeur générique : article si la requête en contient un, jurisprudence sinon |
| `fetch` | `id` (l'identifiant renvoyé par `search`, pas une URL) | Lecture du résultat désigné par `search` |
| `search_articles` | `number`, `code`, `date` | Recherche d'article ciblée, avec code et date |
| `get_article` | `id`, `date` | Lecture d'un article par identifiant `LEGIARTI`, évalue `applicable_at_as_of_date` |
| `search_case_law` | `query`, `jurisdiction`, `date_start`, `date_end` | Recherche de jurisprudence |
| `get_decision` | `id` | Lecture d'une décision |

Préférer `search_articles` → `get_article` à `search` → `fetch` dès qu'un numéro d'article est identifié : la provenance et l'applicabilité y sont plus précises.

**2. Capacité web native de Manus (repli)** — si aucun connecteur MCP n'est disponible. Le nom exact de cette capacité **n'est pas documenté publiquement par Manus** et n'est donc pas supposé ici : constater les outils réellement proposés dans la session en cours plutôt que d'en deviner le nom, et restreindre les requêtes aux domaines officiels listés dans `references/sources-autorisees.md`. Lire la page trouvée plutôt que de se fier au seul extrait de recherche.

**3. Abstention** — si aucune des deux voies n'aboutit (P7).

Ne jamais inventer un appel d'outil, MCP ou natif, ni supposer la disponibilité d'un connecteur non confirmé dans la session.

### Étape 2 — Vérifier la version et l’applicabilité

Pour chaque texte, relever les bornes de validité et l’historique. Si l’utilisateur fournit un identifiant LEGIARTI, le vérifier avant de le retourner et lire la version désignée ; ne pas le remplacer silencieusement par la version actuelle. Pour une recherche d’article, conserver le code et la date exprimés dans la requête. Laisser la date vide seulement lorsqu’il faut évaluer le droit à la date du serveur Manus.

Présenter séparément :

| Champ | Signification |
|---|---|
| `verified` | La source officielle a été retrouvée et lue |
| `as_of_date` | Date à laquelle l’applicabilité est évaluée |
| `version_start_date` / `version_end_date` | Bornes de la version consultée |
| `applicable_at_as_of_date` | La version couvre ou non la date évaluée |
| `caveat` | Écart, version historique ou incertitude à signaler |

### Étape 3 — Vérifier la jurisprudence

Rechercher les décisions qui confirment, précisent ou contredisent l’interprétation. Relever juridiction, formation, date, identifiant, dispositif et motifs utiles. Distinguer ratio decidendi et obiter dictum. L’absence de jurisprudence localisable ne signifie pas que le texte est incertain ; elle doit seulement être signalée.

### Étape 4 — Trianguler si nécessaire

Rendre la triangulation obligatoire en cas d’élément constitutif discutable, qualification concurrente, application analogique apparente, divergence ou revirement connu, articulation de compétences, proportionnalité interprétative ou citation officielle portant une interprétation discutable. Vérifier la source primaire par deux chemins indépendants lorsque c’est possible et rechercher la jurisprudence qui confirme ou contredit.

Une décision est requise pour présenter comme établie une interprétation contentieuse. Une lecture claire d’un texte, une constatation matérielle non ambiguë ou la reproduction d’une règle claire ne requiert pas automatiquement une décision. En cas d’échec, produire une sortie dégradée balisée par P7.

### Étape 5 — Articuler et qualifier

Appliquer les normes aux faits sans dépasser les sources. Identifier exceptions, seuils, cumuls, conflits de normes, dispositions transitoires, compétence, preuve et conséquences pratiques. Pour les opérations de police, activer PA-PJ ; pour les actes administratifs, vérifier compétence, motivation, opposabilité et proportionnalité.

### Étape 6 — Rédiger

Adapter la traçabilité au livrable. Une réponse simple expose les sources, la date applicable et les réserves utiles sans réciter les étapes internes. Une note de fond, un audit ou `[complet]` inclut la synthèse des contrôles, les limites et les objections restantes. Ne pas afficher une auto-critique vide ou rituelle.

### Étape 7 — Auto-critique adversariale

Relire l’analyse depuis trois rôles : l’adversaire qui cherche une faille, le juge ou contrôleur qui exige la preuve, et le praticien du métier lorsque son profil est connu. Si un rôle découvre un défaut, revenir à l’étape concernée avant livraison. Afficher le résultat si une objection subsiste ou dans une note de fond, un audit ou `[complet]`.

## Format minimal de sortie

Pour chaque référence normative ou jurisprudentielle, fournir :

- identifiant officiel : LEGIARTI, numéro de pourvoi, ECLI ou numéro de décision ;
- titre, article ou objet ;
- URL canonique ;
- date de version ou de décision ;
- `as_of` et applicabilité ;
- source officielle et réserve éventuelle.

Employer exactement la réserve suivante lorsque nécessaire : **« Source non confirmée — abstention sur ce point. »**

## Modules

Lire `references/modules.md` dès qu’un module est activé. Les modules sont **PÉNAL**, **ACTE-ADMIN**, **PA-PJ**, **FOND**, **CONTENTIEUX** et **DOC-AUDIT**. En cas de doute sur un déclencheur, activer le module. Le détail des sources et de leur usage figure dans `references/sources-autorisees.md`.
