# Maintenance du skill `recherche-juridique`

Procédure de revue annuelle obligatoire à exécuter **chaque 1er septembre**
(rentrée juridique), priorisée par fréquence d'usage et de contentieux
dans la pratique du praticien. À adapter aux codes et matières
effectivement suivis.

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

### 1.1 Codes suivis dans votre domaine
- Vérifier les modifications de l'année sur les codes effectivement
  mobilisés dans votre pratique (par exemple Code pénal, CPP, et tout
  code spécialisé pertinent).
- Source : fiche Légifrance du code, onglet « Historique des versions »
  filtré sur l'année écoulée.

### 1.2 Code de procédure pénale
- Évolutions des cadres d'enquête, de la preuve, des garanties
  procédurales et des mesures alternatives aux poursuites.
- Source : fiche Légifrance du CPP, onglet historique.

### 1.3 Réglementation d'application
- Décrets et arrêtés d'application parus dans l'année pour les
  dispositions législatives suivies (test du décret d'application,
  mode 9).

### 1.4 Lois de programmation ou d'orientation (priorité variable)
- Identifier toute loi de programmation ou d'orientation publiée dans
  l'année et inventorier ses dispositions impactant les matières
  suivies ou les cadres procéduraux.

---

## 2. Veille jurisprudentielle (priorité haute)

### 2.1 Cour de cassation
- Recenser les arrêts de l'année publiés au **Bulletin** portant sur
  les matières suivies (qualifications pénales d'usage courant,
  procédure, preuve, nullités, responsabilité).
- Source : courdecassation.fr (filtre Bulletin + chambre concernée +
  période 12 mois).

### 2.2 Conseil d'État
- Recenser les arrêts publiés au **Lebon** ou mentionnés aux **Tables**
  portant sur les matières suivies (mesures de police,
  proportionnalité, motivation des actes, responsabilité
  administrative, contentieux applicable).
- Source : conseil-etat.fr (filtre formation + période).

### 2.3 Conseil constitutionnel
- Recenser les **QPC** abrogatives ou réservatives intervenues dans
  l'année sur les codes et dispositions suivis.
- Source : conseil-constitutionnel.fr (rubrique QPC + période).

### 2.4 CJUE et CEDH (si pertinent)
- Arrêts impactant le droit français en matière de libertés publiques,
  données personnelles et garanties procédurales.

---

## 3. Mise à jour des annexes du skill

- `gabarits-requetes.md` : vérifier que les identifiants `LEGITEXT`
  des codes suivis n'ont pas changé.
- `checklist-vigueur.md` : aligner si des points de vigilance nouveaux
  ont émergé (ex. nouvelle disposition transitoire récurrente, nouveau
  type de renvoi normatif).

---

## 4. Contrôle de cohérence interne du SKILL.md

- [ ] Numérotation continue des 14 modes d'erreur.
- [ ] Numérotation continue des 7 principes (P1 à P7).
- [ ] Numérotation continue des 7 étapes (0 à 7).
- [ ] Numérotation continue des 4 techniques (T1 à T4).
- [ ] Les 4 modules ont chacun leurs déclencheurs et leur contenu.
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
   d'article (ex. « quel article pose le principe de légalité des
   délits et des peines ? »). Vérifier l'en-tête standardisé, l'absence
   de modules activés dans l'encart final.

2. **Mode A + PÉNAL + ACTE-ADMIN** — requête de qualification + acte
   (ex. « qualification d'un dépôt illégal de déchets et possibilité
   d'une mise en demeure »). Vérifier la décomposition élémentaire de
   l'infraction, le contrôle de proportionnalité Benjamin, la
   triangulation appliquée à juste mesure.

3. **Mode B `[complet]`** — requête institutionnelle exigeante
   (ex. « `[complet]` note sur l'articulation entre un régime de police
   générale et un régime de police spéciale »). Vérifier que tous les
   modules sont activés, certains marqués « sans objet à cette
   espèce » avec justification.

Si l'un des tests révèle un défaut de cohérence ou d'application →
correction immédiate avant clôture de la revue.

---

## 8. Clôture

- Commit avec message format : `chore(skill): revue annuelle AAAA-MM-JJ`.
- Mettre à jour les métadonnées de suivi dans votre projet (version et date).
