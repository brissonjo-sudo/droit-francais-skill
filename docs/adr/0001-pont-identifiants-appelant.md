# ADR 0001 — Pont MCP : chaque appelant fournit ses identifiants PISTE

- Date : 27/10/2026
- Statut : **proposée** (prototype sur branche, non déployé)
- Décideur : Jo (mainteneur)

## Contexte

Les manifestes `.mcp.json` de ce dépôt et du plugin Collectivité pointent vers
le serveur hébergé du mainteneur. Toute personne qui installe un plugin
consomme donc les clés PISTE du mainteneur.

Les CGU de la plateforme PISTE (lues le 27/10/2026, voir
[obligations-cgu.md](../obligations-cgu.md), section 4 bis) réservent les clés
à une application donnée (§ 3.1.1) et interdisent de les partager hors de son
organisation (§ 3.1.2). Le § 1.2 range les jetons d'accès parmi les clés.
Servir des tiers avec les clés du mainteneur est une question ouverte (P2).

Objectif du mainteneur : garder un MCP distant utilisable par tous, sans que
le serveur consomme ses propres clés.

## Décision proposée

Le serveur devient un **pont** quand `MCP_PISTE_CREDENTIALS=caller` :

1. Chaque appel MCP porte l'identifiant et le secret PISTE de l'appelant dans
   les en-têtes `X-Piste-Client-Id` et `X-Piste-Client-Secret`.
2. Un middleware du SDK MCP 2.x lit ces deux en-têtes, et seulement eux, pour
   la durée de la requête.
3. Le client PISTE obtient un jeton avec ces identifiants. Le jeton est gardé
   en mémoire, sous l'empreinte SHA-256 des identifiants, borné à 256 entrées
   et jamais écrit sur disque. L'environnement du serveur n'est jamais lu
   pendant un appel en mode pont ; Judilibre passe par le même jeton OAuth,
   jamais par la `KeyId` d'un exploitant.
4. En production, le démarrage est refusé si une clé PISTE d'exploitant est
   présente : aucun repli possible sur les clés du mainteneur.
5. OAuth (Auth0) n'est plus exigé : chaque appelant consomme son propre quota,
   et PISTE refuse les identifiants invalides. Le quota individuel suit
   l'empreinte de la paire identifiant-secret : un faux secret accolé à
   l'identifiant d'autrui n'épuise pas le quota de ce dernier.
   Sans OAuth, n'importe qui peut présenter une paire inventée. Une paire à
   laquelle PISTE n'a pas encore délivré de jeton puise donc dans un budget à
   part (`MCP_NEW_CALLERS_PER_MINUTE`, 30 par défaut) : des paires inventées
   ne bloquent que les nouveaux venus, pas les appelants déjà servis. Le
   nombre d'appelants suivis par le quota individuel est plafonné (4 096).
   Limite assumée : pendant une attaque, un nouvel appelant légitime peut
   attendre ; un appelant sorti du cache de jetons (256) repasse par ce budget.
6. Les valeurs reçues sont validées (jeu de caractères restreint, 8 à 256
   caractères), jamais recopiées dans une réponse, et masquées dans le journal,
   y compris sous leurs formes encodées (formulaire, URL, échappement JSON).

Côté Claude Code (à faire, hors de ce prototype), le plugin déclare un
`userConfig` avec `"sensitive": true` : la valeur est saisie à l'installation
et rangée dans le coffre d'identifiants du système, puis injectée dans les
en-têtes par `${user_config.KEY}` (documentation Claude Code, *Plugin manifest
reference* et *MCP*, consultées le 27/10/2026).

## Options écartées

- **Clés du mainteneur, accès restreint à lui seul** : garde le service pour
  le mainteneur seulement ; ne répond pas à l'objectif.
- **Serveur local (stdio) seulement** : la clé ne quitte jamais le poste, mais
  il faut Python et les dépendances. Reste l'option recommandée pour qui ne
  veut confier ses identifiants à aucun service ; elle est conservée.
- **Coffre côté serveur** (base chiffrée, connexion OAuth) : seule voie pour
  ChatGPT, qui ne connaît qu'OAuth. Plus lourde (base, chiffrement, effacement,
  responsabilité de garde des secrets). Non retenue tant qu'une application
  ChatGPT n'est pas un besoin confirmé.

## Conséquences et réserves

- **CGU, non tranché.** Avec le pont, c'est l'appelant qui confie ses
  identifiants au service du mainteneur. La lecture « le pont est un outil
  technique de l'appelant », comme l'hébergeur l'est déjà pour le mainteneur,
  est **plausible, non vérifiée**. Pas de mise en production sans réponse
  écrite du support PISTE.
- **Confiance.** Le secret transite en HTTPS et vit en mémoire du serveur le
  temps de l'appel. Le mainteneur pourrait techniquement le lire : à dire
  clairement dans la politique de confidentialité avant tout déploiement.
- **Changement cassant** pour les utilisateurs actuels des plugins : version
  majeure et annonce requises.
- **Codex** : la transmission d'en-têtes depuis un coffre n'est pas vérifiée.
- Le mode `server` existant est inchangé.

## Vérification

`tests/test_pont_identifiants.py` : isolation du cache par appelant, absence
de repli sur l'exploitant, refus de configuration, et chaîne HTTP réelle du SDK
2.x (middleware, transport, outil, quota individuel), sans réseau.
Après l'avis critique du 01/11/2026 : budget séparé des paires inconnues,
plafond du quota individuel et masquage des formes encodées du secret.
