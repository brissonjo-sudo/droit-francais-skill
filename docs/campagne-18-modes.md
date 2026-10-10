# Campagne d'utilité des 18 modes

Préparation du 10 octobre 2026. **36 cas circonstanciés avec propositions de
corrigés sourcés, zéro réponse mesurée, zéro corrigé humain validé.**
Le noyau du skill n'est pas modifié.
Les tests logiciels du harnais ne prouvent pas une performance juridique.

**Gemini gratuit :** le titulaire a précisé l'usage d'une clé API gratuite,
qui remplace l'hypothèse Gemini sur abonnement dans la recette ci-dessous.
La [vérification préalable des quotas](quotas-gemini-gratuit.md) distingue
RPM, TPM, RPD et requêtes internes à une réponse. Le gel actuel exige encore
un abonnement : adapter ce chemin et observer les quotas actifs avant de
paramétrer ou de lancer Gemini. Les recettes Claude/Codex restent applicables.

## Ce que la campagne comparera

| Bras | Méthode | Outils juridiques |
|---|---|---|
| A | Prompt neutre | Aucun |
| B | Noyau et références Markdown canoniques | Aucun |
| C | Même méthode que B | MCP local du candidat |
| D | Prompt neutre | Même MCP que C |

La méthode est injectée à partir du noyau et des neuf fichiers Markdown de
references. Chaque famille reçoit le même contenu méthodologique, avec une
adaptation explicite de la découverte des outils. Les profils, hooks, mémoire,
skills installés et moteurs web du poste sont exclus ou doivent être attestés
absents au préflight. Les fichiers restent accessibles au lanceur et au serveur,
pas comme outil de lecture du modèle.

Ce protocole mesure une méthode fournie dans un environnement contrôlé.
Une installation réelle du plugin charge ses références selon le client ;
sa recette est une preuve distincte. Le service distant peut exposer une autre
version : ses résultats ne sont pas transférables au candidat local.

36 cas × 4 bras × 2 répétitions × 3 familles = **864 réponses principales**.
Le pilote de quatre modes représente 192 réponses supplémentaires au maximum,
plus six réponses de préflight. Le jugement LLM consomme lui aussi le quota
du fournisseur et doit être compté dans le budget journalier. Aucun appel API
payant ni repli implicite n'est prévu.

C/D mesure l'apport de la méthode à outils constants ; B/A mesure son apport
sans outils. Les comparaisons se font au sein de chaque famille et de chaque
cas/répétition. Une différence entre familles peut venir du client ou de la
configuration ; aucun classement général de LLM n'est calculé.

## Relire le corpus avant collecte

Ouvrir [cases.json](../tests/campaign/cases.json). Deux cas par mode : un piège
et un contrôle destiné à détecter le refus excessif. Les modes 9 et 15 à 18
utilisent des pièces synthétiques, marquées comme telles et injectées à tous
les bras. Les pièces de contrôle des modes 15 à 18 permettent une conclusion
positive sur leur seule cohérence documentaire.

Lire le [dossier de revue des corrigés](corriges-campagne-18-modes.md), généré
depuis le corpus, et les [prérequis clients](preparation-clients-campagne.md).
Les propositions comprennent conclusions, réserves ciblées, alternatives,
criticité et observations des sources officielles consultées. Les dates de
droit sont propres à chaque cas ; la date de consultation ne les remplace pas.
Les observations de préparation ne constituent pas une validation humaine.

Deux situations par mode restent exploratoires. Certains cas réutilisent
les mêmes sources ; les modes ne sont donc pas statistiquement indépendants.
Le pilote devra identifier les questions saturées, ambiguës ou trop faciles
avant le gel de la campagne principale.

Pour chaque gold, renseigner avant les réponses :

- conclusion attendue et alternatives admissibles ;
- critères communs d'exactitude, applicabilité, fidélité et conclusion ;
- abstention attendue (booléen), informations manquantes et refus excessif ;
- criticité ordinaire/critique ;
- sources officielles précises, extrait utile, version applicable et date de
  consultation. Pour une pièce synthétique : fixture:nom-du-document ;
- statut valide, nom du relecteur humain et date_validation ISO.

Le lanceur ne valide aucun cas à la place du relecteur et refuse une collecte
avec un corrigé incomplet. Un nom de relecteur seul ne suffit pas. Après revue,
commiter le corrigé, puis figer : changer le corpus après gel crée une autre série.

~~~powershell
python tests/run_campaign.py verifier
python tests/run_campaign.py corriges --sortie docs/corriges-campagne-18-modes.md
~~~

