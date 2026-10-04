# Qualification locale — candidat 0.9.0, essai v2

Date : 2026-10-04. Destinataire : mainteneur, pilote assisté.
Remise locale uniquement ; aucun commit, tag, push ou déploiement.

## Décision

**GO conditionnel pour la remise du candidat technique local.**
**NO-GO pour une release stable, un déploiement implicite ou la reprise DPM.**
La revue `product-adoption-review` a imposé de séparer les preuves techniques
locales, la validation comportementale, la couverture juridique officielle
et l'approbation humaine. Les trois dernières ne sont pas acquises ici.

## Résultats observés sur le candidat courant

| Contrôle | Résultat et limite |
| --- | --- |
| Windows, Python 3.13, MCP 2.2.0, PyJWT 2.15.0 | 365 tests réussis sur une copie sans secrets |
| Linux, Python 3.14, runtime de l'image | 364 tests réussis, réseau désactivé, source montée en lecture seule |
| Test nécessitant Git | Transféré explicitement au dépôt hôte : 166 fichiers suivis, aucun `.env` réel suivi |
| Transport HTTP de l'image | `/health` annonce 0.9.0 ; huit outils, schémas de sortie et annotations contrôlés sur loopback |
| Politique de production | Configuration sans OAuth refusée, code 2, avec clés amont fictives et sans réseau |
| Contrôles documentaires | Plugin, liens (61 documents), vault (17 notes), affirmations (60 documents), commandes (22 invocations) réussis |
| Ruff, fichiers nouveaux | Vérification et formatage réussis pour `texts.py` et `test_text_consultation.py` |
| pip-audit 2.10.1, dépendances déclarées | Audit strict réussi ; aucune vulnérabilité connue dans la résolution Windows évaluée |
| Trivy 0.75.0, image exportée | 30 paquets système, 28 paquets Python ; aucune vulnérabilité signalée, toutes sévérités inventoriées |
| Gate Trivy HIGH/CRITICAL corrigeables | Réussi, code 0 |
| Inventaires | SBOM CycloneDX des dépendances déclarées et de l'image conservés séparément |

Les tests juridiques emploient des fixtures synthétiques, pas des réponses
officielles récentes. Les tests OAuth emploient des clés/jetons fictifs et des
réponses locales ; ils ne valent pas connexion humaine au service distant.
Le contrôle Git dans la copie sans `.git` ne constitue pas une preuve autonome :
le contrôle séparé sur le dépôt réel est celui retenu. La première tentative
Linux intégrale a échoué parce que l'image de production ne contient pas Git ;
elle est conservée dans le dossier v1, pas transformée en succès.

## Correction découverte pendant la préparation

Le premier paquet v1 conservait PyJWT 2.14.0. Son gate Trivy HIGH/CRITICAL
passait, mais `pip-audit` complet signalait `PYSEC-2026-4141`. Il n'a donc pas
été retenu pour livraison. Le correctif épinglé est PyJWT 2.15.0, confirmé par
[l'avis du mainteneur](https://github.com/jpadilla/pyjwt/security/advisories/GHSA-42vr-xj54-vc7v)
et [sa release](https://github.com/jpadilla/pyjwt/releases/tag/2.15.0).

Le test déterministe injecte `RecursionError` à la frontière JSON réelle de
PyJWT : il échoue avec 2.14.0 et passe avec 2.15.0. Les chemins de décodage
d'une charge récursive et de sélection JWKS sont aussi testés sans réseau.
La première fixture seule ne discriminait pas l'ancienne version ; son journal
est conservé et n'est pas présenté comme reproduction. Aucune exploitation
du serveur en production n'a été démontrée. Son vérificateur custom et sa
politique OAuth n'ont pas été modifiés.

## Constats de mise en produit

| Identifiant stable | État de preuve / portée | Conséquence |
| --- | --- | --- |
| remote-catalog-not-qualified | Non vérifié sur le candidat courant | La sonde locale ne qualifie pas le catalogue distant ; son dernier état historique comptait six outils |
| official-consultations-not-validated | Non vérifié sur le candidat courant | Les nouvelles consultations nécessitent un préflight officiel daté, avant tout cas DPM |
| dependency-audit-all-severities | Observé sur v1 puis corrigé et revérifié sur v2 | Ne pas remplacer l'audit strict des dépendances par un seul seuil HIGH/CRITICAL |
| runtime-git-check-boundary | Observé sur le candidat courant | Un contrôle de suivi Git appartient au dépôt, pas à l'image runtime dépourvue de Git |

## Artefacts remis

Dossier local ignoré : `dist/candidat-0.9.0-20261004-v2/`.

- `droit-francais-0.9.0-sources.zip` : instantané de 170 fichiers publics
  utilisé pour la construction et les tests, sans `.git`, `.env` réel ni cache.
  Les rapports rédigés après qualification sont des pièces jointes séparées.
- `droit-francais-mcp-0.9.0.tar` : image locale Linux amd64, utilisateur `app`.
- `manifest.json` : empreintes des deux artefacts, identité de l'image et bornes
  de qualification ; ne contient aucun secret.
- Journaux, rapports de vulnérabilités, SBOM et contrôles d'intégrité du code.

Tag local : `droit-francais-mcp:0.9.0-candidat-20261004-v2`.
Identité Docker locale :
`sha256:e4efaff101163818c299327cb5b7434f097c20d8b1813405e4a9c85333fc20e5`.
Ce n'est pas un digest de release publiée dans un registre distant.

Le code exécuté dans l'image correspond octet pour octet à la copie qualifiée
pour `server.py`, `catalog.py`, `tools.py`, `texts.py` et `requirements-mcp.txt`.
Le build utilise une base épinglée et `apk upgrade`, ainsi que des dépendances
transitives résolues lors de la construction : ne pas promettre une reconstruction
bit à bit. Pour reproduire cette image précise, conserver son tar et son SBOM.

Trivy est épinglé au digest
`sha256:af6acf9a6b85dfe389a1941505c0ce9efef52a4719635e1a962f022a3d855daa`.
Base CVE mise à jour le `2026-10-04T08:52:32.606987838Z`, téléchargée le
`2026-10-04T12:24:12.838502289Z`. Aucun signal connu à cette date n'est une
garantie d'absence de vulnérabilité future. Les sondes Docker créées pour cette
préparation sont arrêtées et supprimées ; images et preuves sont conservées.

## Suite soumise à autorisation

Revue humaine du diff et des limites, puis autorisation explicite de commit/push
et déploiement. Faire la CI distante et la sonde OAuth sur le service réellement
mis à jour ; vérifier huit outils et les lectures officielles requises. Refaire
ensuite le préflight DPM dans un nouvel essai, sans effacer les échecs antérieurs.
Pas de benchmark comportemental, d'évaluation de modèle ou de nouveau score DPM
dans cette livraison.
