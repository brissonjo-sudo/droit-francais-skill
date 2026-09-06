# `tests/` — évaluation du skill

Deux jeux d'éval complémentaires, des tests unitaires hors réseau, quatre
**contrôles statiques** et des vérifications de déploiement exécutés en CI.

## 1. `eval-modes-erreur.csv` — éval mappée sur les 18 modes d'erreur

Une sonde **par mode d'erreur** du §1 du SKILL (1 à 18), plus des contrôles
transverses :

- **P** — règle de provenance (un identifiant non récupéré n'est jamais inventé) ;
- **L** — voie rapide `[lookup]` (sortie minimale, sans en-tête ni encart) ;
- **Bc / Be / Bs / Bo** — comportement des balises `[complet]` / `[express]` /
  `[syllogisme]` / `[opérationnel]` (ajoutées en v2.4.0) ;
- **N** — profil neutre (v3.0.0) : sans `profil.md`, le skill ne présume aucun
  contexte territorial et pose la question (étape 0 bis) — garde-fou
  anti-régression contre l'ancien contexte codé en dur.

Colonnes : `Mode`, `Intitule`, `Question sonde`, `Comportement attendu`,
`Motifs attendus` (regex, alternation `a|b|c` — une branche suffit),
`Motifs interdits` (regex — aucune occurrence tolérée).

### Lancer l'éval

```bash
# Check-list hors-ligne (aucun appel modèle) — éval manuelle reproductible
python tests/run_eval.py

# Éval réelle via l'API Anthropic (SKILL.md servi en prompt système)
export ANTHROPIC_API_KEY="sk-…"
python tests/run_eval.py --live

# Sous-ensemble de modes
python tests/run_eval.py --live --only 1,5,P

# Verdict par LLM-juge (plus robuste que les regex)
export ANTHROPIC_JUDGE_MODEL="claude-opus-4-8"   # optionnel
python tests/run_eval.py --live --judge
```

Heuristique de réussite par sonde (mode regex, défaut) :

```
PASS ⇔ (motifs attendus vides OU un attendu présent)
       ET (motifs interdits vides OU aucun interdit présent)
```

Avec `--judge`, un **second modèle** note la réponse contre le « Comportement
attendu » et rend un verdict PASS/FAIL sur le fond — cela corrige les **faux
positifs** des regex (le bon mot-clé dans une réponse pourtant fausse).

Le harnais (`run_eval.py`) n'a **aucune dépendance externe** (urllib + csv de
la bibliothèque standard).

### Limites du harnais (à connaître avant d'interpréter un résultat)

- **Le modèle est appelé sans outils.** `--live` envoie `SKILL.md` en système
  et la sonde en message, mais **ne fournit aucun outil** au modèle : il ne
  peut ni exécuter `legifrance.py` ni appeler `web_fetch`. Les sondes de
  provenance (`P`) et d'hallucination (`1`) mesurent donc l'**instinct de
  refus** du modèle, pas la boucle outillée réelle. En production (Claude
  Code), le skill dispose des outils : le comportement peut différer. Une
  validation fidèle de la provenance demanderait un harnais *agentic* (avec
  outils), non couvert ici.
