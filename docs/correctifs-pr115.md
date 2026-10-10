# Correctifs après la revue de #115

État du 10/10/2026. La PR #115 a été intégrée par squash dans main. Ce lot
traite les remarques restantes sur la distribution et la découvrabilité ;
il ne modifie ni le serveur, ni le noyau juridique, ni le déploiement.

| Remarque de la revue | Correction ou preuve | Limite |
|---|---|---|
| OAuth Claude Code trop peu visible | Avertissement au début des sections Claude Code du README et du guide ; issue #88 encore ouverte et configuration du client/callback absente | Pas d'essai OAuth ni de modification Auth0 |
| Résumé anglais retiré | README anglais complet, accessible dès la première ligne des deux langues ; français par défaut | Guides liés et contenu du skill restent en français |
| Description GitHub à 14 modes | Description alignée sur 18 modes, appliquée et relue le 10/10/2026 | Topics inchangés ; aucune mesure d'adoption déduite |
| Schéma du catalogue Codex non vérifié | Forme actuelle conforme aux exemples OpenAI ; version 0.9.0 et description dans le manifeste du plugin ; smoke du client réel réussi | Aucun champ non documenté ajouté au catalogue |
| Sources externes et version CLI | Pages officielles ouvertes, aide locale et versions relevées ; jugement TA d'Orléans référencé en source primaire et paraphrase resserrée sur son texte | Autres références historiques du README non revérifiées par ce lot |
| J+7/J+30 hors périmètre annoncé | Suivi volontaire explicitement inclus ; J0 fixé à la première tentative d'installation par testeur | Pas de cohorte, retour, télémétrie ou rappel automatique créé |

## Smoke local du paquet

Les CLI observées sont Claude Code 2.1.288 et Codex CLI 0.162.0-alpha.2.
Les commandes d'aide ont été relues. Le smoke utilise une copie des fichiers
du checkout correctif, dans un répertoire distinct des profils et du cache.
Les profils temporaires sont vides avant installation ; le répertoire de
travail ne contient ni configuration projet ni identifiants. CODEX_HOME,
CLAUDE_CONFIG_DIR et le cache de plugins Claude pointent vers ces profils
temporaires. Aucune session de génération, authentification ou commande MCP
n'a été lancée.

| Client | Opérations observées | Résultat |
|---|---|---|
| Codex | marketplace add locale, plugin add, list --json, second plugin add, remove, list --json | Tous les codes de sortie sont 0 ; plugin 0.9.0, politique ON_USE ; liste finale installée vide |
| Claude Code | marketplace add locale, plugin install, list --json, update, uninstall, list --json | Tous les codes de sortie sont 0 ; plugin 0.9.0 ; mise à jour indiquant la même version ; liste finale vide |

Les fichiers de configuration personnels contrôlés par hash avant/après
(configuration Codex, état et configuration Claude, registres de plugins
et marketplaces Claude) sont inchangés. Les fichiers suivis de la source
sont également inchangés. L'adaptateur et le noyau sont présents dans le
cache Codex installé avant son retrait.

La première tentative sandbox a échoué sur la canonicalisation du profil
Codex Windows. Une tentative hors sandbox avec le cache placé sous la
source a ensuite dépassé la borne de 45 secondes ; ce montage de recette
a été abandonné. La recette réussie utilise des profils extérieurs à la
source, sur une copie sans artefacts de travail. Ces tentatives ne sont pas
présentées comme une recette d'installation réussie depuis GitHub.

Ce smoke ne qualifie ni téléchargement GitHub, rafraîchissement d'une
marketplace Git, changement de version, chargement de méthode dans une
nouvelle tâche, OAuth, disponibilité du MCP ou recherche juridique réelle.
Le service distant historique et le candidat local restent évalués séparément.

## Sources et contrôles

