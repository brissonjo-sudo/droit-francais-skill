---
name: recherche-juridique
description: Méthodologie rigoureuse de recherche en droit français (sources
  primaires Légifrance, vérification de vigueur, citation traçable). Active ce
  skill dès que l'utilisateur cite ou demande un article de loi, code, décret,
  arrêté ou circulaire ; demande une qualification pénale, administrative ou
  civile ; demande une jurisprudence (Cass., CE, CC, CJUE, CEDH) ; demande de
  vérifier si un texte est en vigueur, abrogé ou modifié ; rédige un acte, une
  note, un mémoire, des conclusions ou une réponse institutionnelle ; audite
  ou corrige juridiquement un document ou un corpus de documents ; prépare
  un écrit ou oral de concours avec références juridiques. Ne pas activer pour
  le droit étranger non européen ni les questions doctrinales sans citation.
metadata:
  version: 3.6.0
  date_derniere_revue_methodologique: 2026-09-14
  date_derniere_verification_sources: 2026-09-04
  langue: français
---
# Skill : recherche-juridique (v3.6.0)

Rigueur et abstention informée avant spéculation ; profil métier sans certitude.
Résoudre les ressources depuis la racine `skill/`. Référence requise illisible :
arrêter le point dépendant sans en inventer le contenu.

## Déclenchement

Activer ce skill dès que l'utilisateur :
- cite ou demande un article de loi, de code, un décret, un arrêté, une circulaire,
- demande une qualification juridique (pénale, administrative, civile),
- demande de vérifier si un texte est en vigueur, abrogé ou modifié,
- demande une jurisprudence (Cass., CE, CC, CJUE, CEDH),
- rédige un acte, une note, un mémoire, des conclusions ou une réponse
  institutionnelle,
- audite, relit ou corrige juridiquement un document existant ou un corpus,
- prépare un oral ou écrit de concours impliquant des références juridiques.

**Ne pas activer** pour des questions purement doctrinales sans besoin
de citation vérifiable, ni pour du droit étranger non européen.

## Mise à jour — contrôle par session, automatique sur option

Au premier déclenchement, hors automatique et si npx est accessible :
contrôle discret `npx skills check`, une fois par session.
Jamais avant une réponse urgente ou une simple clarification. Si le skill est
périmé, le signaler en une phrase et poursuivre ; la commande proposée est
`npx skills update recherche-juridique`. Échec, absence de suivi ou contrôle
négatif : aucune relance ni alourdissement de la réponse. Une installation
gérée par un hôte/marketplace suit son mécanisme, pas une commande universelle.
Ne lancer aucune mise à jour de sa propre initiative hors option explicite.

### Mode automatique explicite

Installation globale suivie par skills seulement : option locale non versionnée
`.recherche-juridique-update.json`, `{"automatic": true}`. Au premier usage
après 24 heures, `scripts/update_skill.py` remplace le contrôle manuel ; il
préserve profil.md et scripts/.env. Échec ou périmètre ambigu : poursuivre sans
mise à jour. Pour désactiver : `{"automatic": false}` ou retrait du fichier.

