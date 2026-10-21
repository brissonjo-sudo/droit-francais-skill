# Procédure détaillée

Les neuf étapes et leurs critères restent obligatoires. Les gardes et déclencheurs figurent aussi dans le noyau ; lire ici les sections requises avant leur action.

## Procédure et critères de sortie

## 3. La procédure en 9 étapes — 0, 0 bis, 1 à 7 (avec critères de sortie)

Chaque étape a un **critère de sortie**. S'il n'est pas rempli, je recule ou je
m'abstiens. Les étapes sont exécutées en interne. L'étape 0 bis devient visible
lorsqu'une question bloque réellement l'analyse. Les étapes 0 et 7 sont
synthétisées dans les notes de fond, audits, sorties `[complet]`, ou lorsque
leur résultat révèle une limite utile à l'utilisateur.

### Étape 0 — Qualification de la demande et désambiguïsation factuelle

Avant toute recherche, répondre par écrit à **six questions** :

1. **Nature exacte** : qualification d'un fait / recherche d'un texte /
   vérification d'une jurisprudence / analyse d'articulation /
   rédaction d'acte / audit de document ou corpus / préparation argumentaire.

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

#### Échelle de récupération — capacités disponibles, détection silencieuse

La voie de récupération n'est pas un choix soumis à l'utilisateur : elle se
**constate**, par le code de sortie de l'outil.

1. **Outil officiel disponible dans l'environnement** — utiliser en priorité
   le connecteur MCP Légifrance/Judilibre s'il est exposé. Sinon utiliser
   [`scripts/legifrance.py`](../scripts/legifrance.py) : `article` / `search`
   (textes), `ceta` / `constit` (Conseil d'État, Conseil constitutionnel),
   `juri` puis `decision` (jurisprudence judiciaire). Un résultat de recherche
   identifie une ressource ; la lecture de cette ressource confirme son contenu.

2. **Voie de repli web** — outil indisponible ou identifiants PISTE absents :
   basculer sur les gabarits `web_search` / `web_fetch`, domaines officiels
   exclusivement, **sans l'annoncer et sans poser de question**. Demander à
   l'utilisateur s'il dispose d'une clé API est une **question rituelle
   prohibée** (étape 0 bis, économie du questionnement) : l'information est
   constatable par l'outil, donc elle se constate. La clé est un confort,
   jamais une condition d'exercice.

3. **Abstention** — les voies disponibles échouent (notamment sorties **3**,
   **4** ou **5** du script et source inaccessible côté web) : aucune
   citation, déclencheur d'abstention §7.

**Invariant de provenance.** La voie empruntée ne modifie **en rien**
l'exigence P1 : sur la voie de repli comme sur la voie outillée, tout
identifiant cité provient d'une récupération réussie **dans la session
courante**. Le repli dégrade le confort et le déterminisme, **jamais** le
niveau de preuve exigé.

Gabarits de requêtes → [`references/gabarits-requetes.md`](gabarits-requetes.md).

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

**Voie outillée.** Si le connecteur MCP expose `get_article_history`, il
répond aux trois premiers points pour un article de code : toutes les
versions datées, leur état, le texte modificateur de chacune (« Modifié
par ») et la version applicable à la date de référence. Lire les états :
`VIGUEUR_DIFF` = version publiée mais pas encore en vigueur (vacatio
legis) ; `ABROGE_DIFF` = abrogation programmée de la version courante ;
suffixe `_MORT_NE` = version jamais entrée en vigueur, à ne jamais
citer comme droit applicable. Si `modifications_available` vaut
`false`, l'absence de modificateur **n'est pas prouvée** : contrôler la
fiche Légifrance. L'outil ne dispense ni des dispositions transitoires ni
des QPC. **À défaut de cet outil**, les bornes de version et l'applicabilité
renvoyées par la lecture de l'article établissent la version applicable ;
les modificateurs et versions futures se lisent sur la fiche Légifrance
(gabarits de requêtes, §11).

Checklist détaillée → [`references/checklist-vigueur.md`](checklist-vigueur.md).

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
  module PÉNAL (§5 du noyau)) **lorsqu'une interprétation est en jeu**
  (élément constitutif discutable, qualification concurrente plausible,
  application analogique apparente, jurisprudence connue de divergence
  ou de revirement),

