# Serveur MCP — Droit français

Cette première intégration ChatGPT est une app **tool-only** : elle n'affiche
pas de widget et ne modifie aucune donnée. Elle donne au modèle des opérations
de lecture structurées sur Légifrance et Judilibre, tout en conservant le skill
historique comme couche de méthode juridique.

## Contrat des outils

| Outil | Source | Usage |
|---|---|---|
| `search(query)` | Légifrance ou Judilibre | Recherche standard ; renvoie `id`, `title`, `url` |
| `fetch(id)` | Légifrance ou Judilibre | Lit un résultat renvoyé par `search` |
| `search_articles(number, code?, date?, limit?)` | Légifrance | Recherche ciblée d'un article applicable à une date |
| `get_article(id, date?)` | Légifrance | Lit une version `LEGIARTI` et son statut |
| `search_case_law(query, jurisdiction?, date_start?, date_end?, limit?)` | Judilibre | Recherche la jurisprudence judiciaire |
| `get_decision(id)` | Judilibre | Lit le texte intégral et les métadonnées d'une décision |

Tous les outils sont annotés en lecture seule. Les outils de lecture indiquent
`metadata.verified: true` uniquement après une réponse de la source officielle.
Une erreur d'authentification, de réseau ou de schéma devient une erreur MCP
« source officielle non vérifiée » ; elle ne produit pas de résultat de
substitution présenté comme officiel.

## Installation locale

Prérequis : Python 3.10+ pour le serveur MCP. Le CLI historique reste compatible
avec Python 3.8+ et ne dépend pas du SDK MCP.

```bash
python -m pip install -r requirements-mcp.txt
```

La commande installe le SDK dans l'interpréteur `python` que `.mcp.json`
lancera. Si un environnement virtuel est préféré, il faut l'activer avant
l'installation et avant le démarrage de l'hôte du plugin.

Configurer ensuite les variables décrites dans
[`skill/scripts/.env.example`](../skill/scripts/.env.example). Le serveur
charge, sans écrasement, le premier fichier disponible parmi le chemin
`LEGIFRANCE_DOTENV`, `./.env` et `skill/scripts/.env`.

```text
LEGIFRANCE_CLIENT_ID=…
LEGIFRANCE_CLIENT_SECRET=…
JUDILIBRE_KEY_ID=…
LEGIFRANCE_ENV=prod
JUDILIBRE_ENV=prod
```

Les valeurs restent locales. `.env` est ignoré par Git et `.mcp.json` ne
contient aucun secret.

## Lancement

Le plugin local utilise le transport stdio déclaré dans `.mcp.json` :

```bash
python mcp_server/server.py
```

Pour tester le transport attendu par une connexion ChatGPT distante :

```bash
python mcp_server/server.py --transport streamable-http
```

Le point d'entrée est alors `http://127.0.0.1:8000/mcp`. Un raccordement réel
à ChatGPT nécessite ensuite un déploiement HTTPS public de ce même endpoint et
la configuration de l'authentification adaptée au canal retenu. Cette étape de
distribution n'est pas incluse dans la phase actuelle. Pour un hébergeur, le
serveur accepte `MCP_HOST` (par exemple `0.0.0.0`) et `PORT` ou `MCP_PORT`.

## Vérification

```bash
python -m unittest discover -s tests -v
python tests/check_plugin.py
python tests/check_links.py
python tests/check_commands.py
python tests/run_eval.py
```

Les tests MCP utilisent des réponses API simulées : ils ne consomment aucune
clé et ne dépendent pas de la disponibilité de PISTE.
