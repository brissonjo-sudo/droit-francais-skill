# `tests/` — évaluation du skill

Deux jeux complémentaires.

## 1. `eval-modes-erreur.csv` — éval mappée sur les 14 modes d'erreur

Une sonde **par mode d'erreur** du §1 du SKILL (1 à 14), plus des contrôles
transverses :

- **P** — règle de provenance (un identifiant non récupéré n'est jamais inventé) ;
- **L** — voie rapide `[lookup]` (sortie minimale, sans en-tête ni encart) ;
- **Bc / Be / Bs / Bo** — comportement des balises `[complet]` / `[express]` /
  `[syllogisme]` / `[opérationnel]` (ajoutées en v2.4.0).

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
- **Heuristiques regex indicatives** : un échec regex signale une sonde à
  revoir manuellement, pas nécessairement un défaut du skill. `--judge` réduit
  ce bruit mais dépend du jugement d'un modèle (non déterministe).

## 2. `evaluation-copilot-studio.csv` — jeu fonctionnel Copilot Studio

Questions de bout en bout (fond + forme) pour une évaluation qualitative
manuelle dans Copilot Studio (correspondance de mots-clés, comparaison de
signification, qualité générale). Inclut une sonde d'hallucination
(article `L. 9999-1` inexistant).

---

Voir aussi la **revue annuelle** (`skill/references/maintenance.md` §7), qui
fait tourner trois requêtes témoins après chaque mise à jour méthodologique.
