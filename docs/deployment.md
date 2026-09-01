# Déploiement public du serveur MCP

## État de cette étape

Le serveur est déployé sur Render à l'adresse
`https://droit-francais-skill.onrender.com/mcp`. Le 30 août 2026, la sonde de
santé, la découverte des six outils MCP et un appel réel vers chacune des API
Légifrance et Judilibre ont réussi. Le skill historique et le serveur local
déclaré dans `.mcp.json` restent inchangés dans leur mode d'installation.

```text
ChatGPT / Codex
      │ HTTPS — Streamable HTTP
      ▼
    /mcp
      │ outils en lecture seule
      ▼
Serveur MCP non-root
      │ limite concurrence + débit par instance
      ▼
API PISTE Légifrance et Judilibre
```

Les identifiants PISTE sont des secrets **du serveur**. Ils ne sont ni des
paramètres d'outil, ni copiés dans l'image Docker, ni renvoyés à OpenAI ou aux
utilisateurs.

## Construire et vérifier l'image

```bash
docker build -t droit-francais-mcp .
```

Pour un test local du conteneur, fournir les secrets au démarrage depuis un
gestionnaire de secrets ou un fichier local ignoré par Git :

```bash
docker run --rm -p 8000:8000 --env-file .env.production droit-francais-mcp
```

Le conteneur démarre en utilisateur non privilégié, écoute sur le port indiqué
par `PORT` et expose :

- `POST /mcp` : transport MCP Streamable HTTP ;
- `GET /health` : sonde minimale (`status` et version, sans secret) ;
- `GET /.well-known/openai-apps-challenge` : vérification de domaine OpenAI,
  inactive tant que `OPENAI_APPS_CHALLENGE` n'est pas défini ;
- `GET /.well-known/oauth-protected-resource/mcp` : métadonnées de ressource
  protégée (RFC 9728), publiées dès que `MCP_AUTH_MODE=oauth`. La même charge
  utile est servie sur `/.well-known/oauth-protected-resource` pour les clients
  qui interrogent la racine.

Le TLS doit être terminé par la plateforme d'hébergement ou un reverse proxy :
la connexion soumise à ChatGPT doit être une URL publique `https://…/mcp`.

## Variables d'environnement

### Obligatoires en production

| Variable | Rôle |
|---|---|
| `MCP_ENV=production` | Active les contrôles de démarrage stricts |
| `LEGIFRANCE_CLIENT_ID` | Identifiant OAuth PISTE Légifrance |
| `LEGIFRANCE_CLIENT_SECRET` | Secret OAuth PISTE Légifrance |
| `JUDILIBRE_KEY_ID` | Clé Judilibre (`PISTE_KEY_ID` reste accepté comme alias) |
| `LEGIFRANCE_ENV=prod` | Interdit le sandbox sur le service public |
| `JUDILIBRE_ENV=prod` | Interdit le sandbox sur le service public |
| `MCP_AUTH_MODE=oauth` | Exige un jeton OAuth 2.1 valide sur `/mcp` |
| `MCP_PUBLIC_URL` | URL publique du service, sans `/mcp` (https obligatoire) |
| `MCP_OAUTH_ISSUER` | Émetteur, recopié **à l'identique** depuis le champ `issuer` du document de découverte, barre oblique finale comprise (https obligatoire) — voir [oauth.md](oauth.md) |

Le démarrage échoue si `MCP_ENV=production` et `MCP_AUTH_MODE=disabled` :
une passerelle MCP publique anonyme consommerait les quotas Légifrance et
Judilibre sous la seule responsabilité du titulaire des clés PISTE. La
procédure de configuration de l'émetteur figure dans [`oauth.md`](oauth.md).

### Facultatives — authentification

| Variable | Défaut | Effet |
|---|---|---|
| `MCP_OAUTH_AUDIENCE` | `MCP_PUBLIC_URL` + `/mcp` | Audience exigée dans le jeton (RFC 8707) |
| `MCP_OAUTH_JWKS_URL` | `MCP_OAUTH_ISSUER` sans barre finale + `/.well-known/jwks.json` | Clés publiques de vérification |
| `MCP_OAUTH_REQUIRED_SCOPES` | `legal:read` | Portées exigées, séparées par des virgules ; `-` désactive le contrôle de portée sans désactiver l'authentification |
| `MCP_JUDILIBRE_SUPPRESSED_IDS` | vide | Identifiants Judilibre retirés temporairement, séparés par des virgules ; voir `incident-response.md` |

Le conteneur définit déjà `MCP_ENV=production`, `MCP_HOST=0.0.0.0` et
`PORT=8000`. La commande suivante permet de contrôler la configuration sans
lancer le service :

```bash
python mcp_server/server.py --check-config
```

### Garde-fous réglables

| Variable | Défaut | Effet |
|---|---:|---|
| `MCP_MAX_CONCURRENT_REQUESTS` | `8` | Nombre maximal d'appels d'outils simultanés par instance |
| `MCP_TOOL_CALLS_PER_MINUTE` | `120` | Budget glissant d'appels d'outils par instance |
| `MCP_USER_CALLS_PER_MINUTE` | `20` | Budget glissant d'appels d'outils par utilisateur authentifié |
| `MCP_QUEUE_TIMEOUT_SECONDS` | `2` | Attente maximale avant une erreur de surcharge explicite |
| `MCP_MAX_REQUEST_BODY_BYTES` | `1048576` | Taille maximale d'une requête HTTP MCP |
| `MCP_LOG_LEVEL` | `INFO` local, `WARNING` dans l'image | Niveau des journaux applicatifs et du SDK MCP |
| `OPENAI_APPS_CHALLENGE` | absent | Jeton temporaire de vérification du domaine |

