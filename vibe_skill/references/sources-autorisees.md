# Sources autorisées — hiérarchie et usage (P3)

Complément de P3 dans `SKILL.md`. Définit les sources admises par niveau
d'autorité et les conditions d'usage pour chaque catégorie.

---

## Ordre de recherche et autorité

### P3 — Autorité, authenticité et articulation des sources

Ne pas confondre trois questions : la source est-elle authentique, quel est le
rang de la norme, et quel effet une décision produit-elle sur son application ?

Ordre de recherche :

1. **Textes officiels publiés** (Légifrance / JORF).

2. **Décisions juridictionnelles officielles** (Cass., CE, CC, CJUE, CEDH),
   qui peuvent interpréter, écarter ou neutraliser l'application d'un texte
   selon leur compétence et leur autorité.

3. **Circulaires et instructions officielles**.

4. **Doctrine institutionnelle**.

Cet ordre organise la recherche ; il ne constitue pas une hiérarchie abstraite
où un texte primerait toujours sur une décision qui en contrôle l'application.

La **doctrine privée** (Dalloz, JCP, blogs spécialisés) ne peut fonder
seule une affirmation normative, mais peut servir comme outil
d'identification, de contextualisation ou de signalement d'une
controverse doctrinale. Elle apparaît alors **explicitement** comme
telle, jamais comme source citable en propre.


→ Bloque modes 6, 7, 8.


Les niveaux ci-dessous organisent la recherche et la qualité de provenance.
Ils ne remplacent ni la hiérarchie des normes ni l'autorité propre des
décisions juridictionnelles. Vérifier séparément l'authenticité de la source,
le rang de la norme et l'effet de la décision sur son application.

### Niveau 1 — Textes officiels publiés

| Source | URL | Usage |
|--------|-----|-------|
| Légifrance | legifrance.gouv.fr | Codes, lois, décrets, arrêtés, ordonnances — **source de référence obligatoire** |
| JORF (Journal Officiel) | legifrance.gouv.fr/jorf/jo | Textes non codifiés, avis, décisions publiées. `journal-officiel.gouv.fr` est un site distinct (DILA, annonces légales — associations, BALO), **pas** la source des lois/décrets |
| EUR-Lex | eur-lex.europa.eu | Droit de l'UE (règlements, directives) — vérifier transposition FR séparément |
| CEDH (arrêts et décisions) | echr.coe.int | Convention EDH et protocoles |

Condition d'usage : **lecture documentée** du texte intégral (pas survol
d'un résultat de recherche). Capturer l'identifiant officiel et la date
de version en vigueur (voir `format-citation.md`).

### Niveau 2 — Décisions juridictionnelles officielles

| Juridiction | Source officielle | Identifiants |
|-------------|------------------|--------------|
| Cour de cassation | courdecassation.fr | n° de pourvoi, chambre, Bulletin (ou inédit) |
| Conseil d'État | conseil-etat.fr | n° de recours, formation, Lebon / Tables / inédit |
| Conseil constitutionnel | conseil-constitutionnel.fr | n° de décision (ex. 2021-xxx QPC) |
| TA / CAA (juridictions admin.) | ArianeWeb (conseil-etat.fr/arianeweb/) | n° requête, juridiction, date |
| Cours d'appel judiciaires | Judilibre (courdecassation.fr/recherche-judilibre — `judilibre.fr` n'est pas un domaine existant) | n° RG, cour, chambre, date |
| CJUE | curia.europa.eu | Affaire C-xxx/xx, ECLI |

Condition d'usage : distinguer **ratio decidendi** (motif décisoire,
fait précédent) et **obiter dictum** (commentaire accessoire, indice
seulement). Ne jamais citer un obiter comme source d'autorité principale.

Vérifier l'absence de **revirement postérieur** avant toute citation.

### Niveau 3 — Circulaires et instructions officielles

| Source | URL | Usage |
|--------|-----|-------|
| Circulaires (rubrique Légifrance) | legifrance.gouv.fr | Circulaires publiées, instructions interministérielles — le sous-domaine `circulaires.legifrance.gouv.fr` redirige vers le site principal depuis la refonte Légifrance d'avril 2026 |
| Bulletins officiels ministériels | selon ministère | BO Intérieur, BO Justice, BO Éducation… |

Condition d'usage : circulaire **publiée** uniquement. Une circulaire
interne non publique (DGGN, DGPN, préfecture, parquet, note de service
DGS, instruction préfectorale) déclenche le **déclencheur d'abstention
n° 4** : signaler l'existence probable pour recherche interne par
l'utilisateur, ne pas spéculer sur son contenu.

### Niveau 4 — Doctrine institutionnelle

| Source | Exemples | Usage |
|--------|----------|-------|
| Rapports parlementaires | Rapports Sénat, AN — senat.fr / assemblee-nationale.fr ; dossiers législatifs, études d'impact et avis du Conseil d'État sur les projets/propositions de loi — vie-publique.fr depuis le 1er avril 2026 (migration hors Légifrance) | Contextualisation, ratio légis |
| Études et avis du Conseil d'État | conseil-etat.fr/avis-publications | Doctrine administrative de référence |
| Direction des Affaires Juridiques (DAJ) | économie.gouv.fr/daj | Actes de la commande publique, marchés |
| Fiches pratiques DGCL | collectivites-locales.gouv.fr | Droit des collectivités territoriales |

Condition d'usage : peut fonder une affirmation normative **à condition
d'être accompagnée d'un texte officiel de niveau 1 ou 2** confirmant la
proposition. Ne constitue jamais une source autonome.

