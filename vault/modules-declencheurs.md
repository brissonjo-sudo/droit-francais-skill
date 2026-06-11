---
tags: [skill/recherche-juridique, reference]
---

# Modules, techniques, abstention

## 5 Modules activables (mode A)

Règle conservatrice : en cas de doute sur le déclenchement, le module s'active. Mode B force tous les modules.

| Module | Déclencheurs | Règles clés |
|--------|-------------|-------------|
| **PÉNAL** | Fait à qualifier pénalement ; mention infraction (contravention/délit/crime) ; visa pénal ; préparation PV | Non désactivable par `[express]`. P6 strict (111-3 et 111-4 CP). Décomposition : élt légal (texte en vigueur à date faits) + élt matériel + élt moral + aggravants + justificatifs + régime procédural + charge et modes de preuve. Triangulation si interprétation en jeu (E4) |
| **ACTE-ADMIN** | Rédaction / analyse / contrôle acte admin : arrêté, décision individuelle, mesure police, sanction disciplinaire, refus autorisation (y compris analyse rétrospective) | Compétence renforcée (auteur, délégation, territoriale, temporelle). Proportionnalité Benjamin (CE 19/05/1933) : adaptée / nécessaire / proportionnée s.s. Motivation (L. 11/07/1979 si applicable). Opposabilité (publication, affichage, signalisation). Éléments de preuve justifiant la mesure. Triangulation obligatoire si acte faisant grief |
| **PA-PJ** | Opération susceptible d'être PA ou PJ : constatation, interpellation, contrôle, mesure préventive | Mini-grille obligatoire : finalité (préventive PA / répressive PJ) ? autorité agissante ? temporalité par rapport au fait ? régime procédural applicable ? |
| **FOND** | Niveau exigence = note de fond / citation pour acte / concours ; ou interprétation explicitement controversée | T3 (archéologie textuelle) obligatoire. Grille autorité jurisprudentielle par arrêt : principe / constante / isolée / factuellement atypique / formation solennelle ou ordinaire / ratio decidendi / obiter dictum |
| **CONTENTIEUX** | Question portant sur risque de recours / stratégie procédurale / voie de droit envisagée | Identifier régime contentieux : REP / plein contentieux / référé suspension / référé liberté / exception illégalité / nullité pénale. Conséquences : office du juge + charge argumentative + moyens opérants + délais de recours |

## 4 Techniques de raisonnement

| # | Technique | Description |
|---|-----------|-------------|
| **T1** | Qualification adversariale | Formuler les qualifications concurrentes plausibles et expliquer en 1 phrase pourquoi elles sont écartées. Réflexe simultané parquet + défense |
| **T2** | Triangulation | Croiser 2 chemins de vérification indépendants (ex. numéro article + recherche thématique ; texte + circulaire + jurisprudence). Convergence renforce, divergence alerte (modes 3/4). Conditions d'obligation : voir `procedure-compacte.md` |
| **T3** | Archéologie textuelle | Retracer : version initiale → principales modifications → raison politique/jurisprudentielle de la dernière réforme. Évite contresens par lecture hors contexte |
| **T4** | Distinction | Identifier les éléments qui différencient la situation du précédent invoqué (factuel, temporel, territorial, qualité d'acteur, pouvoir). Un précédent national ne s'applique pas automatiquement à une situation locale |

## 10 Déclencheurs d'abstention (ou sortie dégradée balisée)

| # | Déclencheur | Conduite |
|---|-------------|---------|
| 1 | Source primaire inaccessible (Légifrance down, URL non résolue, HTTP err) | Abstention motivée |
| 2 | Texte trouvé, date vigueur ou disposition transitoire impossible à confirmer | Abstention motivée ou sortie dégradée balisée |
| 3 | Décision juridictionnelle invoquée, référence exacte introuvable | Abstention motivée |
| 4 | Circulaire interne non publique (DGGN, DGPN, préfecture, parquet, DGS) | Signaler existence probable pour recherche interne ; ne pas spéculer sur le contenu |
| 5 | Faits postérieurs au cutoff, non vérifiables par web | Abstention motivée |
| 6 | Matière répressive : doute sérieux sur un élément constitutif (P6) | Abstention motivée — pas de qualification affirmative comme certaine |
| 7 | Échec de la triangulation obligatoire (E4) | Abstention motivée sur le point concerné |
| 8 | Renvoi normatif essentiel introuvable ou non résolu (mode 12) | Abstention motivée |
| 9 | Délai de prescription ou de forclusion possiblement expiré, calcul incertain | Abstention motivée |
| 10 | Information décisionnelle détenue par le seul utilisateur, manquante (E0bis) | Format « Question préalable nécessaire » (voir ci-dessous) |

L'abstention est **ciblée** sur le point précis — le reste de l'analyse reste livrable avec sortie dégradée balisée (P7).

## Formats d'abstention

### Format standard (déclencheurs 1–9)

```
## ⚠️ Information non vérifiable — abstention motivée

Je ne peux pas produire de citation fiable pour [référence] à la
date du [date] pour la raison suivante : [motif précis].

Démarches alternatives :
- Accéder directement à : [URL officielle]
- Consulter : [autre source officielle]
- Source informelle à vérifier en interne : [si applicable]

Je préfère m'abstenir plutôt que spéculer.
```

### Format déclencheur 10 (E0bis)

```
## Question préalable nécessaire

Un point conditionne la réponse et je ne peux pas le trancher seul :
[formulation fermée ou à choix de la question].

Pourquoi c'est déterminant : [une ligne — quel régime / quelle
conclusion bascule selon la réponse].

Esquisse conditionnelle (bornée) :
- Si [a] → [orientation en une ou deux lignes].
- Si [b] → [orientation en une ou deux lignes].

Je traite la suite dès que ce point est précisé.
```

## Cas particuliers Police Municipale (Saint-Ouen)

| Situation | Point de vigilance |
|-----------|-------------------|
| Arrêtés de police admin | L. 2212-1 et L. 2212-2 CGCT (générale) vs L. 2213-1–32 (spéciales). Lex specialis peut dessaisir la police générale |
| Polices spéciales (enviro, urbanisme, domaine public, sécu routière) | Vérifier si police spéciale dessaisit ou encadre (E5 contrôle 3) |
| Champ territorial | Saint-Ouen = petite couronne → partage compétences avec PP pour certaines polices |
| Qualifications pénales | Date référence = date faits (P2+P6). Comparer versions pour rétroactivité in mitius |
| Compétences intercommunales MGP/EPT | Point E0bis typique : compétence statutaire (conseil territoire décide seul) vs supplémentaire (L. 5211-17 CGCT, communes votent) → question obligatoire avant toute analyse |
| Arrêté municipal hors champ | Illégal, attaquable devant TA Montreuil |
| Conventions collectives | Identifier IDCC + vérifier version convention + accord entreprise |
| Jurisprudence cardinale police admin | CE 19/05/1933 Benjamin (proportionnalité) ; CE 26/10/2011 Commune Saint-Denis n°326492 (motivation + circonstances locales) |
