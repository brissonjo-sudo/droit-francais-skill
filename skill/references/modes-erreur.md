# Les 18 modes d'erreur — détail (§1)

> Référencé depuis `SKILL.md §1`. Détail et exemples de chacun des dix-huit
> modes d'erreur du LLM en droit que la méthodologie est conçue à bloquer.
> La table compacte est dans le noyau ; la cartographie « quel principe /
> quelle étape bloque quel mode » est dans `vault/matrice-modes.md`.

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

Tout le noyau et, pour les modes 15 à 18, la route DOC-AUDIT sont conçus
pour bloquer ces dix-huit modes. Chaque principe
et chaque étape mentionnent les modes qu'ils neutralisent (« → Bloque
modes… »).

**Note (v2.1.0).** L'étape 0 bis n'ajoute pas un mode supplémentaire : elle agit
en amont, comme **garde procédurale** empêchant de déclencher les modes 10
et 14 (analyse du mauvais régime ou du mauvais champ territorial sur une
hypothèse décisionnelle non levée). Elle prolonge P2 et P7 au stade de
l'entrée.
