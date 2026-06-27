# CHANGELOG — recherche-juridique

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

---

### [2.3.0] — 2026-06-27

Issue d'un audit du skill. Cinq axes : fiabilité réelle de la
récupération, anti-simulation de procédure, économie de longueur,
cohérence interne, non-régression.

#### Ajouté
- **`skill/scripts/legifrance.py`** : CLI Python (bibliothèque standard
  uniquement) interrogeant l'**API Légifrance via PISTE** (OAuth2
  client_credentials). Commandes `ping`, `article` (par `LEGIARTI`,
  option `--date`), `search` (par numéro, filtre code). Matérialise le
  « Palier 3 » du §9 : l'identifiant, la date de version en vigueur et
  le statut proviennent d'une réponse officielle, non de la mémoire.
  Dégradation propre et codes de sortie contractuels (4/5 = abstention).
- **`skill/scripts/README.md`** : onboarding BYOK « apporte ta clé » —
  démarrage en 2 minutes, obtention des identifiants PISTE pas-à-pas,
  configuration `.env` ou variables d'environnement, dépannage, limites,
  note de sécurité (pourquoi pas de clé embarquée dans un paquet public).
- **`skill/scripts/.env.example`** : gabarit de configuration (sans
  valeurs) à copier en `.env` (gitignoré).
- **Chargement `.env` automatique** dans `legifrance.py` (sans dépendance) :
  `$LEGIFRANCE_DOTENV`, puis `./.env`, puis `.env` voisin du script ; une
  variable déjà exportée prime. Message d'aide actionnable quand la clé
  manque (étapes de configuration inline).
- **Règle de provenance (P1)** : tout identifiant officiel (`LEGIARTI`,
  `JORFTEXT`, `NOR`, n° de pourvoi / requête / décision) doit provenir
  d'un appel d'outil de la session ; à défaut, omis ou marqué
  `⚠️ non vérifié — identifiant non récupéré`, et interdiction du
  gabarit C. Vise la **simulation de procédure** (cérémonial des étapes
  sans récupération réelle). Référencée à l'étape 6 (contrôle de
  provenance), dans `format-citation.md` et `checklist-vigueur.md`.
- **Balise `[lookup]` — voie rapide** : sortie minimale (sans en-tête ni
  encart) pour une référence ponctuelle non controversée. N'allège aucune
  exigence de fond (P1, provenance, étape 0 bis dues) ; refusée dès qu'une
  interprétation, une qualification pénale ou un acte est en jeu.
- **`tests/eval-modes-erreur.csv`** : jeu d'évaluation mappé 1-pour-1 sur
  les 14 modes d'erreur + 2 contrôles transverses (provenance `P`,
  lookup `L`), avec motifs regex attendus/interdits.
- **`tests/run_eval.py`** : harnais d'évaluation sans dépendance externe
  (hors-ligne par défaut ; `--live` via l'API Anthropic en urllib).
- **`tests/README.md`** : mode d'emploi des deux jeux d'éval.

#### Modifié
- **SKILL.md** : version 2.2.0 → 2.3.0 ; numérotation harmonisée
  « procédure en 9 étapes (0, 0 bis, 1 à 7) » au lieu de « 7 étapes »
  (le titre comptait 0 à 7) ; §9 (Palier 3) pointant le script comme
  voie privilégiée de P1 ; intro et §0 mis à jour pour `[lookup]` et la
  règle de provenance.
- **README.md** : version, arborescence (ajout `scripts/`), balise
  `[lookup]`, mentions provenance et récupération outillée.
- **references/maintenance.md** : checklist cohérence corrigée
  (« 9 étapes » ; « 10 déclencheurs d'abstention » au lieu de 9 ; balise
  `[lookup]` ; contrôle de provenance) ; §3 ajoute `legifrance.py ping`.
- **references/gabarits-requetes.md**, **format-citation.md**,
  **checklist-vigueur.md** : intègrent le script et la règle de provenance.

#### Corrigé
- **Suppression du `SKILL.md` racine obsolète** (pointeur v2.1.0) :
  évite la coexistence de deux `SKILL.md`.
- **maintenance.md** : « 9 déclencheurs d'abstention » → 10 (le 10e date
  de la v2.1.0).

