# Formats de citation normalisés (P4)

Complément de P4 dans `SKILL.md`. Formats imposés pour toute citation
dans une sortie du skill. Absence = défaut bloquant à l'étape 6.

---

## Règle générale

Chaque texte ou décision cité doit comporter :
1. La **référence complète** au format ci-dessous
2. Sa **fonction juridique** explicite : compétence / procédure /
   sanction / définition / exception / renvoi / habilitation / contrôle
3. Son **niveau de confiance** si l'affirmation est portée par ce texte seul

Un texte de compétence ne peut être cité comme texte de sanction, et inversement.

## Règle de provenance (P1, impérative)

Tout **identifiant officiel** d'une citation — `LEGIARTI`, `JORFTEXT`,
`NOR`, n° de pourvoi, n° de requête, n° de décision — doit provenir
d'un **appel d'outil effectué dans la session** (`scripts/legifrance.py`
ou `web_fetch`/`web_search` sur domaine officiel). Un identifiant jamais
récupéré **ne se reconstitue pas de mémoire** : il est omis ou marqué
`⚠️ non vérifié — identifiant non récupéré`, et il **interdit le
gabarit C** (citation pour acte). Les gabarits ci-dessous montrent un
identifiant en clair *uniquement* lorsqu'il a été relevé sur la source ;
sinon, ils conservent le marqueur `LEGIARTI…` à compléter, jamais une
valeur inventée.

---

## Format article de code ou de loi

```
Art. [référence complète], [code ou loi],
version en vigueur depuis le JJ/MM/AAAA,
identifiant Légifrance LEGIARTI[numéro],
consulté le JJ/MM/AAAA
```

**Gabarit à compléter** (l'identifiant et la date de version sont à
relever sur Légifrance, jamais à mémoriser ni à deviner) :
```
Art. L. 2212-2, Code général des collectivités territoriales (CGCT),
version en vigueur depuis le JJ/MM/AAAA,
identifiant Légifrance LEGIARTI000000000000,
consulté le JJ/MM/AAAA
```

**Variante courte** (note express, hors acte officiel) :
```
Art. L. 2212-2 CGCT [version JJ/MM/AAAA, LEGIARTI…]
```

---

## Format décret, arrêté, ordonnance

```
[Nature] n° AAAA-NNN du JJ mois AAAA [intitulé abrégé],
art. [x] [si applicable],
JORF du JJ/MM/AAAA, texte n° NN,
identifiant NOR : [NORXXXXXXXX]
```

**Gabarit à compléter** (intitulé exact, NOR et référence JORF à relever
sur Légifrance ou le Journal officiel — aucun de ces éléments ne se déduit) :
```
[Nature] n° AAAA-NNN du JJ mois AAAA [intitulé exact],
art. [x],
JORF n° XXXX du JJ/MM/AAAA, texte n° NN,
identifiant NOR : XXXXNNNNNNNX
```

---

## Format jurisprudence judiciaire (Cour de cassation)

```
Cass. [chambre], JJ mois AAAA, n° XX-XX.XXX, Bull. [n°] (ou : inédit)
Ratio decidendi : [motif décisoire en 1-2 lignes]
[Obiter dictum : [commentaire accessoire] — indice seulement]
```

**Gabarit à compléter** (n° de pourvoi, chambre, mention au Bulletin à
relever sur Judilibre / courdecassation.fr — jamais reconstitués de mémoire) :
```
Cass. [chambre], JJ mois AAAA, n° XX-XX.XXX, Bull. crim. n° NN (ou : inédit)
Ratio decidendi : [motif décisoire en 1-2 lignes]
[Obiter dictum : [commentaire accessoire] — indice seulement]
```

**Abréviations de chambres :**

| Abréviation | Chambre |
|-------------|---------|
| Cass. crim. | Chambre criminelle |
| Cass. civ. 1re / 2e / 3e | Chambres civiles |
| Cass. com. | Chambre commerciale |
| Cass. soc. | Chambre sociale |
| Cass. AP | Assemblée plénière |
| Cass. Ch. mixte | Chambre mixte |

---

## Format jurisprudence administrative (Conseil d'État)

```
CE, [formation], JJ mois AAAA, n° XXXXXX, Lebon (ou : Tables Lebon / inédit)
Ratio decidendi : [motif décisoire en 1-2 lignes]
[Obiter dictum : [commentaire accessoire] — indice seulement]
```

**Exemple :**
```
CE, Sect., 19 mai 1933, n° [non numéroté à l'époque], Benjamin, Lebon p. 541
Ratio decidendi : toute mesure de police administrative doit être
proportionnée à la menace pour l'ordre public ; l'autorité de police
doit choisir la mesure la moins attentatoire aux libertés permettant
d'atteindre le but d'intérêt général.
```

**Formations du Conseil d'État :**

| Abréviation | Formation |
|-------------|-----------|
| CE, Ass. | Assemblée du contentieux (formation solennelle maximale) |
| CE, Sect. | Section du contentieux |
| CE, 2e-7e Ch. réunies | Chambres réunies |
| CE, 2e Ch. | Chambre ordinaire (décision isolée — autorité réduite) |

---

## Format Conseil constitutionnel

```
CC, décision n° AAAA-NNN [QPC ou DC ou L], JJ mois AAAA,
[intitulé], JORF du JJ/MM/AAAA
Dispositif : [conformité / non-conformité / réserve d'interprétation]
```

**Exemple :**
```
CC, décision n° 2010-14/22 QPC, 30 juillet 2010,
M. Daniel W. et autres, JORF du 31/07/2010
Dispositif : non-conformité partielle des articles 62, 63, 63-1, 77
du Code de procédure pénale (régime de la garde à vue).
```

---

## Format CJUE

```
CJUE, [formation], JJ mois AAAA, affaire C-XXX/XX [nom],
ECLI:EU:C:AAAA:NNN
Ratio : [en 1-2 lignes]
```

---

## Format CEDH

```
CEDH, [formation], JJ mois AAAA, [Requérant] c. [État],
requête n° XXXXX/XX, Recueil [AAAA-X] (ou : non publié au Recueil)
Ratio : [en 1-2 lignes]
```

---

## Ratio decidendi vs obiter dictum

| | Ratio decidendi | Obiter dictum |
|---|----------------|---------------|
| Définition | Motif décisoire sur lequel repose le dispositif | Remarque accessoire, considération de principe non nécessaire à la décision |
| Autorité | Fait précédent (dans les limites du système français) | Indice d'orientation — jamais source principale d'autorité |
| Citation | `Ratio decidendi : […]` | `Obiter dictum : […] — indice seulement` |
| Confiance | `[confiance élevée]` si constante | `[confiance modérée]` au mieux |

---

## Grille d'autorité jurisprudentielle (module FOND)

| Critère | Valeurs |
|---------|---------|
| Nature | Arrêt de principe / Solution constante / Solution isolée / Espèce factuellement atypique |
| Formation | Solennelle (Ass., Sect., AP, Ch. mixte) / Ordinaire |
| Publication | Bulletin / Lebon / Tables / Inédit |
| Portée | Ratio decidendi / Obiter dictum |

Une décision isolée en chambre ordinaire, inédite, avec obiter
= autorité minimale → `[confiance faible]`, triangulation obligatoire.

---

## Mention de source informelle (à signaler explicitement)

Quand une information a été identifiée via une source de doctrine privée
ou un outil non officiel, l'indiquer avant la citation vérifiée :

```
[Source d'identification : [publication], [date] — vérifié
sur Légifrance le JJ/MM/AAAA, identifiant LEGIARTI…]
```
