# Campagne d'utilité des 18 modes — protocole v2

Préparation du 10/10/2026 : **36 cas, zéro réponse juridique collectée et 0/36
corrigés humains validés**. Les tests du harnais n'établissent aucune utilité
juridique. Le noyau du skill reste inchangé.

## Comparaisons et conditions de départ

| Bras | Méthode | Outils juridiques |
|---|---|---|
| A | Prompt neutre | Aucun |
| B | Noyau et références Markdown canoniques | Aucun |
| C | Même méthode que B | MCP local du candidat |
| D | Prompt neutre | Même MCP que C |

Les comparaisons B/A et C/D portent sur le même cas, la même répétition, la
même famille et le même moteur. Aucun classement inter-familles n'est calculé.
Claude et Codex utilisent leur CLI native avec abonnement ; Gemini utilise
exclusivement le moteur REST v2 avec clé gratuite et quotas confirmés. Aucun
repli vers OAuth, un autre modèle, une autre clé ou un moteur payant n'est prévu.

La campagne pilote et principale attend les **trois familles qualifiées
ensemble**. Le gel refuse une qualification Gemini absente, périmée ou non
relue humainement. Le lot [Gemini et quotas](quotas-gemini-gratuit.md) fournit
cette recette séparée. Un catalogue de huit outils ne prouve pas un accès aux
sources ni une lecture juridique réussie.

36 cas × 4 bras × 2 répétitions × 3 familles = 864 réponses principales.
Le pilote, séparé, porte sur les modes 1, 3, 5 et 18 : 192 réponses. Deux cas
et deux répétitions par mode produisent des observations descriptives ; ils
ne permettent pas de conclure à une significativité ni à une utilité générale.

## Corrigés et preuves officielles

Lire le [dossier des corrigés](corriges-campagne-18-modes.md), puis corriger
[cases.json](../tests/campaign/cases.json). Les faits déterminants absents
et leurs limites sont propres à chaque cas ; aucune hypothèse n'est ajoutée
pour rendre le résultat complet. Les questions M04-a, M05-a, M10-a et M18-a
ne prescrivent plus l'analyse attendue.

Le [registre préparatoire des sources](../tests/campaign/preuves-sources-20261010.json)
distingue textes/versions récupérés dans cette session, pièces synthétiques
lues et références historiques non vérifiées dans cette session. Six pages
officielles prioritaires ont été relues : article 1242, articles 78-6, 78-3,
21, 73 du CPP et décision Benjamin. Les fragments sauvegardés sont partiels ;
ils ne suffisent pas à vérifier toute citation possible d'une réponse.
L'article 21 est lu sur une page au 12/10/2023 dont l'intervalle de version
couvre le 16/05/2026 ; la page datée du 16/05/2026 n'a pas été récupérée.
La décision Benjamin n'est vérifiée que pour l'identification historique.

Les résumés restent des résumés. Un fragment officiel, son empreinte et les
bornes de version ne transforment pas une paraphrase en citation. L'axe
fidelite_sources reste indetermine si le passage officiel requis n'est pas
présent. Les pièces synthétiques ne constituent jamais du droit positif.
Le contrôle humain doit confirmer sources et versions à la date utile, puis
renseigner verification_humaine de chaque source et la validation du gold.
Une date future, un nom seul ou une ancienne consultation embarquée ne suffisent
pas. Tous ces champs humains restent vides après la préparation par agent.

Les dates affichées en français sont européennes ; **les dates JSON restent
ISO AAAA-MM-JJ**. La provenance déclare l'assistance Codex et un modèle exact
non attesté, sans déduire une version de LLM depuis l'interface.

~~~powershell
python tests/run_campaign.py verifier
python tests/run_campaign.py corriges --sortie docs/corriges-campagne-18-modes.md
~~~

## Gel, état commun et qualification

Copier [config.example.json](../tests/campaign/config.example.json), puis
renseigner les modèles exacts et réglages. Les paramètres inconnus et les alias
évolutifs, quelle que soit leur casse, sont refusés. Les champs moteur,
ordre_collecte, max_tentatives_par_identite, timeout_s et ablation sont
appliqués ou refusés explicitement. Le profil Gemini et son registre sont
privés ; leur qualification REST est nécessaire avant le gel.

