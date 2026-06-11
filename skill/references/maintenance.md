# Maintenance du skill `recherche-juridique`

Procédure de revue annuelle obligatoire à exécuter **chaque 1er septembre**
(rentrée juridique), priorisée par fréquence de contentieux dans la
pratique du praticien (police municipale, administration locale,
préparation aux concours de catégorie A de la sécurité intérieure le
cas échéant).

---

## 0. Préparation

1. Ouvrir le SKILL.md courant et vérifier l'en-tête YAML : `version`,
   `date_derniere_revue_methodologique`, `date_derniere_verification_sources`.
2. Archiver la version précédente dans `archive/`
   sous la forme `SKILL-vX.Y.Z-AAAA-MM-JJ.md` avant toute modification
   structurante.
3. Préparer un brouillon d'entrée CHANGELOG datée du jour.

---

## 1. Veille législative et réglementaire (priorité haute)

### 1.1 CGCT, partie police municipale
- Vérifier les modifications du livre II, titre Ier, chapitre II
  (art. **L. 2212-1 à L. 2212-5** et suivants).
- Vérifier les polices spéciales (art. **L. 2213-1 à L. 2213-32**).
- Source : fiche Légifrance du CGCT, onglet « Historique des versions »
  filtré sur l'année écoulée.

### 1.2 Code de procédure pénale, cadres d'enquête
- Cadres d'enquête (préliminaire, flagrance, instruction), pouvoirs
  d'OPJ / APJ / APJA, compétence territoriale, garde à vue, mesures
  alternatives aux poursuites.
- Source : fiche Légifrance du CPP, onglet historique.

### 1.3 Code de la route, compétence police municipale
- Articles d'incrimination contraventionnelle relevant de la compétence
  PM (L. 130-4 et suivants, R. 130-x, R. 411-x, R. 412-x, R. 417-x).
- Évolutions des forfaits, des classes contraventionnelles, des
  pouvoirs de constatation.

### 1.4 CSI (Code de la sécurité intérieure) — priorité moyenne
- Livre V (police municipale), livre VI (activités privées de
  sécurité), livre VII (gardes champêtres et agents).
- Évolutions des compétences, des armements (notamment décret 2016-1616
  modifié), de la vidéoprotection (art. L. 251-1 et suivants).

### 1.5 Loi de programmation Intérieur / Justice (priorité variable)
- Identifier toute LOPSI / LOPJ / loi d'orientation publiée dans
  l'année et inventorier ses dispositions impactant la PM ou les
  cadres procéduraux.

---

## 2. Veille jurisprudentielle (priorité haute)

