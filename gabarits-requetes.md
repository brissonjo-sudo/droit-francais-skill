# Gabarits de requêtes Légifrance

Requêtes optimisées pour `web_search` et `web_fetch`. À adapter selon le texte.

---

## 1. Article de code — accès direct par identifiant

```
web_fetch("https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049XXXXXX")
```

Produit la fiche complète avec métadonnées (version en vigueur, historique).

---

## 2. Article de code — recherche par numéro d'article

### Via la recherche Légifrance
```
web_search("site:legifrance.gouv.fr codes article_lc \"L. 2212-2\" CGCT")
```

Ou accès direct au code :
```
web_fetch("https://www.legifrance.gouv.fr/codes/article_lc/[identifiant]")
```

### Via la table des matières du code
```
web_fetch("https://www.legifrance.gouv.fr/codes/id/LEGITEXT000006070633/")
```
(LEGITEXT000006070633 = CGCT — remplacer par l'identifiant du code cible)

**Identifiants des codes fréquents :**
| Code | Identifiant LEGITEXT |
|------|----------------------|
| CGCT | LEGITEXT000006070633 |
| Code pénal | LEGITEXT000006070719 |
| CPP | LEGITEXT000006071154 |
| CSI | LEGITEXT000025503132 |
| Code de la route | LEGITEXT000006074228 |
| CRPA | LEGITEXT000031367321 |
| GFP | LEGITEXT000044416551 |
| Code de l'environnement | LEGITEXT000006074220 |
| Code de la santé publique | LEGITEXT000006072665 |
| Code de l'urbanisme | LEGITEXT000006074075 |

---

## 3. Article de code — version à une date précise

Sur la fiche Légifrance, ajouter le paramètre de date :
```
web_fetch("https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049XXXXXX?dateTexte=20240101")
```

Ou via la recherche :
```
web_search("site:legifrance.gouv.fr \"L. 2212-2\" CGCT vigueur 2024")
```

---

## 4. Texte JORF — par numéro de texte

```
web_fetch("https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049XXXXXX")
```

Recherche par NOR :
```
web_search("site:legifrance.gouv.fr JORF NOR INTB2300001C")
```

---

## 5. Jurisprudence Cour de cassation

### Par numéro de pourvoi
```
web_search("site:legifrance.gouv.fr JURI \"n° 23-81.234\"")
```

### Via Légifrance JURI
```
web_fetch("https://www.legifrance.gouv.fr/juri/id/JURITEXT000049XXXXXX")
```

### Via le site de la Cour de cassation
```
web_fetch("https://www.courdecassation.fr/decision/[identifiant]")
```

---

## 6. Jurisprudence Conseil d'État

### Par numéro de requête
```
web_search("site:legifrance.gouv.fr CETAT \"n° 440258\"")
```

### Via Légifrance CETAT
```
web_fetch("https://www.legifrance.gouv.fr/ceta/id/CETATEXT000XXXXXXXXX")
```

### Via le site du CE
```
web_fetch("https://www.conseil-etat.fr/fr/arianeweb/CE/decision/[date]/[numero]")
```

---

## 7. Circulaires et instructions ministérielles

### Par NOR (identifiant normalisation)
```
web_search("site:circulaires.legifrance.gouv.fr NOR INTB2300001C")
```

### Recherche thématique
```
web_search("site:circulaires.legifrance.gouv.fr \"police municipale\" armement 2023")
```

---

## 8. Recherche thématique dans un code

```
web_search("site:legifrance.gouv.fr CGCT \"vidéoprotection\" \"voie publique\"")
```

Ou dans la recherche full-text Légifrance :
```
web_fetch("https://www.legifrance.gouv.fr/search/all?query=vid%C3%A9oprotection+voie+publique&tab_selection=code")
```

---

## 9. Vérification de l'abrogation d'un texte

```
web_fetch("https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049XXXXXX")
```
→ Lire les métadonnées : présence/absence de "Abrogé par".

Ou via la recherche :
```
web_search("site:legifrance.gouv.fr LEGIARTI000049XXXXXX abrogé")
```

---

## 10. Historique des versions d'un article

Depuis la fiche article Légifrance, cliquer "Versions" ou :
```
web_fetch("https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049XXXXXX#historique")
```

---

## 11. Conventions collectives (KALI)

```
web_search("site:legifrance.gouv.fr KALI IDCC [numéro] \"accord\" vigueur")
```

```
web_fetch("https://www.legifrance.gouv.fr/conv_coll/id/KALICONT000XXXXXXXXX")
```

---

## Patterns de refus — quand la recherche échoue

Si `web_fetch` retourne une erreur ou un contenu inexploitable :
```
⚠️ ÉCHEC D'ACCÈS : La fiche Légifrance pour [référence] n'a pas pu être
consultée (erreur HTTP [code] / contenu non lisible).

Je refuse de citer ce texte sans vérification directe. Accéder manuellement à :
https://www.legifrance.gouv.fr/codes/article_lc/[identifiant si connu]
ou : https://www.legifrance.gouv.fr/search/all?query=[référence]
```
