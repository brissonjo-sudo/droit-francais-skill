# Checklist — Vérification d'entrée en vigueur

Annexe à [`SKILL.md`](../SKILL.md). Détaille les étapes **2, 3 et 5** de
la procédure (récupération, fraîcheur, articulation).

À appliquer **systématiquement** après avoir accédé à la fiche
Légifrance. Chaque point est binaire : ✅ confirmé / ❌ problème à
signaler. Chaque ❌ déclenche un retour à l'étape concernée ou
l'abstention (P6).

---

## Checklist rapide (note express)

```
[ ] 1.  Fiche Légifrance consultée directement (pas un résumé)        → P1, mode 6
[ ] 2.  Identifiant LEGIARTI (ou JORFTEXT) relevé par appel d'outil   → P4, P1 (provenance), modes 1, 4
[ ] 3.  Champ "Version en vigueur depuis le" renseigné                → P2, mode 2
[ ] 4.  Aucune mention "Abrogé" visible                               → mode 2
[ ] 5.  Aucune modification postérieure à la date de référence        → mode 3
[ ] 6.  Décret d'application paru (si la loi le subordonne)           → mode 9
[ ] 7.  Champ territorial conforme à la situation                     → mode 10
[ ] 8.  Date de consultation notée                                    → P4
[ ] 9.  Renvois normatifs résolus (« dans les conditions… », etc.)    → mode 12
[ ] 10. Dispositions transitoires de la loi/décret modificateur lues  → mode 11
[ ] 11. Décisions QPC abrogatives/réservatives vérifiées              → mode 2
[ ] 12. Prescriptions et délais comparés aux dates faits/action       → étape 5, contrôle 7
[ ] 13. Test cumulatif/alternatif (« et » vs « ou ») effectué         → mode 13
[ ] 14. Fonction juridique du texte (compétence/sanction/…) identifiée → mode 14, P4
```

Si tous les points sont ✅ → procéder à la citation normalisée (P4).
Si un point est ❌ → procédure correspondante ci-dessous.

---

## Point 1 — Accès direct à la fiche Légifrance (P1, mode 6)

**Vérifier :** l'URL consultée est bien `legifrance.gouv.fr` (ou
`courdecassation.fr`, `conseil-etat.fr`, etc.) et la page affiche le
texte intégral avec ses métadonnées.

**Si non accessible :** noter l'indisponibilité et **refuser la
citation** (déclencheur d'abstention n° 1).

---

## Point 2 — Identifiant LEGIARTI / JORFTEXT (P4, modes 1 et 4)

**Où le trouver :** dans l'URL de la fiche ou dans l'onglet
« Informations / Identifiant ».

Format : `LEGIARTI` + 12 à 18 chiffres (ex. `LEGIARTI000049123456`).

**Si absent :** chercher l'article via `scripts/legifrance.py` (API
PISTE) ou la recherche plein texte Légifrance. **Ne pas citer sans cet
identifiant** (mode 1 : hallucination de référence).