### 2.1 Cour de cassation, chambre criminelle
- Recenser les arrêts de l'année publiés au **Bulletin** portant sur :
  qualifications pénales d'usage courant en PM, procédure pénale
  (cadres d'enquête, preuve), responsabilité pénale des décideurs
  publics, nullités.
- Source : courdecassation.fr (filtre Bulletin + chambre criminelle +
  période 12 mois).

### 2.2 Conseil d'État
- Recenser les arrêts publiés au **Lebon** ou mentionnés aux **Tables**
  portant sur : pouvoirs de police du maire, proportionnalité des
  mesures de police, motivation des actes, responsabilité administrative
  des communes, contentieux fonctionnaires territoriaux.
- Source : conseil-etat.fr (filtre formation + période).

### 2.3 Conseil constitutionnel
- Recenser les **QPC** abrogatives ou réservatives intervenues dans
  l'année sur les codes suivis (CGCT, CP, CPP, CSI, CdR).
- Source : conseil-constitutionnel.fr (rubrique QPC + période).

### 2.4 CJUE et CEDH (si pertinent)
- Arrêts impactant le droit français en matière de libertés publiques,
  contrôle d'identité, données personnelles, vidéoprotection.

---

## 3. Mise à jour des annexes du skill

- `gabarits-requetes.md` : vérifier que les identifiants `LEGITEXT`
  des codes suivis n'ont pas changé.
- `checklist-vigueur.md` : aligner si des points de vigilance nouveaux
  ont émergé (ex. nouvelle disposition transitoire récurrente, nouveau
  type de renvoi normatif).
- `references/sources-autorisees.md` : ajouter toute source institutionnelle
  nouvelle (ex. autorité de régulation créée dans l'année).
- `references/format-citation.md` : ajouter tout format de citation nouveau
  si nécessaire (ex. nouvelle juridiction spécialisée).

---

## 4. Contrôle de cohérence interne du SKILL.md

- [ ] Numérotation continue des 14 modes d'erreur.
- [ ] Numérotation continue des 7 principes (P1 à P7).
- [ ] Numérotation continue des 7 étapes (0 à 7).
- [ ] Numérotation continue des 4 techniques (T1 à T4).
- [ ] Les 5 modules ont chacun leurs déclencheurs et leur contenu.
- [ ] Chaque étape a un critère de sortie explicite.
- [ ] Chaque étape référence le ou les modes d'erreur qu'elle bloque.
- [ ] Les balises `[complet]`, `[express]`, `[syllogisme]`,
      `[opérationnel]` sont mentionnées de manière cohérente partout.
- [ ] La règle de triangulation pénale unifiée apparaît **au seul
      endroit prévu** (étape 4) et est référencée depuis le module
      PÉNAL.
- [ ] Les gabarits A, B, C et le sous-gabarit syllogisme intègrent
      tous l'en-tête standardisé et l'encart final récapitulatif.
- [ ] Les 9 déclencheurs d'abstention sont listés et un format de
      réponse en cas d'abstention est fourni.

---

## 5. Mise à jour des métadonnées

- Mettre à jour `version` selon le caractère des changements :
  - **MAJEUR** : refonte structurelle (ex. v1 → v2.0.0).
  - **MINEUR** : ajout d'un module, d'une technique, d'un déclencheur,
    sans remise en cause de l'architecture.
  - **PATCH** : correction de coquille, ajustement de référence,
    clarification rédactionnelle.
- Mettre à jour `date_derniere_revue_methodologique` à la date du jour
  (1er septembre AAAA).
- Mettre à jour `date_derniere_verification_sources` à la date du jour.

---

## 6. Entrée CHANGELOG

Format Keep a Changelog 1.1.0. Sections : *Ajouté*, *Modifié*,
*Déprécié*, *Retiré*, *Corrigé*, *Sécurité*. Référencer le commit
si la revue donne lieu à un commit.

---

## 7. Test fonctionnel de fin de revue

Faire tourner le skill, après mise à jour, sur **trois requêtes témoins**
représentatives :

1. **Mode A standard, aucun module** — requête simple de référence
   d'article (ex. « quel article du CGCT définit les pouvoirs généraux
   du maire ? »). Vérifier l'en-tête standardisé, l'absence de
   modules activés dans l'encart final.

2. **Mode A + PÉNAL + ACTE-ADMIN** — requête de qualification + acte
   (ex. « qualification de dépôt sauvage et possibilité d'arrêté de
   mise en demeure »). Vérifier la décomposition élémentaire de
   l'infraction, le contrôle de proportionnalité Benjamin, la
   triangulation appliquée à juste mesure.

3. **Mode B `[complet]`** — requête institutionnelle exigeante
   (ex. « `[complet]` note sur l'articulation police générale du maire
   et police spéciale environnementale »). Vérifier que tous les
   modules sont activés, certains marqués « sans objet à cette
   espèce » avec justification.

Si l'un des tests révèle un défaut de cohérence ou d'application →
correction immédiate avant clôture de la revue.

---

## 8. Clôture

- Commit avec message format : `chore(skill): revue annuelle AAAA-MM-JJ`.
- Mettre à jour les métadonnées de suivi dans votre projet (version et date).
