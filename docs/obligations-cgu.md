# Registre des obligations — Légifrance et Judilibre

─────────────────────────────────────────────
Date d'analyse           : 31/08/2026 ; revue Légifrance le 25/10/2026 ; revue PISTE le 27/10/2026
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
| CGU de la plateforme PISTE | Lues le 27/10/2026 sur <https://piste.gouv.fr/cgu> : page sans date ni numéro de version ; SHA-256 `213cbb5f70cf0fe8c11dc9c4c18e04277aea8962411d755044529a30ea7e0c55` du texte de l'élément `article` (`innerText`, UTF-8, 18 048 octets) | Partie intégrante des CGU Légifrance (I.1) ; analysées en section 4 bis. Page modifiable sans préavis (§ 2.2) : l'empreinte ne vaut que pour cette lecture |
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
| L4 | VI.1 | Fiabilité, complétude et fraîcheur non garanties ; seuls les PDF signés du Journal officiel sont opposables | Mention obligatoire dans les conditions d'utilisation et le dossier de preuve | Confirmé — mention portée dans `terms-of-use.md` §3 |
| L5 | IV.3 | Quotas par seconde, minute ou jour, par application ou par méthode, modifiables avec information par courriel | Quota par client et surveillance de consommation nécessaires avant plusieurs clients | Confirmé |
| L6 | V.1 | Usage conforme aux lois, à la LO 2.0 et au RGPD ; l'utilisateur garantit la DILA contre toute action | Risque contractuel porté par l'exploitant | Confirmé |
| L7 | V.3, VIII | Incident ou compromission : réinitialiser les identifiants et prévenir la DILA et/ou l'AIFE ; notifications vers `retours-legifrance-modernise@dila.gouv.fr` | Contact reporté dans `incident-response.md` | Confirmé |
| L8 | VII.1 | Suspension sans notification préalable et résiliation sans préavis en cas de manquement | Point de défaillance unique ; dégradation déjà prévue (C8) | Confirmé |
| L9 | I.3 | CGU et API modifiables à tout moment ; information par courriel | Surveiller l'adresse du compte PISTE et refaire cette revue à chaque notification | Confirmé |

Le texte n'interdit pas expressément de servir des tiers au moyen de
l'application titulaire des clés ; cette lecture est une **inférence**. La
lecture des CGU PISTE (section 4 bis) ne la confirme pas : elles ne disent rien
non plus sur ce point.

## 4 bis. Plateforme PISTE — affirmations vérifiées (lecture du 27/10/2026)

Paraphrases contrôlées sur le texte intégral (section 1).

| ID | Section | Règle | Conséquence pour le service | État |
|---|---|---|---|---|
| P1 | 3.1.1 | Les clés délivrées ne sont utilisables que pour une Application donnée | Une seule application PISTE pour le service ; pas de réemploi des clés ailleurs | Confirmé |
| P2 | 3.1.2 | L'utilisateur s'engage à ne pas partager ses clés « en dehors de son organisation, pour quelque utilisation que ce soit » | Satisfait au sens littéral (clés côté serveur, C1). Le texte ne dit pas si servir des tiers avec ces clés relève de ce partage : **question ouverte**, à trancher par un avis juridique | Confirmé (texte) ; portée non établie |
| P3 | 3.1.3 | Limites d'usage fixées à la discrétion du fournisseur ; interdiction de les contourner | Cache et rejeu (`transport.py`) à borner pour ne pas contourner un quota ; pas de multiplication d'applications pour cumuler des quotas | Confirmé |
| P4 | 5 | L'AIFE collecte l'origine, le nombre des appels et **le contenu des requêtes**, sauf demande contraire du fournisseur | Les requêtes des utilisateurs sont visibles de l'AIFE ; mention portée dans `privacy-policy.md`. Une demande contraire des fournisseurs DILA ou Cour de cassation n'est pas connue | Confirmé (texte) |
| P5 | 2.2, 2.3 | CGU modifiables à tout moment sans accord préalable ; messages de service (dont révocation des droits d'accès) envoyés à l'adresse du compte | Même veille que L9 : surveiller l'adresse du compte PISTE | Confirmé |
| P6 | 2.8 | Blocage ou suppression du compte sans information préalable en cas d'usage contraire aux CGU | Même point de défaillance unique que L8 (C8) | Confirmé |
| P7 | 3.2 | Interruption de la plateforme annoncée au moins 3 jours ouvrés à l'avance ; niveaux de service propres à chaque fournisseur | Aucun engagement de disponibilité amont (voir L3) | Confirmé |

Ces CGU ne contredisent aucune règle des sections 2 à 4.

## 5. Points restant à vérifier

- avis juridique sur P2 : servir des tiers avec l'application du titulaire
  relève-t-il du « partage de clés » ? ;
- demande contraire éventuelle des fournisseurs sur la collecte du contenu des
  requêtes (P4) ;
- quotas exacts attachés aux deux abonnements PISTE. Le guide utilisateur PISTE
  (copie OCR transmise par le mainteneur le 27/10/2026, SHA-256
  `6264c21134c9ab8fe296b18d45779f861b4b38f5f9285b02598c3929a7d9ab2c`, § 7)
  fixe par défaut 20 requêtes par seconde par application de production
  (HTTP 429 au-delà), modifiable par PISTE, par le fournisseur ou sur demande
  justifiée ; § 6.4 : 1 000 000 d'appels par jour en sandbox. Un quota propre à
  Légifrance ou Judilibre, s'il existe, reste à relever sur la fiche de
  l'application ;
- valeurs effectivement présentes dans les réponses Judilibre pour siège et
  date de mise à jour ;
- délai de rétention et accès aux pseudonymes des journaux Render ;
- exercice chronométré du retrait J4 et de la rotation des clés.

## Sources primaires

- [Catalogue PISTE — Légifrance](https://piste.gouv.fr/api-catalog-sandbox?filter=legifrance)
- CGU de l'API Légifrance V1.0 du 15/12/2022 — copie obtenue depuis le compte
  PISTE du mainteneur le 25/10/2026 (empreinte en section 1)
- [CGU Judilibre du 6 janvier 2022](https://piste.gouv.fr/images/cgu/CGU_open_data_V8.pdf)
- [CGU de la plateforme PISTE](https://piste.gouv.fr/cgu) — lues le
  27/10/2026, sans date de version (empreinte en section 1)
- [Licence Ouverte 2.0](https://www.etalab.gouv.fr/licence-ouverte-open-licence)
- [Ancien PDF Légifrance 2020 — archive seulement](https://piste.gouv.fr/images/cgu/DILA_Legifrance_Beta_v2.pdf)

## Étape 7 — Auto-critique adversariale

- Les CGU PISTE sont lues, mais les mentions légales renvoyées par le texte
  Légifrance ne le sont pas : « conforme aux CGU Légifrance » ne vaut que pour
  le texte de l'API et les CGU PISTE.
- La page PISTE n'est pas versionnée : l'empreinte atteste une lecture datée,
  pas une version publiée.
- Le retrait complet d'une décision réduit la diffusion mais ne remplace pas la
  transmission sans délai à la Cour de cassation.
- Les champs absents d'une réponse Judilibre ne doivent pas être inventés.

─────────────────────────────────────────────
Modules activés                       : [DOC-AUDIT]
Modules non activés                   : [PÉNAL, ACTE-ADMIN, PA-PJ, FOND, CONTENTIEUX]
Niveau de confiance global            : modéré
Sources informelles signalées         : aucune
Limites de la recherche               : mentions légales non lues ; page CGU PISTE non versionnée ; comparaison avec 2020 non refaite
─────────────────────────────────────────────
