# Critères de réussite — finalisation du plugin

Dernière mise à jour : 2 septembre 2026.

Cette grille applique la même boucle à chaque étape : **critère mesurable →
exécution → contre-contrôle → preuve datée**. Un contrôle partiel reste `◐` ;
une réussite sans preuve durable ne passe pas à `✅`.

| Étape | Critère de réussite | Contre-contrôle et preuve | État |
|---|---|---|---|
| Configuration DCR Auth0 | grant utilisateur tiers `Authorized`, `scope: []`, `allow_all_scopes: false` ; accès client tiers `Unauthorized` ; six outils utilisables | JSON expurgé du grant + capture limitée aux réglages + appel ChatGPT réel | ✅ 01/09/2026 |
| Sonde Alpine (#34) | santé et métadonnées OAuth conformes ; six outils listés ; appels Légifrance et Judilibre réels ; article inexistant non inventé | sonde publique puis `check_live_tools.py` avec un jeton M2M éphémère ; latences et version consignées en E4 | ◐ public conforme le 02/09 ; jeton M2M requis |
| Disponibilité avant publication | aucune panne ni dérive sur sept jours ; aucun réveil dépassant 30 s | journal `surveillance`, résumé sur sept jours avec `--exiger-sans-defaut`, qui porte désormais les deux conditions | ❌ service sain à chaud (médiane 0,24 s, 0 indisponibilité) mais **5 réveils sur 5 exécutions planifiées**, 32,4 à 32,7 s ; le maintien hors veille par cron GitHub est réfuté (02/09) |
| Compte de démonstration | connexion complète au plugin sans MFA, SMS ni validation d'e-mail ; aucun secret dans le dépôt | essai en navigation privée et secret remis uniquement au formulaire OpenAI | ☐ création de compte requise |
| Isolation entre deux sujets | le quota du premier sujet n'empêche pas le second ; deux pseudonymes distincts dans les journaux | test chronométré avec deux comptes, sans identifiant brut | ☐ dépend du compte de démonstration |
| Retrait d'urgence Judilibre (E10) | décision masquée, valeur invalide refusée au démarrage, restauration réussie | exercice Render chronométré et journaux `count=1`, refus, puis `count=0` | ☐ accès Render requis |
| Check-list Auth0 complète | chaque ligne `◐`/`☐` dispose d'une preuve datée et expurgée | seconde lecture indépendante des captures et comparaison aux réglages actifs | ◐ DCR terminé ; autres lignes restantes |
| Dossier de soumission | schéma officiel courant, six outils cohérents, 5 cas positifs et 3 négatifs ; identité et domaine vérifiés | validation locale + schéma officiel téléchargé + essai du formulaire | ◐ partie automatisable conforme le 02/09 |
| Vidéo | six outils visibles, deux parcours positifs et un refus sans invention, aucune donnée personnelle à l'écran | relecture intégrale du MP4 avant dépôt | ☐ dépend du compte de démonstration |
| Release finale | version identique serveur/manifeste/notes, tag `plugin-v*` sur le commit fusionné, CI verte | suite complète, contrôles documentaires, PR revue, CI post-fusion | ☐ seulement après toutes les portes précédentes |

## Arrêts exigeant le mainteneur

- choix du compte Google pour se reconnecter au tableau de bord Auth0 ;
- création finale d'un compte ou d'identifiants persistants ;
- vérification d'identité OpenAI ;
- accès ou arbitrage Render : le cron GitHub ne tient pas la cadence (un run
  toutes les deux à quatre heures au lieu de douze par heure), donc le choix
  se réduit à un service de ping externe dédié ou à une instance sans mise en
  veille — voir `exploitation.md` § 1 ;
- validation visuelle et dépôt final de la vidéo.
