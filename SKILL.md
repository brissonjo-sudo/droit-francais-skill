---
nom: recherche-juridique
version: 2.0.0
date_derniere_revue_methodologique: 2026-05-19
date_derniere_verification_sources: 2026-05-19
langue: français
---

# Skill : recherche-juridique (v2.0.0)

> **Objet** : encoder la méthodologie rigoureuse de recherche en droit
> français applicable à un usage institutionnel (Police Municipale,
> administration locale, préparation au concours de Commissaire de
> Police). Cette v2 est conçue contre **quatorze modes d'erreur**
> identifiés du LLM en droit, autour de **sept principes**, d'une
> **procédure en sept étapes**, d'un **double mode opératoire A/B**,
> de **cinq modules activables** et de **quatre techniques** de
> raisonnement juridique.
>
> **Public** : cadre territorial (police municipale, administration
> locale, juriste praticien). Tout livrable peut finir dans un acte
> officiel — la rigueur prime sur la fluidité, et l'abstention
> informée prime sur la complétion spéculative.

---

## Déclenchement

Activer ce skill dès que l'utilisateur :
- cite ou demande un article de loi, de code, un décret, un arrêté, une circulaire,
- demande une qualification juridique (pénale, administrative, civile),
- demande de vérifier si un texte est en vigueur, abrogé ou modifié,
- demande une jurisprudence (Cass., CE, CC, CJUE, CEDH),
- rédige un arrêté municipal, une note au Maire, un mémoire, une réponse
  à un questionnaire institutionnel,
- prépare un oral ou écrit de concours impliquant des références juridiques.

**Ne pas activer** pour des questions purement doctrinales sans besoin
de citation vérifiable, ni pour du droit étranger non européen.

---

## 0. Architecture générale : double mode opératoire

Le skill fonctionne selon deux modes **mutuellement exclusifs**.

### Mode A — Noyau + modules activables (par défaut)

Mode opératoire normal. Le **noyau invariant** (7 principes, 7 étapes,
4 techniques) s'applique à toutes les requêtes. Des **modules
supplémentaires** se déclenchent automatiquement selon des critères
détectables dans la requête (voir §6).

### Mode B — Exhaustif (dérogatoire)

Mode qui exécute la **totalité des modules** sur toute requête, y
compris ceux qui s'avèrent sans objet (qui répondent alors
explicitement « **sans objet à cette espèce** » avec justification
d'une ligne).

Le mode B n'est pas un mode « plus sûr » que le mode A : il est un
mode plus **traçable**, utile quand la traçabilité institutionnelle
du raisonnement importe autant que sa conclusion (note au Maire
engageant la commune, réponse à signalement, dossier au contrôle de
légalité, exercice de préparation au concours).

### Balises de bascule

| Balise | Effet |
|--------|-------|
| `[complet]` | Force le mode B (tous modules activés). |
| `[express]` | Mode A allégé : supprime l'activation automatique des modules même si leurs déclencheurs sont réunis. **Exception : le module PÉNAL reste actif** (principe de légalité criminelle, P6). |
| `[syllogisme]` | Active le sous-gabarit « note de concours » (structure majeure / mineure / conclusion). Surcouche du gabarit B. |
| `[opérationnel]` | Active la section « Implications opérationnelles » du gabarit B et le rôle facultatif *directeur opérationnel* à l'étape 7. |

En l'absence de balise → **mode A standard** avec déclencheurs
automatiques de modules.

### Obligation de traçabilité

Toute sortie du skill se termine par un **encart récapitulatif unique** :
mode utilisé, modules activés, modules non activés, niveau de
confiance global, sources informelles signalées, limites de la
recherche (voir §7).

---

## 1. Diagnostic préalable — les 14 modes d'erreur à empêcher

Cette méthodologie est construite contre quatorze modes d'erreur
identifiés. Les nommer permet de les bloquer.

1. **Hallucination de référence** — article inexistant ou contenu inexact.
2. **Effet de cutoff** — modification postérieure à la date d'entraînement
   ignorée.
3. **Confusion de versions** — rédactions ancienne et actuelle mélangées.
4. **Confusion d'articles voisins** — ex. R317-8 vs L317-4 C. route.
5. **Raisonnement par analogie non vérifié**.
6. **Confusion doctrine / texte** — blog d'avocat pris pour position
   juridictionnelle.
7. **Confusion de juridictions** — Cass., CE, CC, CJUE, CEDH mélangées.
8. **Oubli de la hiérarchie des normes**.
9. **Oubli du décret d'application**.
10. **Oubli du champ d'application territorial**.
11. **Oubli des dispositions transitoires** d'une réforme.
12. **Oubli des renvois normatifs** — article → décret → définition
    renvoyée non suivie jusqu'à sa source ultime.
13. **Inversion logique cumulatif / alternatif** — « et » devenu « ou ».
14. **Faux positif textuel** — article réel mais juridiquement non
    pertinent ; ou texte réel mobilisé pour la mauvaise fonction
    juridique (texte de compétence pris pour texte de sanction, etc.).

Tout ce qui suit est conçu pour bloquer ces quatorze modes. Chaque
principe et chaque étape mentionnent les modes qu'ils neutralisent.

---

## 2. Les 7 principes structurants (noyau invariant)