Le schéma v2 est une rupture : **aucune migration implicite des anciens gels
ou journaux**. Conserver les preuves anciennes dans leur dossier d'origine.
L'état est commun aux worktrees et lié au compte OS : LocalAppData obtenu par
l'[API Windows officielle](https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/nf-shlobj_core-shgetknownfolderpath),
ou dossier personnel obtenu par `pwd.getpwuid` sous Linux, puis
`droit-francais/bench-v2`. HOME, XDG_STATE_HOME et LOCALAPPDATA ne peuvent
changer ses compteurs. `etat` affiche le chemin sans créer de fichier.
L'ancre est vérifiée aux réservations ; un état ancien non vide sans ancre
nécessite un rattachement humain audité. Aucun déplacement ou reset implicite.
Une ancre différente bloque l'opération ; aucune option CLI d'état alternatif.
Les injections d'état des fonctions Python servent aux tests internes.

~~~powershell
$etat = python tests/run_campaign.py etat
python tests/run_campaign.py figer --config config-privee.json --sortie "$etat/gel.json"
python tests/run_campaign.py preflight --gel "$etat/gel.json" --famille claude
python tests/run_campaign.py preflight --gel "$etat/gel.json" --famille codex
python tests/run_campaign.py preflight --gel "$etat/gel.json" --famille gemini
~~~

Le gel conserve commit, hashes du candidat/corpus/harnais, catalogue MCP avec
schémas, configuration, ordre matérialisé, exécutables CLI résolus et versions,
versions/hash des Python du harnais et du serveur, ainsi que toutes les versions
des distributions installées, dont MCP et PyJWT. Préparer un environnement
isolé conservé pendant l'étude et empêcher ses mises à jour automatiques par
les mécanismes documentés des clients ; une modification détectée exige une
nouvelle série. Les contrôles sont faits avant et après chaque réponse.

Chaque reçu de préflight contient deux runs techniques A et C. Préparer
l'instantané, renseigner nom, justification, preuve_isolation, auth_confirmee
et autorise_collecte après contrôle réel, puis l'approuver. L'outil calcule
les hashes et conserve l'historique chaîné et daté. Modifier seulement les
cases du reçu ne vaut pas approbation. Le modèle demandé n'est jamais substitué
à un modèle effectif absent. Un reçu ne remplace pas la validation des corrigés.

~~~powershell
python tests/run_campaign.py preparer-approbation --gel "$etat/gel.json" --type preflight --famille claude --sortie "$etat/avis-preflight-claude.json"
# Relire les preuves puis renseigner explicitement les champs humains de cet avis.
python tests/run_campaign.py approuver-recu --gel "$etat/gel.json" --avis "$etat/avis-preflight-claude.json"
~~~

Répéter pour les trois familles. Après pilote, préparer un avis de type `pilote`
par famille et l'approuver. Son instantané contient uniquement les résultats
et manquants de son pilote ; les manquants principaux ou annexes ne le périment
pas. Une nouvelle approbation conserve la précédente dans l'historique.

## Ordre, réservations et interruptions

~~~powershell
python tests/run_campaign.py collecter-entrelace --gel "$etat/gel.json" --phase pilote
python tests/run_campaign.py collecter-entrelace --gel "$etat/gel.json" --phase principale
~~~

Le plan matérialisé conserve proches les deux répétitions de chaque cas, en
alternant leur ordre selon l'index du cas. Les quatre bras tournent et les
familles alternent par blocs de quatre ; la première famille tourne également.
Une collecte individuelle exige la famille du prochain bloc du plan et
se limite à quatre tentatives. Une autre famille est refusée ; elle ne permet
pas de terminer toutes les répétitions d'une famille avant les autres.
La collecte principale exige une revue humaine de chaque pilote, liée par SHA
aux résultats et déclarations de manquants effectivement examinés, avec auteur
et justification. Aucun score du pilote n'est recyclé dans la principale.

Le verrou couvre lecture autoritaire, réservation, appel, résultat et clôture.
Une réservation durable unique précède toute initialisation MCP et tout appel
modèle ; elle possède attempt_id, identité, numéro et horodatage. L'échéance
globale couvre aussi les vérifications préalables et borne le timeout natif.
Les quotas HTTP Gemini ont leurs propres réservations liées à cette tentative ;
ils ne créent pas une deuxième réservation d'étude.

Maximum 100 **tentatives de réponse par jour UTC**, toutes familles et phases
confondues, et deux tentatives réservées par identité. Une interruption ou une
panne consomme ces deux limites. Aucun remboursement, attente ou retry caché.
Une réponse acquise n'est jamais rejouée. Toute commande en panne sort avec 2.
Une interruption entre réservation et résultat bloque la reprise jusqu'à
clôture explicite, après contrôle du processus. Si un résultat complet avait
été engagé par hash durable puis écrit avant le crash, la récupération vérifie
cet engagement et conserve ce succès au lieu de le
transformer en interruption et de permettre un second tirage.

