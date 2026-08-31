# Obligations contractuelles — CGU Légifrance et Judilibre

Ce document recense les obligations opposables au **titulaire des clés PISTE**
(l'exploitant du serveur MCP déployé sur Render) au titre des conditions
générales d'utilisation des deux API officielles consommées par l'outil. Il
sert de référentiel de conformité : chaque obligation est reliée à l'état
actuel du service et, le cas échéant, à un écart à traiter. Les points de
contrôle correspondants sont audités dans le [plan d'audit sécurité](audit-securite.md)
(phases 5 et 6).

> **Nature juridique.** Le serveur consomme les API avec les clés PISTE de son
> titulaire ; c'est donc lui, et non l'utilisateur final de ChatGPT/Codex, qui
> a la qualité d'« Utilisateur » (CGU Légifrance) et de « Réutilisateur » (CGU
> Judilibre). L'acceptation des CGU s'est faite lors de la souscription des API
> sur PISTE. Les obligations ci-dessous pèsent sur l'exploitant même lorsque la
> requête émane d'un tiers.

## Sources de référence (vérifiées à la source)

| Document | Version | Portée |
|---|---|---|
| [CGU de l'API Légifrance (DILA)](https://piste.gouv.fr/images/cgu/DILA_Legifrance_Beta_v2.pdf) | V1.1 — 04/08/2020 | Accès et réutilisation des fonds Légifrance |
| [CGU réutilisation des données judiciaires (Cour de cassation)](https://piste.gouv.fr/images/cgu/CGU_open_data_V8.pdf) | 6 janvier 2022 | Réutilisation des décisions diffusées via Judilibre |
| [Licence Ouverte / Open Licence 2.0 (Etalab)](https://www.etalab.gouv.fr/licence-ouverte-open-licence) | 2.0 | Licence de réutilisation commune aux deux fonds |
| [CGU de la plateforme PISTE (AIFE)](https://developer.aife.economie.gouv.fr/images/com_apiportal/CGU/cgu_portal_FR.pdf) | — | Utilisation de la plateforme d'intermédiation |

> Ces documents peuvent être modifiés unilatéralement par la DILA ou la Cour de
> cassation, avec effet immédiat à leur publication. La revue annuelle
> (`skill/references/maintenance.md`) doit vérifier qu'aucune version plus
> récente n'a été publiée et re-vérifier la vigueur des articles cités
> (COJ, CRPA, code pénal) — voir le skill `recherche-juridique`.

---

## 1. Obligations communes aux deux API

Le régime PISTE aligne largement les deux CGU. Les obligations suivantes valent
pour Légifrance **et** Judilibre.

| # | Obligation | Fondement | État côté service | Action / preuve d'audit |
|---|---|---|---|---|
| C1 | **Confidentialité des clés OAuth** : strictement réservées à l'application, jamais publiées ni divulguées à un tiers. | Légifrance III.3 ; Judilibre XI.C | Secrets d'environnement Render, jamais dans l'image ni les réponses ; masquage actif dans `_safe_call`. | Vérifier l'absence de secret dans le dépôt, l'image, les logs et les réponses d'erreur (audit phase 1 et 5). |
| C2 | **Responsabilité des identifiants et sécurité de l'environnement d'exécution** (état de l'art, PSSIE : correctifs, pare-feu, contrôle des AC, verrouillage des sessions). | Légifrance III.3 & V.2 ; Judilibre XI.C & XI.E | Conteneur non-root, image `slim` reconstruite en CI, TLS terminé par l'hébergeur. | Chaîner la gestion des correctifs de base image et des dépendances (audit phase 1). |
| C3 | **Notification d'incident et de compromission** : signaler à la DILA/AIFE (Légifrance) ou à la Cour de cassation/AIFE (Judilibre) tout accès anormal ; en cas de compromission, réinitialiser les clés sur PISTE **au plus vite** et avertir dans les plus brefs délais. | Légifrance V.3 ; Judilibre XI.E | **Écart** : aucune procédure d'incident formalisée ni contact désigné. | Rédiger une procédure d'incident (détection surconsommation → rotation clés → notification). Livrable de l'audit phase 5. |
| C4 | **Respect des quotas PISTE** (par seconde/minute/jour ; nombre de requêtes ou bande passante ; modifiables à tout moment). | Légifrance IV.3 ; Judilibre XI.D | Garde-fous applicatifs : concurrence, débit par instance (`MCP_TOOL_CALLS_PER_MINUTE`) et par utilisateur (`MCP_USER_CALLS_PER_MINUTE`). | Vérifier l'alignement des limites internes sur les quotas réellement accordés ; ajouter une limite globale si plusieurs réplicas (audit phase 4). |
| C5 | **Usage conforme aux lois et réglementations** ; l'Utilisateur/Réutilisateur est seul responsable et garantit/indemnise l'administration. | Légifrance V.1 ; Judilibre XII | Conditions d'utilisation publiques listant les usages interdits. | Confronter `docs/terms-of-use.md` aux interdictions CGU (audit phase 6). |
| C6 | **Mention de la source et de la date de mise à jour** ; ne pas altérer ni dénaturer les données (Licence Ouverte 2.0). | Étalab 2.0 ; Légifrance IX ; Judilibre V & XIII | Partiellement couvert : le skill impose la citation traçable et la datation ; à confirmer dans les réponses d'outil. | Vérifier que chaque réponse renvoie source + date/version (audit phase 6). |
| C7 | **Non-opposabilité et non-garantie des données** (API en bêta) : ne jamais présenter un échec de récupération comme une vérification réussie ; seuls les PDF signés du JO sont opposables. | Légifrance VI.1 & VI.2 ; Judilibre XI.A | Couvert : `instructions` du serveur + règle de provenance du skill ; erreur amont renvoyée comme « Source officielle non vérifiée ». | Test dynamique des cas d'erreur (audit phase 7). |
| C8 | **Suspension/résiliation pour manquement** : l'accès peut être coupé sans préavis. | Légifrance VII.1 ; Judilibre XII | Risque opérationnel de continuité. | Documenter le plan de continuité (clé de secours, dégradation vers voie web). |

---

## 2. Obligations propres à Légifrance (DILA)

| # | Obligation | Fondement | État côté service |
|---|---|---|---|
| L1 | Données soumises à la **Licence Ouverte 2.0** ; usage commercial autorisé mais aux risques et périls de l'Utilisateur. | Légifrance IX & VI.2 | Licence du dépôt distincte (CC BY-SA 4.0 pour le code/skill) ; la licence des **données** reste Étalab 2.0 — à mentionner dans les CGU publiques. |
| L2 | Réception des **notifications de la DILA** à l'adresse de contact du compte PISTE. | Légifrance VIII | S'assurer qu'une adresse de contact surveillée est renseignée sur le compte PISTE. |
| L3 | Traitement des **données personnelles du développeur** (email) par la DILA ; droits RGPD auprès du DPD (`dpd@pm.gouv.fr`). | Légifrance X | Information du titulaire ; sans impact sur les utilisateurs finaux. |

---

## 3. Obligations propres à Judilibre (Cour de cassation)

Ce sont les obligations les plus sensibles, car les décisions renvoyées peuvent
contenir des données personnelles malgré la pseudonymisation. L'expertise du
skill `dpo-ct` est mobilisée pour ces points (audit phase 5).

| # | Obligation | Fondement | État côté service | Action / preuve d'audit |
|---|---|---|---|---|
| J1 | **Interdiction du profilage des magistrats et membres du greffe** : ne pas indexer leurs données d'identité pour évaluer, analyser, comparer ou prédire leurs pratiques. Sanctions pénales (art. 226-18, 226-24, 226-31 code pénal) + loi 78-17. | COJ art. L.111-13 al. 3 ; Judilibre VI | Interdit dans `docs/terms-of-use.md`. | Confirmer qu'aucune fonction n'agrège les décisions par magistrat ; conserver l'interdiction dans la sortie utilisateur (audit phase 6). |
| J2 | **Non-réidentification** des personnes physiques occultées ou pseudonymisées ; respect du RGPD et de la loi 78-17, le réutilisateur étant responsable de traitement. | CRPA art. L.322-2 ; Judilibre VII & XII | Interdit dans les CGU publiques ; le service ne stocke pas de base. | Vérifier l'absence de recoupement/stockage permettant la réidentification (audit phase 5). |
| J3 | **Signalement des réidentifications manifestes** persistant dans une décision → transmettre à `anonymisation.sder.courdecassation@justice.fr`. | Judilibre VII | **Écart** : aucun canal de signalement ni procédure. | Créer une procédure et un point de contact ; l'exposer dans la politique publique (audit phase 5). |
| J4 | **Défaut d'occultation des nom/prénoms** : transmettre sans délai toute demande reçue à la Cour de cassation ; procéder à l'occultation « socle » à titre provisoire. | COJ art. L.111-13 al. 2 ; Judilibre IX | **Écart partiel** : le service ne redistribue pas de base persistante, mais restitue du texte en direct ; définir la conduite à tenir si un défaut est signalé. | Formaliser le relais vers la Cour de cassation (audit phase 6). |
| J5 | **Demandes d'occultation / levée d'occultation** : compétence **exclusive** de la Cour de cassation (art. R.111-13 COJ) ; interdiction de modifier la pseudonymisation de sa propre initiative ; informer le demandeur de la bonne adresse (`occultations.courdecassation@justice.fr`). | COJ art. R.111-13 ; Judilibre X | À expliciter dans la politique publique. | Ajouter la mention et l'adresse dans `privacy-policy.md` (audit phase 6). |
| J6 | **Intégrité, exactitude et mise à jour** des données diffusées ; pour chaque décision réutilisée, mention de la **juridiction, formation, siège et date du prononcé**, indissociables de la décision. | Judilibre V & XII | À confirmer dans le format de sortie de `get_decision` / `search_case_law`. | Vérifier que les métadonnées obligatoires accompagnent toujours le texte (audit phase 6). |
| J7 | **Mention de la source « base Open Data de la Cour de cassation »** et de la **date de dernière mise à jour** ; recommandation de ne pas excéder 72 h entre deux mises à jour d'une base dérivée. | Judilibre V | Le service interroge l'API en direct (pas de base dérivée) : la règle des 72 h est de fait respectée ; la mention de source reste due. | Confirmer la mention de source dans la sortie (audit phase 6). |
| J8 | **Exercice des droits RGPD** (accès/rectification) relatifs au traitement Judilibre → SDER de la Cour de cassation. | RGPD art. 15-16 ; Judilibre VIII | À renvoyer dans `privacy-policy.md`. | Compléter la politique publique (audit phase 6). |

---

## 4. Synthèse des écarts à traiter

Les écarts identifiés ci-dessus, à convertir en actions correctives priorisées
par l'audit :

1. **Procédure d'incident et de compromission de clés** (C3) — détection de
   surconsommation, rotation des clés PISTE, notification DILA/AIFE et Cour de
   cassation. *Priorité haute.*
2. **Canal de signalement des réidentifications et défauts d'occultation**
   (J3, J4) — point de contact et relais vers la Cour de cassation. *Priorité haute.*
3. **Mentions RGPD Judilibre et occultation** dans la politique publique
   (J5, J8). *Priorité moyenne.*
4. **Vérification systématique des mentions de source, date et métadonnées
   obligatoires** dans les réponses d'outil (C6, J6, J7). *Priorité moyenne.*
5. **Alignement des quotas internes sur les quotas PISTE réels** et limite
   globale multi-réplicas (C4). *Priorité moyenne.*
6. **Mention de la Licence Ouverte 2.0 des données** distincte de la licence du
   code (L1). *Priorité basse.*

Ces points sont repris comme critères de sortie dans la
[checklist de confidentialité](privacy-checklist.md) et le
[plan d'audit sécurité](audit-securite.md).
