# Plan d'audit sécurité — serveur MCP « Droit français »

Ce document planifie un audit de sécurité complet de l'outil **déployé** : le
serveur MCP exposé en HTTPS à l'adresse
`https://droit-francais-skill.onrender.com/mcp`, qui interroge les API
officielles Légifrance et Judilibre via PISTE au nom du titulaire des clés.

Il couvre le périmètre, le modèle de menace, les **skills à récupérer et
utiliser** à chaque phase, les phases de contrôle, la grille de sévérité, les
livrables et le calendrier. La dimension conformité s'appuie sur le
[registre des obligations CGU](obligations-cgu.md).

- **Version du plan** : 1.0 — 31 août 2026
- **Cible** : serveur MCP `v0.6.0`, plugin `v0.5.0`, skill `v3.2.0`
- **Type** : audit combiné revue de code (SAST) + configuration + test
  dynamique (DAST) + conformité (RGPD / CGU)

---

## 1. Objectifs

1. Vérifier qu'aucun secret (clés PISTE, jetons OAuth) ne fuit par le code,
   l'image, les journaux ou les réponses d'erreur.
2. Valider la robustesse de l'authentification OAuth 2.1 et du contrôle d'accès.
3. Confirmer que les garde-fous de charge protègent réellement les quotas PISTE.
4. Vérifier la conformité RGPD du traitement (données personnelles présentes
   dans la jurisprudence Judilibre) et des journaux.
5. **Établir la conformité aux CGU Légifrance et Judilibre** et convertir les
   écarts en actions correctives priorisées.
6. Produire un rapport traçable et une liste d'actions correctives datée.

---

## 2. Périmètre

### Dans le périmètre

- Le service HTTP déployé : routes `POST /mcp`, `GET /health`,
  `GET /.well-known/oauth-protected-resource[/mcp]`,
  `GET /.well-known/openai-apps-challenge`.
- Le code d'exécution : `mcp_server/` (server, runtime, auth, catalog) et la
  bibliothèque `skill/scripts/droit_francais/` (clients Légifrance/Judilibre,
  transport HTTP, config, outils).
- La chaîne d'authentification OAuth 2.1 (vérification JWKS, `iss`/`aud`/`exp`,
  portées).
- Les garde-fous de charge : concurrence, débit par instance et par utilisateur.
- La configuration de déploiement : `Dockerfile`, variables d'environnement,
  `MCP_ENV=production`, terminaison TLS, gestion des secrets Render.
- Les journaux (métier, SDK MCP, accès hébergeur) et leur rétention.
- La CI (`.github/workflows/ci.yml`) comme maillon de la chaîne
  d'approvisionnement.
- La conformité CGU/licences et RGPD (voir [obligations](obligations-cgu.md)).

### Hors périmètre

- Les API amont Légifrance/Judilibre elles-mêmes (sécurité côté DILA / Cour de
  cassation).
- La plateforme OpenAI (ChatGPT/Codex) et l'infrastructure Render au-delà de la
  configuration exposée au client.
- La méthodologie juridique du skill (exactitude du droit) — hors sécurité,
  couverte par l'éval des 18 modes d'erreur.
- Le mode d'installation autonome du skill (`stdio`, usage local sans clé
  partagée), sauf pour la non-régression.

---

## 3. Actifs et modèle de menace

### Actifs à protéger

| Actif | Sensibilité | Menace principale |
|---|---|---|
| Clés PISTE (Légifrance client_id/secret, Judilibre key_id) | Critique | Exfiltration → consommation frauduleuse des quotas du titulaire |
| Jetons OAuth des utilisateurs | Élevée | Rejeu, falsification, élévation de portée |
| Quotas PISTE | Élevée | Épuisement (DoS économique) sous la responsabilité du titulaire (CGU C4) |
| Données personnelles dans les décisions Judilibre | Élevée | Réidentification, profilage de magistrats (CGU J1-J3) |
| Disponibilité du service | Moyenne | DoS, saturation, mise en veille de l'hébergeur |
| Intégrité des réponses juridiques | Moyenne | Réponse falsifiée présentée comme officielle (CGU C7) |

### Surface d'attaque et vecteurs

- **Requête MCP non authentifiée / mal authentifiée** : jeton absent, expiré,
  émis pour une autre audience, algorithme faible (`none`, HS*), `iss` falsifié.
- **Abus applicatif** : rafales d'appels pour épuiser les quotas PISTE ;
  requêtes volumineuses (corps > limite) ; concurrence excessive.
- **Injection dans les paramètres d'outil** transmis aux API amont (numéro
  d'article, requête, identifiant, filtres de date/juridiction).
