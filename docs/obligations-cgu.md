# Registre des obligations — Légifrance et Judilibre

─────────────────────────────────────────────
Date d'analyse           : 31/08/2026 ; revue Légifrance le 25/10/2026
Date(s) de référence     : 15/12/2022 (Légifrance, V1.0) / 06/01/2022 (Judilibre)
Date des faits           : sans objet
Date d'action / analyse  : 25/10/2026
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
| Texte intégral Légifrance 15/12/2022 | Obtenu le 25/10/2026 depuis le compte PISTE du mainteneur : `CGU_Legifrance_API_VF_15-12-2022.pdf`, V1.0, 9 pages, SHA-256 `9db9cde0dac918721eac7508f76ea47ebfd0b2a7822db3ad9b41bb11629851fd` | **Blocage levé** : source courante, analysée en section 4 |
| CGU Judilibre | PDF officiel, version du 06/01/2022 (`CGU_open_data_V8`), SHA-256 `73f99f811475a0f9c7eb3e18ff431c37a41672e4c549fce64415eae71a713554` (copie du 25/10/2026) | Référentiel public contrôlable |
| CGU de la plateforme PISTE | Non lues | Partie intégrante des CGU Légifrance (I.1) ; à archiver et analyser |
| Licence Ouverte 2.0 | Texte officiel Etalab | Référentiel de réutilisation |

En cas de contradiction, les CGU de l'API Légifrance prévalent sur les CGU
PISTE, les mentions légales et la Licence Ouverte (I.1). Le mainteneur doit
conserver, pour chaque revue : fichier source, URL ou origine PISTE,
date/heure, SHA-256, version, auteur de la vérification et diff.

## 2. Contrôles communs

