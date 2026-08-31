# Connexion et soumission du plugin dans ChatGPT

État vérifié le 30 août 2026.

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
   `WWW-Authenticate`, remonte jusqu'au serveur d'autorisation et s'enregistre
   lui-même — l'enregistrement dynamique de client (RFC 7591) est actif sur le
   locataire Auth0, vérifié le 31 août 2026. Un échec à cette étape est donc un
   défaut de découverte côté serveur, jamais un réglage à corriger dans le
   formulaire : le diagnostiquer avec `tests/check_oauth_metadata.py`.

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

Le fichier `chatgpt-app-submission.json` contient les informations d'app,
les justifications des annotations et les huit cas de test importables.

## Vérification du domaine

Le serveur expose `GET /.well-known/openai-apps-challenge`. Lorsque le portail
fournit son jeton temporaire :

1. ajouter le jeton dans la variable Render `OPENAI_APPS_CHALLENGE` ;
2. laisser Render redéployer le service ;
3. lancer la vérification depuis OpenAI Platform ;
4. retirer immédiatement la variable après validation.

Le jeton ne doit jamais être ajouté au dépôt ou à un fichier de documentation.

## Conditions préalables humaines

Avant l'envoi final, le soumissionnaire doit :

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

L'instance Render gratuite peut se mettre en veille et retarder le premier
appel de plus de 50 secondes. Le protocole fonctionne, mais une instance sans
mise en veille est recommandée avant une revue publique afin de satisfaire les
exigences de stabilité et de réactivité.

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

Ces pages font foi sur les libellés d'interface, qui changent. Toute
modification de cette section doit être vérifiée à la source, jamais rédigée
de mémoire.
