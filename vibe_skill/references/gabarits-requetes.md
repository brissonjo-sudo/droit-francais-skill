# Gabarits de requêtes Légifrance

Requêtes optimisées pour la recherche et la récupération web. À adapter selon
le texte.

> **Noms d'outils.** Ce fichier écrit `web_fetch` / `web_search` de façon
> générique. Selon l'assistant, l'outil réel diffère : en **Claude Code** ce
> sont `WebFetch` / `WebSearch`. Utiliser le nom exposé par l'environnement.

> **Voie privilégiée (Palier 3, v2.3.0) — API PISTE.** Quand des
> identifiants PISTE sont configurés, préférer
> [`scripts/legifrance.py`](../scripts/legifrance.py) aux requêtes
> `web_fetch` ci-dessous : la récupération y est déterministe et les
> métadonnées (identifiant `LEGIARTI`, date de version en vigueur,
> statut abrogé/modifié) sont officielles — ce qui satisfait P1 et la
> **règle de provenance**. Exemples :
> ```
> python scripts/legifrance.py article LEGIARTI000006419288
> python scripts/legifrance.py article --date 2024-01-01 LEGIARTI000006419288
> python scripts/legifrance.py search "2212-2" --code CGCT
> python scripts/legifrance.py ceta "440258"             # CE — fond CETAT
> python scripts/legifrance.py constit "2021-940 QPC"    # CC — fond CONSTIT
> python scripts/legifrance.py juri "sans consentement" --jurisdiction cc
> python scripts/legifrance.py decision <identifiant>    # texte intégral
> python scripts/legifrance.py taxonomy chamber --jurisdiction cc
> ```
> **Deux routes distinctes, à ne pas confondre.** `juri` / `decision` /
> `taxonomy` interrogent **Judilibre** (Cour de cassation, cours d'appel,
> tribunaux) : recherche **plein texte** — et non par numéro — avec
> récupération du **texte intégral** par `decision`. `ceta` / `constit`
> interrogent les fonds **Légifrance** `CETAT` / `CONSTIT` : recherche
> *best-effort* **par numéro**, renvoyant l'**identifiant officiel**
> (`CETATEXT` / `CONSTEXT`) à confirmer avant citation.
> **Judilibre ne couvre ni le Conseil d'État ni le Conseil
> constitutionnel** : pour ces deux juridictions, `ceta` / `constit` sont
> la seule voie outillée.
> Les requêtes `web_fetch`/`web_search` ci-dessous restent la **voie de
> repli** lorsque l'API n'est pas accessible — ordre normé à l'**étape 2**
> du SKILL.md (*échelle de récupération*), qui est le seul lieu
> d'arbitrage des voies.

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
| CRPA | LEGITEXT000031366350 |
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

## 4 bis. Article d'un décret non codifié — récupérer son identifiant

Constat du 17/11/2026 (décret n° 87-602, outils MCP `search_articles` et
`fetch`) : `search_articles` ne retrouve pas l'article d'un décret non
codifié, que l'on passe le numéro de l'article seul ou le numéro du décret
(résultat vide, ou articles homonymes d'autres codes).

Avant le contournement manuel : `search_texts(number=…)` ou
`search_texts(nor=…)` (fonds LODA, depuis 3.7.0) ; il renvoie le `LEGITEXT`,
puis `get_text` ou `get_article` lisent le texte.

Contournement manuel qui a abouti :

1. Ouvrir la page consolidée du texte (LODA) pour y relever l'identifiant
   `LEGIARTI` de l'article visé ; une page longue se lit par tranches
   (`offset` de `WebFetch`) :
   ```
   web_fetch("https://www.legifrance.gouv.fr/loda/id/JORFTEXT000000XXXXXX")
   ```
2. Récupérer l'article par cet identifiant avec l'outil officiel (`fetch`
   ou `get_article`). Seul ce texte reçu prouve le contenu : le résumé de
   la page renvoyé par `WebFetch` ne vaut pas source primaire.
3. Contrôler `applicable_at_as_of_date` et les dates de version : un
   identifiant relevé sur la page peut désigner une version **abrogée**
   (cas de l'article 33 du décret n° 87-602 le 17/11/2026). Dans ce cas,
   ne pas citer cette version comme en vigueur.

Une erreur PISTE ponctuelle (« Authentification PISTE échouée », HTTP 400)
a disparu en relançant une fois le même appel ; elle ne prouve ni
l'absence ni l'abrogation du texte. Échec répété : abstention ciblée.

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

## 7. Jurisprudence Conseil constitutionnel

### Par numéro de décision
```
web_search("site:legifrance.gouv.fr CONSTIT \"n° 2021-940 QPC\"")
```

### Via Légifrance CONSTIT
```
web_fetch("https://www.legifrance.gouv.fr/constit/id/CONSTEXT000XXXXXXXXX")
```

### Via le site du Conseil constitutionnel
```
web_fetch("https://www.conseil-constitutionnel.fr/decision/[année]/[numéro compacté].htm")
```

---

## 8. Circulaires et instructions ministérielles

### Par NOR (identifiant normalisation)
```
web_search("site:legifrance.gouv.fr circulaire NOR INTB2300001C")
```
> Le sous-domaine `circulaires.legifrance.gouv.fr` redirige vers le site
> principal depuis la refonte Légifrance d'avril 2026 : un `site:` ciblant
> encore ce sous-domaine risque de ne plus renvoyer de résultats indexés.

### Recherche thématique
```
web_search("site:legifrance.gouv.fr circulaire \"police municipale\" armement 2023")
```

---

## 9. Recherche thématique dans un code

```
web_search("site:legifrance.gouv.fr CGCT \"vidéoprotection\" \"voie publique\"")
```

Ou dans la recherche full-text Légifrance :
```
web_fetch("https://www.legifrance.gouv.fr/search/all?query=vid%C3%A9oprotection+voie+publique&tab_selection=code")
```

---

## 10. Vérification de l'abrogation d'un texte

```
web_fetch("https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049XXXXXX")
```
→ Lire les métadonnées : présence/absence de "Abrogé par".

Ou via la recherche :
```
web_search("site:legifrance.gouv.fr LEGIARTI000049XXXXXX abrogé")
```

---

## 11. Historique des versions d'un article

Voie outillée : outil MCP `get_article_history(id)` — versions datées,
textes modificateurs et version applicable (voir checklist de vigueur,
point 5).

Voie de repli : depuis la fiche article Légifrance, cliquer "Versions" ou :
```
web_fetch("https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049XXXXXX#historique")
```

---

## 12. Conventions collectives (KALI)

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
