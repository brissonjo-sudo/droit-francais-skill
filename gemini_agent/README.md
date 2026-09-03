# Agent juridique — déclinaison Gemini

Déclinaison **Gemini** (Google `google-genai`) de la méthodologie de recherche
juridique portée par ce dépôt. Contrairement au skill Claude
([`skill/`](../skill)), spécifique au droit français et déjà connecté à
Légifrance/Judilibre, cet agent est **générique** (toute juridiction, toute
branche du droit) et livré **non connecté** : un squelette à brancher sur vos
propres API de recherche documentaire et de jurisprudence.

## Architecture

```
gemini_agent/
├── __init__.py             # marqueur de package
├── legal_agent_config.py   # config de l'agent : modèle, température, prompt, outils
├── tools.py                # squelette des outils (tool calling), non connecté
└── README.md                # ce document
```

Deux fichiers séparés, deux responsabilités :

- **`legal_agent_config.py`** décrit *comment* l'agent doit se comporter :
  quel modèle, avec quelle température, quel system prompt, et quels outils
  il a le droit d'appeler. C'est la seule source de vérité sur la
  configuration — ne dupliquez pas ces valeurs ailleurs.
- **`tools.py`** décrit *ce que* l'agent peut faire : les fonctions
  effectivement exécutées quand le modèle demande un appel d'outil.

Cette séparation permet de faire évoluer les deux indépendamment : changer de
fournisseur de données juridiques ne touche que `tools.py`, changer de modèle
ou de prompt ne touche que `legal_agent_config.py`.

## Le system prompt

Le prompt (`SYSTEM_PROMPT` dans `legal_agent_config.py`) fixe un cadre
non négociable, appliqué à chaque réponse :

1. **Recours aux outils obligatoire** — l'agent ne doit jamais répondre sur le
   droit positif à partir de ses seules données d'entraînement, qui peuvent
   être obsolètes ou fausses. Il doit systématiquement appeler ses outils de
   recherche avant de conclure.
2. **Rigueur des sources** — aucune référence approximative : texte exact,
   numéro d'article, référence de jurisprudence exacte.
3. **Hiérarchie des normes** — vérifier qu'un texte n'est pas neutralisé par
   une norme supérieure avant de le présenter comme applicable.
4. **Neutralité** — ton objectif et analytique, sans prise de position.

Il impose aussi un **format de sortie Markdown fixe** en cinq étapes
(qualification des faits, textes applicables, jurisprudence, syllogisme
juridique, limites et risques), pour que chaque réponse reste comparable et
auditable d'un cas à l'autre.

La **température est figée à `0.0`** : sur un usage juridique, la
reproductibilité d'une réponse prime sur la variété des formulations. Ce
n'est pas un réglage cosmétique — ne l'augmentez pas sans en mesurer l'effet
sur la stabilité des citations.

## L'obligation d'utiliser les outils

Un system prompt seul ne force rien : un modèle peut l'ignorer si rien ne
l'y contraint techniquement. Deux garde-fous complémentaires sont donc à
prévoir côté intégration, en plus du prompt :

- **Déclarer les outils dans la config d'appel** (déjà fait par
  `LegalAgentConfig.generation_config()`, via le paramètre `tools`), pour que
  le modèle sache qu'ils existent et puisse les invoquer.
- **Vérifier, côté application, qu'un appel d'outil a bien eu lieu** avant
  d'accepter une réponse qui cite un texte de loi ou une décision. Un moyen
  simple : inspecter l'historique du chat (`chat.get_history()`) et rejeter
  ou renvoyer en correction toute réponse contenant une référence
  (article, n° de pourvoi) qui n'apparaît dans aucun résultat d'outil.

Le prompt seul reste la première ligne de défense ; la vérification
applicative est ce qui rend l'obligation réellement contraignante.

## Intégrer vos propres API dans `tools.py`

`search_legal_database` et `search_case_law` sont des squelettes : signature
typée, docstring détaillée, corps réduit à un mock (`connected: False`, liste
de résultats vide). Le SDK `google-genai` lit la signature et la docstring
pour générer la déclaration de fonction envoyée au modèle — **toute
modification de signature doit rester documentée dans la docstring**, sous
peine de désynchroniser ce que le modèle croit pouvoir demander de ce que la
fonction accepte réellement.

Pour connecter une vraie source :

1. Remplacez le corps de la fonction par un appel HTTP vers votre API
   (Légifrance/PISTE, Judilibre, ou toute base équivalente pour une autre
   juridiction). Voir [`skill/scripts/droit_francais/`](../skill/scripts/droit_francais)
   pour un exemple de client déjà opérationnel sur Légifrance/Judilibre côté
   Claude, transposable ici sans dépendre du reste du skill.
2. Conservez la forme du dictionnaire retourné (`query`, `results`,
   `connected`) ou adaptez-la, mais mettez à jour la docstring en
   conséquence — c'est elle que le modèle « lit » pour savoir quoi attendre.
3. Gérez les erreurs (API indisponible, requête invalide) en renvoyant un
   dictionnaire explicite plutôt qu'en laissant remonter une exception brute :
   l'agent doit pouvoir signaler à l'utilisateur qu'une vérification a
   échoué, jamais la passer sous silence.
4. Ne stockez aucune clé d'API en dur dans `tools.py` : passez-la par variable
   d'environnement, comme `GEMINI_API_KEY` l'est déjà pour le client Gemini
   dans `legal_agent_config.build_client`.

## Utilisation

```python
from gemini_agent.legal_agent_config import LegalAgentConfig, build_client, build_chat

client = build_client()  # lit GEMINI_API_KEY dans l'environnement
chat = build_chat(client, LegalAgentConfig())

response = chat.send_message("Un salarié peut-il être licencié pendant un arrêt maladie ?")
print(response.text)
```

## Dépendance

```
pip install google-genai
```

Ce package n'introduit aucune dépendance vers le reste du dépôt : il peut
être extrait tel quel dans un autre projet.
