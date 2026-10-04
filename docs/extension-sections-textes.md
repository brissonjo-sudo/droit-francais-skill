# Extension locale : sections CODE et textes consolidés LEGI

Préparée le 4 octobre 2026. **Non déployée, non publiée et non qualifiée en
lecture métier réelle**. La connexion distante existante expose encore six
outils : aucun résultat de campagne DPM n'est débloqué par ce correctif local.

## Contrat vérifié avant implémentation

Le [catalogue public PISTE](https://piste.gouv.fr/api-catalog-sandbox) annonce
Légifrance 2.4.2, API `7e5a0e1d-ffcc-40be-a405-a1a5c1afe950`. Les modèles
publics ont été lus via la requête de documentation du portail :

```text
https://piste.gouv.fr/index.php?option=com_apiportal&task=ajaxrequest.swaggerLoad&apiId=7e5a0e1d-ffcc-40be-a405-a1a5c1afe950&managerId=3&Itemid=179&renderTool=1&swaggerVersion=1.1
```

Ce n'est pas un appel métier ni une preuve du contenu d'une loi. La
[FAQ officielle Légifrance](https://www.legifrance.gouv.fr/contenu/pied-de-page/foire-aux-questions-api)
confirme la consultation des textes par `legiPart`. Le contrat technique
courant du portail, plus précis que l'exemple de la FAQ, est retenu.
La [documentation du SDK MCP](https://py.sdk.modelcontextprotocol.io/v2/api/mcp/server)
a été consultée via Context7 ; le décorateur et les annotations existants
restent utilisés. Les dépendances épinglées ne changent pas.

| Outil local | Endpoint officiel | Requête | Réponse |
|---|---|---|---|
| `get_section(id, text_id, date?)` | `/consult/code` | `CodeConsultRequest` : `textId`, `sctCid`, `date` ISO | `ConsultTextResponse` ; extraction du seul sous-arbre dont `id` ou `cid` correspond |
| `get_text(id, date?)` | `/consult/legiPart` | `LegiConsultRequest` : `textId`, `date` ISO | `ConsultTextResponse` ; articles racine et sections récursives |

## Périmètre et garde-fous

- `LEGISCTA` et `LEGITEXT` : préfixe exact suivi de douze chiffres. Pas d'URL
  arbitraire, de parent deviné ou d'autre source réseau.
- Sections **CODE uniquement**. Textes **consolidés LEGI**, pas JORF initial,
  ni section LODA, ni code entier servi sous forme de simple sommaire.
- La date omise utilise l'horloge du serveur ; la date demandée est tracée.
  Le véritable identifiant de version retourné est conservé. Une identité de
  texte différente, une section absente ou ambiguë entraîne un refus.
- `verified: true` signifie réponse officielle reçue, **pas droit en vigueur**.
  L'applicabilité est contrôlée sur chaque élément ; une borne manquante ou
  illisible reste indéterminée. Une version expirée parmi les descendants
  empêche une affirmation globale de vigueur.
- Arborescence, notes, articles et ordre `intOrdre` sont conservés. Le texte
  rendu est nettoyé du HTML : ce n'est pas une reproduction de la mise en page.
  La complétude est limitée à la réponse API, **hors documents liés externes**.
- Aucun sommaire sans contenu d'article n'est présenté comme lecture complète.
  Une section explicitement sans dispositions peut porter son commentaire.
  Une continuation, une marque d'incomplétude ou une limite dépassée déclenche
  une erreur, jamais une troncature silencieuse.
- Limites internes : 5 000 éléments d'arborescence, profondeur 32, réponse
  API de 2 000 000 octets maximum. Pas de pagination inventée : ces endpoints
  de consultation n'en définissent pas dans leur contrat.
- Toutes les lectures passent par `_safe_call` : OAuth, limitation de charge,
  masquage des secrets et erreurs « source officielle non vérifiée » inchangés.
- `fetch(LEGITEXT...)` est routé vers `get_text`. Une section sans parent ou
  un texte JORF est refusé plutôt qu'envoyé à Judilibre.

## Validation locale et prochaine porte

Résultats du 4 octobre 2026 : **363 tests unitaires réussis**, dont 23 nouveaux
tests de consultation ; protocole stdio et HTTP local : **huit outils** et
annotations conformes. Socle plugin, liens, vault, affirmations et commandes
documentées : contrôles réussis. Le corpus du benchmark reste lisible, mais
signale `get_decision`, `get_section` et `get_text` non couverts : **aucun
benchmark comportemental ni qualification de release** n'en est déduit.

Environnement séparé : Python 3.13, MCP 2.2.0, PyJWT 2.14.0, sans modification
de Python global. Le contrôle initial avec MCP 1.27 a montré deux imports
manquants et deux échecs de métadonnées OAuth ; il ne constitue pas le verdict
du SDK épinglé. La première copie a été invalidée pour mauvais encodage d'un
chemin Git et configuration de test incorrecte. La preuve finale concerne la
copie `v3`, sans `.env`. Les fichiers de code testés et originaux ont les mêmes
empreintes ; les ajouts documentaires postérieurs ne modifient pas ces fichiers.

Traces locales conservées dans le projet DPM :

```text
tests/isolation/r7-connecteur-local-env/
tests/isolation/r7-connecteur-local-source-v3/tests-unitaires.log
tests/isolation/r7-connecteur-local-source-v3/protocole-http.log
```

SHA-256 du module `texts.py` testé :
`85d118ba287f877d9167bfa25308738965215ad75968326cd9a860f49a974d68`.
Ces traces ne sont pas dans le package du plugin. Le serveur HTTP de test
a été arrêté après la sonde ; aucun processus de production n'a été touché.

`tests/test_text_consultation.py` utilise des identifiants **synthétiques** et
des réponses simulées, jamais des références juridiques à citer. La suite
vérifie le contrat, les versions, les identités, les erreurs, les limites,
l'extraction ciblée et les garde-fous du serveur. La sonde de protocole stdio
contrôle les huit outils réellement enregistrés et leurs annotations.

La sonde métier `tests/check_live_tools.py` est adaptée aux huit outils, avec
les identifiants du corpus DPM ; elle **n'est pas exécutée contre le service
distant** dans cette préparation. Le dossier de soumission est synchronisé
localement, sans nouvelle soumission. Les cinq scénarios positifs historiques
ne constituent pas une qualification live des deux nouveaux outils.

Avant tout déploiement : revoir le diff, décider de la version publiée,
qualifier l'image et autoriser explicitement le déploiement. Ensuite seulement :
découvrir le catalogue distant, sonder réellement les deux nouvelles lectures,
préparer un nouvel essai de préflight DPM sans écraser les tentatives bloquées.
Les autres sources du corpus (CE, CNIL, préfecture…) restent leurs propres
portes ; leur accessibilité n'est pas prouvée par cette extension.
