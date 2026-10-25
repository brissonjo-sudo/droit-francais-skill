---
name: recherche-juridique
description: Méthodologie rigoureuse de recherche en droit français et européen — sources primaires officielles, vérification de vigueur et d'applicabilité temporelle, citations traçables et détection d'antinomies. À activer pour toute analyse, consultation, rédaction d'acte, audit de document ou vérification de droit français.
metadata:
  version: 3.6.0-gemini
  base_version: 3.6.0
  langue: français
  adapted_for: Gemini
---

# Recherche juridique — déclinaison Gemini (v3.6.0-gemini)

## Objet et règle cardinale

Ne produire **aucune référence juridique de mémoire** : article de loi, texte réglementaire, décision de justice, identifiant officiel (`LEGIARTI`, `JORFTEXT`, n° de pourvoi), date de version, délai, seuil ou montant doit être vérifié via un outil interrogeant une source primaire officielle **dans la session**. Distinguer la provenance de la source, le contenu du texte, sa vigueur et son applicabilité aux faits.

La fluidité d'expression ne compense jamais une inexactitude normative. L'**abstention informée prime toujours sur la complétion spéculative** (principe P7). Si un élément décisif ne peut être vérifié, le signaler et refuser de conclure sur ce point.

---

## Déclenchement et modes d'exécution

### Déclenchement automatique

Activer systématiquement ce skill dès qu'une requête implique :
- la citation, l'analyse ou la vérification d'un texte de droit français (code, loi, ordonnance, décret, arrêté, circulaire) ;
- une qualification juridique civile, pénale, administrative ou commerciale ;
- la vérification de vigueur, d'abrogation, de modification ou d'applicabilité temporelle d'une norme ;
- une décision de la Cour de cassation, du Conseil d'État, du Conseil constitutionnel, du Tribunal des conflits, des juridictions financières, de la CJUE ou de la CEDH ;
- la rédaction, l'audit, la relecture ou la correction d'un acte juridique, d'une note de synthèse, d'un mémoire ou de conclusions ;
- la préparation d'épreuves de concours administratifs ou d'examens professionnels impliquant du droit.

**Exclusions** : ne pas activer pour des discussions de théorie juridique pure sans citation requise, ni pour le droit étranger non européen.

### Balises de contrôle

- **Mode A (défaut)** : appliquer le noyau et les modules déclenchés par la demande.
- `[complet]` — **mode B** exhaustif : active tous les modules (ceux sans objet sont signalés en une ligne, avec justification) et fournit une synthèse des contrôles et limites.
- `[express]` — réduit les recherches facultatives et la longueur, mais **ne désactive jamais les modules PÉNAL et DOC-AUDIT** ni la vérification d'une affirmation décisive.
- `[syllogisme]` — structure formelle : majeure (norme applicable vérifiée), mineure (faits qualifiés), conclusion.
- `[opérationnel]` — ajoute au livrable ses implications opérationnelles et, à l'étape 7, un quatrième regard sur la mise en œuvre.
- `[lookup]` — vérification ciblée et concise d'une référence ponctuelle ; ce n'est pas une dispense de vérifier la source primaire, la date et l'applicabilité.

En cas de doute sur le déclenchement d'un module, l'activer. Ne pas réciter le plan interne dans une réponse simple ; expliciter les contrôles lorsque le livrable, la complexité ou une limite le justifie.

---

## Les 7 principes invariants (P1 à P7)

**P1 — Source primaire.** Fonder toute affirmation normative sur le texte officiel publié ou la décision de la juridiction compétente (Légifrance, JORF, EUR-Lex, HUDOC, sites institutionnels des juridictions). La doctrine privée sert au repérage, jamais de fondement unique.

**P2 — Date et champ.** Identifier la date des faits, la date d'application demandée (`as_of`) et le champ territorial. Distinguer publication, entrée en vigueur, version consultée et date d'évaluation. Une règle en vigueur aujourd'hui peut ne pas s'appliquer aux faits antérieurs ; lire les dispositions transitoires et les renvois utiles.

**P3 — Autorité et fonction.** Distinguer l'authenticité de la source, le rang de la norme dans la hiérarchie, l'autorité et l'effet de la décision (annulation, abrogation QPC, portée), et la fonction juridique de la disposition (compétence, habilitation, procédure, sanction, définition…). Voir [`references/sources-autorisees.md`](references/sources-autorisees.md).