~~~powershell
python tests/run_campaign.py recuperer-verrou --auteur-humain "NOM" --motif "Processus terminé et contrôlé"
python tests/run_campaign.py clore-interruption --attempt-id ATTEMPT_ID --auteur-humain "NOM" --motif "Contrôle de la tentative interrompue"
python tests/run_campaign.py declarer-manquant --gel "$etat/gel.json" --identite IDENTITE --auteur-humain "NOM" --motif "Deux pannes clôturées, données manquantes acceptées"
~~~

Le retrait vérifie hôte, PID et empreinte de création OS sans terminer de
processus. Un PID réutilisé est distingué de l'ancien propriétaire ; une
identité incertaine bloque l'opération. Les journaux sont créés avec mode 0600
sur POSIX ; les ACL Windows restent celles du profil utilisateur.
Après deux pannes récupérables, seule une déclaration humaine motivée autorise
la poursuite sur les autres unités. Les paires incomplètes sont exclues, sans
imputation d'une panne en réponse correcte ou fausse ; leurs taux sont publiés.
**Après exposition au moteur, contamination, isolation rompue, substitution
de modèle et changement confirmé de gel/runtime invalident définitivement la
phase concernée.** Aucun second tirage dans cette phase. Une contamination
principale invalide toujours la principale ; jugement et ablation ne détruisent
pas ses réponses acquises. Avant appel, une dérive refuse sans invalider.
Une sonde CLI/runtime indisponible est une panne passagère, pas une dérive.
Manquants et invalidations sont filtrés par phase et restent auditables.

Un journal tronqué reste un blocage conservateur. `quarantainer-journal`
archive tous ses octets, leur empreinte et la décision humaine, sans modifier
l'original ni rembourser. **Cette commande ne permet pas de reprendre** : le
nombre de tentatives éventuellement tronquées reste inconnu, même au lendemain.
Examen/restauration externe audités nécessaires ; aucune réparation automatique.

~~~powershell
python tests/run_campaign.py quarantainer-journal --journal "$etat/budget.jsonl" --auteur-humain "NOM" --motif "Append interrompu, compteurs incertains"
python tests/run_campaign.py rattacher-etat --auteur-humain "NOM" --motif "État historique lisible rattaché sans reset"
~~~

## Jugements et arbitrage humain

~~~powershell
python tests/run_campaign.py paquet-revue --resultats "$etat/SERIE/principale-claude.jsonl" --sortie "$etat/SERIE/paquet.json"
python tests/run_campaign.py juger --gel "$etat/gel.json" --paquet "$etat/SERIE/paquet.json" --famille codex --sortie "$etat/SERIE/juges.jsonl"
~~~

Le paquet LLM contient uniquement les réponses techniquement admissibles.
Les pannes avec texte partiel sont conservées dans un paquet privé pour revue
humaine d'incidents ; aucune dépense de jugement automatique ne leur est imputée.
Résultats, jugements et reçus de préflight sont rapprochés des réservations,
clôtures et empreintes exactes avant utilisation. Un succès écrit juste avant
un crash reste inutilisable tant que sa récupération explicite n'est pas faite.
Les tokens HMAC utilisent un sel aléatoire privé. Mapping et sel restent dans
$etat/prive et ne sont pas transmis au juge. Le texte peut révéler la méthode :
anonymisation partielle, pas double aveugle garanti.

Un juge indépendant est attribué par rotation fixe : Claude → Codex,
Codex → Gemini, Gemini → Claude. Les autres commandes de jugement ignorent
les réponses qui ne leur sont pas attribuées ; aucun choix du meilleur juge.
Les axes et la justification LLM sont enregistrés sans aucune signature humaine.

Les avis humains utilisent un **JSONL distinct**. Préparer un fichier d'avis
avec schema=2, identite, revision, precedent_sha256 (vide pour révision 1),
resultat_sha256, jugement_sha256, relecteur_humain, justification_humaine,
date_validation ISO, validation_humaine=true, avis_final=true,
arbitrage=confirmer_juge ou corriger_juge, et axes définitifs. Une révision
suivante référence le SHA de l'avis précédent. Le harnais ne complète aucun
champ humain. Champs inconnus, avis liés à un juge infra rejouable, doublons,
avis orphelins/périmés, dates futures et chaînes
rompues sont refusés. **L'arbitrage humain validé prime sur le jugement LLM**,
qui demeure conservé dans son propre journal.

