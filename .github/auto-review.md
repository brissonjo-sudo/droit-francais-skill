# Règles de relecture du dépôt

Ce dépôt distribue un skill de méthodologie de recherche en droit français,
sous trois formes qui partagent le même cœur méthodologique : skill Claude
Code autonome, plugin Claude Code, plugin OpenAI. Un serveur MCP
(`mcp_server/`) expose les outils de récupération de sources primaires
(Légifrance, Judilibre) et gère l'authentification OAuth.

## À vérifier en priorité

- **Aucune référence juridique inventée dans le diff lui-même.** Un numéro
  d'article, un numéro de pourvoi, une date d'arrêt ajoutés dans la prose du
  dépôt (README, docs/, skill/, vault/) doivent soit citer leur source
  primaire (Légifrance, Judilibre), soit être explicitement marqués comme non
  vérifiés. C'est le risque que ce projet existe pour combattre : une
  référence plausible mais fausse est le mode d'échec central documenté dans
  `docs/article.md`.
- **Deux séries de version indépendantes ne doivent jamais être confondues** :
  le skill est en `2.x`/`3.x` (voir `skill/SKILL.md`, `skill/CHANGELOG.md`),
  le plugin est en `0.x` (voir `.claude-plugin/plugin.json`). Un changement de
  l'un ne doit pas être répercuté sur l'autre par erreur. `tests/check_affirmations.py`
  vérifie déjà mécaniquement que les versions citées en prose correspondent au
  code ; ne refais pas ce contrôle, mais signale un cas qu'il ne peut pas voir
  (une affirmation nouvelle sur une version, hors du motif qu'il reconnaît).
- **L'émetteur OAuth (`issuer`) ne doit jamais être normalisé.** Une barre
  oblique finale ajoutée ou retirée sur `MCP_OAUTH_ISSUER` ou dans
  `mcp_server/auth.py` casse la vérification de jeton en silence : c'est un
  point de rupture historique documenté dans `.github/workflows/ci.yml`.
  Toute modification de la comparaison d'émetteur est un problème grave, pas
  un style.
- **Cohérence entre le manifeste du plugin et le serveur.** `SERVER_VERSION`
  dans `mcp_server/server.py`, la version dans `.claude-plugin/plugin.json`
  et celle citée dans `chatgpt-app-submission.json` doivent avancer ensemble ;
  `tests/check_plugin.py` le vérifie mécaniquement, un diff qui touche l'un
  sans les autres mérite une question, pas un constat certain.
- **`skill/profils/`** encode le métier de l'utilisateur (contexte
  territorial, domaines prioritaires) ; une modification y est distincte
  d'une modification du noyau méthodologique dans `skill/SKILL.md`. Ne pas
  confondre les deux dans un même constat.

## À ne pas signaler

- Le style d'écriture de la méthodologie juridique, sauf s'il introduit une
  ambiguïté sur une règle de provenance ou de citation.
- Les contrôles déjà mécaniques de la CI (`check_links.py`,
  `check_affirmations.py`, `check_commands.py`, `check_plugin.py`,
  `run_eval.py`, l'audit de dépendances, le scan Trivy) : ils s'exécutent sur
  chaque PR et rendent leur propre verdict.
