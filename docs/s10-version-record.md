# S10 — identité du record XML et CID distincts

Le 5 octobre 2026, la première sonde après PR 104 atteint la voie structurée,
mais refuse le record `LEGISCTA000028286713.xml`. Le CID demandé a déjà été
contrôlé dans la liste officielle ; le refus porte sur la représentation de
l'ID de version. Cette sonde négative reste conservée dans le dossier DPM.

La reconnaissance d'un nom de record est limitée à
`LEGISCTA` + douze chiffres + suffixe exact `.xml`. Son identifiant canonique
est la base du record retourné, **pas le CID du demandeur**. Le record brut et
le CID restent distincts et tracés. Les IDs sans suffixe suivent le contrat
existant. Aucun statut juridique n'est déduit d'un nom de fichier.

La liste des versions doit toujours porter le CID demandé, avoir une seule
version applicable et un contexte parent daté conforme. Pour les descendants,
l'ID doit toujours correspondre exactement au lien officiel. Les articles
doivent être liés à l'ID de version canonique ou au record brut, pas à un CID
substitué. Dates, inventaires, complétude, budgets et plafonds sont inchangés.

Trois tests synthétiques supplémentaires contrôlent identité distincte,
provenance, mauvais CID/contexte/date/suffixe et mauvais rattachement d'article.
Le test historique de mauvais CID porte désormais sur un CID réellement
différent, plutôt que sur un ID de version distinct avec CID conforme.
Cela n'établit pas de preuve live : une nouvelle sonde figée doit encore passer
le vérificateur DPM original, y compris l'ancre S10. Aucun résultat métier ou
release juridique n'est qualifié par ce correctif.
