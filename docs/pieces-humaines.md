# Pièces humaines avant soumission

Dernière mise à jour : 2 septembre 2026

Inventaire des pièces humaines, restantes ou achevées, que le dépôt **ne peut
pas porter** : comptes, captures, enregistrement, réglages de consoles. Chaque
pièce dit pourquoi elle est exigée, comment la produire, et où consigner le
résultat. Aucun secret ne doit atterrir ici ni dans une issue publique.

Les critères mesurables, contre-contrôles et états consolidés sont suivis dans
[`finalisation-checklist.md`](finalisation-checklist.md).

Ordre conseillé pour les pièces restantes : commencer par le ping externe
(§ 11), qui conditionne le départ de la période d'observation, et par
l'identité OpenAI (délai le plus long) ; puis le compte de démonstration Auth0,
les sondes et la vidéo. Le contrôle Auth0 #27 est terminé.

| # | Pièce | Bloque | Exige |
|---|---|---|---|
| 1 | [Identité vérifiée OpenAI Platform](#1-identité-vérifiée-openai-platform) | soumission | compte OpenAI, pièce d'identité |
| 2 | [Auth0 — borner les permissions tierces (#27)](#2-auth0--borner-les-permissions-tierces-issue-27) | publication | ✅ configuration et preuve privée terminées le 1/9/2026 |
| 3 | [Compte de démonstration sans MFA](#3-compte-de-démonstration-sans-mfa) | soumission | admin Auth0 |
| 4 | [Sonde des six outils avec jeton (#34)](#4-sonde-des-six-outils-avec-jeton-issue-34) | registre E4 | application M2M Auth0 |
| 5 | [Essai avec un second compte](#5-essai-avec-un-second-compte) | publication | deux comptes |
| 6 | [Exercice du retrait d'urgence (E10)](#6-exercice-du-retrait-durgence-judilibre-e10) | audit | accès Render |
| 7 | [Enregistrement vidéo](#7-enregistrement-vidéo) | soumission | écran, 5 minutes |
| 8 | [Vérification de domaine](#8-vérification-de-domaine) | soumission | jeton du portail, accès Render |
| 9 | [Captures Auth0 de la check-list](#9-captures-auth0-de-la-check-list) | audit | admin Auth0 |
| 10 | [Version et tag de soumission](#10-version-et-tag-de-soumission) | soumission | une PR |
| 11 | [Ping externe de maintien hors veille](#11-ping-externe-de-maintien-hors-veille) | observation | compte sur un service de ping |

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

## 2. Auth0 — borner les permissions tierces (issue #27)

**Pourquoi** — pendant le diagnostic des 30–31 août, *Default Permissions for
third-party applications → User-delegated Access* a été passé à « All ». Ce
réglage accorde toutes les permissions présentes et futures de l'API à toute
application tierce du locataire. Il est trop large. Le remplacer par
« Unauthorized » est toutefois incorrect : un client tiers créé par DCR exige
un *client grant* explicite pour obtenir un jeton destiné à l'API, même lorsque
le serveur accepte un jeton sans portée particulière. Le réglage minimal est
donc « Authorized » avec une liste de permissions vide ; il autorise l'audience
sans accorder `legal:read` ni une permission future.

**Faire**

1. Auth0 → *Applications → APIs → Droit français MCP → Settings*.
2. Section *Access Settings* (ou *Default Permissions for third-party
   applications* selon la version du tableau de bord) :
   * **User-delegated Access : `Authorized`** ;
   * cliquer **None** pour ne sélectionner aucune permission ;
   * **Client Access : `Unauthorized`** ;
   * enregistrer.
3. Vérifier le grant par l'une de ces deux voies :
   * **tableau de bord** : *Monitoring → Logs*, événement **Create client
     grant** ou **Update client grant**, puis **Raw Data** ;
   * **Management API** : avec un jeton limité à la lecture des client grants,
     appeler `GET /api/v2/client-grants` en filtrant `audience` sur l'URL MCP,
     `subject_type=user` et `default_for=third_party_clients`.
   Dans les deux cas, le résultat doit porter l'audience MCP exacte,
   `scope: []`, `allow_all_scopes: false`, `subject_type: user` et
   `default_for: third_party_clients`. Un grant par défaut n'a pas de
   `client_id` : les deux champs sont mutuellement exclusifs.
4. Vérifier séparément **Client Access** dans *Applications → APIs → Droit
   français MCP → Settings → Application Access Policy → Default Permissions
   for third-party applications*. La valeur doit être **Unauthorized — No
   permissions allowed**. Archiver une capture limitée à cette section : le
   grant utilisateur de l'étape 3 ne prouve pas ce réglage distinct.
5. Dans ChatGPT → Paramètres → Plugins → *Droit français*, cliquer
   **Actualiser**. Les six outils doivent apparaître.
6. Tester en mode **Chat** — le mode Work n'expose pas ce plugin — avec
   « Recherche l'article L. 2212-2 du Code général des collectivités
   territoriales ». L'appel doit rendre `LEGIARTI000029946370`, statut
   `VIGUEUR`, version du 22 décembre 2014 et le lien Légifrance.

**Exécuté le 1er septembre 2026** — configuration minimale enregistrée ; grant
vérifié dans le journal Auth0 à `21:13:00Z` ; six outils actualisés ; appel réel
réussi dans ChatGPT avec `search_articles` puis lecture de la source officielle.
Le passage intermédiaire à « Unauthorized » a supprimé le grant et rendu le
plugin inaccessible, ce qui confirme le rôle indispensable de « Authorized ».

**Preuve durable archivée le 1er septembre 2026** — deux pièces sont
conservées hors dépôt dans le dossier privé : le grant expurgé
`Auth0/auth0-dcr-client-grant-2026-09-01.redacted.json` et la capture limitée
aux réglages `Auth0/auth0-third-party-defaults-2026-09-01.png`. La première
porte la date, le locataire, l'audience et les quatre champs attendus du grant ;
la seconde montre séparément `Client Access: Unauthorized`. Jeton, adresse IP,
identité de l'administrateur, identifiants client et de corrélation en sont
exclus. Ces artefacts ne doivent jamais être versés au dépôt.

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

**Rejoué le 2 septembre 2026, sans jeton** : métadonnées OAuth conformes sur
les deux routes, refus anonyme `401` correct, `/health` conforme en 1,399 s,
version `0.7.0`. Après durcissement de la sonde authentifiée, la suite locale
complète compte 171 tests verts. Aucun signe
de résolution dégradée sur les routes publiques.

**Rejoué le 2 septembre 2026, avec jeton M2M éphémère** :

1. le JWT était signé en `RS256`, destiné à l'audience exacte du MCP et émis
   par le tenant attendu ; il a transité par mémoire et variable
   d'environnement uniquement, puis a été effacé ;
2. les six outils ont été découverts, annotés en lecture seule et **chacun
   réellement appelé** : `search`, `fetch`, `search_articles`, `get_article`,
   `search_case_law`, `get_decision` ;
3. le premier appel Légifrance a répondu en **1,000 s** avec
   `LEGIARTI000029946370`, statut `VIGUEUR` et datation explicite au 02/09/2026 ;
4. le premier appel Judilibre a répondu en **0,461 s** ; la lecture de la
   décision portait texte non vide, identifiant exact, date et URL officielle ;
5. le parcours standard `search → fetch` a abouti et l'article inexistant
   `L9999-1` n'a produit aucune référence inventée ; durée totale : **8,72 s**.

Commande reproductible :

```bash
python tests/check_live_tools.py
```

La comparaison directe avec les valeurs des clés fournisseur n'était pas
possible, celles-ci n'étant volontairement pas présentes sur le poste. La
sonde l'a signalé au lieu de produire un faux vert ; le masquage par valeur
reste couvert par les tests serveur et OAuth de bout en bout. Version annoncée
par `/health` : `0.7.0`. La ligne E4 du registre est désormais `PROUVÉ`.

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

## 11. Ping externe de maintien hors veille

**Pourquoi** — l'instance Render gratuite s'endort après quinze minutes sans
trafic, et son réveil coûte 32,4 à 32,7 s sur les cinq mesures relevées les
1er et 2 septembre 2026. Le maintien hors veille par le planificateur GitHub a
été essayé et **réfuté par la mesure** : quatre exécutions pour environ
soixante-dix-huit attendues en treize heures avec `*/10`, une seule après le
resserrement à `3/5`. GitHub n'exécute les workflows planifiés qu'en « meilleur
effort ». Un service de ping est fait pour cela, lui.

Sans ce ping, la période d'observation ne peut pas être propre : le critère
« aucun réveil au-delà de 30 s » est violé à chaque exécution planifiée.

**Faire**

1. Créer un compte sur un service de ping. Deux conviennent, tous deux
   gratuits :
   * **UptimeRobot** — moniteur HTTP(s) toutes les 5 minutes, avec en prime une
     alerte par courriel quand le service ne répond plus. C'est le choix le
     plus utile : il rend aussi le service de surveillance externe ;
   * **cron-job.org** — plus léger, cadence configurable jusqu'à la minute,
     avec un historique d'exécutions consultable.
2. Créer un moniteur sur **`https://droit-francais-skill.onrender.com/health`**,
   en `GET`, toutes les **5 minutes**. Aucune authentification : la route est
   publique et ne rend que `status`, `version` et le mode d'authentification —
   ni secret, ni donnée personnelle. Le tiers n'apprend donc qu'une URL déjà
   publique et des temps de réponse.
3. Attendre **24 heures**, puis croiser deux preuves :

   * l'historique du service de ping ne montre **aucun échec ni trou supérieur
     à 10 minutes** sur les 24 heures ; exporter cet historique ou en faire une
     capture sans donnée de compte ;
   * le journal GitHub ne montre aucun réveil :

   ```bash
   git fetch origin surveillance
   git show origin/surveillance:surveillance.jsonl | python tests/summarize_surveillance.py - --jours 1
   ```

   Attendu : historique externe continu, « Réveils d'instance : aucun » et une
   latence à chaud du même ordre que la référence (0,15 à 0,60 s). Tant qu'un
   trou ou un réveil subsiste, resserrer la cadence à 3 minutes avant de
   conclure.
4. **Vérifier le quota d'heures d'instance** sur le tableau de bord Render.
   Une instance éveillée en permanence consomme des heures en continu, là où
   une instance endormie les économise. Le plan gratuit borne ce total par
   mois, et le quota est partagé si d'autres services gratuits vivent sur le
   même compte : une suspension en fin de mois serait un défaut bien plus
   visible qu'un réveil. Si la marge est trop mince, la seule issue propre est
   une instance sans mise en veille.

**Consigner** — le service retenu, la cadence, la date de mise en service et la
preuve d'historique continu sur 24 h dans le tableau des conditions de publication de
[`exploitation.md`](exploitation.md) ; le résultat de la vérification à 24 h
dans [`finalisation-checklist.md`](finalisation-checklist.md). Ni identifiants,
ni clé d'API du service de ping dans le dépôt.