- **Fuite d'information** : secrets ou données personnelles dans les messages
  d'erreur, les journaux applicatifs, les journaux d'accès de l'hébergeur, ou
  les métadonnées renvoyées.
- **Chaîne d'approvisionnement** : dépendances (`mcp`, `PyJWT[crypto]`), image
  de base `python:3.12-slim`, actions GitHub CI.
- **Mauvaise configuration** : démarrage public sans OAuth, `LEGIFRANCE_ENV`
  pointant vers le sandbox, niveau de log trop verbeux, `.env` embarqué.

### Acteurs

- Utilisateur authentifié abusif (quota, injection).
- Attaquant non authentifié (contournement OAuth, DoS, découverte).
- Tiers recevant des réponses (réutilisation non conforme des décisions).

---

## 4. Récupération et utilisation des skills adaptés

L'audit **mobilise des skills spécialisés** à chaque phase. Cette section
planifie leur récupération et leur activation, comme demandé.

### 4.1 Skills déjà disponibles (à activer)

| Skill | Disponibilité | Rôle dans l'audit | Phase(s) |
|---|---|---|---|
| `security-review` | Intégré Claude Code (`/security-review`) | Revue de sécurité des changements de la branche : secrets, injection, authz, gestion d'erreur | 1, 2, 3 |
| `code-review` | Intégré Claude Code (`/code-review`) | Revue correctness + robustesse (validation d'entrée, cas d'erreur, concurrence) | 1, 4 |
| `dpo-ct` | Skill activé (compte) | Analyse RGPD : base juridique, AIPD, violation de données (notification 72 h), droits des personnes, données publiques Judilibre | 5, 6 |
| `recherche-juridique` | Skill du dépôt + activé | Vérification à la source de la vigueur des textes fondant les CGU (COJ L.111-13, CRPA L.321-1 à L.326-1, code pénal 226-18/24/31) | 6 |
| `session-start-hook` | Intégré Claude Code | Fiabiliser l'exécution des tests/linters de sécurité en session web (hook `SessionStart`) | 0, 7 |

### 4.2 Récupération de skills complémentaires

Avant la phase 1, exécuter une recherche de skills adaptés dans le catalogue
(marketplace) pour compléter la couverture, notamment :

- analyse de dépendances / SBOM et CVE (chaîne d'approvisionnement) ;
- durcissement de conteneur Docker / CIS benchmark ;
- test dynamique d'API HTTP (fuzzing, en-têtes de sécurité).

Procédure : `SuggestSkills` / `SearchSkills` avec les mots-clés
`sécurité, dépendances, SBOM, docker, DAST, OAuth`. Si un skill pertinent
existe, l'installer et l'ajouter à la matrice ci-dessus ; sinon, appliquer les
contrôles manuels décrits dans les phases correspondantes. La revue annuelle
(`skill/references/maintenance.md`) réévalue ce catalogue.

### 4.3 Garde-fou d'usage des skills

Les skills métier (`dpo-ct`, `recherche-juridique`) **vérifient toute règle de
droit à la source officielle avant conclusion** : aucune obligation CGU ou
référence d'article n'est retenue de mémoire. Toute divergence entre ce plan et
la version en vigueur d'une CGU prime en faveur de la source officielle.

---

## 5. Phases de l'audit

Chaque phase indique : objectif, contrôles, skill(s) mobilisé(s), livrable.

### Phase 0 — Cadrage et préparation

- **Objectif** : figer la cible (versions, commit), l'environnement de test et
  les autorisations. Confirmer que l'audit se fait sur une instance de test avec
  des clés PISTE de test (`MCP_ENV=test`), jamais sur les quotas de production.
- **Contrôles** : inventaire des routes, des variables d'environnement, des
  dépendances et des secrets attendus ; mise en place d'un hook `SessionStart`
  garantissant `pip install -r requirements-mcp.txt` + `unittest`.
- **Skill** : `session-start-hook`.
- **Livrable** : périmètre figé, environnement de test opérationnel.

### Phase 1 — Revue de code statique (SAST) et secrets

- **Objectif** : détecter secrets en dur, injections, gestion d'erreur fuyante,
  entrées non validées.
- **Contrôles** :
  - recherche de secrets dans l'historique Git, l'image et les fichiers
    (`.env` jamais embarqué ; `secret_scanning`) ;
  - vérification du masquage des secrets dans `_safe_call` (Légifrance/Judilibre)
    et de l'absence de secret dans les codes de sortie ;
  - validation des entrées d'outils (`number`, `query`, `id`, dates ISO,
    `limit`) et de leur transmission sûre aux clients HTTP (`transport.py`) ;
  - construction d'URL et d'en-têtes amont (pas d'injection d'en-tête, timeout
    présent, taille de réponse bornée à l'affichage d'erreur : 500 caractères).
