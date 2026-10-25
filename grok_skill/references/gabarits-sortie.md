# Gabarits de sortie — détail

> Référencé depuis `SKILL.md §6`. Lire ce fichier avant toute rédaction de livrable.
> Tout gabarit commence par l'en-tête standardisé et se termine par l'encart récapitulatif.

---

Chaque gabarit débute obligatoirement par un **en-tête standardisé**
(absence = défaut bloquant) et se termine par un **encart final
récapitulatif**.

Dans une réponse, un fichier de skill ou de référence se cite par le nom du
skill et la section (ex. « dcp-fpt, §5.5 »), jamais par un lien Markdown ni
par un chemin, relatif ou absolu. Seules les sources officielles (URL
Légifrance, sites publics) prennent la forme d'un lien.

### En-tête standardisé (obligatoire)

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

### Encart final récapitulatif (obligatoire)

```
─────────────────────────────────────────────
Modules activés                       : […]
Modules non activés                   : […]
Niveau de confiance global            : [élevé | modéré | faible]
Sources informelles signalées         : [existence probable, non consultées : …]
Limites de la recherche               : […]
─────────────────────────────────────────────
```

### Gabarit A — Note express

Pour : qualification rapide, recherche ponctuelle, vérification éclair.

```
[En-tête standardisé]

## Étape 0 — Qualification de la demande
- Nature : […]
- Date(s) de référence : […]
- Domaine / code : […]
- Champ territorial : […]
- Niveau : note express
- Test de régime : […]
- Désambiguïsation factuelle : […]

## Étape 0 bis — Arbitrage des informations manquantes
- Informations manquantes : […]
- Classement décisionnel / non décisionnel : […]
- Question(s) posée(s) [si décisionnelle] OU hypothèse(s) déclarée(s) [si non décisionnelle] : […]

## Réponse
[Prose avec citations en ligne au format normalisé,
niveaux de confiance par affirmation.]

J'en déduis que [...] [confiance modérée — justification une ligne]

⚠️ Reste à vérifier : [...]

## Étape 7 — Auto-critique adversariale
- Contradicteur : [...]
- Cassation / contrôle de légalité : [...]
- 3ᵉ regard du profil actif (section 4 de `profil.md`) : [...]

[Encart final récapitulatif]

Recherche effectuée le JJ/MM/AAAA.
Vérification recommandée avant tout usage dans un acte officiel.
```

### Gabarit B — Note de fond

Pour : analyse pour mémoire, préparation concours, réponse
institutionnelle (note au Maire, réponse questionnaire sénatorial),
dossier au contrôle de légalité.

```
[En-tête standardisé]

## Étape 0 — Qualification de la demande
[Six questions + désambiguïsation factuelle]

## Étape 0 bis — Arbitrage des informations manquantes
[Informations manquantes, classement décisionnel/non décisionnel,
question(s) obligatoire(s) ou hypothèse(s) déclarée(s). Si une
information décisionnelle manque : esquisse conditionnelle bornée
seulement, pas d'analyse complète.]

## I. Problème de droit
[Reformulation précise.]

## II. Textes applicables
- [Citation normalisée 1] — fonction juridique : [compétence | sanction | …]
  Contenu : [...]
  Renvois résolus : [...]
  Dispositions transitoires : [...]
- [Citation normalisée 2]
  […]

## III. Jurisprudence
- [Citation arrêt 1] — ratio : [...] ; obiter éventuel : [...]
- [Citation arrêt 2] — [...]

## IV. Discussion
[Articulation textes / arrêts, registres séparés (P5),
niveaux de confiance par affirmation, raisonnement par distinction
si précédent invoqué.]

## V. Conclusion
[Réponse au problème de droit, niveau de confiance global.]

## VI. Limites de la recherche
- Points non vérifiés : […]
- Hypothèses retenues : […]
- Sources informelles signalées : […]

## VII. Implications opérationnelles  [si balise [opérationnel]]
[Mise en œuvre, moyens, articulation police nationale.]

## Étape 7 — Auto-critique adversariale
[Trois (ou quatre) rôles explicites]

[Encart final récapitulatif]
```

### Gabarit C — Citation pour acte

Pour : visa d'arrêté, considérants, motivation d'une décision.
**Citation seule, sans paraphrase, vérifiée doublement.**

