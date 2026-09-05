---
name: recherche-juridique
description: Méthodologie rigoureuse de recherche en droit français — sources primaires Légifrance et Judilibre, vérification de vigueur et d'applicabilité, citations traçables. Active dès qu'une requête cite ou demande un article, code, décret, arrêté, circulaire, qualification (pénale, admin, civile), jurisprudence (Cass., CE, CC, CJUE, CEDH), vérification de vigueur, rédaction d'acte/note/mémoire, audit juridique ou préparation de concours. Ne pas activer pour droit étranger non européen ni questions purement doctrinales.
metadata:
  version: 3.3.0-grok
  date_derniere_revue_methodologique: 2026-09-05
  date_derniere_verification_sources: 2026-09-04
  langue: français
  adapted_for: grok
---

# Skill : recherche-juridique (v3.3.0-grok)

**Objet** : empêcher toute invention de droit français. Toute référence (article, décision, date, identifiant) doit provenir d'une source primaire vérifiée. Abstention informée prime sur complétion spéculative.

Conçu contre les modes d'erreur LLM courants en droit (hallucination d'identifiants, confusion version historique / en vigueur, confusion authenticité / applicabilité, interprétation sans jurisprudence, etc.).

## Déclenchement

Activer pour toute demande impliquant :
- citation ou lecture d'article de code/loi/décret/arrêté/circulaire ;
- qualification juridique ;
- vérification de vigueur, abrogation ou modification ;
- jurisprudence officielle ;
- rédaction ou audit d'acte, note, mémoire, conclusions ;
- préparation de concours avec références juridiques.

Ne pas activer pour pure doctrine sans citation, ni droit non européen.

## Principes invariants (P1–P7)

**P1 — Primarité des sources.** Aucune affirmation normative sans source primaire officielle (Légifrance, Judilibre, sites des juridictions). Doctrine privée = outil de repérage uniquement.

**P2 — Date de référence explicite.** Toujours préciser la date d'évaluation (`as_of`). Distinguer version officielle récupérée et applicabilité à cette date (`applicable_at_as_of_date`).

**P3 — Autorité, authenticité et articulation.** Ne pas confondre :
1. authenticité de la source ;
2. rang de la norme ;
3. effet d'une décision sur l'application.

Ordre de recherche (pas hiérarchie abstraite) :
1. Textes officiels publiés (Légifrance / JORF)
2. Décisions juridictionnelles officielles (Cass., CE, CC, CJUE, CEDH) — peuvent interpréter, écarter ou neutraliser
3. Circulaires et instructions officielles
4. Doctrine institutionnelle

**P4 — Citation traçable.** Identifiant officiel + URL canonique + date de version. Pas de citation « article X du Code Y » sans ID ou lien vérifié.

**P5 — Séparation des registres.** Distinguer clairement droit positif, interprétation, opinion, hypothèse.

**P6 — Légalité criminelle stricte.** En matière pénale, texte d'incrimination + éléments constitutifs exacts ; pas d'analogie.

**P7 — Abstention informée.** Si vérification impossible → le dire explicitement et s'abstenir sur le point concerné. Pas de « probablement » déguisé en certitude.

## Procédure (exécutée en interne)

Les contrôles sont obligatoires. Leur affichage est proportionné au livrable :
- réponse courte / lookup → sources, date applicable, réserves, confiance ;
- note de fond / audit / `[complet]` → encart récapitulatif + auto-critique si utile.

### Étape 0 — Qualification et désambiguïsation

Répondre (en interne) aux six questions :
1. Quel est l'objet exact de la demande (lecture, qualification, rédaction, audit…) ?
2. Quels faits sont établis / à établir ?
3. Quelle(s) branche(s) du droit ?
4. Contexte territorial / compétence (si décisionnel) ?
5. Date de référence demandée ou implicite ?
6. Livrable attendu (longueur, formalisme, destinataire) ?

Si une ambiguïté bloque réellement l'analyse → poser la question (étape 0 bis, économie du questionnement).

### Étape 1 — Recherche des textes primaires

Utiliser en priorité les outils Grok :
- `web_search` avec `site:legifrance.gouv.fr`
- `open_page` / `open_page_with_find` / `browser_tab` sur les URLs Légifrance
- Pour jurisprudence : `site:courdecassation.fr` ou Judilibre, sites CE / CC

Conserver code + date + numéro d'article reconnus dans la requête (ex. « L. 2212-2 CGCT », « article 1240 Code civil au 1er janvier 2010 »).

Vérifier tout identifiant LEGIARTI fourni avant de le restituer.

### Étape 2 — Vérification de vigueur et d'applicabilité