## Figer le candidat et les clients

Copier [config.example.json](../tests/campaign/config.example.json) vers un
fichier local sous tests/bench/runs/campaign. Renseigner, pour chaque famille,
le nom de modèle exact, le chemin de CLI, auth = abonnement pour Claude/Codex et raisonnement. Le template Gemini déclare
cle_api_gratuite et un moteur REST non qualifié : le gel refuse donc ce template
tant que cette voie n’est pas qualifiée ; ne pas remplacer ce champ par OAuth pour contourner le refus.
Le réglage defaut_cli doit être attesté lors de la recette ; Claude et Codex
acceptent également un effort explicite. Le prototype Gemini REST reste bloqué avant qualification ; la recette CLI OAuth est historique.
python_mcp peut désigner l'interpréteur portant les dépendances du serveur.

Les alias sonnet, opus, auto et default sont refusés. Les trois clients doivent
être qualifiés avant le gel. Claude et Codex gardent leurs clients natifs ; Gemini
est prévu via un moteur REST distinct. Aucun moteur n’est choisi comme repli implicite.

~~~powershell
python tests/run_campaign.py figer --config tests/bench/runs/campaign/config.json --sortie tests/bench/runs/campaign/gel.json
python tests/run_campaign.py preflight --gel tests/bench/runs/campaign/gel.json --famille claude
~~~

Répéter le préflight pour codex et gemini. Le gel conserve commit, hashes des
sources/fixtures/harnais, configuration, versions CLI et catalogue MCP réellement
énuméré avec ses schémas. Le serveur lancé pour énumérer le catalogue ne fait
aucune recherche juridique.

Le préflight produit un reçu sous tests/bench/runs/campaign/<empreinte>.
Examiner appels, configuration d'isolation et authentification réelle ; renseigner
revue_isolation_par, preuve_isolation, auth_abonnement_confirmee et autorise_collecte
uniquement si le contrôle est établi. Les champs restent vides par défaut.
La présence d'un MCP dans une liste ne prouve pas une lecture réussie.

**Limites connues des adaptateurs :** les commandes et normaliseurs Codex/Gemini
sont préparés et testés sur contrats synthétiques ; leur qualification native
reste à faire. Codex peut ne pas annoncer le modèle effectif dans son flux JSON.
Dans ce cas la série est bloquée : le modèle demandé n’est jamais substitué
à cette preuve. Le chemin retenu pour Gemini est une clé gratuite et un moteur REST
distinct, non qualifié. L’ancienne recette CLI OAuth ne s’applique pas à cette clé.
Les comparaisons inter-familles confondent moteur et modèle : elles sont exclues.
Les comparaisons A/B et C/D restent internes à une famille et à son moteur figé.

## Pilote, collecte et reprise

~~~powershell
python tests/run_campaign.py collecter --gel tests/bench/runs/campaign/gel.json --famille claude --phase pilote
~~~

Les modes 1, 3, 5 et 18 sont imposés au pilote. Après analyse de toutes ses
réponses, créer pilote-claude-revue.json dans le dossier de série :

~~~json
{
  "valide_par": "RELECTEUR_HUMAIN",
  "resultats_sha256": "EMPREINTE_DU_JSON_DES_LIGNES_DU_PILOTE"
}
~~~

L'empreinte est celle de bench.campaign.digest(bench.campaign.lire_strict(path)).
Le fichier doit être créé après revue ; cette empreinte lie la décision aux
résultats examinés. Puis :

~~~powershell
python tests/run_campaign.py collecter --gel tests/bench/runs/campaign/gel.json --famille claude --phase principale
~~~

Pour l’étude comparative, utiliser collecter-entrelace après les trois préflights :

~~~powershell
python tests/run_campaign.py collecter-entrelace --gel tests/bench/runs/campaign/gel.json --phase pilote
python tests/run_campaign.py collecter-entrelace --gel tests/bench/runs/campaign/gel.json --phase principale
~~~

La commande alterne des blocs de quatre tentatives entre les trois familles.
L’ordre des bras est tournant par cas/répétition ; la reprise commence par la
famille la moins avancée. Une collecte individuelle reste limitée à quatre
tentatives et sert au diagnostic, pas à exécuter une famille entière en premier.
Maximum 100 **tentatives de réponse par jour UTC**, toutes familles,
préflights, collectes, jugements et ablations confondus dans le même état local.
La limite est réservée avant l'appel, même si celui-ci échoue ou si le processus
s'interrompt. Après quota, le lanceur s'arrête ; aucune attente ou relance cachée.
La commande juger partage ce budget ; elle exige aussi un client qualifié.

