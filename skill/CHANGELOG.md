# CHANGELOG — recherche-juridique

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

Deux séries de versions cohabitent depuis la distribution en plugin : le
**skill** (méthodologie, série 3.x) et le **plugin** (empaquetage OpenAI et
Claude Code, série 0.x). Les tags Git portent désormais le préfixe de leur
série — `skill-v*` et `plugin-v*`. Les tags historiques non préfixés
(`v2.0.0`, `v2.4.0`, `v3.0.0`) désignent des versions du skill et sont
conservés tels quels pour ne pas casser les liens publiés.

---

### [3.3.0] — 2026-09-05

#### Modifié
- Les contrôles restent obligatoires, mais leur affichage devient proportionné
  au livrable : les réponses simples ne récitent plus les étapes internes ni
  une auto-critique vide.
- L'ordre de recherche est distingué de la hiérarchie des normes et de l'effet
  des décisions juridictionnelles.
- L'échelle de récupération reconnaît désormais le connecteur MCP lorsqu'il est
  disponible, avant le script local et le repli web.
- La triangulation renforcée cible les interprétations discutables. L'absence
  de jurisprudence ne rend plus automatiquement incertain un texte clair.
- Le vault de navigation (`vault/`) est réaligné sur ces règles : P3, échelle de
  récupération, affichage des étapes et exigence de triangulation.

### [plugin-v0.8.2] — 2026-09-05

#### Corrigé
- `get_article` distingue la provenance officielle de l'applicabilité de la
  version à la date évaluée et signale une version historique.
- `search` vérifie un identifiant `LEGIARTI` fourni avant de le retourner.
- Le routeur conserve le code et la date reconnus et accepte les références
  usuelles telles que `L. 2212-2 CGCT`.

#### Tests
- Ajout de régressions sur la datation d'une version historique, la provenance
  d'un identifiant fourni, la conservation du code et de la date et le routage
  d'une référence préfixée sans le mot « article ».

### [3.2.1] — 2026-09-04

Issue d'un audit de fraîcheur juridique portant sur ce skill et sur
`drh-fpt`, mené par des agents indépendants vérifiant chaque source et
identifiant citée contre l'état réel en ligne. Aucune évolution
méthodologique ; correction de sources devenues fausses ou périmées.

#### Corrigé
- **`references/sources-autorisees.md`** : trois adresses erronées —
  `journal-officiel.gouv.fr` (site DILA des annonces légales, pas le JORF —
  remplacé par `legifrance.gouv.fr/jorf/jo`, seule adresse qui répond
  effectivement), `judilibre.fr` (domaine inexistant — Judilibre n'est
  accessible que via `courdecassation.fr/recherche-judilibre`),
  `arianeweb.conseil-etat.fr` (URL périmée — remplacée par
  `conseil-etat.fr/arianeweb/`). `circulaires.legifrance.gouv.fr` redirige
  désormais vers le site principal (refonte Légifrance d'avril 2026) ;
  corrigé également dans `SKILL.md` (P1, P3) et dans les deux gabarits de
  requête `site:circulaires.legifrance.gouv.fr` de
  `references/gabarits-requetes.md`, repérés lors de la revue de merge.
- **`references/modules.md`** (module ACTE-ADMIN) : le contrôle de
  motivation visait encore la loi du 11 juillet 1979, recodifiée au CRPA
  (art. L.211-2 et s.) par l'ordonnance n° 2015-1341 depuis le 1/01/2016 —
  dix ans de retard sur ce point précis.
- **`references/sources-autorisees.md`** : ajout de vie-publique.fr comme
  source des dossiers législatifs/travaux parlementaires postérieurs au
  1/04/2026, migrés hors Légifrance.
- `date_derniere_verification_sources` portée à 2026-09-04.

#### Vérifié sans changement
Domaines Légifrance, Cour de cassation, Conseil d'État, Conseil
constitutionnel, EUR-Lex ; formats d'identifiants (LEGIARTI, JORFTEXT,
CETATEXT, CONSTEXT) ; formats de citation (Bull./inédit, Lebon/Tables) ;
architecture PISTE (API Légifrance + Judilibre).

### [plugin-v0.8.1] — 2026-09-04

Correctif de sécurité issu d'un audit adversarial du chemin d'authentification,
mené le 4 septembre 2026 puis soumis au test de mutation par une relecture
indépendante. Le noyau méthodologique est inchangé ; seul le vérificateur de
jetons bouge. **Cette version doit être déployée avant toute soumission** : la
production servait encore `0.8.0`, donc un serveur dépourvu de ces correctifs.

