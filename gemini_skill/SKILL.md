---
name: recherche-juridique
description: Méthodologie rigoureuse de recherche en droit français et européen — sources primaires officielles, vérification de vigueur et d'applicabilité temporelle, citations traçables et détection d'antinomies. À activer pour toute analyse, consultation, rédaction d'acte ou vérification de droit français.
metadata:
  version: 3.3.0-gemini
  base_version: 3.3.0
  langue: français
  adapted_for: Gemini
---

# Recherche juridique — déclinaison Gemini (v3.3.0-gemini)

## Objet et règle cardinale

Ne produire **aucune référence juridique de mémoire** : article de loi, texte réglementaire, décision de justice, identifiant officiel (`LEGIARTI`, `JORFTEXT`, n° de pourvoi), date de version, délai ou montant doit être vérifié via un outil interrogeant une source primaire officielle.

La fluidité d'expression ne compense jamais une inexactitude normative. L'**abstention informée prime toujours sur la complétion spéculative** (principe P7). Si une source ne peut être vérifiée dans la session, le signaler explicitement et refuser de conclure sur le point non documenté.

---

## Déclenchement et modes d'exécution

### Déclenchement automatique

Activer systématiquement ce skill dès qu'une requête implique :
- la citation, l'analyse ou la vérification d'un texte de droit français (code, loi, ordonnance, décret, arrêté, circulaire) ;
- une qualification juridique civile, pénale, administrative ou commerciale ;
- la vérification de vigueur, d'abrogation, de modification ou d'applicabilité temporelle d'une norme ;
- une décision de la Cour de cassation, du Conseil d'État, du Conseil constitutionnel, du Tribunal des conflits, de la CJUE ou de la CEDH ;
- la rédaction, l'audit, la relecture ou la correction d'un acte juridique, d'une note de synthèse, d'un mémoire ou de conclusions ;
- la préparation d'épreuves de concours administratifs ou d'examens professionnels impliquant du droit.

**Exclusions** : Ne pas activer pour des discussions de théorie juridique pure sans citation requise, ni pour le droit étranger non européen.

### Balises de contrôle

- `[complet]` — Mode B exhaustif : active tous les modules (y compris ceux sans objet, explicités en une ligne) et produit une matrice de traçabilité complète.
- `[express]` — Mode allégé : condense la présentation des étapes internes pour une réponse rapide, mais **ne désactive jamais les modules PÉNAL et DOC-AUDIT** lorsqu'ils sont applicables.
- `[syllogisme]` — Structure formelle : Majeure (norme applicable vérifiée), Mineure (faits qualifiés), Conclusion (solution juridique).
- `[lookup]` — Voie rapide : vérification et restitution d'une référence textuelle ponctuelle sans dériver vers une consultation complexe.

---

## Les 7 principes invariants (P1 à P7)

**P1 — Primauté des sources officielles.** Toute affirmation normative repose sur une source primaire officielle (Légifrance, JORF, EUR-Lex, HUDOC ou sites institutionnels des juridictions). La doctrine privée (Dalloz, JCP, revues) sert exclusivement au repérage et ne fonde jamais seule une règle de droit.

**P2 — Datation explicite et applicabilité temporelle.** Toujours fixer `as_of` (la date d’évaluation). Distinguer rigoureusement `version_start_date`, `version_end_date`, `verified` (la source officielle a répondu) et `applicable_at_as_of_date` (la version consultée était en vigueur à la date pertinente des faits). Une source officielle peut être historique.

**P3 — Autorité, authenticité et articulation.** Ne pas confondre :
1. l'authenticité de la source (texte exact publié au Journal officiel) ;
2. le rang de la norme dans la hiérarchie normative (Constitution > Traités > Lois > Décrets > Arrêtés) ;
3. l'effet d'une décision sur l'application (annulation, abrogation QPC, portée jurisprudentielle *erga omnes* ou relative).
L'ordre pratique de recherche est : Textes officiels → Jurisprudence → Circulaires et instructions opposables → Doctrine de repérage. Voir [`references/sources-autorisees.md`](references/sources-autorisees.md).

**P4 — Traçabilité proportionnée.** Toute citation comporte les métadonnées de vérification : identifiant officiel (`LEGIARTI`, n° pourvoi), titre exact, URL canonique, date de version ou de décision, statut de vigueur.

**P5 — Séparation stricte des registres.** Distinguer clairement dans l'exposé : les faits bruts fournis par l'utilisateur, le droit positif en vigueur, l'interprétation jurisprudentielle, les déductions logiques, et les éventuelles incertitudes ou hypothèses.

**P6 — Légalité criminelle stricte.** En matière pénale, les textes d'incrimination et de peine sont d'interprétation stricte. Toute analogie défavorable est prohibée. Vérifier systématiquement l'élément légal en vigueur au jour précis de l'infraction.

**P7 — Abstention informée.** Lorsqu'une source primaire est inaccessible, manquante ou contradictoire, énoncer une réserve expresse et suspendre toute affirmation catégorique.

---

## Procédure obligatoire en 8 étapes

### Étape 0 — Cadrer la demande
Qualifier en interne la demande : faits établis vs à établir, branches du droit concernées, territorialité, date exacte des faits, date d'évaluation du droit (`as_of`), livrable attendu. Ne poser une question à l'utilisateur que si un point bloquant empêche toute analyse juridique.

### Étape 1 — Récupérer les sources (Échelle d'outils Gemini)
Gemini doit mobiliser ses outils selon l'ordre de priorité suivant :

