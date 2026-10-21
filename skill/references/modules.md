# Modules activables — détail

> Référencé depuis `SKILL.md §5`. Lire ce fichier dès qu'un module s'active.
> **Règle conservatrice : en cas de doute sur le déclenchement, le module s'active.**
> Le mode B force l'activation de tous les modules.

---

Chaque module est déclenché automatiquement par des critères explicites.
**En cas de doute sur le déclenchement, règle conservatrice : le
module s'active.** Le mode B force l'activation de tous les modules.

### Module PÉNAL

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
  - **contrôle de motivation** (CRPA, art. L.211-2 et s. — anciennement loi
    n° 79-587 du 11 juillet 1979, recodifiée par l'ordonnance n° 2015-1341
    du 23 octobre 2015, en vigueur depuis le 1er janvier 2016 —, lorsqu'applicable),
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

### Module DOC-AUDIT
- **Déclencheurs** : audit, relecture juridique ou correction d'un document
  existant ; contrôle d'un corpus ; reprise d'un document annoncé comme déjà
  audité.
- **Statut** : **non désactivable par `[express]`**. Le précédent audit ne
  réduit pas le périmètre de revérification.
- **Contenu** : lire et exécuter intégralement
  [`audit-documentaire.md`](audit-documentaire.md) : inventaire du corpus,
  registre des affirmations, contrôle en source primaire de 100 % du risque
  élevé, matrice acteur–lieu–propriétaire–pouvoir, double test
  source/conséquence, cohérence interdocuments et contrôle post-correction.
- **Porte bloquante** : ne pas déclarer l'audit achevé si une affirmation à
  risque élevé reste sans vérification, correction ou abstention ciblée.

---

## Déclenchement des six modules

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

| **DOC-AUDIT** | Audit, relecture ou correction juridique d'un ou plusieurs fichiers | Registre des affirmations, risque élevé vérifié à 100 %, matrice acteur–lieu–propriétaire–pouvoir, cohérence du corpus, contrôle post-correction ; non désactivable par `[express]` |