#### Corrigé
- **Amplification JWKS non authentifiée** — un jeton portant un identifiant de
  clé inconnu forçait PyJWT à recharger le jeu de clés en contournant son
  cache, et ce cache ne mémorise pas les échecs. Chaque requête anonyme coûtait
  donc un aller-retour vers l'émetteur, indéfiniment : mesuré en production à
  54 ms de surcoût par requête, facteur 1,8. Le délai d'attente valait trente
  secondes par défaut, sur un pool de quarante threads et un processus unique.
  Le rafraîchissement forcé est désormais plafonné à un par minute quel que
  soit le nombre d'identifiants distincts présentés, et le délai ramené à cinq
  secondes. Contre-épreuve : 20 rechargements réseau sur le code d'avant, 1 sur
  celui-ci ; 200 contre 1 à plus forte charge.
- **Ruée sur l'expiration du cache** — le cache de jeu de clés de PyJWT n'a
  aucun verrou : à l'instant précis où il expire, quarante requêtes
  concurrentes déclenchaient trente appels réseau, sans qu'aucun jeton valide
  soit nécessaire. Les appels sont sérialisés en *single-flight* : un seul
  thread contacte l'émetteur, les autres retrouvent le cache rechargé.
- **Révocation de clé non honorée** — le cache de second niveau était un
  `lru_cache` sans expiration ; le jeu de clés n'en comptant que deux, rien
  n'était jamais évincé et une clé révoquée restait acceptée jusqu'au
  redémarrage du processus. Tourner une clé compromise n'avait donc aucun effet
  sur ce serveur. Elle cesse maintenant d'être acceptée en cinq minutes au pire.
- **Panne de l'émetteur journalisée comme un refus de jeton** —
  `PyJWKClientConnectionError` héritant de `PyJWTError`, un DNS mort, un port
  fermé ou un délai dépassé produisaient `auth_rejected` en INFO au lieu
  d'`auth_unavailable` en WARNING, noyant le signal « l'émetteur est tombé »
  dans le bruit des jetons invalides.

#### Tests
- 178 → **196 tests**, aucun échec, aucun ignoré. Chaque correction porte sa
  contre-épreuve, appliquée puis annulée, de sorte qu'aucun de ces tests ne
  passe sur le code d'avant.
- Comblé deux angles morts que la suite ne voyait pas : les jeux de clés
  simulés n'en contenaient qu'**une seule**, si bien qu'une confusion de clé —
  vérifier la signature avec la mauvaise clé du jeu — survivait à toute la
  suite ; et les quatre branches d'erreur du contrôle de métadonnées OAuth,
  qui protège le point de rupture historique du connecteur ChatGPT, n'étaient
  exercées par aucun test.
- Corrigé des mocks qui rendaient des tests aveugles : ils acceptaient
  n'importe quel identifiant de clé, alors que la check-list Auth0 citait l'un
  d'eux comme preuve du refus d'un identifiant inconnu. La preuve citée ne
  prouvait rien ; elle est devenue vraie.

#### Sécurité — ce qui reste ouvert
- Aucune limitation de débit par IP **avant** l'authentification. L'atténuation
  ci-dessus porte sur deux à trois ordres de grandeur, mais borner la durée
  d'occupation d'un thread ne borne pas leur nombre : le finding est reclassé
  de gravité élevée à moyenne, **non refermé**.
- L'authentification reste la seule autorisation : aucune portée n'est exigée
  et aucun sujet n'est comparé à une liste. Voir `docs/audit-securite.md` § 8.

### [plugin-v0.8.0] — 2026-09-02

Durcissement du serveur MCP après l'audit externe du 1er septembre 2026 et la
revue de fusion du 2. Le noyau méthodologique (v3.2.0) est inchangé ; seul
l'empaquetage et le serveur bougent.

#### Ajouté
- **Reprise bornée sur erreur transitoire** — un `429` ou un `5xx` ponctuel des
  API amont est rejoué deux fois au plus, avec recul exponentiel et respect de
  `Retry-After`, sous un budget de 8 s inférieur au délai d'une seule requête.
  Aucun autre `4xx` n'est rejoué.
- **Identifiant de corrélation** sur les erreurs amont : le client reçoit un
  message public stable, le journal porte le détail sous la même référence.
- **Instructions MCP** servies au client à la connexion : trois règles de
  méthode — rien de mémoire, vigueur vérifiée, refus explicite.