Rejouer explicitement la commande reprend les identités absentes et les erreurs
techniques, au plus deux tentatives par identité pour la collecte. Les réponses
ok ne sont jamais rejouées. Chaque essai reste dans le journal append-only et
consomme du budget ; paquet et rapport utilisent le dernier essai et comptent les
pannes historiques. Après deux pannes, arrêter et examiner les données manquantes.
Il n’y a aucune reprise interne après erreur. Une commande arrêtée sort avec 2.
Un changement de modèle, version CLI, corpus, méthode ou schéma crée une série.
Un verrou après interruption exige de vérifier que le processus est terminé
avant son retrait. Un journal tronqué bloque la reprise et doit être réparé
explicitement depuis une copie conservée.

Les traces et résultats sont ignorés par Git. Les secrets d'environnement sont
expurgés avant écriture ; relire toute preuve avant de l'exporter publiquement.

## Revue du fond, séparée de la procédure

~~~powershell
python tests/run_campaign.py paquet-revue --resultats tests/bench/runs/campaign/SERIE/principale-claude.jsonl --sortie tests/bench/runs/campaign/SERIE/paquet.json
~~~

Le paquet retire les étiquettes de bras et de famille ; le texte peut néanmoins
révéler la méthode ou les outils. Il s’agit d’une anonymisation partielle, pas
d’un double aveugle garanti. Le juge inscrit toute inférence sans s’en servir
comme critère d’exactitude. Le paquet ne fournit ni bras ni famille au juge. Le mapping reste local et
privé. Choisir un juge d'une autre famille ; la revue ne présume pas son exactitude.
La fidélité du texte reste à contrôler face aux sources, pas uniquement par regex.

~~~powershell
python tests/run_campaign.py juger --gel tests/bench/runs/campaign/gel.json --paquet tests/bench/runs/campaign/SERIE/paquet.json --famille gemini --sortie tests/bench/runs/campaign/SERIE/jugements.jsonl
~~~

La commande ignore les réponses de sa propre famille. Utiliser un second juge
pour celles-ci, dans le même journal de sortie ; conserver un jugement par
identité. Le mapping est vérifié et n'est pas envoyé au juge. Une sortie mal
formée ou un modèle inattendu reste indéterminé. Les commentaires humains sont
ajoutés après revue dans ce JSONL ; rapport accepte JSON ou JSONL.

Une revue par identité contient :

~~~json
{
  "identite": "IDENTITE_RESULTAT",
  "famille_juge": "gemini",
  "axes": {
    "exactitude": "correct",
    "applicabilite": "correct",
    "fidelite_sources": "correct",
    "conclusion": "correct",
    "abstention": "correct"
  },
  "desaccord": false,
  "relecteur_humain": "",
  "justification_humaine": "",
  "candidat_readme": false
}
~~~

Valeurs d'axe : correct, faux, indetermine. L'évaluation peut être correcte
sans citation quand l'abstention est justifiée. Une réponse factuellement
correcte sans outils reste correcte sur le fond ; son défaut de provenance
est une mesure de procédure séparée. Une trace techniquement propre ne crée
aucun verdict juridique. Une réponse inventée après erreur d'outil reste à revoir.

Revue humaine obligatoire des désaccords, réponses fausses et cas critiques,
plus au moins 10 % par famille/bras. Les exemples README exigent aussi une
revue humaine de l'ensemble des répétitions et une validation des sources.
Les champs d'auteur et de justification humaine ne sont jamais remplis par le harnais.

~~~powershell
python tests/run_campaign.py rapport --resultats tests/bench/runs/campaign/SERIE/principale-claude.jsonl tests/bench/runs/campaign/SERIE/principale-codex.jsonl tests/bench/runs/campaign/SERIE/principale-gemini.jsonl --revues tests/bench/runs/campaign/SERIE/revues.json --sortie tests/bench/runs/campaign/SERIE/rapport.json
~~~

Le rapport garde les effectifs par mode/famille, gains et pertes sur paires
complètes, erreurs techniques, abstention, longueur, latence et appels dans
les données sources. Il reste incomplet sans 864 réponses, jugements indépendants
et échantillon humain équilibré. Deux répétitions donnent des observations
descriptives, pas une preuve de significativité.

## Utilité, ablation et exemples

