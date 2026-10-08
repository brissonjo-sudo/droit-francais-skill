# S28 : candidat soumis à revue, confirmation stricte des versions morte-nées

Statut au 8 octobre 2026 : candidat soumis à revue dans la
[PR #112](https://github.com/brissonjo-sudo/droit-francais-skill/pull/112),
non fusionné et non qualifié en réel. L'étape locale initiale du 7 octobre
n'autorisait pas de PR ; les accords ultérieurs ont permis sa création,
son passage en revue puis les retouches ciblées et leurs contrôles locaux.
Aucune fusion, aucun déploiement ni sonde live autorisés dans cette étape.

La vérification officielle du 7 octobre a observé `MODIFIE_MORT_NE` et les
bornes inversées de l'article identifié. Elle n'exposait pas le parent brut
et ne qualifiait pas la section complète. Aucun identifiant réel n'est codé
en dur ; les fixtures des tests sont exclusivement synthétiques.

## Décision

Le routeur générique `_active` reste strict. Pour un lien **article** aux
bornes strictement inversées, l'état du lien doit être absent ou explicitement
`MODIFIE_MORT_NE`. Un état présent différent, des bornes illisibles/égales,
un ID invalide/dupliqué, une version/contexte/lien de section invalide refusent.

Le candidat est inventorié avant toute lecture de corps. Le plan d'admission
compte sections, articles actifs et vérifications de versions. Les confirmations
utilisent l'appel `getArticle` existant, après admission de toutes ces requêtes,
avant les corps actifs. Elles comptent dans tous les budgets cumulés.

L'exclusion exige l'ID exact, l'état officiel `MODIFIE_MORT_NE`, les mêmes
valeurs **et types** de bornes brutes, la section parent exacte (avec gestion
XML déjà existante), le texte parent et le contexte daté. Un champ parent
direct contradictoire interdit cette nouvelle exclusion, même si un autre
champ direct est correct. L'absence des champs directs exige toujours le
contexte daté et la section exacte. Toute incohérence reste un refus.
Si la confirmation échoue, le refus reste explicite même si `_active`
cessait de lever sur un intervalle inversé ; aucune trace d'exclusion
ni lecture de corps actif ne doit alors être produite.

La version exclue reste inventoriée avec ID, état, bornes, chemin et preuve
de rattachement dans `metadata.excluded_article_versions`. Son corps n'est
jamais rendu. Le lien amont n'est ni supprimé ni réparé. Les octets de la trace
sont contrôlés dans le volume de restitution ; les octets/nœuds du corps de
confirmation sont comptés dans le volume cumulé des réponses officielles.

Un lien ordonné annonçant une version morte-née ou un corps actif portant cet
état sont refusés, sans déduction d'une substitution. Une section sans contenu
actif n'est pas déclarée complète uniquement parce qu'une exclusion est validée.

## Plafonds et limites de qualification

Inchangés : 67 requêtes, 90 secondes, 5000 nœuds, 2 000 000 octets, profondeur 32.
Tous les contrôles de complétude existants restent appliqués aux confirmations.
Le garde AST des tests diagnostiques est conservé, et le nouveau fichier de
tests possède son propre contrôle de doublons.

Context7 a confirmé la route existante `/consult/getArticle`, mais n'a pas
fourni le schéma du statut du lien. Le code n'invente ni nouveau champ ni route.
Il confirme systématiquement l'état via l'article ; il ne présume pas que le
lien contient ce champ. Une visite web documentaire a échoué (403), sans
remplacer la documentation officielle par une affirmation non vérifiée.

S28 reste non qualifié en réel : son rattachement complet, son volume et le
temps requis doivent encore être mesurés sur le runtime livré après accord.
La qualification locale ne transfère aucun résultat historique au candidat.
