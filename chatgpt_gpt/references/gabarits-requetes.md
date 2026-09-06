# Gabarits de requêtes Légifrance — voie web

Requêtes et adresses types pour la **voie 2** des instructions du GPT
(`instructions.md`) : recherche web restreinte aux domaines officiels, puis
lecture de la page trouvée. À adapter selon le texte cherché.

> **Priorité.** Si l'app « Droit français » est activée dans ce GPT, ses six
> outils passent avant tout ce qui suit : la récupération y est déterministe
> et les métadonnées (identifiant `LEGIARTI`, dates de version, applicabilité)
> proviennent directement de la source officielle. Les gabarits ci-dessous
> sont la voie de repli, et l'arbitrage entre les voies se fait dans les
> instructions, pas ici.

> **Ne jamais citer depuis un extrait de résultat de recherche.** Une requête
> ne fait que localiser la page ; l'identifiant, la date de version et le
> texte se relèvent sur la page ouverte.

---

## 1. Article de code — accès direct par identifiant

Ouvrir :
```
https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049XXXXXX
```

La fiche porte le texte, la version en vigueur et l'historique.

---

## 2. Article de code — recherche par numéro d'article

Rechercher :
```
site:legifrance.gouv.fr codes article_lc "L. 2212-2" CGCT
```

Ou passer par la table des matières du code :
```
https://www.legifrance.gouv.fr/codes/id/LEGITEXT000006070633/
```
(`LEGITEXT000006070633` = CGCT — remplacer par l'identifiant du code cible)

**Identifiants des codes fréquents :**

| Code | Identifiant LEGITEXT |
|------|----------------------|
| CGCT | LEGITEXT000006070633 |
| Code pénal | LEGITEXT000006070719 |
| CPP | LEGITEXT000006071154 |
| CSI | LEGITEXT000025503132 |
| Code de la route | LEGITEXT000006074228 |
| CRPA | LEGITEXT000031366350 |
| GFP | LEGITEXT000044416551 |
| Code de l'environnement | LEGITEXT000006074220 |
| Code de la santé publique | LEGITEXT000006072665 |
| Code de l'urbanisme | LEGITEXT000006074075 |

Ces identifiants localisent un code ; ils ne dispensent jamais de relever
l'identifiant `LEGIARTI` de l'article lui-même.

---

## 3. Article de code — version à une date précise

Ajouter le paramètre de date à l'adresse de la fiche :
```
https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049XXXXXX?dateTexte=20240101
```

Ou rechercher :
```
site:legifrance.gouv.fr "L. 2212-2" CGCT vigueur 2024
```

Relever les dates de début et de fin de version, puis les comparer à la date
d'évaluation avant de conclure à l'applicabilité.

---

## 4. Texte JORF — par numéro de texte

```
https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049XXXXXX
```

Recherche par NOR :
```
site:legifrance.gouv.fr JORF NOR INTB2300001C
```

---

## 5. Jurisprudence Cour de cassation

Par numéro de pourvoi :
```
site:legifrance.gouv.fr JURI "n° 23-81.234"
```

Fiche Légifrance :
```
https://www.legifrance.gouv.fr/juri/id/JURITEXT000049XXXXXX
```

Site de la Cour de cassation :
```
https://www.courdecassation.fr/decision/[identifiant]
```

---

## 6. Jurisprudence Conseil d'État

Par numéro de requête :
```
site:legifrance.gouv.fr CETAT "n° 440258"
```

Fiche Légifrance :
```
https://www.legifrance.gouv.fr/ceta/id/CETATEXT000XXXXXXXXX
```

Site du Conseil d'État :
```
https://www.conseil-etat.fr/fr/arianeweb/CE/decision/[date]/[numero]
```

---

## 7. Jurisprudence Conseil constitutionnel

Par numéro de décision :
```
site:legifrance.gouv.fr CONSTIT "n° 2021-940 QPC"
```

Fiche Légifrance :
```
https://www.legifrance.gouv.fr/constit/id/CONSTEXT000XXXXXXXXX
```

Site du Conseil constitutionnel :
```
https://www.conseil-constitutionnel.fr/decision/[année]/[numéro compacté].htm
```

---

## 8. Circulaires et instructions ministérielles

Par NOR :
```
site:legifrance.gouv.fr circulaire NOR INTB2300001C
```

> Le sous-domaine `circulaires.legifrance.gouv.fr` redirige vers le site
> principal depuis la refonte Légifrance d'avril 2026 : une requête ciblant
> encore ce sous-domaine risque de ne plus renvoyer de résultats indexés.

Recherche thématique :
```
site:legifrance.gouv.fr circulaire "police municipale" armement 2023
```

---

## 9. Recherche thématique dans un code

```
site:legifrance.gouv.fr CGCT "vidéoprotection" "voie publique"
```

Ou par la recherche plein texte de Légifrance :
```
https://www.legifrance.gouv.fr/search/all?query=vid%C3%A9oprotection+voie+publique&tab_selection=code
```

---

## 10. Vérification de l'abrogation d'un texte

Ouvrir la fiche de l'article et lire ses métadonnées : présence ou absence
d'une mention « Abrogé par ».
```
https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049XXXXXX
```

Une absence de mention lue sur la page vaut constatation ; une absence
supposée ne vaut rien.

---

## 11. Historique des versions d'un article

Depuis la fiche, ouvrir l'onglet « Versions » :
```
https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049XXXXXX#historique
```

---

## 12. Conventions collectives (KALI)

```
site:legifrance.gouv.fr KALI IDCC [numéro] "accord" vigueur
```

```
https://www.legifrance.gouv.fr/conv_coll/id/KALICONT000XXXXXXXXX
```

---

## Quand la recherche échoue

Si la page ne s'ouvre pas ou reste illisible, appliquer P7 sans détour :

```
⚠️ ÉCHEC D'ACCÈS : la fiche Légifrance pour [référence] n'a pas pu être
consultée (erreur ou contenu non lisible).

Source non confirmée — abstention sur ce point. Je ne cite pas ce texte sans
l'avoir lu. Pour vérifier directement :
https://www.legifrance.gouv.fr/codes/article_lc/[identifiant si connu]
ou https://www.legifrance.gouv.fr/search/all?query=[référence]
```

Un échec d'accès ne se compense jamais par une citation de mémoire, même pour
un article réputé connu.
