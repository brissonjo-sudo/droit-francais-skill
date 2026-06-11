---
tags: [skill/recherche-juridique, reference]
---

# Matrice modes d'erreur × garde-fous

## Modes → bloqués par (P = principe, E = étape)

| # | Mode | Bloqué par |
|---|------|------------|
| 1 | Hallucination de référence | P1, P4, P7, E2, E6 |
| 2 | Effet de cutoff | P1, P2, P7, E3 |
| 3 | Confusion de versions | P1, P2, P6, E3, E4 |
| 4 | Confusion d'articles voisins | P4, E0, E6, E7 |
| 5 | Analogie non vérifiée | P5, P6, P7, E4, E6, E7 |
| 6 | Confusion doctrine/texte | P3, P4, P5, P7, E4, E7 |
| 7 | Confusion de juridictions | P3, P4, E0, E4 |
| 8 | Oubli hiérarchie des normes | P3, E5, E7 |
| 9 | Oubli décret d'application | E5 |
| 10 | Oubli champ territorial | E0, E5, E0bis |
| 11 | Oubli dispositions transitoires | P2, E3 |
| 12 | Oubli renvois normatifs | E2, E5 |
| 13 | Inversion cumulatif/alternatif | E2 |
| 14 | Faux positif textuel / mauvaise fonction juridique | P4, P5, P6, E0, E0bis, E4, E6, E7 |

## Principes → modes bloqués

| Principe | Résumé en 5 mots | Modes |
|----------|------------------|-------|
| P1 Primarité | Pas de mémoire seule | 1, 2, 3 |
| P2 Date de référence | Date faits vs date analyse | 2, 3, 11 |
| P3 Hiérarchie sources | Texte > jurisprud > circulaire > doctrine | 6, 7, 8 |
| P4 Citation traçable + fonction juridique | Format + fonction pour chaque texte | 1, 4, 6, 7, 14 |
| P5 Séparation registres | Texte / jurisprud / déduction / incertitude | 5, 6, 14 |
| P6 Légalité criminelle | 111-3 et 111-4 CP, rétroactivité in mitius | 2, 3, 5, 11, 14 |
| P7 Abstention informée | S'arrêter sur le point, pas tout | 1, 2, 3, 5, 6 |

## Hiérarchie des sources (P3)

1. Texte officiel publié (Légifrance / JORF)
2. Décision juridictionnelle officielle (Cass., CE, CC, CJUE, CEDH)
3. Circulaires et instructions officielles (circulaires.legifrance.gouv.fr)
4. Doctrine institutionnelle (rapports parlementaires, études CE, DAJ)

Doctrine privée (Dalloz, JCP, blogs) : identification et contextualisation seulement, jamais source normative en propre.

## Formats de citation normalisés (P4)

**Article :**
`Art. [réf], [code], version en vigueur depuis le JJ/MM/AAAA, LEGIARTI…, consulté le JJ/MM/AAAA`

**Jurisprudence judiciaire :**
`Cass. [chambre], JJ mois AAAA, n° XX-XX.XXX, Bull. (ou : inédit)`

**Jurisprudence administrative :**
`CE, [formation], JJ mois AAAA, n° XXXXXX, Lebon (ou : Tables / inédit)`

## Registres P5 (préfixes visuels)

| Registre | Préfixe |
|----------|---------|
| Texte | citation normalisée |
| Jurisprudence | citation arrêt normalisée |
| Déduction | « J'en déduis que… » / « Par voie de conséquence… » |
| Incertitude | « Reste à vérifier… » / bloc `⚠️ À VÉRIFIER` |

## Niveaux de confiance (E6)

| Niveau | Critère |
|--------|---------|
| `[confiance élevée]` | Texte clair + jurisprudence constante |
| `[confiance modérée]` | Interprétation établie mais débattue |
| `[confiance faible]` | Zone grise, jurisprudence divergente ou absente |
