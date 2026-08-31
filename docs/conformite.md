# État des contrôles — serveur MCP public

Revue sur pièces du serveur MCP déployé, de ses garde-fous et de son rapport
aux fournisseurs de données. Établi le 31 août 2026, sur l'état du dépôt à
cette date.

Ce document **n'est pas une attestation de conformité**. La configuration des
consoles Auth0/Render/PISTE et le texte intégral des CGU Légifrance du
15 décembre 2022 restent à vérifier selon `audit-securite.md`.

Le principe qui structure tout ce qui suit : **les clés PISTE appartiennent au
titulaire du service, jamais à l'utilisateur final.** Une passerelle publique
consomme les quotas du titulaire sous sa seule responsabilité. Chaque mesure
ci-dessous existe pour que cette responsabilité reste tenable.

---

## 1. Secrets

| Point | État | Où c'est établi |
|---|---|---|
| Secrets hors du dépôt | ✅ | `.gitignore` exclut `.env` et `.env.*`, sauf `.env.example` |
| Aucun secret suivi par Git | ✅ | Recherche par motifs sur l'arbre suivi : seuls des espaces réservés (`votre_client_secret`) et des valeurs de test |
| Fixtures de test sans valeur réelle | ✅ | `tests/fixtures/sample.env` ne contient que deux variables factices |
| Secrets absents du manifeste MCP | ✅ | Contrôlé en CI par `check_plugin.py`, qui échoue si `.mcp.json` nomme une variable sensible |
| Secrets masqués dans les erreurs | ✅ | `_safe_call()` remplace les valeurs de `LEGIFRANCE_CLIENT_ID`, `LEGIFRANCE_CLIENT_SECRET`, `JUDILIBRE_KEY_ID` et `PISTE_KEY_ID` par `[secret masqué]` avant de propager une erreur au client |
| Secrets absents des journaux | ✅ | Aucun jeton ni charge utile n'est journalisé ; un refus est tracé sous forme de nom de classe d'erreur |

En production, les secrets vivent exclusivement dans les variables
d'environnement de l'hébergeur. Le démarrage échoue si les identifiants
Légifrance ou Judilibre manquent, ou si l'environnement PISTE n'est pas `prod`.

## 2. Authentification

| Contrôle | État |
|---|---|
| Signature vérifiée contre le JWKS de l'émetteur | ✅ RS256 uniquement, valeur exacte du tenant |
| Algorithmes symétriques et `none` refusés | ✅ Le serveur ne partage aucun secret avec l'émetteur |
| `iss` contrôlé | ✅ Égalité stricte avec l'émetteur canonique configuré |
| `aud` lié à la ressource MCP (RFC 8707) | ✅ Un jeton émis pour une autre API est refusé, ce qui bloque la réutilisation d'un jeton dérobé ailleurs |
| `exp` / `nbf` contrôlés | ✅ 30 secondes de tolérance d'horloge |
| `sub` exigé | ✅ Sans sujet, aucun quota n'est imputable : le jeton est refusé |
| Portées | ✅ Vérifiées par le transport, avec opt-out explicite documenté (voir §5) |
| Passerelle anonyme impossible en production | ✅ `validate_public()` refuse le démarrage si `MCP_AUTH_MODE` ne vaut pas `oauth` |

Ces contrôles sont couverts par `tests/test_auth.py` (vérificateur isolé) et
`tests/test_oauth_end_to_end.py` (chaîne complète, transport compris).

## 3. Limitation et robustesse

| Mesure | Valeur par défaut | Rôle |
|---|---|---|
| Concurrence maximale | 8 | Protège l'instance |
| Débit d'instance | 120 appels/min | Protège les quotas PISTE globalement |
| Quota par utilisateur | 20 appels/min | Empêche un seul compte de consommer les quotas du titulaire |
| Attente en file | 2 s | Refuse vite plutôt que d'accumuler |
| Taille maximale de requête | 1 Mio | Borne l'entrée |
| Délai des appels sortants | 30 s | Borne la sortie |

Le quota par utilisateur est indexé sur le `sub` du jeton et purge ses
compteurs inactifs à chaque passage, ce qui borne l'empreinte mémoire sans
tâche de fond. Un dépassement produit un message explicite, distinct d'une
erreur de source.

## 4. Journalisation et vie privée

Le journal métier (`droit_francais.mcp`) est la seule trace permettant de
rattacher un appel d'outil à un utilisateur — donc de tenir l'engagement
d'imputabilité pris envers PISTE. Il reste en `INFO` même lorsque l'image
tourne en `WARNING`.

Chaque ligne porte l'outil, l'issue, la durée et une **empreinte SHA-256
tronquée à 12 caractères** du sujet. Jamais le jeton, jamais l'identifiant brut
du compte. Cette empreinte est une donnée personnelle pseudonymisée, et non
anonyme : sa finalité, son accès, sa rétention et sa suppression restent donc
encadrés par la politique de confidentialité.