- **Skills** : `security-review`, `code-review`.
- **Livrable** : liste des findings SAST classés par sévérité.

### Phase 2 — Authentification et autorisation (OAuth 2.1)

- **Objectif** : garantir qu'aucune requête n'atteint les outils sans jeton
  valide en production.
- **Contrôles** :
  - refus des algorithmes symétriques et `none` (seuls RS*/ES* acceptés,
    `ALLOWED_ALGORITHMS`) ;
  - vérification `iss` (tolérance barre oblique finale), `aud` (RFC 8707 —
    rejet d'un jeton émis pour une autre API), `exp`/`nbf`, présence de `sub` ;
  - comportement en cas de JWKS indisponible (échec fermé, pas de bypass) ;
  - contrôle de portée (`legal:read`) et sémantique de l'opt-out explicite
    (`-`/`none`) : un jeton reste exigé même sans portée ;
  - impossibilité de démarrer en production sans OAuth
    (`validate_public` lève si `MCP_AUTH_MODE=disabled`) ;
  - métadonnées RFC 9728 exactes et non sensibles.
- **Skill** : `security-review`.
- **Livrable** : matrice de tests d'authentification (cas passants et rejets).

### Phase 3 — Exposition réseau et durcissement du conteneur

- **Objectif** : réduire la surface exposée et durcir l'exécution.
- **Contrôles** :
  - conteneur non-root, image `slim`, absence d'outils superflus ;
  - `HEALTHCHECK` sans fuite ; `/health` ne renvoie ni secret ni donnée interne ;
  - `/.well-known/openai-apps-challenge` inactif tant que la variable est
    absente (pas de valeur par défaut exploitable) ;
  - en-têtes de réponse (CORS limité au strict nécessaire sur les routes
    `.well-known`), terminaison TLS par la plateforme, redirection HTTPS ;
  - limite de taille de corps (`MCP_MAX_REQUEST_BODY_BYTES`) effective ;
  - niveau de log `WARNING` en image, pas de fuite en `INFO`.
- **Skill** : `security-review` + contrôles manuels (durcissement Docker).
- **Livrable** : rapport de configuration + écarts de durcissement.

### Phase 4 — Résilience, abus et protection des quotas

- **Objectif** : confirmer que les garde-fous empêchent l'épuisement des quotas
  PISTE (obligation CGU C4) et absorbent les abus.
- **Contrôles** :
  - `RequestGovernor` : concurrence bornée (`BoundedSemaphore`), débit glissant
    par instance, erreur explicite de surcharge (`RuntimeCapacityError`) ;
  - `PrincipalRateLimiter` : quota par utilisateur authentifié, purge des
    compartiments inactifs (borne mémoire, pas de fuite) ;
  - comportement multi-réplicas : nécessité d'une limite globale plateforme ;
  - alignement des valeurs par défaut sur les quotas PISTE réellement accordés ;
  - tenue sous charge (rafale concurrente, corps volumineux, requêtes lentes).
- **Skills** : `code-review` (concurrence, exactitude des limites).
- **Livrable** : résultats de tests de charge + recommandations de réglage.

### Phase 5 — Confidentialité et données personnelles (RGPD)

- **Objectif** : conformité RGPD du traitement et des journaux ; maîtrise des
  données personnelles issues de Judilibre.
- **Contrôles** :
  - journaux métier limités à opération/état/durée + empreinte tronquée du
    sujet (`_pseudonym`) ; ni argument, ni texte, ni secret, ni identifiant brut ;
  - journaux SDK/HTTP et journaux d'accès hébergeur : contenu et rétention
    (Render, 7 j en Hobby) documentés et minimisés ;
  - absence de base de données persistante (pas de stockage des requêtes/réponses) ;
  - non-réidentification et non-profilage garantis par l'architecture (CGU
    J1-J2) ;
  - **procédure d'incident et de compromission de clés** (CGU C3) — écart à
    combler ;
  - **canal de signalement des réidentifications manifestes** vers la Cour de
    cassation (CGU J3) — écart à combler ;
  - complétude de `privacy-policy.md` : finalités, bases juridiques,
    destinataires, transferts (Render US), droits, DPO.
- **Skill** : `dpo-ct` (AIPD, minimisation, violation de données, art. 32 RGPD).
- **Livrable** : analyse RGPD + AIPD simplifiée + procédure d'incident.

### Phase 6 — Conformité CGU et licences

- **Objectif** : établir la conformité aux CGU Légifrance et Judilibre et à la
  Licence Ouverte 2.0.
