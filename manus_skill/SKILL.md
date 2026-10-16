---
name: recherche-juridique
description: >-
  Méthodologie de recherche et d'analyse du droit français et européen à partir
  de sources officielles, avec contrôle de provenance, de version, de vigueur,
  d'applicabilité et de citation. Utiliser pour vérifier ou interpréter un texte,
  rechercher une jurisprudence, qualifier une situation juridique, rédiger ou
  auditer un acte, une note ou un document. Ne pas utiliser pour le droit
  étranger hors UE ni pour une question doctrinale sans enjeu normatif.
metadata:
  version: 3.5.0-manus
  base_version: 3.5.0
  langue: français
  adapted_for: Manus
---

# Recherche juridique — adaptation Manus de la base 3.5.0

## Objet et règle cardinale

N'inventer aucune référence juridique. Toute proposition normative, citation, date, montant, seuil ou délai doit être contrôlé à partir d'une source officielle effectivement consultée dans la session. Distinguer la provenance de la source, le contenu du texte, sa vigueur et son applicabilité aux faits. Si un élément décisif n'est pas vérifié, le signaler et s'abstenir sur ce point.

Cette adaptation est conçue pour les capacités disponibles dans Manus. Les noms d'outils, connecteurs, scripts PISTE et serveurs MCP du dépôt amont ne sont pas présumés disponibles.

## Déclenchement et modes

Activer ce skill dès qu'une demande porte notamment sur un texte normatif, une qualification juridique, la vigueur d'une règle, une décision juridictionnelle, un acte ou un écrit juridique, un concours avec références, ou la relecture/audit d'un document existant.

- **Mode A (défaut)** : appliquer le noyau et les modules déclenchés par la demande.
- **`[complet]` / mode B** : appliquer tous les modules et fournir une synthèse des contrôles et limites.
- **`[express]`** : réduire les recherches facultatives et la longueur de la réponse, jamais les contrôles du module **PÉNAL** ou **DOC-AUDIT**, ni la vérification d'une affirmation décisive.
- **`[lookup]`** : fournir une vérification ciblée et concise. Ne pas la traiter comme une dispense de vérifier la source primaire, la date et l'applicabilité.

En cas de doute sur le déclenchement d'un module, l'activer. Ne pas réciter le plan interne dans une réponse simple ; expliciter les contrôles lorsque le livrable, la complexité ou une limite le justifie.

## Principes invariants

**P1 — Source primaire.** Fonder toute affirmation normative sur le texte officiel publié ou la décision de la juridiction compétente. La doctrine privée peut aider au repérage, jamais constituer seule le fondement.

**P2 — Date et champ.** Identifier la date des faits, la date d'application demandée et le champ territorial. Distinguer publication, entrée en vigueur, version consultée et date d'évaluation. Une règle en vigueur aujourd'hui peut ne pas s'appliquer aux faits antérieurs ; lire les dispositions transitoires et les renvois utiles.

**P3 — Autorité et fonction.** Distinguer l'authenticité d'une source, le rang de la norme, l'autorité de la décision et sa fonction juridique (compétence, habilitation, procédure, sanction, définition, etc.). Ne pas confondre ces dimensions.

**P4 — Traçabilité de session.** Une référence historique, mémorisée ou incluse dans un fichier n'est pas une vérification actuelle. Ne restituer un identifiant ou un extrait comme vérifié que s'il a été récupéré dans la session depuis une source officielle. Des guillemets exigent le texte effectivement consulté.

**P5 — Registres séparés.** Séparer le droit positif, les faits établis, les faits allégués, les inférences, les hypothèses et les recommandations. Ne pas transformer une hypothèse ou une pratique locale en règle de droit.

**P6 — Légalité pénale.** En matière pénale, vérifier la norme applicable à la date des faits, les éléments légal, matériel et moral, les règles de procédure et les éléments de preuve. Ne pas étendre une incrimination par analogie défavorable.

