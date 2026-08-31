# Feuille de route — plugin ChatGPT

Suivi de la finalisation du serveur MCP public comme plugin ChatGPT. Mis à jour
à la fin de chaque phase. Le skill historique et son usage hors plugin ne sont
modifiés par aucune de ces phases.

| Phase | Objet | Branche | État |
|---|---|---|---|
| 1 | Débloquer OAuth (écriture de l'émetteur) | `fix/oauth-issuer-metadata` | Code livré — attend une action humaine |
| 2 | Rendre la CI contraignante | `ci/restore-full-validation` | À faire |
| 3 | Inventaire du checkout local | — | Terminée (sans objet) |
| 4 | Retirer les artefacts de développement | `chore/remove-patch-artifacts` | À faire |
| 5 | Validation OAuth et MCP de bout en bout | — | Bloquée par la phase 1 |
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
