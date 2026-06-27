# `scripts/` — outillage de récupération en source primaire

Ce dossier matérialise le **Palier 3** du skill `recherche-juridique` :
remplacer le scraping fragile de Légifrance par un accès **API officiel**,
de sorte que P1 (primarité) et la **règle de provenance** (v2.3.0) soient
satisfaits par un appel d'outil déterministe plutôt que par la mémoire du
modèle.

---

## `legifrance.py`

CLI Python (bibliothèque standard uniquement, Python 3.8+) interrogeant l'API
Légifrance exposée via la plateforme **PISTE** de la DILA.

### 1. Obtenir des identifiants PISTE

1. Créer un compte sur <https://piste.gouv.fr>.
2. Créer une **application** et l'abonner à l'API **« Légifrance »**.
3. Relever le `client_id` et le `client_secret` de l'application.

L'API Légifrance est gratuite ; l'abonnement peut demander une courte
validation. Un environnement **bac à sable** (`sandbox`) est disponible pour
les tests.

### 2. Configurer l'environnement

Ne **jamais** écrire les secrets dans le dépôt. Les passer par variables
d'environnement :

```bash
export LEGIFRANCE_CLIENT_ID="votre_client_id"
export LEGIFRANCE_CLIENT_SECRET="votre_client_secret"
export LEGIFRANCE_ENV="prod"        # ou "sandbox" (défaut : prod)
```

### 3. Utiliser

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
| 2 | identifiants manquants / mauvais usage | corriger l'appel |
| 3 | échec d'authentification PISTE | configurer / vérifier les secrets |
| 4 | échec API (HTTP, réseau, contenu illisible) | **déclencheur d'abstention §7** |
| 5 | ressource introuvable (article inexistant) | **abstention** — ne pas inventer (mode 1) |

Les codes 4 et 5 valent **abstention motivée** : pas de citation sans
récupération réussie. Un identifiant `LEGIARTI` qui ne ressort d'aucun appel
réussi ne doit jamais figurer dans une sortie sans le marqueur
`⚠️ non vérifié — identifiant non récupéré`.

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

> Le dossier `scripts/` fait partie du paquet skill : il est copié avec
> `SKILL.md`, `CHANGELOG.md` et `references/` lors de l'installation.