- **Surveillance de production** — sonde de disponibilité séparant un réveil
  d'instance d'une panne, résumé de série avec verdict d'observation, et
  workflow planifié tenant le registre.

#### Corrigé
- **Cache de jeton PISTE** commun à Légifrance et Judilibre, respectant
  `expires_in` avec une marge, et renouvelé **une seule fois** sur `401`. Le
  jeton Judilibre n'expirait jamais et cassait la voie OAuth jusqu'au
  redémarrage ; Légifrance en redemandait un à chaque opération.
- **Détail amont** (URL complète, fragment de réponse) retiré des messages
  rendus au client et réservé au journal.
- **Retrait conservatoire Judilibre** : identifiants normalisés, liste
  malformée refusée au démarrage, nombre d'entrées journalisé. Une valeur mal
  recopiée était acceptée en silence et la décision restait servie.

### [plugin-v0.7.0] — 2026-09-01

Première release de la série *plugin*, taguée séparément du skill. Le noyau
méthodologique (v3.2.0) est inchangé.

#### Ajouté
- **`.claude-plugin/plugin.json`** : manifeste plugin Claude Code, aligné sur
  le manifeste OpenAI (nom, version, licence) ; serveur MCP déclaré en ligne
  avec `${CLAUDE_PLUGIN_ROOT}` pour des chemins portables après installation.
- **`.claude-plugin/marketplace.json`** : le dépôt sert de marketplace
  Claude Code (`claude plugin marketplace add brissonjo-sudo/droit-francais-skill`
  puis `claude plugin install droit-francais-skill@droit-francais`).
- **README** : section « Comme plugin Claude Code », prérequis (Python avec
  `requirements-mcp.txt`, identifiants PISTE hors du paquet) et arborescence.
- **Convention de tags préfixés** `skill-v*` / `plugin-v*` (voir en-tête).

#### Conservé
- Skill v3.2.0, plugin OpenAI `.codex-plugin/plugin.json` et serveur MCP
  inchangés : cette release ne modifie que la distribution.

### [3.2.0] — 2026-08-27

Issue d'un retour d'expérience sur l'audit d'un corpus opérationnel. La
méthode vérifiait les sources mais ne garantissait ni l'exhaustivité du
contrôle documentaire, ni la validité de la conséquence tirée d'une citation
exacte, ni la cohérence entre fichiers.

#### Ajouté
- **Module DOC-AUDIT**, non désactivable par `[express]`, pour tout audit,
  toute relecture juridique ou correction d'un document existant.
- **`references/audit-documentaire.md`** : protocole bloquant — qualification
  du livrable et date de droit, inventaire du corpus, registre des
  affirmations, contrôle de 100 % du risque élevé, matrice
  acteur–lieu–propriétaire–pouvoir, double test source/conséquence, cohérence
  interdocuments et contrôle post-correction.
- **Gabarit D — Audit documentaire** : synthèse des corrections, couverture
  du risque élevé, divergences et limites restantes.
- Quatre modes d'erreur : validation héritée (15), citation exacte mais
  conséquence fausse (16), mauvais acteur–lieu–propriétaire–pouvoir (17),
  incohérence de corpus (18).
- Quatre sondes d'évaluation correspondant aux nouveaux modes.

#### Modifié
- **SKILL.md** : version 3.1.1 → 3.2.0 ; déclenchement de DOC-AUDIT ; contrôle
  source/conséquence à l'étape 6.
- **README, références et maintenance** : 18 modes, 6 modules, gabarit D et
  quatrième test fonctionnel de revue.

#### Corrigé
- **`tests/eval-modes-erreur.csv`** : guillemets manquants autour de deux
  regex contenant une virgule ; le lecteur CSV tronquait silencieusement les
  motifs interdits des modes 5 et 7. `run_eval.py` rejette désormais toute
  ligne comportant des colonnes excédentaires au lieu de les ignorer.

#### Sécurité
- Un audit antérieur, même annoncé comme réalisé avec ce skill, ne réduit
  pas la revérification des affirmations à risque élevé.
- Interdiction de déclarer l'audit achevé tant qu'un point à risque élevé
  n'est pas vérifié/corrigé ou placé en abstention ciblée.

#### Conservé
- Profils v3, récupération Légifrance/Judilibre, correctifs `search` v3.1.1,
  7 principes, 9 étapes, 4 techniques et 10 déclencheurs d'abstention.
- `date_derniere_verification_sources` reste au 19 mai 2026 : cette évolution
  est méthodologique et ne vaut pas revue générale de toutes les sources.

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