**P4 — Traçabilité de session.** Une référence historique, mémorisée ou incluse dans un fichier n'est pas une vérification actuelle. Ne restituer un identifiant ou un extrait comme vérifié que s'il a été récupéré dans la session depuis une source officielle ; sinon, l'omettre ou le marquer `⚠️ non vérifié — identifiant non récupéré`. Des guillemets exigent le texte effectivement consulté.

**P5 — Registres séparés.** Séparer le droit positif, les faits établis, les faits allégués, les inférences, les hypothèses et les recommandations. Ne pas transformer une hypothèse ou une pratique locale en règle de droit.

**P6 — Légalité pénale.** Vérifier la norme applicable à la date des faits, les éléments légal, matériel et moral, les règles de procédure et de preuve. Les textes d'incrimination sont d'interprétation stricte ; toute analogie défavorable est prohibée.

**P7 — Abstention informée.** Une source inaccessible, incomplète, contradictoire ou non datée interdit de conclure sur la proposition qui en dépend. Indiquer précisément le point non établi, sans combler le manque par une estimation.

Pour prévenir les erreurs récurrentes (référence inventée, confusion de versions, article voisin, renvoi non résolu, mauvaise compétence, conséquence excessive), consulter [`references/modes-erreur.md`](references/modes-erreur.md) pour les travaux complexes ou à risque élevé.

---

## Procédure obligatoire en 9 étapes (0, 0 bis, 1 à 7)

### Étape 0 — Cadrer la demande

Qualifier l'objet de la demande, le résultat attendu, le domaine et le régime possibles, les faits connus et manquants, les acteurs, le territoire et les dates pertinentes.

Lire `profil.md` s'il existe à la racine du skill (copie d'un fichier de `profils/`) : contexte, domaines et regard critique du métier sont des défauts, supplantés par la demande et rouverts à l'étape 0 bis s'ils deviennent décisionnels. Sans profil, ne supposer ni territoire ni métier.

### Étape 0 bis — Arbitrage des informations manquantes

Avant toute recherche, recenser les informations nécessaires qui manquent. Si la conclusion, le régime, la qualification ou la procédure change selon leur valeur, elles sont décisionnelles : poser la question et suspendre le fond. Sinon seulement, annoncer une hypothèse limitée. Chercher en source primaire ce qui est vérifiable ; ne demander que ce que l'utilisateur détient. Une question par défaut, trois au plus, de préférence fermées ; en attendant la réponse, au plus une esquisse bornée « si a / si b ».

### Étape 1 — Récupérer les sources (Échelle d'outils Gemini)

Mobiliser les outils dans l'ordre suivant ; n'utiliser que ceux effectivement exposés dans la session.

1. **Voie 1 : Connecteur MCP officiel (Priorité absolue)**
   Si le serveur MCP du dépôt (`droit-francais-skill`) est connecté (Google Antigravity, Gemini CLI ou autre intégration MCP), utiliser ses douze outils, dont les noms et paramètres sont ceux de `mcp_server/server.py` (catalogue `mcp_server/catalog.py`) :

   | Outil MCP | Paramètres | Usage |
   |---|---|---|
   | `search` | `query` | Recherche générale routée : article si la requête en contient un, sinon jurisprudence judiciaire |
   | `fetch` | `id` | Lit le document désigné par l'identifiant renvoyé par une recherche (`LEGIARTI`, `LEGITEXT`, `CETATEXT`, `CONSTEXT`, `JUFITEXT`, décision Judilibre) ; jamais une URL |
   | `search_articles` | `number`, `code`, `date`, `limit` | Article de code avec filtre temporel ; garder la graphie officielle (« L80 A ») |
   | `get_article` | `id`, `date` | Lecture certifiée avec évaluation de `applicable_at_as_of_date` |
   | `get_article_history` | `id`, `date` | Toutes les versions datées d'un article, leurs textes modificateurs et la version applicable |
   | `get_section` | `id`, `text_id`, `date`, `cid` | Section de code (`LEGISCTA`) dans son texte parent explicite |
   | `get_text` | `id`, `date` | Texte consolidé (`LEGITEXT`) |
   | `search_case_law` | `query`, `jurisdiction`, `date_start`, `date_end`, `limit`, `sort` | Jurisprudence de l'**ordre judiciaire** seulement (Judilibre : `cc`, `ca`, `tj`, `tcom`) |
   | `get_decision` | `id` | Lecture intégrale d'une décision Judilibre |
   | `search_admin_case_law` | `query`, `jurisdiction`, `date_start`, `date_end`, `limit`, `sort` | Jurisprudence administrative (`ce`, `caa`, `ta`, `tc`) ; tribunaux administratifs seulement en sélection antérieure à 2010 |
   | `search_constitutional_decisions` | `query`, `decision_type`, `date_start`, `date_end`, `limit`, `sort` | Conseil constitutionnel (`qpc`, `dc`, `l`) |
   | `search_financial_case_law` | `query`, `jurisdiction`, `date_start`, `date_end`, `limit`, `sort` | Juridictions financières (`ccomptes`, `crtc`, `caf`, `cdbf`) |

   Dès qu'un numéro d'article est identifié, préférer `search_articles` → `get_article` à `search` → `fetch`. Choisir l'outil de jurisprudence selon l'ordre de juridiction. Ne pas supposer que le connecteur est configuré ; confirmer la disponibilité des outils avant l'appel.

