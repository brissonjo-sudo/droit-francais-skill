---
name: recherche-juridique
description: Méthodologie rigoureuse de recherche en droit français — sources primaires Légifrance et Judilibre, vérification de vigueur et d'applicabilité, citations traçables. Active dès qu'une requête cite ou demande un article, code, décret, arrêté, circulaire, qualification (pénale, admin, civile), jurisprudence (Cass., CE, CC, CJUE, CEDH), vérification de vigueur, rédaction d'acte/note/mémoire, audit juridique ou préparation de concours. Ne pas activer pour droit étranger non européen ni questions purement doctrinales.
license: CC-BY-SA-4.0
user-invocable: false
allowed-tools:
  - web_search
  - web_fetch
  - read_file
  - ask_user_question
metadata:
  version: 3.3.0-vibe
  date_derniere_revue_methodologique: 2026-09-05
  date_derniere_verification_sources: 2026-09-04
  langue: français
  adapted_for: vibe
---

# Skill : recherche-juridique (v3.3.0-vibe)

**Objet** : empêcher toute invention de droit français. Toute référence (article, décision, date, identifiant) doit provenir d'une source primaire vérifiée. Abstention informée prime sur complétion spéculative.

Conçu contre les modes d'erreur LLM courants en droit (hallucination d'identifiants, confusion version historique / en vigueur, confusion authenticité / applicabilité, interprétation sans jurisprudence, etc.).

> **⚠️ À LIRE IMPÉRATIVEMENT AVANT TOUTE UTILISATION**
> Ce skill est un **adaptateur** vers le noyau méthodologique universel.
> **Toute analyse juridique DOIT commencer par la lecture intégrale de :**
> → [`../skill/SKILL.md`](../skill/SKILL.md)
>
> **Si le fichier cible est absent ou illisible**, signaler que l'installation est incomplète.
> Ne pas improviser de règle juridique ni d'identifiant officiel pour compenser.

---

## Déclenchement

Activer pour toute demande impliquant :
- citation ou lecture d'article de code/loi/décret/arrêté/circulaire ;
- qualification juridique ;
- vérification de vigueur, abrogation ou modification ;
- jurisprudence officielle ;
- rédaction ou audit d'acte, note, mémoire, conclusions ;
- préparation de concours avec références juridiques.

Ne pas activer pour pure doctrine sans citation, ni droit non européen.

---

## Principes invariants (P1–P7)

**P1 — Primauté des sources.**
Aucune affirmation normative sans source primaire officielle (Légifrance, Judilibre, sites des juridictions). Doctrine privée = outil de repérage uniquement.

**P2 — Date de référence explicite.**
Toujours préciser la date d'évaluation (`as_of`). Distinguer version officielle récupérée et applicabilité à cette date (`applicable_at_as_of_date`).

**P3 — Autorité, authenticité et articulation.**
Ne pas confondre :
1. authenticité de la source ;
2. rang de la norme ;
3. effet d'une décision sur l'application.

Ordre de recherche (pas hiérarchie abstraite) :
1. Textes officiels publiés (Légifrance / JORF)
2. Décisions juridictionnelles officielles (Cass., CE, CC, CJUE, CEDH) — peuvent interpréter, écarter ou neutraliser
3. Circulaires et instructions officielles
4. Doctrine institutionnelle

**P4 — Citation traçable.**
Identifiant officiel + URL canonique + date de version. Pas de citation « article X du Code Y » sans ID ou lien vérifié.

