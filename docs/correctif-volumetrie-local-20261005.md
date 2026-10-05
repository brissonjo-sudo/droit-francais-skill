# Diagnostic de volumétrie et complétude — correctif local du 5 octobre 2026

## Statut et périmètre

Préparation locale autorisée, sur `codex/correctif-volumetrie-sections-20261005`,
base `21afe1309bbdc3587b6e4f66385a7163e0add4fb`. Aucun commit, push, PR,
déploiement, changement de version ou modification de credential.

Le refus réel S01 observé par DPM ne distinguait pas les octets JSON du
nombre de nœuds. Son corps n'a pas été récupéré : **ce correctif ne prouve
pas le déblocage de S01**. Il permet d'identifier la borne déclenchée et
corrige un défaut de contrôle de complétude des articles.

## Modification

- [`texts.py`](../skill/scripts/droit_francais/texts.py) expose le périmètre
  (`response` ou `selected_section`), la métrique, une mesure au moins égale
  au dépassement constaté et le plafond. Le détail de journal ne contient
  que ces compteurs et constantes ; aucun contenu, identifiant ou secret.
- Les limites restent **2 000 000 octets JSON UTF-8, 5 000 nœuds et profondeur
  32**. Le contrôle de la réponse entière précède toujours la sélection.
  Un petit sous-arbre ne permet pas de contourner un parent trop volumineux.
- Le parcours contrôle aussi les articles : `complete=false`,
  `content_complete=false`, marque de troncature ou de continuation provoquent
  un refus. La profondeur compte désormais les articles, pas seulement les
  sections : cette extension peut rendre un cas limite plus strict.
- L'encodage itératif, documenté dans la
  [bibliothèque standard Python](https://docs.python.org/3.13/library/json.html),
  conserve les séparateurs et `ensure_ascii=False` historiques. Il cesse dès
  le dépassement connu, sans construire une autre sérialisation complète
  de la réponse. **Ce n'est pas une lecture HTTP en streaming** : le transport
  et le décodage amont ne sont pas modifiés ; un gros champ reste un gros chunk.
- En cas de succès seulement, les métadonnées indiquent `response_volume`
  et, pour une section, `section_volume` : octets JSON, nœuds et profondeur.
  En cas de refus, on ne prétend pas mesurer toute la section non extraite.
- Identités, datation, ambiguïtés, provenance, non-substitution de version et
  refus des sommaires sans corps restent contrôlés. Pas de pagination inventée,
  de relecture secondaire, de retry ajouté ni de contenu tronqué.

## Validation locale

Windows, Python 3.13, environnement de test isolé MCP 2.2.0 / PyJWT 2.15.0.
Exécution depuis une nouvelle copie sans `.env` réel, construite depuis la
copie assainie précédente et les deux fichiers modifiés ; les anciens gels
ne sont pas réécrits. Aucun appel PISTE ni appel modèle.

- **38 tests ciblés réussis** : 25 existants et 13 nouveaux dans
  [`test_consultation_limits.py`](../tests/test_consultation_limits.py).
- **378 tests de la suite isolée réussis**. Le contrôle des noms Git est
  exécuté séparément sur le véritable dépôt du connecteur : aucun `.env`
  réel suivi. Le test Git de la copie imbriquée ne constitue pas cette preuve.
- Ruff lint/format et `git diff --check` passent.
- Les contrôles plugin, liens, vault, affirmations et commandes passent
  sur la copie assainie. Pas de CI distante, nouvelle image, audit de
  dépendances ou qualification juridique déduits de ces tests locaux.
- Les nouveaux cas sont **synthétiques**, pas une reproduction certifiée
  du corps officiel S01. Ils couvrent les trois limites, UTF-8 et seuil exact,
  séparation parent/section, arrêt d'encodage, cycles, articles incomplets,
  datation et diagnostic MCP avec référence de corrélation sans fuite.

Empreintes SHA-256 des fichiers testés (octets Windows) :

```text
texts.py                       aef3e46095f64cb2a8290ad5bfc0d8aae51ee1f3160644c24e3d95e93eb1ccc3
test_consultation_limits.py     733de0caf908ad0ec2cd48e53b0eff1882ad751686536d12353ae28f71fa03e7
```

Preuves côté DPM : `tests/isolation/r7-connecteur-volumetrie-20261005-v1/`
et `tests/isolation/r7-connecteur-volumetrie-20261005-v1-unit.log`.

## Suite conditionnelle

Une revue/CI puis une bascule du diagnostic nécessitent un accord distinct.
Ensuite seulement, une lecture S01 contrôlée permettra de mesurer la borne
réelle. Une charge officielle assainie obtenue sans credential peut aussi
permettre une reproduction locale. Si le refus subsiste, choisir la stratégie
de récupération complète sur cette preuve, sans relever arbitrairement les
limites ni supprimer la protection du parent. Nouveau préflight strict des
43 cibles avant T04, pilote ou campagne ; aucune qualification stable acquise.
