# CHANGELOG — recherche-juridique

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

---

### [3.1.1] — 2026-08-12

Release **corrective**, ciblée sur la seule commande `search`, laissée
défaillante par la v3.1.0 (« Connu, non traité »). Aucune méthodologie
modifiée, aucune autre commande touchée.

Le défaut était double, et chaque moitié masquait l'autre : le chemin
`--code` échouait en `HTTP 500` avant d'avoir rien cherché, et le chemin sans
`--code` posait une question à laquelle l'API ne pouvait que répondre « rien ».
Les deux causes ont été établies **contre l'environnement de production**,
variante de *payload* par variante, et non déduites de la documentation.

#### Corrigé
- **`search --code` : `HTTP 500`.** Le bloc `filtres` portait la facette
  `TEXT_LEGAL_STATUS`, que le fond `CODE_DATE` ne connaît pas — pas plus que
  `ARTICLE_LEGAL_STATUS` ou `CODE` : les trois y renvoient une exception non
  gérée. La restriction à ce qui est en vigueur passe par `DATE_VERSION`.
- **`search` sans `--code` : aucun résultat.** Le moteur n'indexe qu'une
  écriture du numéro d'article — la lettre de partie collée, sans point ni
  espace (`L2212-2`). Ni `2212-2`, ni `L. 2212-2`, ni `L 2212-2` n'y renvoient
  quoi que ce soit. Les écritures usuelles sont désormais normalisées, et un
  numéro donné sans lettre est cherché tel quel **puis** préfixé de `L`, `R`,
  `D` et `A`, en un seul appel (critères combinés par `OU`).
- **Le filtre `--code` ne filtrait rien.** `code_id` était résolu depuis la
  table des codes, puis jamais transmis : la ligne qui suivait la construction
  du corps de requête réassignait `args.numero` à sa propre valeur. Le filtre
  passe maintenant par la facette `NOM_CODE`, qui attend le **libellé** du
  code et **non** son identifiant `LEGITEXT` — un `LEGITEXT` y renvoie zéro
  résultat *sans erreur*, panne silencieuse indiscernable d'une absence réelle
  de résultat. C'est ce piège qui rendait l'anomalie invisible.
- **Doublons de versions.** Sans `DATE_VERSION`, le moteur rend une entrée par
  version historique du code — près de 900 pour un seul article. La recherche
  est désormais ancrée à une date : celle du jour par défaut, ou `--date`.
- **`LEGITEXT` du CRPA erroné** dans le script et dans `gabarits-requetes.md` :
  `LEGITEXT000031367321` (rejeté en `HTTP 400` par `consult/legiPart`) →
  `LEGITEXT000031366350`. L'URL de la voie web ne pointait sur rien.
- **Identifiants approximatifs en sortie.** `_first_legiarti` rendait le
  *premier* `LEGIARTI` rencontré dans la réponse, sans vérifier qu'il
  correspondait au numéro demandé. Les résultats sont désormais lus à leur
  emplacement réel — `results[].sections[].extracts[]`, `results[].id` valant
  `None` sur ce fond — et filtrés sur le numéro cherché.

#### Ajouté
- **`search --date AAAA-MM-JJ`** : version du code interrogée, par symétrie
  avec `article --date`. Défaut : la date civile **locale** — en UTC, un poste
  français interrogé en soirée obtiendrait la version de la veille, soit, le
  jour d'une entrée en vigueur, le texte que le skill a pour objet de ne plus
  citer.
- **Sortie de `search` détaillée** : numéro, `LEGIARTI`, code, emplacement dans
  le plan, statut et date de début de version — avec avertissement sur
  `stderr` dès qu'un article rendu n'est pas en vigueur, comme le fait déjà
  `article`.

#### Modifié
- **`CODE_IDS` → `CODES`** : la table porte désormais `(LEGITEXT, libellé)`.
  Les deux colonnes servent à deux voies distinctes — le `LEGITEXT` adresse la
  fiche par URL (voie web), le libellé alimente la facette `NOM_CODE` (voie
  outillée) — et les tenir dans une seule table empêche qu'elles divergent.
  Libellés issus de `consult/legiPart`, vérifiés par aller-retour sur la
  facette pour les 12 clés.