La limite est locale à chaque instance et est remise à zéro au redémarrage.
Tant qu'aucun limiteur global atomique n'est déployé, conserver **un seul
réplica**. Avec plusieurs réplicas, ajouter une limite globale au niveau de la
plateforme afin de rester dans les quotas PISTE.
Le budget porte sur les appels d'outils ; une opération peut effectuer plusieurs
requêtes techniques (authentification puis lecture). Régler donc cette valeur de
façon conservatrice selon les quotas réellement accordés à l'application PISTE.

## Confidentialité et exploitation

Le journal métier ajouté par l'application ne contient que le nom technique de
l'opération, son résultat (`success`, `upstream_error` ou `throttled`), sa
durée et une empreinte tronquée du sujet authentifié. Cette empreinte est une
donnée personnelle pseudonymisée, et non anonyme. Le jeton, sa charge utile
et l'identifiant brut du compte ne sont jamais journalisés. Il ne journalise ni les arguments, ni les textes juridiques, ni les
résultats, ni les clés. L'image utilise `WARNING` par défaut afin de supprimer
les journaux informatifs du SDK MCP et du serveur HTTP. Si `INFO` est réactivé
pour diagnostiquer un incident, ces composants peuvent journaliser une adresse
réseau, un chemin HTTP et un identifiant de session MCP éphémère. Les journaux
d'accès de l'hébergeur peuvent contenir les mêmes métadonnées : leur durée de
conservation doit être réglée et décrite dans la politique de confidentialité.

Les réponses Judilibre peuvent contenir des données personnelles présentes
dans des décisions publiques. Le service doit conserver les mécanismes de
pseudonymisation et les restrictions de réutilisation de la source ; il ne doit
pas servir au profilage des magistrats ou des greffiers.

Le service est déjà exposé au réseau public, avec OAuth obligatoire. Avant sa
publication dans l'annuaire OpenAI, finaliser la [checklist de confidentialité](privacy-checklist.md),
dérouler le [plan d'audit sécurité](audit-securite.md) et le
[registre des obligations CGU](obligations-cgu.md), puis vérifier les quotas et
conditions attachés aux abonnements PISTE utilisés. La correction des findings
critiques et élevés de l'audit conditionne la publication dans l'annuaire.
La [politique de confidentialité](privacy-policy.md), les
[conditions d'utilisation](terms-of-use.md) et le
[guide de soumission ChatGPT](chatgpt-submission.md) décrivent l'état public.

## Passage en mode développeur ChatGPT

1. Utiliser l'origine HTTPS stable
   `https://droit-francais-skill.onrender.com`. Le changement ultérieur de
   l'origine (`scheme`, hôte ou port) peut imposer une nouvelle soumission.
2. Tester `/mcp` avec MCP Inspector, puis chaque outil avec résultats, erreurs,
   identifiants absents et entrées invalides.

   Une sonde locale automatisée est également fournie :

   ```bash
   python tests/check_mcp_http.py https://droit-francais-skill.onrender.com/mcp
   ```
3. Dans ChatGPT, activer le mode développeur et créer une application MCP avec
   l'URL complète `https://droit-francais-skill.onrender.com/mcp`.
4. Vérifier les six outils. Ils doivent annoncer : `readOnlyHint: true`,
   `destructiveHint: false` et `openWorldHint: false` : ils ne modifient
   aucun état publiquement visible d'internet, même s'ils consultent des API
   externes et consomment leurs quotas.
5. Exécuter les jeux d'évaluation positifs et négatifs, puis conserver les
   résultats de cette version.
6. Lors de la soumission, placer le jeton fourni par OpenAI dans
   `OPENAI_APPS_CHALLENGE`, vérifier le domaine, puis retirer la variable après
   validation.

Ne pas ajouter `.app.json` avec un faux identifiant. Ce fichier ne sera ajouté
qu'après création de la connexion réelle à laquelle le plugin local doit se
rattacher.

## Matériel encore requis pour la publication

- identité développeur ou entreprise vérifiée et droit `Apps Management: Write` ;
- alignement du moyen de contact privé avec l'identité publiée ;
- validation finale et téléversement du logo `assets/logo.png` ;
- vérification du domaine dans le portail OpenAI ;
- passage recommandé à une instance Render sans mise en veille.

Les descriptions, les politiques publiques, l'URL MCP et les cinq cas de test
positifs et trois négatifs sont préparés dans
[`chatgpt-app-submission.json`](../chatgpt-app-submission.json).

Références : [connexion et test du plugin][connect], [soumission][submission],
[exigences de revue MCP][review] et [sécurité et confidentialité][security].

[connect]: https://developers.openai.com/plugins/deploy/connect-chatgpt
[submission]: https://developers.openai.com/plugins/deploy/submission
[review]: https://developers.openai.com/plugins/deploy/app-review
[security]: https://developers.openai.com/plugins/guides/security-privacy
