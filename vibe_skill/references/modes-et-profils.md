# Modes et profils

Les gardes d'entrée sont rappelées dans le noyau ; les développements sont conservés ici.

## Déclenchement du noyau

## Déclenchement

Activer ce skill dès que l'utilisateur :

- cite ou demande un article de loi, de code, un décret, un arrêté, une circulaire,

- demande une qualification juridique (pénale, administrative, civile),

- demande de vérifier si un texte est en vigueur, abrogé ou modifié,

- demande une jurisprudence (Cass., CE, CC, CJUE, CEDH),

- rédige un acte, une note, un mémoire, des conclusions ou une réponse
  institutionnelle,

- audite, relit ou corrige juridiquement un document existant ou un corpus,

- prépare un oral ou écrit de concours impliquant des références juridiques.

**Ne pas activer** pour des questions purement doctrinales sans besoin
de citation vérifiable, ni pour du droit étranger non européen.

## Profil actif et neutralité

## 8. Cas particuliers métier — définis par le profil

Les cas particuliers propres à un métier (textes de référence,
jurisprudences cardinales, pièges récurrents) **ne sont pas codés dans le
noyau** : ils vivent dans la **section 5 du profil actif** (`profil.md`).

- **Profil chargé** → appliquer sa section 5 (ex. pour police-gendarmerie :
  pouvoirs OPJ/APJ, arrêtés de police du maire, MGP/EPT ; pour avocat :
  délais et voies de droit ; etc.). Voir [`profils/`](../profils/).

- **Profil neutre** (pas de `profil.md`) → **aucun cas particulier métier
  n'est présumé**. Les particularités **universelles** du droit français
  (Alsace-Moselle, outre-mer, IDF / petite couronne, champ territorial,
  dispositions transitoires) restent traitées par l'étape 5 et
  [`references/checklist-vigueur.md`](checklist-vigueur.md),
  indépendamment de tout profil.

En cas de contexte décisionnel non couvert par le profil → étape 0 bis
(question obligatoire), jamais d'hypothèse.


## 0. Architecture générale : double mode opératoire

### Chargement du profil (`profil.md`) — avant toute analyse

Le **noyau méthodologique est universel** ; le **métier de l'utilisateur
est un paramètre**. Au déclenchement, si un fichier **`profil.md`** existe
à la racine du skill, le lire : il fixe des **défauts** — contexte
territorial (question 4 de l'étape 0), domaines prioritaires (veille §10),
et **3ᵉ regard d'auto-critique** (rôle (c) de l'étape 7). Profils fournis
dans [`profils/`](../profils/) (police-gendarmerie, avocat, juriste-entreprise,
collectivités, étudiant-concours) ; gabarit vierge `profils/_modele.md`.

**Deux règles impératives :**

1. **Un profil ne fournit que des défauts, jamais des certitudes.** Toute
   valeur (ressort, TA compétent, domaine) est **surchargée sans friction**
   par une requête qui vise autre chose, et **rouverte par l'étape 0 bis**
   dès qu'elle devient décisionnelle. Le profil ne dispense d'aucune
   vérification (P1) ni d'aucune question obligatoire (étape 0 bis).

2. **Sans `profil.md` → profil neutre.** Aucune hypothèse territoriale ou
   métier n'est présumée. Si une information de ce type est décisionnelle,
   l'étape 0 bis la **pose en question** (filet de sécurité), au lieu de
   deviner un contexte.

## Modes et balises

### Double mode opératoire

Le skill fonctionne selon deux modes **mutuellement exclusifs**.

### Mode A — Noyau + modules activables (par défaut)

Mode opératoire normal. Le **noyau invariant** (7 principes, 7 étapes,
4 techniques) s'applique à toutes les requêtes. Des **modules
supplémentaires** se déclenchent automatiquement selon des critères
détectables dans la requête (voir §5).

### Mode B — Exhaustif (dérogatoire)

Mode qui exécute la **totalité des modules** sur toute requête, y
compris ceux qui s'avèrent sans objet (qui répondent alors
explicitement « **sans objet à cette espèce** » avec justification
d'une ligne).

Le mode B n'est pas un mode « plus sûr » que le mode A : il est un
mode plus **traçable**, utile quand la traçabilité institutionnelle
du raisonnement importe autant que sa conclusion (note au Maire
engageant la commune, réponse à signalement, dossier au contrôle de
légalité, exercice de préparation au concours).

### Balises de bascule

| Balise | Effet |

|--------|-------|

| `[complet]` | Force le mode B (tous modules activés). |

| `[express]` | Mode A allégé : supprime l'activation automatique des modules même si leurs déclencheurs sont réunis. **Exceptions : PÉNAL reste actif** en matière répressive (P6) et **DOC-AUDIT reste actif** pour tout audit ou correction de documents. |

| `[syllogisme]` | Active le sous-gabarit « note de concours » (structure majeure / mineure / conclusion). Surcouche du gabarit B. |

| `[opérationnel]` | Active la section « Implications opérationnelles » du gabarit B et le rôle facultatif *responsable opérationnel* à l'étape 7. |

| `[lookup]` | **Voie rapide** : référence ponctuelle non controversée. Dispense de l'en-tête standardisé et de l'encart récapitulatif ; sortie minimale (voir ci-dessous). **N'allège aucune exigence de fond** : P1, règle de provenance et étape 0 bis restent dues. Refusée — bascule en mode A standard — dès qu'une interprétation, une qualification pénale ou un acte est en jeu. |

En l'absence de balise → **mode A standard** avec déclencheurs
automatiques de modules.
