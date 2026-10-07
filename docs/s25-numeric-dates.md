# S25 — dates numériques dans les sections consolidées

Le préflight DPM v8 reçoit une section complète, mais ses dix articles portent
des bornes brutes en millisecondes Unix. Le normaliseur des consultations
acceptait uniquement ISO, contrairement à la lecture d'article simple.
La datation et l'ancre ne pouvaient donc pas être attestées par l'oracle.

Correctif ciblé dans `texts._metadata` : accepter les nombres comme
millisecondes depuis l'époque UTC, avec `datetime` et `timedelta` pour ne pas
dépendre de la plage du `gmtime` système. Les champs bruts sont conservés.
Les booléens, valeurs non finies, dépassements, chaînes numériques et dates
malformées restent non attestés. Les bornes manquantes restent non attestées,
la fin demeure exclusive et une date future ou expirée demeure inapplicable.

Référence technique consultée avant modification : Context7 `/python/cpython`,
documentation officielle Python `datetime` (`timedelta`, `timezone.utc`,
limites de `fromtimestamp`). Aucun contrat d'outil, oracle, cible, ID, contenu
juridique, secret, mécanisme OAuth ou plafond de consultation n'est modifié.

Tests hors réseau : `tests/test_section_numeric_dates.py` (huit méthodes),
suite de consultation existante et contrôles complets du dépôt. La reproduction
des dix bornes du run v8 est une simulation locale, pas une récupération live
et pas une qualification juridique ou de campagne.
