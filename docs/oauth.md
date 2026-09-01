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

ChatGPT découvre l'émetteur seul à partir des métadonnées du serveur MCP.
L'émetteur choisi doit offrir :

1. les métadonnées `/.well-known/oauth-authorization-server` (RFC 8414) ;
2. le flux `authorization_code` avec PKCE (S256) ;
3. l'indicateur de ressource `resource` (RFC 8707), ou à défaut une audience
   fixe configurable ;
4. des jetons d'accès signés en RS256, exposés via un JWKS public ;
5. soit l'enregistrement dynamique de client (RFC 7591), soit un client
   prédéfini — OpenAI accepte les deux, ainsi que les documents de métadonnées
   de client (CIMD).

Auth0, Stytch, Clerk, WorkOS et Descope remplissent ces cinq conditions.
Les algorithmes symétriques (`HS*`) sont refusés par le serveur : aucun secret
n'est partagé avec l'émetteur.

## Émetteur retenu : Auth0, locataire en région EU

Le serveur d'autorisation ne conserve qu'une identité de compte. Aucune
requête juridique, aucun texte et aucune clé PISTE ne transitent par lui.
Le locataire est néanmoins créé en **région EU** (`<locataire>.eu.auth0.com`),
cohérent avec un outil destiné à des collectivités françaises.

### 1. API (ressource protégée)

| Champ | Valeur |
|---|---|
| Name | `Droit français MCP` |
| Identifier | `https://droit-francais-skill.onrender.com/mcp` |
| Signing Algorithm | `RS256` |
| Allow Offline Access | activé (jetons de rafraîchissement) |

L'identifiant doit être **exactement** l'URL du transport MCP : c'est la
valeur que le serveur exige dans la revendication `aud`.

### 2. Portée, RBAC et autorisation de l'application

Dans l'onglet **Permissions** de l'API, ajouter `legal:read`
(« Consultation des sources juridiques officielles »).

**Laisser le RBAC désactivé.** Activé, Auth0 ne place dans le jeton que les
permissions assignées à chaque utilisateur par un rôle ; sur une application
ouverte au public, aucun utilisateur n'a de rôle, le jeton arrive sans
`legal:read` et le serveur répond `403` à tout le monde. Sans RBAC, Auth0
accorde la portée demandée dès lors qu'elle est définie sur l'API.

La politique d'accès de l'API reste **Per-app authorization** : chaque
application doit être autorisée explicitement. Dans l'onglet **Application
Access** de l'API, ouvrir la ligne de l'application cliente, cliquer
**Grant Access**, cocher `legal:read` et enregistrer.

### 3. Réglages avancés du locataire

Dans **Settings → Advanced**, activer :

* **Resource Parameter Compatibility Profile** — Auth0 accepte alors le
  paramètre `resource` (RFC 8707) que les clients MCP envoient, et s'en sert
  pour fixer l'audience du jeton ;
* **Include Issuer in Authorization Responses** — ajoute `iss` à la réponse
  d'autorisation et ferme la classe d'attaques par confusion d'émetteur.

Renseigner en complément **Default Audience** (Tenant Settings → API
Authorization Settings) avec le même identifiant d'API. Sans audience, Auth0
délivre un jeton opaque destiné à `/userinfo`, que le serveur refuse : c'est
la panne la plus fréquente de cette intégration. Lorsque `resource` et
`audience` sont tous deux présents, Auth0 retient `audience` — les deux
valeurs étant identiques ici, le résultat est stable.

### 4. Client OAuth

Deux voies, au choix, toutes deux acceptées par OpenAI :

* **Client prédéfini** (recommandé pour garder la main) : créer une
  *Regular Web Application*, coller l'URI de redirection affichée par la page
  de gestion de l'application ChatGPT dans **Allowed Callback URLs**, puis
  reporter `client_id` et `client_secret` dans « Paramètres OAuth avancés ».
* **Enregistrement dynamique** : activer la DCR dans **Settings → Advanced** ;
  ChatGPT crée alors son client seul. Les URI de redirection sont gérées
  automatiquement.

ChatGPT lit `/.well-known/openid-configuration` et demande l'ensemble des
portées qui y sont annoncées. Si l'autorisation échoue en
`OAUTH_SCOPES_MISMATCH`, ajouter une *Post-Login Action* accordant
explicitement les portées OIDC demandées (`openid`, `profile`, `email`,
`offline_access`).

### 5. Valeurs à relever

* Émetteur : recopier le champ `issuer` du document de découverte **tel quel**.
  Auth0 y écrit une barre oblique finale : `https://<locataire>.eu.auth0.com/`.
  Voir « Écriture exacte de l'émetteur » ci-dessous — c'est le point qui a
  bloqué la première tentative de connexion.
