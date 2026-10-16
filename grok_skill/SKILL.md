---
name: recherche-juridique
description: Méthodologie rigoureuse de recherche en droit français (sources primaires Légifrance, vérification de vigueur, citation traçable). Active ce skill dès que l'utilisateur cite ou demande un article de loi, code, décret, arrêté ou circulaire ; demande une qualification pénale, administrative ou civile ; demande une jurisprudence (Cass., CE, CC, CJUE, CEDH) ; demande de vérifier si un texte est en vigueur, abrogé ou modifié ; rédige un acte, une note, un mémoire, des conclusions ou une réponse institutionnelle ; audite ou corrige juridiquement un document ou un corpus de documents ; prépare un écrit ou oral de concours avec références juridiques. Ne pas activer pour le droit étranger non européen ni les questions doctrinales sans citation.
metadata:
  version: 3.5.0-grok
  date_derniere_revue_methodologique: 2026-09-14
  date_derniere_verification_sources: 2026-09-04
  langue: français
  adapted_for: grok
---

# Skill : recherche-juridique (v3.5.0-grok)

**Objet** : empêcher toute invention de droit français. Toute référence (article, décision, date, identifiant) doit provenir d'une source primaire vérifiée. Abstention informée prime sur complétion spéculative.

Conçu contre **dix-huit modes d'erreur** du LLM en droit (hallucination de référence, confusion de versions, analogie non vérifiée, oubli de hiérarchie / territorialité / décret d'application, faux positif textuel, etc.). Liste complète : `references/modes-erreur.md`.

## Déclenchement

Activer dès que l'utilisateur :
- cite ou demande un article de loi, de code, un décret, un arrêté, une circulaire ;
- demande une qualification juridique (pénale, administrative, civile) ;
- demande de vérifier si un texte est en vigueur, abrogé ou modifié ;
- demande une jurisprudence (Cass., CE, CC, CJUE, CEDH) ;
- rédige un acte, une note, un mémoire, des conclusions ou une réponse institutionnelle ;
- audite, relit ou corrige juridiquement un document existant ou un corpus ;
- prépare un oral ou écrit de concours impliquant des références juridiques.

**Ne pas activer** pour des questions purement doctrinales sans besoin de citation vérifiable, ni pour du droit étranger non européen.

## Principes invariants (P1–P7)

**P1 — Primarité des sources.** Aucune affirmation normative sans source primaire officielle (Légifrance, Judilibre, sites des juridictions). Doctrine privée = outil de repérage uniquement.

**Règle de provenance (impérative).** Tout identifiant officiel (`LEGIARTI…`, `JORFTEXT…`, `NOR`, n° de pourvoi, n° de requête, n° de décision) doit provenir d'un **appel d'outil de la session courante**. Un identifiant non récupéré est omis ou marqué `⚠️ non vérifié — identifiant non récupéré`. Jamais reconstitué de mémoire.

**P2 — Date de référence explicite.** Toujours préciser la date d'évaluation (`as_of`). Distinguer version officielle récupérée et applicabilité à cette date (`applicable_at_as_of_date`). Une source officielle peut être historique.

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

**P5 — Séparation des registres.** Distinguer clairement :
- (a) texte / paraphrase fidèle
- (b) jurisprudence (ratio / obiter)
- (c) déduction (« J'en déduis que… »)
- (d) incertitude (`⚠️ À VÉRIFIER`)

**P6 — Légalité criminelle stricte et application de la loi pénale dans le temps.**
Texte d'incrimination + éléments constitutifs exacts ; pas d'analogie (art. 111-3 et 111-4 CP).
S'applique aussi aux sanctions administratives à caractère punitif.
- Non-rétroactivité de la loi plus sévère (version à la date des faits).
- Rétroactivité *in mitius* de la loi plus douce (art. 112-1 al. 3 CP) quand applicable.
En cas de doute sérieux non résolu → aucune qualification affirmative présentée comme certaine.

**P7 — Abstention informée.** Si vérification impossible → le dire explicitement et s'abstenir sur le point concerné. Pas de « probablement » déguisé en certitude. L'abstention porte sur le point précis, pas nécessairement sur toute la réponse.

## Procédure (exécutée en interne)

Les contrôles sont obligatoires. Leur affichage est proportionné au livrable :
- réponse courte / `[lookup]` → sources, date applicable, réserves, confiance ;
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

Conserver code + date + numéro d'article reconnus dans la requête.
Vérifier tout identifiant LEGIARTI fourni avant de le restituer.

### Étape 2 — Vérification de vigueur et d'applicabilité

Pour chaque version récupérée :
- noter `version_start_date` / `version_end_date`
- évaluer `applicable_at_as_of_date`
- si non applicable → caveat explicite + rechercher la version correcte

`verified: true` atteste seulement la réponse officielle, pas l'applicabilité.

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

Balises utiles :
- `[lookup]` — voie rapide (référence ponctuelle non controversée, sortie minimale)
- `[express]` — allège les activations automatiques de modules (PÉNAL et DOC-AUDIT restent actifs)
- `[complet]` — mode B (tous modules + encart récapitulatif)

## Notes d'adaptation Grok

- Pas de serveur MCP local ni d'API PISTE. Les outils natifs (`web_search`, `open_page`, `open_page_with_find`, `browser_tab`) remplacent les appels directs.
- Préférer toujours les domaines officiels `.gouv.fr` et sites des juridictions.
- Conserver le code et la date dans les requêtes de recherche.
- Distinguer explicitement provenance officielle et applicabilité temporelle.
- Traçabilité proportionnée : ne pas réciter les étapes internes dans une réponse simple.
- Pas de mécanisme `npx skills` ni de profil.md local supposé ici (le noyau reste la source de vérité pour les profils métier détaillés).

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

Pour le module **DOC-AUDIT**, exécuter intégralement le protocole `references/audit-documentaire.md`.
Deux contrôles obligatoires (nouveauté 3.5.0) déclenchent une **analyse**, pas une conclusion automatique sur la légalité :

**a) Exécution forcée d'office.**
Si un document prévoit ou recommande de couper, retirer, évacuer, détruire, confisquer ou attribuer à la personne publique un bien privé, tester cette opération **séparément** de l'interdiction ou de la sanction qui la précède. Identifier :
1. une habilitation législative expresse **ou** une urgence caractérisée ;
2. à défaut : l'absence d'autre voie de droit ou sanction, la base légale de la décision à exécuter, la résistance de l'intéressé et la stricte nécessité de la mesure.

Une compétence de police, une contravention, un affichage ou une clause locale ne créent pas, à eux seuls, le pouvoir de disposer du bien. Vérifier la jurisprudence et le régime sectoriel avant de conclure.

**b) Montants répressifs.**
Distinguer toujours la classe de contravention, le maximum légal encouru et, si la procédure le permet, l'amende forfaitaire. Vérifier **chacun séparément** ; aucun ne se déduit des autres.

### Mode A / Mode B

- **Mode A** (défaut) : noyau + modules utiles détectés.
- **Mode B** / `[complet]` : tous les modules + encart récapitulatif.

En cas de conflit entre fluidité et rigueur, choisir la rigueur.
