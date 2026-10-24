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

## Présentation du noyau et public

> **Objet** : encoder la méthodologie rigoureuse de recherche en droit
> français applicable à tout usage professionnel — avocat, juriste,
> agent des forces de l'ordre, cadre territorial, candidat aux concours.
> Conçu contre **dix-huit modes d'erreur** identifiés du LLM en droit,
> autour de **sept principes**, d'une **procédure en neuf étapes**
> (étapes **0** et **0 bis** de cadrage, étapes **1 à 7** opératoires),
> d'un **double mode opératoire A/B**, de **six modules activables** et
> de **quatre techniques** de raisonnement juridique.
>
> **Public** : praticiens du droit français. Le métier de l'utilisateur
> (contexte territorial, domaines prioritaires, 3ᵉ regard d'auto-critique)
> se configure via un **profil** — voir `profil.md` et le dossier
> [`profils/`](../profils/) (§0, *Chargement du profil*). Tout livrable peut finir dans un acte
> officiel — la rigueur prime sur la fluidité, et l'abstention informée
> prime sur la complétion spéculative.

## Diagnostic et rôle de l'étape 0 bis

## 1. Diagnostic préalable — les 18 modes d'erreur à empêcher

Cette méthodologie est construite contre **dix-huit modes d'erreur** du
LLM en droit. Les nommer permet de les bloquer ; chaque principe et
chaque étape indiquent les modes qu'ils neutralisent (« → Bloque modes… »).

| # | Mode | # | Mode |

|---|------|---|------|

| 1 | Hallucination de référence | 10 | Oubli du champ territorial |

| 2 | Effet de cutoff | 11 | Oubli des dispositions transitoires |

| 3 | Confusion de versions | 12 | Oubli des renvois normatifs |

| 4 | Confusion d'articles voisins | 13 | Inversion cumulatif / alternatif |

| 5 | Analogie non vérifiée | 14 | Faux positif textuel |

| 6 | Confusion doctrine / texte | 15 | Validation héritée d'un audit antérieur |

| 7 | Confusion de juridictions | 16 | Citation exacte, conséquence fausse |

| 8 | Oubli de la hiérarchie des normes | 17 | Mauvais acteur–lieu–propriétaire–pouvoir |

| 9 | Oubli du décret d'application | 18 | Incohérence de corpus |


**Note.** L'étape 0 bis (v2.1.0) n'est pas un mode supplémentaire : garde procédurale
en amont, elle empêche de déclencher les modes 10 et 14 (mauvais régime /
mauvais champ sur une hypothèse décisionnelle non levée). Elle prolonge P2
et P7 au stade de l'entrée.
