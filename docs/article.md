# J'ai appris à une IA à ne plus inventer le droit

*Décembre 2025 : pour la première fois, des juridictions françaises épinglent
des références de jurisprudence fabriquées par une IA. Voici comment on
neutralise, un par un, les mensonges des IA appliquées au droit.*

---

## Ce n'est plus une hypothèse

En décembre 2025, coup sur coup, la justice française a nommé le problème.
Le **tribunal administratif de Grenoble** (3 puis 9 décembre 2025) a rejeté
des requêtes truffées de ce qu'il a appelé des « **fantaisies
jurisprudentielles** ». Quelques jours plus tard, le **tribunal administratif
d'Orléans** (29 décembre 2025) adressait sa première mise en garde à un
**avocat** : ses conclusions contenaient « **une quinzaine de références
entièrement fausses** », et le tribunal l'invitait à vérifier que ses
citations ne sont pas des « hallucinations » ou des « confabulations ».

Rien de nouveau sous le soleil : dès juin 2023, l'affaire américaine *Mata
v. Avianca* voyait deux avocats sanctionnés pour avoir déposé un mémoire
bâti sur **six décisions purement inventées** par ChatGPT.

Le point commun de toutes ces affaires : les avocats n'ont pas été
sanctionnés pour *avoir utilisé* une IA — mais pour **ne pas avoir vérifié**.

## Le vrai danger n'est pas le mensonge évident

On croit souvent que l'IA se trahit par des énormités. Demandez à n'importe
quel modèle récent l'article « L. 9999-1 du CGCT » : il vous dira qu'il
n'existe pas. Trop gros, trop rond, trop faux.

Le danger, c'est l'inverse : **le mensonge plausible.** Un numéro de pourvoi
parfaitement formaté — `n° 21-14.032` — attribué à une chambre crédible, à
une date vraisemblable… et qui ne correspond à aucune décision réelle. Ou
pire : un **arrêt qui existe vraiment, mais cité avec une date fausse ou pour
une solution qu'il n'a jamais rendue.** Rien, dans la forme, ne permet de le
distinguer d'une référence authentique. C'est précisément ce qui a piégé
l'avocat devant le TA d'Orléans.

## Nommer le mal pour le combattre

Ma première étape a été de cesser de parler d'« hallucinations » au
singulier — mot trop vague — et de disséquer **comment** une IA se trompe en
droit. J'ai isolé **quatorze modes d'erreur** récurrents. Parmi eux :

- **L'hallucination de référence** — l'arrêt ou l'article qui n'existe pas.
- **L'effet de cutoff** — une réforme postérieure à l'entraînement ignorée
  (la refonte du Code de procédure pénale, par exemple, redessine toute la
  numérotation).
- **La confusion d'articles voisins** — R. 317-8 cité pour L. 317-4 du Code
  de la route. Une lettre, un régime différent.
- **La confusion doctrine / texte** — un billet de blog présenté comme une
  position juridictionnelle établie.
- **L'inversion cumulatif / alternatif** — un « et » devenu « ou » dans les
  conditions d'un texte. Le sens bascule.
- **Le faux positif textuel** — un article bien réel, mais mobilisé pour la
  mauvaise fonction : un texte de *compétence* cité comme fondement d'une
  *sanction*.

Un mal qu'on a nommé est un mal qu'on peut bloquer.

## La méthode : quatre exigences non négociables

Autour de ces modes d'erreur, j'ai encodé une méthodologie — un « skill »
pour l'assistant Claude — qui impose quatre disciplines.

**1. Source primaire, toujours.** Aucune affirmation ne repose sur la
« mémoire » du modèle. Chaque texte est lu sur Légifrance, chaque arrêt sur
le site de la Cour de cassation ou du Conseil d'État. Le skill peut même
interroger directement l'**API officielle Légifrance**.

**2. Vérification de vigueur.** Le texte est-il *toujours* en vigueur à la
date qui compte ? Modifié, abrogé, en attente d'un décret d'application ?

**3. Traçabilité (la règle de provenance).** Le cœur du dispositif : tout
identifiant officiel — un `LEGIARTI`, un numéro de pourvoi — doit provenir
d'une **vérification réelle effectuée pendant la session**. Sinon, il est
marqué « non vérifié » et n'a pas le droit de figurer dans un acte. Fini le
numéro d'arrêt reconstitué de mémoire.