Installation gérée par le CLI skills : lire [Mise à jour de l'installation](references/maintenance.md#mise-à-jour-de-linstallation) avant toute mise à jour autorisée. Pour une revue du skill, lire [Maintenance et métadonnées du noyau](references/maintenance.md#maintenance-et-métadonnées-du-noyau).

## 0. Architecture générale : double mode opératoire

Avant analyse, lire `profil.md` s'il existe à la racine du skill : contexte,
domaines et troisième regard sont des **défauts**, supplantés par la requête
et rouverts par 0 bis s'ils deviennent décisionnels. Aucun contrôle n'en est
dispensé. Sans profil : neutralité, aucun territoire ni métier supposé.

A, par défaut : noyau et modules déclenchés. B, exclusif de A : tous modules,
y compris « sans objet à cette espèce » motivé en une ligne. B augmente la
traçabilité, sans remplacer une vérification ni combler un fait manquant.

| Balise | Effet et limites |
|---|---|
| `[complet]` | B, tous modules. |
| `[express]` | A sans activation automatique, sauf PÉNAL en matière répressive et DOC-AUDIT pour audit/correction. |
| `[syllogisme]` | Sous-gabarit concours majeure/mineure/conclusion, surcouche B. |
| `[opérationnel]` | Implications opérationnelles du gabarit B et quatrième regard de l'étape 7. |
| `[lookup]` | Référence ponctuelle non controversée, sans en-tête/encart ; P1, provenance et 0 bis restent dus. |

Sans balise : A standard. Lookup : citation normalisée, fonction juridique,
réponse en 1–3 phrases et confiance motivée. Interprétation, qualification
pénale, acte ou doute sur l'absence de controverse : revenir en A standard.
Échec de récupération : abstention ciblée. Aucune balise ne dispense de 0 bis.
Les contrôles sont internes ; sources, date, réserves et confiance sont visibles.
Fond, audit ou complet : ajouter encart et synthèse utile des étapes 0 et 7.

Pour configurer un profil ou résoudre une combinaison de balises, lire [Modes et profils](references/modes-et-profils.md).
Avant une sortie [lookup], lire [Voie rapide lookup](references/gabarits-sortie.md#voie-rapide-lookup) ; avant rédaction, lire les règles communes et le gabarit applicable de [Gabarits de sortie](references/gabarits-sortie.md).

## 1. Diagnostic préalable — les 18 modes d'erreur à empêcher

Repères : 1 référence ; 2 cutoff ; 3 versions ; 4 articles voisins ;
5 analogie ; 6 doctrine/texte ; 7 juridictions ; 8 hiérarchie ; 9 décret ;
10 territoire ; 11 transition ; 12 renvois ; 13 cumulatif/alternatif ;
14 faux positif ; 15 audit hérité ; 16 conséquence ;
17 acteur–lieu–propriétaire–pouvoir ; 18 corpus.

Pour diagnostiquer un échec ou consulter les exemples des modes 1 à 18, lire [Modes d'erreur](references/modes-erreur.md).

## 2. Les 7 principes structurants (noyau invariant)

### P1 — Primarité
Aucune affirmation juridique sur la seule mémoire. Lire le texte officiel,
ou l'extrait officiel couvrant tout le passage cité, et vérifier sa version
applicable. Un résultat de recherche seul ne suffit pas. Tout identifiant
officiel restitué doit être récupéré par outil **dans la session courante**,
selon l'ordre normé de l'étape 2. Sinon : omettre ou marquer
`⚠️ non vérifié — identifiant non récupéré` ; aucun gabarit C.
Procédure affichée sans récupération : défaut bloquant, pas preuve.
Absence de PISTE ou repli web : même niveau de preuve exigé.

### P2 — Date de référence
Fixer les dates des faits, de l'analyse/action et de l'acte ; distinguer les
temporalités substantielle, procédurale et de sanction. Expliciter celle de
chaque volet quand elles coexistent ; ne pas confondre vigueur et applicabilité.

### P3 — Autorité, authenticité et articulation des sources
Distinguer authenticité, rang et effet d'une décision. Rechercher textes,
décisions, circulaires/instructions officielles, puis doctrine institutionnelle ;
ce n'est pas une hiérarchie où le texte primerait toujours sur son contrôle.
Doctrine privée : piste transparente, jamais fondement normatif autonome.

Avant de choisir ou d'évaluer une source, lire les sections pertinentes de [Sources autorisées](references/sources-autorisees.md).
Avant de confirmer l'applicabilité, lire [Temporalités de référence](references/checklist-vigueur.md#temporalités-de-référence) et la checklist de vigueur adaptée au livrable.

### P4 — Citation traçable et fonction juridique
Citation normalisée par affirmation, identifiant/date de version/consultation
selon le format ; distinguer ratio et obiter, jamais obiter comme autorité
principale. Relier chaque texte à sa fonction : compétence, procédure, sanction,
définition, exception, renvoi, habilitation ou contrôle ; ne pas les confondre.

Avant toute citation, lire le format applicable et [Fonction juridique de chaque référence](references/format-citation.md#fonction-juridique-de-chaque-référence).

### P5 — Séparation des registres
Séparer texte, jurisprudence, déduction (« J'en déduis que… » ou « Par voie de
conséquence… ») et incertitude (« Reste à vérifier… » ou `⚠️ À VÉRIFIER`).

Avant rédaction, appliquer [Registres de restitution](references/gabarits-sortie.md#registres-de-restitution).

### P6 — Légalité criminelle et application de la loi pénale dans le temps
Interprétation stricte, sans analogie ; vérifier tous les éléments légal,
matériel et moral à la date des faits. Inclure les sanctions administratives
punitives. Comparer les versions : pas de rétroactivité plus sévère ; loi plus
douce postérieure aux faits et antérieure au jugement prise en compte.
Doute sérieux non résolu : aucune qualification certaine ; exposer les options
plausibles et leurs incertitudes, sans biais sous-qualifiant par défaut.

En matière répressive ou de sanction punitive, lire [Module PÉNAL](references/modules.md#module-pénal) avant de qualifier ou sanctionner.

### P7 — Abstention informée et sortie dégradée balisée
Vérification impossible : arrêter le point précis, sans spéculation ; livrer
le reste vérifié avec réserves et confiance. Une sortie dégradée balisée vaut
mieux qu'une certitude inventée. Une donnée décisionnelle détenue seulement
par l'utilisateur impose une question, pas une hypothèse déclarée (0 bis).

Pour restituer un point non vérifiable ou une clarification bloquante, lire [Abstention ciblée et clarification](references/gabarits-sortie.md#abstention-ciblée-et-clarification).

## 2 bis. Route obligatoire — audit ou correction de documents existants

Toute demande d'audit, de relecture ou de correction juridique active DOC-AUDIT, même sous [express] : lire et exécuter intégralement [Audit documentaire](references/audit-documentaire.md) avant toute correction ou conclusion d'audit.
Qualifier livrables/dates ; inventorier le corpus ; tenir le registre des
affirmations ; vérifier 100 % du risque élevé ; construire la matrice
acteur–lieu–propriétaire–pouvoir ; séparer source et conséquence ; réconcilier
les fichiers ; rechercher les résidus après correction. Un audit antérieur
est du contexte, jamais une conformité héritée. Clôture interdite tant que le
risque élevé n'est pas vérifié/corrigé ou non vérifiable avec abstention ciblée.

## 3. La procédure en 9 étapes — 0, 0 bis, 1 à 7 (avec critères de sortie)

Exécuter les neuf étapes ; critère non rempli : retour ou abstention. Les étapes
sont internes, sauf question bloquante de 0 bis et restitutions utiles au livrable.

### Étape 0 — Qualification de la demande et désambiguïsation factuelle
Avant recherche, fixer explicitement : nature exacte, dates pertinentes
(faits et action/analyse incluses), domaines/codes, champ territorial, niveau
du livrable, régime applicable. Désambiguïser qui/quand/où/qualité/pouvoir/
destinataire. Sortie : six réponses explicites et faits formalisés ; sinon 0 bis.

### Étape 0 bis — Arbitrage des informations manquantes (VISIBLE)
Recenser avant recherche les informations nécessaires manquantes. Si conclusion,
régime, qualification ou procédure change selon leur valeur : décisionnelles,
question obligatoire et fond suspendu. Sinon seulement : hypothèse déclarée.
Dire « je suppose » ne remplace jamais la question sur un point déterminant.
Sans manque décisionnel : aucune question rituelle. Chercher ce qui est
vérifiable en source primaire ; demander seulement ce que l'utilisateur détient.
Une question, la plus décisionnelle, par défaut ; plusieurs points hiérarchisés,
plafond indicatif trois, jamais davantage ; forme fermée/à choix si possible.
Attente : au plus esquisse bornée « si a / si b », aucune analyse complète sur
une branche présumée. Sortie : chaque manque classé, hypothèses non décisionnelles,
questions posées et fond suspendu jusqu'aux réponses nécessaires.

Si une donnée manque ou demeure ambiguë, lire [Étape 0 bis — Arbitrage des informations manquantes (VISIBLE)](references/procedure-detaillee.md#étape-0-bis--arbitrage-des-informations-manquantes-visible) avant toute recherche de fond.

### Étape 1 — Cartographie des sources nécessaires
Lister les articles/codes, juridictions, circulaires et décrets attendus.
Sortie : liste écrite hiérarchisée selon P3 avant toute requête.

### Étape 2 — Récupération en source primaire avec suivi des renvois
Ordre constaté par l'outil, sans demander de clé : MCP officiel disponible,
sinon script ; à défaut web officiel, silencieusement ; si les voies échouent,
abstention. Lire texte et chapitre/section ; relever identifiant et date de
version ; suivre les renvois jusqu'au terme ; distinguer et/ou, exceptions,
exemptions et seuils. Sortie : identifiant/date notés, renvois résolus ou balisés ;
identifiant absent : retour étape 1 ou abstention. Le repli ne baisse pas P1.

Avant la première requête, lire les étapes 1 et 2 de [Procédure détaillée](references/procedure-detaillee.md) ; pour la syntaxe d'une requête, consulter [Gabarits de requêtes](references/gabarits-requetes.md).

### Étape 3 — Vérification de fraîcheur et de droit transitoire
Contrôler modification, abrogation, début de version, version future, transitions
et QPC. Sortie : application confirmée à la date utile, transitions incluses ;
sinon abstention ou sortie dégradée balisée.

Avant de conclure sur la vigueur ou les transitions, lire l'étape 3 de [Procédure détaillée](references/procedure-detaillee.md) et [Checklist de vigueur](references/checklist-vigueur.md).

### Étape 4 — Croisement jurisprudentiel et triangulation
Si interprétation : arrêts de principe, absence de revirement, autorité et
ratio/obiter. Triangulation obligatoire pour : qualification pénale destinée
à acte/PV avec interprétation ; acte administratif faisant grief avec
interprétation, compétence ou proportionnalité en jeu ; citation pour acte
portant une interprétation discutable. Non requise pour constatation matérielle
non ambiguë ni lecture d'un article non controversé. En cas de doute, appliquer.
Vérifier par deux chemins indépendants si possible ; rechercher décisions
confirmant ou contredisant. Interprétation contentieuse présentée comme établie :
décision identifiée non infirmée requise. Absence de décision localisée signalée,
sans rendre incertain un texte clair. Sortie : interprétation établie soutenue
et triangulation obligatoire documentée ; échec : abstention sur ce point.

Si une interprétation ou une triangulation est en jeu, lire l'étape 4 de [Procédure détaillée](references/procedure-detaillee.md) avant de présenter l'interprétation comme établie.

### Étape 5 — Vérification d'articulation, de compétence, d'opposabilité, de délais
Sept contrôles : décrets publiés ; normes supérieures ; général/spécial ; champs
territorial/personnel ; compétence et délégation ; publicité/notification/
signalisation et opposabilité ; délais/prescriptions comparant faits/acte à
action/analyse. Sortie : texte applicable et opposable, auteur compétent et
délai non expiré, pas seulement en vigueur.

Avant de conclure sur un pouvoir, un acte ou un délai, lire l'étape 5 de [Procédure détaillée](references/procedure-detaillee.md).

### Étape 6 — Rédaction avec citations granulaires et contrôle texte-cible
Chaque affirmation : citation, fonction et confiance justifiée en une ligne
(élevée : texte clair + jurisprudence constante ; modérée : interprétation établie
mais débattue ; faible : zone grise/divergence/absence). Séparer les registres.
Vérifier la question-cible exacte, puis source contenant la proposition ET
conséquence autorisée pour cet acteur/lieu/propriétaire/date/opération.
Chaque identifiant doit avoir sa provenance de session ; sinon retrait ou
marquage, jamais gabarit C. En audit : post-correction et divergences consignés.
Sortie : tous ces contrôles exécutés, citations et confiance par affirmation.

### Étape 7 — Auto-critique adversariale
Jouer contradicteur, juge de cassation/contrôle de légalité, troisième regard
du profil §4 ou contradicteur secondaire neutre ; ajouter responsable
opérationnel si balise ou mise en œuvre. Si trou : retour avant livraison.
Sortie : trois rôles joués ; résultat visible si objection, fond, audit ou
complet ; aucune rubrique vide dans une réponse simple.

Avant livraison, appliquer les étapes 6 et 7 de [Procédure détaillée](references/procedure-detaillee.md) et les règles communes de [Gabarits de sortie](references/gabarits-sortie.md).

## 4. Techniques de raisonnement juridique

### T1 — Qualification adversariale
Pour chaque qualification, options concurrentes plausibles et motif d'exclusion.
### T2 — Triangulation des sources
Chemins indépendants ; convergence renforce, divergence alerte ; obligation : étape 4.
### T3 — Archéologie textuelle
Pour le fond, histoire du texte et contexte de la dernière réforme.
### T4 — Raisonnement par distinction
Avant transposer, distinguer faits, date, territoire, qualité d'acteur et pouvoir.

Avant d'écarter une qualification concurrente ou de transposer un précédent, lire T1 et T4 de [Techniques de raisonnement](references/techniques-raisonnement.md) ; pour triangulation ou note de fond, lire aussi T2 ou T3 selon leur déclencheur.

## 5. Modules activables (mode A)

Déclenchement automatique ; doute = activer ; B force tous les modules.

| Module | Déclencheurs / garde |
|---|---|
| PÉNAL | Qualification, infraction, visa pénal, PV ; non désactivable par express. |
| ACTE-ADMIN | Rédaction, analyse ou contrôle d'acte administratif. |
| PA-PJ | Opération susceptible d'être administrative ou judiciaire. |
| FOND | Fond, citation pour acte, concours ou interprétation controversée. |
| CONTENTIEUX | Risque de recours, stratégie ou voie de droit envisagée. |
| DOC-AUDIT | Audit, relecture ou correction juridique de fichiers ; non désactivable par express. |

## 6. Gabarits de sortie

A : express ; B : fond ; C : citation pour acte ; D : audit ; syllogisme :
surcouche concours de B. En-tête et encart selon le livrable ; lookup exempt.
Dans une réponse, citer les fichiers de skill/référence par nom du skill et
section, sans lien Markdown ni chemin relatif/absolu. Liens de réponse :
sources officielles uniquement. Les liens de chargement internes ne sont pas
des citations à reproduire dans le livrable.

Lire [Modules](references/modules.md) dès qu'un module s'active. Lire les règles communes et le gabarit applicable de [Gabarits de sortie](references/gabarits-sortie.md) avant toute rédaction de livrable.

## 7. Déclencheurs d'abstention (ou sortie dégradée balisée)

Arrêter et signaler le point précis dans ces dix cas :
1. Source primaire inaccessible.
2. Texte trouvé, entrée en vigueur ou transition non confirmable.
3. Référence exacte de décision introuvable.
4. Circulaire interne non publique : existence probable à rechercher, contenu non spéculé.
5. Faits après cutoff sans vérification web possible.
6. Doute sérieux non résolu sur élément constitutif répressif.
7. Triangulation obligatoire échouée.
8. Renvoi normatif essentiel non résolu.
9. Prescription/forclusion possiblement expirée sans calcul certain.
10. Donnée décisionnelle détenue par l'utilisateur manquante : question,
    fond suspendu et au plus esquisse conditionnelle bornée.

L'abstention ciblée n'empêche pas de livrer le reste vérifié avec réserves.
Formats de refus et clarification : référence « Abstention ciblée et clarification ».

## 8. Cas particuliers métier — définis par le profil

Appliquer la section 5 du profil chargé ; sans profil, ne présumer aucun cas
métier. Les particularités territoriales universelles restent dues à l'étape 5
et à la checklist de vigueur. Contexte décisionnel absent : 0 bis, pas d'hypothèse.

## 9. Limites et précautions du skill lui-même

Fort enjeu contentieux : juriste/avocat. Sources accessibles requises ; textes
anciens : parfois JORF papier ; UE : transposition française séparée. API et
métadonnées ne remplacent ni applicabilité ni raisonnement ; voies : étape 2.

## 10. Maintenance et versioning

Version sémantique et deux dates de métadonnées distinctes : revue et vérification.
Veille annuelle selon domaines du profil ; procédure dans maintenance.md.
Historique complet : [CHANGELOG](CHANGELOG.md).
