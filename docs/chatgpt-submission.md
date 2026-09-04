# Connexion et soumission du plugin dans ChatGPT

État vérifié le 30 août 2026, révisé le 4 septembre 2026.

## Endpoint de production

- Serveur MCP universel : `https://droit-francais-skill.onrender.com/mcp`
- Sonde publique : `https://droit-francais-skill.onrender.com/health`
- Transport : MCP Streamable HTTP sur HTTPS
- Authentification utilisateur : **OAuth 2.1**, serveur d'autorisation externe ;
  les clés PISTE restent côté serveur et ne sont jamais exposées au client
- Métadonnées de ressource protégée :
  `https://droit-francais-skill.onrender.com/.well-known/oauth-protected-resource/mcp`
- Outils : six opérations strictement en lecture seule

## Tester dans ChatGPT

Procédure conforme à la documentation OpenAI du 31 août 2026 (voir « Sources »
en fin de document). La version antérieure de cette section indiquait un chemin
**Apps & Connectors** qui n'existe pas : elle avait été rédigée sans être
parcourue, alors que le document se disait vérifié.

### Prérequis

Compte **Plus, Pro, Business, Enterprise ou Education**, et **sur le web**
(`chatgpt.com`) — le mode développeur n'est pas exposé dans l'application
mobile. Sur un espace de travail Business, Enterprise ou Education, un
administrateur doit l'avoir autorisé au préalable dans *Workspace Settings →
Permissions & Roles → Connected Data → Developer mode / Create custom MCP
connectors*.

### Étapes

1. Ouvrir `chatgpt.com`, puis **Settings → Security and login**.
2. Activer l'interrupteur **Developer mode**.
3. Ouvrir **`https://chatgpt.com/plugins`** — c'est là qu'est le bouton de
   création, et non dans les réglages, qui ne servent qu'à activer le mode.
4. Cliquer sur le **bouton +**, puis renseigner le formulaire :

   | Champ | Valeur |
   |---|---|
   | Nom | `Droit français` |
   | Description | `Recherche juridique française sourcée — Légifrance et Judilibre` |
   | **Connection** | `https://droit-francais-skill.onrender.com/mcp` (chemin `/mcp` compris) |

   L'option `Tunnel` de la section *Connection* concerne les serveurs privés ;
   celui-ci est public.

   **Il n'y a aucun champ d'authentification à remplir.** L'authentification
   est *découverte*, pas déclarée : ChatGPT appelle `/mcp`, reçoit le `401`,
   lit l'adresse de la métadonnée de ressource dans l'en-tête
   `WWW-Authenticate` et remonte jusqu'au serveur d'autorisation. Un échec à
   cette étape est donc un défaut de découverte côté serveur, jamais un réglage
   à corriger dans le formulaire : le diagnostiquer avec
   `tests/check_oauth_metadata.py`.

   **Cas particulier de la première connexion.** ChatGPT s'enregistre lui-même
   par enregistrement dynamique (RFC 7591), mais celui-ci **n'est pas laissé
   ouvert** sur le locataire Auth0 : il a été activé le temps d'un
   enregistrement le 4 septembre 2026, puis refermé aussitôt. Le client obtenu,
   `tpc_tTMV6uujD9aHwP8DoFfEMg`, est durable — ChatGPT n'a plus à se
   réenregistrer, et la connexion fonctionne DCR fermée. C'est un client
   **public** (`token_endpoint_auth_method: none`) : il n'a pas de secret
   client, et aucun champ du formulaire n'en demande. Si un jour un nouvel
   enregistrement devenait nécessaire, rouvrir la DCR le temps de l'opération
   et la refermer dans le même passage ; procédure détaillée dans
   [`oauth.md`](oauth.md) § 4.

   Les protocoles acceptés sont SSE et *streaming HTTP* ; le transport du
   service est en Streamable HTTP.
5. Créer la connexion, puis **vérifier les outils et métadonnées découverts** :
   les six outils doivent apparaître. L'application créée est rangée sous
   **Drafts**, avec une page de détail permettant d'activer ou désactiver
   chaque outil et de rafraîchir la découverte.
6. Vérifier que ChatGPT découvre `search`, `fetch`, `search_articles`,
   `get_article`, `search_case_law` et `get_decision`.
7. Exécuter les cinq scénarios positifs et les trois scénarios négatifs du
   fichier [`chatgpt-app-submission.json`](../chatgpt-app-submission.json).
8. Après toute modification des outils ou de leurs métadonnées, actualiser
   l'application dans ChatGPT pour forcer une nouvelle découverte.

