# Relecture de la campagne — PR #116

État au 10/10/2026 : harnais v2 préparé localement, aucune réponse de modèle
réelle générée, aucun corrigé humain validé (0/36). La qualification Gemini
REST et la revue juridique restent des passages distincts avant les trois
familles du pilote. Le [protocole](campagne-18-modes.md) décrit leurs commandes.

## Corrections des constats

| Constat | Garantie appliquée |
|---|---|
| Succès rejoué après reprise ou concurrence | Verrou partagé sur toute la collecte ; lecture autoritaire sous verrou ; succès acquis immuable |
| Crash contournant les deux tentatives ou les 100/jour | Réservation durable avant moteur et MCP ; aucun remboursement ; deux réservations par identité et 100 par jour UTC toutes phases/familles |
| Fenêtre résultat écrit/clôture absente | Arrêt indéterminé ; récupération humaine rapproche résultat, réservation et hash, conserve son succès et interdit son rejeu |
| Retrait concurrent d'un verrou abandonné | Exclusion OS courte partagée par création, retrait et nettoyage ; aucune suppression si processus actif ou état incertain |
| Deux pannes bloquant tout le reste | Déclaration humaine motivée de manquant après deux échecs clôturés ; autres unités autorisées ensuite |
| Contamination, modèle ou isolation réessayés | Invalidation définitive de la série ; panne jamais jugée automatiquement |
| Avis humain mélangé au journal du juge | Journal humain séparé, chaîne de révisions et deux liens SHA ; arbitrage final validé prioritaire, juge conservé |
| Résultat ou jugement fabriqué pour le rapport | Lecture vérifiée contre réservation/clôture/hash et lien jugement/résultat ; rapport sous verrou ; ablation exige son recalcul |
| Alias/paramètres implicites et clients changeants | Modèles exacts, paramètres réellement appliqués et champs inconnus refusés ; CLI, Python, versions de distributions, catalogue et fichiers de dépendances gelés |
| Reprises donnant 300 secondes supplémentaires | Deadline absolue créée avant MCP ; vérifications consomment ce délai ; timeout natif borné au reste |
| Répétitions séparées par une longue dérive | Ordre matérialisé : répétitions proches, rotations de familles et bras, contrôlé lors des reprises |
| Jeton de revue déductible publiquement | HMAC avec sel aléatoire gardé dans le mapping privé canonique ; labels de bras/famille absents du paquet |
| Dénominateurs statiques et pannes masquées | Effectifs attendus dérivés du plan ; réservations historiques et manquants par strate ; paires incomplètes exclues |
| Questions orientées ou manque de faits uniforme | Quatre questions neutralisées et 36 explications individualisées ; faits manquants renseignés lorsqu'ils affectent le cas |
| Résumés présentés comme vérification juridique | Statut de preuve par source, fragment primaire et version lorsque récupérés ; ailleurs non vérifié ; champ de revue humaine vide |

## Vérifications locales

Le 10/10/2026, la suite complète `python -m unittest discover -s tests -p
'test_*.py'` a exécuté **548 tests**, avec **1 test d'intégration volontairement
ignoré** dans cette commande. Le contrôle distinct, activé par
`BENCH_TEST_MCP_INTEGRATION=1`, a ensuite exécuté et réussi le vrai catalogue
stdio des huit outils. Ce contrôle est également une étape explicite de CI ;
aucun résultat de CI distante n'est revendiqué ici.

Les contrôles plugin, liens, affirmations, commandes, vault, corpus et
`git diff --check` passent localement. La suite ciblée de campagne exécute
51 tests, dont le même contrôle opt-in ignoré hors activation. Les moteurs
de réponse de ces régressions sont simulés ; les collecteurs, réservations,
reprises et écritures sont réellement exécutés dans des états temporaires.

Les anciens tests v1 devenus incompatibles ont été remplacés par des preuves
du nouveau contrat, sans réduire les garanties à des assertions sur des mocks.

| Garantie ancienne | Régression v2 |
|---|---|
| Budget/lendemain et deux tentatives | `test_budget100_global_avant_appel_et_reprise_lendemain`, crash avant clôture et déclaration motivée |
| Gel changé avant/après | Tests de gel/runtime avant et après réponse, avec invalidation durable |
| Reprise et entrelacement | Collecteurs réels, reprise zéro réponse acquise, concurrence deux collecteurs et ordre des 24 unités réduit |
| Revue privée et humain distinct | Paquet HMAC sans labels, exclusion infra, révisions humaines, refus de signature LLM et arbitrage prioritaire |
| Journaux tronqués et ancien format | Refus sans migration ni effacement ; catégorie infra inconnue refusée |
| Ablation exacte/autre candidat | Passage absent/ambigu refusé, autre série refusée, contamination classée infra et skill préservé |
| Authenticité des résultats | Refus d'identité reconstruite ; jugement durable non clôturé refusé puis récupéré sans rejeu |
| Catalogue MCP réel | Test opt-in stdio effectivement exécuté et étape dédiée en CI |

## Preuve juridique préparatoire et limites

Le [registre des sources](../tests/campaign/preuves-sources-20261010.json)
recense 27 références distinctes, pièces comprises. Six textes ou décisions
officiels ont été récupérés dans la session : articles 1242 du Code civil,
21, 73, 78-3 et 78-6 du CPP, et décision Benjamin du 19/05/1933. Chaque entrée
décrit son fragment, sa version et ses limites ; les autres références
juridiques restent explicitement non vérifiées dans cette session.

L'article 21 a été lu dans la version couvrant la date utile du cas, mais
sa page adressée précisément au 16/05/2026 n'a pas été récupérée. Benjamin
est une identification historique, sans recherche de sa portée actuelle.
Les fragments ne remplacent pas les textes complets pour contrôler toutes
les propositions du corrigé. Aucune paraphrase n'est transformée en citation
exacte et aucune préparation agent ne remplit le champ de validation humaine.

Les dates numériques françaises du dossier généré sont européennes ; les
dates machine JSON restent ISO. Le modèle exact de rédaction des brouillons
reste non attesté. Les dépendances installées dans la venv locale (MCP 2.2.0,
PyJWT 2.15.0) qualifient ces contrôles logiciels ; elles ne prouvent ni compte
gratuit, quota Gemini, comportement des trois modèles ni utilité des 18 modes.

Le minimum de planification reste 1 930 réservations avec qualification Gemini
et jugements, avant reprises, puis jusqu'à 2 074 avec ablation maximale.
Les anciens bilans 521/525 et observations de 16 sources sont conservés comme
traces historiques, sans transfert de qualification au harnais v2.
