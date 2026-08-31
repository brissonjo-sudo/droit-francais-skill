# Registre des obligations — Légifrance et Judilibre

─────────────────────────────────────────────
Date d'analyse           : 31/08/2026
Date(s) de référence     : 15/12/2022 (Légifrance, document à obtenir) / 06/01/2022 (Judilibre)
Date des faits           : sans objet
Date d'action / analyse  : 31/08/2026
Champ territorial        : France
Régime juridique primaire: contrats d'accès API et réutilisation de données
Niveau d'exigence        : note de fond
Mode opératoire          : B complet
─────────────────────────────────────────────

Ce registre concerne l'exploitant qui utilise ses propres clés PISTE. Il ne
transfère pas les clés ni la qualité de titulaire à l'utilisateur final.

## 1. État des sources et règle d'abstention

| Source | État vérifié au 31/08/2026 | Conséquence |
|---|---|---|
| Catalogue officiel PISTE Légifrance | Référence `CGU_Legifrance_API_VF_15-12-2022`, API 2.4.2 | Source courante identifiée |
| PDF `DILA_Legifrance_Beta_v2.pdf` | V1.1 du 04/08/2020 | **Historique, supersédé : ne fonde plus une conclusion de conformité** |
| Texte intégral Légifrance 15/12/2022 | Non accessible anonymement pendant l'audit | **Blocage** : obtenir depuis le compte PISTE, dater, calculer SHA-256 et comparer |
| CGU Judilibre | PDF officiel, version du 06/01/2022 (`CGU_open_data_V8`) | Référentiel public contrôlable |
| Licence Ouverte 2.0 | Texte officiel Etalab | Référentiel de réutilisation |

Tant que le texte Légifrance 2022 n'est pas archivé, les règles Légifrance
ci-dessous issues du document 2020 sont des **hypothèses conservatoires à
revalider**, pas des obligations actuelles déclarées comme certaines. Le
mainteneur doit conserver, pour chaque revue : fichier source, URL ou origine
PISTE, date/heure, SHA-256, version, auteur de la vérification et diff.

## 2. Contrôles communs — statut provisoire côté Légifrance

| ID | Contrôle appliqué au service | Judilibre 2022 | Légifrance 2022 | État technique |
|---|---|---|---|---|
| C1 | Clés réservées à l'application, jamais envoyées au client | Confirmé XI.C | À vérifier | Secrets Render, masquage d'erreur |
| C2 | Sécuriser environnement et identifiants | Confirmé XI.C/XI.E | À vérifier | Conteneur non-root ; audit supply-chain ouvert |
| C3 | Détecter incident, réinitialiser les clés et notifier rapidement | Confirmé XI.E | À vérifier | Runbook créé, exercice à faire |
| C4 | Respecter les quotas accordés et leurs changements | Confirmé XI.D | À vérifier | Limiteurs locaux ; quota global ou mono-réplica requis |
| C5 | Usage licite et responsabilité du réutilisateur | Confirmé XII | À vérifier | Conditions publiques |
| C6 | Ne pas altérer/dénaturer, mentionner source et mise à jour | Confirmé V/XIII + LO 2.0 | À vérifier | Provenance structurée ; contrôle des champs ouvert |
| C7 | Ne pas transformer une panne en vérification réussie | Confirmé XI.A | À vérifier | Erreur « source officielle non vérifiée » |
| C8 | Prévoir suspension ou indisponibilité de l'accès | Confirmé XII | À vérifier | Dégradation documentée, pas de clé de secours automatique |

## 3. Judilibre — affirmations vérifiées

