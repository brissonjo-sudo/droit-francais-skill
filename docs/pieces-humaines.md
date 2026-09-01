# Pièces humaines avant soumission

Dernière mise à jour : 1er septembre 2026

Tout ce qui reste à faire pour soumettre le plugin et que le dépôt **ne peut
pas porter** : comptes, captures, enregistrement, réglages de consoles. Chaque
pièce dit pourquoi elle est exigée, comment la produire, et où consigner le
résultat. Aucun secret ne doit atterrir ici ni dans une issue publique.

Ordre conseillé : commencer par l'identité OpenAI (délai le plus long), puis
Auth0 (#27 et compte de démonstration), puis les sondes, puis la vidéo.

| # | Pièce | Bloque | Exige |
|---|---|---|---|
| 1 | [Identité vérifiée OpenAI Platform](#1-identité-vérifiée-openai-platform) | soumission | compte OpenAI, pièce d'identité |
| 2 | [Auth0 — refermer les permissions par défaut (#27)](#2-auth0--refermer-les-permissions-par-défaut-issue-27) | publication | admin Auth0 |
| 3 | [Compte de démonstration sans MFA](#3-compte-de-démonstration-sans-mfa) | soumission | admin Auth0 |
| 4 | [Sonde des six outils avec jeton (#34)](#4-sonde-des-six-outils-avec-jeton-issue-34) | registre E4 | application M2M Auth0 |
| 5 | [Essai avec un second compte](#5-essai-avec-un-second-compte) | publication | deux comptes |
| 6 | [Exercice du retrait d'urgence (E10)](#6-exercice-du-retrait-durgence-judilibre-e10) | audit | accès Render |
| 7 | [Enregistrement vidéo](#7-enregistrement-vidéo) | soumission | écran, 5 minutes |
| 8 | [Vérification de domaine](#8-vérification-de-domaine) | soumission | jeton du portail, accès Render |
| 9 | [Captures Auth0 de la check-list](#9-captures-auth0-de-la-check-list) | audit | admin Auth0 |
| 10 | [Version et tag de soumission](#10-version-et-tag-de-soumission) | soumission | une PR |

---

## 1. Identité vérifiée OpenAI Platform

**Pourquoi** — le relecteur vérifie que nom, site, support, confidentialité et
conditions concordent avec une identité vérifiée. Sans elle, le formulaire ne
peut pas être envoyé.

**Faire**

1. Sur OpenAI Platform, ouvrir les réglages de l'organisation et lancer la
   vérification d'identité (individuelle ou commerciale). Choisir celle dont le
   nom public correspondra au développeur affiché dans l'annuaire.
2. Vérifier que le compte porte le droit **Apps Management: Write**.
3. Relire, une fois l'identité connue, que ce nom est cohérent avec
   [`privacy-policy.md`](privacy-policy.md), [`terms-of-use.md`](terms-of-use.md)
   et le nom de développeur qui sera saisi dans le formulaire (section
   « Info »). Si le dossier [`chatgpt-app-submission.json`](../chatgpt-app-submission.json)
   doit changer, relancer `python tests/check_plugin.py`.

**Consigner** — la date et le type d'identité dans la feuille de route ; rien
d'autre.

## 2. Auth0 — refermer les permissions par défaut (issue #27)

**Pourquoi** — pendant le diagnostic des 30–31 août, *Default Permissions for
third-party applications → User-delegated Access* a été passé de « Unauthorized »
à « All ». Ce réglage n'a jamais servi : la cause du `403` était ailleurs, et
la correction retenue est `MCP_OAUTH_REQUIRED_SCOPES=-` côté serveur. Laissé
à « All », il accorde par défaut toutes les permissions présentes et futures de
l'API à toute application tierce du locataire — théorique tant que
l'enregistrement dynamique reste maîtrisé, réel dès qu'il ne l'est plus.

**Faire**

1. Auth0 → *Applications → APIs → Droit français MCP → Settings*.
2. Section *Access Settings* (ou *Default Permissions for third-party
   applications* selon la version du tableau de bord) → **User-delegated
   Access** : repasser de « All » à **« Unauthorized »**. Enregistrer.
3. Dans ChatGPT, ouvrir le connecteur *Droit français* et rafraîchir la
   découverte : les six outils doivent toujours apparaître, et un appel réel
   (« Recherche l'article L. 2212-2 du Code général des collectivités
   territoriales ») doit aboutir. L'accès ne dépend plus de la portée.

**Consigner** — fermer l'issue #27 avec la date ; cocher la ligne « DCR » de
[`auth0-security-checklist.md`](auth0-security-checklist.md).

## 3. Compte de démonstration sans MFA

**Pourquoi** — le serveur est en OAuth : le relecteur OpenAI doit pouvoir se
connecter. Les identifiants doivent fonctionner **sans MFA, ni SMS, ni
confirmation par courriel** — un relecteur ne peut pas recevoir votre second
facteur.

**Faire**

1. Auth0 → *User Management → Users → Create User*. Connexion
   `Username-Password-Authentication`, adresse dédiée (par exemple une adresse
   de test sur un domaine que vous contrôlez), mot de passe long et unique
   généré par un gestionnaire de mots de passe.
2. Auth0 → *Security → Multi-factor Auth* : vérifier la politique *Require
   Multi-factor Auth*. Si elle vaut « Always », le compte de démonstration ne
   pourra pas passer : soit la mettre à « Never » (le service n'impose pas de
   MFA aux utilisateurs — seuls les administrateurs Auth0 en ont besoin,
   ligne « Admins » de la check-list), soit ajouter une *Action* post-login
   qui exempte ce seul utilisateur.
3. Vérifier qu'aucune *Action* ni règle n'exige `email_verified` à la
   connexion. Auth0 n'en fait pas une condition par défaut.
4. **Tester en navigation privée** : créer ou reconnecter le connecteur dans
   ChatGPT, s'authentifier avec ce compte, lancer un appel réel. Le parcours
   doit aboutir sans aucune étape de vérification supplémentaire.
5. Reporter courriel et mot de passe **uniquement** dans le champ
   « identifiants de démonstration » du formulaire OpenAI Platform. Jamais
   dans le dépôt, une issue, un document ou une conversation.

**Consigner** — la date de création et le fait que le test en navigation
privée a abouti ; jamais les identifiants.

## 4. Sonde des six outils avec jeton (issue #34)

**Pourquoi** — la PR #24 a fait passer l'image de `python:3.12-slim` (glibc) à
Alpine (musl), dont le résolveur DNS diffère. La CI construit l'image mais ne
fait aucun appel sortant depuis le conteneur ; or le métier du service est
l'appel HTTPS sortant. La ligne E4 du registre d'audit a été établie sur
l'image Debian et ne couvre plus l'image déployée.

**Déjà rejoué le 1er septembre 2026, sans jeton** : métadonnées OAuth
conformes sur les deux routes, refus anonyme `401` correct, `/health` à
0,415 s à chaud puis 0,09–0,15 s sur trois appels successifs. Aucun signe de
résolution dégradée sur les routes publiques.

**Reste à faire, avec jeton** — les six outils, dont un appel Légifrance et un
appel Judilibre réels depuis le conteneur Alpine :

1. Obtenir un jeton par le flux *client credentials* de l'application
   machine-à-machine Auth0 — procédure dans
   [`validation-chatgpt.md`](validation-chatgpt.md), section « Raccourci ».
   Le jeton va dans `MCP_ACCESS_TOKEN`, jamais en argument ni dans un fichier.
2. Lancer :

   ```bash
   python tests/check_live_tools.py
   ```

3. Relever la latence du premier appel Légifrance et du premier appel
   Judilibre : une résolution DNS dégradée se verrait d'abord là.

**Consigner** — la date, la version annoncée par `/health`, et les cinq ✅ de
la sonde dans la ligne E4 de [`audit-securite.md`](audit-securite.md) ; fermer
l'issue #34.

## 5. Essai avec un second compte

**Pourquoi** — un compte unique ne peut pas prouver l'isolation du quota par
sujet ni l'absence de fuite d'état entre utilisateurs. Le harnais automatisé
le vérifie en processus, mais sur un émetteur factice.

**Faire** — avec le compte de démonstration (pièce 3) comme second sujet :

1. Depuis le compte habituel, enchaîner plus de `MCP_USER_CALLS_PER_MINUTE`
   appels en une minute (20 par défaut) jusqu'au message de quota individuel.
2. Sans attendre, depuis le second compte, lancer un appel : il doit aboutir.
3. Dans les journaux Render, vérifier deux valeurs distinctes de `principal=`
   sur les lignes `tool_call` — deux empreintes, aucun identifiant brut.
4. Attendre une minute : le premier compte redevient servi.

**Consigner** — la date et le résultat dans le tableau des conditions de
publication de [`exploitation.md`](exploitation.md).

## 6. Exercice du retrait d'urgence Judilibre (E10)

**Pourquoi** — la mesure conservatoire J4 n'a jamais été jouée sur l'instance
déployée. Depuis la PR #46, une entrée malformée refuse le démarrage et le
nombre d'identifiants chargés est journalisé : l'exercice vérifie que ces
garde-fous se voient bien depuis Render.

**Faire** — chronométrer du début à la fin :

1. Choisir une décision réelle quelconque (par exemple un identifiant renvoyé
   par `search_case_law`). Poser `MCP_JUDILIBRE_SUPPRESSED_IDS=<identifiant>`
   dans les variables du service Render, laisser redémarrer.
2. Journal de démarrage : `judilibre_suppression_list count=1`.
3. Depuis ChatGPT : une recherche qui renvoyait cette décision ne la renvoie
   plus ; sa lecture directe répond « temporairement indisponible ».
4. Contre-épreuve : poser une valeur malformée (`abc`) → le service **refuse
   de démarrer** et le journal nomme la position fautive. Remettre la valeur
   correcte.
5. Retirer la variable, redémarrer, vérifier que la décision est de nouveau
   servie.

**Consigner** — durée totale et date dans la ligne E10 de
[`audit-securite.md`](audit-securite.md), statut `PROUVÉ` ; fermer l'issue #33
si elle est encore ouverte.

## 7. Enregistrement vidéo

**Pourquoi** — le formulaire de soumission demande un enregistrement montrant
les principaux cas d'usage et outils.

**Faire** — capture d'écran de `chatgpt.com`, 2 à 4 minutes, sans commentaire
audio nécessaire, en navigation privée avec le compte de démonstration
(aucune donnée personnelle à l'écran ; masquer l'adresse si elle apparaît).
Reprendre les cas de test du dossier, dans cet ordre :

| Séquence | Prompt | Ce qui doit se voir |
|---|---|---|
| 0 | — | Page du connecteur : six outils, tous en lecture seule |
| 1 | « Recherche l'article L. 2212-2 du Code général des collectivités territoriales » | `search_articles` puis `get_article` ; identifiant `LEGIARTI…`, statut, date de version, lien Légifrance |
| 2 | « Trouve une décision Judilibre récente sur la responsabilité du fait des choses, puis lis-la » | `search_case_law` puis `get_decision` ; juridiction, date, numéro, lien courdecassation.fr |
| 3 | « Que dit l'article L. 9999-1 du Code général des collectivités territoriales ? » | Refus explicite : article introuvable, rien d'inventé |

Exporter en MP4 1080p. Le fichier ne va pas dans le dépôt.

## 8. Vérification de domaine

Procédure complète dans [`chatgpt-submission.md`](chatgpt-submission.md),
section « Vérification du domaine ». En résumé : le portail fournit un jeton
temporaire → variable Render `OPENAI_APPS_CHALLENGE` → redéploiement →
vérification depuis le portail → **retrait immédiat** de la variable. La route
`/.well-known/openai-apps-challenge` existe déjà et rend le jeton seul.

## 9. Captures Auth0 de la check-list

[`auth0-security-checklist.md`](auth0-security-checklist.md) porte, depuis le
1er septembre 2026, ce qui est prouvé depuis le code et le document de
découverte public. Les lignes restantes exigent le tableau de bord du
locataire : durée du jeton, MFA et comptes des administrateurs, protections
contre la force brute, journaux, rotation JWKS, révocation. Captures expurgées
(aucun secret), datées, à conserver dans un dossier privé ; la check-list
reçoit la date, le locataire, l'administrateur et le commit testé.

## 10. Version et tag de soumission

Le dossier de soumission fige le code par un tag `plugin-v*`, et les notes de
version le citent. Les correctifs fusionnés depuis le tag courant (retrait
d'urgence, cache de jetons, transport, instructions MCP) changent le serveur :
avant d'envoyer le dossier, incrémenter `SERVER_VERSION`, les deux manifestes
(`.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`), les notes de
version du fichier de soumission et le `CHANGELOG`, puis poser le tag sur le
commit fusionné. `python tests/check_plugin.py` et
`python tests/check_affirmations.py` refusent toute incohérence entre ces
sources. Convention des tags : [`architecture-plugin.md`](architecture-plugin.md).
