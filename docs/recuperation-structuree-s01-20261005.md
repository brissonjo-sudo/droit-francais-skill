# Récupération structurée des sections CODE — 5 octobre 2026

## Motif et contrat

Après bascule de la PR 93, la sonde native S01 constate un dépassement du
parent `/consult/code` : au moins 5 003 nœuds, plafond 5 000, référence
`2ae8dfdf`. Cette preuve négative est conservée côté DPM dans
`tests/isolation/r7-s01-pr93-v1/`. Aucun corps partiel n'est exploité.

Le [Swagger public PISTE](https://piste.gouv.fr/api-catalog-sandbox), API
Légifrance 2.4.2, décrit `/consult/getSectionByCid`, `SectionCidRequest.cid`,
`GetListSectionResponse.listSection`, les liens d'enfants versionnés et
`/consult/getArticle`. Context7 interrogé n'a pas de documentation spécifique
à ces modèles ; le contrat officiel public a été consulté directement.

## Parcours et garanties

Le chemin habituel `/consult/code` reste inchangé. Un refus de **nœuds**
seulement permet d'engager ce parcours alternatif explicite, toujours sur
l'API officielle. Aucun repli sur erreur d'authentification, troncature,
datation ou schéma ; aucune nouvelle source, pagination ou URL de lien suivie.

Le corps parent refusé est abandonné : seules identité et titre sont
retenus, après contrôle d'identité. Les versions de la section sont relues
par CID ; exactement une doit couvrir la date demandée. Son contexte
doit attester son rattachement daté au texte parent. Les listes d'articles
et sous-sections sont obligatoires. Tous les liens couvrant la date sont
lus ; tout lien illisible, enfant absent, mauvais parent, version ambiguë
ou identité dupliquée provoque un refus sans résultat partiel.

Pour chaque article, ID exact, parent section, texte parent, contexte et
période sont recoupés. Sous-sections récursives : CID et ID du lien contrôlés.
Le statut juridique manquant demeure `UNKNOWN` : il n'est pas inventé
à partir des seules dates. Notes, corps et ordre restent normalisés.

Plafonds **inchangés** : 2 000 000 octets JSON, 5 000 nœuds, profondeur 32.
Ils s'appliquent à chaque réponse, à l'assemblage et aux totaux cumulés des
réponses alternatives. Deux garde-fous supplémentaires : 64 requêtes au
maximum, budget vérifié avant chaque requête de 50 secondes, appels espacés
de 1,1 seconde. Le transport conserve ses délais/reprises déjà bornés ; une
requête en cours peut finir après le budget, mais aucune suivante n'est lancée.
Le transport HTTP n'est pas transformé en lecture streaming.

La métadonnée `endpoint` conserve la consultation initiale `/consult/code` ;
`primary_consultation_refused`, `retrieval_strategy=official_structure_links`,
`content_endpoints` et `source_calls` indiquent sans ambiguïté que le corps
complet provient des lectures de structure/articles, pas du parent refusé.
Le contrôle de complétude ne transforme pas une table des matières en texte.

## Tests avant livraison

Copie Windows/Python 3.13 sans `.env` réel, environnement isolé existant.
**393 tests réussis**, dont 15 nouveaux cas de structure. Ruff et contrôles
plugin/liens/vault/affirmations/commandes passent. Les tests sont synthétiques,
pas une preuve de déblocage réel. CI distante et nouvelle sonde datée S01
requises avant conclusion ; aucune campagne métier ou qualification stable
ne se déduit de la seule remise de ce correctif.

Code : [`sections.py`](../skill/scripts/droit_francais/sections.py),
intégration [`texts.py`](../skill/scripts/droit_francais/texts.py), tests
[`test_structured_sections.py`](../tests/test_structured_sections.py).

## Diagnostic après première sonde

La PR 94 est en service mais S01 reste refusé (référence `11aa2921`) pour
une identité invalide ou dupliquée. Le correctif de diagnostic distingue
ces causes et n'affiche que les identifiants de nomenclature publique
bornée ; toute autre chaîne est masquée. Aucun contrôle d'identité n'est
assoupli. Cette étape n'est pas une preuve de déblocage.

Le diagnostic PR 96 précise un identifiant de 24 caractères, CID de S01
suivi d'un séparateur et de trois lettres. Une correspondance d'index
limitée `CID + _VIG` est ajoutée : identité juridique conservée au CID,
identifiant brut gardé dans `source_record_id`. Elle ne déduit aucun statut
juridique, ne remplace aucune borne ni preuve de parent et refuse les autres
suffixes. La nouvelle sonde réelle doit établir si cette forme correspond
bien au retour officiel et si le corps complet satisfait les contrôles.

Les sondes réelles après PR 97/98 n'ont pas confirmé `_VIG` / `_vig`.
Ces correspondances sont retirées : seule la forme fichier `CID + .xml`
est désormais examinée, sans changer le CID juridique ni aucune autre
condition. Le brut est conservé pour confirmation par la sonde réelle.
