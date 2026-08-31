# Check-list de validation du connecteur ChatGPT

Cette check-list ferme la validation de bout en bout. Elle est **manuelle par
nécessité** : le harnais automatisé
([`tests/test_oauth_end_to_end.py`](../tests/test_oauth_end_to_end.py)) prouve
que le serveur se comporte correctement — jeton valide, jetons refusés, quotas,
portées — mais il ne peut pas prouver qu'un utilisateur parvient à se connecter
**depuis ChatGPT**, ce qui est le critère de fin réel.

Les deux volets sont complémentaires : le harnais empêche la régression et
tourne en CI, cette check-list constate le résultat.

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
| 1.1 | Ouvrir le formulaire de création de connecteur dans ChatGPT | Le formulaire s'ouvre | |
| 1.2 | Saisir l'URL `https://droit-francais-skill.onrender.com/mcp` | Les endpoints OAuth se **pré-remplissent seuls** | |
| 1.3 | Valider | Aucune erreur de métadonnée ni de PKCE | |

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
