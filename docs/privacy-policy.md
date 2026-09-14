# Politique de confidentialité — Droit français

Dernière mise à jour : 4 septembre 2026

## Responsable et contact

Le plugin **Droit français** est édité par le mainteneur du dépôt public
[`brissonjo-sudo/droit-francais-skill`](https://github.com/brissonjo-sudo/droit-francais-skill).
Le nom public de l'éditeur doit correspondre à l'identité vérifiée retenue lors
de la soumission sur OpenAI Platform.

Pour une question relative à la confidentialité, utiliser la
[page de support](https://github.com/brissonjo-sudo/droit-francais-skill/issues)
en demandant, si nécessaire, un canal privé. Ne jamais publier de donnée
personnelle ou de pièce confidentielle dans une issue publique.

## Objet du service

Le plugin recherche et lit, à la demande de l'utilisateur, des articles de
droit français et des décisions judiciaires provenant de Légifrance et de
Judilibre. Il fonctionne en lecture seule et ne crée, ne modifie ni ne supprime
aucune donnée dans ces sources.

## Données traitées

Le service peut traiter :

- la requête juridique et les filtres volontairement fournis par l'utilisateur ;
- les identifiants de textes ou de décisions demandés ;
- les textes et métadonnées publics renvoyés par Légifrance ou Judilibre ;
- les métadonnées techniques nécessaires à la connexion HTTPS et MCP, telles
  qu'une adresse IP, un chemin HTTP, un horodatage ou un identifiant de session
  éphémère, lorsqu'elles sont produites par l'hébergeur ou le protocole ;
- le jeton d'authentification OAuth 2.1 présenté à chaque appel et
  l'identifiant de sujet qu'il contient, délivré par le fournisseur
  d'authentification : cet identifiant n'est jamais conservé tel quel et ne
  sert qu'à calculer l'empreinte pseudonymisée décrite à la section
  « Conservation ».

Les décisions diffusées par Judilibre sont pseudonymisées avant leur mise à
disposition, mais peuvent encore contenir des données personnelles présentes
dans une décision publique. L'utilisateur ne doit pas transmettre de données
personnelles sans nécessité pour sa recherche. Le service n'offre aucune
fonction de constitution d'un profil de magistrat ou de membre du greffe à
partir des décisions diffusées ; cet usage est interdit à l'utilisateur (voir
les [conditions d'utilisation](terms-of-use.md), art. 4).

## Finalités et bases juridiques

Les requêtes et identifiants sont traités pour exécuter la recherche demandée
et restituer la source officielle. Ce traitement est nécessaire à la fourniture
du service sollicité. Les métadonnées techniques strictement nécessaires à la
sécurité, à la prévention des abus et au diagnostic relèvent de l'intérêt
légitime de l'éditeur à exploiter un service sûr et disponible.

Le service n'utilise pas les requêtes pour la publicité, le profilage des
utilisateurs ou l'entraînement d'un modèle par l'éditeur.

## Destinataires et prestataires

Selon l'opération demandée, les données nécessaires sont transmises :

- à OpenAI, qui héberge l'interface de conversation et appelle le serveur MCP
  selon les choix de l'utilisateur ;
- à Auth0 (Okta), fournisseur d'authentification retenu par l'éditeur : il
  authentifie l'utilisateur avant tout accès aux outils, le cas échéant par une
  connexion Google promue au niveau du domaine, puis délivre le jeton dont le
  serveur lit l'identifiant de sujet ; aucune requête juridique ni aucune clé
  PISTE ne lui est transmise ;
- à Render Services, Inc., hébergeur du serveur MCP, actuellement déployé dans
  la région de Francfort ;
- à PISTE/DILA pour les recherches Légifrance ;
- à PISTE et à la Cour de cassation pour les recherches Judilibre.

Les clés d'accès PISTE sont conservées côté serveur. Elles ne sont ni demandées
à l'utilisateur, ni renvoyées dans les réponses du plugin.

Render est un prestataire établi aux États-Unis. Son accord de traitement des
données décrit les garanties contractuelles applicables aux transferts. Le
locataire Auth0 utilisé est configuré en région Union européenne ; ses propres
traitements sont régis par la politique de confidentialité d'Auth0/Okta. Les
propres traitements d'OpenAI sont régis par les informations communiquées par
OpenAI à l'utilisateur de ChatGPT ou Codex.

## Conservation

L'application ne possède pas de base de données et ne conserve pas les requêtes
ou les résultats. Son journal métier n'enregistre que le nom de l'opération,
l'état de réussite ou d'erreur, la durée et, uniquement lorsque l'appel réussit,
une empreinte tronquée stable du sujet authentifié — une erreur amont ou un
refus de quota ne journalise aucune empreinte. Cette empreinte est une **donnée
personnelle pseudonymisée**, pas une donnée anonyme : elle est obtenue par une
fonction à sens unique, non salée, et reste donc stable pour un même sujet.
Elle sert exclusivement à la sécurité, à l'imputabilité
et à la prévention des abus ; les arguments, résultats, identifiants bruts,
jetons et secrets sont exclus.

L'accès aux journaux doit rester limité aux personnes chargées de l'exploitation
et les entrées doivent être supprimées à l'issue de la durée de rétention de
l'hébergeur, sauf conservation probatoire justifiée pour un incident.
L'hébergeur peut conserver des journaux techniques selon le forfait du compte.
La documentation Render indique actuellement une conservation de 7 jours pour
un espace Hobby. Aucun flux de journaux vers un prestataire tiers n'est prévu
par l'application. Le fournisseur d'authentification conserve séparément ses
propres journaux de connexion, selon sa politique ; leur durée de rétention
reste à documenter ici.

L'historique de la conversation peut être conservé séparément par OpenAI selon
les paramètres et conditions du compte de l'utilisateur.

## Droits

Lorsque le RGPD ou la loi Informatique et Libertés s'applique, une personne peut
demander l'accès, la rectification, l'effacement ou la limitation de ses données
et, selon la base juridique, s'opposer au traitement. Elle peut également saisir
la [CNIL](https://www.cnil.fr/).

Le journal métier n'utilisant qu'une empreinte à sens unique du sujet
authentifié, l'éditeur ne peut pas retrouver de lui-même les entrées propres à
une personne déterminée : exercer un droit sur ce journal suppose que la
personne communique l'identifiant de sujet attaché à sa connexion, à partir
duquel la même empreinte peut être recalculée. Passé le délai de rétention
mentionné ci-dessus, les entrées ont déjà été supprimées par l'hébergeur et
aucune copie n'en subsiste.

L'application ne conservant pas de requête dans une base propre, certaines
demandes peuvent devoir être adressées directement à OpenAI, Render, Auth0 ou à
la source officielle concernée — notamment une demande portant sur l'identité
de connexion elle-même (compte Google ou identifiants du service), qui relève
d'Auth0 et non de l'éditeur. Les demandes d'occultation ou de levée
d'occultation d'une décision Judilibre relèvent exclusivement de la Cour de
cassation et peuvent être adressées à
`occultations.courdecassation@justice.fr`. Les droits d'accès ou de
rectification portant sur le traitement Judilibre relèvent du SDER de la Cour
de cassation.

## Sécurité et limites

Les échanges utilisent HTTPS. Le conteneur s'exécute sans privilège, les
secrets restent dans l'environnement de l'hébergeur et les erreurs sont filtrées
avant d'être renvoyées au client. Lorsqu'un défaut d'occultation crédible est
signalé, la décision complète peut être rendue temporairement indisponible,
sans modification de son texte, puis le signalement est transmis sans délai à
la Cour de cassation. Une réidentification manifeste persistante peut être
signalée à `anonymisation.sder.courdecassation@justice.fr`. Aucun système ne
pouvant être garanti sans risque, un incident peut être signalé par la page de
support ci-dessus.

## Sources de référence

- [Information des personnes — CNIL](https://www.cnil.fr/fr/conformite-rgpd-information-des-personnes-et-transparence)
- [Données ouvertes et API Judilibre](https://www.courdecassation.fr/acces-rapide-judilibre/donnees-ouvertes-open-data-et-api)
- [Accord de traitement des données Render](https://render.com/dpa)
- [Conservation des journaux Render](https://render.com/docs/logging#retention-period)
- [Politique de confidentialité Auth0/Okta](https://auth0.com/privacy)
