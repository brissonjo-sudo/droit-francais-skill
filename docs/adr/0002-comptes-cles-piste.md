# ADR 0002 — Comptes : clés PISTE personnelles, stockées chiffrées

- Date : 25/11/2026
- Statut : **proposée**. Décision attendue de Jo à la fusion.
- Décideur : Jo (mainteneur)
- Complète l'[ADR 0001](0001-pont-identifiants-appelant.md), sans la remplacer.

## Contexte

Le besoin de Jo : chaque personne utilise **ses propres clés PISTE**, depuis
**n'importe quel client**, smartphone compris.

- Le pont de l'ADR 0001 lit les clés dans des en-têtes HTTP. Or les connecteurs
  claude.ai, sur le web comme sur mobile, n'en envoient pas : ils ne savent faire
  que de l'OAuth.
- Le mode OAuth historique fonctionne partout, mais il consomme les clés de
  l'exploitant.

## Décision

Un mode `MCP_PISTE_CREDENTIALS=account`, sur le service `droit-francais-pont` :

1. **Identité.** L'utilisateur se connecte par OAuth via Auth0
   (`MCP_AUTH_MODE=oauth`, obligatoire dans ce mode).
2. **Stockage.** Ses clés PISTE sont rangées dans son `app_metadata` Auth0, que
   l'utilisateur ne peut pas modifier. Elles y sont chiffrées en AES-256-GCM par le
   serveur, avec `MCP_CREDENTIALS_KEY`, et le `sub` sert de donnée associée : un
   blob recopié dans un autre compte ne se déchiffre pas. L'accès passe par l'API
   Management (application M2M, portées `read:users` et
   `update:users_app_metadata`). Il
   n'existe aucune base de données, et Render free n'a pas de disque.
3. **Saisie.** L'outil `configurer_cles_piste` renvoie un lien signé HMAC,
   valable 10 minutes et à usage unique, vers `/compte`. Les clés y sont vérifiées
   auprès de PISTE avant d'être enregistrées. Le secret ne passe jamais dans la
   conversation, ni chez le fournisseur du modèle.
4. **Usage.** `_caller_pair()` lit la paire du `sub` courant. La suite est celle
   du pont : `caller_credentials`, le cache de jetons par empreinte, Judilibre en
   OAuth, aucun repli sur des clés d'exploitant, et le quota par `sub`.
5. **Suppression.** L'outil `oublier_cles_piste`.

Code : `mcp_server/credential_store.py`, `mcp_server/compte.py`, et
`_account_pair` dans `mcp_server/server.py`.

## Conséquences et réserves

- **Le service public détient un accès Management sur tout le tenant** : la
  lecture de tous les profils (e-mails compris) et l'écriture de leurs
  `app_metadata`. Une compromission du service exposerait aussi les comptes du
  service historique, qui partage le même tenant.
- **Jetons M2M.** L'offre gratuite d'Auth0 en plafonne le nombre mensuel. Le
  jeton n'est gardé qu'en mémoire : chaque réveil de l'instance free en
  redemande un.
- **Lien transmis à un tiers.** Un utilisateur qui enverrait son lien à
  quelqu'un d'autre consommerait ensuite le quota PISTE de cette personne.
  C'est pourquoi la page et l'outil affichent un indice du compte.
- **L'exploitant détient la clé de déchiffrement.** Il pourrait techniquement
  lire les clés : c'est dit dans la politique de confidentialité.
- **Perdre `MCP_CREDENTIALS_KEY` rend toutes les clés illisibles.** Chacun
  devrait alors les ressaisir.
- **La question des CGU PISTE § 3.1.2 reste ouverte**, comme pour l'ADR 0001.
- **Le jeton du lien apparaît dans l'URL** : il peut figurer dans les journaux de
  requêtes de l'hébergeur pendant ses 10 minutes de validité.
- **Le cache est en mémoire, pour 5 minutes.** Une suppression faite sur une
  autre instance ne serait vue qu'à l'expiration. Le service n'a qu'une instance.
- **L'API Management Auth0 est limitée en débit sur l'offre gratuite.** Le cache
  réduit la charge à un appel par utilisateur toutes les 5 minutes.

## Vérification

`tests/test_comptes_piste.py` couvre :
- le chiffrement, et le refus d'un blob d'un autre sujet, altéré ou chiffré avec
  une autre clé ;
- le lien : usage unique, expiration, falsification ;
- le coffre avec une API Management simulée ;
- la configuration de production ;
- la chaîne HTTP réelle (OAuth, outils, `/compte`) : chaque sujet utilise ses
  propres clés, un sujet sans clés reçoit l'invitation, des clés refusées par
  PISTE ne sont pas enregistrées.
