# Vérification Gemini gratuit — 10 octobre 2026

La campagne doit utiliser la clé Gemini gratuite indiquée par le titulaire.
Cela remplace l'hypothèse d'une connexion Gemini sur abonnement Google.
**Les valeurs actives RPM/TPM/RPD ne sont pas établies : aucun réglage de
cadence ni gel pour cette clé n'est validé. Aucun appel de modèle n'a été fait.**

## Règles officielles vérifiées

La [documentation Gemini API](https://ai.google.dev/gemini-api/docs/rate-limits),
mise à jour le 9 octobre 2026 et consultée le 10 octobre, définit :

| Dimension | Ce qui est limité |
|---|---|
| RPM | Requêtes par minute |
| TPM | Tokens d'entrée par minute |
| RPD | Requêtes par jour |

Dépasser une seule dimension suffit à déclencher une erreur de quota.
Les limites sont propres au modèle et au niveau du **projet**, pas à chaque
clé séparément. Les autres usages du même projet consomment donc cette capacité.
Les RPD se réinitialisent à minuit, heure du Pacifique ; le jour UTC du
compteur actuel du harnais n'est pas cette fenêtre. Les modèles expérimentaux
et preview ont des limites plus restrictives. Google renvoie désormais vers
[AI Studio, limites actives](https://aistudio.google.com/rate-limit) pour les
valeurs du projet et précise que la capacité réelle peut varier.

La [page des quotas Gemini CLI](https://geminicli.com/docs/resources/quota-and-pricing/)
annonce, pour une clé API non payante, **250 requêtes de modèle par jour** et
l'accès aux modèles **Flash seulement**. Ce chiffre général ne prouve ni les
RPM/TPM ni les limites actives du modèle et du projet retenus. Il ne doit pas
être enregistré comme quota observé du compte. Les quotas OAuth Google sont
distincts et ne sont pas transférables à une clé API.

L'[authentification officielle de la CLI](https://geminicli.com/docs/get-started/authentication/)
prend en charge GEMINI_API_KEY et la sélection « Use Gemini API key ».
Le secret doit rester dans l'environnement du processus, hors des fichiers
de gel, des traces et de Git. Aucun changement de facturation n'est prévu.

## Observations locales et limites

La page AI Studio authentifiée a été consultée en lecture seule. Deux projets
consultés portent le badge « Niveau sans frais », mais leur tableau indique
« Aucune donnée d'utilisation disponible », y compris avec « Tous les modèles ».
Cela ne prouve ni un quota nul ni une capacité illimitée. Le rattachement de
la clé de campagne à l'un de ces projets reste à confirmer par le titulaire.
Les identifiants du compte, des projets et des clés ne sont pas publiés ici.

GEMINI_API_KEY et GOOGLE_API_KEY ne sont pas exposées dans l'environnement
de cette session ; ces noms sont également absents du fichier .env canonique
du dépôt contrôlé. Cela ne prouve pas l'absence de la clé sur le poste.
Aucun secret n'a été affiché et aucune clé n'a été créée ou remplacée.

Le harnais actuel retire les clés API de l'environnement et sélectionne
oauth-personal dans Gemini CLI. Le gel et les préflights exigent encore
auth = abonnement. **Ce chemin ne peut pas exécuter la campagne demandée avec
une clé gratuite ; sa modification est un préalable distinct.**

La méthode et ses références représentent localement **113 659 octets UTF-8**,
avant la question, les pièces et les retours des outils. Ce volume n'est pas
un nombre de tokens. Il faut mesurer les tokens d'entrée du modèle retenu,
y compris le contexte transmis à chaque reprise après un appel d'outil.

Le paquet Gemini CLI 0.63.0 installé contient un mécanisme retryWithBackoff
pour les appels au modèle et une valeur DEFAULT_MAX_ATTEMPTS de 10 dans
packages/core/src/utils/retry.ts, visible dans le bundle. Les options peuvent
la remplacer : ce constat ne prouve pas dix tentatives dans chaque run.
L'absence de boucle de retry dans le lanceur Python ne garantit donc pas
l'absence de reprises internes dans la CLI. Elles doivent être maîtrisées
et comptées avant de qualifier le chemin gratuit.

Context7 a retourné « Monthly quota exceeded ». Les règles ci-dessus proviennent
des pages officielles et le constat de reprise du paquet effectivement installé.

## Paramétrage à établir avant le test

1. Identifier le projet de la clé, confirmer son niveau gratuit et relever,
   pour un identifiant Flash exact accessible, les valeurs actives RPM, TPM,
   RPD et toute autre limite affichée. Conserver date et preuve dans l'état
   local ignoré ; ne pas inventer de valeurs si le tableau reste vide.
2. Adapter explicitement l'authentification Gemini du harnais à cette clé,
   sans Vertex, OAuth, facturation supplémentaire, repli de modèle ou
   sélection automatique. Vérifier l'isolation et l'absence de secret dans
   les traces. Les chemins Claude et Codex restent sur leurs abonnements.
3. Contrôler la cadence **à chaque requête de modèle**, pas uniquement entre
   réponses finales. Inclure les reprises après outils, erreurs, préflights
   et jugements ; réserver un budget avant envoi et suivre les tokens
   d'entrée. Prévoir une marge pour les autres usages du projet et pour les
   données AI Studio qui peuvent être différées de quinze minutes.
4. Garder le plafond global de 100 tentatives de réponse/jour UTC comme
   limite propre à l'étude, et appliquer en plus les limites API par modèle
   et projet, avec un compteur RPD au fuseau America/Los_Angeles tenant compte
   des changements d'heure. La plus restrictive des limites s'applique.
5. Sur 429, conserver les preuves et arrêter le lot ; aucune reprise interne
   non comptée ni changement de modèle. Une reprise ultérieure est explicite,
   après réévaluation du quota. Si la CLI ne permet pas de contrôler ces
   requêtes, ne pas qualifier cet adaptateur pour la collecte gratuite.
6. Exécuter les préflights techniques puis le pilote après la revue humaine
   des corrigés. Mesurer requêtes/réponse, tokens d'entrée, reprises et durée
   pour estimer la capacité quotidienne avant la campagne principale.

Pour Gemini seul, le protocole prévoit **288 réponses principales + 64 de
pilote + 2 de préflight = 354 réponses**, hors jugements et ablations.
Avec au moins un appel par réponse, cela représente au moins 354 requêtes.
Si le plafond général de 250 RPD s'applique, deux fenêtres quotidiennes sont
déjà nécessaires ; les appels d'outils, jugements et TPM peuvent allonger
fortement cette durée. Aucune date de fin n'est donc promise avant le pilote.

L'absence de quotas observables bloque le paramétrage de la collecte Gemini,
mais pas la revue des 36 corrigés ni la préparation des autres clients.

## Contrôle local du relevé

Le formulaire contient seulement des champs vides et des quotas null.
Créer sa copie privée dans l'état ignoré :

~~~powershell
python tests/run_campaign.py quotas-gemini --initialiser tests/bench/runs/gemini/releve.json
python tests/run_campaign.py quotas-gemini --preuve tests/bench/runs/gemini/releve.json
~~~

Le deuxième appel échoue volontairement tant que le relevé n'est pas complet.
Renseigner le projet Google associé à la clé, un modèle Flash exact, les trois
valeurs positives, une date ISO avec fuseau et une pièce locale avec son SHA-256.
La preuve doit également rester sous tests/bench/runs ; ne pas y inclure la clé.
Confirmer la vérification des éventuelles autres limites. Si elles existent,
le contrôle bloque pour examen plutôt que de les ignorer.

Le contrôle applique une fraîcheur maximale de 24 heures, choix conservateur
du protocole, et vérifie les octets de la pièce. Il ne vérifie pas lui-même
le contenu de l'image ni le rattachement réel de la clé : un relevé cohérent
reste une déclaration à examiner au préflight. Aucune valeur privée ni secret
n'est affiché. La présence de GEMINI_API_KEY est seulement signalée par un
booléen ; elle ne prouve ni l'authentification ni la gratuité.

Même avec un relevé cohérent, collecte_autorisee reste false : cet outil
ne remplace ni l'adaptateur avec contrôle par requête ni les validations humaines.
Un gel configuré avec auth = cle_api_gratuite s'arrête explicitement avant
toute invocation CLI tant que ce chemin n'est pas qualifié.

Lors de la reprise, AI Studio a redirigé vers sa page d'erreur /520. Aucun
quota actif supplémentaire n'a donc été acquis. Le Python local ne dispose
pas non plus des données ZoneInfo America/Los_Angeles : leur fourniture
reproductible sous Windows reste nécessaire avant d'implémenter le compteur.

## Clé GitHub Actions

Le titulaire autorise l'utilisation de GEMINI_API_KEY du dépôt GitHub.
La vérification des métadonnées constate un **secret Actions** de ce nom ;
aucune variable Actions Gemini n'a été trouvée. L'API GitHub ne restitue
[jamais la valeur d'un secret](https://docs.github.com/en/rest/actions/secrets#get-a-repository-secret).
La clé est donc utilisable dans le runner, sans extraction vers le poste.

Le workflow manuel existant Sonde fonctionnelle possède désormais un choix
gemini-catalogue. Ce choix exécute uniquement un GET du catalogue officiel,
avec la clé dans l'en-tête x-goog-api-key et une destination fixe HTTPS.
Il refuse les redirections et les reprises. Aucun prompt, génération, source
juridique, appel Auth0 ou PISTE n'est envoyé par ce job. La sonde MCP habituelle
reste le choix par défaut et est exclue pour ce contrôle Gemini.

~~~powershell
gh workflow run sonde-fonctionnelle.yml --repo brissonjo-sudo/droit-francais-skill --ref codex/adoption-evaluation-20261010 -f controle=gemini-catalogue
~~~

Seules les métadonnées du catalogue sont archivées pour un jour : noms,
tailles de contexte et capacité de génération déclarée. Une lecture réussie
ne prouve ni l'accès à une génération gratuite, ni les quotas actifs,
ni l'association de cette clé au projet consulté dans AI Studio. Les tailles
de contexte inputTokenLimit/outputTokenLimit ne sont pas des limites TPM.

## Complément vérifié après le retour documentaire

Le retour fourni par un LLM est une déclaration, pas une preuve des quotas
actifs. Les pages officielles ont été relues le 10 octobre 2026. Aucun chiffre
RPM/TPM/RPD du projet n'est ajouté au relevé privé sur cette base.

La [fiche Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash)
classe gemini-3.8-flash comme version stable, avec function calling et thinking.
La [tarification officielle](https://ai.google.dev/gemini-api/docs/pricing)
indique des entrées et sorties gratuites pour ce modèle en mode Standard.
Ce nom est donc un candidat documenté pour la qualification ; il n'est pas
encore gelé pour l'étude. Ni ces pages ni le catalogue ne démontrent la
capacité active du projet. Le Batch et le grounding Google Search/Maps ne
sont pas disponibles gratuitement pour ce modèle dans cette grille ; les
sources juridiques restent celles du MCP prévu par le protocole.

Le [guide de comptage](https://ai.google.dev/gemini-api/docs/tokens) fournit
countTokens pour mesurer l'entrée de la requête. Le volume de 113 659 octets
ne devient pas une mesure de 25 000 à 30 000 tokens par une conversion
approximative. Compter le contexte réellement transmis : instructions,
question, pièces, schémas d'outils et historique selon le format choisi.
Cette mesure technique doit rester distincte d'une génération et conserver
modèle, empreinte de l'entrée, nombre de tokens et date. Elle ne détermine
pas les quotas ni la réussite d'une génération.

Le [guide thinking](https://ai.google.dev/gemini-api/docs/thinking) distingue
les tokens de sortie et de raisonnement dans les métadonnées d'usage ; leur
somme intervient dans la tarification et le plafond de génération. Le TPM
documenté pour les limites de débit porte sur l'entrée. Ne pas assimiler
automatiquement ces compteurs à une même limite.

Le [guide de dépannage](https://ai.google.dev/gemini-api/docs/troubleshooting)
recommande un backoff borné pour les erreurs transitoires. Ce conseil ne
prouve pas qu'un 429 consomme toujours le RPM ou le RPD, ni qu'il épuise la
journée. Pour notre compteur conservateur, toute tentative envoyée réserve
une unité avant envoi ; un échec ne rembourse pas cette réservation locale.
Le protocole conserve l'arrêt du lot sur 429, avec diagnostic avant reprise,
pour éviter des retries internes non comptés. C'est un choix de l'étude.

Les pages consultées n'établissent pas que models.list ou l'ouverture du
Playground initialisent les quotas visibles. Cette suggestion n'est pas
une procédure officielle vérifiée. La documentation de la CLI distingue
également l'accès par compte Google de l'accès par clé API ; la CLI ne
consomme pas toujours les quotas de la Developer API, selon son mode
d'authentification. Le chemin retenu ici reste celui de la clé gratuite.

Enfin, 354 réponses sous le plafond interne de 100 tentatives par jour UTC
nécessitent **au moins quatre journées UTC de quota pour Gemini seul**.
Il s'agit de fenêtres de compteur, pas d'une promesse de quatre fois 24 heures
écoulées. Ce budget est partagé avec les autres familles et les jugements ;
les TPM, RPD au fuseau Pacifique, tours d'outils et temps de traitement peuvent
allonger le calendrier. Les calculs de 35 ou 89 minutes correspondent seulement
à un espacement hypothétique de 354 appels simples, sans ces contraintes.

Le réglage reste à concurrence 1, sans fallback ni changement de facturation.
Un intervalle fixe de 10 à 15 secondes ne suffit pas à qualifier le TPM :
la cadence doit résulter des quotas observés et des entrées mesurées par tour.

## Plusieurs clés et profils privés

Les limites Gemini sont appliquées au projet. Deux clés du même projet ne
créent donc pas deux budgets indépendants. Pour des projets distincts, les
conditions générales [Google APIs, section 2(d)](https://developers.google.com/terms#section_2_using_our_apis)
interdisent le contournement des limitations. Le simple rattachement à des
projets distincts ne prouve pas l'autorisation de cumuler des quotas gratuits
pour une même campagne. L'usage envisagé doit être compatible avec ces limites ;
une extension au-delà requiert l'accord exprès prévu dans ces conditions.

Le harnais prépare un registre privé de profils pour identifier les clés,
leurs projets et leurs relevés sans les divulguer. Il ne réalise aucune
rotation automatique ni bascule après un 429. Le plafond global de 100
tentatives de réponse par jour UTC reste commun à toute l'étude, quel que
soit le nombre de profils. Aucun cumul de capacité gratuite n'est annoncé.

~~~powershell
python tests/run_campaign.py profils-gemini --initialiser tests/bench/runs/gemini/profils.json
python tests/run_campaign.py quotas-gemini --initialiser tests/bench/runs/gemini/profil-01/releve.json
python tests/run_campaign.py quotas-gemini --initialiser tests/bench/runs/gemini/profil-02/releve.json
python tests/run_campaign.py profils-gemini --registre tests/bench/runs/gemini/profils.json --profil profil-01
~~~

Chaque entrée contient un identifiant neutre profil-01, le **nom** d'une
variable d'environnement (GEMINI_API_KEY ou GEMINI_API_KEY_COMPTE_2), et le
chemin d'un relevé privé. Aucun secret en clair n'est accepté dans ce registre.
Les valeurs restent dans l'environnement ou les secrets Actions, jamais dans
le chat, les arguments CLI, le gel ou les fichiers suivis. Le titulaire peut
préparer d'autres profils sans créer de clé depuis le harnais.

Le contrôle réutilise les exigences du relevé individuel : projet confirmé,
modèle exact, quotas actifs, preuve avec empreinte et fraîcheur de 24 heures.
Il regroupe les déclarations cohérentes par projet, détecte les relevés
contradictoires et les noms de profil ou variable dupliqués. Des modèles
différents exigent des séries distinctes. Sa sortie expose seulement des
identifiants neutres, groupes de quotas déclarés, problèmes et booléens de
présence des clés ; pas les projets, chemins privés ni valeurs de secrets.

La sélection exige --profil ; aucun profil disponible ne remplace un profil
absent ou incomplet. Ce contrôle reste hors réseau et collecte_autorisee
reste false, même avec des profils cohérents. Il prépare la configuration,
sans qualifier l'adaptateur gratuit ni le gel. L'exécuteur devra attacher un
profil fixe à chaque lot, garder le même profil pour tous les tours d'un cas,
compter RPM/TPM/RPD par projet et modèle, et partager les compteurs entre clés
d'un même projet. Un changement explicite de profil devra être tracé et pris
en compte dans l'équilibrage des bras et répétitions ; pas de nouveau tirage
d'une réponse décevante sous une autre clé.

## Mesure technique de l'entrée

Le workflow Sonde fonctionnelle accepte gemini-tokens : un POST countTokens
vers gemini-3.8-flash, sans génération, retry, Auth0 ou PISTE. La charge est
la requête du bras B : instructions et références, puis le cas sélectionné
par taille de prompt UTF-8. Ce critère n'affirme pas un maximum de tokens.
La [référence REST countTokens](https://ai.google.dev/api/tokens) prévoit
generateContentRequest pour inclure les instructions système. Aucune clé
n'est placée dans l'URL, la charge, la sortie ou les arguments CLI.

~~~powershell
gh workflow run sonde-fonctionnelle.yml --repo brissonjo-sudo/droit-francais-skill --ref codex/adoption-evaluation-20261010 -f controle=gemini-tokens
~~~

L'artefact tokens-gemini ne contient que modèle demandé, cas, date, compteur,
tailles et empreintes de la charge et du corpus ; pas le texte transmis.
Sa rétention est d'un jour. Ni les outils des bras C/D ni leur historique
ne sont inclus dans cette mesure. Aucun résultat juridique, quota actif,
modèle effectif d'une génération ou autorisation de collecte n'est déduit.
