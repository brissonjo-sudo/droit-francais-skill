# Check-list de validation du connecteur ChatGPT

Cette check-list ferme la validation de bout en bout. Elle est **manuelle par
nécessité** : le harnais automatisé
([`tests/test_oauth_end_to_end.py`](../tests/test_oauth_end_to_end.py)) prouve
que le serveur se comporte correctement — jeton valide, jetons refusés, quotas,
portées — mais il ne peut pas prouver qu'un utilisateur parvient à se connecter
**depuis ChatGPT**, ce qui est le critère de fin réel.

Les deux volets sont complémentaires : le harnais empêche la régression et
tourne en CI, cette check-list constate le résultat.

## Raccourci : valider les outils sans navigateur

Les sections 3 à 6 ci-dessous n'ont pas besoin de ChatGPT. Elles ont besoin
d'un **jeton d'accès valide**, que l'on peut obtenir en une commande via le
flux *client credentials*, sans écran de connexion.

### 1. Créer une application machine à machine dans Auth0

*Applications → Create Application → Machine to Machine*, autorisée sur l'API
dont l'identifiant est `https://droit-francais-skill.onrender.com/mcp`. Cocher
la portée `legal:read` si le contrôle de portée est réactivé.

### 2. Demander un jeton

Remplacer les deux valeurs entre chevrons. **Ne jamais coller le résultat dans
un fichier du dépôt, ni dans une conversation.**

```bash
export MCP_ACCESS_TOKEN=$(curl -s --request POST   --url https://dev-7soa32jfmxpejzhs.eu.auth0.com/oauth/token   --header 'content-type: application/json'   --data '{"client_id":"<ID>","client_secret":"<SECRET>","audience":"https://droit-francais-skill.onrender.com/mcp","grant_type":"client_credentials"}'   | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
```

### 3. Lancer la sonde

```bash
python tests/check_live_tools.py
```

Elle vérifie la découverte et les annotations, puis appelle réellement chacun
des six outils. Elle mesure les premiers appels Légifrance et Judilibre,
contrôle les lectures avec texte, identifiant et provenance officielle, la datation, le parcours
`search → fetch` et l'absence non inventée. Si les valeurs des clés fournisseur
existent localement, elle vérifie qu'elles ne sont pas renvoyées ; sinon elle
signale honnêtement que cette comparaison n'a pas pu être faite. Le jeton est
lu dans l'environnement, jamais affiché ni écrit.

Cette sonde consomme le quota PISTE du titulaire, comme n'importe quel appel
réel.

> **Ce raccourci ne remplace pas les sections 1 et 2.** Un jeton machine à
> machine prouve que le serveur répond correctement à un porteur authentifié ;
> il ne prouve pas qu'un utilisateur parvient à créer le connecteur et à
> s'autoriser depuis ChatGPT, qui est le critère de fin réel.

---

## 0. Prérequis — état du serveur

À faire avant d'ouvrir ChatGPT. Ces trois commandes ne demandent aucun secret.

```bash
curl -s https://droit-francais-skill.onrender.com/health
```

Attendu : `{"status":"ok","version":"…","auth":"oauth"}`. Si `auth` vaut
`disabled`, s'arrêter — la suite n'a pas de sens.

```bash
python tests/check_oauth_metadata.py https://droit-francais-skill.onrender.com --discover
```

Attendu : trois lignes vertes. Cette sonde compare l'émetteur publié à celui du
document de découverte **caractère pour caractère** et vérifie le refus
anonyme. Un échec ici bloque tout : ChatGPT applique la même comparaison.

> Le défaut le plus fréquent est une barre oblique finale de différence.
> Voir [oauth.md](oauth.md), section « Écriture exacte de l'émetteur ».

---

## 1. Création du connecteur

