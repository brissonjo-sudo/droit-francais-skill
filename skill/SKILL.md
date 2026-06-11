---
name: recherche-juridique
description: Méthodologie rigoureuse de recherche en droit français (sources
  primaires Légifrance, vérification de vigueur, citation traçable). Active ce
  skill dès que l'utilisateur cite ou demande un article de loi, code, décret,
  arrêté ou circulaire ; demande une qualification pénale ou administrative ;
  demande une jurisprudence (Cass., CE, CC, CJUE, CEDH) ; demande de vérifier
  si un texte est en vigueur, abrogé ou modifié ; rédige un arrêté municipal,
  une note au Maire, un mémoire ou une réponse institutionnelle ; prépare un
  écrit ou oral de concours avec références juridiques. Ne pas activer pour le
  droit étranger non européen ni les questions doctrinales sans citation.
metadata:
  version: 2.2.0
  date_derniere_revue_methodologique: 2026-06-11
  date_derniere_verification_sources: 2026-05-19
  langue: français
---
# Skill : recherche-juridique (v2.2.0)

> **Objet** : encoder la méthodologie rigoureuse de recherche en droit
> français applicable à un usage institutionnel (Police Municipale,
> administration locale, préparation au concours de Commissaire de
> Police). Cette v2 est conçue contre **quatorze modes d'erreur**
> identifiés du LLM en droit, autour de **sept principes**, d'une
> **procédure en sept étapes** (complétée par une **étape 0 bis**
> d'arbitrage des informations manquantes), d'un **double mode
> opératoire A/B**, de **cinq modules activables** et de **quatre
> techniques** de raisonnement juridique.
>
> **Public** : Chef de Service PM / DGA Saint-Ouen-sur-Seine. Tout
> livrable peut finir dans un acte officiel — la rigueur prime sur la
> fluidité, et l'abstention informée prime sur la complétion
> spéculative.

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

**Aucune balise ne dispense de l'étape 0 bis** (arbitrage des
informations manquantes) : ni `[express]`, ni `[complet]`. Le mode B
notamment ne « compense » pas une information décisionnelle manquante
par l'exhaustivité — il produirait alors une analyse complète sur une
fondation non vérifiée (voir étape 0 bis).

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

**Note de v2.1.0.** L'étape 0 bis ajoutée en v2.1.0 ne crée pas un
quinzième mode : elle agit en amont, comme **garde procédurale** qui
empêche de déclencher les modes 10 et 14 (analyse du mauvais régime
ou du mauvais champ territorial sur une hypothèse décisionnelle non
levée). Elle prolonge P2 et P7 au stade de l'entrée.

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

Détail → [`references/sources-autorisees.md`](references/sources-autorisees.md).

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

Détail → [`references/format-citation.md`](references/format-citation.md).

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

**Corollaire d'entrée (v2.1.0).** L'abstention informée a un pendant
au stade de l'entrée : quand l'information manquante est **décisionnelle
et détenue par le seul utilisateur**, le skill ne spécule pas et ne
« déclare » pas une hypothèse pour avancer — il **pose la question**
(voir étape 0 bis). P7 régit la sortie ; l'étape 0 bis régit l'entrée.

→ Bloque modes 1, 2, 3, 5, 6.

---

## 3. La procédure en 7 étapes (avec critères de sortie)

Chaque étape a un **critère de sortie**. S'il n'est pas rempli, je
recule ou je m'abstiens. **Les étapes 0, 0 bis et 7 sont visibles dans
la réponse finale** — c'est là que l'utilisateur peut corriger avant
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
4. **Champ territorial** : national / IDF / Seine-Saint-Denis /
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
ambiguë ou si une information nécessaire manque → **passer à l'étape
0 bis** (arbitrage) **avant** de chercher.

→ Bloque modes 4, 7, 10, 14.

### Étape 0 bis — Arbitrage des informations manquantes (VISIBLE)

Ajoutée en v2.1.0. Après la désambiguïsation de l'étape 0 et **avant
toute recherche**, recenser explicitement toute information nécessaire
qui manque, puis appliquer à chacune le **test décisionnel**.