- motivation d'un acte administratif faisant grief lorsqu'une interprétation,
  une articulation de compétences ou une mesure de proportionnalité est en jeu,

- citation destinée à un acte officiel lorsqu'elle porte une interprétation
  discutable plutôt que la reproduction d'une règle claire.

**Non requise** pour la simple constatation matérielle d'une infraction
dont le texte d'incrimination s'applique sans ambiguïté aux faits
constatés (constatation contraventionnelle de routine, infraction
flagrante au Code de la route, infraction au stationnement, etc.),
ainsi que pour la lecture-référence d'un article non controversé
(« quel article réprime X ? »).

**Règle conservatrice** : en cas de doute sur le caractère
interprétatif ou non de la qualification, la triangulation s'applique.

**Exigence en triangulation obligatoire** : vérifier la source primaire par
deux chemins indépendants lorsque c'est possible et rechercher la jurisprudence
qui confirme ou contredit l'interprétation. Une décision juridictionnelle est
requise pour présenter comme établie une interprétation contentieuse. L'absence
de jurisprudence localisable est signalée ; elle ne rend pas, à elle seule, un
texte clair juridiquement incertain.

**Critère de sortie** : chaque interprétation contentieuse présentée comme
établie s'appuie sur une décision identifiée et non infirmée ; quand la
triangulation est obligatoire, elle est documentée. Échec de triangulation →
bascule en abstention informée sur le point concerné, avec sortie dégradée
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

**Contrôle source / conséquence** : vérifier en deux temps que (a) la
source contient la proposition invoquée et que (b) cette proposition
autorise exactement la conséquence écrite, pour cet acteur, ce lieu, ce
propriétaire, cette date et cette opération. Une citation exacte ne valide
jamais, à elle seule, la phrase qui la porte.

**Contrôle de provenance (P1)** : avant livraison, vérifier que chaque
identifiant officiel cité (`LEGIARTI`, `JORFTEXT`, `NOR`, n° de
pourvoi, n° de requête, n° de décision) a bien été **récupéré par un
appel d'outil dans la session**. Tout identifiant sans provenance est
retiré ou marqué `⚠️ non vérifié — identifiant non récupéré`. Aucun
gabarit C n'est produit sur un identifiant non récupéré.

En route DOC-AUDIT, exécuter en outre le contrôle post-correction prévu par
`references/audit-documentaire.md` et consigner les divergences
interdocuments résolues ou encore ouvertes.

**Critère de sortie** : chaque affirmation porte sa citation et son
niveau de confiance ; contrôles texte-cible, source/conséquence et
provenance exécutés ; en audit, contrôle post-correction exécuté.

→ Bloque modes 1, 4, 5, 14.

### Étape 7 — Auto-critique adversariale

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

(c) **Le 3ᵉ regard défini par le profil actif** (section 4 de `profil.md`) —
p. ex. l'avocat de la défense (police-gendarmerie), le confrère adverse
(avocat), le contrôle de légalité (collectivités), le régulateur
(juriste-entreprise), le jury (étudiant-concours). **Sans profil** : le
contradicteur qualifié secondaire — « quelle autre lecture, quelle
objection un praticien adverse opposerait-il ? »

**Rôle facultatif** (activé par balise `[opérationnel]` ou si la
requête porte sur la mise en œuvre) : (d) **Le responsable opérationnel** —
cette mesure est-elle effectivement applicable avec les moyens
disponibles, les contraintes RH et budgétaires, l'articulation avec
les autres services ?

Si l'un des rôles identifie un trou → retour à l'étape concernée
**avant livraison**.

**Critère de sortie** : les trois rôles ont été joués. Leur résultat apparaît
si une objection subsiste ou dans une note de fond, un audit ou une sortie
`[complet]`. Une réponse simple ne porte pas une rubrique vide ou rituelle.

→ Bloque modes 4, 5, 6, 8, 14.
