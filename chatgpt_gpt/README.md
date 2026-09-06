# Skill juridique — déclinaison GPT personnalisé (ChatGPT)

Déclinaison **GPT personnalisé** (builder de GPT de ChatGPT) de la méthodologie
de recherche juridique portée par ce dépôt. Elle est distincte de l'**app
ChatGPT** documentée dans [`docs/chatgpt-submission.md`](../docs/chatgpt-submission.md) :
l'app est un connecteur MCP vers le serveur du dépôt, le GPT est un jeu
d'instructions et de fichiers de connaissances, sans serveur. Les deux peuvent
se combiner : si l'app est activée dans le GPT, elle devient sa première voie
de récupération.

État vérifié le 6 septembre 2026, sur la documentation OpenAI listée en fin
de document.

> **Condition d'accès.** La création et la publication d'un **nouveau** GPT ne
> sont **pas disponibles sur les comptes personnels** — Free, Go, Plus et Pro.
> Elles supposent un espace de travail **Business, Enterprise ou Edu**, et
> l'autorisation correspondante. Les GPT existants restent utilisables, et
> modifiables si l'offre et les permissions le permettent. La création se fait
> sur le web ; les applications mobiles ne la proposent pas.

## Ce qui la distingue du noyau

| Noyau (`skill/`) | Déclinaison GPT (`chatgpt_gpt/`) |
|---|---|
| `SKILL.md` de 47 000 caractères, chargé à la demande | Champ **Instructions** plafonné à **8 000 caractères** par le builder ; tout ce qui n'y tient pas passe en fichiers de connaissances |
| Connecteur MCP Légifrance/Judilibre | **App « Droit français »** si elle est activée dans le GPT (voie 1), sinon **recherche web** restreinte aux domaines officiels (voie 2) |
| `scripts/legifrance.py` (API PISTE) | Sans équivalent : un GPT n'exécute pas de script du dépôt |
| Neuf références lues par chemin relatif | **Huit** d'entre elles téléversées en fichiers **Knowledge**, consultées par recherche sémantique. `maintenance.md` est écartée : elle décrit la revue annuelle du dépôt, pas la méthode juridique |

**L'invariant de provenance ne change pas** : identifiant officiel, URL
canonique et date de version restent exigés quelle que soit la voie. Une
source inaccessible conduit à l'abstention (P7), jamais à une citation
reconstituée.

## Ce qu'elle conserve

- les sept principes invariants **P1 à P7**, dont la formulation v3.3.0 de P3 ;
- la distinction entre **provenance officielle** et **applicabilité à la date
  évaluée** ;
- la **traçabilité proportionnée** et la **triangulation ciblée** ;
- les **six modules activables** et la règle conservatrice de déclenchement ;
- les noms exacts des six outils de l'app, vérifiés dans
  [`mcp_server/server.py`](../mcp_server/server.py).

## Arborescence

```
chatgpt_gpt/
├── instructions.md               ← texte à coller dans le champ Instructions (≤ 8 000 caractères)
├── references/                   ← huit fichiers Knowledge à téléverser
│   ├── sources-autorisees.md     ← ordre de recherche et autorité (P3)
│   ├── modules.md                ← six modules activables, détail
│   ├── gabarits-requetes.md      ← adresses et requêtes Légifrance, réécrites pour la voie web
│   ├── checklist-vigueur.md      ← contrôle de vigueur et d'applicabilité
│   ├── format-citation.md        ← formats de citation imposés (exemples illustratifs)
│   ├── gabarits-sortie.md        ← canevas de livrables
│   ├── audit-documentaire.md     ← méthode d'audit d'un document ou d'un corpus
│   └── modes-erreur.md           ← modes d'erreur LLM connus
└── README.md                     ← ce document
```

## Paramétrage, champ par champ

Sur `chatgpt.com`, ouvrir **GPTs → Créer**, puis l'onglet **Configure**.
Ne pas passer par l'onglet *Create* (conversationnel) : il réécrit les
instructions et les amorces à chaque échange.

| Champ | Valeur |
|---|---|
| Nom | `Droit français — Recherche juridique` |
| Description | `Recherche juridique française sourcée : Légifrance et Judilibre, vérification de vigueur et d'applicabilité, citations traçables. N'invente jamais de référence ; s'abstient si la source n'est pas vérifiée.` |
| Instructions | Contenu intégral de [`instructions.md`](instructions.md), collé tel quel |
| Amorces de conversation | Les quatre amorces ci-dessous |
| Connaissances | Les huit fichiers de `references/`, téléversés un à un. Le builder accepte jusqu'à **20 fichiers**, de 512 Mo chacun |
| Fonctionnalités | **Recherche web : activée** — c'est la voie 2, indispensable. **Canvas : activable, sans compter dessus** : il a été retiré de GPT-5.5 Instant et Thinking le 28 mai 2026, la rédaction passant par les blocs d'écriture en réponse. Génération d'images : désactivée. Interpréteur de code : désactivé par défaut ; l'activer seulement pour auditer des corpus volumineux téléversés |
| Modèle recommandé | **GPT-5.6 Sol**, modèle de raisonnement phare des offres payantes depuis le 9 juillet 2026. La tâche est un enchaînement recherche / lecture / comparaison de dates : préférer un modèle de raisonnement à une variante Instant. Ce réglage n'est qu'une suggestion — l'utilisateur peut en changer, et un modèle proche est choisi s'il n'y a pas accès. Si une app ou une action est branchée, le sélecteur ne propose que des modèles non-Pro. **GPT-6 Astra**, introduit le 3 septembre 2026, n'est pas encore généralement disponible : reprendre cette ligne quand il le sera |

