# Checklist de confidentialité avant publication

Ce document prépare la future politique publique ; il ne la remplace pas.
L'identité de l'éditeur, l'hébergeur, les coordonnées de contact et les durées
de conservation doivent être connus avant de rédiger la version opposable.

## Données à inventorier

- requêtes juridiques et identifiants transmis aux outils ;
- textes et métadonnées publics renvoyés par Légifrance et Judilibre ;
- données personnelles éventuellement présentes dans la jurisprudence publique ;
- journaux d'accès de l'hébergeur (IP, date, chemin, agent utilisateur) ;
- journaux métier limités au nom d'opération, état, durée et pseudonyme du
  sujet ; ce pseudonyme reste une donnée personnelle ;
- si le niveau `INFO` est activé, identifiants de session MCP éphémères et
  métadonnées réseau émis par le SDK et le serveur HTTP ;
- aucune clé PISTE, aucun jeton OAuth et aucun secret dans les réponses ou logs.

## Acteurs à déclarer

- l'éditeur du plugin, responsable de son service MCP ;
- l'hébergeur et ses régions de traitement ;
- OpenAI, qui appelle le serveur selon les choix et conditions de l'utilisateur ;
- PISTE/DILA et la Cour de cassation, sources officielles interrogées.

## Décisions à prendre avant publication dans l'annuaire

- fixer la finalité exacte et la base juridique de chaque traitement ;
- choisir une région d'hébergement et une durée de rétention minimale ;
- désactiver les logs de corps de requête et de réponse sur toute la chaîne ;
- définir contact, exercice des droits, suppression et procédure d'incident ;
- fixer et vérifier la rétention, l'accès et l'effacement des pseudonymes ;
- expliquer que les résultats ne remplacent pas un conseil juridique ;
- vérifier les conditions de réutilisation des décisions et l'interdiction de
  profilage des magistrats et greffiers ;
- faire correspondre strictement cette politique aux champs réellement renvoyés.

## Conformité CGU et audit sécurité

Cette checklist est complétée par les documents dédiés à dérouler avant toute
publication dans l'annuaire (le serveur est déjà exposé au réseau avec OAuth) :

- le [registre des obligations CGU](obligations-cgu.md) — obligations
  Légifrance et Judilibre opposables au titulaire des clés, et écarts à traiter
  (procédure d'incident, signalement des réidentifications, mentions RGPD
  Judilibre, mentions de source et de date) ;
- le [plan d'audit sécurité](audit-securite.md) — phases, contrôles mobilisés,
  grille de sévérité et livrables. Les findings critiques et élevés doivent
  être corrigés avant la publication ;
- la [procédure d'incident](incident-response.md) et la
  [checklist Auth0](auth0-security-checklist.md).

## Test de sortie

Avant soumission, appeler chaque outil avec des cas réalistes et inspecter les
réponses imbriquées. Supprimer tout identifiant interne, trace, information de
débogage, secret ou donnée personnelle sans nécessité directe pour la demande.
