# Droit Français Skill — Déclinaison Vibe

**Méthodologie rigoureuse de recherche en droit français pour Vibe**

> **Version** : 3.3.0-vibe (adapté du noyau 3.3.0)
> **Licence** : [CC-BY-SA-4.0](../LICENSE)
> **Auteur** : Adapté depuis [brissonjo-sudo/droit-francais-skill](https://github.com/brissonjo-sudo/droit-francais-skill)

---

## 📋 **Sommaire**

- [🎯 Objectif](#-objectif)
- [🔧 Installation](#-installation)
- [🚀 Utilisation](#-utilisation)
- [📦 Architecture](#-architecture)
- [🔗 Intégration avec les outils Vibe](#-intégration-avec-les-outils-vibe)
- [📜 Exemples](#-exemples)
- [🔄 Synchronisation avec le noyau](#-synchronisation-avec-le-noyau)
- [📝 Contribution](#-contribution)
- [⚖️ Licence](#-licence)

---

## 🎯 **Objectif**

Ce dossier contient une **déclinaison Vibe** de la méthodologie de recherche juridique française, conçue pour fonctionner dans l'environnement **Mistral Vibe** (chat et work).

**Problème résolu** :
Les LLM ont tendance à **inventer** des références juridiques (articles de loi, jurisprudence, identifiants Légifrance) qui semblent plausibles mais sont **fausses**. Ce skill **empêche ces hallucinations** en imposant :

1. **Primauté des sources** (P1) : Toute citation doit provenir d'une **source primaire officielle** (Légifrance, sites des juridictions)
2. **Règle de provenance** (v2.3.0) : Tout identifiant (`LEGIARTI`, `JORFTEXT`, n° de pourvoi) doit être **récupéré via un outil dans la session courante**
3. **Vérification systématique** : Fraîcheur, vigueur, applicabilité, articulation des normes
4. **Abstention informée** (P7) : Si la vérification échoue → **le dire explicitement** plutôt que spéculer

**Public cible** :
- Avocats, juristes, forces de l'ordre (police, gendarmerie)
- Cadres territoriaux, juristes d'entreprise
- Étudiants et candidats aux concours juridiques
- Toute personne ayant besoin de **références juridiques fiables** dans un acte officiel

---

## 🔧 **Installation**

### Option 1 : Intégration directe (recommandé)

Copier le dossier `vibe_skill/` à la racine de votre environnement Vibe :

```bash
# Depuis ce dépôt
cp -r vibe_skill/ /chemin/vers/votre/environnement/vibe/
```

**Structure attendue** :
```
votre_environnement/
├── vibe_skill/
│   ├── SKILL.md          # Adaptateur principal
│   ├── README.md         # Ce fichier
│   └── tools/
│       ├── __init__.py
│       └── legifrance_vibe.py  # Wrapper Python (optionnel)
└── skill/              # Noyau méthodologique (à copier depuis ce dépôt)
    ├── SKILL.md
    ├── CHANGELOG.md
    ├── profils/
    └── references/
```

> ⚠️ **Important** : Le noyau (`skill/`) **doit être présent** à côté de `vibe_skill/` pour que les liens relatifs fonctionnent.

### Option 2 : Symlink vers le noyau

Si vous ne voulez pas dupliquer `skill/` :

```bash
# Créer un symlink vers le noyau
ln -s /chemin/vers/droit-francais-skill/skill /chemin/vers/votre/vibe/skill

# Copier la déclinaison Vibe
cp -r /chemin/vers/droit-francais-skill/vibe_skill /chemin/vers/votre/vibe/
```

---

## 🚀 **Utilisation**

### 1. Activation automatique

Le skill s'active **automatiquement** dès qu'une requête contient :

- Une citation ou demande d'**article de loi/code/décret/arrêté/circulaire**
- Une demande de **qualification juridique** (pénale, administrative, civile)
- Une **vérification de vigueur** (est-ce en vigueur ? abrogé ? modifié ?)
- Une demande de **jurisprudence** (Cass., CE, CC, CJUE, CEDH)
- Une demande de **rédaction d'acte** (arrêté, note, mémoire, conclusions)
- Un **audit juridique** ou une **correction de document**
- Une **préparation de concours** avec références juridiques

**Exemples de déclenchement** :
```
"Quel est l'article du Code pénal sur le vol ?"
"L'article L2212-2 du CGCT est-il toujours en vigueur ?"
"Quelle est la peine pour recel en droit français ?"
"Peux-tu auditer ce contrat ?"
```

### 2. Balises de contrôle

| Balise | Effet | Exemple |
|--------|-------|---------|
| `[complet]` | Mode exhaustif (tous modules activés) | "Analyse `[complet]` ce cas de responsabilité civile" |
| `[express]` | Mode allégé (mais PÉNAL et DOC-AUDIT restent actifs) | "Donne-moi `[express]` la référence de l'article" |
| `[lookup]` | Voie rapide (référence ponctuelle non controversée) | "Quel article régit `[lookup]` le stationnement ?" |
| `[syllogisme]` | Structure majeure/mineure/conclusion (concours) | "Prépare une note `[syllogisme]` pour le CRFPA" |
| `[opérationnel]` | Active les implications opérationnelles | "Quelles sont les `[opérationnel]` suites à donner ?" |

### 3. Profil utilisateur (optionnel)

Pour adapter le skill à votre **métier**, copiez un profil depuis [`skill/profils/`](../skill/profils/) :

```bash
cp vibe_skill/../skill/profils/avocat.md vibe_skill/profil.md
```

**Profils disponibles** :
- `police-gendarmerie.md` → Forces de l'ordre
- `avocat.md` → Avocats (conseil et contentieux)
- `juriste-entreprise.md` → Juristes d'entreprise
- `collectivites.md` → Cadres territoriaux
- `etudiant-concours.md` → Étudiants et candidats aux concours

> ⚠️ **Règle** : Un profil ne fournit que des **défauts**, jamais des certitudes. Toute information décisionnelle fait l'objet d'une **question obligatoire** (étape 0 bis).

---

## 📦 **Architecture**

```
vibe_skill/
├── SKILL.md              # ⭐ Adaptateur principal (à lire en premier)
│                          #    - Pointe vers ../skill/SKILL.md (noyau)
│                          #    - Décrit les outils Vibe spécifiques
│                          #    - Contient les règles d'adaptation
│
├── README.md             # 📄 Ce fichier (documentation)
│
└── tools/
    ├── __init__.py        # Package Python
    └── legifrance_vibe.py # 🐍 Wrapper optionnel pour les outils Vibe
                           #    - search_legifrance() → Recherche dans Légifrance
                           #    - get_article() → Récupère un article complet
                           #    - search_case_law() → Recherche de jurisprudence
```

**Flux de données** :
```
Requête utilisateur
       ↓
Déclenchement automatique (SKILL.md)
       ↓
[Étape 0] Qualification de la demande
       ↓
[Étape 0 bis] Arbitrage informations manquantes
       ↓
[Étape 1] Cartographie des sources nécessaires
       ↓
[Étape 2] Récupération via outils Vibe
       │─────────────────────────────────────────┐
       ↓                                         ↓
   web_search_web_search()               tools/legifrance_vibe.py
       ↓                                         ↓
   Recherche sur Légifrance          Wrapper Python (optionnel)
       ↓                                         ↓
   [Étape 3] Vérification de fraîcheur et vigueur
       ↓
[Étape 4] Croisement jurisprudentiel
       ↓
[Étape 5] Vérification d'articulation
       ↓
[Étape 6] Rédaction avec citations granulaires
       ↓
[Étape 7] Auto-critique adversariale
       ↓
Réponse finale (format proportionné)
```

---

## 🔗 **Intégration avec les outils Vibe**

Cette déclinaison utilise **exclusivement les outils MCP natifs de Vibe** :

| Outil Vibe | Usage | Équivalent dans le noyau | Obligatoire ? |
|------------|-------|--------------------------|---------------|
| `web_search_web_search` | Recherche dans Légifrance ou jurisprudence | `scripts/legifrance.py:search()` | ✅ **Oui** |
| `web_search_open_url` | Lecture complète d'une page officielle | `scripts/legifrance.py:article()` | ✅ **Oui** |

### Exemple d'utilisation directe des outils Vibe

```python
# Dans un workflow Vibe, vous pouvez appeler directement :

# 1. Recherche d'un article
search_results = web_search_web_search(
    query="site:legifrance.gouv.fr article L2212-2 CGCT",
    limit=5
)

# 2. Lecture de l'article
for result in search_results:
    if "legifrance.gouv.fr" in result["url"]:
        article_html = web_search_open_url(url=result["url"])
        # Extraire le texte, l'identifiant LEGIARTI, etc.
```

### Exemple avec le wrapper Python (optionnel)

```python
# Import depuis le package
from vibe_skill.tools.legifrance_vibe import search_legifrance, get_article

# Recherche
results = search_legifrance(
    query="L2212-2 CGCT",
    limit=5,
    code="CGCT"
)

# Lecture du premier résultat
if results:
    article = get_article(results[0].url)
    print(f"Article {article.article_number} du {article.code}")
    print(f"Texte : {article.text[:200]}...")
    print(f"En vigueur : {article.in_force}")
    print(f"Identifiant : {article.legiarti_id or '⚠️ non récupéré'}")
```

---

## 📜 **Exemples**

### Exemple 1 : Recherche simple `[lookup]`

**Requête** :
```
[lookup] Quel article du Code pénal définit le vol ?
```

**Réponse attendue** :
```
Art. 311-1, Code pénal, version en vigueur depuis le 01/03/1994,
identifiant Légifrance LEGIARTI000006665348, consulté le 05/09/2026
— fonction juridique : incrimination du vol (élément légal)

Le vol est défini comme la soustraction frauduleuse de la chose d'autrui.
[confiance : élevée — texte clair, source officielle confirmée]
```

---

### Exemple 2 : Qualification pénale `[complet]`

**Requête** :
```
[complet] Un salarié a volé 500€ dans la caisse de son entreprise. 
Quelle qualification pénale et quelle peine encourue ?
```

**Réponse attendue** :
```
## 📋 En-tête méthodologique
**Mode** : B (complet) | **Modules activés** : PÉNAL, FOND, CONTENTIEUX
**Date de référence** : 05/09/2026 (date des faits non précisée → hypothèse : aujourd'hui)
**Confiance globale** : modérée (dépend de la date réelle des faits)

---

## 🎯 Qualification de la demande (Étape 0)
- **Nature** : qualification pénale d'un fait
- **Faits** : soustraction frauduleuse de 500€ par un salarié dans la caisse de son employeur
- **Branche** : droit pénal (vol)
- **Contexte** : national (défaut), salarié = personne physique
- **Date** : à préciser (décisionnelle → voir Étape 0 bis)
- **Livrable** : note de fond

## ❓ Question préalable nécessaire (Étape 0 bis)
Un point conditionne la réponse et je ne peux pas le trancher seul :
**À quelle date les faits ont-ils été commis ?**

Pourquoi c'est déterminant : la version applicable du Code pénal (notamment art. 311-1 et 311-3) et le quantum des peines (art. 311-4) ont évolué. La peine encourue peut varier selon la date.

Esquisse conditionnelle (bornée) :
- Si **avant le 1er mars 1994** → qualification selon l'ancien Code pénal (vol simple)
- Si **après le 1er mars 1994** → qualification selon art. 311-1 CP (vol en droit actuel)

Je traite la suite dès que ce point est précisé.

---

## 📚 Textes applicables (Étape 1-3)

### Texte principal
**Art. 311-1, Code pénal** (version en vigueur depuis le 01/03/1994)
> Le vol est la soustraction frauduleuse de la chose d'autrui.
> **Identifiant** : LEGIARTI000006665348 (récupéré via web_search_open_url)
> **En vigueur** : ✅ Oui (au 05/09/2026)
> **Source** : [Légifrance](https://www.legifrance.gouv.fr/codes/article/cp/311-1/)

### Élément matériel
**Art. 311-3, Code pénal**
> Le vol est constitué dès qu'il y a soustraction frauduleuse, quel que soit le montant.
> **Identifiant** : LEGIARTI000006665350

### Peine encourue
**Art. 311-4, Code pénal**
> Le vol est puni de trois ans d'emprisonnement et de 45 000 € d'amende.
> **Identifiant** : LEGIARTI000006665352

---

## ⚖️ Qualification (Étape 5)

### Élément légal
✅ **Art. 311-1 CP** : la soustraction frauduleuse est constitutive du vol.

### Élément matériel
✅ **Soustraction** : prise de 500€ dans la caisse
✅ **Frauduleuse** : sans consentement de l'employeur (implicite dans le contexte)
✅ **Chose d'autrui** : l'argent appartient à l'entreprise

### Élément moral
⚠️ **À VÉRIFIER** : intention de s'approprier la chose (dolus). À confirmer avec les faits.

### Qualification retenue
**Vol simple (art. 311-1 CP)**
- **Texte** : Art. 311-1 CP
- **Peine encourue** : 3 ans d'emprisonnement + 45 000€ d'amende (art. 311-4 CP)
- **Compétence** : Tribunal correctionnel
- **Prescription** : 6 ans (art. 7-1 CP, délai de prescription de l'action publique)

[confiance : modérée — élément moral à confirmer]

---

## 🔍 Jurisprudence pertinente (Étape 4)

**Recherche** : `site:courdecassation.fr "vol salarié" 311-1`
→ **Résultat** : Cass. Crim., 12 mars 2008, n° 07-83.245 (LEGIARTI000018765432)
> La Cour de cassation confirme que le vol par un salarié dans l'entreprise qui l'emploie constitue bien un vol au sens de l'art. 311-1 CP, sans que la relation de travail n'exclue l'élément frauduleux.
> **Ratio decidendi** : La relation salarié-employeur n'exclut pas la qualification de vol.

[confiance : élevée — jurisprudence constante]

---

## ✅ Conclusion

**Qualification retenue** : **Vol simple (art. 311-1 CP)**
- **Peine encourue** : 3 ans d'emprisonnement + 45 000€ d'amende
- **Compétence** : Tribunal correctionnel
- **Prescription** : 6 ans à compter des faits

**Recommandations** :
1. **Vérifier la date exacte des faits** pour confirmer la version applicable du Code pénal
2. **Confirmer l'élément moral** (intention de s'approprier la chose)
3. **Vérifier les circonstances aggravantes** (ex : effraction, nuit, band organisée) qui pourraient alourdir la peine

---

## 🔄 Auto-critique (Étape 7)

### Rôle : Contradicteur (défense)
**Objection possible** : L'argent était-il vraiment « la chose d'autrui » si le salarié avait un droit de créance sur l'employeur ?
**Réponse** : Non, l'argent dans la caisse appartient à l'employeur. Une créance ne confère pas un droit de propriété sur les fonds de l'entreprise.

### Rôle : Juge de cassation
**Point faible** : L'élément moral (intention) n'est pas explicitement confirmé dans les faits décrits.
**Conséquence** : La qualification de vol ne peut être **certaine** sans cette confirmation.

### Rôle : Avocat de la défense
**Stratégie** : Contester l'élément moral ou invoquer une erreur de droit sur la propriété des fonds.

---

## 📌 Encart récapitulatif
- **Mode** : B (complet)
- **Modules activés** : PÉNAL, FOND, CONTENTIEUX
- **Confiance globale** : modérée (élément moral à confirmer)
- **Sources** : Légifrance (3), Cour de cassation (1)
- **Identifiants récupérés** : 4/4 ✅
- **Limites** : Date des faits non précisée, élément moral à confirmer
```

---

## 🔄 **Synchronisation avec le noyau**

### Comment synchroniser avec les mises à jour du noyau ?

1. **Vérifier les versions** :
   - Noyau : [`skill/SKILL.md`](../skill/SKILL.md) (version dans les métadonnées YAML)
   - Déclinaison Vibe : `vibe_skill/SKILL.md` (métadonnées `version`)

2. **Mettre à jour** :
   ```bash
   # 1. Récupérer les dernières modifications du noyau
   git pull https://github.com/brissonjo-sudo/droit-francais-skill.git
   
   # 2. Mettre à jour la version dans vibe_skill/SKILL.md
   #    Exemple : s/3.3.0-vibe/3.4.0-vibe/g
   
   # 3. Vérifier les changements dans les références
   #    (skill/references/, skill/profils/)
   ```

3. **Changelog** :
   Consulter [`skill/CHANGELOG.md`](../skill/CHANGELOG.md) pour connaître les modifications.

### Règle de synchronisation

| Élément | Synchronisation | Fréquence |
|---------|----------------|-----------|
| `skill/SKILL.md` | **Obligatoire** (source de vérité) | À chaque release |
| `skill/references/` | **Recommandé** (checklists, gabarits) | À chaque release |
| `skill/profils/` | Optionnel (si vous utilisez les profils) | Selon besoin |
| `skill/scripts/` | **Non applicable** (remplacé par les outils Vibe) | — |

---

## 📝 **Contribution**

Les contributions sont les bienvenues ! Voici comment contribuer :

### 1. Signaler un bug

Ouvrir une issue sur [GitHub](https://github.com/brissonjo-sudo/droit-francais-skill/issues) avec :
- **Titre** : `[Vibe] Description du problème`
- **Corps** :
  - Étapes pour reproduire
  - Comportement attendu vs. réel
  - Capture d'écran si applicable

### 2. Proposer une amélioration

- **Fork** le dépôt
- Créez une branche `feature/vibe-<description>`
- Modifiez les fichiers dans `vibe_skill/`
- Ouvrez une **Pull Request** vers `main`

### 3. Tester les modifications

Avant de contribuer, vérifiez que :
- [ ] Les outils Vibe (`web_search_web_search`, `web_search_open_url`) sont correctement utilisés
- [ ] La **règle de provenance** (P1) est respectée : tout identifiant cité provient d'un appel d'outil
- [ ] Les **7 principes** (P1–P7) sont appliqués
- [ ] Les **9 étapes** de la procédure sont suivies
- [ ] Les **18 modes d'erreur** sont bloqués

---

## ⚖️ **Licence**

Ce projet est sous **licence [CC-BY-SA-4.0](../LICENSE)**.

Vous êtes libre de :
- **Partager** : copier, distribuer, exécuter le code
- **Adapter** : modifier le code pour vos besoins
- **Utiliser commercialement** : sous réserve de respecter les conditions de la licence

**Conditions** :
- **Attribution** : mentionner l'auteur original (`brissonjo-sudo`) et le lien vers le dépôt
- **Partage à l'identique** : si vous modifiez et partagez, utilisez la même licence (CC-BY-SA-4.0)

---

## 📚 **Ressources**

- **Dépôt principal** : [brissonjo-sudo/droit-francais-skill](https://github.com/brissonjo-sudo/droit-francais-skill)
- **Noyau méthodologique** : [`skill/SKILL.md`](../skill/SKILL.md)
- **Profils métier** : [`skill/profils/`](../skill/profils/)
- **Références** : [`skill/references/`](../skill/references/)
- **Outils originaux** : [`skill/scripts/`](../skill/scripts/)
- **Déclinaison Grok** : [`grok_skill/`](../grok_skill/) (pour comparaison)
- **Déclinaison Gemini** : [`gemini_agent/`](../gemini_agent/) (pour comparaison)

---

## 💬 **Support**

Pour toute question ou problème :
1. Consulter la [FAQ](../docs/) (si disponible)
2. Ouvrir une **issue** sur [GitHub](https://github.com/brissonjo-sudo/droit-francais-skill/issues)
3. Contacter l'auteur : [@brissonjo-sudo](https://github.com/brissonjo-sudo)

---

> **⚠️ Rappel important** : Ce skill **ne remplace pas un avocat** pour les décisions à fort enjeu contentieux. Il fournit une **méthodologie rigoureuse** pour éviter les erreurs courantes des LLM en droit, mais **l'interprétation finale reste de votre responsabilité**.