**Règle de provenance (P1).** L'identifiant doit avoir été **récupéré
dans la session** (appel d'outil), jamais reconstitué de mémoire. À
défaut : le marquer `⚠️ non vérifié — identifiant non récupéré` et
interdire le gabarit C.

**Cas critique — articles voisins (mode 4) :** vérifier que
l'identifiant correspond bien à l'article cherché. Exemple R317-8 vs
L317-4 C. route : confronter le contenu de la fiche à la question.
Une lettre L/R, un chiffre, une partie change tout.

---

## Point 3 — Champ « Version en vigueur depuis le » (P2, mode 2)

**Où le trouver :** en haut de la fiche article.

**À distinguer de :**
- la date de **promulgation** de la loi modificatrice (≠ date d'entrée
  en vigueur),
- la date de **publication au JORF** (peut être différente si délai
  spécifié dans le texte).

**Si champ absent ou ambigu :** vérifier l'article de la loi/décret
modificateur pour la date d'entrée en vigueur effective.

---

## Point 4 — Vérification de l'abrogation (mode 2)

**Sur la fiche Légifrance :**
- Absence de bandeau rouge « Ce texte a été abrogé ».
- Absence de mention « Abrogé par … du JJ/MM/AAAA ».

**Si abrogé :**
1. Identifier le texte de remplacement (lien sur la fiche).
2. Relever sa date d'entrée en vigueur.
3. Signaler l'abrogation **avant** toute analyse (encadré ⚠️).
4. Ne citer l'article abrogé que pour l'analyse historique, jamais
   comme droit positif applicable.

---

## Point 5 — Absence de modification postérieure (mode 3)

**Sur la fiche Légifrance :**
1. Vérifier l'onglet « Versions » ou « Historique ».
2. Confirmer qu'aucune modification n'est intervenue entre la date
   d'entrée en vigueur relevée et la date de référence.
3. Si plusieurs versions existent → identifier la version applicable
   à la date de référence et relever son identifiant LEGIARTI
   **spécifique**.

**Cas de la version historique** (date de référence dans le passé) :
- Légifrance permet d'afficher un article « au [date] » via le
  sélecteur de date.
- Citer l'identifiant LEGIARTI de cette version historique.
- Format : `version en vigueur du JJ/MM/AAAA au JJ/MM/AAAA`.

---

## Point 6 — Décret d'application (mode 9)

**Vérifier :** si la loi précise que ses dispositions s'appliquent
« dans les conditions fixées par décret en Conseil d'État » ou
similaire, **le décret a-t-il été pris ?**

**Comment vérifier :**
- Onglet « Textes d'application » sur la fiche de la loi sur Légifrance.
- Recherche du NOR ou de l'intitulé du décret au JORF.

**Si décret non pris :** signaler explicitement — la loi est
**inapplicable** sur ce point. C'est une cause fréquente d'erreur
sur les lois récentes.

---

## Point 7 — Champ territorial (mode 10)

**Vérifier l'étendue d'application :**
- Métropole hors Alsace-Moselle (régime particulier de droit local).
- Alsace-Moselle (Bas-Rhin, Haut-Rhin, Moselle) — droit local
  spécifique sur certaines matières (associations, presse, etc.).
- Outre-mer — application de plein droit (DROM) ou par mention
  expresse (COM) ; spécificités Mayotte, Saint-Barthélemy, etc.
- **Île-de-France** : compétences de police municipale partagées avec
  la préfecture de police (Paris) ou modulées (petite couronne).
- **Paris intra-muros** : régime spécifique de police (préfet de
  police, et non maire jusqu'aux récentes réformes — à vérifier sur
  chaque point).

**En petite couronne parisienne (Hauts-de-Seine, Seine-Saint-Denis,
Val-de-Marne) :** attention au partage des compétences avec la
préfecture de police sur certaines matières — vérifier le périmètre
exact pour la commune concernée.

---

## Point 8 — Date de consultation (P4)

Noter la date du jour au moment de l'accès. Figure dans la citation
normalisée : `consulté le JJ/MM/AAAA`.

---

## Signalements spéciaux

### Vacatio legis
Texte publié au JORF mais date d'entrée en vigueur future.

Indicateurs Légifrance : « Version en vigueur à partir du [date
future] » ou « Version à venir ».

**Action :** signaler explicitement + indiquer la date d'entrée en
vigueur prévue.

### Application différée (décret non pris)
Voir Point 6.

### Abrogation implicite
Rare mais possible : un texte postérieur peut abroger implicitement
un texte antérieur par incompatibilité. Ne ressort pas clairement de
Légifrance.

**Action :** signaler la possibilité si deux textes semblent
contradictoires. Recommander une vérification juridique approfondie.

### Texte territorial ou local
Voir Point 7.

### Revirement de jurisprudence
Si la position citée s'appuie sur un arrêt ancien, vérifier
qu'aucun arrêt postérieur n'a opéré un revirement. La triangulation
(T2) sur deux requêtes différentes est utile ici.

### Renvois normatifs (mode 12, ajouté v2.0.0)
Si l'article cité contient un renvoi (« dans les conditions prévues
par décret », « tel que défini à l'article… », « selon les modalités
fixées par arrêté »), suivre le renvoi **jusqu'à sa source ultime** :
le décret existe-t-il ? est-il en vigueur ? quelle est la définition
renvoyée ? Une analyse qui s'arrête à l'article principal sans
résoudre ses renvois est incomplète et doit être signalée comme telle.

### Dispositions transitoires (mode 11, ajouté v2.0.0)
Lire systématiquement les dispositions transitoires de la loi ou du
décret modificateur. Un texte peut être **en vigueur sans être
applicable** à la situation analysée si une disposition transitoire
maintient l'ancien régime pour les procédures, situations ou faits
antérieurs.

### QPC abrogatives ou réservatives (ajouté v2.0.0)
Vérifier sur la fiche Légifrance la mention d'une décision QPC ayant
abrogé ou réservé l'interprétation de la disposition. Une réserve
d'interprétation du Conseil constitutionnel modifie la portée du
texte sans en changer la lettre.

### Test cumulatif / alternatif (mode 13, ajouté v2.0.0)
Lire la structure logique du texte. Les conditions d'application
sont-elles liées par « et » (cumulatives) ou « ou » (alternatives) ?
Existe-t-il des exceptions, exemptions, seuils ? Inverser « et » et
« ou » est une erreur de raisonnement classique et grave.

### Prescriptions et délais (étape 5, ajouté v2.0.0)
Comparer la date des faits ou de l'acte à la date d'action ou
d'analyse. Prescription de l'action publique, prescription
contraventionnelle, forclusion administrative, délais de recours
contentieux : un texte applicable peut être procéduralement
inopérant par expiration des délais.
