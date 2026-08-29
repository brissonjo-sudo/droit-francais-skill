# Architecture plugin — audit et trajectoire

Date de l'audit : **29 août 2026**

Branche d'implémentation : **`feat/plugin-foundation`**

## Décision

Le dépôt évolue selon une approche **skill-first, plugin-ready** :

- `skill/` reste la source de vérité et le paquet autonome historique ;
- le dépôt devient aussi un plugin OpenAI grâce à `.codex-plugin/plugin.json` ;
- `skills/recherche-juridique/` sert d'adaptateur de découverte, sans copie du noyau ;
- l'outillage API sera extrait progressivement avant d'être exposé par une app ou un serveur MCP.

Cette première étape ne modifie ni la méthode juridique, ni le CLI, ni les variables d'environnement existantes.

## Audit de l'existant

### Points solides

- Le noyau méthodologique est isolé dans `skill/SKILL.md`, avec références et profils dédiés.
- La règle de provenance interdit de produire des identifiants officiels non récupérés pendant la session.
- `skill/scripts/legifrance.py` couvre Légifrance et Judilibre en bibliothèque standard, avec configuration BYOK et dégradation vers le web.
- Les contrôles existants compilent le CLI, vérifient les liens, synchronisent documentation et commandes, puis exécutent 21 sondes hors ligne.
- Les secrets sont exclus du dépôt (`.env` ignoré) et aucune clé n'est embarquée.

### Couplages à réduire

- Le transport HTTP, l'authentification, la logique Légifrance, la logique Judilibre, le formatage et le CLI sont réunis dans un seul fichier.
- Le script est rangé dans le paquet du skill : il n'existe pas encore de bibliothèque réutilisable par une app.
- Le dépôt ne possédait ni manifeste de plugin, ni point de découverte `skills/`, ni contrôle de cohérence du paquet.
- L'installation documentée ciblait uniquement Claude Code.

### Risques d'une migration directe

- Déplacer `skill/` casserait le chemin d'installation autonome et les liens relatifs.
- Déplacer immédiatement `legifrance.py` casserait les commandes documentées et le contrôle `check_commands.py`.
- Déclarer `apps` ou `mcpServers` avant leur implémentation créerait un plugin invalide et laisserait croire que les API sont déjà appelables comme outils natifs.
- Copier le noyau sous `skills/` créerait deux sources de vérité susceptibles de diverger.

## Architecture cible

```text
droit-francais-skill/
├── .codex-plugin/
│   └── plugin.json                 # identité et capacités réellement livrées
├── skills/
│   └── recherche-juridique/
│       └── SKILL.md                # adaptateur vers le noyau historique
├── skill/                          # compatibilité autonome, source de vérité
│   ├── SKILL.md
│   ├── references/
│   ├── profils/
│   └── scripts/
│       └── legifrance.py           # à terme : façade CLI compatible
├── tools/                          # étape 2
│   └── droit_francais/
│       ├── config.py               # environnement et secrets
│       ├── transport.py            # HTTP, délais, erreurs
│       ├── legifrance.py            # client Légifrance
│       ├── judilibre.py             # client Judilibre
│       └── cli.py                  # commandes et rendu terminal
├── app/                            # étape 3
│   └── server.*                    # pont d'outils/app vers la bibliothèque
├── .mcp.json                       # seulement quand le serveur existe
├── .app.json                       # seulement quand l'app existe
└── tests/
    ├── check_plugin.py
    ├── check_commands.py
    ├── check_links.py
    └── run_eval.py
```

### Flux cible

```text
Utilisateur
    ↓
Plugin → skill recherche-juridique → méthode et règles de provenance
    ↓
App / outils MCP → bibliothèque tools/droit_francais
    ↓
API officielles Légifrance et Judilibre
```

Le skill décide **quand et comment rechercher**. La bibliothèque exécute les appels déterministes. L'app expose uniquement des opérations bornées et structurées au modèle.

## Migration progressive

### Étape 1 — socle plugin (implémentée)

- Ajouter un manifeste plugin minimal et valide.
- Ajouter un adaptateur natif sous `skills/` qui charge `skill/SKILL.md`.
- Ne déclarer ni app ni serveur MCP.
- Ajouter un contrôle CI des invariants de compatibilité.
- Documenter la trajectoire et les limites de cette version.

Critère de sortie : le validateur du plugin, le validateur du skill et tous les tests historiques passent sans modifier le noyau.

### Étape 2 — bibliothèque d'outils

- Extraire les fonctions de configuration, transport et clients API dans `tools/droit_francais/`.
- Conserver `skill/scripts/legifrance.py` comme façade compatible vers la nouvelle bibliothèque.
- Ajouter des tests unitaires avec réponses HTTP simulées, sans dépendance au réseau ni aux clés PISTE.
- Stabiliser des résultats structurés indépendants de l'affichage terminal.

Critère de sortie : toutes les commandes, codes de sortie et variables d'environnement documentés restent compatibles.

### Étape 3 — app / MCP

- Exposer des outils bornés : recherche d'article, lecture par identifiant, recherche et lecture de décision, taxonomie et diagnostic de connexion.
- Définir des schémas d'entrée/sortie stricts et préserver l'abstention en cas d'échec de récupération.
- Ajouter `.mcp.json` et/ou `.app.json` uniquement lorsque le serveur correspondant est exécutable et testé.
- Laisser les secrets dans l'environnement ou le mécanisme d'authentification de l'hôte ; ne jamais les placer dans le manifeste ou les réponses d'outil.

Critère de sortie : un test de bout en bout démontre qu'un identifiant cité provient de la réponse officielle renvoyée par l'outil.

### Étape 4 — distribution

- Ajouter les métadonnées visuelles et juridiques nécessaires à la distribution.
- Choisir le canal de publication et son mécanisme d'authentification.
- Tester l'installation, la mise à jour et la reprise dans une nouvelle conversation.

## Invariants de non-régression

1. `skill/SKILL.md` reste installable indépendamment du plugin.
2. Les chemins et commandes documentés de `skill/scripts/legifrance.py` restent valides jusqu'à une version majeure explicitement annoncée.
3. Une clé absente ne réduit jamais les exigences de provenance ; elle déclenche la voie de repli ou l'abstention.
4. Aucun identifiant officiel n'est présenté comme vérifié s'il ne provient pas d'une récupération effective.
5. Le manifeste ne déclare que les composants réellement présents et testés.
6. Le noyau juridique ne doit exister qu'en un seul exemplaire maintenu.

## Tests de l'étape 1

- validation officielle de `.codex-plugin/plugin.json` ;
- validation du frontmatter de `skills/recherche-juridique/SKILL.md` ;
- contrôle local `tests/check_plugin.py` ;
- compilation Python ;
- contrôle des liens et des commandes documentées ;
- évaluation hors ligne des 21 sondes existantes.