~~~powershell
python tests/run_campaign.py ajouter-revue-humaine --avis avis-humain.json --resultats "$etat/SERIE/principale-claude.jsonl" --revues "$etat/SERIE/juges.jsonl" --sortie "$etat/SERIE/humains.jsonl"
python tests/run_campaign.py rapport --gel "$etat/gel.json" --resultats "$etat/SERIE/principale-claude.jsonl" "$etat/SERIE/principale-codex.jsonl" "$etat/SERIE/principale-gemini.jsonl" --revues "$etat/SERIE/juges.jsonl" --revues-humaines "$etat/SERIE/humains.jsonl" --sortie "$etat/SERIE/rapport.json"
~~~

Revue humaine de tous les désaccords, réponses fausses et cas critiques, plus
au moins 10 % par famille/bras. Les dénominateurs viennent du gel et de la
phase. Le rapport distingue résultats admissibles, réservations, interruptions,
pannes historiques et manquants par strate, ainsi que gains/pertes sur paires
complètes. Un rapport partiel ne produit aucun exemple README complet.

## Ablation, exemples et calendrier

Au plus six modes, après rapport principal complet et recette relue humainement.
Le rapport conserve ses chemins et empreintes dans l'état privé ; il est
recalculé depuis les traces acquises avant préparation et avant chaque collecte
d'ablation. Modifier son statut à la main ne permet pas d'ouvrir ce passage.
Un seul plan d'ablation est enregistré par série : un nouveau dossier n'ouvre
pas une nouvelle enveloppe. Chaque variante est liée par hash au C principal
du même cas, famille et répétition avant de réserver son appel.
Chaque recette indique passages_exacts, raison, regles_partagees et valide_par ;
un passage absent ou présent plusieurs fois est refusé. Les variantes sont
hashées et restent dans l'état privé, sans modifier le skill canonique. La
collecte d'ablation reprend le plan et les mêmes garanties de réservation,
isolation, contamination et gel. Elle reste limitée à quatre tentatives par
commande individuelle et se compare au C principal du même cas/répétition.

~~~powershell
python tests/run_campaign.py preparer-ablation --gel "$etat/gel.json" --recettes recettes-ablation.json --rapport "$etat/SERIE/rapport.json" --dossier "$etat/SERIE/experiences"
python tests/run_campaign.py ablation --gel "$etat/gel.json" --plan "$etat/SERIE/experiences/plan.json" --famille claude
python tests/run_campaign.py comparer-ablation --gel "$etat/gel.json" --plan "$etat/SERIE/experiences/plan.json" --revues "$etat/SERIE/juges.jsonl" --revues-humaines "$etat/SERIE/humains.jsonl" --sortie "$etat/SERIE/comparaison-ablation.json"
~~~

La comparaison énumère les paires C/variante et fournit leur delta descriptif
uniquement après acquisition des deux jugements et arbitrages humains finaux.
Une ablation invalidée ne produit aucun score. Les ajouts annexes au journal
de jugements n'altèrent pas les empreintes filtrées du rapport principal.

La décision de simplifier une règle reste humaine. Les exemples README
exigent un cas complet, toutes ses répétitions, les sources et un arbitrage
humain de toutes ses réponses ; conserver également les limites et échecs.
Aucun choix de la seule meilleure sortie, aucune affirmation que les 18 modes
sont utiles avant mesure.
Le rapport propose le premier identifiant lexical éligible par catégorie
gain, abstention et limite, et conserve la liste complète des éligibles. Un
cas doit réunir toutes les familles, bras et répétitions, leurs arbitrages
humains et un accord `candidat_readme` explicite. Si une catégorie manque,
aucun exemple n'est inventé. La publication reste une décision humaine.

Minimum sans panne : 4 réponses de qualification Gemini REST + 6 préflights +
192 pilote + 864 principale + 864 jugements = **1 930 tentatives**, au moins
20 journées UTC à 100/jour. L'ablation maximale ajoute 72 réponses et 72
jugements : **2 074**, au moins 21 journées. Ces valeurs excluent les autres
recettes réelles, reprises, sondes et délais humains. Chaque réponse REST peut
consommer plusieurs HTTP ; la limite d'étude ne remplace pas RPM/TPM/RPD.
La réinitialisation fournisseur en heure du Pacifique est distincte du budget
UTC d'étude. Ces minimums ne constituent pas une date de livraison.
