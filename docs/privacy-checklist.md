# Checklist de confidentialité avant publication

Ce document prépare la future politique publique ; il ne la remplace pas.
L'identité de l'éditeur, l'hébergeur, les coordonnées de contact et les durées
de conservation doivent être connus avant de rédiger la version opposable.

## Données à inventorier

- requêtes juridiques et identifiants transmis aux outils ;
- textes et métadonnées publics renvoyés par Légifrance et Judilibre ;
- données personnelles éventuellement présentes dans la jurisprudence publique ;
- journaux d'accès de l'hébergeur (IP, date, chemin, agent utilisateur) ;
- journaux applicatifs limités au nom d'opération, état et durée ;
- aucune clé PISTE, aucun jeton OAuth et aucun secret dans les réponses ou logs.

## Acteurs à déclarer

- l'éditeur du plugin, responsable de son service MCP ;
- l'hébergeur et ses régions de traitement ;
- OpenAI, qui appelle le serveur selon les choix et conditions de l'utilisateur ;
- PISTE/DILA et la Cour de cassation, sources officielles interrogées.

## Décisions à prendre avant mise en ligne

- fixer la finalité exacte et la base juridique de chaque traitement ;
- choisir une région d'hébergement et une durée de rétention minimale ;
- désactiver les logs de corps de requête et de réponse sur toute la chaîne ;
- définir contact, exercice des droits, suppression et procédure d'incident ;
- expliquer que les résultats ne remplacent pas un conseil juridique ;
- vérifier les conditions de réutilisation des décisions et l'interdiction de
  profilage des magistrats et greffiers ;
- faire correspondre strictement cette politique aux champs réellement renvoyés.

## Test de sortie

Avant soumission, appeler chaque outil avec des cas réalistes et inspecter les
réponses imbriquées. Supprimer tout identifiant interne, trace, information de
débogage, secret ou donnée personnelle sans nécessité directe pour la demande.