| ID | Nature | Règle | Contrôle du service |
|---|---|---|---|
| J1 | Contractuelle/légale | Ne pas profiler magistrats ou membres du greffe à partir de leur identité | Fonction absente et usage interdit |
| J2 | Contractuelle/légale | Ne pas réidentifier les personnes occultées ou pseudonymisées | Usage interdit ; aucune base de rapprochement |
| J3 | **Recommandation forte** | Section VII : le réutilisateur est **invité** à signaler une réidentification manifeste persistante à `anonymisation.sder.courdecassation@justice.fr` | Canal et runbook proposés ; ne pas présenter comme engagement contractuel |
| J4 | **Obligation contractuelle** | Section IX : transmettre sans délai une demande relative à un défaut d'occultation des nom/prénoms et effectuer une occultation socle provisoire | Retrait complet temporaire via `MCP_JUDILIBRE_SUPPRESSED_IDS`, relais immédiat, levée après correction amont |
| J5 | Compétence exclusive | Les demandes d'occultation/levée relèvent de la Cour de cassation ; le réutilisateur n'en décide pas seul | Orientation vers `occultations.courdecassation@justice.fr` ; aucune altération autonome |
| J6 | Contractuelle | Juridiction, formation, siège et date du prononcé restent indissociables de la décision | Champs renvoyés lorsqu'ils existent ; test de complétude à poursuivre |
| J7 | Contractuelle | Mention « base Open Data de la Cour de cassation » et date de dernière mise à jour ; recommandation 72 h pour une base dérivée | Source exacte + date amont si fournie + date de récupération ; aucune base dérivée |
| J8 | Information RGPD | Accès/rectification du traitement Judilibre auprès du SDER | Renvoi dans la politique de confidentialité |

### Mesure conservatoire J4

Le service ne doit pas inventer une occultation ni modifier la décision. Dès
qu'un signalement crédible vise une décision :

1. ajouter son identifiant à `MCP_JUDILIBRE_SUPPRESSED_IDS` sur Render ;
2. redémarrer et vérifier que recherche et lecture ne la redistribuent plus ;
3. transmettre sans délai le signalement à la Cour de cassation selon
   `incident-response.md` ;
4. conserver une preuve privée minimale, sans recopier les données exposées ;
5. retirer l'identifiant uniquement après correction de la source et contrôle.

La suppression complète est une mesure temporaire et conservatrice : elle est
plus restrictive que l'occultation socle, mais évite au service d'exercer la
compétence d'occultation réservée à la Cour.

## 4. Légifrance — registre suspendu jusqu'au texte 2022

Les points suivants figuraient dans le PDF 2020 : confidentialité des clés,
sécurité de l'environnement, quotas, notification d'incident, Licence Ouverte,
contact du compte PISTE et données du développeur. Ils restent appliqués par
prudence mais doivent chacun recevoir, après récupération du PDF 2022 :

- la section exacte et une paraphrase contrôlée ;
- les différences avec 2020 ;
- la conséquence précise pour ce service public avec utilisateurs tiers ;
- l'état `confirmé`, `corrigé`, `supprimé` ou `à arbitrer`.

Jusqu'à cette revue, écrire « conforme aux CGU Légifrance » est interdit.

## 5. Points restant à vérifier

- texte intégral et empreinte des CGU Légifrance 15/12/2022 ;
- quotas exacts attachés aux deux abonnements PISTE ;
- valeurs effectivement présentes dans les réponses Judilibre pour siège et
  date de mise à jour ;
- délai de rétention et accès aux pseudonymes des journaux Render ;
- exercice chronométré du retrait J4 et de la rotation des clés.

## Sources primaires

- [Catalogue PISTE — Légifrance](https://piste.gouv.fr/api-catalog-sandbox?filter=legifrance)
- [CGU Judilibre du 6 janvier 2022](https://piste.gouv.fr/images/cgu/CGU_open_data_V8.pdf)
- [Licence Ouverte 2.0](https://www.etalab.gouv.fr/licence-ouverte-open-licence)
- [Ancien PDF Légifrance 2020 — archive seulement](https://piste.gouv.fr/images/cgu/DILA_Legifrance_Beta_v2.pdf)

## Étape 7 — Auto-critique adversariale

- Le catalogue prouve l'identifiant de la version Légifrance, pas son contenu.
- Le retrait complet d'une décision réduit la diffusion mais ne remplace pas la
  transmission sans délai à la Cour de cassation.
- Les champs absents d'une réponse Judilibre ne doivent pas être inventés.

─────────────────────────────────────────────
Modules activés                       : [DOC-AUDIT]
Modules non activés                   : [PÉNAL, ACTE-ADMIN, PA-PJ, FOND, CONTENTIEUX]
Niveau de confiance global            : modéré
Sources informelles signalées         : aucune
Limites de la recherche               : contenu intégral des CGU Légifrance 2022 non obtenu
─────────────────────────────────────────────
