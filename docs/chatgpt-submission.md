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

1. Ouvrir les paramètres ChatGPT, puis **Apps & Connectors** et les paramètres
   avancés.
2. Activer le mode développeur.
3. Créer une application distante avec l'URL MCP complète :
   `https://droit-francais-skill.onrender.com/mcp`, en choisissant
   l'authentification **OAuth**. ChatGPT lit les métadonnées de ressource
   protégée, puis les métadonnées du serveur d'autorisation, et s'enregistre
   lui-même par enregistrement dynamique de client (RFC 7591).
4. Vérifier que ChatGPT découvre `search`, `fetch`, `search_articles`,
   `get_article`, `search_case_law` et `get_decision`.
5. Exécuter les cinq scénarios positifs et les trois scénarios négatifs du
   fichier [`chatgpt-app-submission.json`](../chatgpt-app-submission.json).
6. Après toute modification des outils ou de leurs métadonnées, actualiser
   l'application dans ChatGPT pour forcer une nouvelle découverte.

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
