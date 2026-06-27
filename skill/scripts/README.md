# `scripts/` — outillage de récupération en source primaire

Ce dossier matérialise le **Palier 3** du skill `recherche-juridique` :
remplacer le scraping fragile de Légifrance par un accès **API officiel**,
de sorte que P1 (primarité) et la **règle de provenance** (v2.3.0) soient
satisfaits par un appel d'outil déterministe plutôt que par la mémoire du
modèle.

> **Modèle « apporte ta clé » (BYOK).** Le skill est distribué publiquement :
> il n'embarque **aucune** clé. Chaque utilisateur configure **sa propre**
> clé PISTE (gratuite). Une clé partagée dans un paquet public ne serait plus
> un secret — voir la note de sécurité en bas de page.

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

CLI Python (bibliothèque standard uniquement, Python 3.8+) interrogeant l'API
Légifrance exposée via la plateforme **PISTE** de la DILA.

### Étape 1 — Obtenir des identifiants PISTE (gratuit)

1. Créer un compte sur <https://piste.gouv.fr>.
2. Menu **« Applications »** → créer une application.
3. L'**abonner à l'API « Légifrance »** (catalogue des API → Légifrance →
   souscrire). L'abonnement peut demander une courte validation.
4. Dans la fiche de l'application, relever le **`client_id`** et le
   **`client_secret`**.

Un environnement **bac à sable** (`sandbox`) est disponible pour tester sans
toucher la production : mettre `LEGIFRANCE_ENV=sandbox`.

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
```

> Une variable déjà exportée **prime** sur la valeur du `.env` : pratique pour
> surcharger ponctuellement sans éditer le fichier.

### Étape 3 — Utiliser

```bash
# Vérifier l'authentification et la disponibilité de l'API
python legifrance.py ping

# Récupérer un article par identifiant LEGIARTI (métadonnées + texte)
python legifrance.py article LEGIARTI000006419288

# Version applicable à une date donnée
python legifrance.py article --date 2024-01-01 LEGIARTI000006419288

# Rechercher un article par numéro, filtré sur un code
python legifrance.py search "2212-2" --code CGCT

# Sortie JSON brute (chaînage / archivage)
python legifrance.py article --json LEGIARTI000006419288
```

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
| 2 | identifiants manquants / mauvais usage | configurer la clé (voir étape 2) |
| 3 | échec d'authentification PISTE | vérifier les identifiants / l'abonnement |
| 4 | échec API (HTTP, réseau, contenu illisible) | **déclencheur d'abstention §7** |
| 5 | ressource introuvable (article inexistant) | **abstention** — ne pas inventer (mode 1) |

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
| `search` sans résultat | payload spécifique au fond | confirmer via `article <LEGIARTI>` (voir limites) |

### Limites connues

- Les schémas de réponse de l'API Légifrance évoluent : la commande `article`
  (endpoint `consult/getArticle`) est stable et prioritaire ; `search`
  (endpoint `/search`, fond `CODE_DATE`) est **best-effort** et peut demander
  un ajustement du *payload* selon le fond interrogé — d'où l'invite à
  **confirmer** tout identifiant via `article <LEGIARTI>`.
- Le script ne couvre pas (encore) la jurisprudence (fonds `JURI`, `CETAT`,
  `CONSTIT`) ni les circulaires : pour ces sources, utiliser les gabarits
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
