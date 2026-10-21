# Les 18 modes d'erreur — détail

> Référencé depuis le noyau du `SKILL.md`. Détail et exemples de chacun des
> dix-huit modes d'erreur du LLM en droit que la méthodologie vise à prévenir.

---

1. **Hallucination de référence** — article inexistant ou contenu inexact.
2. **Effet de cutoff** — modification postérieure à la date d'entraînement
   ignorée.
3. **Confusion de versions** — rédactions ancienne et actuelle mélangées.
4. **Confusion d'articles voisins** — ex. R317-8 vs L317-4 C. route.
5. **Raisonnement par analogie non vérifié**.
6. **Confusion doctrine / texte** — blog d'avocat pris pour position
   juridictionnelle.
7. **Confusion de juridictions** — Cass., CE, CC, CJUE, CEDH mélangées.
8. **Oubli de la hiérarchie des normes**.
9. **Oubli du décret d'application**.
10. **Oubli du champ d'application territorial**.
11. **Oubli des dispositions transitoires** d'une réforme.
12. **Oubli des renvois normatifs** — article → décret → définition
    renvoyée non suivie jusqu'à sa source ultime.
13. **Inversion logique cumulatif / alternatif** — « et » devenu « ou ».
14. **Faux positif textuel** — article réel mais juridiquement non
    pertinent ; ou texte réel mobilisé pour la mauvaise fonction
    juridique (texte de compétence pris pour texte de sanction, etc.).
15. **Validation héritée** — un audit antérieur, une mention « vérifié » ou
    l'autorité supposée d'un autre modèle remplace la revérification
    indépendante des affirmations à risque.
16. **Citation exacte, conséquence fausse** — la source existe, mais ne
    permet pas l'action, la sanction ou la conclusion opérationnelle écrite.
17. **Mauvais acteur–lieu–propriétaire–pouvoir** — une compétence réelle est
    étendue au mauvais agent, espace, propriétaire ou type d'opération.
18. **Incohérence de corpus** — des fichiers d'un même dossier divergent sur
    un article, une date, un montant, un acteur, une procédure, un indicateur
    ou une qualification.

Le noyau Gemini vise à prévenir ces erreurs par ses principes, sa procédure
et ses modules. Pour les modes 15 à 18, appliquer en particulier la voie
DOC-AUDIT et le protocole `audit-documentaire.md`. Lorsqu'une information
manquante est décisionnelle, la faire préciser ou borner explicitement
l'analyse à une hypothèse conditionnelle, conformément à l'étape 0 de `SKILL.md`.