## 5. Contrôle de portée désactivé — choix assumé

`MCP_OAUTH_REQUIRED_SCOPES=-` désactive **uniquement** l'exigence de portée.
L'authentification reste obligatoire : un jeton valide est toujours exigé, et
l'imputabilité repose sur son sujet.

Ce réglage existe pour un cas réel : un client qui n'annonce pas la portée
personnalisée dans sa requête d'autorisation alors que l'authentification, elle,
aboutit. Le refus se manifeste par un `403` après une authentification réussie.

C'est une **configuration de compatibilité**, pas un état cible. Le retour à
`legal:read` est un simple changement de variable, et les deux réglages sont
couverts par des tests. Aucune valeur de cette variable ne peut désactiver
l'authentification : `MCP_AUTH_MODE` seul en décide, et la production refuse
`disabled`.

## 6. Dépendances et image

`mcp` et `PyJWT[crypto]` sont **épinglés à une version exacte**. Ce n'est pas
une précaution de style : le comportement des métadonnées RFC 9728 dépend de la
version du SDK, et une plage de versions avait fait diverger poste de
développement, CI et production sur le point précis dont dépend le connecteur
ChatGPT. L'image de base est épinglée par digest. La CI affiche les versions,
produit un SBOM CycloneDX, audite les dépendances Python et bloque les CVE
élevées/critiques de l'image ; Dependabot suit Python, Actions et Docker.

## 7. Rapport aux fournisseurs

**Les clés restent côté serveur.** Aucune clé Légifrance, Judilibre ou PISTE
n'est transmise au client MCP, ni exposée dans une réponse d'outil, ni
mentionnée dans un message d'erreur. Les conditions d'utilisation le disent
explicitement : les clés sont réservées à l'application et ne confèrent aucun
droit d'accès direct à l'utilisateur.

**Aucune mutualisation implicite.** Chaque utilisateur authentifié dispose de
son propre quota. Le service n'offre pas un accès anonyme partagé aux quotas du
titulaire — la production refuse d'ailleurs de démarrer dans cette
configuration.

**Limites de débit à valider.** Les quotas d'instance et par utilisateur
refusent un dépassement local, mais leur alignement sur les quotas PISTE réels
n'est pas encore prouvé. Le limiteur étant local et réinitialisé au redémarrage,
la production doit rester à un réplica jusqu'à l'ajout d'un quota global.

**Aucune prétention d'officialité.** Les conditions d'utilisation portent une
clause de non-affiliation explicite : le service n'est ni édité, ni approuvé,
ni labellisé par la DILA, Légifrance, la Cour de cassation, Judilibre ou une
autre administration.

**Vérifiabilité.** La méthode du skill impose de lire la source avant de la
citer, de signaler un échec d'accès comme une source non vérifiée, et de dater
explicitement la version consultée (`as_of_date`, `date_basis`). Tout résultat
reste vérifiable dans la source primaire par son identifiant et son URL.

**Licences.** Les données récupérées restent soumises aux droits et licences de
leurs producteurs, notamment la Licence Ouverte 2.0. Le code et le skill sont
sous CC BY-SA 4.0. La conformité contractuelle Légifrance ne sera conclue
qu'après récupération et contrôle de la CGU 2022 actuellement référencée par
PISTE ; le PDF 2020 n'est conservé que comme archive.

---

## Points à surveiller

Ce qui suit n'est pas un défaut constaté, mais ce qu'un exploitant doit garder
sous l'œil.

1. **Écriture de l'émetteur.** C'est le point de rupture historique du
   connecteur. À revérifier après tout changement d'émetteur, de locataire
   Auth0 ou de domaine — `python tests/check_oauth_metadata.py <url> --discover`.
2. **Dimensionnement des quotas.** Les valeurs par défaut n'ont pas été
   confrontées à une charge réelle. À réviser dès que le service compte
   plusieurs utilisateurs actifs, en regard des limites PISTE effectives.
3. **Portée désactivée.** Tant que `MCP_OAUTH_REQUIRED_SCOPES=-` est en place,
   tout jeton valide émis par l'émetteur pour cette audience ouvre l'accès. La
   granularité par portée est perdue ; seule l'audience discrimine.
4. **Mémoire du limiteur.** Les compteurs vivent en mémoire de processus : un
   redémarrage remet les quotas à zéro, et une exécution multi-instance ne les
   partagerait pas. Acceptable pour une instance unique, à revoir en cas de
   passage à l'échelle.
5. **Épinglage.** Une version figée doit être **suivie**, sans quoi elle
   devient une dette de sécurité. Prévoir une revue des mises à jour du SDK MCP
   et de PyJWT.
6. **Journaux de l'hébergeur.** La pseudonymisation vaut pour le journal métier
   du service. Les journaux d'accès de l'hébergeur (adresses IP, en-têtes) sont
   hors de ce périmètre et relèvent de sa propre politique.
