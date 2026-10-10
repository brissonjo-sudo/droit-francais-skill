# Livraison : audit d'adoption et préparation de la campagne

**Trace historique de la première préparation du 10/10/2026.** Les 521 tests,
versions de clients et empreintes ci-dessous décrivent ce candidat antérieur,
pas le harnais v2. Voir le [bilan de relecture actuel](relecture-campagne-116.md)
et le [protocole actuel](campagne-18-modes.md). Les preuves anciennes sont
conservées ; elles ne qualifient aucun runtime ni corrigé supplémentaire.

10 octobre 2026. Base : main, commit 17a2bb88e0187d6eb1e906f0ef7c83c2ab9564d8.
Candidat préparé dans un worktree séparé ; aucun changement au noyau juridique.

| Constat | Correction livrée | Preuve et reste à faire |
|---|---|---|
| Promesse absolue non mesurée | Promesse testable ; exemple ancien explicitement historique | Contrôle documentaire ; trois exemples contemporains après campagne |
| Local/distant/publication confondus | Tableau des canaux, texte et description marketplace cohérents | Statique ; recette d'installation réelle par client encore ouverte |
| Cycle de vie incomplet | Installation, vérification, mise à jour et retrait ; marketplace native Codex | Aides CLI contrôlées, commandes non exécutées sur les installations du compte |
| OAuth nouveaux clients bloqué | Recette et variante de configuration concrètes | Issues 88/89 maintenues ouvertes ; aucun changement Auth0 ou de production |
| Utilité actuelle des 18 modes inconnue | Corpus 36 cas, quatre bras, trois adaptateurs et lanceur phasé | Zéro corrigé humain validé ; zéro réponse principale mesurée |
| Adoption non observée | Formulaire volontaire J+7/J+30 et métadonnées proposées | Aucune télémétrie ou publication des paramètres GitHub |

## Validation locale effectuée

- 521 tests unitaires/protocole passent, dont 27 non-régressions de campagne.
- Dépendances installées dans un environnement isolé : MCP 2.2.0 et PyJWT 2.15.0.
  Python global porte des versions différentes et ne doit pas servir à qualifier ce candidat.
- Catalogue MCP réellement énuméré en stdio : fetch, get_article, get_decision,
  get_section, get_text, search, search_articles, search_case_law.
- Empreinte SHA-256 des noms et schémas sérialisés :
  7afe9cc1b205e6682ec3bc7afdc08b075fcc2007d2f1f61eb43a8045a269bf2e.
- Contrôles du socle plugin, liens, affirmations, commandes et vault passent ;
  corpus et compilation Python vérifiés ; git diff --check sans défaut.
- L'évaluation historique hors ligne imprime sa check-list ; elle n'exécute
  aucun modèle et ne constitue pas une mesure des modes.
- Aucun appel modèle, API payante ou recherche PISTE effectué pour cette livraison.

L'énumération du catalogue confirme le transport et ses schémas, pas une
récupération de droit positif. Les tests incluent des fixtures de contrats
Codex/Gemini synthétiques ; celles-ci ne valent pas preuve de leur runtime.

## Frontière restante

Claude Code 2.1.288 est authentifié via claude.ai avec abonnement Pro ;
Codex CLI 0.162.0-alpha.2 indique une connexion ChatGPT. Ce sont des constats
d'authentification, pas une qualification des modèles retenus.
Gemini CLI n'a pas été trouvée au contrôle effectué sur ce poste.

Avant collecte : choisir les modèles exacts accessibles dans les abonnements,
préparer le client Gemini et son authentification, compléter puis relire les
36 corrigés, commiter et figer, qualifier chaque préflight, puis revoir le pilote.
Un modèle effectif absent du flux Codex bloque la série ; aucun alias demandé
n'est enregistré comme preuve du modèle utilisé.

Le [protocole](campagne-18-modes.md) détaille le budget, la reprise, le jugement
indépendant et l'ablation limitée à six modes. Les variantes expérimentales
restent séparées du skill ; toute suppression de règles exige une décision
ultérieure fondée sur les résultats.

La CI distante, les recettes d'installation/OAuth, la revue juridique, la mesure
et la sélection des exemples restent des preuves distinctes. Cette livraison
n'est ni une release publiée, ni un déploiement, ni une validation métier.
