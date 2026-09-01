# Checklist Auth0 avant publication

Dernière mise à jour : 1er septembre 2026

À remplir depuis le tenant réel. Ne jamais coller client secret, jeton ou clé
privée dans ce document ; conserver seulement captures expurgées et identifiants
non secrets.

Statuts : ✅ prouvé (preuve citée, datée) · ◐ partiel (le code ou le document
public prouve une partie ; la capture du tableau de bord manque) · ☐ humain.

**Relevé du 1er septembre 2026** — locataire `dev-7soa32jfmxpejzhs.eu.auth0.com`,
document de découverte public lu ce jour, serveur `0.7.0` déployé. Les lignes
◐ et ☐ demandent le tableau de bord : voir [pieces-humaines.md](pieces-humaines.md) § 9.

| Contrôle | Valeur attendue | Preuve | Statut |
|---|---|---|---|
| Issuer | Identique au document OIDC, barre finale comprise | `check_oauth_metadata.py --discover` sur la production le 1/9/2026 : émetteur identique sur les deux routes et au document de découverte ; rejoué en CI à chaque PR | ✅ |
| Audience/API identifier | URL canonique `https://droit-francais-skill.onrender.com/mcp` | métadonnée `resource` publiée le 1/9/2026 ; jeton M2M émis pour cette audience accepté par le serveur (E4, 31/8) ; audience étrangère refusée (`test_oauth_end_to_end.py`) | ✅ |
| Algorithme de signature | RS256 uniquement | côté serveur : seul RS256 accepté, `none`/`HS*` refusés (`test_auth.py`) ; côté locataire : API créée en RS256 ([oauth.md](oauth.md) § 1), capture à archiver | ◐ |
| Client OpenAI | DCR/CIMD ou client prédéfini explicitement retenu | **DCR retenu** : `registration_endpoint` présent dans le document de découverte du 1/9/2026, enregistrement vérifié le 31/8 ([chatgpt-submission.md](chatgpt-submission.md)) ; export de configuration à archiver | ◐ |
| Redirect URI | URI exacte fournie par OpenAI, aucune wildcard | gérée par la DCR ; vérifier qu'aucune application prédéfinie ne porte de wildcard | ☐ |
| PKCE | S256 exigé | document OIDC du 1/9/2026 : `code_challenge_methods_supported` = `S256`, `plain` ; le refus de `plain` n'est pas prouvé, essai négatif à jouer | ◐ |
| Token endpoint auth | méthodes minimales compatibles avec le client choisi | document OIDC du 1/9/2026 : `client_secret_basic`, `client_secret_post`, `private_key_jwt`, `tls_client_auth`, `self_signed_tls_client_auth`, `none` — `none` est nécessaire à un client DCR public avec PKCE ; confirmer l'enregistrement PKCE du client ChatGPT | ◐ |
| Durée du jeton | valeur courte, justifiée et consignée | capture API | ☐ |
| Portée | `legal:read` ou décision explicite documentant son absence | **absence tranchée et documentée** le 1/9/2026 : [exploitation.md](exploitation.md) incident n° 4, [conformite.md](conformite.md) § 5, exception argumentée dans [chatgpt-submission.md](chatgpt-submission.md) ; portées reçues journalisées (`scopes=`) | ✅ |
| DCR | désactivé si inutile ; sinon politique et limites documentées | activée, nécessaire (ChatGPT s'enregistre lui-même) ; observé dans le journal Auth0 le 1/9/2026 à 21:13Z : grant tiers utilisateur `Authorized` sans permission (`scope: []`, `allow_all_scopes: false`). Réglage distinct `Client Access: Unauthorized` vérifié le même jour. Test négatif avec grant supprimé puis rétablissement, six outils visibles et appel Légifrance réel réussi. JSON expurgé du grant et capture limitée aux réglages archivés le 1/9/2026 dans le dossier privé `Auth0/` ; procédure reproductible et noms des deux pièces : [pieces-humaines.md](pieces-humaines.md) § 2 | ✅ |
| Création de compte | politique d'inscription choisie, anti-Sybil documenté | capture connexion ; risque Sybil consigné dans [audit-securite.md](audit-securite.md) § 3 | ☐ |
| Admins | MFA, moindre privilège, aucun compte dormant | revue des membres | ☐ |
| Protections | brute force, suspicious IP et breached password activés si disponibles | capture Attack Protection | ☐ |
| Journaux | accès restreint, rétention définie, alerte sur échecs/administration | capture logs/alertes | ☐ |
| Rotation JWKS | ancien/nouveau `kid` testé sans assouplir issuer/audience | refus d'un `kid` inconnu prouvé (`test_oauth_end_to_end.py`) ; exercice de rotation réel à jouer | ◐ |
| Révocation | déconnexion et blocage d'un sujet testés | compte rendu | ☐ |

La checklist terminée doit porter la date, le tenant, l'administrateur et le
commit/image du serveur testés. Elle ne remplace pas le parcours manuel dans
ChatGPT : connexion, appel d'outil, déconnexion et révocation.

