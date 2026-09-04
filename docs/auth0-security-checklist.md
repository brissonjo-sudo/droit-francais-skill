# Checklist Auth0 avant publication

Dernière mise à jour : 4 septembre 2026

À remplir depuis le tenant réel. Ne jamais coller client secret, jeton ou clé
privée dans ce document ; conserver seulement captures expurgées et identifiants
non secrets.

Statuts : ✅ prouvé (preuve citée, datée) · ◐ partiel (le code ou le document
public prouve une partie ; la capture du tableau de bord manque) · ☐ humain.

**Relevé du 4 septembre 2026** — locataire `dev-7soa32jfmxpejzhs.eu.auth0.com`,
document de découverte public relu ce jour, serveur `0.8.0` déployé. Les lignes
◐ et ☐ demandent le tableau de bord : voir [pieces-humaines.md](pieces-humaines.md) § 9.

**Bascule du 4 septembre 2026 — du client dynamique au client enregistré.**
La voie d'intégration a changé de nature, et cette check-list en tient compte
ligne à ligne. L'enregistrement dynamique (DCR) n'est plus un mécanisme
permanent : il a été **ouvert le temps d'un enregistrement, puis refermé**. Il
en subsiste un client tiers **public** et durable :

* client retenu : `tpc_tTMV6uujD9aHwP8DoFfEMg` (identifiant non secret) ;
* `token_endpoint_auth_method: none` — c'est un client **public** : il n'a pas
  de secret client, et il ne faut donc en chercher ni en saisir aucun ;
* l'ancien client `dRsmaHYVujnQft3RtXOynPj7qeK3rAWg` a été **supprimé**
  (journal Auth0 *Delete a client*). Il n'est pas réutilisable, et aucune
  procédure ne doit y renvoyer ;
* la connexion Google a été promue au niveau du domaine, sans quoi une
  application tierce ne peut pas authentifier l'utilisateur ;
* résultat mesuré le 4 septembre 2026 : *Success Login* puis *Success
  Exchange* dans le journal Auth0, six outils découverts par ChatGPT, et
  lecture réelle de l'article 1240 du Code civil (`LEGIARTI000032041571`).

La procédure correcte est donc désormais, et dans cet ordre : **activer la DCR
temporairement → laisser ChatGPT s'enregistrer → refermer la DCR
immédiatement**. Laisser la DCR ouverte reviendrait à autoriser n'importe qui à
créer un client sur le locataire.

