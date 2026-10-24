# Recherche juridique — Grok

Version **3.6.0-grok**, base méthodologique **3.6.0**.

Le noyau court reprend les sept principes, neuf étapes (0, 0 bis, 1 à 7),
dix-huit modes d'erreur, six modules et quatre techniques du noyau.
Les onze références juridiques sont reprises mot pour mot, hors renvois
d'en-tête de DOC-AUDIT et des modules. Les profils sont également repris.
La règle de citation interne utilise le nom du skill et la section, sans
lien ni chemin ; seuls les liens de chargement restent relatifs.

## Installation et lecture des références

Charger le dossier complet dans Grok en conservant l'arborescence.
Le noyau route chaque lecture requise vers ses références locales.
La lecture de ces références doit être possible ; sinon suspendre le point
dépendant. Aucun fichier voisin du dépôt n'est nécessaire à l'analyse.

## Capacités et écarts volontaires

Voie native : `web_search`, puis `open_page` ou `open_page_with_find` ; `browser_tab` si nécessaire.
Les noms génériques des références sont traduits vers ces outils exposés.
Pas de MCP, de PISTE ni d'historique d'article natif supposé : utiliser la
lecture officielle et le repli historique décrit dans les références.
`scripts/legifrance.py` est une copie documentaire du noyau pour garder les
liens des références intacts ; ne pas l'exécuter dans cette déclinaison.

La maintenance du CLI skills (3.4.x) est sans objet ici : aucune copie de
sa référence maintenance.md, aucun updater annoncé ou livré. Utiliser le
mécanisme de la plateforme ou une copie manuelle autorisée du paquet complet.
Les développements juridiques 3.4.x, DOC-AUDIT 3.5.0, fraîcheur 3.5.1,
routage court 3.6.0 et citations par nom et section sont conservés.
Les dates embarquées restent celles du noyau ; aucune nouvelle vérification
juridique ni recette réelle Grok n'a été effectuée (pas de clés).

## Fichiers

- `SKILL.md` : noyau court et adaptations de capacité.
- `references/` : onze références chargées selon leurs déclencheurs.
- `profils/` : profils métier optionnels ; copier le profil choisi en profil.md.
- `scripts/legifrance.py` : source documentaire du noyau.
- `CHANGELOG.md` : historique de cette déclinaison.

Licence : [CC-BY-SA-4.0](../LICENSE). [Noyau source](../skill/SKILL.md).