- **Les motifs interdits `LEGIARTI[0-9]{6}` (sondes `1` et `P`) ne valent que
  sans outils.** Sans outil, produire un identifiant officiel ne peut être
  qu'une invention, donc l'interdire est correct. Avec les outils, un
  identifiant **récupéré** est au contraire le comportement attendu : le même
  critère produirait un faux négatif. Ne pas transposer ces interdits à un
  harnais outillé — la provenance s'y juge sur la trace d'appels (l'identifiant
  cité figure-t-il dans un résultat d'outil de la session ?), pas sur son
  absence.
- **Heuristiques regex indicatives** : un échec regex signale une sonde à
  revoir manuellement, pas nécessairement un défaut du skill. `--judge` réduit
  ce bruit mais dépend du jugement d'un modèle (non déterministe).

## 1 bis. `run_bench.py` — benchmark agentique (avec outils)

Ce que la section précédente ne peut pas mesurer. `run_eval.py` appelle le
modèle **sans outils** ; la promesse centrale du skill — « aucune référence ne
se produit de mémoire » — ne se vérifie qu'avec les outils branchés, en
regardant si l'identifiant cité provient réellement d'un appel.

Le harnais pilote la **vraie CLI en headless** (`claude -p --output-format
stream-json`), pas une boucle d'API reconstituée : ce qui est mesuré est la
méthodologie telle qu'elle s'applique dans la chaîne d'outils distribuée.

### Trois bras, un seul corpus

| Bras | Prompt système | Outils | Ce qu'il mesure |
|---|---|---|---|
| **A** | neutre | aucun | témoin — ce que le modèle fait sans la méthode |
| **B** | `skill/SKILL.md` | aucun | la méthode seule |
| **C** | `skill/SKILL.md` | connecteur MCP | la production |

Les trois bras sont isolés par `--tools ""` (désactive les outils intégrés,
sans quoi le « sans outils » n'en est pas un) et `--setting-sources ""` (sans
quoi le skill installé sur le poste contaminerait le bras A).

### Deux sources de verdict, non substituables

**Contrôles déterministes sur la trace**, dans `bench/verdicts.py` :

| Contrôle | Question |
|---|---|
| `provenance` | tout identifiant cité figure-t-il dans un résultat d'outil antérieur ? |
| `outils_attendus` | l'outil que la sonde attend a-t-il été appelé ? |
| `appels_interdits` | un outil hors périmètre a-t-il été appelé ? |
| `plafond` | le nombre d'appels reste-t-il borné ? |
| `date` | la date de référence a-t-elle été passée à l'outil ? |
| `secrets` | une valeur secrète fuit-elle dans la trace persistée ? |

**Juge-modèle** sur la réponse augmentée du résumé de trace. Un cas passe si
les deux concluent au succès : **un juge indulgent ne peut pas à lui seul
faire réussir une sonde.**

Trois précautions rendent le contrôle de provenance juste : un identifiant
déjà présent dans la question n'est pas une invention ; un identifiant marqué
« non vérifié » est toléré (le noyau autorise ce marquage) ; un identifiant
trouvé dans les *arguments* d'un appel ne prouve rien — une référence inventée
puis soumise à `get_article` y figurerait et se validerait elle-même.

### Commandes

```bash
python tests/run_bench.py --verifier-corpus          # hors réseau, joué en CI
python tests/run_bench.py --only L-1 --bras C --sans-juge --garder-flux
python tests/run_bench.py --bras A,B,C --repeats 3 --sortie bench/runs/x.jsonl
python tests/run_bench.py --reprendre bench/runs/x.jsonl
python tests/bench/resume.py bench/runs/x.jsonl --baseline bench/baselines/…
```

### Où mettre les identifiants

| Famille | Fichier | Utilité |
|---|---|---|
| Auth0 du connecteur MCP (`AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET`) | **`.env`** à la racine (modèle : `.env.example`) | bras C |
| Clés PISTE (`LEGIFRANCE_*`, `JUDILIBRE_KEY_ID`) | **`skill/scripts/.env`** (modèle voisin) | uniquement `--mcp-local` |
| Jeton de la CLI Claude | **aucun fichier** — `claude setup-token`, ou secret GitHub `CLAUDE_CODE_OAUTH_TOKEN` pour la CI | tous les bras |

Les deux `.env` sont ignorés par Git (`.env`, `.env.*`, seuls les
`.env.example` sont suivis). Une variable **déjà exportée** garde la priorité
sur le fichier : en CI, rien n'est lu sur disque, les secrets viennent du
coffre.

En mode par défaut, les clés PISTE ne sont pas nécessaires en local — c'est le
serveur de production qui les détient. Le jeton obtenu par échange Auth0 n'est
ni écrit sur disque, ni passé en ligne de commande.

### Limites (à connaître avant d'interpréter un résultat)

- **Non-déterminisme.** Un même cas peut basculer d'un run à l'autre. Les
  baselines se font à `--repeats 3` ; une baisse d'un seul cas-équivalent par
  mode est traitée comme de la variance, pas comme une régression.
- **Le juge est un modèle.** Son champ `extrait` cite la phrase qui fonde son
  verdict, précisément pour qu'un relecteur humain puisse le contredire. Un
  échantillon des verdicts doit être relu à chaque baseline.
- **La métrique de falsification est un proxy.** Elle constate qu'une
  recherche distincte a suivi la première lecture aboutie — donc *la recherche
  de réfutation*, pas sa pertinence. Le juge apprécie le reste.
- **La surface mesurée n'est pas exactement la surface distribuée.** Le skill
  est injecté en prompt système et le connecteur MCP est joint en HTTP ; le
  plugin installé, lui, lance le serveur en stdio. L'écart porte sur le
  transport, pas sur la méthode.
- **Les pannes ne sont pas des échecs.** Instance endormie, jeton expiré,
  quota atteint : classés `infra_error`, exclus des taux, rejouables par
  `--reprendre`. Les compter comme des échecs ferait baisser un score pour des
  raisons étrangères à ce qu'on mesure.

Le corpus (`bench-cases.csv`) porte une colonne **`Valide par`** : par défaut,
seules les sondes dont le fond juridique a été relu par un humain sont jouées.
Une baseline construite sur des attentes non validées mesurerait le skill
contre une erreur.

## 2. `evaluation-copilot-studio.csv` — jeu fonctionnel Copilot Studio

Questions de bout en bout (fond + forme) pour une évaluation qualitative
manuelle dans Copilot Studio (correspondance de mots-clés, comparaison de
signification, qualité générale). Inclut une sonde d'hallucination
(article `L. 9999-1` inexistant).

## 3. Tests unitaires de l'outillage

`test_tools.py` vérifie sans réseau et sans clé PISTE :

- la sélection des environnements Légifrance et Judilibre ;
- la priorité des variables exportées sur le fichier `.env` ;
- le transport JSON et la traduction des erreurs HTTP ;
- OAuth2 Légifrance et la construction des requêtes JSON authentifiées ;
- le cache et la bascule `KeyId` vers OAuth2 de Judilibre ;
- la conservation des huit sous-commandes publiques du CLI.

```bash
python tests/test_tools.py
```

`test_mcp_app.py` couvre le contrat des six outils, le masquage des secrets,
les limites de capacité, la configuration de production, les annotations et
une session MCP `stdio` réelle. `test_deployment.py` contrôle le paquet Docker
sans lancer de conteneur.

`test_auth.py` vérifie le vérificateur de jetons isolément, ainsi que
l'écriture canonique de l'émetteur publiée par les deux routes de métadonnées.

`test_oauth_end_to_end.py` exerce la **chaîne complète** en processus :
application ASGI construite par le SDK, middleware d'authentification,
transport Streamable HTTP, dispatch d'outil. Seuls le JWKS de l'émetteur —
remplacé par une clé RSA engendrée à la volée — et les appels aux API
juridiques sont simulés. Sont couverts : le refus anonyme et son challenge,
le jeton valide menant à un appel d'outil réussi, les refus pour audience,
émetteur, expiration, signature et sujet manquant, le quota isolé par sujet,
et le comportement du contrôle de portée dans ses deux réglages. Aucun secret
n'est lu, aucun jeton réel n'est nécessaire.

Le CI démarre en plus le serveur Streamable HTTP, vérifie `/health`, initialise
une vraie session sur `/mcp`, découvre les six outils, puis construit l'image
Docker. La même sonde HTTP peut viser un déploiement de test :

```bash
python tests/check_mcp_http.py https://domaine.example/mcp
```

`check_oauth_metadata.py` contrôle le point dont dépend l'acceptation du
connecteur ChatGPT : les deux routes RFC 9728 doivent annoncer l'émetteur
**exactement** tel qu'il est configuré, sans normalisation de la barre oblique
finale, et une requête anonyme doit être refusée en `401` avec un challenge
renvoyant vers la bonne route. Aucun jeton n'est présenté, aucun secret n'est
lu. La CI l'exécute sur les deux écritures avec un émetteur factice ; la même
sonde vise la production, l'émetteur attendu étant alors lu dans le document
de découverte :

```bash
python tests/check_oauth_metadata.py https://domaine.example --discover
```

`check_live_tools.py` valide les **six outils contre le service déployé**, avec
un vrai jeton : découverte et annotations, appel effectif de chacun des six,
latence des premiers appels Légifrance et Judilibre, lectures avec texte,
datation, provenance, parcours `search → fetch` et article inexistant. Lorsque
les valeurs des clés fournisseur existent localement, la sonde vérifie aussi
qu'elles ne sont pas renvoyées ; sinon elle avertit explicitement que cette
comparaison n'a pas pu être faite. Le jeton est lu dans `MCP_ACCESS_TOKEN` —
jamais en argument — et n'est ni affiché ni écrit.

```bash
export MCP_ACCESS_TOKEN="…"
python tests/check_live_tools.py
```

Sans jeton local, le workflow manuel **Sonde fonctionnelle**
(`.github/workflows/sonde-fonctionnelle.yml`) exécute le même parcours depuis
GitHub. Il ne stocke pas de jeton — un jeton expire, les identifiants non : les
secrets de dépôt `AUTH0_CLIENT_ID` et `AUTH0_CLIENT_SECRET` sont échangés contre
un jeton neuf à chaque exécution. Il n'est pas planifié : chaque exécution
consomme le quota PISTE.

`check_service_health.py` est la sonde d'**exploitation courante** : latence
de `/health`, version et mode d'authentification annoncés, plus les contrôles
de métadonnées rejoués. Elle n'appelle aucun outil, donc ne consomme aucun
quota, et n'exige aucun jeton. Sa sortie `--json` tient sur une ligne, faite
pour être accumulée — une dérive de latence ne se voit que sur une série.

```bash
python tests/check_service_health.py
python tests/check_service_health.py --json >> surveillance.jsonl
```

`summarize_surveillance.py` résume une telle série (défauts, latence médiane
et p95, réveils d'instance, ventilation par jour) ; `--jours N` borne la
fenêtre, `--exiger-sans-defaut` rend 1 si sa couverture est insuffisante ou si
elle porte un défaut, une dérive du p95 à chaud ou un réveil grave. Le workflow
`surveillance.yml` alimente le journal une fois par heure sur la branche
`surveillance` — voir
`docs/exploitation.md`.

```bash
git show origin/surveillance:surveillance.jsonl | python tests/summarize_surveillance.py - --jours 7
```

Cette sonde n'est **pas** jouée en CI : elle exige un jeton et consomme le
quota PISTE du titulaire. Elle sert la validation de bout en bout décrite dans
[`docs/validation-chatgpt.md`](../docs/validation-chatgpt.md).

## 4. Contrôles statiques (CI)

Quatre vérificateurs statiques sans dépendance externe, exécutés à chaque push
et chaque PR par `.github/workflows/ci.yml`, aux côtés des sondes HTTP
`check_mcp_http.py` et `check_oauth_metadata.py`. Ils ne jugent pas le skill : ils empêchent
le dépôt de se contredire lui-même.

```bash
python tests/check_links.py         # liens Markdown relatifs
python tests/check_commands.py      # sous-commandes doc ↔ CLI
python tests/check_affirmations.py  # affirmations de la doc ↔ code
python tests/check_plugin.py        # manifeste et adaptateur plugin
python tests/check_vault.py         # maillage du vault (vue graphe)
```

**`check_links.py`** — vérifie que chaque lien relatif Markdown (`[libellé]`
suivi de `(chemin)`) des `.md` pointe vers un fichier existant. Hors
`vault/`, qui utilise des wikilinks Obsidian non résolus en chemins.

**`check_vault.py`** — prend en charge ce que `check_links.py` laisse de côté :
le maillage de wikiliens du vault, lu par la vue graphe. Quatre invariants —
section `## Liens (maillage Graphify)` sur chaque note, aucune note orpheline
(sans lien entrant), aucun cul-de-sac (sans lien sortant), aucun lien non
résolu. Un auto-lien ne rend pas une note atteignable et ne compte pas comme
lien entrant ; un wikilien écrit en `code` n'est pas un lien, Obsidian ne
l'interprétant pas.

La tolérance aux liens non résolus **n'est pas une liste dans le
vérificateur** : elle est dérivée de la section « Fichiers supprimés (remplacés
par agrégats) » de `index-recherche-juridique.md`, où ces notions sont écrites
en `code`. Déclarer une notion agrégée dans l'index suffit à la faire accepter ;
l'oublier fait échouer le contrôle. `tests/test_check_vault.py` éprouve chaque
invariant sur un vault de test qui le viole — un vérificateur qui passe toujours
ne vérifie rien.

Il vise une dérive constatée le 5 septembre 2026 : deux notes sur treize
portaient une section de liens, trois agrégats n'avaient aucun lien sortant, et
deux notes de version aucun lien entrant. Une note isolée existe mais aucun
chemin de lecture n'y mène.

**`check_commands.py`** — compare les sous-commandes citées dans la
documentation à celles réellement exposées par `build_parser()` de
`legifrance.py`, dans les deux sens : commande **citée mais inexistante**, et
commande **exposée mais jamais documentée**. La liste de référence est
extraite du parser par introspection argparse, jamais par regex sur le source
— sans quoi elle divergerait à son tour. Le balayage ne lit que le contexte
de code (blocs clôturés et spans `` `…` ``), la prose étant hors champ.

Exclusions : `vault/` (notes historiques) et `skill/CHANGELOG.md` (journal
immuable, qui cite légitimement des commandes retirées depuis).

**`check_affirmations.py`** — même principe que `check_commands.py`, appliqué
aux affirmations chiffrées de la prose. Il confronte au code, qui fait foi :
les versions de plugin citées (`v0.x.y`), les valeurs d'annotations d'outils
citées (`openWorldHint`, `readOnlyHint`, `destructiveHint`) et les variables
d'environnement `MCP_*` mentionnées. Il vérifie aussi que le dossier de
soumission annonce les mêmes annotations que le serveur.

Il vise une classe d'erreur constatée trois fois lors de l'audit du 1er
septembre 2026 : *un document affirme une propriété que le code contredit*,
chaque affirmation restant plausible isolément faute de recoupement. Le
contrôle se déclenche dans les deux sens — documentation périmée comme dérive
du serveur.

Exclusion : `docs/roadmap-chatgpt-plugin.md`, journal daté qui doit pouvoir
citer une valeur d'époque. Une entrée devenue fausse y reçoit une mention de
péremption, à la main — même logique que `skill/CHANGELOG.md` ci-dessus.

**`check_plugin.py`** — vérifie le manifeste, son identité, son interface, le
point de découverte `skills/recherche-juridique/` et la présence intacte du
skill historique `skill/SKILL.md`. Il interdit aussi de déclarer une app ou un
serveur MCP sans fichier compagnon.

Il applique en outre les **limites publiées par OpenAI** pour la soumission —
longueurs de champs, liste des catégories, nombre et longueur des prompts et
des capacités, quatre URL publiques, notes de version, justification par
annotation — et la règle de version retenue : *le manifeste du plugin suit le
serveur MCP*, le skill gardant sa propre ligne éditoriale.

Enfin, il **valide `chatgpt-app-submission.json` contre le schéma officiel**,
dont une copie est embarquée dans `fixtures/`. Cette validation est facultative :
elle demande `jsonschema`, qui arrive avec le SDK MCP. Quand il manque, son
absence est dite explicitement — un contrôle muet se lit à tort comme un
contrôle réussi. Rafraîchir la copie depuis l'URL déclarée lors des revues.

> **Pourquoi cette validation existe.** Le fichier déclarait une URL de schéma
> obsolète (`apps-sdk` au lieu de `plugins`) et **échouait à la validation
> officielle**. Le défaut n'a été vu qu'en téléchargeant le schéma à la main,
> une fois. Rien, dans le dépôt, ne l'aurait signalé.

> **Pourquoi ce contrôle existe.** La v3.1.0 a dû réparer la suppression
> accidentelle de `ceta` et `constit` par une PR qui n'avait touché **aucun**
> `.md` : pendant ce temps, quatre fichiers prescrivaient au modèle des
> commandes inexistantes, et deux commandes ajoutées (`decision`, `taxonomy`)
> n'étaient documentées nulle part, donc inutilisables. Aucun contrôle
> existant ne pouvait le voir. Un garde-fou dont on a oublié le motif finit
> désactivé : voilà le motif.

---

Voir aussi la **revue annuelle** (`skill/references/maintenance.md` §7), qui
fait tourner quatre requêtes témoins après chaque mise à jour méthodologique.
