# Politique de confidentialité — Droit français

Dernière mise à jour : 30 août 2026

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
  éphémère, lorsqu'elles sont produites par l'hébergeur ou le protocole.

Les décisions diffusées par Judilibre sont pseudonymisées avant leur mise à
disposition, mais peuvent encore contenir des données personnelles présentes
dans une décision publique. L'utilisateur ne doit pas transmettre de données
personnelles sans nécessité pour sa recherche.

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
- à Render Services, Inc., hébergeur du serveur MCP, actuellement déployé dans
  la région de Francfort ;
- à PISTE/DILA pour les recherches Légifrance ;
- à PISTE et à la Cour de cassation pour les recherches Judilibre.

Les clés d'accès PISTE sont conservées côté serveur. Elles ne sont ni demandées
à l'utilisateur, ni renvoyées dans les réponses du plugin.

Render est un prestataire établi aux États-Unis. Son accord de traitement des
données décrit les garanties contractuelles applicables aux transferts. Les
propres traitements d'OpenAI sont régis par les informations communiquées par
OpenAI à l'utilisateur de ChatGPT ou Codex.

## Conservation

L'application ne possède pas de base de données et ne conserve pas les requêtes
ou les résultats. Son journal métier n'enregistre que le nom de l'opération,
l'état de réussite ou d'erreur et la durée ; les arguments, résultats et
secrets sont exclus.

L'hébergeur peut conserver des journaux techniques selon le forfait du compte.
La documentation Render indique actuellement une conservation de 7 jours pour
un espace Hobby. Aucun flux de journaux vers un prestataire tiers n'est prévu
par l'application.

L'historique de la conversation peut être conservé séparément par OpenAI selon
les paramètres et conditions du compte de l'utilisateur.

## Droits

Lorsque le RGPD ou la loi Informatique et Libertés s'applique, une personne peut
demander l'accès, la rectification, l'effacement ou la limitation de ses données
et, selon la base juridique, s'opposer au traitement. Elle peut également saisir
la [CNIL](https://www.cnil.fr/).

L'application ne conservant pas de requête dans une base propre, certaines
demandes peuvent devoir être adressées directement à OpenAI, Render ou à la
source officielle concernée. Les demandes d'occultation ou de levée
d'occultation d'une décision Judilibre relèvent de la Cour de cassation.

## Sécurité et limites

Les échanges utilisent HTTPS. Le conteneur s'exécute sans privilège, les
secrets restent dans l'environnement de l'hébergeur et les erreurs sont filtrées
avant d'être renvoyées au client. Aucun système ne pouvant être garanti sans
risque, un incident peut être signalé par la page de support ci-dessus.

## Sources de référence

- [Information des personnes — CNIL](https://www.cnil.fr/fr/conformite-rgpd-information-des-personnes-et-transparence)
- [Données ouvertes et API Judilibre](https://www.courdecassation.fr/acces-rapide-judilibre/donnees-ouvertes-open-data-et-api)
- [Accord de traitement des données Render](https://render.com/dpa)
- [Conservation des journaux Render](https://render.com/docs/logging#retention-period)
