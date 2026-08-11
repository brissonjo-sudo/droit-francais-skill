# `scripts/` — outillage de récupération en source primaire

Ce dossier matérialise le **Palier 3** du skill `recherche-juridique` :
remplacer le scraping fragile de Légifrance par un accès **aux API
officielles**, de sorte que P1 (primarité) et la **règle de provenance**
(v2.3.0) soient satisfaits par un appel d'outil déterministe plutôt que par
la mémoire du modèle.

Deux API, souscrites sur la même plateforme PISTE, se partagent la matière :

| API | Couvre | Commandes |
|-----|--------|-----------|
| **Légifrance** (DILA) | codes, lois, décrets, arrêtés, JORF | `article`, `search` |
| **Légifrance** (fonds `CETAT` / `CONSTIT`) | Conseil d'État, Conseil constitutionnel | `ceta`, `constit` |
| **Judilibre** (Cour de cassation) | Cass., cours d'appel, tribunaux judiciaires et de commerce | `juri`, `decision`, `taxonomy` |

**Judilibre ne couvre ni le Conseil d'État ni le Conseil constitutionnel** :
ces deux juridictions passent par les fonds Légifrance. Confondre les deux
périmètres, c'est retirer au skill toute voie outillée vers la jurisprudence
administrative et constitutionnelle.

> **Modèle « apporte ta clé » (BYOK).** Le skill est distribué publiquement :
> il n'embarque **aucune** clé. Chaque utilisateur configure **sa propre**
> clé PISTE (gratuite). Une clé partagée dans un paquet public ne serait plus
> un secret — voir la note de sécurité en bas de page.

> **La clé est optionnelle.** Sans identifiants PISTE, le skill reste
> pleinement opérationnel : il bascule sur la **voie de repli web**
> (`web_search` / `web_fetch` sur domaines officiels,
> [`references/gabarits-requetes.md`](../references/gabarits-requetes.md)),
> et la **règle de provenance s'y applique à l'identique**. La clé apporte le
> déterminisme et les métadonnées officielles, jamais un droit de citer plus
> librement. Ordre des voies : SKILL.md, étape 2, *échelle de récupération*.

---

## Démarrage en 2 minutes

```bash
# 1. Obtenir une clé PISTE (gratuit) — voir l'étape détaillée plus bas
# 2. Renseigner ses identifiants
cp skill/scripts/.env.example skill/scripts/.env
$EDITOR skill/scripts/.env         # coller CLIENT_ID et CLIENT_SECRET

# 3. Vérifier que tout répond
python skill/scripts/legifrance.py ping
```

Si `ping` affiche « ✅ Authentification PISTE réussie », c'est prêt.

---

## `legifrance.py`

CLI Python (bibliothèque standard uniquement, Python 3.8+) interrogeant les API
Légifrance et Judilibre exposées via la plateforme **PISTE** de la DILA.

### Étape 1 — Obtenir des identifiants PISTE (gratuit)

1. Créer un compte sur <https://piste.gouv.fr>.
2. Menu **« Applications »** → créer une application.
3. L'**abonner à l'API « Légifrance »** (catalogue des API → Légifrance →
   souscrire). L'abonnement peut demander une courte validation.
4. Dans la fiche de l'application, relever le **`client_id`** et le
   **`client_secret`**.
5. *Pour la jurisprudence judiciaire* — accepter les **CGU JUDILIBRE**, puis
   cocher l'API JUDILIBRE (**Applications → Modifier l'application →
   Sélectionner les API**). Relever ensuite la **clé d'API « `KeyId` »** sur
   la fiche de l'application : ce n'est **pas** le `client_secret`.
   L'abonnement Judilibre est **distinct** de l'abonnement Légifrance ; une
   application peut souscrire aux deux.