---

## Sources non admises comme sources normatives

| Catégorie | Exemples | Statut autorisé |
|-----------|----------|----------------|
| Doctrine privée | Dalloz, LexisNexis, JCP, Revue de droit public | Identification, contextualisation, signalement d'une controverse — **jamais citée en propre** |
| Blogs et sites spécialisés | Dalloz actualité, blogs d'avocats, Village de la Justice | Piste de recherche uniquement — **non citable** |
| Encyclopédies collaboratives | Wikipédia | **Exclue** comme source juridique |
| IA génératives (réponses d'autres LLM) | ChatGPT, Gemini, etc. | **Exclue** — risque de mode 1 cumulé |
| Manuels universitaires | Droit administratif de X, Traité de procédure pénale | Identification et contextualisation — non citable comme source normative |

Quand une source de doctrine privée est utilisée comme piste
d'identification, elle doit être **transparente** : « J'ai identifié
l'article X via [source] — je le vérifie maintenant sur Légifrance. »

---

## Règles d'usage croisé

- **Convergence de sources** (même conclusion via niveaux 1+2) : renforce
  la confiance → `[confiance élevée]` si jurisprudence constante.
- **Divergence entre niveaux** (circulaire contredisant la jurisprudence) :
  le niveau supérieur prévaut ; signaler la divergence explicitement.
- **Source unique de niveau 1 sans jurisprudence** sur un point interprétatif :
  → `[confiance modérée]` minimum ; triangulation obligatoire si l'acte
  fait grief (voir étape 4 dans `SKILL.md`).
- **Absence de source officielle** sur un point : abstention informée (P7),
  pas de déduction à partir de sources de niveau 4 seul.

## Primarité et provenance de session

## 2. Les 7 principes structurants (noyau invariant)

### P1 — Primarité

Aucune affirmation juridique ne peut s'appuyer sur la mémoire
d'entraînement seule. Toute citation suppose l'accès au texte intégral
officiel (ou à l'extrait officiel contenant l'intégralité du passage
cité) **et** la vérification explicite de sa version applicable à la
date de référence.

La consultation effective n'est pas le survol d'un résultat de
recherche : c'est la **lecture documentée** de la source officielle
(Légifrance — dont sa rubrique Circulaires, le sous-domaine
`circulaires.legifrance.gouv.fr` redirigeant vers le site principal depuis
la refonte d'avril 2026 —, courdecassation.fr, conseil-etat.fr,
conseil-constitutionnel.fr, JORF).

**Règle de provenance (impérative, v2.3.0).** Tout **identifiant
officiel** figurant dans une sortie — `LEGIARTI…`, `JORFTEXT…`,
`NOR`, n° de pourvoi, n° de requête, n° de décision — doit provenir
d'un **appel d'outil effectué dans la session courante** (récupération
en source primaire : selon l'ordre normé de l'**étape 2**, *échelle de récupération* :
connecteur MCP officiel disponible, sinon `scripts/legifrance.py`,
à défaut `web_fetch`/`web_search` sur un domaine officiel). Un identifiant qui n'a pas
été récupéré ne peut **jamais** être reconstitué de mémoire : il est
soit omis, soit marqué `⚠️ non vérifié — identifiant non récupéré`. La
conformité apparente de la procédure (afficher les étapes 0 à 7,
l'en-tête, l'encart) ne dispense **pas** de cette provenance : produire
le cérémonial sans la récupération est une **simulation de procédure**,
traitée comme un défaut bloquant à l'étape 6. Un identifiant non
récupéré interdit la voie **gabarit C** (citation pour acte).

La règle est **indifférente à la voie** : un identifiant récupéré par
`web_fetch` sur Légifrance vaut exactement un identifiant récupéré par
l'API ; un identifiant non récupéré ne vaut rien dans les deux cas.
L'absence de clé PISTE n'abaisse donc jamais le niveau de preuve — elle
change seulement le moyen d'atteindre la source.

→ Bloque modes 1, 2, 3.

## Limites des voies de vérification

## 9. Limites et précautions du skill lui-même

- Ce skill ne remplace pas l'avis d'un juriste ou d'un avocat pour
  les décisions à fort enjeu contentieux.

- La qualité dépend de l'accessibilité de Légifrance et des autres
  sources au moment de la requête.

- Pour les textes anciens non codifiés (avant numérisation
  Légifrance), la vérification manuelle au JORF papier peut être
  nécessaire.

- Les textes UE (EUR-Lex) suivent leur propre nomenclature ; vérifier
  la transposition en droit français séparément.

- **Palier 3 (API PISTE) — outillé depuis la v2.3.0.** L'étape 2
  (récupération) peut être automatisée et fiabilisée par les
  métadonnées officielles via [`scripts/legifrance.py`](../scripts/legifrance.py)
  (API Légifrance **et** Judilibre, toutes deux via PISTE). C'est le moyen
  privilégié de satisfaire P1 et la règle de provenance : l'identifiant
  `LEGIARTI`, la date de version en vigueur et le statut (en vigueur /
  modifié / abrogé) proviennent alors d'une réponse officielle, non de la
  mémoire du modèle. L'**ordre des voies** (outillée → repli web →
  abstention) est normé à l'**étape 2** et ne se rejoue pas ici : à défaut
  d'accès API, la voie web conserve son risque de rendu incomplet, sans
  abaisser d'un cran l'exigence de provenance. Les étapes 0, 0 bis, 4, 5,
  6, 7 et les techniques T1/T2/T3/T4 restent essentielles.
