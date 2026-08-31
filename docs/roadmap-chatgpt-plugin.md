# Feuille de route — plugin ChatGPT

Suivi de la finalisation du serveur MCP public comme plugin ChatGPT. Mis à jour
à la fin de chaque phase. Le skill historique et son usage hors plugin ne sont
modifiés par aucune de ces phases.

| Phase | Objet | Branche | État |
|---|---|---|---|
| 1 | Débloquer OAuth (écriture de l'émetteur) | `fix/oauth-issuer-metadata` | **Terminée** — vérifiée en production le 31/08/2026 |
| 2 | Rendre la CI contraignante | `ci/restore-full-validation` | Terminée (PR #17 fusionnée, `main` protégée) |
| 3 | Inventaire du checkout local | — | Terminée (sans objet) |
| 4 | Retirer les artefacts de développement | `chore/remove-patch-artifacts` | Terminée (PR #15 fusionnée) |
| 5 | Validation OAuth et MCP de bout en bout | `test/oauth-end-to-end` | **Terminée** — connecteur éprouvé dans ChatGPT le 31/08/2026 |
| 6 | Sécurité et conformité | `docs/conformite` | Terminée — voir [conformite.md](conformite.md) |
| 7 | Dossier de soumission | `release/chatgpt-submission` | Dépôt conforme — reste trois pièces humaines |
| 8 | Publication progressive | `ops/exploitation-surveillance` | Outillage livré — observation et pièces humaines à mener |

---

## Phase 1 — Débloquer OAuth

### Défaut corrigé

Le connecteur ChatGPT ne pouvait pas aboutir : la métadonnée RFC 9728 vers
laquelle ChatGPT est renvoyé annonçait un émetteur différant d'un caractère de
celui publié par Auth0. Relevé sur la production le 31/08/2026 :

| Source | Valeur publiée |
|---|---|
| Auth0, champ `issuer` | `https://dev-7soa32jfmxpejzhs.eu.auth0.com/` |
| `/.well-known/oauth-protected-resource` | `https://dev-7soa32jfmxpejzhs.eu.auth0.com/` |
| `/.well-known/oauth-protected-resource/mcp` | `https://dev-7soa32jfmxpejzhs.eu.auth0.com` |

Le `WWW-Authenticate` du `401` anonyme pointe sur la route `/mcp` — la seule
des deux qui était fausse.

### Cause racine

`_https_url()` appliquait `.rstrip("/")` à `MCP_OAUTH_ISSUER`. La valeur
tronquée était transmise à `AuthSettings.issuer_url`, que le SDK MCP 2.x
sérialise **verbatim** : son modèle `ProtectedResourceMetadata` porte
`model_config = ConfigDict(url_preserve_empty_path=True)`, justement parce que
la comparaison d'émetteur au sens RFC 8414/9207 est une égalité de chaînes.

Deux conséquences ont orienté le correctif :

* une route personnalisée ne pouvait pas corriger `/mcp` — le SDK monte les
  routes personnalisées en dernier, avec la priorité la plus basse ; le
  correctif devait donc porter sur la valeur remise au SDK, pas sur le routage ;
* le défaut était **invisible en local** : `requirements-mcp.txt` déclarait
  `mcp>=1.27,<3`, le poste avait `1.27` (où pydantic rajoutait la barre tout
  seul) tandis que CI et Render installaient `2.1.1`.

### Modifications

* `mcp_server/runtime.py` — `_https_url()` accepte `strip_trailing_slash` ;
  `MCP_OAUTH_ISSUER` est conservé verbatim, `MCP_PUBLIC_URL` reste tronqué.
  Nouvelle propriété `oauth_issuer_base`, réservée aux concaténations d'URL, sur
  laquelle bascule la dérivation du JWKS — ce qui supprime la double barre qui
  obligeait jusqu'ici la documentation à interdire la barre finale.
* `mcp_server/server.py` — suppression de `_canonical_issuer()`, qui *inventait*
  une barre quand le chemin était vide (juste pour Auth0, faux pour un émetteur
  dont la forme canonique n'en porte pas). La route racine sert désormais
  `SETTINGS.oauth_issuer` verbatim. Ajout de `--check-issuer`.
* `mcp_server/auth.py` — inchangé sur le fond. La tolérance à la barre finale
  dans la revendication `iss` d'un jeton est conservée et désormais documentée
  comme distincte de l'égalité stricte exigée côté métadonnée.
* `requirements-mcp.txt` — `mcp==2.1.1` et `PyJWT[crypto]==2.13.0` figés, pour
  que poste, CI et Render se comportent identiquement sur ce point précis.

### Contrôles exécutés

* Suite complète : **69 tests, tous verts**, avec le SDK épinglé (`mcp 2.1.1`).
* 9 tests ajoutés dans `IssuerCanonicalisationTests`, dont trois qui exercent
  réellement les deux routes : la route racine est appelée via son handler, la
  route `/mcp` est reconstruite comme le fait `create_protected_resource_routes`.
  Le test de la route SDK sert aussi de garde-fou de version.
* Sonde HTTP locale, serveur démarré en `MCP_AUTH_MODE=oauth` : les deux routes
  publient une chaîne identique à la valeur configurée, **avec comme sans**
  barre finale, et le `POST /mcp` anonyme rend `401` avec un `resource_metadata`
  pointant sur la route `/mcp`.
* `--check-issuer` contre le locataire Auth0 réel : accepte l'écriture exacte,
  rejette l'autre avec un message explicite et un code de sortie `2`.

### Critère de fin — atteint le 31 août 2026

La variable Render `MCP_OAUTH_ISSUER` a été passée à la forme canonique, barre
oblique finale incluse. Relevé sur la production après redéploiement :

| Source | Valeur publiée |
|---|---|
| Auth0, champ `issuer` | `https://dev-7soa32jfmxpejzhs.eu.auth0.com/` |
| `/.well-known/oauth-protected-resource` | `https://dev-7soa32jfmxpejzhs.eu.auth0.com/` |
| `/.well-known/oauth-protected-resource/mcp` | `https://dev-7soa32jfmxpejzhs.eu.auth0.com/` |

Les trois chaînes sont identiques caractère pour caractère. Vérifications
complémentaires :

* la sonde automatisée passe — émetteur conforme au document de découverte,
  ressource cohérente entre les deux routes, requête anonyme refusée en `401`
  avec le bon challenge :

```bash
python tests/check_oauth_metadata.py https://droit-francais-skill.onrender.com --discover
```

* l'URL JWKS dérivée répond en `200` : la barre finale n'est pas concaténée, et
  le défaut de double barre qui motivait historiquement la troncature n'existe
  donc plus.

---

## Phase 2 — Rendre la CI contraignante

### Constat corrigé

L'énoncé de mission supposait la CI cassée : « aucun workflow n'est associé au
commit `75fc5bd` ». C'est inexact. Le workflow existait bien à ce commit, s'est
déclenché sur `push` et **a réussi** (31/08/2026, 11:07 UTC). Les versions
d'actions employées (`actions/checkout@v7`, `actions/setup-python@v7`) existent
également. Il n'y avait donc rien à restaurer.

La phase porte sur ce que la CI **ne garantissait pas**.

### Trous fermés

* **Aucune couverture des métadonnées OAuth.** La sonde HTTP existante tournait
  en mode anonyme : ni les routes `.well-known`, ni le refus `401` n'étaient
  vérifiés. C'est très exactement ce qui a laissé passer le défaut de la
  phase 1. Nouvelle sonde `tests/check_oauth_metadata.py`, exécutée en CI sur
  **les deux écritures** de l'émetteur, avec un émetteur factice : aucun jeton,
  aucun secret. Elle vise aussi la production avec `--discover`, qui lit
  l'émetteur attendu dans le document de découverte.
* **Divergence de versions invisible.** Étape `pip list` ajoutée : une
  divergence poste / CI / Render se lit désormais dans le journal, au lieu de
  devoir être déduite d'un échec de test.
* **Fragilités du script d'étape.** Le shell d'Actions tourne en `set -e` : les
  attentes de démarrage sont testées par un `if`, l'échec de la sonde est capté
  explicitement, chaque écriture utilise un port distinct — ne jamais dépendre
  du recyclage d'un port entre deux itérations — et un garde-fou distingue un
  serveur qui n'a pas démarré d'une métadonnée fautive.

### Reste à faire — protection de branche

`main` n'est pas protégée : `75fc5bd` y est arrivé par push direct, ce qui
explique le scénario « PR #10 rejouée sur main ». À activer :

* pull request obligatoire avant fusion ;
* check `checks` requis et à jour ;
* push direct interdit.

---

## Phase 3 — Inventaire du checkout local

Phase close sans intervention : l'énoncé de mission supposait des fichiers non
suivis à préserver, l'inventaire ne les trouve pas.

* Arbre de travail propre, aucun fichier non suivi ni modifié.
* `main` local strictement égal à `origin/main` (`75fc5bd`), aucun écart dans
  l'un ou l'autre sens.
* Un seul worktree, aucun worktree résiduel.
* `assets/logo-chatgpt.png` **n'existe pas** ; seul `assets/logo.png` est
  présent, et c'est bien lui que référence le manifeste.
* Aucun dossier `scripts/` à la racine ; les scripts vivent dans
  `skill/scripts/`.
* La branche `feat/oauth-mcp` (`a31e18b`) subsiste en local et sur le distant.
  Elle est laissée intacte : sa suppression sera proposée séparément.

Aucun `reset --hard`, aucune suppression, aucune synchronisation destructrice
n'a été nécessaire.

---

## Phase 4 — Retirer les artefacts de développement

Huit fichiers `.patch` (~128 Ko) à la racine, tous introduits par le seul
commit `75fc5bd`. Vérifié avant suppression : aucune référence dans le code,
les tests, la CI ou la documentation ; aucun secret ; cinq réversibles par
`git apply --check --reverse`, donc strictement redondants avec l'arbre, et les
trois autres vérifiés ligne à ligne. Règle `*.patch` et `*.diff` ajoutée au
`.gitignore`. Aucun `__pycache__`, `.pyc`, `.venv` ni sortie de test n'est
suivi par ailleurs.

`vault/` est conservé : contenu rédigé (versions historiques de la
méthodologie), pas un artefact de construction.

---

## Phase 2 — Protection de branche (complément)

Appliquée sur `main` et vérifiée par un push direct, effectivement rejeté :

| Réglage | Valeur |
|---|---|
| Check requis | `checks`, en mode strict (branche à jour exigée) |
| Pull request | Obligatoire, 0 relecture requise — un mainteneur seul peut fusionner |
| Appliqué aux administrateurs | Oui : le propriétaire non plus ne peut pas pousser directement |
| Force-push, suppression | Interdits |
| Historique linéaire | Exigé |

Le compte de relectures est volontairement à zéro : exiger une approbation
bloquerait un dépôt à mainteneur unique, sans rien ajouter à la garantie
recherchée, qui est que **la CI passe avant toute fusion**.

---

## Phase 5 — Validation de bout en bout

### Volet automatisé — livré

`tests/test_oauth_end_to_end.py` exerce la chaîne réelle en processus :
application ASGI construite par le SDK, middleware d'authentification,
transport Streamable HTTP, dispatch d'outil. Seuls le JWKS de l'émetteur
(clé RSA engendrée à la volée) et les appels aux API juridiques sont simulés.

Seize tests couvrant les scénarios 1 à 5 de la mission :

* requête anonyme refusée en `401`, avec le challenge attendu ;
* jeton valide menant à un appel d'outil réussi, imputé au `sub` du jeton ;
* refus pour audience étrangère, émetteur étranger, expiration, signature
  inconnue, sujet absent ;
* absence de détail exploitable dans le corps du refus ;
* erreur métier ne réexposant aucun secret d'environnement ;
* quota isolé par sujet, avec message explicite au dépassement, et second
  sujet toujours servi ;
* `MCP_OAUTH_REQUIRED_SCOPES=-` laissant l'authentification exigée tout en
  acceptant un jeton sans la portée ; réglage inverse refusant ce même jeton
  en `403`.

Deux points relevés en écrivant ces tests, et corrigés :

* le cas « jeton accepté » ne peut pas se vérifier sur un `POST` brut — hors
  session MCP, le transport répond `400` quel que soit le jeton, ce qui ne
  dirait rien de l'autorisation. Il porte donc sur une session complète ;
* une assertion `assertNotEqual(401, …)` aurait laissé passer un `403`, donc un
  refus de portée. Remplacée par une vérification du succès effectif.

Le harnais est joué par `unittest discover`, donc en CI à chaque PR.

### Volet manuel — à exécuter

[validation-chatgpt.md](validation-chatgpt.md) : check-list numérotée couvrant
la création du connecteur, l'autorisation Auth0, la découverte des six outils,
un appel Légifrance réel, un appel Judilibre réel, le comportement en cas
d'échec et le quota.

**La phase reste ouverte tant que cette check-list n'est pas revenue
renseignée.** Les phases 6 à 8 en dépendent.

---

## Phase 6 — Sécurité et conformité

Audit sur pièces consigné dans [conformite.md](conformite.md). Aucun défaut
constaté : les garde-fous attendus existaient déjà et ont été vérifiés un à un
— secrets hors dépôt et masqués dans les erreurs, validation JWT complète avec
audience liée à la ressource, limitation de concurrence et de débit, quota par
sujet, taille de requête et délais réseau bornés, journal pseudonymisé par
empreinte SHA-256 tronquée, refus de démarrage d'une passerelle publique
anonyme.

Un seul manque a été comblé : les conditions d'utilisation ne portaient pas de
clause de **non-affiliation**. Elles disent désormais explicitement que le
service n'est ni édité, ni approuvé, ni labellisé par la DILA, Légifrance, la
Cour de cassation, Judilibre ou une autre administration.

La note liste six points à surveiller — dont le dimensionnement des quotas,
jamais confronté à une charge réelle, et le fait qu'une version épinglée doit
être suivie sous peine de devenir une dette de sécurité.

---

## Phase 5 — Clôture

Le connecteur « Droit français » a été connecté dans ChatGPT en OAuth sur
l'endpoint Render, ses six outils découverts, et un essai réel a abouti le
31 août 2026 : ChatGPT a enchaîné `search_articles` puis `fetch` et rendu le
texte en vigueur de l'article L. 2212-2 du CGCT, avec l'identifiant
`LEGIARTI000029946370`, son statut, sa date de version et le lien Légifrance.

Le critère de fin est donc atteint : un utilisateur se connecte depuis ChatGPT
et obtient une réponse juridique réelle issue d'une source officielle. Le
connecteur reste en statut **development**, non soumis et non publié.

---

## Phase 7 — Dossier de soumission

### Méthode

Les exigences ont été relevées **à la source**, dans la documentation OpenAI,
et non reprises de `docs/chatgpt-submission.md` — dont une section s'était déjà
révélée fausse tout en se déclarant vérifiée. Le fichier de soumission a
ensuite été validé contre le schéma JSON officiel qu'il déclare.

### Défauts trouvés et corrigés

| Défaut | Conséquence évitée |
|---|---|
| `$schema` pointait vers l'ancien chemin `apps-sdk` | **Échec de validation** du dossier : le schéma exige la forme `plugins` |
| `shortDescription` faisait 50 caractères | Rejet : la limite est de 30 |
| `supportURL` absent du manifeste | Rejet : quatre URL sont exigées, pas trois |
| `release_notes` absent | Rejet : obligatoire à la soumission |
| Version du manifeste `0.5.0` ≠ serveur `0.6.0` | Incohérence visible du dossier |

Le fichier de soumission **valide désormais contre le schéma officiel**.

### Ce qui était déjà conforme

Logo carré 1254 × 1254 en PNG, très en deçà des 5 Mio et des 4096 pixels
admis ; nom, description longue et nom de développeur sous leurs limites ;
catégorie dans la liste OpenAI ; trois prompts de démarrage distincts et
courts ; cinq cas positifs et trois cas négatifs ; justification présente pour
chacune des trois annotations de chacun des six outils ; quatre URL publiques
répondant en `200`.

### Garde-fous ajoutés

`tests/check_plugin.py` applique désormais les limites publiées par OpenAI —
longueurs de champs, liste des catégories, nombre et longueur des prompts et
des capacités, quatre URL, URL de schéma, présence des notes de version et des
justifications — ainsi que la règle de version retenue : **le manifeste du
plugin suit le serveur MCP**, le skill gardant sa propre ligne éditoriale.

Les huit défauts correspondants ont été réintroduits un à un et sont tous
détectés, avec un message nommant la limite dépassée.

### Reste à faire — trois pièces humaines

Elles ne peuvent pas vivre dans le dépôt :

1. **Identité vérifiée** (individuelle ou commerciale) sur OpenAI Platform, et
   droit *Apps Management: Write*. Le relecteur s'en sert pour vérifier que nom,
   site, support, confidentialité et conditions concordent.
2. **Identifiants de démonstration** pour le relecteur, le serveur étant en
   OAuth. Ils doivent fonctionner **sans MFA, SMS ni confirmation par courriel**.
   À créer dans Auth0 comme compte de test dédié.
3. **Enregistrement vidéo** montrant les principaux cas d'usage et outils.

S'y ajoute la **vérification de domaine** : le portail fournit un jeton
temporaire à placer dans la variable Render `OPENAI_APPS_CHALLENGE`, puis à
retirer aussitôt après validation. Le serveur expose déjà la route
`/.well-known/openai-apps-challenge`.

### Point ouvert avant soumission

`MCP_OAUTH_REQUIRED_SCOPES=-` reste actif : `scopes_supported` est vide en
production. C'est documenté comme configuration de compatibilité
([conformite.md](conformite.md) §5) et réversible par un simple changement de
variable. À trancher avant le dépôt du dossier.

---

## Phase 8 — Publication progressive

### Ce qui est livré

`tests/check_service_health.py` — sonde d'exploitation **sans jeton et sans
consommation de quota** : latence de `/health`, version et mode
d'authentification annoncés, contrôles de métadonnées et refus anonyme rejoués.
Sa sortie `--json` tient sur une ligne, faite pour être accumulée : une dérive
de latence ne se voit que sur une série, jamais sur une mesure isolée.

[exploitation.md](exploitation.md) — surveillance, rollback, incidents connus
et conditions de publication.

### Mesures de référence, prises le 31 août 2026

Service chaud, depuis la France : `/health` entre 0,15 s et 0,60 s ;
métadonnées et refus anonyme du même ordre. Ce sont des mesures, pas des
objectifs choisis a priori — les seuils de la sonde en découlent.

### Deux points d'exploitation qui n'étaient écrits nulle part

* **Un rollback depuis le tableau de bord Render désactive les déploiements
  automatiques du service.** C'est voulu — cela évite qu'un déploiement
  réintroduise le défaut — mais le correctif suivant ne partira pas tout seul.
  Le rollback par l'API, lui, ne les désactive pas : un déploiement automatique
  peut alors restaurer le code qu'on venait d'écarter. Les deux voies sont donc
  distinguées, avec leurs pièges respectifs.
* **Un défaut peut venir d'une variable d'environnement, pas du code.** Le
  rollback d'artefact n'y change alors rien. Le cas s'est produit ici même, à la
  phase 1 : le correctif était déployé, mais la variable ne l'était pas.

### Quatre incidents consignés

Écriture de l'émetteur, réveil d'instance pris pour une panne, jeton opaque
refusé faute de *Default Audience*, et portée annoncée vide. Chacun avec son
symptôme, sa cause, sa résolution — et, quand elle existe, la prévention
automatisée.

### Reste à faire

| Condition | État |
|---|---|
| Parcours OAuth éprouvé dans ChatGPT | ✅ |
| Dossier conforme au schéma officiel | ✅ |
| Instance sans mise en veille | ⚠️ à trancher |
| Essai avec un second compte | ☐ |
| Période d'observation sans défaut | ☐ |
| Identité vérifiée, identifiants de démo, vidéo | ☐ humain |

La publication n'est pas une étape de code : elle attend une période
d'observation stable et trois pièces que le dépôt ne peut pas porter.
