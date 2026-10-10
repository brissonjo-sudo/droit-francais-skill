# Préparation des clients — 10 octobre 2026

Ces observations portent sur l'installation et les capacités déclarées des
clients. **Aucune réponse de modèle, aucun préflight comportemental ni score
d'utilité n'est acquis.** La sélection des trois modèles demeure à renseigner
avant le gel.

**Choix retenu :** Gemini utilise une clé gratuite et le moteur REST v2,
séparément qualifié. La [vérification des quotas](quotas-gemini-gratuit.md)
et le [protocole v2](campagne-18-modes.md) font autorité ; la recette CLI OAuth
ci-dessous est historique et ne constitue aucun repli. Le pilote attend les
trois familles ensemble après qualification réelle. Aucun appel modèle n'est
autorisé par le seul constat d'installation.

| Client | Observation locale | Reste à établir |
|---|---|---|
| Claude Code | Version 2.1.288 ; abonnement claude.ai constaté lors de la première livraison | Modèle exact accessible au compte, effort, absence de crédits supplémentaires et preuve de préflight |
| Codex | Version 0.162.0-alpha.2 ; connexion ChatGPT constatée lors de la première livraison | Modèle exact et preuve du modèle effectif dans le flux |
| Gemini CLI historique | Version 0.63.0 installée localement, aide et version exécutées depuis Python sous Windows ; clé gratuite déclarée par le titulaire | Projet et quotas actifs, modèle Flash exact, qualification du moteur REST v2, indépendante de cette CLI |

Les états d'authentification de la première livraison ne valent pas un appel
réussi aujourd'hui. Le préflight les contrôle à nouveau, sans repli API.

## Gemini local et reproductible

Installation effectuée sous le dossier ignoré
tests/bench/runs/clients/gemini-0.63.0 avec Node 24.14.1 :

~~~powershell
npm install --prefix tests/bench/runs/clients/gemini-0.63.0 --ignore-scripts --no-audit --no-fund --save-exact @google/gemini-cli@0.63.0
& ./tests/bench/runs/clients/gemini-0.63.0/node_modules/.bin/gemini.cmd --version
~~~

Le paquet, son verrou npm et ses dépendances restent locaux et ignorés.
Aucun script d'installation ni réglage global n'a été modifié.
L'appel Python subprocess au shim gemini.cmd a également retourné 0.63.0.
Cela vérifie le lancement du client, pas l'isolation d'un appel de modèle.
La CLI requiert Node >= 20 selon le paquet et la
[documentation officielle d'installation](https://geminicli.com/docs/get-started/installation/).

Pour le chemin OAuth initial, lancer ce même gemini.cmd, puis choisir
la connexion Google de l'abonnement. Cette étape doit être accomplie par
le titulaire du compte ; aucun jeton ni mot de passe n'est demandé dans le chat.
Cette recette n'est pas à exécuter pour la clé gratuite désormais retenue.
Le cache oauth_creds.json n'était pas présent au chemin utilisateur standard
lors du contrôle. Le harnais recopie seulement les caches d'authentification
dans sa session isolée.

## Choix des modèles

Le cache de modèles Codex récupéré localement le 10 octobre 2026 expose notamment
gpt-6.1-sol, gpt-6-astra, gpt-6-sol et gpt-6-luna. Cette liste est une observation
du catalogue du client ; elle ne prouve ni une réponse ni le modèle effectif
d'une future exécution.

La [documentation Claude Code](https://code.claude.com/docs/en/model-config)
consultée le 10 octobre décrit notamment les identifiants claude-opus-5-5 et
claude-sonnet-5-5. Les versions minimales indiquées, respectivement 2.1.280 et
2.1.284, sont inférieures à la version locale. La disponibilité réelle dans
l'abonnement reste à constater. Les alias évolutifs sont exclus du gel.

Fable reste exclu du périmètre de campagne. Cette exclusion est une règle
d'étude ; la préparation ne déduit aucun tarif d'une observation non sourcée.
Les modèles précis, leur authentification et leur disponibilité doivent être
confirmés avant les recettes réelles.

La [documentation de sélection Gemini](https://geminicli.com/docs/cli/model/)
consultée est datée de mars 2026. Elle décrit /model et --model, mais ne suffit
pas à choisir le modèle le plus récent aujourd'hui. Le paquet 0.63.0 contient
plusieurs identifiants dont gemini-3.1-pro et gemini-3.5-flash ; leur présence
dans le code ne prouve pas leur disponibilité dans le compte. Relever le choix
manuel accessible après connexion, puis le modèle réellement annoncé par le
flux et les statistiques. Tout basculement reste bloquant pour la comparaison.

## Préflight restant

Préparer les preuves de sources puis obtenir la validation humaine des corrigés, choisir les modèles exacts et leurs réglages,
commiter le candidat puis figer. Chaque client doit ensuite réussir son test
technique et une recherche suivie d'une lecture juridique via le MCP local.
Le catalogue de huit outils énuméré précédemment ne prouve pas cette lecture.
Les identifiants PISTE n'étaient pas exposés dans l'environnement ni dans les
fichiers canoniques contrôlés ; le fonctionnement de l'accès aux sources du
MCP local reste donc à établir avant le pilote.

La documentation officielle et le code du paquet installé ont été consultés
pour la recette. Context7 a retourné « Monthly quota exceeded » ; aucune API
ou capacité n'est déduite de sa seule absence.

Le chemin gratuit doit fournir un reçu REST v2 indépendant, lié au runtime
Python du candidat et relu humainement. Sans ce reçu, le gel des trois familles
reste fermé. CLI, Python et dépendances sont figés puis contrôlés avant/après
chaque réponse ; conserver des environnements isolés et empêcher leurs mises
à jour automatiques durant la série. Une modification détectée exige une
nouvelle série sans transfert de qualification.