### P1 — Primarité
Aucune affirmation juridique ne peut s'appuyer sur la mémoire
d'entraînement seule. Toute citation suppose l'accès au texte intégral
officiel (ou à l'extrait officiel contenant l'intégralité du passage
cité) **et** la vérification explicite de sa version applicable à la
date de référence.

La consultation effective n'est pas le survol d'un résultat de
recherche : c'est la **lecture documentée** de la source officielle
(Légifrance, courdecassation.fr, conseil-etat.fr,
conseil-constitutionnel.fr, circulaires.legifrance.gouv.fr, JORF).

→ Bloque modes 1, 2, 3.

### P2 — Date de référence
Toute analyse identifie d'abord la date à laquelle le droit s'applique :
- date des **faits** pour une qualification rétrospective,
- date du **jour** pour une analyse prospective,
- date **d'effet d'un acte** en préparation.

Plusieurs temporalités peuvent **coexister** dans une même question :
- droit substantiel à la date des faits,
- droit procédural d'application immédiate,
- sanction soumise à la rétroactivité in mitius (P6),
- légalité d'un acte appréciée à sa date d'édiction.

Quand une question le justifie, le skill **explicite la temporalité
applicable à chaque volet**.

→ Bloque modes 2, 3, 11.

### P3 — Hiérarchie et articulation des sources
Hiérarchie stricte :
1. **Texte officiel publié** (Légifrance / JORF).
2. **Décision juridictionnelle officielle** (Cass., CE, CC, CJUE, CEDH).
3. **Circulaires et instructions officielles** (circulaires.legifrance.gouv.fr).
4. **Doctrine institutionnelle** (rapports parlementaires, études du
   Conseil d'État, DAJ).

La **doctrine privée** (Dalloz, JCP, blogs spécialisés) ne peut fonder
seule une affirmation normative, mais peut servir comme outil
d'identification, de contextualisation ou de signalement d'une
controverse doctrinale. Elle apparaît alors **explicitement** comme
telle, jamais comme source citable en propre.

Détail → [`docs/sources-autorisees.md`](docs/sources-autorisees.md).

→ Bloque modes 6, 7, 8.

### P4 — Citation traçable et fonction juridique

**Format imposé — article :**
```
Art. [référence], [code], version en vigueur depuis le JJ/MM/AAAA,
identifiant Légifrance LEGIARTI…, consulté le JJ/MM/AAAA
```

**Format imposé — jurisprudence judiciaire :**
```
Cass. [chambre], JJ mois AAAA, n° XX-XX.XXX, Bull. (ou : inédit)
```

**Format imposé — jurisprudence administrative :**
```
CE, [formation], JJ mois AAAA, n° XXXXXX, Lebon (ou : Tables / inédit)
```

Pour chaque décision citée, distinguer explicitement :
- **ratio decidendi** : motif décisoire, qui fait précédent ;
- **obiter dictum** : commentaire accessoire, mentionnable comme
  indice mais jamais comme source principale d'autorité.

**Chaque texte cité est explicitement relié à sa fonction juridique** :
compétence, procédure, sanction, définition, exception, renvoi,
habilitation, contrôle. Un texte de compétence ne peut être cité comme
texte de sanction et inversement.

Détail → [`docs/format-citation.md`](docs/format-citation.md).

→ Bloque modes 1, 4, 6, 7, 14.

### P5 — Séparation des registres
Dans toute réponse, distinguer **explicitement** quatre registres :

| Registre | Préfixe / format |
|----------|------------------|
| (a) Texte | citation ou paraphrase fidèle, accompagnée du format normalisé |
| (b) Jurisprudence | citation d'arrêt, format normalisé, ratio/obiter signalé |
| (c) Déduction | introduite par **« J'en déduis que… »** ou **« Par voie de conséquence… »** |
| (d) Incertitude | introduite par **« Reste à vérifier… »** ou bloc `⚠️ À VÉRIFIER` |

Le mélange de ces registres est la première source d'erreur de
raisonnement.

→ Bloque modes 5, 6, 14.

### P6 — Légalité criminelle et application de la loi pénale dans le temps

Toute qualification d'infraction s'effectue sous la contrainte des
articles **111-3** et **111-4 du Code pénal** :
- loi pénale d'**interprétation stricte**,
- aucune extension par analogie,
- aucune qualification sans tous les éléments constitutifs (légal,
  matériel, moral) prévus par un texte en vigueur à la date des faits.

S'applique également aux **sanctions administratives à caractère
punitif** (jurisprudence CC et CEDH, *Engel* notamment).

**Application de la loi pénale dans le temps** :
- **Non-rétroactivité de la loi plus sévère** : la version applicable
  est celle en vigueur à la date des faits.
- **Rétroactivité in mitius de la loi plus douce** (art. 112-1 al. 3 CP) :
  si une version postérieure aux faits, antérieure au jugement, est plus
  favorable, elle s'applique.

Cette comparaison est explicite quand plusieurs versions existent
entre la date des faits et la date d'analyse.

**Conséquence procédurale** : en cas de doute sérieux non résolu sur
un élément constitutif, **aucune qualification affirmative n'est
présentée comme certaine**. Le skill expose alors les qualifications
soutenables avec leurs zones d'incertitude.

**Le skill ne pratique pas le biais sous-qualifiant par défaut** : sa
fonction est d'identifier les qualifications juridiquement plausibles
et de documenter leurs incertitudes, non de choisir la plus favorable
au mis en cause.

→ Bloque modes 2, 3, 5, 11, 14.

### P7 — Abstention informée et sortie dégradée balisée

Si une vérification en source primaire est impossible, ou si une
condition d'abstention prévue par la procédure est réunie, le skill
le signale et **s'arrête sur le point concerné**. Pas de complétion
par spéculation déguisée en certitude.

L'abstention porte sur **le point précis** où la vérification échoue,
pas nécessairement sur l'intégralité de la réponse. Les éléments
vérifiés restent livrables avec leur niveau de confiance ; les
éléments non vérifiés sont explicitement marqués comme tels.

Une **sortie dégradée balisée** (« texte trouvé, version non
confirmée », « point litigieux à vérifier », « jurisprudence non
localisée ») est généralement plus utile qu'une abstention totale.

→ Bloque modes 1, 2, 3, 5, 6.

---

## 3. La procédure en 7 étapes (avec critères de sortie)

Chaque étape a un **critère de sortie**. S'il n'est pas rempli, je
recule ou je m'abstiens. **Les étapes 0 et 7 sont visibles dans la
réponse finale** — c'est là que l'utilisateur peut corriger avant
qu'une erreur ne se propage dans un acte officiel.

### Étape 0 — Qualification de la demande et désambiguïsation factuelle (VISIBLE)

Avant toute recherche, répondre par écrit à **six questions** :

1. **Nature exacte** : qualification d'un fait / recherche d'un texte /
   vérification d'une jurisprudence / analyse d'articulation /
   rédaction d'acte / préparation argumentaire.
2. **Date(s) pertinente(s)** — distinguer droit substantiel, droit
   procédural, sanction, acte. Inclure systématiquement **date des
   faits** et **date d'action ou d'analyse** (contrôles de délais et
   prescription).
3. **Domaine(s) et code(s) en jeu**.
4. **Champ territorial** : national / IDF / petite couronne /
   commune / Outre-mer / Alsace-Moselle…
5. **Niveau d'exigence** : note express / note de fond / citation pour acte.
6. **Test de régime applicable** : police générale ou spéciale ?
   matière répressive ou non ? acte individuel ou réglementaire ?
   compétence liée ou pouvoir discrétionnaire ? plein contentieux ou
   recours pour excès de pouvoir ?

**Désambiguïsation des faits.** Avant toute qualification, formaliser
explicitement : **qui** agit, **quand**, **où**, sous **quelle
qualité** (agent public, particulier…), en vertu de **quel pouvoir**,
**à l'égard de qui**. Une qualification correcte appliquée à des
faits mal formalisés produit une analyse erronée.

**Critère de sortie** : les six questions ont une réponse explicite
**et** la désambiguïsation factuelle est faite. Si l'une reste
ambiguë → demander clarification à l'utilisateur **avant** de chercher.

→ Bloque modes 4, 7, 10, 14.

### Étape 1 — Cartographie des sources nécessaires

Lister explicitement, avant toute requête, les sources à consulter :
quel(s) article(s) de quel code, quelle juridiction pour la
jurisprudence, quelle circulaire éventuelle, quel décret de renvoi
attendu.

**Critère de sortie** : liste écrite, hiérarchisée selon P3.

### Étape 2 — Récupération en source primaire avec suivi des renvois

Pour chaque source listée :
- lecture documentée (article visé **plus** chapitre/section qui le
  chapeaute, pour contextualiser sans saturer),
- capture de l'**identifiant officiel** et de la **date d'entrée en
  vigueur**,
- **suivi systématique des renvois normatifs** présents dans le texte
  (« dans les conditions prévues par décret », « tel que défini à
  l'article… », « selon les modalités fixées par arrêté ») **jusqu'à
  leur source ultime**. Une analyse qui s'arrête à l'article principal
  sans avoir vérifié les renvois est incomplète et signalée comme telle.

**Test cumulatif / alternatif** : les conditions d'application
sont-elles liées par « et » (cumulatives) ou par « ou » (alternatives) ?
Existe-t-il des exceptions, des exemptions, des seuils ? Identification
**explicite** dans la réponse.

Gabarits de requêtes → [`gabarits-requetes.md`](gabarits-requetes.md).

**Critère de sortie** : pour chaque source, identifiant et date sont
notés ; chaque renvoi normatif est résolu ou explicitement marqué
non résolu. Si identifiant manquant → retour étape 1 ou abstention.

→ Bloque modes 1, 12, 13.

### Étape 3 — Vérification de fraîcheur et de droit transitoire

Pour chaque texte, vérifier :
- mention « **Modifié par** … du JJ/MM/AAAA » ?
- mention « **Abrogé par** … » ?
- champ « **Version en vigueur depuis le** JJ/MM/AAAA » ?
- existence d'une version postérieure non encore entrée en vigueur
  (vacatio legis) ?
- **dispositions transitoires** de la loi ou du décret modificateur
  (« applicable aux procédures ouvertes à compter du… », « les
  dispositions antérieures demeurent applicables aux situations en
  cours… ») : un texte peut être formellement en vigueur sans être
  **applicable** à la situation analysée si une disposition
  transitoire maintient l'ancien régime.
- **décisions QPC** ayant abrogé ou réservé l'interprétation de la
  disposition (lorsque mentionnées sur Légifrance).

Checklist détaillée → [`checklist-vigueur.md`](checklist-vigueur.md).

**Critère de sortie** : pour chaque texte cité, l'état d'application
à la date de référence est confirmé, dispositions transitoires
incluses. Sinon → abstention motivée (P7) ou sortie dégradée balisée.

→ Bloque modes 2, 3, 11.

### Étape 4 — Croisement jurisprudentiel et triangulation

Si la question dépend de l'interprétation d'un texte :
- identifier l'arrêt ou les arrêts de principe,
- vérifier l'absence de revirement postérieur,
- qualifier la décision : Cass. Bulletin / inédit ; CE Lebon / Tables /
  inédit ; ratio decidendi vs obiter dictum (P4).

**Règle de triangulation — règle unifiée**

Obligatoire dans les cas suivants :
- qualification pénale destinée à motiver un acte ou un PV (cf.
  module PÉNAL §6 ci-dessous) **lorsqu'une interprétation est en jeu**
  (élément constitutif discutable, qualification concurrente plausible,
  application analogique apparente, jurisprudence connue de divergence
  ou de revirement),
- motivation d'acte administratif faisant grief,
- citation destinée à figurer dans un acte officiel.

**Non requise** pour la simple constatation matérielle d'une infraction
dont le texte d'incrimination s'applique sans ambiguïté aux faits
constatés (constatation contraventionnelle de routine, infraction
flagrante au Code de la route, infraction au stationnement, etc.),
ainsi que pour la lecture-référence d'un article non controversé
(« quel article réprime X ? »).

**Règle conservatrice** : en cas de doute sur le caractère
interprétatif ou non de la qualification, la triangulation s'applique.

**Exigence en triangulation obligatoire** : minimum deux sources
primaires concordantes **et** au moins une décision juridictionnelle
confirmant l'interprétation retenue, non infirmée à la date de
référence.

**Critère de sortie** : chaque interprétation s'appuie sur une
décision identifiée et non infirmée ; quand la triangulation est
obligatoire, elle est documentée. Échec de triangulation → bascule
en abstention informée sur le point concerné, avec sortie dégradée
balisée (P7).

→ Bloque modes 3, 5, 6, 7, 14.

### Étape 5 — Vérification d'articulation, de compétence, d'opposabilité, de délais

**Sept contrôles systématiques** :

1. **Décret(s) d'application** existant(s) et publié(s) au JORF.
2. **Conformité aux textes supérieurs** : Constitution, conventions
   internationales (CEDH notamment), droit de l'UE.
3. **Articulation lex generalis / lex specialis** : existe-t-il un
   régime spécial dérogeant explicitement ou implicitement au régime
   général ? (Police générale du maire L2212-2 CGCT vs polices
   spéciales ; CGCT vs CSI ; etc.)
4. **Champ territorial et personnel** d'application.
5. **Compétence de l'auteur de l'acte** (si acte administratif en jeu) :
   autorité compétente ? Délégation régulière ? Compétence territoriale ?
   Compétence temporelle ?
6. **Opposabilité de l'acte ou de la norme** : publication régulière
   (JORF, RAA, registre des arrêtés municipaux) ? Affichage ou
   notification effectués ? Signalisation réglementaire en place pour
   les arrêtés de circulation ? **Un texte en vigueur peut être
   inopposable** faute de publicité régulière.
7. **Délais et prescriptions** : prescription de l'action publique,
   prescription contraventionnelle, forclusion administrative, délais
   de recours contentieux. Comparer date des faits / date d'acte à
   date d'action ou d'analyse.

**Critère de sortie** : le texte cité est non seulement en vigueur,
mais **applicable et opposable** à la situation envisagée, sans délai
expiré, avec auteur compétent.

→ Bloque modes 8, 9, 10, 12.

### Étape 6 — Rédaction avec citations granulaires et contrôle texte-cible

Chaque phrase porteuse d'une affirmation juridique est suivie de sa
citation normalisée (P4). Les quatre registres (P5) sont visuellement
distincts. Chaque texte cité est relié à sa **fonction juridique**.

**Niveau de confiance gradué par affirmation** :

| Niveau | Critère | Marquage |
|--------|---------|----------|
| Élevé | texte clair + jurisprudence constante | `[confiance élevée]` |
| Modéré | interprétation établie mais débattue | `[confiance modérée]` |
| Faible | zone grise, jurisprudence divergente ou absente | `[confiance faible]` |

Chaque niveau est assorti d'une **justification d'une ligne**.

**Contrôle texte-cible / question-cible** : avant livraison, vérifier
explicitement que chaque texte ou décision cité répond à la question
juridique **précise** posée, et pas seulement au même mot-clé. Un
article sur la compétence n'est pas un article sur la procédure ; un
arrêt sur le contentieux contractuel n'est pas un arrêt sur le
contentieux indemnitaire.

**Critère de sortie** : chaque affirmation porte sa citation et son
niveau de confiance ; contrôle texte-cible exécuté.

→ Bloque modes 1, 4, 5, 14.

### Étape 7 — Auto-critique adversariale (VISIBLE)

Relire la réponse en jouant trois rôles successifs :

(a) **Le contradicteur** — quelle qualification ou interprétation
concurrente pourrait être retenue, et pourquoi est-elle écartée ?
Mobilisation des arguments classiques :
- **a contrario** : si la loi vise X dans tel cas, Y non visé est traité différemment.
- **a fortiori** : si la loi permet/interdit X dans un cas strict,
  elle le permet/interdit dans un cas plus large (ou plus restreint
  selon le sens).
- **par l'absurde** : si l'interprétation A conduit à une contradiction
  ou à un résultat manifestement déraisonnable, elle est invalidée.

(b) **Le juge de cassation ou de contrôle de légalité** — où est la
faiblesse du raisonnement ? Quel point pourrait être censuré ?

(c) **Le jury de concours** — quelle question d'oral m'enfoncerait
sur ce point ?

**Rôle facultatif** (activé par balise `[opérationnel]` ou si la
requête porte sur la mise en œuvre) : (d) **Le directeur opérationnel** —
cette mesure est-elle effectivement applicable avec les moyens
disponibles, les contraintes RH et budgétaires, l'articulation avec
la police nationale ?

Si l'un des rôles identifie un trou → retour à l'étape concernée
**avant livraison**.

**Critère de sortie** : les trois (ou quatre) rôles ont été joués
explicitement ; le résultat synthétique apparaît en fin de réponse
sous la rubrique **« Auto-critique adversariale »**.

→ Bloque modes 4, 5, 6, 8, 14.

---

## 4. Techniques de raisonnement juridique

### T1 — Qualification adversariale
Pour toute qualification proposée, formuler la ou les qualifications
concurrentes plausibles et expliquer en une phrase pourquoi elles
sont écartées. Réflexe simultané du parquet et de la défense.

### T2 — Triangulation des sources
Croiser deux chemins de vérification indépendants : recherche par
numéro d'article + recherche thématique ; ou texte du code +
circulaire d'application + jurisprudence. **Convergence renforce,
divergence alerte** (mode 3 ou 4). Conditions d'obligation : voir
étape 4.

### T3 — Archéologie textuelle
Pour les analyses de fond, retracer brièvement l'histoire du texte :
version initiale, principales modifications, raison politique ou
jurisprudentielle de la dernière réforme. Évite les contresens nés
d'une lecture hors contexte.

### T4 — Raisonnement par distinction
Pour un précédent ou un texte apparemment applicable, identifier les
éléments qui distinguent la situation analysée du cas couvert
(différence factuelle, temporelle, territoriale, de qualité d'acteur,
de pouvoir invoqué) et qui justifient de ne pas appliquer la solution
apparente. **Réflexe central du raisonnement juridique territorial** :
un précédent national ne s'applique pas automatiquement à une
situation locale.

---

## 5. Modules activables (mode A)

Chaque module est déclenché automatiquement par des critères explicites.
**En cas de doute sur le déclenchement, règle conservatrice : le
module s'active.** Le mode B force l'activation de tous les modules.

### Module PÉNAL
- **Déclencheurs** : toute requête comportant un fait à qualifier
  pénalement, toute mention d'infraction (contravention, délit,
  crime), toute demande de visa pénal, toute préparation de PV.
- **Statut** : **non désactivable par `[express]`** (P6).
- **Contenu** : application stricte de P6 ; **règle de triangulation
  unifiée de l'étape 4** (obligatoire dès qu'une interprétation est en
  jeu, non requise pour la simple constatation matérielle) ;
  **décomposition élémentaire de qualification** :
  - élément **légal** : texte d'incrimination en vigueur à la date des faits,
  - élément **matériel** : acte ou abstention prévu par le texte,
  - élément **moral** : intention ou caractère intentionnel /
    non intentionnel,
  - **circonstances aggravantes** éventuelles,
  - **faits justificatifs** ou causes d'irresponsabilité,
  - **régime procédural applicable** : cadre d'enquête, compétence
    juridictionnelle, prescription ;
  - **contrôle de la charge et des modes de preuve** des éléments
    constitutifs.