Un environnement **bac à sable** (`sandbox`) est disponible pour tester sans
toucher la production : mettre `LEGIFRANCE_ENV=sandbox`. Attention, les
identifiants sandbox et production sont **distincts** (des identifiants
sandbox contre l'endpoint prod renvoient `invalid_client`), et les données du
bac à sable **ne reflètent pas le droit en vigueur** : ne jamais conclure sur
la vigueur d'un texte depuis la sandbox.

### Étape 2 — Configurer les identifiants

Deux méthodes, au choix. Dans les deux cas, **le secret ne doit jamais entrer
dans le dépôt**.

**A. Fichier `.env` (recommandé — rien à réexporter à chaque session)**

```bash
cp skill/scripts/.env.example skill/scripts/.env
# éditer .env et coller les deux identifiants
```

Le script charge automatiquement un `.env` trouvé (dans l'ordre) via
`$LEGIFRANCE_DOTENV`, puis dans le dossier courant, puis à côté du script.
`.env` est **déjà gitignoré**.

**B. Variables d'environnement (sessions ponctuelles, CI)**

```bash
export LEGIFRANCE_CLIENT_ID="votre_client_id"
export LEGIFRANCE_CLIENT_SECRET="votre_client_secret"
export LEGIFRANCE_ENV="prod"        # ou "sandbox" (défaut : prod)
export JUDILIBRE_KEY_ID="votre_cle_api"   # optionnel — jurisprudence judiciaire
export JUDILIBRE_ENV="prod"               # optionnel — défaut : LEGIFRANCE_ENV
```

> Une variable déjà exportée **prime** sur la valeur du `.env` : pratique pour
> surcharger ponctuellement sans éditer le fichier.

**Authentification Judilibre — deux modes, essayés dans l'ordre.** Selon la
façon dont l'application PISTE a été déclarée, Judilibre accepte soit
l'en-tête `KeyId` documenté par la Cour de cassation, soit le jeton OAuth 2.0
`Authorization: Bearer` commun aux API PISTE. Le script tente `KeyId` en
premier si `JUDILIBRE_KEY_ID` est défini, puis **bascule automatiquement** sur
le jeton OAuth en cas de 401/403. Aucune configuration supplémentaire n'est
nécessaire si l'application est abonnée à Judilibre avec les mêmes
identifiants que Légifrance.

`JUDILIBRE_ENV` permet de viser un environnement différent pour chaque API —
par exemple Légifrance en production et Judilibre en bac à sable. Laissée
vide, elle reprend `LEGIFRANCE_ENV`.

### Étape 3 — Utiliser

```bash
# Vérifier l'authentification et la disponibilité de l'API
python legifrance.py ping

# Récupérer un article par identifiant LEGIARTI (métadonnées + texte)
python legifrance.py article LEGIARTI000006419288

# Version applicable à une date donnée
python legifrance.py article --date 2024-01-01 LEGIARTI000006419288

# Rechercher un article par numéro, filtré sur un code
# La lettre de partie est facultative : « 2212-2 » teste aussi L/R/D/A.
python legifrance.py search "2212-2" --code CGCT

# Même recherche dans la version du code en vigueur à une date passée
python legifrance.py search "2212-2" --code CGCT --date 2010-01-01

# Jurisprudence administrative / constitutionnelle — recherche PAR NUMÉRO,
# renvoie l'identifiant officiel de la décision (best-effort)
python legifrance.py ceta "440258"           # Conseil d'État (fond CETAT)
python legifrance.py constit "2021-940 QPC"  # Conseil constitutionnel (CONSTIT)

# Jurisprudence judiciaire (Judilibre) — recherche PLEIN TEXTE, pas par numéro
python legifrance.py juri "soins sans consentement" --jurisdiction cc
python legifrance.py juri "police municipale" --date-start 2020-01-01 --publication b

# Texte intégral d'une décision, par l'identifiant renvoyé par `juri`
python legifrance.py decision 5fca...

# Valeurs acceptées par un filtre Judilibre (chambre, formation, thème…)
python legifrance.py taxonomy chamber --jurisdiction cc

# Sortie JSON brute (chaînage / archivage)
python legifrance.py article --json LEGIARTI000006419288
```

> **Provenance de la jurisprudence.** La règle de provenance (v2.3.0) vise
> aussi les n° de pourvoi / requête / décision. Les deux routes n'offrent pas
> le même niveau :
>
> - **Judilibre** (`juri` → `decision`) — provenance **forte** : `decision`
>   restitue le **texte intégral** de la décision par son identifiant. Une
>   décision citée après `decision` est vérifiée, pas devinée.
> - **Légifrance** (`ceta`, `constit`) — provenance **best-effort** :
>   recherche par numéro renvoyant le seul **identifiant officiel**
>   (`CETATEXT` / `CONSTEXT`). Confirmer formation, date et publication
>   (Lebon / recueil) sur la source officielle **avant** citation.
>
> Dans les deux cas, un identifiant non récupéré ne se reconstitue jamais de
> mémoire : il est omis ou marqué `⚠️ non vérifié — identifiant non récupéré`.

### Ce que la commande `article` restitue

- l'**identifiant** confirmé (`LEGIARTI…`) — *provenance vérifiée* ;
- le **statut** (`VIGUEUR`, `ABROGE`, `MODIFIE`, …) ;
- la **date d'entrée en vigueur** (et de fin le cas échéant) ;
- le **texte** de l'article ;
- une **citation normalisée** pré-remplie au format `format-citation.md`.

### Codes de sortie (contrat avec le skill)

| Code | Sens | Conduite côté skill |
|------|------|---------------------|
| 0 | succès | citation autorisée (provenance acquise) |
| 2 | identifiants absents / mauvais usage | **basculer sur la voie de repli web** — sans le dire, sans demander de clé |
| 3 | échec d'authentification PISTE | vérifier les identifiants / l'abonnement |
| 4 | échec API (HTTP, réseau, contenu illisible) | **déclencheur d'abstention §7** |
| 5 | ressource introuvable (article, décision ou recherche sans résultat) | **abstention** — ne pas inventer (mode 1) |

Le code **2 n'est pas une panne** : c'est la bascule normale vers la voie de
repli web (d'où le préfixe `⚠️` et non `❌`). Le skill poursuit son analyse
avec `web_search`/`web_fetch` sur domaines officiels et **ne demande jamais de
clé à l'utilisateur** — voir SKILL.md, étape 2, *échelle de récupération*.

Les codes 4 et 5 valent **abstention motivée** : pas de citation sans
récupération réussie. Un identifiant `LEGIARTI` qui ne ressort d'aucun appel
réussi ne doit jamais figurer dans une sortie sans le marqueur
`⚠️ non vérifié — identifiant non récupéré`.

### Dépannage

| Symptôme | Cause probable | Action |
|----------|----------------|--------|
| `code 2` malgré un `.env` | `.env` hors des chemins cherchés | `export LEGIFRANCE_DOTENV=/chemin/.env` ou lancer depuis la racine du repo |
| `code 3` à `ping` | secret erroné, ou application non abonnée à Légifrance | revérifier `client_secret` ; confirmer l'abonnement sur piste.gouv.fr |
| `code 4` répété | endpoint indisponible / quota | réessayer ; en cas de persistance, le skill bascule en abstention |
| `search` sans résultat | numéro absent du code, ou absent de la version interrogée | vérifier le numéro ; élargir en retirant `--code` ; essayer une autre `--date` |
| `search` trouve l'article dans un autre code | homonymie de numérotation entre codes | ajouter `--code` pour restreindre |
| `⚠️ Judilibre indisponible` au `ping` | application non abonnée à Judilibre, ou CGU non acceptées | souscrire l'API JUDILIBRE sur piste.gouv.fr (étape 1.5), ou renseigner `JUDILIBRE_KEY_ID` |
| `code 3` sur `juri`/`decision` alors qu'`article` fonctionne | les **deux** modes d'authentification Judilibre ont été refusés | vérifier la clé `KeyId` (≠ `client_secret`) et l'abonnement Judilibre, distinct de Légifrance |
| Judilibre répond des données inattendues | `JUDILIBRE_ENV` vise un autre environnement que `LEGIFRANCE_ENV` | comparer les deux URL affichées par `ping` |

### Limites connues

- Les schémas de réponse de l'API Légifrance évoluent : la commande `article`
  (endpoint `consult/getArticle`) est stable et prioritaire ; `search`
  (endpoint `/search`, fond `CODE_DATE`) reste un point d'entrée de
  **recherche** — d'où l'invite à **confirmer** tout identifiant via
  `article <LEGIARTI>` avant citation.
- `search` ne couvre que les **codes**. Lois, décrets et arrêtés non codifiés
  (fond `LODA`) n'y sont pas cherchés : passer par les gabarits web (§2 de
  `gabarits-requetes.md`), puis confirmer par `article <LEGIARTI>`.
- `search` interroge **une seule version** du code, celle en vigueur à la date
  demandée (`--date`, défaut : aujourd'hui). Un article abrogé avant cette
  date n'y figure pas : l'interroger à une date où il était applicable.
- Le *payload* de `search` dépend de facettes non interchangeables du fond
  `CODE_DATE` : `NOM_CODE` attend le **libellé** du code (un identifiant
  `LEGITEXT` y renvoie zéro résultat *sans erreur*), et `TEXT_LEGAL_STATUS`
  comme `ARTICLE_LEGAL_STATUS` y déclenchent un **HTTP 500**. Ne pas les
  réintroduire pour filtrer sur la vigueur : c'est `DATE_VERSION` qui la
  porte. Détail dans la *docstring* de `cmd_search`.
- La **jurisprudence administrative et constitutionnelle** (`ceta`/`constit`,
  fonds `CETAT`/`CONSTIT`) est prise en charge en **recherche best-effort par
  numéro** : le format du numéro est sensible, d'où l'invite à confirmer la
  décision sur la source officielle. Seul l'**identifiant** est restitué, pas
  le texte intégral.
- La **jurisprudence judiciaire** passe par **Judilibre** (`juri`, `decision`,
  `taxonomy`) : la recherche y est **plein texte** — lui passer un n° de
  pourvoi comme requête n'est pas une recherche par numéro — et le **texte
  intégral** d'une décision est restitué par `decision <identifiant>`. Le fond
  `JURI` de Légifrance n'est plus interrogé : Judilibre le remplace.
- Les **circulaires** ne sont pas couvertes : utiliser les gabarits
  `web_fetch`/`web_search` de `references/gabarits-requetes.md`.
- Vérifier annuellement les endpoints lors de la revue (`maintenance.md` §3).

---

## Note de sécurité — pourquoi BYOK et pas une clé embarquée

Un secret livré dans un paquet public **n'est plus un secret** : quiconque
installe le skill peut l'extraire. Embarquer une clé partagée exposerait le
quota et l'identité de son auteur, sous sa responsabilité. Le flux
`client_credentials` de PISTE est un flux *confidential client*, prévu pour
rester côté utilisateur/serveur, jamais distribué. D'où le modèle BYOK :
le code va dans le dépôt, **le secret va dans l'environnement** — les deux ne
se croisent jamais. Si une clé a été exposée par accident, la **régénérer**
sur piste.gouv.fr (rotation).

> Le dossier `scripts/` fait partie du paquet skill : il est copié avec
> `SKILL.md`, `CHANGELOG.md` et `references/` lors de l'installation
> (`.env` exclu — il reste local).
