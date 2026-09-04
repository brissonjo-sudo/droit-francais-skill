# Plan d'audit sécurité v1.1 — serveur MCP « Droit français »

─────────────────────────────────────────────
Date d'analyse           : 31/08/2026, révisé le 04/09/2026
Date(s) de référence     : 04/09/2026
Date des faits           : sans objet
Date d'action / analyse  : 31/08/2026
Champ territorial        : France / service internet
Régime juridique primaire: sécurité, données personnelles et contrats d'API
Niveau d'exigence        : note de fond
Mode opératoire          : B complet
─────────────────────────────────────────────

Ce document est un **plan vivant**, pas une attestation de conformité. Il
distingue les contrôles déjà prouvés, ceux à rejouer et ceux qui nécessitent un
accès humain à Auth0, Render ou PISTE. Une case n'est « terminée » que si son
élément de preuve est archivé avec la version testée.

## 1. Décision de sécurité et architecture

Le service est un plugin MCP `tool-only` en lecture seule, déjà exposé sur
internet mais protégé par OAuth. Sa publication dans l'annuaire OpenAI est une
étape distincte de cette exposition réseau.

```text
Utilisateur → ChatGPT/Codex → Auth0 → Render / serveur MCP
                                      ├→ PISTE → DILA / Légifrance
                                      └→ PISTE → Cour de cassation / Judilibre
```

Les six outils ne modifient pas les sources (`readOnlyHint=true`,
`destructiveHint=false`) et ne peuvent modifier aucun état publiquement
visible d'internet (`openWorldHint=false`) : ils atteignent des systèmes
externes et consomment des quotas PISTE, mais uniquement en lecture. Les
textes juridiques reçus sont des données non fiables à analyser, jamais des
instructions à exécuter.

## 2. Portes bloquantes

La publication dans l'annuaire reste interdite tant que l'un de ces points est
ouvert :

1. finding critique ou élevé non corrigé ou non accepté explicitement ;
2. configuration Auth0 non vérifiée depuis le tenant réel ;
3. version courante des CGU Légifrance 2022 non récupérée depuis le compte
   PISTE, non archivée et non comparée au référentiel ;
4. quotas PISTE réels non consignés ou protection globale incompatible avec le
   nombre de réplicas Render ;
5. procédure d'incident non testée ;
6. parcours OAuth utilisateur ChatGPT non validé manuellement ;
7. politique de confidentialité ou conditions d'utilisation discordantes avec
   le comportement observé.

## 3. Actifs, menaces et limites de confiance

| Actif / frontière | Menaces principales | Contrôles attendus |
|---|---|---|
| Clés PISTE et secrets Render | fuite Git, image, logs, compte compromis | secret manager, rotation, scan historique, runbook |
| Tenant Auth0 | prise de compte admin, DCR abusif, mauvais callback, clé tournée | MFA admin, protections anti-bruteforce, journal d'audit, paramètres exacts |
| Jetons OAuth | confusion issuer/audience/algorithme, rejeu, portée excessive | `iss` exact, `aud` exact, RS256 seul, durée courte, PKCE S256, JWKS |
| Endpoint Render | accès anonyme, DoS, gros corps, redirections/TLS/Host | OAuth obligatoire, limite de corps, HTTPS, aucun redirect, host canonique |
| Quotas PISTE | Sybil multi-comptes, réplica ou redémarrage contournant le compteur mémoire | budget global externe ou un seul réplica, plafond par sujet, alerte 429 |
| Contenu Légifrance/Judilibre | prompt injection dans un texte, HTML, métadonnée forgée | sortie structurée, contenu marqué non fiable, aucun interpréteur/exécution |
| Décisions Judilibre | réidentification, profilage, défaut d'occultation | interdictions, retrait temporaire, relais Cour de cassation |
| Comptes GitHub/Render/PISTE | supply-chain, déploiement ou clé détournés | MFA, moindre privilège, revue, environnements protégés, journaux |
| Journaux | secret ou donnée personnelle, conservation excessive | liste blanche métier, pseudonyme, rétention et accès bornés |

