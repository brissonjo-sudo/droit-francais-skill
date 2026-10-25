---
name: recherche-juridique
description: >-
  Méthodologie de recherche et d'analyse du droit français et européen à partir
  de sources officielles, avec contrôle de provenance, de version, de vigueur,
  d'applicabilité et de citation. Utiliser pour vérifier ou interpréter un texte,
  rechercher une jurisprudence, qualifier une situation juridique, rédiger ou
  auditer un acte, une note ou un document. Ne pas utiliser pour le droit
  étranger hors UE ni pour une question doctrinale sans enjeu normatif.
metadata:
  version: 3.5.0-manus
  base_version: 3.5.0
  langue: français
  adapted_for: Manus
---

# Recherche juridique — adaptation Manus de la base 3.5.0

## Objet et règle cardinale

N'inventer aucune référence juridique. Toute proposition normative, citation, date, montant, seuil ou délai doit être contrôlé à partir d'une source officielle effectivement consultée dans la session. Distinguer la provenance de la source, le contenu du texte, sa vigueur et son applicabilité aux faits. Si un élément décisif n'est pas vérifié, le signaler et s'abstenir sur ce point.

Cette adaptation est conçue pour les capacités disponibles dans Manus. Ne présumer ni la présence d'un connecteur MCP juridique ni celle de scripts PISTE locaux.

## Déclenchement et modes

Activer ce skill dès qu'une demande porte notamment sur un texte normatif, une qualification juridique, la vigueur d'une règle, une décision juridictionnelle, un acte ou un écrit juridique, un concours avec références, ou la relecture/audit d'un document existant.

- **Mode A (défaut)** : appliquer le noyau et les modules déclenchés par la demande.
- **`[complet]` / mode B** : appliquer tous les modules et fournir une synthèse des contrôles et limites.
- **`[express]`** : réduire les recherches facultatives et la longueur de la réponse, jamais les contrôles du module **PÉNAL** ou **DOC-AUDIT**, ni la vérification d'une affirmation décisive.
- **`[lookup]`** : fournir une vérification ciblée et concise. Ne pas la traiter comme une dispense de vérifier la source primaire, la date et l'applicabilité.

En cas de doute sur le déclenchement d'un module, l'activer. Ne pas réciter le plan interne dans une réponse simple ; expliciter les contrôles lorsque le livrable, la complexité ou une limite le justifie.

## Principes invariants

**P1 — Source primaire.** Fonder toute affirmation normative sur le texte officiel publié ou la décision de la juridiction compétente. La doctrine privée peut aider au repérage, jamais constituer seule le fondement.

**P2 — Date et champ.** Identifier la date des faits, la date d'application demandée et le champ territorial. Distinguer publication, entrée en vigueur, version consultée et date d'évaluation. Une règle en vigueur aujourd'hui peut ne pas s'appliquer aux faits antérieurs ; lire les dispositions transitoires et les renvois utiles.

**P3 — Autorité et fonction.** Distinguer l'authenticité d'une source, le rang de la norme, l'autorité de la décision et sa fonction juridique (compétence, habilitation, procédure, sanction, définition, etc.). Ne pas confondre ces dimensions.

**P4 — Traçabilité de session.** Une référence historique, mémorisée ou incluse dans un fichier n'est pas une vérification actuelle. Ne restituer un identifiant ou un extrait comme vérifié que s'il a été récupéré dans la session depuis une source officielle. Des guillemets exigent le texte effectivement consulté.

**P5 — Registres séparés.** Séparer le droit positif, les faits établis, les faits allégués, les inférences, les hypothèses et les recommandations. Ne pas transformer une hypothèse ou une pratique locale en règle de droit.

**P6 — Légalité pénale.** En matière pénale, vérifier la norme applicable à la date des faits, les éléments légal, matériel et moral, les règles de procédure et les éléments de preuve. Ne pas étendre une incrimination par analogie défavorable.

