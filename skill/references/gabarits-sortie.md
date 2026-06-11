# Gabarits de sortie — détail (v2.2.0)

> Référencé depuis `SKILL.md §6`. Lire ce fichier avant toute rédaction de livrable.
> Tout gabarit commence par l'en-tête standardisé et se termine par l'encart récapitulatif.

---

Chaque gabarit débute obligatoirement par un **en-tête standardisé**
(absence = défaut bloquant) et se termine par un **encart final
récapitulatif**.

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
- Jury de concours : [...]

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

Utile pour l'oral de Commissaire de Police. Non imposée aux autres
gabarits.

---
