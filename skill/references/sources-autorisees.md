# Sources autorisées — hiérarchie et usage (P3)

Complément de P3 dans `SKILL.md`. Définit les sources admises par niveau
d'autorité et les conditions d'usage pour chaque catégorie.

---

## Ordre de recherche et autorité

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