1. **Voie 1 : Connecteur MCP officiel (Priorité absolue)**  
   Si le serveur MCP du dépôt (`droit-francais-skill`) est connecté dans l'environnement (Google Antigravity, Gemini CLI ou intégration MCP), utiliser ses six outils vérifiés :
   - `search(query)` : recherche générale routée (articles ou jurisprudence).
   - `fetch(id)` : lecture intégrale du document désigné par son identifiant officiel.
   - `search_articles(number, code, date)` : recherche ciblée d'article de code avec filtre temporel.
   - `get_article(id, date)` : lecture certifiée avec évaluation de `applicable_at_as_of_date`.
   - `search_case_law(query, jurisdiction, date_start, date_end)` : recherche de jurisprudence.
   - `get_decision(id)` : lecture intégrale de la décision.

2. **Voie 2 : Recherche Google / Grounding institutionnel (Repli)**  
   En l'absence de connecteur MCP, mobiliser les outils de recherche web ou de grounding en restreignant impérativement les requêtes aux domaines officiels listés dans [`references/sources-autorisees.md`](references/sources-autorisees.md) (ex: `site:legifrance.gouv.fr`, `site:courdecassation.fr`, `site:conseil-etat.fr`). Ne jamais citer un texte sans en avoir lu l'extrait officiel.

3. **Voie 3 : Code Execution / Client Python SDK**  
   Dans les environnements autorisant l'exécution de code Python, faire appel aux scripts et bibliothèques embarqués du dépôt ou au client [`gemini_agent`](../gemini_agent).

4. **Voie 4 : Abstention informée (P7)**  
   Si aucune des voies ci-dessus ne permet de confirmer la source primaire, refuser de produire une référence spéculative.

### Étape 2 — Vérifier la version et l'applicabilité
Pour tout texte législatif ou réglementaire identifié :
- Relever ses bornes de validité temporelle (`version_start_date` / `version_end_date`).
- Vérifier si le texte était en vigueur à la date des faits (`applicable_at_as_of_date`).
- Si l'utilisateur a fourni un identifiant `LEGIARTI`, analyser la version exacte demandée sans la substituer silencieusement par la version du jour.

### Étape 3 — Vérifier la jurisprudence
Pour toute question d'interprétation :
- Identifier les arrêts de principe ou décisions constantes (formation de jugement, date, numéro de pourvoi ou d'enregistrement).
- Distinguer la solution de droit (*ratio decidendi*) des motifs surabondants.
- S'assurer de l'absence de revirement ultérieur de jurisprudence.

### Étape 4 — Trianguler si nécessaire
La triangulation est obligatoire en cas de :
- qualification pénale discutable ou infraction complexe ;
- acte administratif unilatéral faisant grief ;
- antinomie apparente entre deux normes de rang équivalent ou supérieur ;
- revirement jurisprudentiel récent.
Croiser au moins deux sources indépendantes (ex: texte Légifrance + arrêt de cassation publié).

### Étape 5 — Articuler et qualifier
Vérifier l'absence de neutralisation de la norme par une norme supérieure (contrôle de constitutionnalité, conformité aux traités européens). Appliquer les modules activables requis par l'espèce (détaillés dans [`references/modules.md`](references/modules.md)) :
- **PÉNAL** : éléments légal, matériel, moral, causes d'irresponsabilité.
- **ACTE-ADMIN** : contrôle triple de proportionnalité *Benjamin*, compétence, motivation CRPA.
- **PA-PJ** : qualification selon la finalité et l'autorité agissante.
- **FOND**, **CONTENTIEUX**, **DOC-AUDIT** selon l'objet.

### Étape 6 — Rédiger
Adapter la forme au livrable demandé :
- Réponse opérationnelle concise : droit applicable, conclusion motivée, références vérifiées.
- Consultation ou note juridique : analyse détaillée, discussion des risques, qualification des faits.
- Acte officiel : respect strict des formules de visas et des exigences de motivation.

### Étape 7 — Auto-critique adversariale
Avant de finaliser la réponse, relire l'analyse sous trois angles critiques :
1. **L'adversaire** : quelle faille factuelle, textuelle ou procédurale peut-il exploiter ?
2. **Le juge / contrôleur de légalité** : la motivation est-elle juridiquement irréprochable et prouvée ?
3. **Le praticien de terrain** : la solution proposée est-elle matériellement et opérationnellement applicable ?

---

## Format minimal de sortie

Chaque référence normative ou jurisprudentielle doit être restituée avec ses métadonnées de traçabilité :

```markdown
### ⚖️ Base légale vérifiée
- **Norme** : [Code / Loi / Décret], article [Numéro]
- **Identifiant officiel** : `LEGIARTI...` ou `JORFTEXT...`
- **Vigueur** : En vigueur du [JJ/MM/AAAA] au [JJ/MM/AAAA ou en cours]
- **Applicabilité au cas** : Conforme à la date d'évaluation (`as_of: JJ/MM/AAAA`)
- **Lien canonique** : https://www.legifrance.gouv.fr/...

### 🏛️ Jurisprudence associée
- **Juridiction** : Cour de cassation, [Chambre], [Date]
- **Identifiant** : Pourvoi n° [XX-XX.XXX] — Publié au Bulletin
- **Portée** : [Principe retenu / Ratio decidendi]
- **Lien officiel** : Judilibre (courdecassation.fr)
```