- **`references/maintenance.md`** : valeur témoin pour `search`, et contrôle
  des libellés ajouté à la revue annuelle.
- **`scripts/README.md`** : limite « `search` est défaillant » levée ;
  remplacée par les limites réelles de la commande (codes seulement, une
  version à la fois) et par la liste des facettes à ne pas réintroduire.

#### Retiré
- **`_first_legiarti`** : sans appelant après la reprise de `cmd_search`.
  `_first_id_with_prefix`, qu'il enveloppait, reste utilisé par `ceta` et
  `constit`.

#### Conservé (iso-fond)
- 14 modes, 7 principes, étapes 0 / 0 bis / 1-7, 4 techniques, 5 modules,
  10 déclencheurs d'abstention, gabarits de sortie, règle de provenance —
  inchangés. Aucune balise nouvelle. `search` reste une **recherche** : la
  citation exige toujours `article <LEGIARTI>`.

---

### [3.1.0] — 2026-08-12

Release **corrective et additive**, consécutive à l'intégration de JUDILIBRE
(PR #6), qui avait retiré par inadvertance les sous-commandes `ceta` et
`constit`. JUDILIBRE couvre la jurisprudence **judiciaire** (Cass., CA, TJ,
tribunaux de commerce) et **ni le Conseil d'État ni le Conseil
constitutionnel** : la perte n'était compensée par rien, tandis que quatre
fichiers de documentation continuaient de prescrire ces commandes au modèle.
Aucune méthodologie modifiée.

#### Ajouté
- **`ceta` / `constit` restaurées** dans `scripts/legifrance.py` (fonds
  Légifrance `CETAT` / `CONSTIT`), aux côtés du `juri` JUDILIBRE : chaque
  juridiction est routée vers l'API qui la couvre réellement. Helper
  `_first_id_with_prefix` réintroduit — dans les réponses `/search`,
  `results[i]["id"]` vaut `None` et l'identifiant officiel n'existe que sous
  `titles[0].id`.
- **Échelle de récupération (SKILL.md, étape 2)** — ordre imposé et
  **détection silencieuse** : voie outillée (sortie 0) → voie de repli web
  (sortie 2) → abstention §7. La voie se **constate** par le code de sortie ;
  demander à l'utilisateur s'il possède une clé PISTE est une **question
  rituelle prohibée** (étape 0 bis). L'étape 2 devient le **seul** lieu
  d'arbitrage des voies.
- **Section 7 « Jurisprudence Conseil constitutionnel »** dans
  `gabarits-requetes.md` : la voie web n'avait aucun gabarit CC, alors que
  `sources-autorisees.md` liste conseil-constitutionnel.fr comme source
  autorisée. Sections 7-11 renumérotées 8-12.
- **`tests/check_commands.py`** + étape CI dédiée : contrôle bidirectionnel
  entre les sous-commandes exposées par `build_parser()` (par introspection
  argparse, jamais par regex) et celles citées dans la documentation.
  Attrape les deux fautes de la PR #6 — commande supprimée encore prescrite,
  commande ajoutée jamais documentée.
- **`JUDILIBRE_ENV`** enfin lue par le script (`_judilibre_base()`) : les deux
  API peuvent viser des environnements distincts.
- **`scripts/README.md`** : documentation JUDILIBRE (CGU, souscription, clé
  `KeyId` distincte du `client_secret`, repli `KeyId` → `Bearer`, dépannage).

#### Modifié
- **SKILL.md** : version 3.0.0 → 3.1.0.
- **P1 (règle de provenance)** : les deux voies étaient juxtaposées par une
  virgule plate, ce qui contredisait la hiérarchie affirmée au §9. L'ordre
  renvoie désormais à l'étape 2, et la règle est déclarée **indifférente à la
  voie** — un identifiant récupéré par `web_fetch` vaut celui récupéré par
  l'API ; l'absence de clé n'abaisse jamais le niveau de preuve.
- **§9** : cesse d'arbitrer l'ordre des voies et renvoie à l'étape 2 ;
  mentionne les deux API et non « l'API Légifrance/PISTE » au singulier.
- **Message d'absence d'identifiants PISTE** : de « il manque une clé, va la
  chercher » à « la clé est OPTIONNELLE, bascule sur la voie web ». Les deux
  premières lignes portent les mots-clés de routage, le message étant lu par
  un modèle qui doit décider, non par un humain qui doit s'inscrire. Le code
  de sortie 2 s'affiche en `⚠️` et non `❌` : ce n'est pas une panne.
- **`references/maintenance.md`** : les deux API se vérifient séparément
  (abonnements PISTE distincts, régressions indépendantes), avec valeurs
  témoins ; nouveau point de revue sur l'unicité du lieu d'arbitrage.
- **`README.md`**, **`tests/README.md`** : deux API, contrôles statiques.

#### Corrigé
- **Sémantique de `juri` dans la documentation** : présentée comme une
  recherche par n° de pourvoi (fond `JURI`) depuis la PR #6, alors qu'elle est
  devenue une recherche **plein texte** JUDILIBRE.
- **« Texte intégral non exposé »** dans les limites de `scripts/README.md` :
  caduc depuis l'ajout de `decision`.
- **Titres Légifrance** débarrassés du balisage `<mark>` de surlignage, qui
  serait sorti tel quel dans les résultats de `ceta` / `constit`.
- **`_first_legiarti`** redélégué à `_first_id_with_prefix` : la PR #6 en
  avait dupliqué la récursion sans raison.
- **`JUDILIBRE_ENV`** était documentée dans `.env.example` mais jamais lue :
  l'utilisateur croyait viser un environnement et atteignait l'autre — sur un
  skill qui interdit de conclure sur la vigueur depuis le bac à sable.

#### Connu, non traité
- **`search` est défaillant** (défaut antérieur, constaté ici) : `HTTP 500`
  avec `--code`, aucun résultat sans. Le *payload* est à reprendre ; documenté
  dans les limites de `scripts/README.md`.
  → **Corrigé en [3.1.1]** : les deux pannes tenaient au bloc `filtres` et au
  format du numéro d'article, pas au fond interrogé.

#### Conservé (iso-fond)
- 14 modes, 7 principes, étapes 0 / 0 bis / 1-7, 4 techniques, 5 modules,
  10 déclencheurs d'abstention, gabarits de sortie, règle de provenance —
  inchangés au fond. **Aucune balise nouvelle** ; l'économie du questionnement
  (étape 0 bis) n'est pas touchée.

---

### [3.0.0] — 2026-07-02

Refonte **structurelle** (MAJEUR) : le noyau méthodologique devient
**universel**, le métier de l'utilisateur devient un **paramètre** (profil).
Objectif d'adoption : rendre le skill utile à tout praticien du droit
français, pas seulement à son auteur. Aucun contenu méthodologique retiré.

#### Ajouté
- **`skill/profils/`** — système de profils configurables. Un `profil.md`
  (copié depuis un modèle) fixe les **défauts** : contexte territorial
  (question 4 de l'étape 0), domaines prioritaires (veille §10), et 3ᵉ regard
  d'auto-critique (rôle (c) de l'étape 7). Profils fournis : `_modele`,
  `police-gendarmerie` (police nationale / gendarmerie / police municipale,
  avec distinction OPJ/APJ/APJA), `avocat`, `juriste-entreprise`,
  `collectivites`, `etudiant-concours`.
- **Règle de chargement (§0)** : lecture de `profil.md` au déclenchement ;
  valeurs = **défauts jamais des certitudes** (surchargées par la requête,
  rouvertes par l'étape 0 bis si décisionnelles). Sans profil → **profil
  neutre** (aucune hypothèse métier/territoriale).
- **Sonde d'éval `N`** (profil neutre) : garde-fou anti-régression — sans
  profil, le skill pose la question territoriale (étape 0 bis) au lieu de
  présumer un contexte.
- **README** : TL;DR anglais, démo avant/après (hallucination vs abstention),
  badges (CI / release / licence), encadré « fonctionne sans clé API »,
  section « Choisir son profil ».

#### Modifié
- **SKILL.md** : version 2.4.0 → 3.0.0. Objet/Public généralisés (praticiens
  du droit français). **§8** « Cas particuliers PM/Saint-Ouen » → renvoi à la
  section 5 du profil actif. Étape 7 rôle (c) et §10 (veille) pilotés par le
  profil. Balise `[opérationnel]` : « directeur » → « responsable » opérationnel.
- **references/maintenance.md**, **gabarits-sortie.md** : veille et rôle (c)
  pilotés par le profil (contenu PM conservé comme exemple police-gendarmerie).
- **README.md**, **vault/** (index, procedure-compacte) : système de profils.

#### Retiré
- Du **noyau** : le contexte personnel codé en dur (Saint-Ouen, TA Montreuil,
  DGA, Commissaire de Police). Le contenu métier PM est **conservé**, déplacé
  dans `profils/police-gendarmerie.md` avec les valeurs locales en
  `[à compléter]`.

#### Corrigé
- **LICENSE** : texte canonique complet CC BY-SA 4.0 (legalcode SPDX) au lieu
  du résumé — pour la détection automatique par GitHub (affichait « Other »).

#### Conservé (iso-fond)
- 14 modes, 7 principes, étapes 0 / 0 bis / 1–7, 4 techniques, 5 modules,
  10 déclencheurs d'abstention, gabarits, outillage PISTE — inchangés au fond.

---

### [2.4.0] — 2026-06-27

Issue d'un **second audit** (post-v2.3.0). Traite les tensions introduites par
la v2.3.0 et les points restés ouverts, sans toucher au fond juridique.

#### Ajouté
- **Jurisprudence dans `scripts/legifrance.py`** : commandes `juri` (fond
  JURI, Cass.), `ceta` (CETAT, CE), `constit` (CONSTIT, CC), recherche
  best-effort par numéro renvoyant l'identifiant officiel (JURITEXT /
  CETATEXT / CONSTEXT). **Résout l'asymétrie de provenance** : la règle vise
  les n° de pourvoi / requête / décision, désormais récupérables par outil.
- **CI GitHub Actions** (`.github/workflows/ci.yml`) : `py_compile` des
  scripts, vérification des liens Markdown, éval hors-ligne — à chaque push
  sur `main` et à chaque PR.
- **`tests/check_links.py`** : vérificateur de liens Markdown relatifs (stdlib,
  hors `vault/`).
- **`tests/run_eval.py --judge`** : verdict par **LLM-juge** (2e appel notant
  le fond) en alternative aux regex, pour réduire les faux positifs.
- **Sondes de balises** dans `tests/eval-modes-erreur.csv` : `[complet]`,
  `[express]`, `[syllogisme]`, `[opérationnel]` (Bc/Be/Bs/Bo).
- **`skill/references/modes-erreur.md`** : détail des 14 modes (extrait du §1).

#### Modifié
- **SKILL.md** : version 2.3.0 → 2.4.0. **§1 dégraissé** : les 14 modes en
  table compacte + pointeur vers `references/modes-erreur.md` (détail déplacé).
- **`tests/README.md`** : section **Limites** (le harnais appelle le modèle
  **sans outils** ; regex indicatives), usage `--judge`, sondes de balises.
- **`skill/references/format-citation.md`** : les citations d'exemple (Benjamin,
  QPC) sont explicitement marquées **illustratives** (format, non vérifiées) —
  cohérence avec la règle de provenance.
- **`skill/references/gabarits-requetes.md`** : commandes jurisprudence du
  script ; note sur les noms d'outils (`WebFetch`/`WebSearch` en Claude Code).
- **`skill/scripts/README.md`** : usage jurisprudence, limite révisée.
- **README.md** : portée « Claude Code + portable » (au lieu de « toutes les
  IA »), arborescence (CI, `modes-erreur.md`, `check_links.py`), version.

#### Corrigé
- **Asymétrie provenance ↔ outillage** (introduite en v2.3.0) : la règle de
  provenance exigeait des identifiants de jurisprudence par outil, mais le
  script ne couvrait que les articles de code — désormais résolu.

#### Conservé (iso-fond)
- 14 modes, 7 principes, étapes 0 / 0 bis / 1–7, 4 techniques, 5 modules,
  10 déclencheurs d'abstention, gabarits — inchangés au fond.

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
