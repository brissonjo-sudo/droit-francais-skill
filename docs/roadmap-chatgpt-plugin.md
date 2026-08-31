# Feuille de route — plugin ChatGPT

Suivi de la finalisation du serveur MCP public comme plugin ChatGPT. Mis à jour
à la fin de chaque phase. Le skill historique et son usage hors plugin ne sont
modifiés par aucune de ces phases.

| Phase | Objet | Branche | État |
|---|---|---|---|
| 1 | Débloquer OAuth (écriture de l'émetteur) | `fix/oauth-issuer-metadata` | Code fusionné (PR #14) — attend la variable Render |
| 2 | Rendre la CI contraignante | `ci/restore-full-validation` | Terminée (PR #17 fusionnée, `main` protégée) |
| 3 | Inventaire du checkout local | — | Terminée (sans objet) |
| 4 | Retirer les artefacts de développement | `chore/remove-patch-artifacts` | Terminée (PR #15 fusionnée) |
| 5 | Validation OAuth et MCP de bout en bout | `test/oauth-end-to-end` | Harnais livré — check-list manuelle à exécuter |
| 6 | Sécurité et conformité | — | À faire |
| 7 | Dossier de soumission | `release/chatgpt-submission` | À faire |
| 8 | Publication progressive | — | À faire |

---

## Phase 1 — Débloquer OAuth

### Défaut corrigé

Le connecteur ChatGPT ne pouvait pas aboutir : la métadonnée RFC 9728 vers
laquelle ChatGPT est renvoyé annonçait un émetteur différant d'un caractère de
celui publié par Auth0. Relevé sur la production le 31/08/2026 :

| Source | Valeur publiée |
|---|---|
| Auth0, champ `issuer` | `https://dev-7soa32jfmxpejzhs.eu.auth0.com/` |
| `/.well-known/oauth-protected-resource` | `https://dev-7soa32jfmxpejzhs.eu.auth0.com/` |
| `/.well-known/oauth-protected-resource/mcp` | `https://dev-7soa32jfmxpejzhs.eu.auth0.com` |

Le `WWW-Authenticate` du `401` anonyme pointe sur la route `/mcp` — la seule
des deux qui était fausse.

### Cause racine

`_https_url()` appliquait `.rstrip("/")` à `MCP_OAUTH_ISSUER`. La valeur
tronquée était transmise à `AuthSettings.issuer_url`, que le SDK MCP 2.x
sérialise **verbatim** : son modèle `ProtectedResourceMetadata` porte
`model_config = ConfigDict(url_preserve_empty_path=True)`, justement parce que
la comparaison d'émetteur au sens RFC 8414/9207 est une égalité de chaînes.

Deux conséquences ont orienté le correctif :

* une route personnalisée ne pouvait pas corriger `/mcp` — le SDK monte les
  routes personnalisées en dernier, avec la priorité la plus basse ; le
  correctif devait donc porter sur la valeur remise au SDK, pas sur le routage ;
* le défaut était **invisible en local** : `requirements-mcp.txt` déclarait
  `mcp>=1.27,<3`, le poste avait `1.27` (où pydantic rajoutait la barre tout
  seul) tandis que CI et Render installaient `2.1.1`.

### Modifications

* `mcp_server/runtime.py` — `_https_url()` accepte `strip_trailing_slash` ;
  `MCP_OAUTH_ISSUER` est conservé verbatim, `MCP_PUBLIC_URL` reste tronqué.
  Nouvelle propriété `oauth_issuer_base`, réservée aux concaténations d'URL, sur
  laquelle bascule la dérivation du JWKS — ce qui supprime la double barre qui
  obligeait jusqu'ici la documentation à interdire la barre finale.
* `mcp_server/server.py` — suppression de `_canonical_issuer()`, qui *inventait*
  une barre quand le chemin était vide (juste pour Auth0, faux pour un émetteur
  dont la forme canonique n'en porte pas). La route racine sert désormais
  `SETTINGS.oauth_issuer` verbatim. Ajout de `--check-issuer`.
* `mcp_server/auth.py` — inchangé sur le fond. La tolérance à la barre finale
  dans la revendication `iss` d'un jeton est conservée et désormais documentée
  comme distincte de l'égalité stricte exigée côté métadonnée.
* `requirements-mcp.txt` — `mcp==2.1.1` et `PyJWT[crypto]==2.13.0` figés, pour
  que poste, CI et Render se comportent identiquement sur ce point précis.

### Contrôles exécutés

* Suite complète : **69 tests, tous verts**, avec le SDK épinglé (`mcp 2.1.1`).
* 9 tests ajoutés dans `IssuerCanonicalisationTests`, dont trois qui exercent
  réellement les deux routes : la route racine est appelée via son handler, la
  route `/mcp` est reconstruite comme le fait `create_protected_resource_routes`.
  Le test de la route SDK sert aussi de garde-fou de version.
* Sonde HTTP locale, serveur démarré en `MCP_AUTH_MODE=oauth` : les deux routes
  publient une chaîne identique à la valeur configurée, **avec comme sans**
  barre finale, et le `POST /mcp` anonyme rend `401` avec un `resource_metadata`
  pointant sur la route `/mcp`.
* `--check-issuer` contre le locataire Auth0 réel : accepte l'écriture exacte,
  rejette l'autre avec un message explicite et un code de sortie `2`.

### Action humaine requise

Le code seul ne peut pas produire le critère de fin. Sur Render, passer :

```
MCP_OAUTH_ISSUER=https://dev-7soa32jfmxpejzhs.eu.auth0.com/
```

(barre oblique finale incluse), puis redéployer. Vérifier ensuite que les trois
valeurs de la section « Vérification après déploiement » de
[oauth.md](oauth.md) sont identiques.

---

## Phase 2 — Rendre la CI contraignante

### Constat corrigé

L'énoncé de mission supposait la CI cassée : « aucun workflow n'est associé au
commit `75fc5bd` ». C'est inexact. Le workflow existait bien à ce commit, s'est
déclenché sur `push` et **a réussi** (31/08/2026, 11:07 UTC). Les versions
d'actions employées (`actions/checkout@v7`, `actions/setup-python@v7`) existent
également. Il n'y avait donc rien à restaurer.

La phase porte sur ce que la CI **ne garantissait pas**.

### Trous fermés

* **Aucune couverture des métadonnées OAuth.** La sonde HTTP existante tournait
  en mode anonyme : ni les routes `.well-known`, ni le refus `401` n'étaient
  vérifiés. C'est très exactement ce qui a laissé passer le défaut de la
  phase 1. Nouvelle sonde `tests/check_oauth_metadata.py`, exécutée en CI sur
  **les deux écritures** de l'émetteur, avec un émetteur factice : aucun jeton,
  aucun secret. Elle vise aussi la production avec `--discover`, qui lit
  l'émetteur attendu dans le document de découverte.
* **Divergence de versions invisible.** Étape `pip list` ajoutée : une
  divergence poste / CI / Render se lit désormais dans le journal, au lieu de
  devoir être déduite d'un échec de test.
* **Fragilités du script d'étape.** Le shell d'Actions tourne en `set -e` : les
  attentes de démarrage sont testées par un `if`, l'échec de la sonde est capté
  explicitement, chaque écriture utilise un port distinct — ne jamais dépendre
  du recyclage d'un port entre deux itérations — et un garde-fou distingue un
  serveur qui n'a pas démarré d'une métadonnée fautive.

### Reste à faire — protection de branche

`main` n'est pas protégée : `75fc5bd` y est arrivé par push direct, ce qui
explique le scénario « PR #10 rejouée sur main ». À activer :

* pull request obligatoire avant fusion ;
* check `checks` requis et à jour ;
* push direct interdit.

---

## Phase 3 — Inventaire du checkout local

Phase close sans intervention : l'énoncé de mission supposait des fichiers non
suivis à préserver, l'inventaire ne les trouve pas.

* Arbre de travail propre, aucun fichier non suivi ni modifié.
* `main` local strictement égal à `origin/main` (`75fc5bd`), aucun écart dans
  l'un ou l'autre sens.
* Un seul worktree, aucun worktree résiduel.
* `assets/logo-chatgpt.png` **n'existe pas** ; seul `assets/logo.png` est
  présent, et c'est bien lui que référence le manifeste.
* Aucun dossier `scripts/` à la racine ; les scripts vivent dans
  `skill/scripts/`.
* La branche `feat/oauth-mcp` (`a31e18b`) subsiste en local et sur le distant.
  Elle est laissée intacte : sa suppression sera proposée séparément.

Aucun `reset --hard`, aucune suppression, aucune synchronisation destructrice
n'a été nécessaire.

---

## Phase 4 — Retirer les artefacts de développement

Huit fichiers `.patch` (~128 Ko) à la racine, tous introduits par le seul
commit `75fc5bd`. Vérifié avant suppression : aucune référence dans le code,
les tests, la CI ou la documentation ; aucun secret ; cinq réversibles par
`git apply --check --reverse`, donc strictement redondants avec l'arbre, et les
trois autres vérifiés ligne à ligne. Règle `*.patch` et `*.diff` ajoutée au
`.gitignore`. Aucun `__pycache__`, `.pyc`, `.venv` ni sortie de test n'est
suivi par ailleurs.

`vault/` est conservé : contenu rédigé (versions historiques de la
méthodologie), pas un artefact de construction.

---

## Phase 2 — Protection de branche (complément)

Appliquée sur `main` et vérifiée par un push direct, effectivement rejeté :

| Réglage | Valeur |
|---|---|
| Check requis | `checks`, en mode strict (branche à jour exigée) |
| Pull request | Obligatoire, 0 relecture requise — un mainteneur seul peut fusionner |
| Appliqué aux administrateurs | Oui : le propriétaire non plus ne peut pas pousser directement |
| Force-push, suppression | Interdits |
| Historique linéaire | Exigé |

Le compte de relectures est volontairement à zéro : exiger une approbation
bloquerait un dépôt à mainteneur unique, sans rien ajouter à la garantie
recherchée, qui est que **la CI passe avant toute fusion**.

---

## Phase 5 — Validation de bout en bout

### Volet automatisé — livré

`tests/test_oauth_end_to_end.py` exerce la chaîne réelle en processus :
application ASGI construite par le SDK, middleware d'authentification,
transport Streamable HTTP, dispatch d'outil. Seuls le JWKS de l'émetteur
(clé RSA engendrée à la volée) et les appels aux API juridiques sont simulés.

Seize tests couvrant les scénarios 1 à 5 de la mission :

* requête anonyme refusée en `401`, avec le challenge attendu ;
* jeton valide menant à un appel d'outil réussi, imputé au `sub` du jeton ;
* refus pour audience étrangère, émetteur étranger, expiration, signature
  inconnue, sujet absent ;
* absence de détail exploitable dans le corps du refus ;
* erreur métier ne réexposant aucun secret d'environnement ;
* quota isolé par sujet, avec message explicite au dépassement, et second
  sujet toujours servi ;
* `MCP_OAUTH_REQUIRED_SCOPES=-` laissant l'authentification exigée tout en
  acceptant un jeton sans la portée ; réglage inverse refusant ce même jeton
  en `403`.

Deux points relevés en écrivant ces tests, et corrigés :

* le cas « jeton accepté » ne peut pas se vérifier sur un `POST` brut — hors
  session MCP, le transport répond `400` quel que soit le jeton, ce qui ne
  dirait rien de l'autorisation. Il porte donc sur une session complète ;
* une assertion `assertNotEqual(401, …)` aurait laissé passer un `403`, donc un
  refus de portée. Remplacée par une vérification du succès effectif.

Le harnais est joué par `unittest discover`, donc en CI à chaque PR.

### Volet manuel — à exécuter

[validation-chatgpt.md](validation-chatgpt.md) : check-list numérotée couvrant
la création du connecteur, l'autorisation Auth0, la découverte des six outils,
un appel Légifrance réel, un appel Judilibre réel, le comportement en cas
d'échec et le quota.

**La phase reste ouverte tant que cette check-list n'est pas revenue
renseignée.** Les phases 6 à 8 en dépendent.