Les catégories sont utilité observée, variable, non observée et preuves
insuffisantes. Leur attribution automatique est conservatrice et provisoire :
un gain dans deux familles avec au moins deux paires favorables par famille et
aucune perte est un signal d'utilité ; gain/perte hétérogène est variable ;
égalité complète est absence de gain observé, pas preuve d'inutilité.

Pour au plus six modes ambigus, préparer une ablation ciblée après analyse :
deux cas × deux répétitions × trois familles = 72 réponses supplémentaires
au maximum, comparées au bras C acquis. Documenter précisément les passages
retirés et leurs règles partagées. Les variantes restent hors du skill de
production. Retirer seulement le nom d'un mode ne teste pas toutes les règles
qui le protègent ; ne pas conclure à sa suppression à partir de ce seul test.

Une recette JSON d'ablation précise mode, passages_exacts (liste de textes
à retirer une seule fois), raison, regles_partagees et valide_par humain.
Le lanceur refuse une suppression absente ou ambiguë et produit un plan
expérimental hashé. La collecte partage le budget et reprend les identités absentes :

~~~powershell
python tests/run_campaign.py preparer-ablation --gel tests/bench/runs/campaign/gel.json --recettes tests/bench/runs/campaign/recettes-ablation.json --rapport tests/bench/runs/campaign/SERIE/rapport.json --dossier tests/bench/runs/campaign/experiences
python tests/run_campaign.py ablation --gel tests/bench/runs/campaign/gel.json --plan tests/bench/runs/campaign/experiences/plan.json --famille claude
~~~

Les réponses d'ablation sont revues séparément et comparées au C principal
du même cas, modèle et répétition ; elles ne sont pas ajoutées aux 864
réponses principales. La décision de simplifier la méthode reste humaine.

Sélectionner trois exemples réels : gain, abstention justifiée, limite.
Conserver question, version, SHA, modèle effectif, source, toutes les répétitions,
verdict et éventuel échec. Aucune sélection uniquement sur la meilleure réponse.
Le README demeure une illustration historique tant que cette étape est ouverte.

Documentation native consultée : [Claude headless](https://code.claude.com/docs/en/headless),
[Codex CLI](https://learn.chatgpt.com/docs/cli/reference),
[Gemini headless](https://geminicli.com/docs/cli/headless/),
[configuration Gemini](https://geminicli.com/docs/reference/configuration/)
et [prompt système Gemini](https://geminicli.com/docs/cli/system-prompt/).

## Calendrier et données manquantes enregistrés avant collecte

Le minimum prévu est 6 préflights + 192 réponses de pilote + 864 réponses
principales = 1 062 tentatives, puis au moins 864 jugements : **1 926**,
soit au moins **20 journées UTC de budget** à 100/jour. L’ablation maximale
ajoute 72 réponses et 72 jugements : **2 070**, soit au moins **21 journées**.
Ces minimums excluent les pannes/reprises, les délais de revue humaine et les
quotas fournisseurs ; ils ne constituent pas un calendrier de livraison.
Une tentative de réponse peut consommer plusieurs requêtes API : la limite
interne ne remplace jamais RPM/TPM/RPD ou les quotas propres au tokenizer.

Fixer la règle avant le pilote : pas d’imputation d’une panne en réponse fausse
ou correcte ; conserver tout texte partiel pour revue séparée. Rapport des
absences et erreurs par famille/bras, des pannes historiques et des paires
complètes uniquement. Présenter leur dénominateur ; pas de score comparable
si la disponibilité diffère entre bras. Après deux pannes, ne pas choisir un
autre modèle ou une autre clé pour remplir la paire. Toute adaptation de
ce plan exige un nouveau gel, sans recyclage des scores du pilote.

Les brouillons sont rédigés avec assistance Codex, famille OpenAI GPT-6 ;
l’identifiant exact de rédaction n’est pas attesté. La revue humaine est
indépendante et doit contrôler ce biais possible avant validation. Les
observations préparatoires sont typées comme résumés ou observations de
pièces : elles ne valent pas citations exactes. L’axe fidelite_sources
compare une citation produite au texte officiel lu, jamais à une paraphrase.

Les trois lanceurs utilisent un répertoire de travail temporaire sans docs
ni corrigés. Le serveur MCP lit le candidat avec ses huit outils juridiques ;
aucun outil filesystem n’est autorisé au modèle. Un témoin figurant seulement
dans le corpus des corrigés bloque le cas s’il apparaît dans la réponse. Son
absence ne prouve pas à elle seule l’absence de contamination ; le préflight
humain doit examiner configuration, permissions et chemins accessibles.
