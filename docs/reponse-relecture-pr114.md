# Traitement de la revue de la PR 114 — 10/10/2026

Ce bilan décrit le candidat historique `c071041` du 10/10/2026. La PR 114
est fermée comme remplacée par les PR 115, 116 et 117 ; sa revue et sa branche
sont conservées. Les nouvelles revues ont révélé des limites supplémentaires,
notamment pour les reprises et les délais : les lignes ci-dessous ne valent
pas preuve des garanties du candidat actuel.

Le [suivi des trois revues](reponse-relectures-115-117.md) décrit les corrections
suivantes. Aucune correction technique ne valide les 36 corrigés ni Gemini
gratuit. Le noyau méthodologique et le déploiement ne sont pas modifiés.

| Constat | Traitement et preuve | Limite restante |
|---|---|---|
| 1. Reprise après panne | Une reprise explicite peut refaire une identité en erreur, au plus deux tentatives. Les essais restent dans le journal ; paquet et rapport retiennent le dernier. Tests de panne/reprise et de refus du troisième essai. | Aucune reprise interne ; données manquantes après deux pannes. |
| 2. Surveillance du gel | Fichiers et version CLI contrôlés avant et après chaque réponse, préflight, jugement et ablation. Tests de dérive avant et pendant l'exécution. | Le modèle effectif doit encore être attesté par chaque client. |
| 3. Secret GitHub | Environnement gemini-free créé, limité à main, avec revue humaine. Jobs Gemini réseau retirés ; job de préparation sans secret. | Déplacer la clé dans cet environnement et retirer le secret de dépôt ; métadonnées à contrôler après l'action du titulaire. |
| 4. Fable | Sous-chaîne fable refusée en minuscules, dans toutes les familles avant toute CLI. | Les autres modèles exacts restent à qualifier. |
| 5. Budget REST | Le prototype réserve une tentative de réponse dans le journal commun 100/jour UTC ; ses tours ne créent pas une nouvelle réponse. Test de refus avant HTTP au cent-unième cas. | Pas d'intégration implicite au collecteur : gel gratuit fermé. |
| 6. Sondes hors budget | Les sondes locales exigent profil et état persistant ; models.list et countTokens réservent leurs requêtes et arrêtent après 429. Sondes Actions réseau désactivées. | Quotas auxiliaires fournisseur et usages externes du projet non qualifiés. Anciennes sondes hors journal conservées comme mesures historiques. |
| 7. Délais REST/MCP | Délai du cas autour de l'ouverture MCP ; initialize/list_tools et call_tool bornés ; échéance transmise à HTTP et vérifiée avant envoi/lecture. | Un envoi déjà en vol termine sous son plafond de transport de 30 secondes ; aucune annulation distante supposée. |
| 8. Secrets | Une seule politique d'identifiants/secrets pour refus de transfert, journaux et flux natifs conservés. Test avec secret JSON imbriqué. | Toute publication de trace exige toujours une relecture. |
| 9. Code de sortie | Pannes de collecte, jugement et ablation lèvent un arrêt repris par le CLI avec code 2 ; préflight en panne retourne aussi 2. | Les preuves de tentative sont conservées. |
| 10. README | .mcp.json décrit la connexion distante ; service historique à six outils distingué du candidat local à huit. | Les issues OAuth 88 et 89 restent ouvertes. |
| 11. Moteurs | Claude/Codex natifs et Gemini REST explicitement distincts ; ancienne recette OAuth marquée historique. | Aucun classement inter-familles ; le moteur est un facteur de confusion. |
| 12. Calendrier | 1 926 tentatives avant ablation, au moins 20 journées UTC ; 2 070 avec ablation et ses jugements, au moins 21. Unité : tentative de réponse. | Hors pannes, revues et quotas fournisseurs. |
| 13. Mesure | Collecte entrelacée par blocs de quatre, historique des pannes et absences par strate, paires complètes uniquement ; anonymisation partielle explicitée. Répertoires de travail temporaires déjà présents, témoin des corrigés ajouté. Questions M05-a/M17-a/M18-a neutralisées. | L'absence de témoin ne prouve pas l'isolation ; préflight humain requis. |
| 14. Extraits | Tous les passages préparatoires typés résumé ou observation de pièce. Une citation exacte future exige un vérificateur identifié ; le juge ne compare pas une citation littérale à un résumé. | Fidélité juridique à valider sur le texte officiel. |
| 15. Corrigés | Référence latérale non sourcée supprimée de M10-a ; lacunes M17-a explicites, absence de lacune motivée ailleurs. M14-a accepte une réserve conditionnelle sur l'article 73, sans constater ses conditions ni autoriser une rétention. | Tous les corrigés restent brouillons. Article 73 consulté sur Légifrance dans la version affichée depuis le 02/06/2014 ; date du dossier à reconfirmer en revue humaine. |
| 16. Rédaction | Assistance Codex, famille OpenAI GPT-6, indiquée dans le corpus et le dossier ; identifiant exact non attesté. Affirmation « aucun résultat de modèle » limitée aux réponses de campagne non collectées. | Revue indépendante requise pour le biais possible de famille. |

Références : [protocole](campagne-18-modes.md),
[corrigés](corriges-campagne-18-modes.md),
[état Gemini](quotas-gemini-gratuit.md).
L'environnement est une protection GitHub ; ce fichier ne déclare aucune
réponse Gemini gratuite, preuve de quota ou validation humaine supplémentaire.
