# `tests/` — évaluation du skill

Deux jeux complémentaires.

## 1. `eval-modes-erreur.csv` — éval mappée sur les 14 modes d'erreur

Une sonde **par mode d'erreur** du §1 du SKILL (1 à 14), plus deux contrôles
transverses introduits en v2.3.0 :

- **P** — règle de provenance (un identifiant non récupéré n'est jamais inventé) ;
- **L** — voie rapide `[lookup]` (sortie minimale, sans en-tête ni encart).

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
```

Heuristique de réussite par sonde :

```
PASS ⇔ (motifs attendus vides OU un attendu présent)
       ET (motifs interdits vides OU aucun interdit présent)
```

Le harnais (`run_eval.py`) n'a **aucune dépendance externe** (urllib + csv de
la bibliothèque standard). Les heuristiques regex sont volontairement
indicatives : un échec signale une sonde à revoir manuellement, pas
nécessairement un défaut du skill.

## 2. `evaluation-copilot-studio.csv` — jeu fonctionnel Copilot Studio

Questions de bout en bout (fond + forme) pour une évaluation qualitative
manuelle dans Copilot Studio (correspondance de mots-clés, comparaison de
signification, qualité générale). Inclut une sonde d'hallucination
(article `L. 9999-1` inexistant).

---

Voir aussi la **revue annuelle** (`skill/references/maintenance.md` §7), qui
fait tourner trois requêtes témoins après chaque mise à jour méthodologique.