2. **Voie 2 : Code Execution / Client Python SDK**
   Sans connecteur MCP, dans un environnement autorisant l'exécution de Python et disposant d'identifiants PISTE, les scripts du noyau (`skill/scripts/legifrance.py`) interrogent Légifrance et Judilibre. Le client [`gemini_agent`](../gemini_agent) est un squelette dont les fonctions-outils ne sont pas branchées sur une source : ne jamais présenter son résultat comme une vérification.

3. **Voie 3 : Recherche Google / Grounding institutionnel (Repli)**
   À défaut des deux premières voies, utiliser la recherche web ou le grounding en restreignant les requêtes aux domaines officiels de [`references/sources-autorisees.md`](references/sources-autorisees.md) (ex. `site:legifrance.gouv.fr`, `site:courdecassation.fr`, `site:conseil-etat.fr`). Lire la page officielle elle-même, pas seulement l'extrait de recherche.

4. **Voie 4 : Abstention informée (P7)**
   Si aucune voie ne permet de confirmer la source primaire, refuser de produire une référence spéculative : omettre l'identifiant ou le marquer `⚠️ non vérifié — identifiant non récupéré`, et s'abstenir de conclure sur le point qui en dépend.

### Étape 2 — Vérifier la version, la fraîcheur et l'applicabilité

Pour chaque texte déterminant, vérifier les bornes de validité, l'historique, les renvois nécessaires et les dispositions transitoires. Si l'utilisateur fournit un identifiant `LEGIARTI`, lire la version désignée sans la remplacer silencieusement par la version du jour. Évaluer à la date utile ; n'utiliser la date du jour que si c'est la date d'évaluation demandée. Établir le champ territorial et matériel, les exceptions et les conditions cumulatives ou alternatives ; ne pas transformer un « et » en « ou ».

| Champ | Signification |
|---|---|
| `verified` | La source officielle a répondu — ne prouve pas, à lui seul, que la version s'applique aux faits |
| `as_of_date` | Date à laquelle l'applicabilité est évaluée |
| `version_start_date` / `version_end_date` | Bornes de la version consultée |
| `applicable_at_as_of_date` | La version couvre ou non la date évaluée |
| `caveat` | Écart, version historique ou incertitude à signaler |

**Fraîcheur (voie outillée).** `get_article_history` donne toutes les versions datées, le texte modificateur de chacune et la version applicable. Lire les états : `VIGUEUR_DIFF` = version publiée mais pas encore en vigueur (vacatio legis) ; `ABROGE_DIFF` = abrogation programmée de la version courante ; suffixe `_MORT_NE` = version jamais entrée en vigueur, à ne jamais citer comme droit applicable. `modifications_available: false` ne prouve pas l'absence de modification. À défaut de cet outil, les bornes de version de `get_article` établissent la version applicable, et les modificateurs se lisent sur la fiche Légifrance. L'outil ne dispense ni des dispositions transitoires ni des QPC.

### Étape 3 — Vérifier la jurisprudence

Rechercher les décisions qui confirment, précisent ou contredisent l'interprétation lorsque la solution est contestable, contentieuse ou porteuse de conséquences importantes. Relever juridiction, formation, date, identifiant récupéré, dispositif et motifs utiles. Distinguer la solution de droit (*ratio decidendi*) des motifs surabondants et s'assurer de l'absence de revirement. L'absence de décision localisable doit être signalée, sans la présenter comme preuve d'incertitude du texte.

### Étape 4 — Trianguler lorsque requis

