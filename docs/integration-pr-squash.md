# Intégration des PR après squash — 10/10/2026

L'ordre reste **118 → 116 → 117**. Chaque fusion GitHub est une décision
humaine ; les branches dépendantes doivent ensuite intégrer le nouveau main
et repasser leurs contrôles. La présence d'un ancien commit de distribution
dans leur historique ne prouve pas qu'elles intègrent le nouveau commit squash.

Un rebase est possible, mais **n'est pas obligatoire**. Cette livraison
conserve les historiques publiés : elle choisit une fusion explicite de main
dans chaque branche dépendante, la résolution contrôlée des conflits, puis
un push normal. Le [manuel Git merge](https://git-scm.com/docs/git-merge)
décrit cette réunion des historiques et le fonctionnement de `--squash`,
qui ne conserve pas l'ascendance comme une fusion ordinaire.

## Procédure après chaque squash confirmé

1. Vérifier la PR fusionnée, le SHA de son squash et le nouveau main distant.
2. Vérifier que le worktree dépendant est propre ; conserver les modifications
   locales existantes si ce n'est pas le cas.
3. Faire `git fetch origin`, puis `git merge --no-ff origin/main` dans la
   branche concernée. Aucun force-push ni suppression de l'ancienne branche.
4. Examiner chaque conflit avec les deux contenus et leurs changements.
   Garder les correctifs squashés **et** les modifications propres au lot.
   Ne pas appliquer aveuglément une stratégie ours/theirs sur le dépôt réel.
5. Valider README français/anglais, liens, corpus, tests et CI du nouveau SHA.
6. Pousser normalement la branche et vérifier son diff contre main.
7. Après le squash de 116, intégrer le nouveau main dans 117, puis vérifier
   et changer sa base GitHub vers main. Cela laisse le lot Gemini reviewable
   indépendamment des anciens commits de campagne.

## Preuve locale limitée

Une simulation a été exécutée dans un dépôt temporaire séparé, avec hooks
désactivés, sans modifier les branches de travail ni GitHub. Elle utilise main
`a71d3d5`, distribution `0560a7c`, campagne `a5a1789` et Gemini `a1fd38c`.

Après squash simulé de 118, la fusion dans 116 rencontre un conflit add/add
sur README.en.md. Après résolution examinée, l'arbre final est identique à
celui de la campagne avant intégration : aucune traduction ni modification
de campagne n'est perdue. Après squash simulé de 116 puis intégration dans
117, les conflits sont résolus dans le dépôt temporaire ; l'arbre Gemini est
également identique à son arbre d'origine.

Cette simulation confirme une voie sans réécriture pour ces quatre SHA.
Elle ne garantit pas l'absence de nouveaux conflits après d'autres commits.
La procédure doit être revérifiée sur les SHA effectivement fusionnés.