Risques résiduels à décider : le limiteur en mémoire est remis à zéro à chaque
redémarrage et n'est pas partagé entre réplicas ; OAuth n'empêche pas une même
personne de créer plusieurs comptes ; la disponibilité des API amont n'est pas
garantie. Tant qu'aucun limiteur global n'existe, la production doit rester à
**un seul réplica** avec des plafonds inférieurs aux quotas PISTE réels.

## 4. Registre d'exécution

Statuts : `PROUVÉ`, `À REJOUER`, `ACTION HUMAINE`, `BLOQUANT`, `ACCEPTÉ`.

| ID | Contrôle | Statut au 03/09/2026 | Preuve attendue / existante | Responsable | Dernière revue |
|---|---|---|---|---|---|
| E1 | CI métadonnées OAuth et refus anonyme | PROUVÉ | PR #17, tests `check_oauth_metadata.py` | mainteneur | 31/08/2026 |
| E2 | Parcours OAuth automatisé serveur | PROUVÉ | PR #18, `test_oauth_end_to_end.py` | mainteneur | 31/08/2026 |
| E3 | Émetteur de production exact | PROUVÉ techniquement | PR #20 + `--check-issuer`; capture tenant à conserver | mainteneur | 31/08/2026 |
| E4 | Six outils sur service déployé | PROUVÉ (image Alpine) | Rejoué le 03/09/2026 avec jeton M2M contre `/health` version `0.8.0` : six outils découverts et chacun réellement appelé ; Légifrance 1,429 s, Judilibre 0,487 s ; lectures avec texte, identifiant, provenance officielle, datation, parcours `search` → `fetch` et absence non inventée conformes. Détail : [pieces-humaines.md](pieces-humaines.md) § 4 ; issue #34 fermée | mainteneur | 03/09/2026 |
| E5 | Parcours OAuth utilisateur ChatGPT | ACTION HUMAINE | capture connexion, appel réussi, déconnexion/révocation | mainteneur | — |
| E6 | CGU Légifrance 2022 intégrales | BLOQUANT | PDF exporté du compte PISTE + SHA-256 + date + diff | titulaire PISTE | — |
| E7 | CGU Judilibre 06/01/2022 | PROUVÉ pour le texte public | URL officielle + empreinte archivée lors de l'audit | mainteneur | 31/08/2026 |
| E8 | Paramètres tenant Auth0 | ACTION HUMAINE (partiel) | `auth0-security-checklist.md` : 3 lignes prouvées et 6 partielles depuis le code et le document de découverte (1/9/2026) ; captures du tableau de bord à archiver | admin Auth0 | 01/09/2026 |
| E9 | Quotas réels et nombre de réplicas | ACTION HUMAINE | capture PISTE + configuration Render | titulaire PISTE | — |
| E10 | Retrait d'urgence Judilibre | À REJOUER | tests unitaires PROUVÉS (PR #46 : casse, liste malformée refusée, nombre journalisé) ; exercice chronométré du runbook sur Render : [pieces-humaines.md](pieces-humaines.md) § 6 | mainteneur | 01/09/2026 |
| E11 | CVE système sans correctif éditeur | BLOQUANT | rapport Trivy CI + analyse d'exploitabilité et acceptation datée | mainteneur sécurité | à chaque build |
| E12 | Audit adversarial du chemin d'authentification | PROUVÉ **pour la part rejouable** ; banc complet non archivé | les sondes publiques du 4/9/2026 sont reproductibles telles quelles (§ 8), et les refus d'algorithme, d'émetteur, d'audience et d'expiration sont couverts par des tests commis (`tests/test_auth.py`). En revanche le banc d'attaque ayant produit le 13/13 — confusion HS256 forgée à la main, `nbf` futur, injection de journal par le `sub` — était un script jetable : **il n'est pas archivé, et un tiers ne peut pas le rejouer en l'état**. La ligne ne passera à PROUVÉ que lorsqu'il le sera | mainteneur | 04/09/2026 |

## 5. Programme de contrôles

### Phase A — Référentiel, comptes et chaîne d'approvisionnement

- inventorier versions, images, actions CI et comptes GitHub/Render/Auth0/PISTE ;
- vérifier MFA, rôles, comptes dormants, jetons personnels et journaux d'audit ;
- produire un SBOM CycloneDX pour Python et l'image ;
- scanner dépendances Python et image pour les CVE ; la CI inventorie toutes
  les sévérités élevées/critiques et bloque automatiquement celles pour
  lesquelles l'éditeur publie un correctif ;