* JWKS : `https://<locataire>.eu.auth0.com/.well-known/jwks.json`

Le champ **Allowed Callback URLs** de l'application est un composant à
étiquettes : la valeur doit être validée par la touche Entrée pour que le
bouton d'enregistrement apparaisse.

Auth0 écrit la revendication `iss` avec une barre oblique finale, absente des
écrans de configuration. Aucune tolérance n'est appliquée nulle part : la
revendication `iss` du jeton est comparée **caractère pour caractère** à
`MCP_OAUTH_ISSUER`, au même titre que la métadonnée publiée. C'est donc
l'écriture du document de découverte — barre finale comprise — qu'il faut
recopier dans la configuration, faute de quoi tout jeton est refusé en `401`.
Voir « Écriture exacte de l'émetteur » ci-dessous.

## Configuration côté serveur

Variables à définir sur l'hébergeur :

```bash
MCP_AUTH_MODE=oauth
MCP_PUBLIC_URL=https://droit-francais-skill.onrender.com
# Recopier à l'identique le champ « issuer » du document de découverte,
# barre oblique finale comprise si l'émetteur en écrit une (cas d'Auth0).
MCP_OAUTH_ISSUER=https://<votre-emetteur>/
# Facultatif — valeurs déduites si absentes :
# MCP_OAUTH_AUDIENCE=https://droit-francais-skill.onrender.com/mcp
# MCP_OAUTH_JWKS_URL=https://<votre-emetteur>/.well-known/jwks.json
# MCP_OAUTH_REQUIRED_SCOPES=legal:read
MCP_USER_CALLS_PER_MINUTE=20
```

### Écriture exacte de l'émetteur

`MCP_OAUTH_ISSUER` est publié **verbatim** dans les métadonnées RFC 9728, sans
aucune normalisation. C'est délibéré : OpenAI rapproche par comparaison
textuelle stricte l'`issuer` annoncé par le serveur d'autorisation et celui que
publie le serveur MCP. Une barre oblique finale ajoutée ou retirée suffit à
faire échouer la création du connecteur, alors même que les deux chaînes
désignent le même émetteur.

La règle est donc : **recopier le champ `issuer` du document de découverte, tel
quel**. Auth0 y écrit une barre finale ; d'autres émetteurs n'en écrivent pas.
Le serveur ne devine ni n'ajoute rien.

La barre finale ne pose plus de problème de concaténation : les URL dérivées
(JWKS, découverte) sont construites sur une forme tronquée interne, jamais sur
la forme canonique.

Contrôle avant déploiement, sans lancer le service :

```bash
python mcp_server/server.py --check-config
```

Contrôle de l'écriture de l'émetteur, avec un appel réseau à l'émetteur —
échoue avec un code non nul si la chaîne configurée diffère de celle publiée :

```bash
python mcp_server/server.py --check-issuer
```

Ce contrôle n'est jamais joué au démarrage : le service ne doit pas dépendre de
la disponibilité de l'émetteur pour démarrer.

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

Les **trois** valeurs suivantes doivent être identiques, caractère pour
caractère. C'est le contrôle qui conditionne l'acceptation du connecteur :

```bash
curl -s https://<votre-emetteur>/.well-known/openid-configuration | grep -o '"issuer":"[^"]*"'
curl -s https://droit-francais-skill.onrender.com/.well-known/oauth-protected-resource | grep -o '"authorization_servers":\["[^"]*"'
curl -s https://droit-francais-skill.onrender.com/.well-known/oauth-protected-resource/mcp | grep -o '"authorization_servers":\["[^"]*"'
```

La route suffixée par `/mcp` est celle vers laquelle pointe le
`WWW-Authenticate` du `401`, donc celle que ChatGPT lit réellement. La route
racine n'est qu'un alias de compatibilité.

Ces trois contrôles sont automatisés — l'émetteur attendu est alors lu dans le
document de découverte, et le refus anonyme est vérifié dans la foulée :

```bash
python tests/check_oauth_metadata.py https://droit-francais-skill.onrender.com --discover
```

La réponse attendue en 2 comporte
`www-authenticate: Bearer error="invalid_token", …, resource_metadata="…"`.
C'est cet en-tête qui déclenche la découverte automatique par ChatGPT.

## Contrôles appliqués à chaque jeton

* signature vérifiée contre le JWKS de l'émetteur (RS256 uniquement) ;
* `iss` strictement égal à l'émetteur canonique configuré ;
* `aud` contenant l'audience configurée — un jeton émis pour une autre API est
  refusé, ce qui bloque la réutilisation d'un jeton dérobé ailleurs ;