#### Conservé (iso-fond)
- 14 modes d'erreur, 7 principes P1–P7, étapes 0 / 0 bis / 1–7,
  4 techniques T1–T4, 5 modules, 10 déclencheurs d'abstention, gabarits
  A/B/C + syllogisme, cas particuliers PM/Saint-Ouen — inchangés au fond.

---

### [2.2.0] — 2026-06-11

#### Ajouté
- **skill/** : répertoire unique empaqueté pour l'installation (contient SKILL.md,
  CHANGELOG.md, references/).
- **skill/references/gabarits-sortie.md** : gabarits A (express), B (fond),
  C (citation pour acte) et sous-gabarit `[syllogisme]` (note de concours) —
  extrait verbatim de l'ancien §6.
- **skill/references/modules.md** : détail des 5 modules activables (PÉNAL,
  ACTE-ADMIN, PA-PJ, FOND, CONTENTIEUX) — extrait verbatim de l'ancien §5.
- **skill/references/sources-autorisees.md** : hiérarchie des 4 niveaux de
  sources, sources non admises, règles d'usage croisé (complément P3) — créé
  en v2.2.0 à partir du contenu de P3 (liens cassés dans les versions
  antérieures).
- **skill/references/format-citation.md** : formats normalisés article / décret /
  Cass. / CE / CC / CJUE / CEDH, grille autorité jurisprudentielle, ratio/obiter
  (complément P4) — créé en v2.2.0 à partir du contenu de P4 (liens cassés dans
  les versions antérieures).
- **skill/references/gabarits-requetes.md** : gabarits de requêtes Légifrance —
  déplacé depuis la racine.
- **skill/references/checklist-vigueur.md** : checklist 14 points de vigueur —
  déplacée depuis la racine.
- **skill/references/maintenance.md** : procédure de revue annuelle — déplacée
  depuis docs/.
- **vault/structure-v2.2.0.md** : note Obsidian documentant le découpage modulaire
  et le maillage noyau ↔ références.

#### Modifié
- **SKILL.md** : frontmatter `nom:` → `name:` + `description:` conformes au
  standard skill. Version 2.1.0 → 2.2.0. §5 modules : déclencheurs + résumé
  tabulaire + pointeur vers references/modules.md. §6 gabarits : stub 4 lignes
  + pointeur vers references/gabarits-sortie.md. CHANGELOG retiré (déplacé dans
  CHANGELOG.md). Liens internes mis à jour vers references/.
- **README.md** : version 2.1.0 → 2.2.0, mention étape 0 bis, nouvelle
  arborescence, instruction d'installation (empaqueter uniquement skill/),
  ajout note de synchronisation README/CHANGELOG à chaque release.

#### Conservé (iso-fond)
- 14 modes d'erreur (§1) — inchangés.
- 7 principes P1–P7 (§2) — inchangés.
- Étapes 0, 0 bis, 1–7 complètes (§3) — inchangées.
- 4 techniques T1–T4 (§4) — inchangées.
- 5 modules PÉNAL/ACTE-ADMIN/PA-PJ/FOND/CONTENTIEUX — contenu déplacé verbatim,
  non modifié.
- 10 déclencheurs d'abstention (§7) — inchangés.
- Cas particuliers PM/Saint-Ouen (§8) — inchangés.
- Gabarits A, B, C, syllogisme — contenu déplacé verbatim, non modifié.
- Aucun contenu méthodologique ou juridique modifié.

---

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

### [2.1.0] — 2026-06-02

#### Ajouté
- **Étape 0 bis — Arbitrage des informations manquantes (VISIBLE)**,
  insérée entre l'étape 0 et l'étape 1. Recense les informations
  manquantes et applique à chacune un **test décisionnel**.
- **Test décisionnel / non décisionnel** : seul aiguillage entre
  question obligatoire (l'information fait basculer la conclusion, le
  régime, la qualification ou la procédure) et hypothèse déclarée
  autorisée (l'information ne change pas la conclusion).
- **Clause anti-échappatoire (impérative)** : la déclaration
  d'hypothèse ne peut jamais se substituer à la question sur un point
  décisionnel. Signal d'alarme explicite sur les formules « déterminant
  / central / commande la réponse ».
- **Économie du questionnement** : pas de question rituelle ; une seule
  question par défaut (plafond trois) ; question fermée ou à choix ;
  réservée à ce que seul l'utilisateur détient (sinon, chercher).
- **Esquisse conditionnelle bornée** : tant qu'un point décisionnel
  n'est pas tranché, pas d'analyse complète, au plus un « si (a) /
  si (b) » de quelques lignes.
- **10e déclencheur d'abstention** : information décisionnelle détenue
  par le seul utilisateur, manquante. Avec **format de clarification
  motivée** dédié au §7.
- Cas particulier **Répartition des compétences intercommunales
  (MGP / EPT)** au §8, avec exemple type d'étape 0 bis (compétence
  statutaire vs supplémentaire, L. 5211-17 CGCT).
- Rubrique **Étape 0 bis** ajoutée aux gabarits A et B (§6).

#### Modifié
- **Étape 0**, critère de sortie : renvoi explicite vers l'étape 0 bis
  en cas d'ambiguïté ou d'information manquante (au lieu d'un simple
  « demander clarification »).
- **P7** : ajout d'un corollaire d'entrée (l'abstention informée a son
  pendant au stade de l'entrée = poser la question, étape 0 bis).
- **Architecture §0** : précision qu'aucune balise (`[express]`,
  `[complet]`) ne dispense de l'étape 0 bis.
- **§9** : étape 0 bis ajoutée à la liste des étapes restant
  essentielles au Palier 3 (API PISTE).
- Métadonnées : `version` 2.0.0 → 2.1.0 ;
  `date_derniere_revue_methodologique` → 2026-06-02.

#### Motivation
- Deux cas observés où une ambiguïté **décisionnelle** a été traitée
  par hypothèse — déclarée ou silencieuse — au lieu d'une question,
  produisant (mode B) une analyse complète sur une fondation non
  confirmée. Le second cas est le plus instructif : le skill avait
  lui-même qualifié le point de « déterminant » et « commande toute la
  réponse », puis avait écrit « je traite ce scénario comme principal
  et signale l'alternative ». La clause anti-échappatoire vise
  précisément ce contournement par transparence.

#### Conservé
- 14 modes d'erreur (l'étape 0 bis est une garde procédurale, pas un
  15e mode).
- 7 principes, procédure en 7 étapes, double mode A/B, 5 modules,
  4 techniques, 3 gabarits + sous-gabarit concours.
- Étapes 0 et 7 visibles ; l'étape 0 bis rejoint la liste des étapes
  visibles.

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
- Cas particuliers Police Municipale Saint-Ouen alignés sur les
  nouveaux modules (notamment partage de compétences avec PP en
  petite couronne).

#### Conservé (issu de v1)
- 4 registres explicites (texte / jurisprudence / déduction /
  incertitude) — désormais P5.
- 3 gabarits de sortie (express / fond / citation pour acte).
- Techniques T1 (qualification adversariale), T2 (triangulation),
  T3 (archéologie textuelle).
- Étapes 0 et 7 **visibles** dans la réponse finale.

### [1.0.0] — 2026-05-19 (commit 2f73937)

#### Ajouté
- Version initiale avec 10 modes d'erreur, 6 principes, procédure en
  7 étapes, 3 gabarits, 3 techniques, 5 déclencheurs d'abstention.