```
[En-tête standardisé]

[Référence normalisée complète, avec identifiant Légifrance et date
de consultation]

Texte intégral de l'article / extrait pertinent :
« [...] »

Fonction juridique : [compétence | habilitation | sanction | …]
Source : [URL Légifrance directe]
Vérifié le : JJ/MM/AAAA
Statut : en vigueur à la date du JJ/MM/AAAA
Triangulation : [chemin 1 + chemin 2]

[Encart final récapitulatif]
```

### Gabarit D — Audit documentaire

Pour : audit, relecture juridique ou correction directe d'un ou plusieurs
fichiers. Le registre complet peut rester un document de travail ; la
synthèse doit montrer immédiatement les corrections et les limites.

```
[En-tête standardisé]

## Périmètre
- Fichiers contrôlés : […]
- Date du droit : […]
- Audit antérieur : […] (sans présomption de conformité)

## Corrections effectuées
- [fichier / emplacement] : [ancienne proposition] → [correction]
  Motif : [source / conséquence / compétence / date / cohérence]

## Contrôles transversaux
- Affirmations à risque élevé : [n/n traitées]
- Matrice acteur–lieu–propriétaire–pouvoir : [complète / limites]
- Divergences interdocuments : [résolues / ouvertes]
- Recherche post-correction : [résultat]

## Points restant à vérifier ou arbitrer
- […]

## Étape 7 — Auto-critique adversariale
- Conséquence opérationnelle excessive encore possible : […]
- Résidu ou divergence possible : […]

[Encart final récapitulatif]
```

Ne jamais écrire « conforme » si le contrôle à 100 % du risque élevé ou le
contrôle post-correction n'est pas achevé.

### Sous-gabarit « note de concours » (balise `[syllogisme]`)

Surcouche du gabarit B structurant explicitement le raisonnement :

```
## Majeure — Règle de droit applicable
[Règle identifiée et citée, format normalisé, fonction juridique.]

## Mineure — Faits qualifiés
[Faits formalisés et qualifiés à la lumière de la règle.]

## Conclusion — Application motivée
[Application de la règle aux faits, niveau de confiance,
qualifications concurrentes écartées (T1).]
```

Utile pour les épreuves de concours (profil étudiant-concours) et tout
raisonnement à structure imposée. Non imposée aux autres gabarits.

---

## Voie rapide lookup

### Voie rapide `[lookup]` — sortie minimale

Pour la simple lecture-référence d'un texte non controversé (« quel
article réprime X ? », « L. 2212-2 CGCT est-il en vigueur ? »),
l'appareil complet (en-tête + 9 étapes visibles + encart) est
disproportionné. La balise `[lookup]` produit alors :

```
[Citation normalisée avec identifiant récupéré] — fonction juridique : […]
[Réponse en 1–3 phrases] [confiance : élevée | modérée | faible — 1 ligne]
```

**Garde-fous (non négociables)** : la citation suppose une
récupération réelle en source primaire (P1) et un identifiant de
provenance vérifiée (règle de provenance) ; si la récupération échoue,
la voie rapide bascule en **abstention motivée** (§7). En cas de doute
sur le caractère « non controversé », `[lookup]` est **ignorée** et le
mode A standard s'applique.

**Aucune balise ne dispense de l'étape 0 bis** (arbitrage des
informations manquantes) : ni `[express]`, ni `[complet]`. Le mode B
notamment ne « compense » pas une information décisionnelle manquante
par l'exhaustivité — il produirait alors une analyse complète sur une
fondation non vérifiée (voir étape 0 bis).

## Traçabilité proportionnée

### Traçabilité proportionnée

Les contrôles sont obligatoires ; leur affichage dépend du livrable. Une
réponse courte expose les sources, la date applicable, les réserves utiles et
la confiance sans réciter la procédure. Une note de fond, un audit ou une
demande `[complet]` ajoute l'encart récapitulatif : mode, modules activés,
confiance globale, sources informelles et limites. `[lookup]` conserve sa
sortie minimale. La provenance des identifiants reste obligatoire dans tous
les cas.

## Registres de restitution

### P5 — Séparation des registres

Dans toute réponse, distinguer **explicitement** quatre registres :

| Registre | Préfixe / format |

|----------|------------------|

| (a) Texte | citation ou paraphrase fidèle, accompagnée du format normalisé |

| (b) Jurisprudence | citation d'arrêt, format normalisé, ratio/obiter signalé |

| (c) Déduction | introduite par **« J'en déduis que… »** ou **« Par voie de conséquence… »** |

