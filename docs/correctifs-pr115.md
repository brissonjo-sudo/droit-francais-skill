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
