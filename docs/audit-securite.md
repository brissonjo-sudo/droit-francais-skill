# Plan d'audit sécurité v1.1 — serveur MCP « Droit français »

─────────────────────────────────────────────
Date d'analyse           : 31/08/2026
Date(s) de référence     : 31/08/2026
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
`destructiveHint=false`) mais atteignent des systèmes externes et consomment
des quotas PISTE (`openWorldHint=true`). Les textes juridiques reçus sont des
données non fiables à analyser, jamais des instructions à exécuter.

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

| ID | Contrôle | Statut au 31/08/2026 | Preuve attendue / existante | Responsable | Dernière revue |
|---|---|---|---|---|---|
| E1 | CI métadonnées OAuth et refus anonyme | PROUVÉ | PR #17, tests `check_oauth_metadata.py` | mainteneur | 31/08/2026 |
| E2 | Parcours OAuth automatisé serveur | PROUVÉ | PR #18, `test_oauth_end_to_end.py` | mainteneur | 31/08/2026 |
| E3 | Émetteur de production exact | PROUVÉ techniquement | PR #20 + `--check-issuer`; capture tenant à conserver | mainteneur | 31/08/2026 |
| E4 | Six outils sur service déployé | PROUVÉ M2M | PR #21, sonde live ; **ne prouve pas** le parcours utilisateur ChatGPT | mainteneur | 31/08/2026 |
| E5 | Parcours OAuth utilisateur ChatGPT | ACTION HUMAINE | capture connexion, appel réussi, déconnexion/révocation | mainteneur | — |
| E6 | CGU Légifrance 2022 intégrales | BLOQUANT | PDF exporté du compte PISTE + SHA-256 + date + diff | titulaire PISTE | — |
| E7 | CGU Judilibre 06/01/2022 | PROUVÉ pour le texte public | URL officielle + empreinte archivée lors de l'audit | mainteneur | 31/08/2026 |
| E8 | Paramètres tenant Auth0 | ACTION HUMAINE | checklist `auth0-security-checklist.md` signée/capturée | admin Auth0 | — |
| E9 | Quotas réels et nombre de réplicas | ACTION HUMAINE | capture PISTE + configuration Render | titulaire PISTE | — |
| E10 | Retrait d'urgence Judilibre | À REJOUER | test unitaire + exercice du runbook | mainteneur | 31/08/2026 |
| E11 | CVE système sans correctif éditeur | BLOQUANT | rapport Trivy CI + analyse d'exploitabilité et acceptation datée | mainteneur sécurité | à chaque build |

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

─────────────────────────────────────────────
Modules activés                       : [DOC-AUDIT]
Modules non activés                   : [PÉNAL, ACTE-ADMIN, PA-PJ, FOND, CONTENTIEUX]
Niveau de confiance global            : modéré
Sources informelles signalées         : aucune
Limites de la recherche               : CGU Légifrance 2022 intégrales non accessibles anonymement ; consoles Auth0/PISTE/Render non inspectées
─────────────────────────────────────────────
