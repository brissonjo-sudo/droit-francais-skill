# Modules activables — détail (v3.3.0-grok)

Référencé depuis `SKILL.md`. Lire ce fichier dès qu’un module s’active.  
**Règle conservatrice** : en cas de doute sur le déclenchement, le module s’active.  
Le mode B force l’activation de tous les modules.

---

## Module PÉNAL

**Déclencheurs** : toute requête comportant un fait à qualifier pénalement, toute mention d’infraction (contravention, délit, crime), toute demande de visa pénal, toute préparation de PV.

**Statut** : **non désactivable par `[express]`** (principe P6).

**Contenu obligatoire** :
- Application stricte de la légalité criminelle (P6).
- Décomposition élémentaire de la qualification :
  - **élément légal** : texte d’incrimination en vigueur à la date des faits (vérifié sur Légifrance) ;
  - **élément matériel** : acte ou abstention prévu par le texte ;
  - **élément moral** : intention ou caractère intentionnel / non intentionnel ;
  - circonstances aggravantes éventuelles ;
  - faits justificatifs ou causes d’irresponsabilité ;
  - régime procédural applicable (cadre d’enquête, compétence juridictionnelle, prescription) ;
  - contrôle de la charge et des modes de preuve des éléments constitutifs.
- Triangulation (étape 4) obligatoire dès qu’une interprétation est en jeu ; non requise pour la simple constatation matérielle non ambiguë.

---

## Module ACTE-ADMIN

**Déclencheurs** : rédaction, analyse ou contrôle d’un acte administratif (arrêté, décision individuelle, mesure de police, sanction disciplinaire, refus d’autorisation), y compris en analyse rétrospective d’un acte existant.

**Contenu obligatoire** :
- **Contrôle de compétence renforcé** : auteur de l’acte, délégation de signature / de pouvoir, compétence territoriale et temporelle.
- **Contrôle de proportionnalité** (jurisprudence *Benjamin*, CE 19 mai 1933) en trois temps :
  - **adaptée** : la mesure est-elle apte à atteindre le but d’intérêt général visé ?
  - **nécessaire** : le but ne pourrait-il être atteint par une mesure moins attentatoire ?
  - **proportionnée stricto sensu** : l’atteinte aux libertés est-elle en équilibre raisonnable avec le bénéfice attendu pour l’ordre public ?
- **Contrôle de motivation** (CRPA, art. L. 211-2 et s., lorsqu’applicable).
- **Contrôle d’opposabilité** : publication, affichage, signalisation.
- **Contrôle des éléments de preuve** justifiant la mesure.
- **Triangulation obligatoire** si l’acte fait grief (interprétation, articulation de compétences ou proportionnalité en jeu).

---

## Module PA-PJ

**Déclencheurs** : question portant sur des opérations susceptibles d’appartenir à la police administrative ou à la police judiciaire ; mention de constatation, d’interpellation, de contrôle, de mesure préventive.

**Contenu obligatoire** — mini-grille de distinction :

| Critère | Police administrative (PA) | Police judiciaire (PJ) |
|---------|----------------------------|------------------------|
| **Finalité** | Préventive (ordre public) | Répressive (recherche et poursuite d’infractions) |
| **Autorité agissante** | Autorité administrative (maire, préfet, police municipale…) | Autorité judiciaire (OPJ, APJ sous direction du parquet / juge) |
| **Temporalité** | Avant ou indépendamment d’une infraction | À partir d’une infraction constatée ou suspectée |
| **Régime procédural** | Droit administratif (recours, proportionnalité) | Code de procédure pénale (garde à vue, perquisitions, etc.) |

Toujours qualifier explicitement l’opération selon ces quatre critères avant toute analyse de légalité ou de régime applicable.

---

## Module FOND

**Déclencheurs** : niveau d’exigence = note de fond / citation destinée à un acte officiel / préparation de concours ; ou question d’interprétation explicitement controversée.

**Contenu obligatoire** :
- **Archéologie textuelle** (évolution du texte, versions successives, travaux préparatoires si pertinents).
- **Grille d’autorité jurisprudentielle** pour chaque décision citée :
  - arrêt de principe / solution constante / solution isolée ;
  - espèce factuellement atypique ou non ;
  - formation (solennelle / ordinaire / chambre mixte / assemblée plénière…) ;
  - distinction claire **ratio decidendi** vs **obiter dictum**.
- Triangulation renforcée (étape 4) systématique.
- Présentation des divergences éventuelles et de l’état du droit à la date de référence.

---

## Module CONTENTIEUX

**Déclencheurs** : question portant explicitement sur un risque de recours, une stratégie procédurale, une voie de droit envisagée.

**Contenu obligatoire** :
- Identification du **régime contentieux applicable** :
  - REP (recours pour excès de pouvoir)
  - Plein contentieux
  - Référé suspension / référé liberté / référé conservatoire
  - Exception d’illégalité
  - Nullité pénale (le cas échéant)
- Conséquences concrètes sur :
  - l’**office du juge**
  - la **charge argumentative** et la charge de la preuve
  - les **moyens opérants**
  - les **délais de recours** (et éventuelles forclusions)
- Vérification des conditions de recevabilité et d’intérêt à agir à la date de référence.

---

## Module DOC-AUDIT

**Déclencheurs** : audit, relecture juridique ou correction d’un document existant ; contrôle d’un corpus ; reprise d’un document annoncé comme déjà audité.

**Statut** : **non désactivable par `[express]`**. Un audit antérieur ne réduit pas le périmètre de revérification.

**Contenu obligatoire** :
1. **Indépendance** : reprendre depuis les sources primaires toutes les affirmations à risque élevé. Établir un delta temporel si le document est antérieur.
2. **Qualification du livrable** : nature réelle, auteur, destinataires, effet recherché, dates (faits / application / audit). Qualifier par le contenu et les effets, jamais par le seul titre.
3. **Inventaire du corpus** : lister fichiers, versions, annexes, doublons. Séparer faits confirmés / hypothèses / recommandations.
4. **Registre exhaustif des affirmations** : extraire toute proposition juridiquement significative (fichier + emplacement, formulation exacte, registre droit/fait/inférence, niveau de risque, acteur, lieu, pouvoir, source, conséquence revendiquée, état).
5. **Vérification à 100 % du risque élevé** (compétence, qualification d’infraction, peines/montants/délais, contrôles/interpellations/fouilles, accès lieux privés, données personnelles, etc.). Aucun échantillonnage pour le risque élevé.
6. **Matrice acteur–lieu–propriétaire–pouvoir** pour chaque action sensible.
7. **Double test source / conséquence** + cohérence interdocuments.
8. **Contrôle post-correction** : relire le document corrigé pour vérifier qu’aucune affirmation à risque n’a été introduite ou laissée.

Sortie typique : registre des affirmations + liste des corrections + réserves restantes.