**P5 — Séparation des registres.**
Distinguer clairement :
- (a) Texte (citation exacte, identifiant vérifié)
- (b) Jurisprudence (ratio decidendi vs obiter dictum)
- (c) Déduction (introduite par « J'en déduis que… »)
- (d) Incertitude (introduite par « Reste à vérifier… » ou bloc `⚠️ À VÉRIFIER`)

**P6 — Légalité criminelle stricte.**
En matière pénale : texte d'incrimination + éléments constitutifs exacts ; pas d'analogie ; non-rétroactivité de la loi plus sévère ; rétroactivité in mitius de la loi plus douce (art. 112-1 al. 3 CP).

**P7 — Abstention informée.**
Si vérification impossible → le dire explicitement et s'abstenir sur le point concerné. Pas de « probablement » déguisé en certitude.

---

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

Utiliser en priorité les **outils Vibe natifs** :
- `web_search` avec `site:legifrance.gouv.fr` ou `site:courdecassation.fr`
- `web_fetch` sur les URLs Légifrance pour lecture complète

**Exemples de requêtes optimisées** :
```
site:legifrance.gouv.fr "article L2212-2" CGCT
site:legifrance.gouv.fr code général des collectivités territoriales L2212-2
site:courdecassation.fr "Cass. Crim." 2024
```

Conserver code + date + numéro d'article reconnus dans la requête (ex. « L. 2212-2 CGCT », « article 1240 Code civil au 1er janvier 2010 »).

**Vérifier tout identifiant LEGIARTI fourni avant de le restituer** (règle de provenance, P1).

### Étape 2 — Vérification de vigueur et d'applicabilité

Pour chaque version récupérée :
- noter `version_start_date` / `version_end_date` (si disponibles dans la page)
- évaluer `applicable_at_as_of_date` (date de référence de la question)
- si non applicable → caveat explicite + rechercher la version correcte

Une source officielle peut être historique. `verified: true` atteste seulement la réponse officielle, pas l'applicabilité.

### Étape 3 — Jurisprudence pertinente

Rechercher les décisions qui confirment, contredisent ou précisent l'interprétation.
**Absence de jurisprudence localisable ≠ texte clair devient incertain.** Signaler l'absence ; exiger une décision seulement pour présenter comme établie une interprétation contentieuse.

### Étape 4 — Triangulation (quand requise)

**Obligatoire si :**
- qualification ou élément constitutif discutable ;
- application analogique apparente ;
- jurisprudence divergente connue ;
- citation destinée à un acte officiel portant interprétation.

**Non requise** pour lecture pure d'un texte clair ou constatation matérielle non ambiguë.

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

---

## Échelle de récupération (Vibe)

1. **Outils web officiels** (priorité) —
   `web_search` avec `site:legifrance.gouv.fr` ou domaines juridictionnels,
   `web_fetch` sur les pages articles / codes / décisions.
2. **Sites juridictionnels** —
   `courdecassation.fr`, `conseil-etat.fr`, `conseil-constitutionnel.fr`, `eur-lex.europa.eu`, `echr.coe.int`.
3. **Abstention** si sources inaccessibles ou illisibles → aucune citation inventée.

**Invariant** : la voie de récupération ne modifie jamais l'exigence de provenance (P1).
Un identifiant non récupéré via ces outils **doit être marqué** `⚠️ non vérifié — identifiant non récupéré`.

---

## Outils Vibe disponibles

Noms vérifiés contre le registre public des outils intégrés de Vibe Code
(`mistralai/mistral-vibe`, `vibe/core/tools/builtins/`, au 5 septembre 2026).
Vérifier qu'ils correspondent à la version de Vibe effectivement installée.

| Outil Vibe | Paramètre(s) | Usage | Équivalent noyau | Obligatoire ? |
|------------|--------------|-------|------------------|---------------|
| `web_search` | `query` | Recherche dans Légifrance ou jurisprudence | `scripts/legifrance.py:search()` | ✅ Oui |
| `web_fetch` | `url` | Lecture complète d'une page officielle | `scripts/legifrance.py:article()` | ✅ Oui |

**Exemple d'utilisation combinée** :
```
1. web_search(query="site:legifrance.gouv.fr article L111-1 Code pénal")
2. Pour chaque résultat → web_fetch(url=result.url) pour extraire LEGIARTI, date, texte
3. Si échec → abstention (P7)
```

---

## Intégration Python optionnelle — squelette non connecté

[`tools/legifrance_vibe.py`](tools/legifrance_vibe.py) esquisse un wrapper structuré
autour de `web_search` / `web_fetch` : extraction d'identifiant `LEGIARTI`,
normalisation en dataclasses. **Ce module ne fonctionne pas tel quel** : ses
fonctions ne contiennent aucun appel réel à `web_search` ou `web_fetch` — elles
retournent une liste vide ou un texte vide, silencieusement, sans lever
d'erreur. Rien ne doit s'y fier pour une citation réelle.

Utiliser directement `web_search` et `web_fetch`, comme décrit ci-dessus.
Ce squelette n'a d'intérêt que pour qui veut le compléter — brancher les
appels réels aux emplacements commentés `# Dans Vibe : …` — avant de
l'utiliser en production.

---

## Sources autorisées (résumé)

Voir [`../skill/references/sources-autorisees.md`](../skill/references/sources-autorisees.md) pour le détail.

- **Niveau 1** : Légifrance (codes, lois, décrets…), JORF, EUR-Lex, CEDH.
- **Niveau 2** : Cassation (Judilibre), CE, CC, TA/CAA, CJUE.
- **Niveau 3** : Circulaires Légifrance, bulletins officiels.
- **Doctrine privée** : repérage uniquement, jamais fondement normatif.

---

## Format de sortie minimal

Pour toute citation :
- Identifiant (LEGIARTI… ou n° de pourvoi / décision)
- Titre / numéro d'article
- URL canonique
- Date de version + applicabilité à la date évaluée
- Source (Légifrance / page officielle)

**Exemple** :
```
Art. L. 2212-2, Code général des collectivités territoriales, version en vigueur depuis le 01/01/2024,
identifiant Légifrance LEGIARTI000043183456, consulté le 05/09/2026
[confiance : élevée — texte clair, source officielle confirmée]
```

En cas de doute ou d'échec de vérification :
```
⚠️ Source non confirmée — abstention sur ce point.
Démarches alternatives :
- Accéder directement à : [URL officielle]
- Consulter : [autre source officielle]
```

---

## Notes d'adaptation Vibe

- **Pas de serveur MCP local supposé.** Les outils natifs (`web_search`, `web_fetch`) remplacent les appels PISTE/Judilibre directs.
- **Préférer toujours les domaines officiels** `.gouv.fr` et sites des juridictions.
- **Conserver le code et la date** dans les requêtes de recherche.
- **Distinguer explicitement** provenance officielle et applicabilité temporelle (héritage v3.3.0).
- **Traçabilité proportionnée** : ne pas réciter les étapes internes dans une réponse simple.
- **Règle de provenance stricte** : tout identifiant cité doit provenir d'un appel à `web_search` **suivi** d'un `web_fetch` confirmant l'identifiant sur la page.

---

## Modules activables (mode A)

Chaque module se déclenche automatiquement selon des critères explicites.
**Règle conservatrice** : en cas de doute, le module s'active.
Le mode B / `[complet]` force tous les modules.
`[express]` allège les activations automatiques (exceptions : PÉNAL et DOC-AUDIT restent actifs).

Lire [`../skill/references/modules.md`](../skill/references/modules.md) dès qu'un module s'active.

### Modules disponibles

| Module | Déclencheurs principaux | Statut |
|--------|-------------------------|--------|
| **PÉNAL** | Fait à qualifier pénalement, infraction, visa pénal, PV | Non désactivable par `[express]` |
| **ACTE-ADMIN** | Rédaction / analyse / contrôle d'acte administratif | — |
| **PA-PJ** | Opération susceptible d'être PA ou PJ | — |
| **FOND** | Note de fond, citation pour acte, interprétation controversée | — |
| **CONTENTIEUX** | Risque de recours, stratégie procédurale | — |
| **DOC-AUDIT** | Audit / relecture / correction de document(s) | Non désactivable par `[express]` |

---

## Mode A / Mode B

- **Mode A** (défaut) : noyau + modules utiles détectés.
- **Mode B** / `[complet]` : tous les modules + encart récapitulatif.
- **Profil utilisateur** (`profil.md`) : défauts métier uniquement, jamais certitudes.

En cas de conflit entre fluidité et rigueur, **choisir la rigueur**.

---

## Balises de contrôle

| Balise | Effet |
|--------|-------|
| `[complet]` | Force le mode B (tous modules activés). |
| `[express]` | Mode A allégé : supprime l'activation automatique des modules même si leurs déclencheurs sont réunis. **Exceptions** : PÉNAL reste actif en matière répressive (P6) et DOC-AUDIT reste actif pour tout audit ou correction de documents. |
| `[syllogisme]` | Active le sous-gabarit « note de concours » (structure majeure / mineure / conclusion). |
| `[opérationnel]` | Active la section « Implications opérationnelles » et le rôle *responsable opérationnel* à l'étape 7. |
| `[lookup]` | **Voie rapide** : référence ponctuelle non controversée. Sortie minimale (voir ci-dessous). **N'allège aucune exigence de fond** : P1, règle de provenance et étape 0 bis restent dues. |

### Voie rapide `[lookup]` — sortie minimale

Pour la simple lecture-référence d'un texte non controversé (« quel article réprime X ? », « L. 2212-2 CGCT est-il en vigueur ? »), l'appareil complet est disproportionné. La balise `[lookup]` produit :

```
[Citation normalisée avec identifiant récupéré] — fonction juridique : […]
[Réponse en 1–3 phrases] [confiance : élevée | modérée | faible — 1 ligne]
```

**Garde-fous** : la citation suppose une récupération réelle en source primaire (P1) et un identifiant de provenance vérifiée ; si la récupération échoue, la voie rapide bascule en **abstention motivée** (P7).

---

## Déclencheurs d'abstention

Le skill s'arrête sur le point concerné et le signale dans **dix cas** (voir [`../skill/SKILL.md`](../skill/SKILL.md#7-déclencheurs-dabstention-ou-sortie-dégradée-balisée)) :

1. Source primaire inaccessible
2. Texte trouvé mais date d'entrée en vigueur impossible à confirmer
3. Décision juridictionnelle invoquée dont la référence exacte est introuvable
4. Circulaire interne non publique
5. Faits postérieurs au cutoff d'entraînement, non vérifiables
6. Matière répressive : doute sérieux sur un élément constitutif (P6)
7. Échec de la triangulation obligatoire (étape 4)
8. Renvoi normatif essentiel introuvable ou non résolu
9. Délai de prescription ou de forclusion possiblement expiré
10. Information décisionnelle détenue par le seul utilisateur, manquante (étape 0 bis)

---

## Cas particuliers métier

Défis par le **profil utilisateur** (`profil.md` à la racine du skill).
Voir [`../skill/profils/`](../skill/profils/) pour les profils disponibles (police-gendarmerie, avocat, juriste-entreprise, collectivités, étudiant-concours).

Sans `profil.md` → **profil neutre** : aucun contexte métier n'est présumé.

---

## Maintenance

- **Source de vérité** : [`../skill/SKILL.md`](../skill/SKILL.md) (version 3.3.0)
- **Synchronisation** : Mettre à jour `metadata.version` dans ce fichier à chaque release du noyau (ex: `3.3.0-vibe` → `3.4.0-vibe`)
- **Tests** : Vérifier que les outils Vibe (`web_search`, `web_fetch`) répondent aux exigences P1–P7

---

## Limites

- Ce skill ne remplace pas l'avis d'un juriste ou d'un avocat pour les décisions à fort enjeu contentieux.
- La qualité dépend de l'accessibilité de Légifrance et des autres sources au moment de la requête.
- Pour les textes anciens non codifiés, la vérification manuelle au JORF papier peut être nécessaire.