- mettre à niveau les paquets système pendant le build. Une CVE sans correctif
  ne doit jamais être masquée : elle reste dans le rapport et impose, avant
  publication, une analyse d'exploitabilité et une acceptation datée en E11 ;
- vérifier les hashes/lock des dépendances et épingler l'image de base par digest ;
- épingler les GitHub Actions par SHA, réduire `permissions`, isoler les secrets
  des PR de forks et activer les mises à jour automatiques ;
- conserver l'attestation reliant image, commit et résultat des contrôles.

Sortie : inventaire daté, SBOM, rapports CVE complets, aucune CVE corrigeable
élevée/critique, aucun secret dans le dépôt ou l'historique, risques résiduels
et risques de comptes documentés.

### Phase B — OAuth 2.1 et tenant Auth0

Vérifier le code **et** le tenant réel :

- DCR/CIMD ou client prédéfini explicitement choisi ;
- redirect URI exacte, aucune wildcard, PKCE `S256` exigé ;
- issuer, audience et resource exacts ; algorithme d'accès **RS256 seulement** ;
- durée de jeton bornée, rotation JWKS testée, aucune acceptation `none`/`HS*` ;
- méthodes du token endpoint minimales ; portées et rôles minimaux ;
- politique de création de compte, MFA admin, anti-bruteforce, détection de
  credential stuffing et conservation des logs ;
- 401 avec challenge RFC 9728 et refus des jetons expirés, mauvaise audience,
  mauvais issuer, clé inconnue ou portée absente.

Sortie : checklist Auth0 remplie, captures sans secrets, tests négatifs verts.

### Phase C — Réseau, conteneur et plateforme

- vérifier TLS, chaîne de certificats, DNS, absence de redirection sur `/mcp`,
  en-têtes `Host`/proxy et URL canonique ;
- tester SSRF/rebinding via les URLs configurables et la récupération JWKS ;
- confirmer conteneur non-root, filesystem minimal, aucune clé dans les couches,
  taille de corps et concurrence bornées ;
- ne pas activer CORS : le flux MCP est serveur-à-serveur. Tout besoin futur
  doit être prouvé puis limité à une origine explicite ;
- distinguer le logger racine `WARNING` du logger métier autorisé `INFO` ; ce
  dernier ne journalise que outil, issue, durée et pseudonyme.

### Phase D — Abus, quotas et résilience

- aligner les budgets applicatifs sur les quotas PISTE observés, avec marge ;
- tester rafales, concurrence, timeout, 429 amont, redémarrage et multi-réplica ;
- arrêter immédiatement toute sonde live sur premier 429 ;
- limiter à un réplica ou déployer un quota global atomique avant scaling ;
- documenter le risque Sybil et prévoir suspension/révocation par sujet ;
- vérifier que l'échec amont reste « source non vérifiée ».

### Phase E — Données, injection et CGU

- traiter l'empreinte tronquée du sujet comme une **donnée personnelle
  pseudonymisée**, jamais comme une donnée anonyme ; documenter finalité,
  intérêt légitime, accès, durée et suppression ;
- tester qu'un texte de décision contenant une fausse instruction reste une
  chaîne de données et n'entraîne aucun appel ou exécution ;
- vérifier source, URL, juridiction, formation, siège, date de décision et date
  de mise à jour lorsqu'elle est fournie par Judilibre ;
- rejouer la procédure `incident-response.md`, y compris le retrait temporaire
  par `MCP_JUDILIBRE_SUPPRESSED_IDS` et sa levée après correction amont ;
- comparer ligne par ligne les CGU Légifrance 2022 récupérées avec
  `obligations-cgu.md`. Jusque-là, aucune conclusion de conformité Légifrance.

### Phase F — Tests dynamiques séparés

**Staging destructif** : environnement dédié, amont simulé ou clés de test,
fuzzing des schémas, gros corps, charge, concurrence, OAuth négatif, prompt
injection et pannes. Aucun secret de production.

**Production non destructif** : health, métadonnées, authentification, puis au
maximum un appel représentatif par API avec un budget écrit. Aucun fuzzing,
aucune charge, aucun balayage. Arrêt immédiat sur 429, 5xx répété ou anomalie de
quota.

