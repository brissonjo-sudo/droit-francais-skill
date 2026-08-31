# Checklist Auth0 avant publication

Dernière mise à jour : 31 août 2026

À remplir depuis le tenant réel. Ne jamais coller client secret, jeton ou clé
privée dans ce document ; conserver seulement captures expurgées et identifiants
non secrets.

| Contrôle | Valeur attendue | Preuve | Statut |
|---|---|---|---|
| Issuer | Identique au document OIDC, barre finale comprise | capture + `--check-issuer` | ☐ |
| Audience/API identifier | URL canonique `https://droit-francais-skill.onrender.com/mcp` | capture API Auth0 | ☐ |
| Algorithme de signature | RS256 uniquement | capture API Auth0 + test | ☐ |
| Client OpenAI | DCR/CIMD ou client prédéfini explicitement retenu | export de configuration | ☐ |
| Redirect URI | URI exacte fournie par OpenAI, aucune wildcard | capture application | ☐ |
| PKCE | S256 exigé | métadonnées + essai négatif | ☐ |
| Token endpoint auth | méthodes minimales compatibles avec le client choisi | document OIDC | ☐ |
| Durée du jeton | valeur courte, justifiée et consignée | capture API | ☐ |
| Portée | `legal:read` ou décision explicite documentant son absence | jeton décodé sans signature/secret | ☐ |
| DCR | désactivé si inutile ; sinon politique et limites documentées | capture tenant | ☐ |
| Création de compte | politique d'inscription choisie, anti-Sybil documenté | capture connexion | ☐ |
| Admins | MFA, moindre privilège, aucun compte dormant | revue des membres | ☐ |
| Protections | brute force, suspicious IP et breached password activés si disponibles | capture Attack Protection | ☐ |
| Journaux | accès restreint, rétention définie, alerte sur échecs/administration | capture logs/alertes | ☐ |
| Rotation JWKS | ancien/nouveau `kid` testé sans assouplir issuer/audience | compte rendu d'exercice | ☐ |
| Révocation | déconnexion et blocage d'un sujet testés | compte rendu | ☐ |

La checklist terminée doit porter la date, le tenant, l'administrateur et le
commit/image du serveur testés. Elle ne remplace pas le parcours manuel dans
ChatGPT : connexion, appel d'outil, déconnexion et révocation.