**P7 — Abstention informée.** Une source inaccessible, incomplète, contradictoire ou non datée interdit de conclure sur la proposition qui en dépend. Indiquer précisément le point non établi, sans combler le manque par une estimation.

Pour prévenir les erreurs récurrentes (référence inventée, confusion de versions, article voisin, renvoi non résolu, mauvaise compétence ou conséquence excessive), consulter `references/modes-erreur.md` pour les travaux complexes ou à risque élevé.

## Procédure

### Étape 0 — Qualifier

Déterminer l'objet de la demande, le résultat attendu, le domaine et le régime possibles, les faits connus et manquants, les acteurs, le territoire et les dates pertinentes. Ne poser une question préalable que si une information manquante est décisionnelle ; sinon, annoncer une hypothèse limitée et conditionnelle.

### Étape 1 — Repérer puis lire les sources

1. Utiliser `search` pour repérer les sources officielles, en conservant autant que possible le code, l'article, l'identifiant, la juridiction et la date demandés.
2. Utiliser `fetch` pour ouvrir et lire la page officielle ou le texte intégral ; un extrait de recherche ne suffit pas. La recherche repère une source, elle ne confirme pas à elle seule le contenu.
3. Si une page est dynamique, mal extraite ou inaccessible, découvrir les outils de navigateur/MCP effectivement disponibles et leur schéma avant de les appeler. Ne jamais inventer le nom ou les paramètres d'un outil.
4. Si aucune voie ne permet une vérification suffisante, appliquer P7.

Prioriser les sources selon `references/sources-autorisees.md`. Ne pas présumer qu'un serveur MCP juridique personnalisé, une API Légifrance/Judilibre ou des identifiants PISTE sont connectés.

### Étape 2 — Vérifier texte, version et applicabilité

Pour chaque disposition déterminante :

- relever le texte et l'identifiant officiel effectivement trouvés, l'URL canonique et la date de consultation ;
- vérifier la version correspondant à la date utile, ses bornes de vigueur, une éventuelle abrogation, les modifications et les dispositions transitoires ;
- suivre les renvois nécessaires jusqu'aux textes d'application ou définitions utiles ;
- établir le champ territorial et matériel, les exceptions et les conditions cumulatives ou alternatives ;
- séparer `source consultée`, `version applicable à la date` et `conclusion sur les faits`.

Ne jamais remplacer silencieusement un identifiant historique fourni par l'utilisateur par la version actuelle. Un identifiant non récupéré dans la session n'est pas à reconstituer de mémoire.

### Étape 3 — Contrôler la jurisprudence pertinente

Rechercher les décisions officielles qui précisent, confirment ou contredisent l'interprétation lorsque la solution est contestable, contentieuse ou porteuse de conséquences importantes. Identifier la juridiction, la date, le numéro/ECLI s'il est récupéré, la formation et la portée utile. Distinguer le dispositif, le motif décisif et les observations incidentes ; vérifier les évolutions ultérieures lorsque nécessaire.

### Étape 4 — Qualifier et articuler

Appliquer les sources aux seuls faits établis. Examiner compétence, procédure, opposabilité, preuve, exceptions, régimes spéciaux, dispositions transitoires et conséquences opérationnelles. Pour une mesure administrative ou de police, analyser l'adaptation, la nécessité et la proportionnalité lorsque ces critères sont pertinents. Pour une interprétation controversée, trianguler les sources et présenter les objections sérieuses.

### Étape 5 — Rédiger et contrôler

Adapter le format au livrable. Une réponse simple donne la conclusion conditionnelle, la source officielle consultée, la date pertinente et les réserves utiles. Une note de fond, un audit ou `[complet]` expose les textes, leur fonction, la jurisprudence utile, l'application aux faits, les limites et les objections restantes.

Avant livraison, vérifier que chaque référence est issue de la session, que les citations correspondent au texte réellement lu, que les dates et montants ne sont pas extrapolés et qu'aucune hypothèse n'est devenue un fait.