### Amorces de conversation

1. `Vérifie si l'article L. 2212-2 du CGCT est en vigueur et donne-moi sa version applicable aujourd'hui, avec identifiant et lien Légifrance.`
2. `Qualifie pénalement ces faits, avec les textes d'incrimination vérifiés et leurs éléments constitutifs : [décrire les faits]`
3. `Trouve une décision récente de la Cour de cassation sur la responsabilité du fait des choses et lis-la avant de la citer.`
4. `[complet] Audite juridiquement ce document et liste chaque affirmation à risque avec sa source : [coller le texte]`

Le builder régénère parfois les amorces après une modification ; la dernière
ligne des instructions lui demande de les conserver. Vérifier après chaque
enregistrement.

### App ou actions : ce qui est possible aujourd'hui

- Un GPT utilise **soit des apps, soit des actions**, jamais les deux.
- Les **actions** exigent un schéma **OpenAPI** et des points d'accès REST.
  Le serveur du dépôt ne parle que MCP ; ses seules routes HTTP annexes sont
  `/health` et deux routes `.well-known`. **Aucune action n'est donc
  configurable** sans façade REST, qui n'existe pas et n'est pas prévue.
- Les **apps** : l'app « Droit français » créée en mode développeur
  ([procédure](../docs/chatgpt-submission.md)) est la voie 1 des instructions.
  Sa disponibilité dans la section *Apps* de l'éditeur de GPT dépend du plan
  et des réglages de l'espace de travail : **la constater dans l'éditeur**,
  ne pas la supposer. Si elle n'apparaît pas, le GPT fonctionne en voie 2
  (recherche web sur domaines officiels) ; les instructions le prévoient.

### Partage

Le GPT peut rester **privé**, être partagé **par lien** ou publié sur le
**GPT Store**. Une publication publique avec app ou action demande une
politique de confidentialité valide : celle du dépôt est
[`docs/privacy-policy.md`](../docs/privacy-policy.md). Sans app ni action,
aucune donnée ne transite par le serveur du dépôt.

## Recette

Après enregistrement, dérouler dans l'aperçu les cinq scénarios positifs et
les trois négatifs de [`chatgpt-app-submission.json`](../chatgpt-app-submission.json).
Attendu en voie 2 : le GPT ouvre une page `legifrance.gouv.fr` ou un site de
juridiction avant de citer, restitue identifiant, URL et date de version, et
répond « Source non confirmée — abstention sur ce point » quand la page
n'est pas lisible. Un scénario négatif (droit californien, agenda, poème) ne
doit déclencher ni recherche juridique ni citation.

Contrôle automatisé côté dépôt : `python -m unittest tests.test_chatgpt_gpt`
vérifie le plafond de 8 000 caractères avec marge, les principes P1 à P7,
les six modules, les trois voies de récupération, la correspondance exacte
entre les fichiers annoncés dans les instructions et ceux présents dans
`references/`, et l'absence d'outillage inexistant dans un GPT.

## Versionnement

Les instructions suivent la version du noyau dont elles reprennent la
méthodologie : **3.3.0**. Une évolution du noyau qui touche les principes ou
l'échelle de récupération appelle une reprise ici, puis une nouvelle
sauvegarde du GPT : les deux ne se synchronisent pas d'eux-mêmes.

## Documentation OpenAI consultée

- [Configuring actions in GPTs](https://help.openai.com/en/articles/9442513-configuring-actions-in-gpts) : apps ou actions, schéma OpenAPI, authentification.
- [Developer mode and MCP apps in ChatGPT](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt) : création d'une app MCP.
- [Creating and editing GPTs](https://help.openai.com/en/articles/8554397-creating-a-gpt) : conditions d'accès, champs, limites de connaissances, modèle recommandé.
- [Model Release Notes](https://help.openai.com/en/articles/9624314-model-release-notes) : GPT-5.6 Sol (9 juillet 2026), retrait de canvas des modèles 5.5 (28 mai 2026).
- [ChatGPT — Release Notes](https://help.openai.com/en/articles/6825453-chatgpt-release-notes) : GPT-6 Astra (3 septembre 2026), non généralement disponible.
- [GPT Action authentication](https://developers.openai.com/api/docs/actions/authentication).
- Plafond de 8 000 caractères du champ Instructions : constaté dans le builder et documenté par la [communauté OpenAI](https://community.openai.com/t/how-can-i-increase-the-ceiling-for-gpt-instructions-beyond-8000-characters/801867).

Ces pages font foi sur les libellés d'interface, qui changent. Toute
modification de cette section doit être vérifiée à la source.