Sur un fournisseur OpenID Connect, la portée `offline_access` doit être
demandée pour obtenir un jeton de rafraîchissement, sans quoi la connexion se
rompt à l'expiration du premier jeton. Auth0 l'annonce bien, et l'API porte
*Allow Offline Access*.

## Préparer le formulaire OpenAI Platform

Type de soumission : **With MCP**, URL **Universal**.

| Champ | Valeur proposée |
|---|---|
| Nom | Droit français |
| Sous-titre | Rechercher le droit français |
| Catégorie | Productivity |
| Site | `https://github.com/brissonjo-sudo/droit-francais-skill` |
| Support | `https://github.com/brissonjo-sudo/droit-francais-skill/issues` |
| Confidentialité | `https://github.com/brissonjo-sudo/droit-francais-skill/blob/main/docs/privacy-policy.md` |
| Conditions | `https://github.com/brissonjo-sudo/droit-francais-skill/blob/main/docs/terms-of-use.md` |
| MCP | `https://droit-francais-skill.onrender.com/mcp` |

La table ci-dessus ne couvrait que sept champs. Le formulaire en demande
davantage ; les voici tous, relevés dans la documentation OpenAI le 31 août
2026.

**Section « Info »** — nom, description courte, description longue, identité de
développeur vérifiée, logo, catégorie, puis les **quatre** URL publiques : site,
support, confidentialité, conditions.

**Section « MCP »** — type d'URL (`Universal` ou `Template`), URL MCP de
production, configuration d'authentification, **identifiants de démonstration**
et domaines de politique de sécurité de contenu.

**Puis** — prompts de démarrage, cinq cas de test positifs et trois négatifs,
pays de distribution, et notes de version.

Les identifiants de démonstration doivent fonctionner **sans MFA, ni SMS, ni
confirmation par courriel** : un relecteur ne peut pas recevoir votre second
facteur. Prévoir un compte de test dédié dans le locataire Auth0.

Le fichier `chatgpt-app-submission.json` porte les informations d'app, les
justifications des annotations, les notes de version et les huit cas de test
importables. Il est **validé contre le schéma officiel** par
`python tests/check_plugin.py`, à chaque PR. Les notes de version renvoient
au tag Git `plugin-v*` qui fige le code source soumis ; à chaque nouvelle
soumission, mettre à jour ce tag dans les notes en même temps que la version du
manifeste. L'historique des tags est tenu dans `skill/CHANGELOG.md`.

> Attention à deux vocabulaires distincts : `app_info.category` du fichier de
> soumission utilise l'énumération en majuscules du schéma (`PRODUCTIVITY`),
> tandis que `interface.category` du manifeste utilise la liste en casse de
> titre (`Productivity`). Les deux sont contrôlés, chacun contre sa liste.

## Vérification du domaine

Un plugin avec MCP doit prouver le contrôle du domaine qui héberge le serveur.
Le serveur expose `GET /.well-known/openai-apps-challenge`, qui rend **le jeton
seul** — ni JSON, ni liste, ni plusieurs jetons : le portail compare la réponse
au jeton exact. Les espaces et retours à la ligne sont retirés côté serveur,
parce qu'un jeton collé depuis le portail en emporte souvent un.

L'origine interrogée par le portail (*Challenge Base URL*) doit être l'hôte du
serveur MCP ou un hôte parent ; les chemins sont ignorés.

Lorsque le portail fournit son jeton temporaire :

1. ajouter le jeton dans la variable Render `OPENAI_APPS_CHALLENGE` ;
2. laisser Render redéployer le service ;
3. lancer la vérification depuis OpenAI Platform ;
4. retirer immédiatement la variable après validation.

Le jeton ne doit jamais être ajouté au dépôt ou à un fichier de documentation.

## Portées OAuth : exception argumentée

À porter explicitement à la connaissance du relecteur, car le service s'écarte
sur ce point d'une consigne écrite d'OpenAI.

