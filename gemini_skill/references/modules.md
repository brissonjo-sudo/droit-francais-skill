# Modules activables — détail (v3.3.0-gemini)

Référencé depuis `SKILL.md`. Lire ce fichier dès qu’un module s’active.  
**Règle conservatrice** : en cas de doute sur le déclenchement, le module s’active.  
Le mode B (`[complet]`) force l’activation de tous les modules.

---

## Module PÉNAL

**Déclencheurs** : toute requête comportant un fait à qualifier pénalement, toute mention d’infraction (contravention, délit, crime), toute demande de visa pénal, toute préparation de procès-verbal ou plainte.

**Statut** : **non désactivable par `[express]`** (principe P6 de légalité criminelle stricte).

**Contenu obligatoire** :
- Application stricte de la légalité criminelle (P6 : pas d'analogie défavorable, interprétation stricte).
- Décomposition élémentaire de la qualification :
  - **élément légal** : texte d’incrimination et de pénalité en vigueur à la date exacte des faits (vérifié en source primaire sur Légifrance) ;
  - **élément matériel** : acte positif ou abstention caractérisée requis par le texte ;
  - **élément moral** : intention dolosive (dol général / dol spécial) ou faute non intentionnelle (imprudence, négligence, manquement délibéré) ;
  - circonstances aggravantes éventuelles ;
  - faits justificatifs (légitime défense, état de nécessité, ordre de la loi, commandement de l'autorité légitime) ou causes d’irresponsabilité (trouble psychique, contrainte, erreur de droit invincible) ;
  - régime procédural applicable : cadre d’enquête (flagrance, préliminaire), compétence juridictionnelle, prescription de l'action publique ;
  - contrôle de la charge et des modes de preuve des éléments constitutifs.
- Triangulation (étape 4) obligatoire dès qu’une interprétation ou une qualification concurrente est en jeu ; non requise pour la simple constatation matérielle non ambiguë.

---

## Module ACTE-ADMIN

**Déclencheurs** : rédaction, analyse ou contrôle d’un acte administratif unilatéral ou réglementaire (arrêté municipal ou préfectoral, décision individuelle, mesure de police, sanction disciplinaire, refus d’autorisation), y compris en audit rétrospectif d’un acte existant.

**Contenu obligatoire** :
- **Contrôle de compétence renforcé** : auteur de l’acte, délégation de signature / de pouvoir régulière et publiée, compétence matérielle, territoriale et temporelle.
- **Contrôle de proportionnalité** (jurisprudence *Benjamin*, CE 19 mai 1933) en trois temps :
  - **adaptée** : la mesure est-elle apte à atteindre le but d’intérêt général ou d'ordre public visé ?
  - **nécessaire** : le but ne pourrait-il être atteint par une mesure moins attentatoire aux libertés publiques ?
  - **proportionnée stricto sensu** : l’atteinte aux droits et libertés est-elle en équilibre raisonnable avec la gravité du trouble ?
- **Contrôle de motivation** : respect des articles L. 211-2 et suivants du CRPA (Code des relations entre le public et l'administration) lorsqu'une motivation est légalement exigée.
- **Contrôle d’opposabilité** : formalités de publicité (affichage, publication au recueil des actes administratifs, télétransmission au contrôle de légalité, notification individuelle).
- **Contrôle des éléments de preuve et matérialité des faits** fondant la mesure.
- **Triangulation obligatoire** si l’acte fait grief ou si l'articulation des compétences est contentieuse.

---

## Module PA-PJ

**Déclencheurs** : question portant sur des opérations susceptibles d’appartenir à la police administrative ou à la police judiciaire ; mention de constatation, d’interpellation, de contrôle, de fouille, de capture ou de mesure préventive.

**Contenu obligatoire** — grille de distinction cumulative :

| Critère | Police administrative (PA) | Police judiciaire (PJ) |
|---------|----------------------------|------------------------|
| **Finalité** | Préventive (maintien du bon ordre, de la sûreté, de la salubrité et de la tranquillité) | Répressive (recherche, constatation d’infractions et rassemblement des preuves) |
| **Autorité de tutelle** | Autorité administrative (Maire, Préfet, Ministre de l'Intérieur) | Autorité judiciaire (Procureur de la République, Juge d'instruction) |
| **Temporalité** | En amont ou en l'absence de commission d'une infraction pénale | À partir d’une infraction pénale constatée, suspectée ou en cours |
| **Régime contentieux** | Juridiction administrative (TA / CAA / Conseil d'État) | Juridiction judiciaire (Tribunal correctionnel, TJ, Cour d'appel) |

Toujours qualifier explicitement l’opération selon ces quatre critères avant d'analyser la légalité des actes ou l'emploi de la force.

---

## Module FOND

**Déclencheurs** : consultation juridique complexe, note de synthèse approfondie, mémoire universitaire ou professionnel, examen d'une articulation normative controversée.

**Contenu obligatoire** :
- **Archéologie textuelle** : analyse de l'évolution législative (loi d'origine, modifications successives, dispositions transitoires applicables).
- **Circulaires et doctrine administrative** : identification des instructions officielles applicables, sous réserve de leur opposabilité.
- **Régimes comparés ou dérogatoires** : identification des régimes spéciaux primant sur le droit commun (*specialia generalibus derogant*).

---

## Module CONTENTIEUX

**Déclencheurs** : recours juridictionnel, requête contentieuse, conclusions d'avocat, question prioritaire de constitutionnalité (QPC), moyen de cassation.

**Contenu obligatoire** :
- **Recevabilité** : intérêt à agir, qualité pour agir, respect des délais de recours (délai de 2 mois en contentieux administratif, forclusion), exercice préalable obligatoire d'un recours administratif (RAPO).
- **Filtrage et recevabilité des moyens** : distinction des moyens d'ordre public (MOP), recevabilité en cassation (moyens nouveaux prohibés), conditions de transmission d'une QPC (applicabilité au litige, caractère nouveau ou sérieux).
- **Charge et administration de la preuve** : règles probatoires selon la nature du contentieux (système inquisitoire administratif, liberté des preuves en pénal, charge reposant sur le demandeur en civil).

---

## Module DOC-AUDIT

**Déclencheurs** : relecture critique, audit ou correction juridique d'un projet d'acte, d'un contrat, d'une consultation ou d'un corpus de documents juridiques.

**Statut** : **non désactivable par `[express]`** dès qu'un document existant est soumis à l'audit.

**Contenu obligatoire** :
- Registre exhaustif des affirmations juridiques contenues dans le document audité.
- Vérification systématique de 100 % des références citées contre les sources primaires officielles (recherche de textes abrogés, fausses références, numéros de pourvoi erronés).
- Matrice de cohérence des compétences (auteur, signataire, délégation, territorialité).
- Rapport d'écarts avec niveau de gravité (Critique / Majeur / Mineur) et propositions de rédaction corrective sécurisée.