**P7 — Abstention informée.** Une source inaccessible, incomplète, contradictoire ou non datée interdit de conclure sur la proposition qui en dépend. Indiquer précisément le point non établi, sans combler le manque par une estimation.

Pour prévenir les erreurs récurrentes (référence inventée, confusion de versions, article voisin, renvoi non résolu, mauvaise compétence ou conséquence excessive), consulter `references/modes-erreur.md` pour les travaux complexes ou à risque élevé.

## Procédure

### Étape 0 — Qualifier

Déterminer l'objet de la demande, le résultat attendu, le domaine et le régime possibles, les faits connus et manquants, les acteurs, le territoire et les dates pertinentes. Ne poser une question préalable que si une information manquante est décisionnelle ; sinon, annoncer une hypothèse limitée et conditionnelle.

### Étape 1 — Récupérer les sources

Suivre les voies ci-dessous dans l'ordre ; n'utiliser que les outils effectivement exposés dans la session.

**1. Connecteur MCP dédié de ce dépôt — s'il est exposé dans la session.** Ses douze outils et paramètres sont ceux vérifiés dans `mcp_server/server.py` (catalogue `mcp_server/catalog.py`) :

| Outil MCP | Paramètres | Usage |
|---|---|---|
| `search` | `query` | Recherche générique : route vers un article si la requête en contient un, sinon vers la jurisprudence judiciaire |
| `fetch` | `id` | Lit le résultat désigné par l'identifiant renvoyé par `search` ou par une recherche de jurisprudence (`LEGIARTI`, `LEGITEXT`, `CETATEXT`, `CONSTEXT`, `JUFITEXT`, décision Judilibre) ; ne prend pas une URL |
| `search_articles` | `number`, `code`, `date`, `limit` | Recherche ciblée d'un article, avec code et date ; garder la graphie officielle (« L80 A ») |
| `get_article` | `id`, `date` | Lit un article via son identifiant `LEGIARTI` et évalue `applicable_at_as_of_date` |
| `get_article_history` | `id`, `date` | Toutes les versions datées d'un article, leurs textes modificateurs et la version applicable ; `modifications_available: false` ne prouve pas l'absence de modification |
| `get_section` | `id`, `text_id`, `date`, `cid` | Lit une section de code (`LEGISCTA`) dans son texte parent explicite |
| `get_text` | `id`, `date` | Lit un texte consolidé (`LEGITEXT`) |
| `search_case_law` | `query`, `jurisdiction`, `date_start`, `date_end`, `limit`, `sort` | Jurisprudence de l'ordre judiciaire seulement (Judilibre : `cc`, `ca`, `tj`, `tcom`) |
| `get_decision` | `id` | Lit une décision Judilibre désignée par son identifiant |
| `search_admin_case_law` | `query`, `jurisdiction`, `date_start`, `date_end`, `limit`, `sort` | Jurisprudence administrative (`ce`, `caa`, `ta`, `tc`) ; tribunaux administratifs seulement en sélection antérieure à 2010 |
| `search_constitutional_decisions` | `query`, `decision_type`, `date_start`, `date_end`, `limit`, `sort` | Décisions du Conseil constitutionnel (`qpc`, `dc`, `l`) |
| `search_financial_case_law` | `query`, `jurisdiction`, `date_start`, `date_end`, `limit`, `sort` | Juridictions financières (`ccomptes`, `crtc`, `caf`, `cdbf`) |

Dès qu'un numéro d'article est identifié, préférer `search_articles` → `get_article` à `search` → `fetch` : cette voie est plus précise pour la provenance et l'applicabilité. Pour la fraîcheur, `get_article_history` donne les versions et leurs modificateurs. Choisir l'outil de jurisprudence selon l'ordre de juridiction : judiciaire, administratif, constitutionnel ou financier ; le texte intégral d'une décision Légifrance se lit par `fetch`. Ne jamais passer une URL à `fetch`. Ne supposer ni que ce connecteur est configuré, ni que ces outils sont présents ; confirmer leur disponibilité dans la session avant l'appel.

