# Instrumentation locale S30 — non déployée, 09/10/2026

Le candidat ajoute une trace diagnostique à `get_text` uniquement pour le
texte `LEGITEXT000005627880` à la date explicite `2026-10-05`. Aucune signature
MCP ni requête API ne change ; aucune consultation supplémentaire n'est faite.

La métadonnée `source_dating_diagnostic` observe les champs directs de la
section `LEGISCTA000006098957`, après les contrôles existants et le calcul
de datation. Elle distingue champ absent, null et type de valeur. Les nombres
finis bornés et les dates ISO strictes peuvent être conservés à l'identique ;
les chaînes libres, booléens, objets ou valeurs illisibles ne sont pas émis.
Cette trace ne convertit aucune borne ni ne fournit de valeur de remplacement.

Les noms de clés sont à liste blanche ; les autres sont seulement comptés.
Leur nom ou contenu, les corps d'articles et les en-têtes sont exclus. Le
périmètre n'inclut pas les champs imbriqués de contexte : une trace directe
ne permet pas d'affirmer qu'aucune autre datation n'existe dans la réponse.
La trace est plafonnée à 4 096 octets ; une limite n'est pas masquée par une
troncature prétendument complète.

Les champs explorés `dateDebutVersion`, `dateFinVersion`, `debut` et `fin`
ne sont pas déclarés équivalents à `dateDebut` et `dateFin`. L'absence de
bornes attendues continue de produire une applicabilité inconnue. Les refus,
la datation agrégée et les plafonds de consultation restent inchangés.

Les tests utilisent des corps et dates simulés, même lorsque le sélecteur
S30 est réel. Ils ne constituent pas une réponse brute Légifrance. La
réponse brute n'a pas été reçue lors du diagnostic du 09/10/2026 ; aucune
cause amont ni correction de mapping n'est démontrée par ce candidat.

Avant toute lecture réelle : revue du diff, autorisation séparée de livraison,
CI et SHA déployé vérifiés, puis une seule lecture diagnostique autorisée.
Aucune campagne, publication ou qualification juridique n'est accordée ici.
