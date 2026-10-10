# Gemini gratuit : préparation, qualification et limites

Le moteur retenu pour une clé gratuite est **gemini-rest-v2**, distinct de
Gemini CLI, de l'application Gemini et de Vertex AI. Il n'utilise ni repli,
rotation de clé, retry, grounding Google ou changement de facturation. Le
code et ses tests locaux ne prouvent pas une génération gratuite réussie.
La collecte juridique exige les quotas actifs, la qualification technique,
les accès aux sources et la validation humaine des 36 corrigés.

## Relevé privé et identité du projet

Les [limites officielles](https://ai.google.dev/gemini-api/docs/rate-limits)
portent sur le projet, indépendamment de la clé. RPM, TPM d'entrée et RPD
doivent être relevés pour le modèle exact dans AI Studio. RPD se réinitialise
à minuit Pacifique. Aucun quota communautaire ou fourni par un LLM ne remplit
le relevé du projet. Toute autre limite affichée bloque pour examen.

Les formulaires privés sont au schéma **2**. Le titulaire renseigne le numéro
Google du projet, son project ID, son nom de validateur, le niveau free, le
rattachement de la clé, le modèle Flash exact hors alias, les quotas, une date
ISO avec fuseau et une preuve locale accompagnée de son SHA-256. La preuve
date de moins de 24 heures. Le code contrôle sa cohérence et ses octets ; il
ne lit ni IAM ni la valeur d'une clé GitHub et n'authentifie pas le contenu
d'une capture. Les dates destinées au lecteur sont écrites en français ou
au format JJ/MM/AAAA ; les champs machine conservent ISO.

~~~powershell
python tests/run_campaign.py quotas-gemini --initialiser tests/bench/runs/gemini/profil-01/releve.json
python tests/run_campaign.py profils-gemini --initialiser tests/bench/runs/gemini/profils.json
python tests/run_campaign.py profils-gemini --registre tests/bench/runs/gemini/profils.json --profil profil-01
~~~

Supprimer du registre privé les profils non utilisés. Chaque profil contient
seulement son identifiant, le **nom** de la variable de clé, le chemin du
relevé et celui du reçu technique `qualification` (vide avant qualification).
Ne transmettre aucune clé dans le chat, les arguments CLI, les gels ou les
fichiers suivis. Un registre cohérent conserve `collecte_autorisee=false`.

Le numéro Google normalisé identifie le budget. Une liaison privée de
l'empreinte SHA-256 de la clé au numéro bloque la redéclaration de cette clé
sous un autre projet. Deux clés déclarées au même numéro/modèle partagent
un compteur, même dans des worktrees différents. Le rattachement repose
toujours sur l'attestation du titulaire : cette liaison locale n'est pas
une preuve cryptographique Google.

Le [cadre Google APIs](https://developers.google.com/terms#section_2_using_our_apis)
doit être respecté. Plusieurs profils ne donnent aucune autorisation de
cumuler des quotas pour contourner une limite ; aucune rotation automatique
ou bascule après 429 n'est implémentée.

## État canonique et deux unités distinctes

Le lanceur utilise une seule racine utilisateur, commune aux worktrees :
`%LOCALAPPDATA%/droit-francais/bench-v2` sous Windows et le dossier utilisateur
XDG state sous Linux. Il n'existe plus d'option CLI `--budget-state`.
Les preuves privées restent dans `tests/bench/runs`, ignoré par Git.

Le lanceur réserve une tentative de réponse dans le plafond commun de
**100/jour UTC**, puis fournit un contexte avec identité, numéro de tentative,
attempt_id et échéance. REST vérifie la réservation durable active ; il ne
réserve pas une deuxième réponse. Toutes les familles et phases, y compris
qualification, préflights, juges et ablations, consomment ce plafond.

Le journal HTTP, distinct, réserve chaque `models.list`, `countTokens` et
`generateContent` avant envoi, sous verrou exclusif conservé pendant HTTP.
La marge est de 20 %, avec arrondi entier et minimum une unité. RPM/TPM ont
une fenêtre glissante de 60 secondes ; RPD suit America/Los_Angeles, fourni
par tzdata épinglé, y compris les changements d'heure. Le compteur local ne
voit pas les usages externes du projet. Les runners éphémères et plusieurs
machines ne partagent pas cet état : l'étude utilise un seul poste.

Tout envoi réservé conserve sa consommation après panne ; aucune promesse
de remboursement fournisseur. Un 429 crée un arrêt persistant, contrôlé
avant ouverture MCP et avant la réservation suivante. Le titulaire doit
examiner la cause et les usages du projet avant toute reprise. Les verrous
contiennent PID, hôte, date et nonce ; un verrou orphelin arrête et n'est
jamais retiré automatiquement. Conserver les anciens journaux : aucun
schéma v1 n'est importé silencieusement comme un budget vide. La reprise
d'anciens états ou de données ambiguës nécessite un examen explicite.

Après constat d'un PID mort sur le même poste, le retrait humain dispose
d'une commande limitée à l'état canonique ; elle journalise auteur et motif.
L'acquisition, le retrait et les récupérateurs concurrents utilisent le même
verrou OS court. Un processus actif ou une preuve de verrou ambiguë bloque
le retrait. Par exemple, pour un verrou de requête abandonné :

```powershell
python tests/bench/verrous_gemini.py --registre tests/bench/runs/profils.json --profil profil-01 --type requete --auteur "Responsable" --motif "Processus arrêté après interruption contrôlée"
```

Le type `profils` traite seulement le verrou des liaisons privées. Cette
commande conserve les budgets, les réponses et l'arrêt après HTTP 429.
Un retrait manuel de fichier hors de cette commande contourne l'exclusion
et ne constitue pas une reprise prise en charge.

## Transport, délai et confidentialité

Une échéance monotone unique débute avant MCP. Elle couvre ouverture,
initialisation, catalogue, tokenizer, génération et appels d'outils. Chaque
HTTP est aussi limité à **120 secondes au total**, bornées par l'échéance du
cas (300 secondes par défaut) ; les timeouts socket ne sont pas présentés
comme une durée totale. Le transport HTTPX est asynchrone, sans thread de
génération non annulable, proxy hérité, redirect ou retry. La lecture est
bornée à deux millions d'octets. Après délai/annulation, aucun nouvel envoi
n'est lancé. La fermeture locale bénéficie de cinq secondes au maximum,
sans nouveau modèle ni outil. Une requête déjà reçue par Google peut
continuer côté fournisseur ; le lanceur ne prétend pas l'annuler à distance.

Chaque génération est précédée du comptage de la requête complète,
instructions, schémas et historique compris. La réservation d'entrée est
majorée de 10 % puis de 32 jetons. L'usage réel absent ou excédentaire arrête
le budget, sans remboursement. Les thoughtSignature sont conservées dans
l'historique nécessaire ; leurs valeurs et les blocs de raisonnement ne
sont pas journalisés. Les erreurs ont des catégories fermées et assainies.

Le sous-processus MCP reçoit une liste blanche OS/Python et les seuls
identifiants sources Légifrance/Judilibre prévus. Les clés de modèles,
tokens GitHub, OAuth Claude, Auth0 et MCP_ACCESS_TOKEN sont exclus. Le garde
bench `LEGIFRANCE_NO_DOTENV=1` empêche leur réintroduction par les `.env` du
checkout ; les lancements habituels du serveur conservent leur comportement.

Les profils et preuves sont capturés puis validés sur les mêmes octets.
Une modification/péremption pendant le cas arrête avant la requête suivante.
Entre deux cas, une preuve fraîche identique peut renouveler le relevé ;
une hausse ne relève pas le plafond initial, une baisse ou un changement de
projet/modèle impose un examen. Les trois familles démarrent ensemble après
qualification de Gemini, aucune série à deux familles n'est substituée.

## Sondes et qualification technique

Installer le verrou du harnais, y compris ses dépendances transitives :

~~~powershell
python -m pip install --require-hashes -r requirements-bench.txt
python tests/bench/catalogue_gemini.py --registre tests/bench/runs/gemini/profils.json --profil profil-01 --sortie tests/bench/runs/gemini/catalogue.json
python tests/bench/mesure_tokens_gemini.py --registre tests/bench/runs/gemini/profils.json --profil profil-01 --sortie tests/bench/runs/gemini/tokens.json
~~~

Ces commandes envoient réellement une requête Google : les lancer seulement
après rattachement et quotas confirmés. Les sondes utilisent le même vrai
journal que REST. Le catalogue restitue les candidats Flash explicites et
des limites de contexte, qui ne sont pas des TPM. La mesure tokens prend le
modèle du profil et le plus grand prompt UTF-8 ; ce critère n'affirme pas un
maximum de tokens. Aucune de ces sondes ne génère une réponse ni ne qualifie
les outils/historiques suivants.

Un chemin technique distinct du gel juridique permet de vérifier les quatre
bras avec des demandes de contrôle, hors corrigés et avis juridique :

~~~powershell
python tests/bench/qualification_gemini.py --registre tests/bench/runs/gemini/profils.json --profil profil-01 --config tests/bench/runs/campagne-config.json --sortie tests/bench/runs/gemini/qualification.json
~~~

Cette commande génère **quatre réponses techniques** si toutes réussissent,
comptées dans le plafond commun. Elle exige moteur gemini-rest-v2, free tier,
modèle exact et effort low/medium/high explicitement configuré. Elle conserve
chaque tentative dans le journal canonique, produit un reçu `a_relire`,
et retourne 2 après panne. Après contrôle humain de l'authentification,
du modèle, de l'isolation et des accès sources, renseigner les champs de
validation du reçu et son chemin dans le registre. Le gate exige les
preuves durables concordantes, le candidat et le runtime identiques ; il
n'accepte ni un simple booléen de configuration ni un résultat Gemini CLI.
Ce reçu technique ne valide aucun corrigé et n'autorise pas seul le pilote.

Le protocole v2 prévoit **358 réponses Gemini** : quatre qualifications,
deux préflights, 64 réponses de pilote et 288 principales. Cela représente
**au moins 716 requêtes HTTP** avec tokenizer par tour. Le prototype
historique, hors ces quatre qualifications, prévoyait 354 réponses/708 HTTP.
Outils, jugements, sondes
et erreurs allongent ce minimum. Le quota RPD effectif est 80 % du quota
observé, avec l'arrondi décrit ci-dessus ; le calendrier se calcule sur les
valeurs actives. Le plafond UTC de 100 réponses reste indépendant du RPD
Pacifique. Aucune durée finale n'est promise avant le pilote.

## GitHub et preuves historiques

Les jobs réseau Gemini Actions ont été retirés le **10/10/2026**. Le job de
préparation est limité à main et à l'environnement gemini-free, ne lit
aucun secret et refuse tout envoi. La protection n'est terminée qu'après
confirmation que GEMINI_API_KEY existe dans cet environnement et a disparu
des secrets de dépôt ; un environnement ne protège pas un secret de dépôt.
Ne relancer aucun ancien workflow de branche ni transférer la clé au chat.

La [mesure Actions du 10/10/2026](https://github.com/brissonjo-sudo/droit-francais-skill/actions/runs/38046628086)
observait 31 558 tokens pour B/M15-b, 118 504 octets UTF-8, modèle demandé
gemini-3.8-flash, une requête et zéro génération. Empreinte de requête :
5402a49af46d162651f70fbdfef13e68c4bc1151901a48607a6894aed4f250eb.
L'artefact tokens-gemini était historique et retenu un jour. Le corpus a
changé depuis ; cette mesure ne qualifie ni l'entrée actuelle, ni les quotas,
ni une génération, ni les outils. Aucun appel réel Google supplémentaire
n'a été exécuté pour corriger les revues #116/#117.
