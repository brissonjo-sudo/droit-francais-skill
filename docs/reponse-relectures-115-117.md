# Suivi des revues 115, 116 et 117 — 10/10/2026

La PR 115 est fusionnée par squash (`a71d3d5`). Ses remarques restent traitées
dans la [PR corrective 118](https://github.com/brissonjo-sudo/droit-francais-skill/pull/118).
La [PR 116](https://github.com/brissonjo-sudo/droit-francais-skill/pull/116)
est réalignée sur main ; la [PR 117](https://github.com/brissonjo-sudo/droit-francais-skill/pull/117)
reste basée sur la campagne. Aucun force-push, merge de PR ou déploiement
automatique n'est prévu pour ces correctifs.

## Distribution

Le README français et sa traduction complète anglaise proposent les deux
langues dès la première ligne. Le parcours Claude Code affiche son blocage
OAuth avant l'installation. Le catalogue Codex conserve le schéma officiel ;
la version et la description appartiennent au manifeste du plugin.

La description GitHub a été relue après alignement sur 18 modes ; les topics
n'ont pas été changés. Les contrôles d'aide et de documentation sont distincts
des recettes d'installation et de l'accès OAuth réel. Le suivi volontaire à
J+7/J+30 n'ajoute aucune télémétrie ni automatisation de messages.

## Contrats d'étude

Le schéma v2 distingue réservations, résultats, clôtures, déclarations humaines
de données manquantes et invalidations de série. Les anciennes preuves sont
conservées : aucune migration implicite n'est une autorisation de collecte.
La réservation durable fait autorité pour les 100 tentatives par jour UTC et
les deux tentatives par identité ; un résultat déjà acquis ne doit pas être
rejoué après interruption. Le même contrôle d'admissibilité couvre collecte,
jugement et ablation.

Une panne transitoire arrête la commande. Après deux pannes, une déclaration
humaine motivée permet de poursuivre les autres unités avec une donnée
manquante. Une contamination, rupture d'isolation, changement de candidat,
de runtime ou substitution de modèle invalide définitivement la série.
Les avis humains restent séparés des jugements LLM et liés aux preuves relues.
Les paquets de jugement excluent les réponses en panne ; leur mapping reste
privé. L'aveuglement demeure partiel.

La qualification technique REST préalable ajoute quatre tentatives d'étude :
avec les six préflights, le pilote, la collecte principale et leurs jugements,
le calendrier minimal porte sur **1 930 tentatives**, soit au moins 20 journées
UTC avec le plafond global de 100. L'ablation et ses jugements portent ce total
à **2 074**, soit au moins 21 journées. Ce calcul ne comprend ni pannes, ni
reprises, ni limites propres aux fournisseurs. Pour Gemini seul, avant les
jugements, 358 réponses représentent au moins 716 requêtes HTTP de comptage et
génération ; les tours d'outils et les sondes augmentent ce nombre.

## Gemini

La tentative d'étude est réservée une seule fois par le lanceur. Les sondes,
comptages de jetons et générations ont des réservations HTTP distinctes,
dans l'état canonique commun à ce poste et aux worktrees. Le rattachement
au numéro de projet repose sur une preuve privée du titulaire : une empreinte
de clé contrôle les déclarations contradictoires, pas leur authenticité Google.

L'échéance du cas commence avant l'ouverture MCP. Le transport HTTP asynchrone
vise une durée totale de 120 secondes par requête au plus, limitée par les
300 secondes du cas. Annuler localement une requête ne garantit pas l'arrêt du
calcul accepté par Google ; sa réservation reste consommée. Le préflight réel
doit encore déterminer si ces plafonds conviennent au modèle choisi.

L'environnement MCP du harnais est filtré et le chargement automatique des
fichiers .env est désactivé pour ce parcours. L'arrêt après 429 et les verrous
abandonnés exigent examen explicite. Aucun fallback, retry ou changement
automatique de clé n'est une voie de reprise.

## Frontières conservées

- **0/36 corrigés validés humainement** ; vérification de sources par un agent
  et validation humaine sont distinctes.
- Aucun modèle précis, quota actif, accès juridique amont ou préflight réel
  n'est qualifié par les tests synthétiques.
- Le démarrage commun Claude/Codex/Gemini attend les trois qualifications,
  les corrigés humains, puis la revue du pilote.
- Le relevé historique de 31 558 jetons ne qualifie pas le corpus corrigé.
- Le secret de dépôt GEMINI_API_KEY reste à déplacer dans gemini-free et à
  retirer du dépôt ; l'annonce du transfert ne prouve pas sa réalisation.
- Le compteur local ne couvre pas les usages externes ni une seconde machine.
- Aucun score d'utilité, exemple README mesuré ou publication de version n'est
  déduit de cette livraison.

Les résultats de tests et les SHA effectivement contrôlés figurent dans les
descriptions des PR et leurs CI. Ce suivi ne transforme pas un test prévu ou
une qualification absente en preuve acquise.
