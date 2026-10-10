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