| Contrôle | Valeur attendue | Preuve | Statut |
|---|---|---|---|
| Issuer | Identique au document OIDC, barre finale comprise | `check_oauth_metadata.py --discover` sur la production le 1/9/2026 : émetteur identique sur les deux routes et au document de découverte ; rejoué en CI à chaque PR | ✅ |
| Audience/API identifier | URL canonique `https://droit-francais-skill.onrender.com/mcp` | métadonnée `resource` publiée le 1/9/2026 ; jeton M2M émis pour cette audience accepté par le serveur (E4, 31/8) ; audience étrangère refusée (`test_oauth_end_to_end.py`) | ✅ |
| Algorithme de signature | RS256 uniquement | côté serveur : seul RS256 accepté, `none`/`HS*` refusés (`test_auth.py`) ; côté locataire : API créée en RS256 ([oauth.md](oauth.md) § 1), capture à archiver | ◐ |
| Client OpenAI | client explicitement retenu et durable | **client public enregistré retenu** : `tpc_tTMV6uujD9aHwP8DoFfEMg`, issu d'un enregistrement dynamique ouvert puis refermé le 4/9/2026 ; l'ancien client `dRsmaHYVujnQft3RtXOynPj7qeK3rAWg` est supprimé (journal *Delete a client*) ; connexion aboutie le 4/9/2026 (*Success Login* puis *Success Exchange*) | ✅ |
| Redirect URI | URI exacte fournie par OpenAI, aucune wildcard | portée par le seul client `tpc_tTMV…`, figée à l'enregistrement ; **à relire dans le tableau de bord** maintenant que la DCR est fermée et que l'URI ne peut plus se renégocier seule : vérifier l'égalité exacte avec l'URI OpenAI et l'absence de `*` | ☐ |
| PKCE | S256 exigé | document OIDC du 1/9/2026 : `code_challenge_methods_supported` = `S256`, `plain` ; le refus de `plain` n'est pas prouvé, essai négatif à jouer | ◐ |
| Token endpoint auth | méthodes minimales compatibles avec le client choisi | document OIDC du 1/9/2026 : `client_secret_basic`, `client_secret_post`, `private_key_jwt`, `tls_client_auth`, `self_signed_tls_client_auth`, `none` — le client retenu `tpc_tTMV…` utilise `none` : c'est un client **public**, sans secret, dont la sécurité repose entièrement sur PKCE ; confirmer dans le tableau de bord que S256 est bien exigé pour ce client | ◐ |
| Durée du jeton | valeur courte, justifiée et consignée | capture API | ☐ |
| Portée | `legal:read` ou décision explicite documentant son absence | **absence tranchée et documentée** le 1/9/2026 : [exploitation.md](exploitation.md) incident n° 4, [conformite.md](conformite.md) § 5, exception argumentée dans [chatgpt-submission.md](chatgpt-submission.md) ; portées reçues journalisées (`scopes=`) | ✅ |
| DCR | désactivé si inutile ; sinon politique et limites documentées | **désactivée depuis le 4/9/2026**, après avoir été ouverte le temps d'enregistrer `tpc_tTMV6uujD9aHwP8DoFfEMg` puis refermée aussitôt. Elle n'est plus nécessaire : le client obtenu est durable et ChatGPT n'a plus à se réenregistrer. Le grant tiers, lui, reste indispensable — observé dans le journal Auth0 le 1/9/2026 à 21:13Z : grant tiers utilisateur `Authorized` sans permission (`scope: []`, `allow_all_scopes: false`). Réglage distinct `Client Access: Unauthorized` vérifié le même jour. Test négatif avec grant supprimé puis rétablissement, six outils visibles et appel Légifrance réel réussi. JSON expurgé du grant et capture limitée aux réglages archivés le 1/9/2026 dans le dossier privé `Auth0/` ; procédure reproductible et noms des deux pièces : [pieces-humaines.md](pieces-humaines.md) § 2 | ✅ |
| Connexions du domaine | strictement celles qui sont nécessaires, aucune connexion résiduelle | la connexion **Google a été promue au niveau du domaine** le 4/9/2026 : sans cela une application tierce ne peut pas authentifier l'utilisateur. Contrepartie à vérifier au tableau de bord : cette promotion vaut pour **toutes** les applications tierces du locataire, présentes et futures — recenser les connexions actives et désactiver celles qui ne servent pas | ☐ |
| Création de compte | politique d'inscription choisie, anti-Sybil documenté | capture connexion ; risque Sybil consigné dans [audit-securite.md](audit-securite.md) § 3 | ☐ |
| Admins | MFA, moindre privilège, aucun compte dormant | revue des membres | ☐ |
| Protections | brute force, suspicious IP et breached password activés si disponibles | capture Attack Protection | ☐ |
| Journaux | accès restreint, rétention définie, alerte sur échecs/administration | capture logs/alertes | ☐ |
| Rotation JWKS | ancien/nouveau `kid` testé sans assouplir issuer/audience | refus d'un `kid` inconnu prouvé (`test_oauth_end_to_end.py`) ; exercice de rotation réel à jouer | ◐ |
| Révocation | déconnexion et blocage d'un sujet testés | compte rendu | ☐ |

La checklist terminée doit porter la date, le tenant, l'administrateur et le
commit/image du serveur testés. Elle ne remplace pas le parcours manuel dans
ChatGPT : connexion, appel d'outil, déconnexion et révocation.