- **Contrôles** : dérouler le [registre des obligations](obligations-cgu.md)
  point par point (C1-C8, L1-L3, J1-J8), en particulier :
  - mention systématique de la **source** et de la **date/version** dans les
    réponses (C6, J6, J7) ;
  - métadonnées obligatoires par décision : juridiction, formation, siège, date
    du prononcé (J6) ;
  - interdiction de profilage/réidentification reflétée dans la sortie et les
    CGU publiques (J1-J2) ;
  - relais des demandes d'occultation/levée vers la Cour de cassation (J4-J5) ;
  - mention distincte de la Licence Ouverte 2.0 des **données** vs licence du
    **code** (L1).
  - **vérification de vigueur à la source** des textes fondateurs (COJ, CRPA,
    code pénal) et de la version en vigueur des deux CGU.
- **Skills** : `recherche-juridique` (vigueur des textes), `dpo-ct` (volet
  données personnelles).
- **Livrable** : tableau de conformité CGU renseigné + écarts priorisés.

### Phase 7 — Test dynamique (DAST) et validation

- **Objectif** : confirmer le comportement réel du service déployé.
- **Contrôles** :
  - sonde `tests/check_mcp_http.py` contre l'instance de test ;
  - MCP Inspector : découverte des 6 outils, annotations `readOnlyHint: true`,
    `destructiveHint: false`, `openWorldHint: false` ;
  - jeux positifs/négatifs (`chatgpt-app-submission.json`) : identifiants
    absents, entrées invalides, erreurs amont, quota atteint ;
  - vérification que les erreurs ne fuient ni secret ni trace interne ;
  - test des `.well-known` et de la négociation OAuth de bout en bout.
- **Skills** : `security-review` (analyse des réponses), `session-start-hook`
  (exécution fiable des sondes en session).
- **Livrable** : preuves d'exécution + captures des réponses.

---

## 6. Grille de sévérité

| Niveau | Définition | Délai de correction cible |
|---|---|---|
| Critique | Fuite de secret, contournement d'authentification, réidentification possible | Immédiat (blocage mise en ligne) |
| Élevé | Épuisement de quota exploitable, fuite de donnée personnelle, non-conformité CGU sanctionnable (profilage, occultation) | ≤ 7 jours |
| Moyen | Durcissement manquant, journal trop verbeux, mention de source/date absente | ≤ 30 jours |
| Bas | Amélioration défensive, documentation, licence des données | Revue annuelle |

---

## 7. Livrables

1. **Rapport d'audit** daté : findings par phase, sévérité, preuve, recommandation.
2. **Registre des obligations CGU renseigné** ([obligations-cgu.md](obligations-cgu.md)),
   colonne « état » à jour.
3. **Procédure d'incident** (compromission de clés PISTE, réidentification,
   défaut d'occultation) avec points de contact DILA/AIFE et Cour de cassation.
4. **Matrice de tests d'authentification et de charge** rejouable.
5. **Plan d'actions correctives** priorisé selon la grille de sévérité.
6. Mise à jour de la [checklist de confidentialité](privacy-checklist.md) et,
   si nécessaire, de `privacy-policy.md` / `terms-of-use.md`.

---

## 8. Calendrier indicatif

| Semaine | Phases | Jalons |
|---|---|---|
| S1 | 0, 1 | Cadrage figé ; findings SAST |
| S2 | 2, 3, 4 | Authz validée ; durcissement ; tenue en charge |
| S3 | 5, 6 | Analyse RGPD ; conformité CGU ; écarts priorisés |
| S4 | 7 | Test dynamique ; rapport final ; plan d'actions |

La correction des findings **critiques et élevés** conditionne l'ouverture au
public (soumission ChatGPT) et complète les prérequis listés dans
[`deployment.md`](deployment.md) et [`privacy-checklist.md`](privacy-checklist.md).

---

## 9. Sources de référence

- [Registre des obligations CGU](obligations-cgu.md)
- [Guide de déploiement](deployment.md)
- [Guide OAuth 2.1](oauth.md)
- [Politique de confidentialité](privacy-policy.md)
- [Conditions d'utilisation](terms-of-use.md)
- [Checklist de confidentialité](privacy-checklist.md)
- [CGU API Légifrance (DILA, V1.1)](https://piste.gouv.fr/images/cgu/DILA_Legifrance_Beta_v2.pdf)
- [CGU réutilisation données judiciaires (Cour de cassation, 06/01/2022)](https://piste.gouv.fr/images/cgu/CGU_open_data_V8.pdf)
- [Licence Ouverte 2.0 (Etalab)](https://www.etalab.gouv.fr/licence-ouverte-open-licence)
