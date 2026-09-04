# Critères de réussite — finalisation du plugin

Dernière mise à jour : 4 septembre 2026.

Cette grille applique la même boucle à chaque étape : **critère mesurable →
exécution → contre-contrôle → preuve datée**. Un contrôle partiel reste `◐` ;
une réussite sans preuve durable ne passe pas à `✅`.

| Étape | Critère de réussite | Contre-contrôle et preuve | État |
|---|---|---|---|
| Configuration du client tiers Auth0 | grant utilisateur tiers `Authorized`, `scope: []`, `allow_all_scopes: false` ; accès client tiers `Unauthorized` ; six outils utilisables | JSON expurgé du grant + capture limitée aux réglages + appel ChatGPT réel | ✅ 01/09/2026 |
| Fermeture de la DCR Auth0 | enregistrement dynamique désactivé après l'obtention d'un client durable ; ancien client supprimé | client `tpc_tTMV6uujD9aHwP8DoFfEMg` conservé, `dRsmaHYVujnQft3RtXOynPj7qeK3rAWg` supprimé (journal *Delete a client*) ; connexion ChatGPT aboutie DCR fermée, lecture réelle de l'article 1240 du Code civil | ✅ 04/09/2026 |
| Sonde Alpine (#34) | santé et métadonnées OAuth conformes ; six outils listés et réellement appelés ; lectures Légifrance/Judilibre avec texte et provenance officielle ; article inexistant non inventé | sonde publique puis `check_live_tools.py` avec jeton M2M ; Légifrance 1,429 s, Judilibre 0,487 s, version 0.8.0 consignées en E4 | ✅ 03/09/2026 |
| Maintien hors veille | aucun réveil sur 24 h après mise en service du ping externe | historique du ping sans échec ni trou > 10 min + résumé `--jours 1` sans réveil ; quota d'heures Render vérifié | ◐ **ping en service, daté par la mesure** : mise en service le 03/09/2026 entre 14:24 et 18:32 UTC ; côté journal `surveillance`, 0 réveil sur les 6 sondes suivantes contre 5 réveils sur 5 auparavant. Reste dû : l'historique du service de ping lui-même et le quota d'heures Render — § 11 des pièces |
| Disponibilité avant publication | couverture sur sept jours sans trou > 6 h ; aucune panne ni dérive ; aucun réveil dépassant 30 s | journal `surveillance`, résumé sur sept jours avec `--exiger-sans-defaut`, qui porte les quatre conditions | ⏳ **échéance datée : 10/09/2026 18:32 UTC**, sept jours après la mise en service mesurée du ping. À ce jour 0 défaut, 0 indisponibilité, 0 réveil, médiane 0,22 s |
| Portée `legal:read` | mesure de `scopes=` sur un appel ChatGPT réel, puis bascule ordonnée ou maintien argumenté | journal Render + contrôle positif et négatif après bascule | ⏳ **le motif d'impossibilité est tombé** le 04/09/2026 : la métadonnée de ressource protégée du serveur prime sur le document de l'émetteur (`mcp/client/auth/utils.py:109-119`). Chemin de bascule et mesure décisive : [`exploitation.md`](exploitation.md) incident n° 4 |
| Compte de démonstration | connexion complète au plugin sans MFA, SMS ni validation d'e-mail ; aucun secret dans le dépôt | essai en navigation privée et secret remis uniquement au formulaire OpenAI | ☐ création de compte requise |
| Isolation entre deux sujets | le quota du premier sujet n'empêche pas le second ; deux pseudonymes distincts dans les journaux | test chronométré avec deux comptes, sans identifiant brut | ☐ dépend du compte de démonstration |
| Retrait d'urgence Judilibre (E10) | décision masquée, valeur invalide refusée au démarrage, restauration réussie | exercice Render chronométré et journaux `count=1`, refus, puis `count=0` | ☐ accès Render requis |
| Check-list Auth0 complète | chaque ligne `◐`/`☐` dispose d'une preuve datée et expurgée | seconde lecture indépendante des captures et comparaison aux réglages actifs | ◐ DCR terminé ; autres lignes restantes |
| Findings de sécurité | aucun finding élevé ouvert et non accepté ; chaque correction adossée à une contre-épreuve | audit adversarial du 04/09/2026, § 8 de [`audit-securite.md`](audit-securite.md) | ◐ 14 findings ; SEC-03 et SEC-14 corrigés, SEC-01 atténué de 2 à 3 ordres de grandeur et reclassé MOYEN sans être refermé, SEC-05 corrigé. **SEC-02 reste le seul verrou** : sa gravité dépend de l'ouverture de l'inscription sur le locataire Auth0, invisible depuis l'extérieur |
| Déploiement du correctif de sécurité | `/health` annonce la version qui porte le correctif JWKS | montée en `0.8.1`, fusion, redéploiement Render, puis relecture de `/health` | ☐ **dépend de la fusion des PR #64 et #65** ; la production sert encore `0.8.0`, donc sans le correctif |
| Dossier de soumission | schéma officiel courant, six outils cohérents, 5 cas positifs et 3 négatifs ; identité et domaine vérifiés ; **chaque identifiant cité résout réellement** | validation locale + schéma officiel téléchargé + essai du formulaire + appel réel sur les identifiants des scénarios | ◐ partie automatisable conforme ; identifiant mort du 4ᵉ cas positif corrigé le 04/09/2026 après appel réel. **Lacune connue** : `check_plugin.py` ne vérifie que la cohérence interne du dossier, jamais la résolution des identifiants — c'est par là qu'une fixture de test s'y était glissée |
| Vidéo | six outils visibles, deux parcours positifs et un refus sans invention, aucune donnée personnelle à l'écran | relecture intégrale du MP4 avant dépôt | ☐ dépend du compte de démonstration |
| Release finale | version identique serveur/manifeste/notes, tag `plugin-v*` sur le commit fusionné, CI verte | suite complète, contrôles documentaires, PR revue, CI post-fusion | ☐ seulement après toutes les portes précédentes |

## Arrêts exigeant le mainteneur

- choix du compte Google pour se reconnecter au tableau de bord Auth0 ;
- création finale d'un compte ou d'identifiants persistants ;
- vérification d'identité OpenAI ;
- ~~création du compte de ping externe~~ **fait** : mesuré en service depuis le
  03/09/2026 entre 14:24 et 18:32 UTC. Reste dû sur ce point : exporter
  l'historique du service de ping sur 24 h et **vérifier le quota d'heures
  Render**, une instance maintenue éveillée consommant des heures en continu
  (§ 11 des pièces humaines) ;
- **relevé de `scopes=` dans les journaux Render** sur un appel ChatGPT réel :
  une mesure de quelques minutes qui décide seule du sort de la portée
  `legal:read` ([`exploitation.md`](exploitation.md), incident n° 4) ;
- **échéance de l'essai Auth0 vers le 21 septembre 2026** — 17 jours restants
  au 04/09/2026. Le locataire n'est pas suspendu, l'offre gratuite s'active
  d'elle-même ; la seule régression établie est la **rétention des journaux
  ramenée à un jour**, or ce sont les preuves d'audit de ce dossier. Les
  exporter avant l'échéance ;
- **l'inscription libre est-elle ouverte sur le locataire Auth0 ?** C'est la
  question qui décide de la gravité de SEC-02, et aucune sonde externe ne peut
  y répondre. Si elle est ouverte, n'importe qui peut obtenir un jeton valide
  et consommer les clés PISTE du titulaire ;
- validation visuelle et dépôt final de la vidéo.
