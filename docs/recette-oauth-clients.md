# Recette OAuth des nouveaux clients

Proposition du 10 octobre 2026 ; aucune configuration Auth0 ou de production
n'est modifiée par ce document. Les issues 88 et 89 restent ouvertes.

## Paramètres à valider avant changement

L'enregistrement dynamique est fermé. Un client public prédéfini doit être
autorisé pour chaque parcours, avec PKCE et URI de retour exactes.
L'identifiant utilisé par claude.ai n'est pas une preuve de compatibilité avec
Claude Code, Codex ou ChatGPT. Un client public ne reçoit pas de secret embarqué.

La recette doit fixer : nom du client, version, identifiant public destiné à
ce client, URL du service, issuer tel qu'annoncé, URI de retour enregistrée,
audience/resource, scopes et preuve de consentement. Ne pas publier de jeton,
secret, code OAuth ou identifiant de compte.

## Claude Code

La CLI relevée accepte --client-id et --callback-port avec mcp add. Le format
MCP peut déclarer oauth.clientId et oauth.callbackPort. Préparer une variante
de configuration en recette, sans modifier la racine distribuée avant preuve :

~~~json
{
  "mcpServers": {
    "droit-francais": {
      "type": "http",
      "url": "https://droit-francais-skill.onrender.com/mcp",
      "oauth": {
        "clientId": "IDENTIFIANT_PUBLIC_A_VALIDER",
        "callbackPort": 8765
      }
    }
  }
}
~~~

Le port est un choix de recette, pas une valeur garantie par l'hébergement.
Confirmer l'URI localhost correspondante dans Auth0, puis tester autorisation,
PKCE, échange, retour au client et premier appel réel. Tester aussi refus,
expiration et reconnexion. Pas de réduction des contrôles de jeton du serveur.

## Codex et ChatGPT

Codex permet un identifiant OAuth explicite pour un MCP HTTP ; contrôler les
paramètres du client installé et son URI de retour avant de rédiger la
configuration finale. ChatGPT utilise son propre parcours : un succès Codex
ou Claude ne clôt pas l'issue 89. Recueillir la phase de blocage sans exporter
les codes ou cookies.

## Critère de clôture par client

Une installation vierge doit découvrir le serveur, s'authentifier, exécuter
search puis fetch ou une paire spécialisée, restituer un identifiant issu
du résultat, et renouveler la session. Le test anonyme doit rester refusé.
Conserver client, versions, date, commit distribué, catalogue effectivement
exposé et résultat assaini. Les contrôles statiques et les preuves d'un ancien
client ne suffisent pas à clôturer la recette.

Après ces preuves, soumettre le diff de configuration pour revue avant tout
changement Auth0 ou déploiement. Une fermeture d'issue vient après la recette.

Sources : [OAuth Claude Code](https://code.claude.com/docs/en/mcp),
[MCP dans Codex](https://learn.chatgpt.com/docs/developer-commands) et
[configuration Codex](https://learn.chatgpt.com/docs/config-file/config-reference).
