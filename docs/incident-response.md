# Procédure d'incident — clés PISTE et données Judilibre

Dernière mise à jour : 31 août 2026

Cette procédure est utilisable sans outil particulier. Les captures et preuves
contenant une clé, un jeton ou une identité restent dans un dossier privé à
accès restreint, jamais dans une issue GitHub publique.

## Déclencheurs

- hausse inexpliquée de consommation, 401/403/429 inhabituels ;
- secret trouvé dans un commit, une image, un log ou une réponse ;
- compte GitHub, Render, Auth0 ou PISTE compromis ;
- signalement d'un nom/prénom non occulté ou d'une réidentification manifeste ;
- réponse du plugin redistribuant une décision qui devrait être retirée.

## Priorités immédiates

1. Ouvrir une fiche privée avec heure UTC, service, version et déclarant.
2. Contenir : suspendre le service ou l'accès concerné si la fuite continue.
3. Ne pas recopier le secret ni la donnée personnelle dans les journaux.
4. Préserver les preuves minimales et relever l'image/commit déployé.

## Compromission d'une clé PISTE

1. Révoquer/réinitialiser la clé dans PISTE **au plus vite**.
2. Remplacer le secret dans Render, redéployer, puis tester un seul appel.
3. Contrôler les quotas et journaux sur la période d'exposition.
4. Informer via les canaux du compte PISTE le producteur concerné et l'AIFE,
   conformément à la version des CGU acceptée par le titulaire.
5. Pour Légifrance, vérifier les destinataires exacts dans les CGU 2022 avant
   d'envoyer une notification : le PDF 2020 n'est pas la source courante.
6. Révoquer aussi les sessions/jetons des comptes compromis et changer les
   secrets dépendants.

## Défaut d'occultation Judilibre

1. Identifier la décision sans reproduire publiquement le passage.
2. Ajouter l'identifiant exact à la variable Render
   `MCP_JUDILIBRE_SUPPRESSED_IDS` (liste séparée par des virgules). Un
   identifiant Judilibre fait 24 caractères hexadécimaux ; la casse est
   indifférente, les espaces autour des virgules sont ignorés.
3. Redémarrer le service et vérifier :
   - le journal de démarrage porte `judilibre_suppression_list count=N`, où
     `N` est le nombre d'identifiants attendus — jamais les identifiants
     eux-mêmes. **Une entrée malformée empêche le service de démarrer**, avec
     un message qui nomme la position fautive dans la liste : corriger la
     variable, ne pas contourner ;
   - la décision est filtrée des résultats de recherche ;
   - sa lecture directe renvoie « temporairement indisponible ».
4. Transmettre **sans délai** la demande portant sur un défaut d'occultation à
   la Cour de cassation. Pour une demande d'occultation ou levée, utiliser
   `occultations.courdecassation@justice.fr`.
5. Une réidentification manifeste persistante peut être signalée à
   `anonymisation.sder.courdecassation@justice.fr` ; il s'agit d'une
   recommandation forte de la section VII, distincte de l'obligation précédente.
6. Ne pas modifier soi-même le texte ou la pseudonymisation. Le retrait complet
   est la mesure conservatoire du service.
7. Après confirmation de la correction amont, relire la décision, retirer son
   identifiant de la variable, redémarrer et consigner la clôture.

## Communication et clôture

- informer les personnes ou autorités requises selon l'incident et le droit
  applicable ; faire valider toute notification RGPD si une violation de
  données personnelles est plausible ;
- documenter cause, durée, impact, clés touchées, décisions retirées et actions ;
- ajouter un test de non-régression sans intégrer les données exposées ;
- réaliser un exercice semestriel et dater son résultat dans
  `audit-securite.md`.