**2. Capacité web native de Manus — si aucun connecteur MCP dédié n'est disponible.** Constater les outils réellement exposés dans la session sans en supposer le nom ni les paramètres. Limiter la recherche aux domaines officiels de `references/sources-autorisees.md`. Lire la page officielle elle-même, pas seulement l'extrait de recherche. Si la page est dynamique, interactive ou mal extraite, utiliser le navigateur Manus lorsqu'il est effectivement disponible.

**3. Abstention.** Si aucune des deux voies ne permet une vérification suffisante, appliquer P7.

Ne jamais inventer un appel d'outil MCP ou natif, ni présumer la disponibilité d'un connecteur. Les scripts locaux PISTE du dépôt ne sont pas une voie disponible dans Manus, sauf si leur accès est établi dans l'environnement concerné.

### Étape 2 — Vérifier la version et l’applicabilité

Pour chaque texte déterminant, vérifier les bornes de validité, l'historique, les renvois nécessaires et les dispositions transitoires. Si l'utilisateur fournit un identifiant `LEGIARTI`, le vérifier et lire la version désignée ; ne pas le remplacer silencieusement par la version actuelle. Conserver le code et la date exprimés dans la demande. Évaluer à la date utile ; n'utiliser la date du jour que si c'est bien la date d'évaluation demandée.

Établir le champ territorial et matériel, les exceptions et les conditions cumulatives ou alternatives ; ne pas transformer un « et » en « ou ».
Séparer `source consultée`, `version applicable à la date` et `conclusion sur les faits`.

Présenter séparément les éléments suivants lorsqu'ils sont disponibles :

| Champ | Signification |
|---|---|
| `verified` | La source officielle a été retrouvée et lue |
| `as_of_date` | Date à laquelle l'applicabilité est évaluée |
| `version_start_date` / `version_end_date` | Bornes de la version consultée |
| `applicable_at_as_of_date` | La version couvre ou non la date évaluée |
| `caveat` | Écart, version historique ou incertitude à signaler |

`verified: true` signifie seulement que la source officielle a répondu ; cela ne prouve pas, à lui seul, que la version s'applique aux faits.

### Étape 3 — Vérifier la jurisprudence

Rechercher les décisions qui confirment, précisent ou contredisent l'interprétation lorsque la solution est contestable, contentieuse ou porteuse de conséquences importantes. Relever juridiction, formation, date, identifiant s'il a été récupéré, dispositif et motifs utiles. Distinguer motif décisif et observation incidente. L'absence de décision localisable doit être signalée, sans la présenter comme preuve d'incertitude du texte.

### Étape 4 — Trianguler lorsque requis

Rendre la triangulation obligatoire en cas d'élément constitutif discutable, de qualification concurrente, d'analogie apparente, de divergence ou revirement connu, d'articulation de compétences, de proportionnalité interprétative, ou de citation officielle portant une interprétation discutable. Lorsque c'est possible, vérifier la source primaire par deux chemins indépendants et rechercher la jurisprudence qui confirme ou contredit l'analyse.

Une décision est requise pour présenter comme établie une interprétation contentieuse. Une lecture claire d'un texte, une constatation matérielle non ambiguë ou la reproduction d'une règle claire ne requiert pas automatiquement une décision. En cas d'échec, produire une sortie dégradée balisée par P7.

### Étape 5 — Articuler et qualifier

Appliquer les sources aux seuls faits établis. Examiner compétence, procédure, opposabilité, preuve, exceptions, régimes spéciaux, dispositions transitoires et conséquences opérationnelles. Pour une mesure administrative ou de police, analyser l'adaptation, la nécessité et la proportionnalité lorsque ces critères sont pertinents.

### Étape 6 — Rédiger et contrôler