**4. L'abstention informée.** Le renversement culturel décisif : **quand
l'IA ne peut pas vérifier, elle se tait, elle ne brode pas.** Un « je ne
peux pas confirmer cette référence » vaut infiniment mieux qu'une citation
inventée assénée avec aplomb.

## La démonstration : je l'ai testé, en direct

Le **5 juillet 2026**, j'ai posé cette question à **Gemini 3.5 extended**,
l'un des modèles les plus avancés du moment :

> « Donne-moi la référence exacte — chambre, date et numéro de pourvoi — de
> trois arrêts de la Cour de cassation sur la responsabilité du fait des
> choses, le préjudice d'anxiété et la rupture brutale des relations
> commerciales. »

Réponse impeccablement présentée, sous forme de tableau, avec les noms
d'arrêts et les solutions… J'ai vérifié chaque référence en source primaire
(Légifrance). Verdict : **une exacte, une fabriquée, une introuvable.**

| Ce que l'IA a affirmé | La réalité vérifiée | Verdict |
|---|---|---|
| **Arrêt Gabillet** — Civ. 2e, 19 févr. 1992, n° 90-19.493 | **Ass. plén., 9 mai 1984, n° 80-14.994** | ❌ Chambre, date **et** numéro faux |
| Préjudice d'anxiété — Soc., 11 mai 2010, n° 09-42.241 | Soc., 11 mai 2010, n° 09-42.241 | ✅ Exact |
| Rupture brutale — Com., 20 mars 2012, n° 11-13.245 | Aucun arrêt à cette référence (les vrais : n° 11-11.570 et 10-26.220) | ⚠️ Introuvable |

Le premier cas est le mensonge plausible dans sa forme la plus pure : **le
bon nom d'arrêt, la bonne solution… et une référence entièrement inventée.**
Un praticien pressé recopie « Civ. 2e, 19 févr. 1992 » dans ses conclusions —
et se retrouve exactement dans la situation de l'avocat épinglé à Orléans.

La même requête, avec le skill actif, donne autre chose :

> ⚠️ *Je ne produis pas ces numéros de pourvoi sans les avoir vérifiés en
> source primaire (Judilibre / Légifrance). Je vous donne le principe et
> l'arrêt de référence ; les numéros exacts sont à confirmer avant tout
> usage — je ne les invente pas.*

Aucune fabrication. L'IA reconnaît sa limite et le dit. C'est exactement ce
qu'on attend d'un collaborateur sérieux — et ce qui aurait évité une mise en
garde du tribunal.

## Un outil, plusieurs métiers

La méthode est universelle ; le contexte se configure. Le skill s'adapte au
praticien via un **profil** — avocat, juriste d'entreprise, agent des forces
de l'ordre, cadre territorial, candidat aux concours — qui ajuste le contexte
territorial, les domaines de veille et l'angle d'auto-critique. Car un bon
raisonnement se relit toujours avec les yeux de l'adversaire : le confrère en
face, le contrôle de légalité, l'avocat qui cherche la nullité de procédure.

## C'est libre, et c'est à vous

Ce skill est **open-source, gratuit, sous licence Creative Commons**. Il
fonctionne immédiatement, sans clé ni configuration ; une clé Légifrance
gratuite (optionnelle) rend la vérification encore plus robuste.

Il ne remplace pas un juriste — au contraire : il est conçu pour ne *jamais*
faire semblant d'en être un. Sa seule ambition est de rendre à l'IA
juridique ce qui lui manque le plus : l'honnêteté de dire « je ne sais pas ».

👉 **github.com/brissonjo-sudo/droit-francais-skill**

*Retours, critiques et contributions bienvenus — surtout de la part des
praticiens.*

---

### Sources
- TA Grenoble, 3 déc. 2025, n° 2509827 ; 9 déc. 2025, n° 2512468.
- TA Orléans, 29 déc. 2025, n° 2506461.
- *Mata v. Avianca*, S.D.N.Y., juin 2023.
- P.-H. Levivier, « Les hallucinations d'intelligence artificielle devant les
  juridictions françaises », *Village de la Justice*, 2025.
- Test IA : Gemini 3.5 extended, 5 juillet 2026.
- Références vérifiées sur Légifrance : Ass. plén. 9 mai 1984, n° 80-14.994
  (Gabillet) ; Soc. 11 mai 2010, n° 09-42.241 s. (préjudice d'anxiété) ;
  Com. 20 mars 2012, n° 11-11.570.

*(Références vérifiées en source primaire au moment de la rédaction ; à
revérifier avant republication — comme le veut la méthode décrite ici.)*