| (d) Incertitude | introduite par **« Reste à vérifier… »** ou bloc `⚠️ À VÉRIFIER` |

Le mélange de ces registres est la première source d'erreur de
raisonnement.

→ Bloque modes 5, 6, 14.

## Abstention ciblée et clarification

## 7. Déclencheurs d'abstention (ou sortie dégradée balisée)

Le skill s'arrête sur le point concerné et le signale, plutôt que de
spéculer, dans **dix cas** :

1. **Source primaire inaccessible** (Légifrance indisponible, URL non
   résolue, erreur HTTP).

2. **Texte trouvé** mais date d'entrée en vigueur ou disposition
   transitoire **impossible à confirmer**.

3. **Décision juridictionnelle** invoquée dont la **référence exacte
   est introuvable**.

4. **Circulaire interne non publique** (DGGN, DGPN, préfecture,
   parquet, note de service DGS, instruction préfectorale) : signaler
   l'**existence probable** pour recherche interne par l'utilisateur,
   ne **pas spéculer** sur le contenu.

5. **Faits postérieurs au cutoff** d'entraînement, non vérifiables
   par recherche web.

6. **Matière répressive** : doute sérieux sur un élément constitutif
   (P6).

7. **Échec de la triangulation obligatoire** (étape 4).

8. **Renvoi normatif essentiel** introuvable ou non résolu (mode 12).

9. **Délai de prescription ou de forclusion** possiblement expiré,
   sans possibilité de calcul certain.

10. **Information décisionnelle détenue par le seul utilisateur,
    manquante** (étape 0 bis) : ne pas déployer d'analyse complète sur
    une hypothèse non levée ; poser la question et, au plus, livrer
    une esquisse conditionnelle bornée.

**Format d'abstention motivée** :

```
**⚠️ Information non vérifiable — abstention motivée**

Je ne peux pas produire de citation fiable pour [référence] à la
date du [date] pour la raison suivante : [motif précis dans la
liste ci-dessus].

Démarches alternatives :
- Accéder directement à : [URL officielle]
- Consulter : [autre source officielle]
- Source informelle à vérifier en interne : [si applicable]

Je préfère m'abstenir plutôt que spéculer.
```

**Format de clarification motivée (cas n° 10, étape 0 bis)** :

```
**Question préalable nécessaire**

Un point conditionne la réponse et je ne peux pas le trancher seul :
[formulation fermée ou à choix de la question].

Pourquoi c'est déterminant : [une ligne — quel régime / quelle
conclusion bascule selon la réponse].

Esquisse conditionnelle (bornée) :
- Si [a] → [orientation en une ou deux lignes].
- Si [b] → [orientation en une ou deux lignes].

Je traite la suite dès que ce point est précisé.
```

Dans tous les cas, **l'abstention est ciblée** sur le point précis et
n'empêche pas la livraison du reste de l'analyse avec sortie dégradée
balisée (P7).


### P7 — Abstention informée et sortie dégradée balisée

Si une vérification en source primaire est impossible, ou si une
condition d'abstention prévue par la procédure est réunie, le skill
le signale et **s'arrête sur le point concerné**. Pas de complétion
par spéculation déguisée en certitude.

L'abstention porte sur **le point précis** où la vérification échoue,
pas nécessairement sur l'intégralité de la réponse. Les éléments
vérifiés restent livrables avec leur niveau de confiance ; les
éléments non vérifiés sont explicitement marqués comme tels.

Une **sortie dégradée balisée** (« texte trouvé, version non
confirmée », « point litigieux à vérifier », « jurisprudence non
localisée ») est généralement plus utile qu'une abstention totale.

**Corollaire d'entrée (v2.1.0).** L'abstention informée a un pendant
au stade de l'entrée : quand l'information manquante est **décisionnelle
et détenue par le seul utilisateur**, le skill ne spécule pas et ne
« déclare » pas une hypothèse pour avancer — il **pose la question**
(voir étape 0 bis). P7 régit la sortie ; l'étape 0 bis régit l'entrée.

→ Bloque modes 1, 2, 3, 5, 6.

## Choix du livrable

## 6. Gabarits de sortie

**Gabarit A** — Note express · **Gabarit B** — Note de fond · **Gabarit C** — Citation
pour acte · **Gabarit D** — Audit documentaire · **Sous-gabarit
`[syllogisme]`** — Note de concours (surcouche B).