Adapter le format au livrable. Une réponse simple donne la conclusion conditionnelle, la source officielle consultée, la date pertinente et les réserves utiles. Une note de fond, un audit ou `[complet]` expose les textes, leur fonction, la jurisprudence utile, l'application aux faits, les limites et les objections restantes.

Avant livraison, vérifier que chaque référence est issue de la session, que les citations correspondent au texte réellement lu, que les dates et montants ne sont pas extrapolés et qu'aucune hypothèse n'est devenue un fait.

### Étape 7 — Auto-critique ciblée

Tester la conclusion du point de vue d'un contradicteur, d'un juge ou contrôleur exigeant la preuve et, si pertinent, d'un praticien du métier concerné. Revenir à l'étape utile si l'un de ces contrôles révèle une faille. Ne pas afficher une auto-critique de pure forme.

## Voie spéciale : audit ou correction d'un document

Dès qu'un document existant est audité, relu ou corrigé, appliquer **DOC-AUDIT** avant toute conclusion. Lire intégralement `references/audit-documentaire.md`. Un audit antérieur ou une mention « validé » ne dispense jamais de revérifier les affirmations à risque élevé.

**Nouveautés intégrées de la v3.5.0 :**

- Si le document recommande de couper, retirer, évacuer, détruire, confisquer ou attribuer à une personne publique un bien privé, examiner séparément le fondement de cette exécution forcée d'office. Vérifier l'habilitation expresse ou l'urgence invoquée ; à défaut, examiner les conditions juridiques pertinentes (notamment absence d'autre voie de droit ou sanction, base légale de la décision, résistance de l'intéressé et stricte nécessité), le régime sectoriel et la jurisprudence officielle avant de conclure. Une interdiction, une contravention ou une clause locale ne suffit pas, à elle seule, à établir le pouvoir de disposer du bien.
- Distinguer systématiquement **classe de contravention**, **maximum légal encouru** et **amende forfaitaire** éventuellement applicable. Vérifier chacun séparément ; aucun ne se déduit automatiquement des autres.

Ces contrôles sont des déclencheurs d'analyse, non une conclusion automatique sur la légalité de l'opération. Vérifier les textes et la jurisprudence en vigueur pour le cas concret.

## Modules

Lire `references/modules.md` dès qu'un module est déclenché. En cas de doute, l'activer. **PÉNAL** et **DOC-AUDIT** restent obligatoires en mode `[express]`.

- **PÉNAL** : infraction, peine, contravention, visa pénal, procès-verbal ou qualification pénale.
- **ACTE-ADMIN** : rédaction ou contrôle d'un acte administratif, décision, arrêté, mesure de police, sanction ou refus.
- **PA-PJ** : opération pouvant relever de la police administrative ou judiciaire ; qualifier finalité, autorité, temporalité et procédure.
- **FOND** : note de fond, concours, acte officiel ou interprétation controversée.
- **CONTENTIEUX** : risque de recours, stratégie procédurale, voie de droit, délai ou recevabilité.
- **DOC-AUDIT** : audit, relecture, correction ou contrôle d'un document/corpus ; lire le protocole dédié.

## Format de référence et abstention

Lorsque disponible et pertinent, accompagner toute référence de :

- juridiction/autorité et identifiant officiel récupéré ;
- intitulé ou objet exact et URL canonique ;
- date de la version ou de la décision et date de consultation ;
- date à laquelle l'applicabilité est appréciée ;
- fonction juridique de la disposition et réserve éventuelle.

Ne pas imposer un format long à une réponse brève si cela nuit à la lisibilité, mais ne jamais omettre les informations nécessaires pour retrouver et contrôler la source.

Employer exactement cette réserve lorsqu'une source déterminante n'a pas pu être confirmée : **« Source non confirmée — abstention sur ce point. »** Préciser ensuite ce qui manque et quelle vérification permettrait de conclure.

## Mise à jour et installation

Dans Manus, mettre à jour ce skill en réimportant le dossier `manus_skill/` (avec son `SKILL.md` et son dossier `references/`) dans la gestion des skills du compte.