La triangulation est obligatoire en cas d'élément constitutif discutable, de qualification concurrente, d'analogie apparente, de divergence ou revirement connu, d'articulation de compétences, de proportionnalité interprétative, d'antinomie apparente ou de citation officielle portant une interprétation discutable. Vérifier la source primaire par deux chemins indépendants et rechercher la jurisprudence qui confirme ou contredit l'analyse.

Une décision est requise pour présenter comme établie une interprétation contentieuse. La reproduction d'une règle claire ne requiert pas automatiquement une décision. En cas d'échec, produire une sortie dégradée balisée par P7.

### Étape 5 — Articuler et qualifier

Appliquer les sources aux seuls faits établis. Vérifier l'absence de neutralisation par une norme supérieure (constitutionnalité, conventionnalité). Examiner compétence, procédure, opposabilité, preuve, exceptions, régimes spéciaux, dispositions transitoires et conséquences opérationnelles. Pour une mesure administrative ou de police, analyser adaptation, nécessité et proportionnalité. Appliquer les modules requis (détail dans [`references/modules.md`](references/modules.md)).

### Étape 6 — Rédiger et contrôler

Adapter la forme au livrable : réponse opérationnelle (conclusion conditionnelle, source consultée, date pertinente, réserves), note ou consultation (textes, fonction, jurisprudence, application, limites), acte officiel (visas et motivation).

Avant livraison, vérifier que chaque référence est issue de la session, que les citations correspondent au texte réellement lu, que les dates et montants ne sont pas extrapolés et qu'aucune hypothèse n'est devenue un fait. Citer les fichiers du skill par le nom du skill et la section, sans lien ni chemin ; les liens sont réservés aux sources officielles.

### Étape 7 — Auto-critique adversariale

Tester la conclusion du point de vue :
1. **de l'adversaire** : quelle faille factuelle, textuelle ou procédurale peut-il exploiter ?
2. **du juge ou contrôleur de légalité** : la motivation est-elle prouvée ?
3. **du praticien de terrain** : la solution est-elle opérationnellement applicable ?

Revenir à l'étape utile si l'un de ces contrôles révèle une faille ; ne pas afficher une auto-critique de pure forme. Pour une analyse de fond, retracer brièvement l'histoire du texte (version initiale, modificateurs, motif de la dernière réforme) — `get_article_history` en fournit la chronologie.

---

## Voie spéciale : audit ou correction d'un document

Dès qu'un document existant est audité, relu ou corrigé, appliquer **DOC-AUDIT** avant toute conclusion et lire intégralement [`references/audit-documentaire.md`](references/audit-documentaire.md). Un audit antérieur ou une mention « validé » ne dispense jamais de revérifier les affirmations à risque élevé.

- Si le document recommande de couper, retirer, évacuer, détruire, confisquer ou attribuer à une personne publique un bien privé, examiner **séparément** le fondement de cette exécution forcée d'office : habilitation expresse ou urgence ; à défaut, absence d'autre voie de droit ou sanction, base légale de la décision, résistance de l'intéressé et stricte nécessité, régime sectoriel et jurisprudence officielle. Une interdiction, une contravention ou une clause locale ne suffit pas, à elle seule, à établir le pouvoir de disposer du bien.
- Distinguer **classe de contravention**, **maximum légal encouru** et **amende forfaitaire** éventuelle ; vérifier chacun séparément.
- Ne jamais déclarer le document « conforme » tant qu'une affirmation à risque élevé reste non vérifiée, non corrigée et sans abstention ciblée, ou que le contrôle post-correction n'a pas été fait.

---

## Format minimal de sortie

Chaque référence normative ou jurisprudentielle est restituée avec ses métadonnées de traçabilité :

```markdown
### Base légale vérifiée
- **Norme** : [Code / Loi / Décret], article [Numéro]
- **Identifiant officiel** : `LEGIARTI...` ou `JORFTEXT...` (récupéré dans la session)
- **Vigueur** : version du [JJ/MM/AAAA] au [JJ/MM/AAAA ou en cours]
- **Applicabilité au cas** : appréciée au [JJ/MM/AAAA] (`as_of`)
- **Lien canonique** : https://www.legifrance.gouv.fr/...

### Jurisprudence associée
- **Juridiction** : [juridiction], [formation], [date]
- **Identifiant** : [n° de pourvoi, de requête ou de décision] — [publication]
- **Portée** : [solution retenue / ratio decidendi]
- **Lien officiel** : [source officielle]
```

Ne pas imposer un format long à une réponse brève si cela nuit à la lisibilité, mais ne jamais omettre les informations nécessaires pour retrouver et contrôler la source.