## 6. Sévérité et clôture

| Niveau | Exemple | Délai |
|---|---|---|
| Critique | clé exposée, bypass OAuth, exécution depuis contenu amont | rotation/fermeture immédiate |
| Élevé | confusion issuer/audience, quota exploitable, défaut d'occultation redistribué | avant publication |
| Moyen | rétention ou métadonnée insuffisamment documentée | plan daté avant publication |
| Faible | durcissement sans voie d'exploitation réaliste | backlog accepté |

La clôture exige : registre à jour, preuves liées au commit et à l'image,
100 % des affirmations contractuelles à risque élevé vérifiées ou marquées en
abstention, aucun critique/élevé ouvert, et approbation humaine des éléments
Auth0/PISTE/Render.

## 7. Sources primaires

- [OpenAI — annotations des outils](https://developers.openai.com/plugins/build/mcp-server#tool-annotations-and-elicitation)
- [OpenAI — authentification OAuth](https://developers.openai.com/plugins/build/auth)
- [OpenAI — sécurité et confidentialité](https://developers.openai.com/plugins/guides/security-privacy)
- [PISTE — catalogue Légifrance, identifiant CGU 15/12/2022](https://piste.gouv.fr/api-catalog-sandbox?filter=legifrance)
- [Judilibre — CGU du 6 janvier 2022](https://piste.gouv.fr/images/cgu/CGU_open_data_V8.pdf)

## Étape 7 — Auto-critique adversariale

- Une suite de tests verte ne prouve pas la configuration des consoles SaaS.
- La suppression d'une décision complète est une mesure conservatoire plus
  restrictive qu'une occultation ciblée ; elle évite toute altération autonome
  et doit rester temporaire jusqu'à correction par la Cour de cassation.
- Les obligations Légifrance restent ouvertes tant que le document 2022 accepté
  par le titulaire n'a pas été obtenu et contrôlé.
- Une sonde unique peut mentir dans les deux sens. L'essai d'enregistrement
  dynamique du 4/9/2026 renvoyait d'abord une erreur de *schéma*, qu'une lecture
  pressée aurait classée « DCR ouverte, finding critique ». Il a fallu faire
  varier le corps trois fois pour atteindre la vraie porte, qui répond
  « dynamic client registration is disabled ». Toute conclusion tirée d'une
  seule requête doit être tenue pour suspecte.

## 8. Findings de l'audit adversarial du 4 septembre 2026

Méthode : sondes publiques en lecture seule contre la production, puis banc
d'attaque local exerçant le vrai vérificateur de jetons avec des jetons forgés
(clés engendrées à la volée, aucun secret réel). Aucune modification de
production, aucun client créé, aucun jeton réel manipulé.

| ID | Gravité | Objet | État |
|---|---|---|---|
| SEC-01 | **ÉLEVÉE** | Amplification JWKS non authentifiée : un `kid` inconnu force un appel réseau vers Auth0 à **chaque** requête, sans cache négatif ni limitation avant authentification. Aggravé par `timeout` à 30 s sur un pool de 40 threads, dans un processus unique | **corrigé** : rafraîchissement forcé bridé à un par minute quel que soit le nombre de `kid` distincts, et `timeout` ramené à 5 s. Contre-épreuve exécutée : 20 rafraîchissements sur le code vulnérable, 1 sur le code corrigé (`test_unknown_kid_flood_triggers_a_single_forced_refresh`). **Reste ouvert** : aucune limitation de débit par IP avant authentification — à poser à la bordure, hors code |
| SEC-02 | **ÉLEVÉE** | L'authentification est la seule autorisation : aucune portée exigée, aucune liste de sujets autorisés. Tout jeton du locataire portant la bonne audience ouvre les six outils et consomme les quotas PISTE du titulaire | dépend d'un réglage non observable de l'extérieur, voir ci-dessous |
| SEC-03 | MOYENNE | La révocation d'une clé de signature n'est pas honorée : `cache_keys=True` installe un cache sans expiration, et le JWKS ne comptant que deux clés, rien n'est jamais évincé. Une clé révoquée reste acceptée jusqu'au redémarrage | **corrigé** : `cache_keys=False` et cache à expiration ramené de 3600 s à 300 s. Une clé révoquée cesse d'être acceptée en cinq minutes au pire, non plus au redémarrage du processus (`test_jwks_client_is_configured_defensively`) |
| SEC-04 | MOYENNE | HSTS, `nosniff` et `Referrer-Policy` absents ; `x-render-origin-server: uvicorn` divulgue la pile amont. Sans HSTS, la **première** requête d'un client reste interceptable — or c'est celle qui porte un jeton | ouvert |
| SEC-05 | MOYENNE | La documentation contredisait l'état réel de la DCR | **corrigé le 4/9/2026**, et la correction est corroborée par une mesure indépendante |
| SEC-06 | MOYENNE | Le locataire annonce `plain` pour PKCE, et les grants `password`, `implicit` et `token-exchange` | à refermer au tableau de bord, sur le client |
| SEC-07 | FAIBLE | Locataire `dev-*` en production : plafonds de débit bas, ce qui aggrave SEC-01, et aucun engagement de service | à acter ou à migrer |
| SEC-08 | FAIBLE | `POST /mcp/` répond `307` **avant** authentification, sans `WWW-Authenticate` : un client qui aborde le serveur par la barre finale ne peut pas découvrir les métadonnées. Même classe de défaut que la rupture historique du connecteur | ouvert |
| SEC-09 | FAIBLE | `/.well-known/openai-apps-challenge` publie sans authentification le contenu littéral d'une variable d'environnement. Aujourd'hui sans effet — la variable n'est pas posée, la route répond `404` — mais une erreur de saisie au tableau de bord la publierait aussitôt | à retirer après la vérification de domaine |
| SEC-10 à SEC-13 | INFO | Audience multi-valuée acceptée (sémantique RFC 7519 normale) ; pseudonyme SHA-256 non salé (point RGPD, pas de sécurité) ; quotas en mémoire volatils et autoritaires sur un seul processus ; hôte amont volontairement divulgué dans les messages d'erreur | consignés |

**Conséquence sur les portes bloquantes du § 2** — SEC-01 et SEC-02 étant de
gravité élevée, la première porte reste fermée tant qu'ils ne sont pas corrigés
ou explicitement acceptés et datés par le mainteneur.

**La question qui décide de SEC-02** — sa gravité dépend d'un réglage
invisible depuis l'extérieur : **l'inscription libre est-elle ouverte sur le
locataire Auth0 ?** Si elle l'est, n'importe quel internaute peut créer une
identité, obtenir un jeton valide et consommer les clés PISTE du titulaire, à
qui la consommation est imputée. Si elle est fermée, la surface se réduit aux
comptes existants et le finding retombe à MOYENNE. Ce réglage doit être relevé
au tableau de bord avant toute publication.

**Ce que l'audit n'a pas pu vérifier**, et sur quoi aucun ✅ ne doit être posé
sans une pièce du tableau de bord : le mode d'authentification réel du client
`tpc_tTMV…`, l'ouverture de l'inscription, le MFA administrateur, les
protections anti-force-brute, les connexions actives, la liste exacte des URI
de redirection, le journal Auth0, les variables d'environnement effectives sur
Render, et le lien entre la version `0.8.0` annoncée par `/health` et un commit
précis — `/health` ne publie aucune empreinte de révision.

**Ce qui a résisté** — treize attaques, treize refus : `alg: none`, confusion
HS256 forgée à la main, RS384, PS256, `kid` inconnu, émetteur à une barre
oblique près, audience étrangère, audience absente, `exp` dépassé, `nbf`
futur, `exp` absent, `sub` vide, et injection de journal par un `sub` contenant
un saut de ligne — neutralisée par le pseudonyme. S'y ajoutent l'absence de
SSRF, l'étanchéité des identifiants PISTE et la constance du corps de refus.

─────────────────────────────────────────────
Modules activés                       : [DOC-AUDIT]
Modules non activés                   : [PÉNAL, ACTE-ADMIN, PA-PJ, FOND, CONTENTIEUX]
Niveau de confiance global            : modéré
Sources informelles signalées         : aucune
Limites de la recherche               : CGU Légifrance 2022 intégrales non accessibles anonymement ; consoles Auth0/PISTE/Render non inspectées
─────────────────────────────────────────────