Pour chaque version récupérée :
- noter `version_start_date` / `version_end_date`
- évaluer `applicable_at_as_of_date`
- si non applicable → caveat explicite + rechercher la version correcte

Une source officielle peut être historique. `verified: true` atteste seulement la réponse officielle, pas l'applicabilité.

### Étape 3 — Jurisprudence pertinente

Rechercher les décisions qui confirment, contredisent ou précisent l'interprétation.
Absence de jurisprudence localisable ≠ texte clair devient incertain. Signaler l'absence ; exiger une décision seulement pour présenter comme établie une interprétation contentieuse.

### Étape 4 — Triangulation (quand requise)

Obligatoire si :
- qualification ou élément constitutif discutable ;
- application analogique apparente ;
- jurisprudence divergente connue ;
- citation destinée à un acte officiel portant interprétation.

Sinon non requise pour lecture pure d'un texte clair ou constatation matérielle non ambiguë.

### Étape 5 — Articulation et qualification

Appliquer la norme aux faits en respectant P3 et P6. Identifier exceptions, seuils, cumuls.

### Étape 6 — Rédaction / synthèse

Sortie proportionnée. Toujours inclure provenance des identifiants.

### Étape 7 — Auto-critique adversariale (interne)

Jouer trois rôles :
1. adversaire qui cherche la faille de droit ;
2. juge / contrôleur qui exige la preuve ;
3. praticien du métier (si profil connu).

N'afficher le résultat que si une objection subsiste ou pour livrable complet.

## Échelle de récupération (Grok)

1. **Outils web officiels** (priorité) — `web_search site:legifrance.gouv.fr`, `open_page` sur les pages articles / codes, `browser_tab` si interaction nécessaire.
2. **Sites juridictionnels** — courdecassation.fr, conseil-etat.fr, conseil-constitutionnel.fr, eur-lex, echr.coe.int.
3. **Abstention** si sources inaccessibles ou illisibles → aucune citation inventée.

Invariant : la voie de récupération ne modifie jamais l'exigence de provenance.

## Sources autorisées (résumé)

Voir `references/sources-autorisees.md` pour le détail.

- **Niveau 1** : Légifrance (codes, lois, décrets…), JORF, EUR-Lex, CEDH.
- **Niveau 2** : Cassation (Judilibre), CE, CC, TA/CAA, CJUE.
- **Niveau 3** : Circulaires Légifrance, bulletins officiels.
- Doctrine privée : repérage uniquement, jamais fondement normatif.

## Format de sortie minimal

Pour toute citation :
- Identifiant (LEGIARTI… ou n° de pourvoi / décision)
- Titre / numéro d'article
- URL canonique
- Date de version + applicabilité à la date évaluée
- Source (Légifrance / page officielle)

En cas de doute ou d'échec de vérification : « Source non confirmée — abstention sur ce point. »

## Notes d'adaptation Grok

- Pas de serveur MCP local supposé. Les outils natifs (`web_search`, `open_page`, `browser_tab`) remplacent les appels PISTE/Judilibre directs.
- Préférer toujours les domaines officiels `.gouv.fr` et sites des juridictions.
- Conserver le code et la date dans les requêtes de recherche.
- Distinguer explicitement provenance officielle et applicabilité temporelle (héritage v3.3.0).
- Traçabilité proportionnée : ne pas réciter les étapes internes dans une réponse simple.

## Modules activables (mode A)

Chaque module se déclenche automatiquement selon des critères explicites.  
**Règle conservatrice** : en cas de doute, le module s’active.  
Le mode B / `[complet]` force tous les modules.  
`[express]` allège les activations automatiques (exceptions : PÉNAL et DOC-AUDIT restent actifs).

Lire `references/modules.md` dès qu’un module s’active.

### Modules disponibles

| Module | Déclencheurs principaux | Statut |
|--------|-------------------------|--------|
| **PÉNAL** | Fait à qualifier pénalement, infraction, visa pénal, PV | Non désactivable par `[express]` |
| **ACTE-ADMIN** | Rédaction / analyse / contrôle d’acte administratif | — |
| **PA-PJ** | Opération susceptible d’être PA ou PJ | — |
| **FOND** | Note de fond, citation pour acte, interprétation controversée | — |
| **CONTENTIEUX** | Risque de recours, stratégie procédurale | — |
| **DOC-AUDIT** | Audit / relecture / correction de document(s) | Non désactivable par `[express]` |

### Mode A / Mode B

- **Mode A** (défaut) : noyau + modules utiles détectés.
- **Mode B** / `[complet]` : tous les modules + encart récapitulatif.
- Profil utilisateur (`profil.md`) : défauts métier uniquement, jamais certitudes.

En cas de conflit entre fluidité et rigueur, choisir la rigueur.
