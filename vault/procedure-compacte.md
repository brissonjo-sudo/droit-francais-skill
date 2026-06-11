---
tags: [skill/recherche-juridique, reference]
---

# Procédure 9 étapes — table compacte

## Étapes × actions × critères de sortie

| Étape | Visible | Action clé | Critère de sortie | Modes bloqués |
|-------|:-------:|------------|-------------------|:-------------:|
| **0** Qualification | ✓ | 6 questions : nature / dates / domaine+code / territorial / niveau exigence / test régime. Désambiguïsation : qui, quand, où, qualité, pouvoir, envers qui | 6 réponses + désambig complète. Ambiguïté ou info manquante → E0bis avant de chercher | 4, 7, 10, 14 |
| **0bis** Arbitrage | ✓ | Test décisionnel par info manquante : conclusion/régime/qualification/procédure bascule ? → décisionnelle (question oblig) ou non décisionnelle (hypothèse déclarée) | Toute info classée. Décisionnelle → question posée + recherche suspendue. Non décisionnelle → hypothèse déclarée. Aucune analyse complète sur branche non confirmée | -(prévient 10, 14 en amont) |
| **1** Cartographie | — | Lister sources à consulter : article+code, juridiction, circulaire, décret de renvoi | Liste écrite, hiérarchisée selon P3 | — |
| **2** Récupération | — | Lire source + capturer identifiant officiel + date vigueur + suivre renvois normatifs jusqu'à source ultime + test cumulatif/alternatif (« et » vs « ou ») | ID et date notés pour chaque source. Renvois résolus ou marqués non résolus | 1, 12, 13 |
| **3** Fraîcheur | — | Vérifier : Modifié par ? Abrogé par ? Version en vigueur depuis ? Vacatio legis ? Dispositions transitoires ? Décisions QPC ? | État d'application à date de référence confirmé, transitoires incluses. Sinon → abstention P7 ou sortie dégradée balisée | 2, 3, 11 |
| **4** Jurisprudence | — | Arrêt de principe + vérif. revirement. Qualifier : Bulletin/inédit, Lebon/Tables/inédit, ratio/obiter. Triangulation si obligatoire (voir table ci-dessous) | Interprétation = décision identifiée + non infirmée. Si triangulation oblig : 2 sources primaires concordantes + 1 décision confirmant. Échec → abstention P7 sur ce point | 3, 5, 6, 7, 14 |
| **5** Articulation | — | 7 contrôles : ① décret(s) appli publié(s) ② conformité normes sup. (Constit., CEDH, UE) ③ lex generalis/specialis ④ champ territorial et personnel ⑤ compétence auteur (délégation, territ., temporelle) ⑥ opposabilité (publication, affichage, signalisation) ⑦ délais et prescriptions | Texte applicable ET opposable ET auteur compétent ET délai non expiré | 8, 9, 10, 12 |
| **6** Rédaction | — | Citation granulaire (P4) + 4 registres visuellement distincts (P5) + niveau de confiance par affirmation + justification 1 ligne + contrôle texte-cible (le texte cité répond à la question précise, pas seulement au mot-clé) | Chaque affirmation = citation + niveau confiance. Contrôle texte-cible exécuté | 1, 4, 5, 14 |
| **7** Auto-critique | ✓ | 3 rôles : (a) contradicteur — qualification concurrente ? (b) cassation/légalité — faiblesse censurable ? (c) jury concours — question d'oral fatale ? (d) directeur opérationnel si `[opérationnel]`. Trou identifié → retour étape concernée avant livraison | 3 (ou 4) rôles joués. Résultat en rubrique « Auto-critique adversariale » | 4, 5, 6, 8, 14 |

## Règle de triangulation (E4) — quand obligatoire

| Situation | Triangulation |
|-----------|:------------:|
| Qualification pénale + interprétation en jeu (élt constitutif discutable, qualification concurrente, analogie, divergence) | Obligatoire |
| Motivation d'acte administratif faisant grief | Obligatoire |
| Citation pour acte officiel | Obligatoire |
| Doute sur le caractère interprétatif → règle conservatrice | Obligatoire |
| Constatation matérielle sans ambiguïté (PV stationnement, excès vitesse flagrant, infraction code route évidente) | Non requise |
| Lecture-référence d'un article non controversé | Non requise |

Exigence en triangulation obligatoire : **≥ 2 sources primaires concordantes + ≥ 1 décision confirmant l'interprétation, non infirmée.**

## Balises de bascule

| Balise | Mode | Effet |
|--------|------|-------|
| *(aucune)* | A standard | Modules auto-activés selon déclencheurs |
| `[express]` | A allégé | Pas d'activation auto des modules sauf PÉNAL (non désactivable) |
| `[complet]` | B exhaustif | Tous modules activés ; modules sans objet → « sans objet à cette espèce » + justification 1 ligne |
| `[syllogisme]` | surcouche B | Sous-gabarit concours : majeure / mineure / conclusion |
| `[opérationnel]` | surcouche | + rôle (d) directeur opérationnel en E7 + section VII Implications du gabarit B |

**Invariant :** aucune balise ne dispense de E0bis. Le mode B sur fondation décisionnelle non levée produit une analyse complète sur une hypothèse — c'est le cas d'échec typique visé par E0bis.

## En-tête standardisé (obligatoire, toute sortie)

```
─────────────────────────────────────────────
Date d'analyse           : JJ/MM/AAAA
Date(s) de référence     : JJ/MM/AAAA (substantiel) / JJ/MM/AAAA (procédural) / …
Date des faits           : JJ/MM/AAAA
Date d'action / analyse  : JJ/MM/AAAA
Champ territorial        : [national | IDF | Seine-Saint-Denis | commune | …]
Régime juridique primaire: [police générale | police spéciale | répressif | …]
Niveau d'exigence        : [note express | note de fond | citation pour acte]
Mode opératoire          : [A standard | A express | B complet]
─────────────────────────────────────────────
```

## Encart final récapitulatif (obligatoire, toute sortie)

```
─────────────────────────────────────────────
Modules activés                       : […]
Modules non activés                   : […]
Niveau de confiance global            : [élevé | modéré | faible]
Sources informelles signalées         : […]
Limites de la recherche               : […]
─────────────────────────────────────────────
```