| # | Étape | Attendu | Constaté |
|---|---|---|---|
| 1.1 | `chatgpt.com` → **Settings → Security and login** → activer **Developer mode**, puis bouton **+** | Le formulaire de création s'ouvre | |
| 1.2 | Sur `chatgpt.com/plugins`, bouton **+** : nom, description, puis sous **Connection** l'URL `https://droit-francais-skill.onrender.com/mcp`. Aucun champ d'authentification à remplir — elle est découverte | La connexion se crée sans réglage d'authentification | |
| 1.3 | Valider | Les six outils apparaissent ; aucune erreur de métadonnée ni de PKCE | |

> Si ChatGPT réclame `code_challenge_methods_supported` avec `S256`, le
> formulaire a été ouvert avant que le serveur ne passe en mode OAuth : fermer
> et recréer le connecteur depuis le début. Voir la section « Dépannage » de
> [oauth.md](oauth.md).

## 2. Autorisation

| # | Étape | Attendu | Constaté |
|---|---|---|---|
| 2.1 | Lancer la connexion | Redirection vers l'écran Auth0 | |
| 2.2 | S'authentifier | Retour à ChatGPT sans erreur | |
| 2.3 | Vérifier l'état du connecteur | « Connecté » | |

## 3. Découverte des outils

| # | Étape | Attendu | Constaté |
|---|---|---|---|
| 3.1 | Lister les outils exposés | **Six** outils : `search`, `fetch`, `search_articles`, `get_article`, `search_case_law`, `get_decision` | |
| 3.2 | Vérifier les annotations | Tous en lecture seule, non destructifs | |

## 4. Appel Légifrance réel

> Automatisable par `check_live_tools.py` — voir le raccourci ci-dessus.

Demander par exemple : « Recherche l'article L. 2212-2 du Code général des
collectivités territoriales. »

| # | Point de contrôle | Attendu | Constaté |
|---|---|---|---|
| 4.1 | Un outil Légifrance est appelé | `search_articles` ou `get_article` | |
| 4.2 | La réponse cite un identifiant `LEGIARTI…` | Identifiant réel, non inventé | |
| 4.3 | Le statut juridique est présent | `VIGUEUR` ou autre état explicite | |
| 4.4 | La date de référence est explicite | `as_of_date` et `date_basis` présents | |
| 4.5 | Aucune clé fournisseur n'apparaît | Aucun `LEGIFRANCE_*`, `JUDILIBRE_*`, `PISTE_*` | |

## 5. Appel JUDILIBRE réel

> Automatisable par `check_live_tools.py` — voir le raccourci ci-dessus.

Demander par exemple : « Trouve une décision récente de la Cour de cassation
sur la responsabilité du fait des choses. »

| # | Point de contrôle | Attendu | Constaté |
|---|---|---|---|
| 5.1 | Un outil Judilibre est appelé | `search_case_law` ou `get_decision` | |
| 5.2 | La décision est identifiée | Juridiction, date, numéro | |
| 5.3 | L'URL pointe vers une source officielle | `courdecassation.fr` | |
| 5.4 | Aucune clé fournisseur n'apparaît | Aucun identifiant technique en clair | |

## 6. Comportement en cas d'échec

| # | Étape | Attendu | Constaté |
|---|---|---|---|
| 6.1 | Demander un article inexistant (`L. 9999-1` d'un code réel) | Le modèle dit qu'il ne l'a pas trouvé | |
| 6.2 | Vérifier la formulation | Une erreur d'accès n'est **jamais** présentée comme une vérification réussie | |
| 6.3 | Vérifier le message d'erreur | Aucune valeur sensible, aucun détail technique exploitable | |

## 7. Quota

| # | Étape | Attendu | Constaté |
|---|---|---|---|
| 7.1 | Enchaîner plus de `MCP_USER_CALLS_PER_MINUTE` appels en une minute | Message explicite de quota individuel | |
| 7.2 | Attendre une minute puis réessayer | Le service redevient disponible | |

---

## Restitution

Reporter les constats dans la colonne « Constaté », puis les transmettre. Un
seul point rouge suffit à laisser la phase 5 ouverte : les phases suivantes
(conformité, dossier de soumission, publication) en dépendent.

Le résultat est consigné dans
[roadmap-chatgpt-plugin.md](roadmap-chatgpt-plugin.md).
