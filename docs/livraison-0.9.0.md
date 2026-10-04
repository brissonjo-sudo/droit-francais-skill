# Livraison préparatoire — candidat 0.9.0

Date : 2026-10-04. Audience : mainteneur du connecteur et pilote assisté.
Canal : remise locale, sans publication. Stade visé : candidat technique pour
pilote assisté, et non release stable ni qualification juridique.

## Périmètre

Le candidat ajoute `get_section` (section CODE avec parent explicite) et
`get_text` (texte consolidé LEGI) aux six outils historiques. Les versions des
manifestes et du serveur sont alignées sur 0.9.0. La méthodologie du skill,
l'authentification et la configuration du service distant ne sont pas modifiées.

La dépendance PyJWT passe de 2.14.0 à 2.15.0 pour le correctif amont
[GHSA-42vr-xj54-vc7v](https://github.com/jpadilla/pyjwt/security/advisories/GHSA-42vr-xj54-vc7v).
La politique OAuth et son implémentation restent inchangées. L'audit
`pip-audit` complet, distinct du seuil Trivy HIGH/CRITICAL, a détecté ce point.

Les réponses restent du contenu non fiable au sens des instructions : une
source récupérée ne prouve pas à elle seule la vigueur ou l'applicabilité.
La consultation refuse les identités incohérentes, les sommaires sans contenu,
les continuations inattendues et les dépassements de taille/profondeur.

## Preuves à conserver

La préparation utilise une copie du code sans `.env`, sans `.git`, sans caches
ni identifiants. Les artefacts générés sont conservés dans `dist/` (ignoré par
Git et par Docker) : sources du candidat, image exportée, sommes SHA-256,
journaux de contrôle, rapport de vulnérabilités et inventaire logiciel.

Le rapport `qualification-0.9.0.md` consigne les contrôles réellement exécutés.
Les fixtures juridiques sont synthétiques ; elles ne remplacent pas une réponse
PISTE officielle. Un catalogue MCP local de huit outils ne prouve pas que le
service distant les expose. Une compilation locale ne vaut pas CI distante.

## Portes de livraison

1. Contrôles statiques et tests de contrats sur le code figé du candidat.
2. Construction locale de l'image sans secrets ; exécution non-root et
   protocole HTTP limité au loopback, puis audit des dépendances de l'image.
3. Remise des artefacts et revue humaine du diff, du rapport et des limites.
4. Sur autorisation distincte : commit/push, CI distante, puis déploiement
   contrôlé avec OAuth et secrets gérés hors du dépôt.
5. Sonde distante authentifiée, huit outils réellement disponibles, puis
   récupération datée des sections/textes officiels requis par le préflight DPM.
6. Reprise de la campagne DPM uniquement après validation de son préflight.

Les portes 4 à 6 ne font pas partie de cette préparation locale. Aucun tag,
push, déploiement ni remplacement du plugin installé n'est implicite.

## Retour arrière

Conserver la révision et l'image effectivement déployées avant toute bascule.
La révision de départ du travail local est
`e437d10a2d4bbf66ba7a9c1e9fb49e773166054e` ; cela ne prouve pas qu'elle est
la révision distante en production. Un éventuel retour arrière remettrait
l'image précédemment qualifiée et sa configuration, sans suppression des
preuves de campagne et sans réécriture de l'historique Git.

## Décision provisoire

GO conditionnel pour préparer et remettre un candidat technique local.
NO-GO pour déclarer la release stable ou débloquer la campagne nominale DPM
tant que les preuves distantes, les consultations officielles et la revue
humaine ne sont pas obtenues. Cette séparation suit la revue de mise en produit
(`product-adoption-review`) ; elle ne constitue pas une approbation juridique.
