# Arborescence et maintenance du dépôt

Relevé le 25/10/2026 sur `main` (`git ls-files`). Les dossiers de tests,
de documentation et de déclinaisons ne sont pas détaillés.

```text
droit-francais-skill/
├── .agents/plugins/marketplace.json  ← marketplace native Codex
├── .claude-plugin/
│   ├── plugin.json                   ← manifeste du plugin Claude Code
│   └── marketplace.json              ← distribution directe depuis le dépôt
├── .codex-plugin/plugin.json         ← manifeste du plugin OpenAI
├── .mcp.json                         ← connexion au service MCP distant
├── assets/                           ← logo de distribution
├── mcp_server/
│   ├── server.py                     ← outils MCP stdio ou HTTP /mcp
│   ├── catalog.py                    ← liste des outils publiés (source unique)
│   ├── auth.py                       ← vérification des jetons OAuth
│   ├── runtime.py                    ← configuration et garde-fous du serveur
│   └── skills.py                     ← catalogue de compétences (extension Skills), non exposé
├── skills/recherche-juridique/SKILL.md ← adaptateur plugin vers le noyau
├── skill/                            ← paquet autonome et source de vérité
│   ├── SKILL.md                      ← noyau méthodologique
│   ├── CHANGELOG.md                  ← historique des versions
│   ├── profils/                      ← profils métier et gabarit _modele.md
│   ├── references/                   ← modules, gabarits, modes d'erreur, vigueur…
│   └── scripts/
│       ├── legifrance.py             ← CLI Légifrance + Judilibre (via PISTE)
│       ├── update_skill.py           ← mise à jour automatique facultative
│       ├── droit_francais/           ← bibliothèque partagée avec le serveur
│       ├── .env.example              ← gabarit de configuration
│       └── README.md                 ← configuration PISTE et usage
├── docs/                             ← guides, conformité, exploitation
├── tests/                            ← contrôles statiques, tests, évaluations
├── gemini_skill/, gemini_agent/      ← déclinaisons Gemini
├── grok_skill/, vibe_skill/, manus_skill/ ← déclinaisons Grok, Vibe, Manus
├── vault/                            ← notes Obsidian (hors paquet)
├── chatgpt-app-submission.json       ← métadonnées de soumission ChatGPT
├── Dockerfile                        ← image du serveur MCP
├── requirements-*.txt                ← dépendances serveur, banc, audit
├── README.md, README.en.md
└── LICENSE
```

Le fichier `profil.md`, copié depuis `skill/profils/` par l'utilisateur, est
local et ignoré par Git.

## Maintenance

- Revue annuelle recommandée le **1er septembre** (rentrée juridique) :
  procédure dans [`skill/references/maintenance.md`](../skill/references/maintenance.md).
- À chaque release : mettre à jour `README.md` et sa traduction complète
  `README.en.md`, ce relevé d'arborescence et `skill/CHANGELOG.md` (entrée
  Ajouté/Modifié/Conservé) avant de pousser le tag. Le tag porte le préfixe de
  sa série : `skill-v*` (méthodologie) ou `plugin-v*` (empaquetage OpenAI et
  Claude Code, dont les notes de soumission ChatGPT référencent le tag).
- La parité des deux README est contrôlée par `tests/check_readme_parity.py`.