- [Commandes Codex officielles](https://learn.chatgpt.com/docs/developer-commands) : add/list/remove et marketplace add/upgrade.
- [Catalogue et manifeste OpenAI](https://developers.openai.com/plugins/build/plugins) : chemins relatifs à la racine de la marketplace et séparation des métadonnées.
- [Répertoire de configuration Claude](https://code.claude.com/docs/en/claude-directory) : portée de CLAUDE_CONFIG_DIR et stockage des plugins.
- [TA Orléans, 29/12/2025, n° 2506461](https://opendata.justice-administrative.fr/recherche/shareFile/TA45/DTA_2506461_20251229) : texte indexé officiel lu le 10/10/2026, section « Sur les décisions juridictionnelles citées ». La page ouverte seule demande JavaScript ; la lecture a été obtenue par le texte indexé du même portail. Ce passage ne permet pas d'attribuer les références à une IA déterminée.

Les contrôles locaux du socle plugin, des liens Markdown, des affirmations,
des commandes, du vault et du corpus historique passent. run_eval.py ne fait
qu'afficher sa checklist hors ligne ; il n'apporte aucune mesure de réponse
LLM. La CI distante et la revue de la PR corrective restent distinctes.

## Suivi de la relecture de #118 — 10/10/2026

La [relecture de #118](https://github.com/brissonjo-sudo/droit-francais-skill/pull/118#pullrequestreview-5480374724)
porte sur le commit 0560a7c, avant ce suivi. Son avis est « approuvable »,
avec deux points de suivi et aucun bloquant. Le tableau qualifie les preuves
selon product-adoption-review ; il s'agit d'un suivi correctif, sans nouvel
audit d'adoption ni nouveau journal d'usage.

| Identifiant | Changement et preuve | État de preuve / portée | Limite |
|---|---|---|---|
| readme-language-parity | Contrôle hors réseau tests/check_readme_parity.py : ordre des niveaux de titre, dimensions des tableaux, langues des blocs, commandes, cibles et occurrences des liens, versions, navigation dès la première ligne ; tests de mutations et étape CI ajoutés | observed / current : contrôle et tests locaux | Ne vérifie ni équivalence sémantique de la traduction ni contenu distant des liens ; accepte ancres traduites et suffixes .en.md/.fr.md pour les pages locales |
| translated-guide-language | Les liens vers docs/ dans README.en.md portent « in French » | observed / current : lecture du fichier | Les guides liés restent en français |
| installation-evidence-age | Le guide distingue le relevé du 10/10/2026 des versions futures et demande de rafraîchir versions, aide, sources et recette à chaque release | observed / current : consigne documentaire | Aucun smoke ni OAuth rejoué pendant ce suivi ; le smoke précédent reste observed / earlier |
| squash-dependent-branches | Procédure proposée ci-dessous : intégrer main dans chaque branche dépendante après un squash et examiner les conflits | declared / current : procédure proposée | Aucun merge, rebase, push ni squash effectué par ce suivi ; relecture des branches après leur actualisation requise |

Les tests de parité refusent une cible externe remplacée à nombre de liens
constant, un changement de commande ou de version, un niveau de titre
modifié, une colonne/ligne de tableau ou un bloc retiré et une navigation
altérée. Ils acceptent la prose et les commentaires traduits, et un lien
vers le même titre traduit. Le contrôle est aussi joué sur les deux README
réels. Il complète check_links.py, qui contrôle l'existence des cibles locales.
La CI verte citée dans la relecture concerne 0560a7c ; une CI de ce suivi
reste à obtenir après publication du commit.

check_links.py ignore désormais exactement tests/bench/runs, qui contient
des artefacts privés non suivis, après calcul du chemin relatif à la racine
du dépôt. Une régression place un clone sous un parent nommé runs et un
guide public dans docs/runs : son lien cassé reste détecté, tandis qu'un
brouillon privé cassé est ignoré. Aucune preuve ni aucun brouillon supprimé.
Au 10/10/2026, les huit tests ciblés passent ; la compilation des quatre
scripts, les contrôles parité, liens (77 fichiers), plugin, affirmations
et commandes passent localement. Ces preuves statiques ne renouvellent
ni le smoke d'installation, ni la qualification OAuth, ni une mesure LLM.

### Actualiser les branches dépendantes après chaque squash

Un squash crée un nouveau commit dans main : l'ancien commit partagé par
les branches n'est pas reconnu comme un ancêtre de ce nouveau commit.
Cela ne rend pas un rebase ni un force-push obligatoires. Sur chaque branche
dépendante, après avoir vérifié un checkout propre et sa base actualisée :

```powershell
git fetch origin
git merge origin/main
```

Résoudre les conflits éventuels en conservant le contenu effectivement
intégré et les ajouts propres à la branche ; comparer ensuite le diff de
cette branche avec origin/main, rejouer ses contrôles et actualiser son
descriptif de PR. Une fusion de main conserve l'historique de la branche et
permet un push normal. Après le squash suivant, répéter cette actualisation
sur les branches encore ouvertes. Le choix et l'exécution relèvent de
l'orchestration, après lecture de leur état réel ; aucune réécriture
d'historique n'est présumée nécessaire.