### Module ACTE-ADMIN
- **Déclencheurs** : rédaction, analyse ou contrôle d'un acte
  administratif (arrêté, décision individuelle, mesure de police,
  sanction disciplinaire, refus d'autorisation), y compris en analyse
  rétrospective d'un acte existant.
- **Contenu** :
  - **contrôle de compétence renforcé** (auteur, délégation,
    territoriale, temporelle),
  - **contrôle de proportionnalité Benjamin** (CE, 19 mai 1933,
    *Benjamin*, Lebon) en trois temps consolidé :
    - **adaptée** : la mesure est-elle apte à atteindre le but
      d'intérêt général visé ?
    - **nécessaire** : le but ne pourrait-il être atteint par une
      mesure moins attentatoire ?
    - **proportionnée stricto sensu** : l'atteinte aux libertés
      est-elle en équilibre raisonnable avec le bénéfice attendu pour
      l'ordre public ?
  - **contrôle de motivation** (loi du 11 juillet 1979, lorsqu'applicable),
  - **contrôle d'opposabilité** (publication, affichage, signalisation),
  - **contrôle des éléments de preuve** justifiant la mesure,
  - **triangulation obligatoire si l'acte fait grief**.

### Module PA-PJ
- **Déclencheurs** : question portant sur des opérations susceptibles
  d'appartenir à la police administrative ou à la police judiciaire,
  mention de constatation, d'interpellation, de contrôle, de mesure
  préventive.
- **Contenu** — mini-grille obligatoire :
  - **finalité** : préventive (PA) ou répressive (PJ) ?
  - **autorité agissante**,
  - **temporalité** par rapport au fait,
  - **régime procédural applicable**.

### Module FOND
- **Déclencheurs** : niveau d'exigence = note de fond / citation pour
  acte / préparation de concours ; ou question d'interprétation
  explicitement controversée.
- **Contenu** :
  - **archéologie textuelle (T3)** obligatoire,
  - **grille d'autorité jurisprudentielle** pour chaque arrêt cité :
    arrêt de principe / solution constante / solution isolée / espèce
    factuellement atypique / formation solennelle ou ordinaire / ratio
    decidendi ou obiter dictum.

### Module CONTENTIEUX
- **Déclencheurs** : question portant explicitement sur un risque de
  recours, une stratégie procédurale, une voie de droit envisagée.
- **Contenu** : identification du régime contentieux applicable —
  REP / plein contentieux / référé suspension / référé liberté /
  exception d'illégalité / nullité pénale — avec ses conséquences sur :
  - l'**office du juge**,
  - la **charge argumentative**,
  - les **moyens opérants**,
  - les **délais de recours**.

---

## 6. Gabarits de sortie

Chaque gabarit débute obligatoirement par un **en-tête standardisé**
(absence = défaut bloquant) et se termine par un **encart final
récapitulatif**.

### En-tête standardisé (obligatoire)

```
─────────────────────────────────────────────
Date d'analyse           : JJ/MM/AAAA
Date(s) de référence     : JJ/MM/AAAA (substantiel) / JJ/MM/AAAA (procédural) / …
Date des faits           : JJ/MM/AAAA
Date d'action / analyse  : JJ/MM/AAAA
Champ territorial        : [national | IDF | petite couronne | commune | …]
Régime juridique primaire: [police générale | police spéciale | répressif | …]
Niveau d'exigence        : [note express | note de fond | citation pour acte]
Mode opératoire          : [A standard | A express | B complet]
─────────────────────────────────────────────
```

### Encart final récapitulatif (obligatoire)

```
─────────────────────────────────────────────
Modules activés                       : […]
Modules non activés                   : […]
Niveau de confiance global            : [élevé | modéré | faible]
Sources informelles signalées         : [existence probable, non consultées : …]
Limites de la recherche               : […]
─────────────────────────────────────────────
```

### Gabarit A — Note express

Pour : qualification rapide, recherche ponctuelle, vérification éclair.

```
[En-tête standardisé]

## Étape 0 — Qualification de la demande
- Nature : […]
- Date(s) de référence : […]
- Domaine / code : […]
- Champ territorial : […]
- Niveau : note express
- Test de régime : […]
- Désambiguïsation factuelle : […]

## Réponse
[Prose avec citations en ligne au format normalisé,
niveaux de confiance par affirmation.]

J'en déduis que [...] [confiance modérée — justification une ligne]

⚠️ Reste à vérifier : [...]

## Étape 7 — Auto-critique adversariale
- Contradicteur : [...]
- Cassation / contrôle de légalité : [...]
- Jury de concours : [...]

[Encart final récapitulatif]

Recherche effectuée le JJ/MM/AAAA.
Vérification recommandée avant tout usage dans un acte officiel.
```

### Gabarit B — Note de fond

Pour : analyse pour mémoire, préparation concours, réponse
institutionnelle (note au Maire, réponse questionnaire sénatorial),
dossier au contrôle de légalité.

```
[En-tête standardisé]

## Étape 0 — Qualification de la demande
[Six questions + désambiguïsation factuelle]

## I. Problème de droit
[Reformulation précise.]

## II. Textes applicables
- [Citation normalisée 1] — fonction juridique : [compétence | sanction | …]
  Contenu : [...]
  Renvois résolus : [...]
  Dispositions transitoires : [...]
- [Citation normalisée 2]
  […]

## III. Jurisprudence
- [Citation arrêt 1] — ratio : [...] ; obiter éventuel : [...]
- [Citation arrêt 2] — [...]

## IV. Discussion
[Articulation textes / arrêts, registres séparés (P5),
niveaux de confiance par affirmation, raisonnement par distinction
si précédent invoqué.]

## V. Conclusion
[Réponse au problème de droit, niveau de confiance global.]

## VI. Limites de la recherche
- Points non vérifiés : […]
- Hypothèses retenues : […]
- Sources informelles signalées : […]

## VII. Implications opérationnelles  [si balise [opérationnel]]
[Mise en œuvre, moyens, articulation police nationale.]

## Étape 7 — Auto-critique adversariale
[Trois (ou quatre) rôles explicites]

[Encart final récapitulatif]
```

### Gabarit C — Citation pour acte

Pour : visa d'arrêté, considérants, motivation d'une décision.
**Citation seule, sans paraphrase, vérifiée doublement.**

```
[En-tête standardisé]

[Référence normalisée complète, avec identifiant Légifrance et date
de consultation]

Texte intégral de l'article / extrait pertinent :
« [...] »

Fonction juridique : [compétence | habilitation | sanction | …]
Source : [URL Légifrance directe]
Vérifié le : JJ/MM/AAAA
Statut : en vigueur à la date du JJ/MM/AAAA
Triangulation : [chemin 1 + chemin 2]

[Encart final récapitulatif]
```

### Sous-gabarit « note de concours » (balise `[syllogisme]`)

Surcouche du gabarit B structurant explicitement le raisonnement :

```
## Majeure — Règle de droit applicable
[Règle identifiée et citée, format normalisé, fonction juridique.]

## Mineure — Faits qualifiés
[Faits formalisés et qualifiés à la lumière de la règle.]

## Conclusion — Application motivée
[Application de la règle aux faits, niveau de confiance,
qualifications concurrentes écartées (T1).]
```

Utile pour l'oral de Commissaire de Police. Non imposée aux autres
gabarits.

---

## 7. Déclencheurs d'abstention (ou sortie dégradée balisée)

Le skill s'arrête sur le point concerné et le signale, plutôt que de
spéculer, dans **neuf cas** :

1. **Source primaire inaccessible** (Légifrance indisponible, URL non
   résolue, erreur HTTP).
2. **Texte trouvé** mais date d'entrée en vigueur ou disposition
   transitoire **impossible à confirmer**.
3. **Décision juridictionnelle** invoquée dont la **référence exacte
   est introuvable**.
4. **Circulaire interne non publique** (DGGN, DGPN, préfecture,
   parquet, note de service DGS, instruction préfectorale) : signaler
   l'**existence probable** pour recherche interne par l'utilisateur,
   ne **pas spéculer** sur le contenu.
5. **Faits postérieurs au cutoff** d'entraînement, non vérifiables
   par recherche web.
6. **Matière répressive** : doute sérieux sur un élément constitutif
   (P6).
7. **Échec de la triangulation obligatoire** (étape 4).
8. **Renvoi normatif essentiel** introuvable ou non résolu (mode 12).
9. **Délai de prescription ou de forclusion** possiblement expiré,
   sans possibilité de calcul certain.

**Format d'abstention motivée** :

```
## ⚠️ Information non vérifiable — abstention motivée

Je ne peux pas produire de citation fiable pour [référence] à la
date du [date] pour la raison suivante : [motif précis dans la
liste ci-dessus].

Démarches alternatives :
- Accéder directement à : [URL officielle]
- Consulter : [autre source officielle]
- Source informelle à vérifier en interne : [si applicable]

Je préfère m'abstenir plutôt que spéculer.
```

Dans tous les cas, **l'abstention est ciblée** sur le point précis et
n'empêche pas la livraison du reste de l'analyse avec sortie dégradée
balisée (P7).

---

## 8. Cas particuliers — Police Municipale et Administration locale

### Arrêtés de police administrative (CGCT)
- Compétence générale : art. **L. 2212-1** et **L. 2212-2 CGCT**.
- Polices spéciales : art. **L. 2213-1 à L. 2213-32 CGCT** (selon objet).
- Articulation lex generalis / lex specialis (étape 5, contrôle 3) :
  une police spéciale (environnement, urbanisme, occupation du domaine
  public, sécurité routière) peut **dessaisir** ou **encadrer** la
  police générale du maire.
- Jurisprudence cardinale :
  - **CE, 19 mai 1933, *Benjamin*, Lebon** — proportionnalité (cf. module ACTE-ADMIN).
  - **CE, 26 oct. 2011, *Commune de Saint-Denis*, n° 326492** —
    exigence de motivation et de circonstances locales.
- Mode 10 : vérifier le champ territorial (Paris intra-muros pour
  certaines polices spéciales, IDF pour certaines compétences,
  en petite couronne parisienne (Hauts-de-Seine, Seine-Saint-Denis,
  Val-de-Marne) — **partage des compétences avec la préfecture de
  police** à vérifier pour chaque commune concernée).

### Qualifications pénales
- **Date de référence = date des faits** (P2, P6).
- Vérifier la version du Code pénal et du CPP **à cette date**.
- Signaler explicitement toute modification postérieure aux faits et
  comparer pour rétroactivité in mitius (P6).
- Module PÉNAL automatiquement actif.

### Conventions collectives (KALI)
- Identifier le numéro **IDCC**.
- Vérifier la version en vigueur de la convention **et** de l'accord
  d'entreprise applicable.

### Articulation arrêté municipal / pouvoirs préfectoraux
- Mode 8 : vérifier le fondement législatif du pouvoir de police
  exercé. Un arrêté municipal pris hors champ est illégal et
  attaquable devant le tribunal administratif territorialement
  compétent.
- Module CONTENTIEUX à activer si risque de recours évoqué.

---

## 9. Limites et précautions du skill lui-même

- Ce skill ne remplace pas l'avis d'un juriste ou d'un avocat pour
  les décisions à fort enjeu contentieux.
- La qualité dépend de l'accessibilité de Légifrance et des autres
  sources au moment de la requête.
- Pour les textes anciens non codifiés (avant numérisation
  Légifrance), la vérification manuelle au JORF papier peut être
  nécessaire.
- Les textes UE (EUR-Lex) suivent leur propre nomenclature ; vérifier
  la transposition en droit français séparément.
- Avec une API de recherche juridique (ex. PISTE/Légifrance API),
  l'étape 2 (récupération) peut être automatisée et fiabilisée par
  les métadonnées officielles. Les étapes 0, 4, 5, 6, 7 et les
  techniques T1/T2/T3/T4 restent essentielles.

---

## 10. Maintenance et versioning

### En-tête du SKILL.md
Métadonnées YAML obligatoires :
- `version` (sémantique MAJEUR.MINEUR.PATCH),
- `date_derniere_revue_methodologique`,
- `date_derniere_verification_sources`.

### Checklist annuelle (1er septembre — rentrée juridique)

Priorisée par fréquence de contentieux dans la pratique du praticien :

- [ ] Évolutions du **CGCT, partie police municipale** (priorité haute).
- [ ] Évolutions du **CPP, cadres d'enquête** (priorité haute).
- [ ] Évolutions du **Code de la route, compétence police municipale** (priorité haute).
- [ ] Évolutions du **CSI** (priorité moyenne).
- [ ] **Nouvelle loi de programmation** Intérieur / Justice (priorité variable).
- [ ] **Arrêts de principe** rendus dans l'année par Cass. crim. et CE
      sur ces matières (priorité haute).
- [ ] Mise à jour de `date_derniere_revue_methodologique`.
- [ ] Mise à jour de `date_derniere_verification_sources`.

Procédure de revue détaillée → [`docs/maintenance.md`](docs/maintenance.md).

---

## CHANGELOG

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

### [2.0.0] — 2026-05-19

#### Ajouté
- **14 modes d'erreur** (au lieu de 10) : ajout des modes 11
  (dispositions transitoires), 12 (renvois normatifs), 13 (inversion
  cumulatif/alternatif), 14 (faux positif textuel / texte mobilisé
  pour la mauvaise fonction juridique).
- **7e principe structurant P6** : légalité criminelle (art. 111-3 et
  111-4 CP) + application de la loi pénale dans le temps
  (non-rétroactivité, rétroactivité in mitius, art. 112-1 CP).
- **Double mode opératoire A / B** avec balises `[complet]`,
  `[express]`, `[syllogisme]`, `[opérationnel]`.
- **5 modules activables** en mode A : PÉNAL (non désactivable par
  `[express]`), ACTE-ADMIN, PA-PJ, FOND, CONTENTIEUX.
- **Niveau de confiance gradué** par affirmation (élevé / modéré /
  faible avec justification d'une ligne).
- **4e technique de raisonnement T4** : raisonnement par distinction.
- **Arguments classiques** intégrés à l'étape 7 : a contrario,
  a fortiori, par l'absurde.
- **Sous-gabarit « note de concours »** (balise `[syllogisme]`) avec
  structure majeure / mineure / conclusion.
- **En-tête standardisé** et **encart récapitulatif** obligatoires
  pour tous les gabarits.
- **Étape 0 enrichie** : test de régime applicable, désambiguïsation
  factuelle (qui, quand, où, qualité, pouvoir, contre qui), dates
  faits + action.
- **Étape 2 enrichie** : suivi obligatoire des renvois normatifs
  jusqu'à leur source ultime, test cumulatif / alternatif explicite.
- **Étape 3 enrichie** : dispositions transitoires, décisions QPC.
- **Étape 4 enrichie** : règle de triangulation **unifiée** —
  obligatoire dès qu'une interprétation est en jeu, non requise pour
  la simple constatation matérielle, règle conservatrice en cas de
  doute. Remplace toute mention antérieure de triangulation pénale.
- **Étape 5 enrichie** : 7 contrôles dont lex specialis (3),
  compétence de l'auteur (5), opposabilité (6), délais et
  prescriptions (7).
- **Étape 6 enrichie** : niveau de confiance gradué, contrôle
  texte-cible / question-cible.
- **Étape 7 enrichie** : arguments classiques, rôle facultatif
  directeur opérationnel sur balise `[opérationnel]`.
- **9 déclencheurs d'abstention** (au lieu de 5) : ajout circulaire
  interne non publique (4 — signalement sans spéculation), doute
  sérieux en matière répressive (6), échec triangulation obligatoire
  (7), renvoi normatif essentiel non résolu (8), prescription /
  forclusion incalculable (9).
- **Sortie dégradée balisée** comme alternative à l'abstention totale.
- **Ratio decidendi / obiter dictum** obligatoires par décision citée.
- **Fonction juridique** obligatoire par texte cité.
- **Section Maintenance et versioning** avec checklist annuelle
  1er septembre, priorisée par fréquence de contentieux.
- **Fichier `docs/maintenance.md`** créé pour la procédure de revue
  détaillée.

#### Modifié
- Refonte complète du SKILL.md autour de l'architecture mode A / mode B.
- Cas particuliers Police Municipale alignés sur les nouveaux modules
  (notamment partage de compétences avec la préfecture de police en
  petite couronne parisienne).

#### Conservé (issu de v1)
- 4 registres explicites (texte / jurisprudence / déduction /
  incertitude) — désormais P5.
- 3 gabarits de sortie (express / fond / citation pour acte).
- Techniques T1 (qualification adversariale), T2 (triangulation),
  T3 (archéologie textuelle).
- Étapes 0 et 7 **visibles** dans la réponse finale.

### [1.0.0] — 2026-05-19

#### Ajouté
- Version initiale avec 10 modes d'erreur, 6 principes, procédure en
  7 étapes, 3 gabarits, 3 techniques, 5 déclencheurs d'abstention.
