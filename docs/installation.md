# Installer et vérifier Droit français

État du guide : 10 octobre 2026. Les commandes sont relevées sur Claude Code
2.1.288 et Codex CLI 0.162.0-alpha.2. Leur aide a été contrôlée ; le parcours
complet d'installation puis OAuth n'est pas encore qualifié sur ces versions.
Un smoke local du paquet a réussi le 10/10/2026 dans des profils temporaires
vides : installation, liste et retrait sur les deux CLI, réinstallation
Codex et contrôle de mise à jour Claude sans changement de version. Il porte
sur une copie locale des fichiers du dépôt, pas sur l'acquisition GitHub,
la mise à niveau vers une autre version, une nouvelle session ou OAuth.
Voir les [preuves et limites du correctif](correctifs-pr115.md).

Le noyau présent dans le dépôt est 3.5.0 ; le plugin 0.9.0 est un candidat.
La dernière release plugin relevée lors de l'audit porte le numéro 0.7.0.
Une installation depuis main prend le candidat, pas une release stable figée.
Pour une recette reproductible, noter le commit et la version réellement installés.

## Choisir le canal

- **Skill autonome** : méthode uniquement. L'absence de clé PISTE est compatible
  avec une recherche web sur sources officielles si le client permet cet accès.
  Sans moyen de vérification, la réponse doit expliciter cette limite.
- **Plugin du dépôt** : méthode et serveur MCP distant annoncé par la racine
  .mcp.json. Python et PISTE ne sont pas nécessaires sur le poste, mais OAuth
  reste nécessaire pour les outils.
- **Serveur local** : Python, dépendances MCP et identifiants PISTE nécessaires.
  Les huit outils du candidat ne sont pas automatiquement ceux du service distant.

## Claude Code

> **Connexion OAuth bloquée pour une installation neuve du plugin** : le
> client prédéfini et le callback restent à configurer
> ([#88](https://github.com/brissonjo-sudo/droit-francais-skill/issues/88)).
> L'installation du paquet et le chargement de la méthode peuvent être
> vérifiés séparément ; ils ne donnent pas accès aux outils distants.

Installation depuis la marketplace du dépôt :

~~~powershell
claude plugin marketplace add brissonjo-sudo/droit-francais-skill
claude plugin install droit-francais-skill@droit-francais
claude plugin list
~~~

Ouvrir une nouvelle session. Contrôler la présence du skill recherche-juridique
et du serveur dans /mcp. Demander une recherche puis une lecture d'article ;
conserver l'identifiant, la date et les appels observés. Une réponse rappelant
la méthode, sans appel réel, ne prouve pas que le connecteur fonctionne.

Pour mettre à jour, puis relancer la session :

~~~powershell
claude plugin marketplace update droit-francais
claude plugin update droit-francais-skill@droit-francais
~~~

Pour retirer ce plugin uniquement :

~~~powershell
claude plugin uninstall droit-francais-skill@droit-francais
claude plugin list
~~~

## Codex

Le dépôt contient une marketplace native .agents/plugins/marketplace.json :

~~~powershell
codex plugin marketplace add brissonjo-sudo/droit-francais-skill
codex plugin add droit-francais-skill@droit-francais
codex plugin list --json
~~~

Le catalogue est présent dans main depuis l'intégration de
[#115](https://github.com/brissonjo-sudo/droit-francais-skill/pull/115).
Pour tester une branche de recette, remplacer la source GitHub par son
checkout absolu, ou figer la source Git avec --ref COMMIT.

Le catalogue indique l'origine, le nom et la politique d'installation. La
version 0.9.0 et la description du plugin se trouvent dans
.codex-plugin/plugin.json, conformément aux exemples officiels OpenAI ;
elles ne sont pas dupliquées dans les entrées du catalogue. Le chemin ./
est relatif à la racine de la marketplace, pas à .agents/plugins/.

Au 10/10/2026, codex --version et l'aide de chaque sous-commande ci-dessus
ont été relus sur Codex CLI 0.162.0-alpha.2. Les liens officiels en fin de
guide répondent et documentent ces commandes. Ce contrôle d'aide et de
documentation ne constitue pas une recette d'installation ou d'OAuth.

Dans l'application, ajouter la marketplace dans le répertoire des plugins,
installer Droit français puis ouvrir une nouvelle tâche. Vérifier séparément
le skill chargé et l'authentification du MCP. Un catalogue visible n'atteste
ni la connexion OAuth ni une lecture juridique réussie.

Mise à jour de la source puis réinstallation et nouvelle session :

~~~powershell
codex plugin marketplace upgrade droit-francais
codex plugin add droit-francais-skill@droit-francais
~~~

Retrait du plugin uniquement :

~~~powershell
codex plugin remove droit-francais-skill@droit-francais
codex plugin list --json
~~~

## OAuth et dépannage

Les nouveaux clients Claude Code et ChatGPT restent en qualification.
Pour Codex, l'installation complète et le parcours OAuth de cette version
restent également à qualifier ; un succès dans un autre client ne les valide pas.
Voir la [proposition de recette OAuth](recette-oauth-clients.md), le
[guide OAuth](oauth.md) et les issues
[#88](https://github.com/brissonjo-sudo/droit-francais-skill/issues/88) et
[#89](https://github.com/brissonjo-sudo/droit-francais-skill/issues/89).

- Plugin absent : contrôler la marketplace, le nom, le commit, puis redémarrer
  le client. Ne pas confondre codex mcp add avec une installation du skill.
- Outils absents ou 401 : noter le client et la phase OAuth, sans copier jeton,
  code d'autorisation ni secret dans une issue.
- Outils présents mais erreur de récupération : conserver un constat assaini
  séparé ; cela ne valide ni n'invalide la méthode juridique.
- Deux installations du skill : choisir une seule origine active pour la
  recette ; conserver les autres installations sans les réécrire automatiquement.

## Skill autonome

~~~powershell
npx skills add https://github.com/brissonjo-sudo/droit-francais-skill/tree/main/skill --skill recherche-juridique
npx skills update recherche-juridique
~~~

La méthode est utilisable sans le plugin. La gestion et le retrait dépendent
du client et de la portée choisie par skills ; vérifier npx skills --help et
la liste des installations avant de supprimer un répertoire. Ne pas retirer
le dossier du dépôt de développement à la place du skill installé.

Sources des commandes : [Claude Code](https://code.claude.com/docs/en/discover-plugins),
[Codex CLI](https://learn.chatgpt.com/docs/developer-commands) et
[marketplaces OpenAI](https://developers.openai.com/plugins/build/plugins).
