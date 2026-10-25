[🇫🇷 Français](README.md) | [🇬🇧 English](README.en.md)

<p align="center"><img src="assets/banner.svg" width="800" alt="Dessin au trait : un policier municipal, une avocate en robe autour de la tête de laquelle tournent six lucioles aux couleurs de Claude, ChatGPT, Gemini, Mistral, Grok et Perplexity, et un étudiant en droit qui révise, à côté d'un tribunal pavoisé. Six lucioles, une seule source : Légifrance."></p>

# Droit français — recherche juridique vérifiée

**Vérifier chaque référence de droit français sur Légifrance et Judilibre avant de l'écrire.**

[![CI](https://github.com/brissonjo-sudo/droit-francais-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/brissonjo-sudo/droit-francais-skill/actions/workflows/ci.yml)
[![Skill](https://img.shields.io/github/v/tag/brissonjo-sudo/droit-francais-skill?filter=skill-v*&label=skill)](https://github.com/brissonjo-sudo/droit-francais-skill/releases)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/license-CC%20BY--SA%204.0-blue)](LICENSE)

Un assistant IA cite volontiers un article qui n'existe pas, un arrêt mal
numéroté ou une version abrogée. Ce skill impose à l'assistant (Claude,
ChatGPT, Codex, Gemini…) une méthode de recherche sur sources officielles :
chaque référence provient d'une consultation faite pendant la session, avec sa
date d'applicabilité, et ce qui n'a pas pu être vérifié est signalé comme tel.

> Outil d'aide à la recherche, pas un avis juridique. Seules les publications
> signées au Journal officiel font foi ; aucune absence d'erreur n'est garantie.

---

## Exemple

Question : *« Quels sont les pouvoirs de police générale du maire ? »*

Le skill ne cite l'article qu'après l'avoir récupéré. Résultat réel du
connecteur le 25/10/2026, mis en forme :

```text
Article L2212-2 — Code général des collectivités territoriales
Identifiant    : LEGIARTI000029946370
Statut         : en vigueur, version du 22/12/2014
Applicable au  : 25/10/2026 — oui
Source         : API Légifrance, consultée le 25/10/2026
Lien           : https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000029946370
```

Si aucune source ne confirme une référence, la réponse le dit au lieu de la
compléter de mémoire :

> ⚠️ *Je ne produis pas ces numéros de pourvoi sans les avoir vérifiés en
> source primaire (Judilibre / Légifrance) — je ne les invente pas.*

---

## Pourquoi

Le danger n'est pas la référence absurde, que tout modèle récent rejette. C'est
la **référence plausible** : parfaitement formatée, mais fausse. Lors d'un essai
isolé du 5 juillet 2026, Gemini 3.5 extended a répondu ainsi à une demande de
trois arrêts de la Cour de cassation :

| Réponse de l'IA | Réalité (Légifrance) | Verdict |
|---|---|---|
| Gabillet — Civ. 2e, 19 févr. 1992, n° 90-19.493 | Ass. plén., 9 mai 1984, n° 80-14.994 | ❌ Chambre, date **et** n° faux |
| Anxiété — Soc., 11 mai 2010, n° 09-42.241 | Soc., 11 mai 2010, n° 09-42.241 | ✅ Exact |
| Rupture brutale — Com., 20 mars 2012, n° 11-13.245 | Aucun arrêt à ce n° | ⚠️ Introuvable |

Le **TA d'Orléans**, dans son
[jugement du 29/12/2025, n° 2506461](https://opendata.justice-administrative.fr/recherche/shareFile/TA45/DTA_2506461_20251229),
relève des décisions citées inexistantes et invite le conseil à vérifier ses
références. Ni l'un ni l'autre ne mesure l'effet de ce skill : voir
[Mesure de la qualité](#mesure-de-la-qualité).

---

## Démarrage rapide

### Dans claude.ai ou l'application Claude — outils inclus

1. Ajouter un connecteur personnalisé à l'adresse
   `https://droit-francais-skill.onrender.com/mcp`.
2. Dans ses *Advanced settings*, saisir `UydR0hHVgqArHoQpoonkYUN1vSLfaptD`
   comme « OAuth Client ID » et laisser le secret vide.
3. Se connecter, puis poser une question juridique.

Rien à installer : le service porte ses propres clés officielles, avec un quota
par utilisateur. Détails et dépannage : [guide OAuth](docs/oauth.md).

### Dans Claude Code — la méthode

```bash
npx skills add https://github.com/brissonjo-sudo/droit-francais-skill/tree/main/skill --skill recherche-juridique
```

Aucune clé n'est obligatoire : sans API, la recherche passe par les sites
officiels (Légifrance, Cour de cassation, Conseil d'État…). Une **clé PISTE
gratuite** rend la récupération déterministe — voir
[la configuration PISTE](skill/scripts/README.md).

### Autres installations

Plugin Claude Code ou Codex, serveur MCP local, copie manuelle, mises à jour
automatiques : voir le [guide d'installation](docs/installation.md).

Déclinaisons pour d'autres assistants, chacune documentée dans son dossier :

| Assistant | Dossier |
|---|---|
| Gemini (Google) | [`gemini_skill/`](gemini_skill) et [`gemini_agent/`](gemini_agent) |
| Grok (xAI) | [`grok_skill/`](grok_skill) |
| Vibe (Mistral) | [`vibe_skill/`](vibe_skill) |
| Manus | [`manus_skill/`](manus_skill) |

`skill/` reste la seule source de vérité : les déclinaisons ne s'y
synchronisent pas d'elles-mêmes.

---

## Ce que vous obtenez

- **Des références vérifiées** : tout identifiant officiel (article, NOR,
  n° de pourvoi…) vient d'une consultation de la session, jamais de la
  mémoire ; sinon il est marqué « non vérifié ».
- **La bonne version à la bonne date** : vigueur, historique de l'article et
  applicabilité à la date des faits.
- **La jurisprudence utile** : Cour de cassation et juridictions judiciaires
  (Judilibre), Conseil d'État et cours administratives d'appel, Conseil
  constitutionnel, juridictions financières.
- **Un raisonnement contrôlé** : qualification, articulation des normes, puis
  auto-critique adversariale avant de rendre la réponse.
- **L'audit de documents** : relecture juridique d'un acte ou d'un ensemble
  d'actes (références périmées, incohérences).
- **Des sorties adaptées** : réponse express, note de fond, citation pour un
  acte, note de concours.

---

## Choisir son profil

Le skill s'adapte à votre métier via un fichier `profil.md`. Chaque profil
ajoute un regard critique propre au métier :

| Profil | Pour qui | Regard critique ajouté |
|--------|----------|------------------------|
| `collectivites` | DGS, secrétaire de mairie, juriste territorial | Le contrôle de légalité préfectoral |
| `avocat` | Avocat (conseil, contentieux) | Le confrère adverse |
| `juriste-entreprise` | Direction juridique, conformité | Le régulateur ou l'auditeur |
| `police-gendarmerie` | Police nationale, gendarmerie, police municipale | L'avocat de la défense (nullités de procédure) |
| `etudiant-concours` | Étudiant, candidat aux concours | Le jury ou le correcteur |

Activation, après installation :

```bash
cd ~/.claude/skills/recherche-juridique
cp profils/avocat.md profil.md      # remplacer par votre profil
# puis compléter les champs [à compléter] du profil.md
```

Sans `profil.md`, le skill ne présume aucun contexte et pose la question quand
elle compte.

---

## Utilisation

Le skill s'active tout seul quand vous citez ou demandez un texte, une
qualification, une jurisprudence, la vigueur d'un texte, la rédaction d'un acte
ou la relecture juridique d'un document. Des balises ajustent la réponse :

| Balise | Effet |
|---|---|
| `[lookup]` | Référence ponctuelle, réponse minimale |
| `[express]` | Réponse allégée |
| `[complet]` | Analyse exhaustive |
| `[syllogisme]` | Majeure, mineure, conclusion (concours) |
| `[opérationnel]` | Conséquences pratiques détaillées |

---

## Questions fréquentes

**Est-ce gratuit ?** Le skill est libre (CC BY-SA 4.0) et la clé PISTE est
gratuite. Le service hébergé est ouvert après connexion, avec un quota par
utilisateur.

**Faut-il une clé API ?** Non. La clé PISTE est facultative ; sans elle, la
recherche passe par les sites officiels.

**Où vont mes questions ?** Voir la [politique de confidentialité](docs/privacy-policy.md).

**Qui répond d'une erreur ?** L'utilisateur reste responsable de ce qu'il
écrit. Les données officielles ne sont pas opposables ; seules les
publications signées au Journal officiel font foi. Voir les
[conditions d'utilisation](docs/terms-of-use.md).

---

## État du projet

| Composant | État au 25 octobre 2026 | Détail |
|---|---|---|
| Skill | 3.5.1, publié (étiquette `skill-v3.5.1`) | Méthode stable, installable seule |
| Service hébergé | Douze outils exposés au connecteur Claude | Connexion OAuth vérifiée dans claude.ai |
| Plugins Claude Code et Codex | Candidat 0.9.0, non publié | OAuth Claude Code et ChatGPT en cours ([#88](https://github.com/brissonjo-sudo/droit-francais-skill/issues/88), [#89](https://github.com/brissonjo-sudo/droit-francais-skill/issues/89)) |

---

## Mesure de la qualité

La [campagne des 18 modes d'erreur](docs/campagne-18-modes.md) compare trois
situations : le modèle seul, la méthode seule, la méthode avec les outils. Elle
vérifie que chaque identifiant cité provient bien d'un appel d'outil. Aucun
résultat chiffré n'est encore publié. Le protocole est décrit dans
[`tests/README.md`](tests/README.md).

---

## Pour aller plus loin

- [Arborescence et maintenance du dépôt](docs/arborescence.md)
- [Architecture skill, bibliothèque et plugin](docs/architecture-plugin.md)
- [Outils MCP et leur contrat](docs/mcp-app.md)
- [Déploiement du service](docs/deployment.md)
- [Obligations des CGU Légifrance et Judilibre](docs/obligations-cgu.md)
- [Historique des versions](skill/CHANGELOG.md)

---

## Licence et contribution

[Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](LICENSE)
— © 2026 @brissonjo-sudo.

Questions, erreurs, propositions : ouvrir une
[issue](https://github.com/brissonjo-sudo/droit-francais-skill/issues).