**Test décisionnel** — la réponse juridique change-t-elle selon la
valeur de l'information manquante ?
- Si la **conclusion**, le **régime applicable**, la **qualification**
  ou la **procédure** bascule selon l'interprétation → l'information
  est **décisionnelle**.
- Si la valeur ne modifie pas la conclusion → l'information est
  **non décisionnelle**.

**Conduite à tenir :**

| Type | Conduite |
|------|----------|
| Décisionnelle | **Question obligatoire** à l'utilisateur. La recherche de fond est suspendue jusqu'à la réponse. |
| Non décisionnelle | **Hypothèse déclarée** explicite, puis poursuite. |

**Clause anti-échappatoire (impérative).** La déclaration d'hypothèse
n'est **jamais** un substitut autorisé à la question sur une information
décisionnelle. Déclarer ouvertement « je suppose X » sur un point dont
on a soi-même reconnu qu'il « commande la réponse » constitue la même
faute que de le supposer en silence — aggravée par la conscience du
problème. **Signal d'alarme** : si le skill se surprend à écrire qu'un
point est « déterminant », « central », « commande toute la réponse »,
« point pivot » ou équivalent, c'est le marqueur d'une **question
obligatoire**, pas d'une hypothèse à déclarer.

**Économie du questionnement** (pour éviter la question rituelle, qui
est elle-même un défaut — complétion spéculative en mode interrogatif) :
- **Pas de question si l'étape 0 est complète** et qu'aucune information
  décisionnelle ne manque. Procéder directement.
- **Une seule question par défaut**, portant sur le point **le plus
  décisionnel**. Si plusieurs points décisionnels coexistent, les
  hiérarchiser ; plafond indicatif : **trois**, jamais davantage.
- **Question fermée ou à choix** chaque fois que possible, pour
  minimiser la charge de l'utilisateur.
- **Réservée à ce que seul l'utilisateur détient.** Si l'information
  est vérifiable en source primaire (Légifrance, etc.), la **chercher**
  au lieu de la demander. La question ne sert pas à se décharger de la
  recherche autonome.

**Esquisse conditionnelle bornée.** Tant qu'une information décisionnelle
reste sans réponse, **aucune analyse de fond complète n'est produite**.
Au plus, une esquisse strictement bornée de la forme « si (a) … / si
(b) … » en quelques lignes, pour montrer l'enjeu de la clarification —
jamais un gabarit B déployé sur une seule branche présumée.

**Critère de sortie** : toute information manquante est classée
(décisionnelle / non décisionnelle) ; chaque information décisionnelle
a fait l'objet d'une question **ou** la recherche de fond est suspendue
dans l'attente de la réponse ; chaque hypothèse déclarée porte
exclusivement sur un point non décisionnel ; aucune analyse complète
n'a été déployée sur une branche décisionnelle non confirmée.

→ Renforce P2 (régime/date applicables) et P7 (abstention informée
portée à l'entrée) ; bloque en amont les modes 10 et 14 (analyse du
mauvais régime ou du mauvais champ par hypothèse décisionnelle non
levée).

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

Gabarits de requêtes → [`references/gabarits-requetes.md`](references/gabarits-requetes.md).

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

Checklist détaillée → [`references/checklist-vigueur.md`](references/checklist-vigueur.md).

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

Chaque module est déclenché automatiquement. **Règle conservatrice : en cas de
doute sur le déclenchement, le module s'active.** Le mode B force tous les modules.

| Module | Déclencheurs | Résumé |
|--------|-------------|--------|
| **PÉNAL** | Fait à qualifier pénalement, infraction, visa pénal, PV | P6 strict, décomposition 3 éléments (légal/matériel/moral), non désactivable par `[express]` |
| **ACTE-ADMIN** | Rédaction/analyse/contrôle acte admin (arrêté, décision individuelle, sanction, refus) | Proportionnalité Benjamin, compétence renforcée, opposabilité, triangulation si acte faisant grief |
| **PA-PJ** | Opération susceptible d'être PA ou PJ (constatation, interpellation, contrôle, mesure préventive) | Mini-grille : finalité / autorité / temporalité / régime procédural |
| **FOND** | Niveau = note de fond / citation pour acte / concours ; ou interprétation controversée | T3 obligatoire, grille autorité jurisprudentielle |
| **CONTENTIEUX** | Risque recours / stratégie procédurale / voie de droit envisagée | Régime contentieux + office juge + charge + moyens + délais |