| ID | Contrôle appliqué au service | Judilibre 2022 | Légifrance 2022 | État technique |
|---|---|---|---|---|
| C1 | Clés réservées à l'application, jamais envoyées au client | Confirmé XI.C | Confirmé III.3 | Secrets Render, masquage d'erreur |
| C2 | Sécuriser environnement et identifiants | Confirmé XI.C/XI.E | Confirmé III.3/V.2 (état de l'art CNIL/ANSSI, recommandations PSSIE) | Conteneur non-root ; audit supply-chain ouvert |
| C3 | Détecter incident, réinitialiser les clés et notifier rapidement | Confirmé XI.E | Confirmé V.3 (DILA et/ou AIFE) | Runbook créé, exercice à faire |
| C4 | Respecter les quotas accordés et leurs changements | Confirmé XI.D | Confirmé IV.3 (par application ou par méthode, modifiables) | Limiteurs locaux ; quota global ou mono-réplica requis |
| C5 | Usage licite et responsabilité du réutilisateur | Confirmé XII | Confirmé V.1/VI.2 (avec garantie de la DILA) | Conditions publiques |
| C6 | Ne pas altérer/dénaturer, mentionner source et mise à jour | Confirmé V/XIII + LO 2.0 | Corrigé : renvoi à la LO 2.0 (V.1, IX) ; pas d'interdiction d'altérer propre au texte | Provenance structurée ; contrôle des champs ouvert |
| C7 | Ne pas transformer une panne en vérification réussie | Confirmé XI.A | Corrigé : règle du service, fondée sur IV.1 et VI.1 (aucune garantie de disponibilité ni de fiabilité) | Erreur « source officielle non vérifiée » |
| C8 | Prévoir suspension ou indisponibilité de l'accès | Confirmé XII | Confirmé IV.1/VII.1 | Dégradation documentée, pas de clé de secours automatique |

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

## 4. Légifrance — affirmations vérifiées (CGU du 15/12/2022)

Revue du 25/10/2026 sur le texte intégral (section 1). Paraphrases contrôlées ;
la comparaison détaillée avec le PDF 2020 n'a pas été refaite.

| ID | Section | Règle | Conséquence pour le service | État |
|---|---|---|---|---|
| L1 | III.3 | Clés strictement réservées à l'application, jamais publiées ni divulguées à un tiers | Le service hébergé appelle l'API pour ses utilisateurs ; aucune clé n'est remise à un client | Confirmé |
| L2 | VI.2, IX | La Licence Ouverte 2.0 autorise l'usage commercial des données, aux risques de l'utilisateur | Une offre payante est permise ; la responsabilité envers les clients repose sur l'exploitant | Confirmé |
| L3 | IV.1 | Aucune disponibilité minimale garantie ; objectif de moyens de 95 % par jour en production, aucun en sandbox | Aucun engagement de disponibilité client ne peut couvrir l'amont ; exclusion à prévoir au contrat | Confirmé |
| L4 | VI.1 | Fiabilité, complétude et fraîcheur non garanties ; seuls les PDF signés du Journal officiel sont opposables | Mention obligatoire dans les conditions d'utilisation et le dossier de preuve | Confirmé — mention à vérifier dans `terms-of-use.md` |
| L5 | IV.3 | Quotas par seconde, minute ou jour, par application ou par méthode, modifiables avec information par courriel | Quota par client et surveillance de consommation nécessaires avant plusieurs clients | Confirmé |
| L6 | V.1 | Usage conforme aux lois, à la LO 2.0 et au RGPD ; l'utilisateur garantit la DILA contre toute action | Risque contractuel porté par l'exploitant | Confirmé |
| L7 | V.3, VIII | Incident ou compromission : réinitialiser les identifiants et prévenir la DILA et/ou l'AIFE ; notifications vers `retours-legifrance-modernise@dila.gouv.fr` | Contact à reporter dans `incident-response.md` | Confirmé |
| L8 | VII.1 | Suspension sans notification préalable et résiliation sans préavis en cas de manquement | Point de défaillance unique ; dégradation déjà prévue (C8) | Confirmé |
| L9 | I.3 | CGU et API modifiables à tout moment ; information par courriel | Surveiller l'adresse du compte PISTE et refaire cette revue à chaque notification | Confirmé |

Le texte n'interdit pas expressément de servir des tiers au moyen de
l'application titulaire des clés ; cette lecture est une **inférence**, à
confirmer par les CGU PISTE.

## 5. Points restant à vérifier

- texte intégral et empreinte des CGU de la plateforme PISTE ;
- quotas exacts attachés aux deux abonnements PISTE ;
- valeurs effectivement présentes dans les réponses Judilibre pour siège et
  date de mise à jour ;
- délai de rétention et accès aux pseudonymes des journaux Render ;
- exercice chronométré du retrait J4 et de la rotation des clés.

## Sources primaires

- [Catalogue PISTE — Légifrance](https://piste.gouv.fr/api-catalog-sandbox?filter=legifrance)
- CGU de l'API Légifrance V1.0 du 15/12/2022 — copie obtenue depuis le compte
  PISTE du mainteneur le 25/10/2026 (empreinte en section 1)
- [CGU Judilibre du 6 janvier 2022](https://piste.gouv.fr/images/cgu/CGU_open_data_V8.pdf)
- [Licence Ouverte 2.0](https://www.etalab.gouv.fr/licence-ouverte-open-licence)
- [Ancien PDF Légifrance 2020 — archive seulement](https://piste.gouv.fr/images/cgu/DILA_Legifrance_Beta_v2.pdf)

## Étape 7 — Auto-critique adversariale

- Le texte Légifrance 2022 lève le blocage, mais ses renvois (CGU PISTE,
  mentions légales) restent non lus : « conforme aux CGU Légifrance » ne vaut
  que pour le texte de l'API.
- Le retrait complet d'une décision réduit la diffusion mais ne remplace pas la
  transmission sans délai à la Cour de cassation.
- Les champs absents d'une réponse Judilibre ne doivent pas être inventés.

─────────────────────────────────────────────
Modules activés                       : [DOC-AUDIT]
Modules non activés                   : [PÉNAL, ACTE-ADMIN, PA-PJ, FOND, CONTENTIEUX]
Niveau de confiance global            : modéré
Sources informelles signalées         : aucune
Limites de la recherche               : CGU PISTE non lues ; comparaison avec 2020 non refaite
─────────────────────────────────────────────