La [documentation sécurité](https://developers.openai.com/apps-sdk/guides/security-privacy)
demande de *« verify and enforce scopes on every tool call »*. Ce service tourne
en production avec `MCP_OAUTH_REQUIRED_SCOPES=-` : il exige un jeton valide à
chaque appel, mais n'exige aucune portée particulière.

La cause est technique et documentée en détail dans
[`conformite.md`](conformite.md) § 5 : le SDK MCP construit la métadonnée avec
`scopes_supported=auth.required_scopes` et remet la même liste au middleware
d'autorisation. Annoncer et exiger sont indissociables. Or une portée d'API
personnalisée n'apparaît pas dans le document de découverte OIDC de l'émetteur :
un client qui ne demande que ce qui y est annoncé obtient un jeton sans
`legal:read`. Exiger la portée reviendrait donc à répondre `403` à tout le monde.

Ce que le service conserve malgré cet écart :

- **authentification obligatoire** — aucun accès anonyme, `MCP_AUTH_MODE` seul
  en décide et la production refuse `disabled` ;
- **audience contrôlée** — un jeton émis pour une autre API est refusé (RFC 8707),
  ce qui bloque la réutilisation d'un jeton obtenu ailleurs ;
- **imputabilité par sujet** — chaque appel est journalisé avec une empreinte
  tronquée du sujet du jeton : c'est sur lui, et non sur une portée, que repose
  la traçabilité ;
- **quota par sujet, à la portée limitée** — un quota glissant est indexé par
  sujet, en plus du quota global de l'instance. Il est tenu **en mémoire du
  processus** : il repart à zéro à chaque redémarrage et n'est pas partagé
  entre réplicas. C'est un garde-fou de premier rang contre la consommation
  des quotas PISTE par un seul compte, pas une garantie distribuée — d'où la
  contrainte d'exploitation d'**un seul réplica** avec des plafonds inférieurs
  aux quotas réels, tant qu'aucun limiteur global n'existe. Voir
  [`audit-securite.md`](audit-securite.md) § 3 ;
- **surface sans privilège à graduer** — six outils en lecture seule sur des
  données exclusivement publiques (Légifrance, Judilibre). Il n'existe aucune
  opération réservée qu'une portée viendrait distinguer d'une autre : le moindre
  privilège est déjà le seul privilège.

Le contrôle n'est pas abandonné. Le journal métier porte les portées reçues
(`scopes=`) : la réactivation devient possible dès que les appels réels montrent
`legal:read`. Voir [`exploitation.md`](exploitation.md), incident n° 4.

## Conditions préalables humaines

Procédures détaillées, pièce par pièce, dans
[`pieces-humaines.md`](pieces-humaines.md). Avant l'envoi final, le
soumissionnaire doit :

- disposer du droit **Apps Management: Write** dans l'organisation OpenAI ;
- sélectionner une identité individuelle ou commerciale vérifiée ;
- vérifier que le nom public de cette identité correspond à la politique de
  confidentialité, au site et au compte de support ;
- valider la publication d'un moyen de contact privé pour les demandes de
  protection des données ;
- contrôler et téléverser le logo `assets/logo.png` ;
- accepter la disponibilité et les pays de distribution proposés dans le
  portail.

## Risque d'exploitation restant

L'instance Render gratuite se met en veille et retarde le premier appel :
**22,8 s** mesurées au réveil le 31 août 2026, **32,6 s** le 1er septembre,
contre 0,15 à 0,60 s à chaud (voir [`exploitation.md`](exploitation.md),
incident n° 2). Le cron GitHub essayé les 1er et 2 septembre n'a pas tenu sa
cadence : cinq réveils sur cinq runs planifiés. Décision du 2 septembre 2026 :
le plan gratuit est conservé et un service de ping externe appelle `/health`
toutes les cinq minutes. La période d'observation ne commence qu'après sa mise
en place et sa vérification sur 24 h ; si des réveils subsistent, passer à une
instance sans mise en veille avant la revue.

## Documentation officielle OpenAI

- [Construire un serveur MCP](https://developers.openai.com/plugins/build/mcp-server)
- [Définir les outils](https://developers.openai.com/plugins/plan/tools)
- [Soumettre et publier](https://developers.openai.com/plugins/deploy/submission)
- [Règles de publication](https://developers.openai.com/plugins/app-guidelines)

## Sources

* [Developer mode — documentation OpenAI](https://developers.openai.com/api/docs/guides/developer-mode)
* [Developer mode and MCP apps in ChatGPT — centre d'aide OpenAI](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt)
* [Connect and test your plugin — documentation OpenAI](https://developers.openai.com/plugins/deploy/connect-chatgpt)
* [Authentication — documentation OpenAI](https://developers.openai.com/plugins/build/auth)
* [Verifying your domain — centre d'aide OpenAI](https://help.openai.com/en/articles/8871611-domain-verification)

Ces pages font foi sur les libellés d'interface, qui changent. Toute
modification de cette section doit être vérifiée à la source, jamais rédigée
de mémoire.
