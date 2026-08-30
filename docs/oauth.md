# Authentification OAuth 2.1 du serveur MCP public

État vérifié le 30 août 2026.

## Pourquoi une authentification

Les clés PISTE (Légifrance, Judilibre) sont conservées côté serveur et ne sont
jamais renvoyées au client. Ce point est conforme aux CGU. Le risque résiduel
est ailleurs : sans authentification, toute personne connaissant l'URL publique
consomme les API officielles **sous l'application PISTE du titulaire des clés**,
sans quota individuel ni imputabilité.

Les CGU PISTE réservent la clé à l'application enregistrée et laissent son
titulaire responsable de l'usage et des quotas ; les CGU Judilibre interdisent
en outre le profilage des magistrats et des greffiers. Une passerelle publique
anonyme rend ces obligations invérifiables.

L'authentification déplace donc l'usage vers un sujet identifié : quota par
utilisateur, journal imputable, révocation possible.

## Architecture retenue

| Liaison | Mécanisme |
|---|---|
| ChatGPT → serveur MCP | OAuth 2.1, jeton porteur signé |
| Serveur MCP → serveur d'autorisation | Vérification locale du JWKS public |
| Serveur MCP → PISTE | Clés du titulaire, variables d'environnement |
| Utilisateur final → clés PISTE | Aucun accès, jamais |

Le serveur MCP est un **Resource Server** : il ne délivre aucun jeton,
n'héberge aucun mot de passe et ne stocke aucun compte. Il publie ses
métadonnées (RFC 9728) et vérifie chaque jeton contre les clés publiques de
l'émetteur. Aucun état d'authentification n'est conservé en mémoire, ce qui
rend le service insensible aux redémarrages d'instance.

## Exigences imposées au serveur d'autorisation

ChatGPT découvre et s'enregistre seul. L'émetteur choisi doit donc offrir :

1. les métadonnées `/.well-known/oauth-authorization-server` (RFC 8414) ;
2. l'enregistrement dynamique de client (RFC 7591) ;
3. le flux `authorization_code` avec PKCE (S256) ;
4. l'indicateur de ressource `resource` (RFC 8707), ou à défaut une audience
   fixe configurable ;
5. des jetons signés en RS256 ou ES256, exposés via un JWKS public.

Auth0, Stytch, Clerk, WorkOS et Descope remplissent ces cinq conditions.
Les algorithmes symétriques (`HS*`) sont refusés par le serveur : aucun secret
n'est partagé avec l'émetteur.

## Configuration côté émetteur

1. Créer une API (ou « ressource protégée ») dont l'identifiant est
   exactement `https://droit-francais-skill.onrender.com/mcp`.
2. Déclarer la portée `legal:read` et l'accorder par défaut.
3. Activer l'enregistrement dynamique de client.
4. Restreindre les URI de redirection au domaine de ChatGPT indiqué par la
   console développeur.
5. Relever l'URL de l'émetteur (`issuer`) et vérifier que
   `<issuer>/.well-known/jwks.json` répond.

## Configuration côté serveur

Variables à définir sur l'hébergeur :

```bash
MCP_AUTH_MODE=oauth
MCP_PUBLIC_URL=https://droit-francais-skill.onrender.com
MCP_OAUTH_ISSUER=https://<votre-emetteur>
# Facultatif — valeurs déduites si absentes :
# MCP_OAUTH_AUDIENCE=https://droit-francais-skill.onrender.com/mcp
# MCP_OAUTH_JWKS_URL=https://<votre-emetteur>/.well-known/jwks.json
# MCP_OAUTH_REQUIRED_SCOPES=legal:read
MCP_USER_CALLS_PER_MINUTE=20
```

Contrôle avant déploiement, sans lancer le service :

```bash
python mcp_server/server.py --check-config
```

En production, `MCP_AUTH_MODE=disabled` fait échouer le démarrage.

## Vérification après déploiement

```bash
# 1. Métadonnées de ressource protégée
curl -s https://droit-francais-skill.onrender.com/.well-known/oauth-protected-resource/mcp

# 2. Refus attendu sans jeton : 401 + en-tête WWW-Authenticate
curl -si -X POST https://droit-francais-skill.onrender.com/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | head -n 8

# 3. Métadonnées du serveur d'autorisation
curl -s https://<votre-emetteur>/.well-known/oauth-authorization-server
```

La réponse attendue en 2 comporte
`www-authenticate: Bearer error="invalid_token", …, resource_metadata="…"`.
C'est cet en-tête qui déclenche la découverte automatique par ChatGPT.

## Contrôles appliqués à chaque jeton

* signature vérifiée contre le JWKS de l'émetteur (RS256/ES256 seulement) ;
* `iss` strictement égal à l'émetteur configuré ;
* `aud` contenant l'audience configurée — un jeton émis pour une autre API est
  refusé, ce qui bloque la réutilisation d'un jeton dérobé ailleurs ;
* `exp` et `nbf` contrôlés, avec 30 secondes de tolérance d'horloge ;
* portées requises vérifiées avant l'exécution de l'outil ;
* quota glissant par sujet authentifié, distinct du quota global d'instance.

Un échec renvoie `401` sans détail exploitable. Le motif technique est
journalisé sous forme de nom de classe d'erreur, jamais avec le jeton.

## Limites connues

* Le quota par utilisateur est local à une instance. Avec plusieurs réplicas,
  il faut une limitation partagée au niveau de la plateforme.
* La révocation dépend de l'émetteur : le serveur ne consulte pas d'endpoint
  d'introspection et respecte donc la durée de vie du jeton.
* Le contrôle des usages interdits par les CGU Judilibre (profilage des
  magistrats et des greffiers) reste à implémenter dans les outils de
  jurisprudence ; l'authentification le rend imputable, pas impossible.
