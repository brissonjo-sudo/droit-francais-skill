# Suite de la préparation — 10 octobre 2026

**Trace historique de la préparation de la PR #114, le 10/10/2026.** Les
525 tests, le client Gemini CLI et les observations de 16 sources ci-dessous
décrivent cette étape antérieure. Une observation documentaire ne prouve pas
la lecture du texte primaire ni sa vigueur. Le [bilan de relecture actuel](relecture-campagne-116.md)
distingue les preuves récupérées dans la session et les validations humaines
encore absentes ; le [protocole v2](campagne-18-modes.md) utilise un autre moteur Gemini.

La PR brouillon #114 poursuit maintenant la préparation des cas et des clients.
Le noyau du skill et le serveur de production sont inchangés.

## Résultat concret

Les 36 cas ont une question circonstanciée, une date utile, une proposition
de conclusion, des critères, une criticité et une réserve d'abstention ciblée.
Les observations de 16 sources officielles consultées et les 10 pièces
synthétiques sont incluses. Les contrôles des modes 15 à 18 utilisent des
pièces distinctes permettant une réponse positive sur la cohérence.

Le [dossier de revue](corriges-campagne-18-modes.md) est généré depuis le JSON
et porte son empreinte. Il n'altère aucune validation. Les 36 corrigés restent
en statut brouillon avec les champs humains vides. Le gel ne peut pas transformer
une proposition de corrigé en validation et la collecte demeure bloquée.

Le cas de versions utilise désormais les contenus différents de l'article
1240 du Code civil avant et après 2016. Le contrôle pénal oppose une extension
par analogie à l'assimilation de l'énergie au vol expressément prévue par la loi.
Les autres questions remplacent les invitations générales à « vérifier »
par des propositions et des faits précisément délimités.

## Clients et validation

Gemini CLI 0.63.0 est installé dans un dossier local ignoré ; sa version,
son aide et le lancement depuis Python sur Windows ont été vérifiés.
Aucune connexion Google ni requête de modèle n'a été effectuée. Les modèles
exacts et les réglages des trois familles ne sont pas figés.
Voir les [preuves et limites des clients](preparation-clients-campagne.md).

Les validateurs de documentation excluent maintenant les dépendances
node_modules et les sorties locales tests/bench/runs, tout en conservant
les fixtures du corpus. L'installation locale avait rendu visible cette
erreur de périmètre. Une non-régression vérifie que les vrais documents
et leurs erreurs restent contrôlés.

Validation locale : 525 tests réussis, compilation des fichiers du harnais
(hors sorties et dépendances tierces), corpus 36/18 avec 0 corrigé validé,
contrôles plugin, liens, affirmations, commandes et vault réussis.
Le statut CI du nouveau commit sera constaté séparément.
Les tests logiciels ne constituent ni une mesure d'utilité ni une revue juridique.

## Porte suivante

Relire le dossier, corriger puis valider humainement les 36 corrigés, fixer
les modèles exacts et qualifier les comptes. Après commit et gel, effectuer
les préflights, puis le pilote des modes 1, 3, 5 et 18. Une éventuelle
révision du corpus après pilote devra être commitée et gelée dans une nouvelle
série avant la campagne principale. Aucun exemple de réponse ne sera ajouté
au README avant mesure et revue humaine.