* `exp` et `nbf` contrôlés, avec 30 secondes de tolérance d'horloge ;
* portées requises vérifiées avant l'exécution de l'outil — **contrôle
  configurable, désactivé en production** : `MCP_OAUTH_REQUIRED_SCOPES=-` y
  supprime l'exigence de portée, sans jamais rendre le jeton facultatif. Motif
  et conditions de réactivation : [`conformite.md`](conformite.md) § 5 ;
* quota glissant par sujet authentifié, distinct du quota global d'instance.

Un jeton invalide — signature, `iss`, `aud` ou expiration — renvoie `401` sans
détail exploitable. Un jeton valide auquel manque une portée exigée renvoie
`403`. Le motif technique est journalisé sous forme de nom de classe d'erreur,
jamais avec le jeton.

Le journal métier (`droit_francais.mcp`) reste en `INFO` même lorsque l'image
tourne en `WARNING` : c'est la seule trace permettant de rattacher un appel
d'outil à un utilisateur, donc de tenir l'engagement d'imputabilité pris
envers PISTE. Chaque ligne porte l'outil, l'issue, la durée, une empreinte
tronquée du sujet et les **portées reçues** — jamais le jeton ni l'identifiant
brut du compte.

```
tool_call tool=search principal=a1b2c3d4e5f6 scopes=legal:read outcome=success duration_ms=412
```

Le champ `scopes=` n'est pas décoratif : c'est lui qui dira si le contrôle de
portée peut être réactivé sans casser le connecteur. Une portée n'est pas une
donnée personnelle ; la journaliser ne coûte rien à la vie privée.

## Dépannage

**« OAuth authorization server metadata must advertise PKCE support with
code_challenge_methods_supported containing S256 »** — le formulaire de
création du connecteur a été ouvert *avant* que le serveur ne passe en mode
OAuth. ChatGPT découvre les endpoints à l'ouverture du formulaire ; une
découverte faite contre un serveur encore anonyme reste vide et n'est pas
rejouée. Fermer le formulaire et recréer le connecteur depuis le début : les
endpoints se pré-remplissent alors seuls. Vérifier au préalable, à la main,
que l'émetteur annonce bien `S256` :

```bash
curl -s https://<emetteur>/.well-known/oauth-authorization-server | grep -o 'code_challenge_methods_supported[^]]*]'
```

**Connecteur refusé alors que l'authentification fonctionne, ou émetteur jugé
non concordant** — les deux chaînes diffèrent d'une barre oblique finale.
Comparer les trois valeurs de la section « Vérification après déploiement », ou
lancer `--check-issuer`. Historiquement, la consigne inverse figurait ici : ne
pas écrire la barre finale, parce qu'elle produisait une double barre dans
l'URL de découverte. Ce défaut de concaténation est corrigé — la forme
canonique et la forme servant de préfixe sont désormais distinctes — et c'est
bien la **recopie exacte** qui est attendue.

**Jeton opaque refusé par le serveur** — `Default Audience` n'est pas
renseignée côté locataire ; Auth0 délivre alors un jeton destiné à
`/userinfo` au lieu d'un JWT pour l'API.

**`403` alors que l'authentification réussit** — le jeton est valide mais ne
porte pas `legal:read`. Les journaux du serveur le montrent sans ambiguïté :
un `401` suivi d'une lecture des métadonnées, puis un `403`, sans aucune ligne
`auth_rejected` — signature, émetteur, audience et expiration sont donc bons.

Trois causes possibles, dans cet ordre de fréquence :

1. le client n'a jamais demandé la portée. Un émetteur n'annonce dans
   `scopes_supported` que ses portées OIDC ; une portée d'API personnalisée
   n'y figure pas, et certains clients ne demandent que ce qui y est annoncé.
   Aucun réglage côté émetteur n'y change quoi que ce soit ;
2. le RBAC est activé sans rôle assigné à l'utilisateur ;
3. l'application n'est pas autorisée sur l'API (onglet **Application Access**),
   ou la valeur *Default Permissions for third-party applications* est restée
   à « Unauthorized ».

Pour le cas 1, poser `MCP_OAUTH_REQUIRED_SCOPES=-`. Le transport exige alors
un jeton valide sans exiger de portée particulière. L'imputabilité est
préservée : elle repose sur le sujet du jeton, pas sur la portée. Le serveur
journalise `auth_scope_gate disabled` au démarrage pour que ce choix reste
visible en exploitation.

## Limites connues

* Le quota par utilisateur est local à une instance. Avec plusieurs réplicas,
  il faut une limitation partagée au niveau de la plateforme.
* La révocation dépend de l'émetteur : le serveur ne consulte pas d'endpoint
  d'introspection et respecte donc la durée de vie du jeton.
* Le contrôle des usages interdits par les CGU Judilibre (profilage des
  magistrats et des greffiers) reste à implémenter dans les outils de
  jurisprudence ; l'authentification le rend imputable, pas impossible.