**Lire [`references/modules.md`](references/modules.md) dès qu'un module s'active.**

---
## 6. Gabarits de sortie

**Gabarit A** — Note express · **Gabarit B** — Note de fond · **Gabarit C** — Citation
pour acte · **Sous-gabarit `[syllogisme]`** — Note de concours (surcouche B).

**Lire [`references/gabarits-sortie.md`](references/gabarits-sortie.md) avant toute rédaction de livrable.**

---
## 7. Déclencheurs d'abstention (ou sortie dégradée balisée)

Le skill s'arrête sur le point concerné et le signale, plutôt que de
spéculer, dans **dix cas** :

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
10. **Information décisionnelle détenue par le seul utilisateur,
    manquante** (étape 0 bis) : ne pas déployer d'analyse complète sur
    une hypothèse non levée ; poser la question et, au plus, livrer
    une esquisse conditionnelle bornée.

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

**Format de clarification motivée (cas n° 10, étape 0 bis)** :

```
## Question préalable nécessaire

Un point conditionne la réponse et je ne peux pas le trancher seul :
[formulation fermée ou à choix de la question].

Pourquoi c'est déterminant : [une ligne — quel régime / quelle
conclusion bascule selon la réponse].

Esquisse conditionnelle (bornée) :
- Si [a] → [orientation en une ou deux lignes].
- Si [b] → [orientation en une ou deux lignes].

Je traite la suite dès que ce point est précisé.
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
  Seine-Saint-Denis / petite couronne — **partage des compétences
  avec la préfecture de police** pour Saint-Ouen).

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
  attaquable devant le TA (TA Montreuil pour Saint-Ouen).
- Module CONTENTIEUX à activer si risque de recours évoqué.

### Répartition des compétences intercommunales (MGP / EPT)
- Champ très réformé (loi NOTRe 2015, loi Engagement et proximité
  2019, loi 3DS 2022) → P1 et étape 3 impératifs.
- **Point d'étape 0 bis typique** : une demande de type « l'EPT veut
  récupérer une compétence, comment la conserver ? » dépend d'une
  information **décisionnelle** détenue par le seul utilisateur — la
  compétence est-elle déjà **statutaire** (le conseil de territoire
  décide seul) ou **supplémentaire** (procédure L. 5211-17 CGCT, les
  communes votent) ? Cette question est **obligatoire** avant toute
  analyse de fond ; la déclarer en hypothèse est interdit (clause
  anti-échappatoire).

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
- Au Palier 3 (API PISTE), l'étape 2 (récupération) sera automatisée
  et fiabilisée par les métadonnées officielles. Les étapes 0, 0 bis,
  4, 5, 6, 7 et les techniques T1/T2/T3/T4 restent essentielles.

---

## 10. Maintenance et versioning

### En-tête du SKILL.md
Métadonnées YAML obligatoires :
- `version` (sémantique MAJEUR.MINEUR.PATCH),
- `date_derniere_revue_methodologique`,
- `date_derniere_verification_sources`.

### Checklist annuelle (1er septembre — rentrée juridique)

Priorisée par fréquence de contentieux dans la pratique de
l'utilisateur :

- [ ] Évolutions du **CGCT, partie police municipale** (priorité haute).
- [ ] Évolutions du **CPP, cadres d'enquête** (priorité haute).
- [ ] Évolutions du **Code de la route, compétence police municipale** (priorité haute).
- [ ] Évolutions du **CSI** (priorité moyenne).
- [ ] **Nouvelle loi de programmation** Intérieur / Justice (priorité variable).
- [ ] **Arrêts de principe** rendus dans l'année par Cass. crim. et CE
      sur ces matières (priorité haute).
- [ ] Mise à jour de `date_derniere_revue_methodologique`.
- [ ] Mise à jour de `date_derniere_verification_sources`.

Procédure de revue détaillée → [`references/maintenance.md`](references/maintenance.md).

---


> Historique complet → [`CHANGELOG.md`](CHANGELOG.md)