### Étape 6 — Auto-critique ciblée

Tester la conclusion du point de vue d'un contradicteur, d'un juge ou contrôleur exigeant la preuve et, si pertinent, d'un praticien du métier concerné. Revenir à l'étape utile si l'un de ces contrôles révèle une faille. Ne pas afficher une auto-critique de pure forme.

## Voie spéciale : audit ou correction d'un document

Dès qu'un document existant est audité, relu ou corrigé, appliquer **DOC-AUDIT** avant toute conclusion. Lire intégralement `references/audit-documentaire.md`. Un audit antérieur ou une mention « validé » ne dispense jamais de revérifier les affirmations à risque élevé.

**Nouveautés intégrées de la v3.5.0 :**

- Si le document recommande de couper, retirer, évacuer, détruire, confisquer ou attribuer à une personne publique un bien privé, examiner séparément le fondement de cette exécution forcée d'office. Vérifier l'habilitation expresse ou l'urgence invoquée ; à défaut, examiner les conditions juridiques pertinentes (notamment absence d'autre voie de droit ou sanction, base légale de la décision, résistance de l'intéressé et stricte nécessité), le régime sectoriel et la jurisprudence officielle avant de conclure. Une interdiction, une contravention ou une clause locale ne suffit pas, à elle seule, à établir le pouvoir de disposer du bien.
- Distinguer systématiquement **classe de contravention**, **maximum légal encouru** et **amende forfaitaire** éventuellement applicable. Vérifier chacun séparément ; aucun ne se déduit automatiquement des autres.

Ces contrôles sont des déclencheurs d'analyse, non une conclusion automatique sur la légalité de l'opération. Vérifier les textes et la jurisprudence en vigueur pour le cas concret.

## Modules

Lire `references/modules.md` dès qu'un module est déclenché. En cas de doute, l'activer. **PÉNAL** et **DOC-AUDIT** restent obligatoires en mode `[express]`.

- **PÉNAL** : infraction, peine, contravention, visa pénal, procès-verbal ou qualification pénale.
- **ACTE-ADMIN** : rédaction ou contrôle d'un acte administratif, décision, arrêté, mesure de police, sanction ou refus.
- **PA-PJ** : opération pouvant relever de la police administrative ou judiciaire ; qualifier finalité, autorité, temporalité et procédure.
- **FOND** : note de fond, concours, acte officiel ou interprétation controversée.
- **CONTENTIEUX** : risque de recours, stratégie procédurale, voie de droit, délai ou recevabilité.
- **DOC-AUDIT** : audit, relecture, correction ou contrôle d'un document/corpus ; lire le protocole dédié.

## Format de référence et abstention

Lorsque disponible et pertinent, accompagner toute référence de :

- juridiction/autorité et identifiant officiel récupéré ;
- intitulé ou objet exact et URL canonique ;
- date de la version ou de la décision et date de consultation ;
- date à laquelle l'applicabilité est appréciée ;
- fonction juridique de la disposition et réserve éventuelle.

Ne pas imposer un format long à une réponse brève si cela nuit à la lisibilité, mais ne jamais omettre les informations nécessaires pour retrouver et contrôler la source.

Employer exactement cette réserve lorsqu'une source déterminante n'a pas pu être confirmée : **« Source non confirmée — abstention sur ce point. »** Préciser ensuite ce qui manque et quelle vérification permettrait de conclure.

## Mise à jour et installation

Le dépôt décrit le skill mais n'effectue pas son installation dans un compte Manus. Ne pas lancer `npx skills update` ni modifier les fichiers du compte pour une installation gérée par Manus ; suivre le mécanisme de mise à jour de l'hôte. N'utiliser un gestionnaire CLI que si le skill est effectivement installé et suivi par ce gestionnaire, et si l'utilisateur l'a demandé ou a activé explicitement son mode automatique.
