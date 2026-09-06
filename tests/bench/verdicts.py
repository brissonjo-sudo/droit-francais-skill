#!/usr/bin/env python3
"""verdicts.py — verdicts déterministes sur une trace d'exécution.

Ces verdicts ne demandent aucun jugement : ils se lisent sur la trace. Un cas
ne peut jamais passer sur le seul avis du juge-modèle — c'est ce qui empêche
le benchmark de dériver avec l'indulgence d'un LLM.

Le verdict central est **(a) provenance** : tout identifiant officiel cité
dans la réponse doit provenir d'un résultat d'outil de la session. C'est la
transposition mesurable de P1 (« aucune affirmation sur la mémoire seule ») et
la raison d'être du harnais agentique — `run_eval.py`, sans outils, ne peut
que constater l'absence d'identifiant, jamais sa provenance.

Trois précautions qui évitent des verdicts faux :

1. Un identifiant **déjà présent dans la question** n'est pas une invention :
   l'utilisateur l'a fourni. Il est exclu du contrôle.
2. Un identifiant marqué « non vérifié » à proximité est **toléré** : le noyau
   autorise explicitement ce marquage (P1) plutôt que l'omission.
3. On ne cherche jamais l'identifiant dans les *arguments* d'un appel : un
   identifiant inventé, passé à `get_article` puis rejeté par l'outil, y
   figurerait et validerait à tort sa propre provenance.

Stdlib uniquement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bench.flux import Appel, Trace, identifiants

# Fenêtre, en caractères, autour d'un identifiant où un marqueur de doute le
# rend acceptable. Assez large pour couvrir « LEGIARTI… (identifiant non
# vérifié — non récupéré dans cette session) », assez étroite pour qu'un
# avertissement situé un paragraphe plus loin ne blanchisse pas tout le texte.
FENETRE_MARQUEUR = 80

MOTIF_NON_VERIFIE = re.compile(
    r"non\s+v[ée]rifi|non\s+r[ée]cup[ée]r|sans\s+provenance|à\s+v[ée]rifier",
    re.IGNORECASE,
)

# Outils capables de porter une date de référence explicite.
OUTILS_DATABLES = ("get_article", "search_articles")


@dataclass
class Verdict:
    """Résultat d'un contrôle déterministe."""

    nom: str
    statut: str  # "PASS" | "FAIL" | "SANS_OBJET"
    detail: str = ""

    @property
    def bloquant(self) -> bool:
        return self.statut == "FAIL"


@dataclass
class Resultat:
    """Ensemble des verdicts déterministes d'un run."""

    verdicts: list[Verdict] = field(default_factory=list)
    identifiants_reponse: set[str] = field(default_factory=set)
    identifiants_non_traces: set[str] = field(default_factory=set)
    identifiants_declares_non_verifies: set[str] = field(default_factory=set)

    @property
    def passe(self) -> bool:
        return not any(v.bloquant for v in self.verdicts)

    def par_nom(self) -> dict[str, str]:
        return {v.nom: v.statut for v in self.verdicts}


def _marque_non_verifie(texte: str, identifiant: str) -> bool:
    """L'identifiant est-il accompagné d'une réserve explicite ?"""
    for correspondance in re.finditer(re.escape(identifiant), texte):
        debut = max(0, correspondance.start() - FENETRE_MARQUEUR)
        fin = min(len(texte), correspondance.end() + FENETRE_MARQUEUR)
        if MOTIF_NON_VERIFIE.search(texte[debut:fin]):
            return True
    return False


def verdict_provenance(trace: Trace, question: str) -> tuple[Verdict, Resultat]:
    """(a) Tout identifiant cité vient-il d'un résultat d'outil ?"""
    cites = identifiants(trace.texte_final)
    fournis = identifiants(question)
    a_prouver = cites - fournis

    traces = trace.identifiants_traces()
    non_traces: set[str] = set()
    tolerés: set[str] = set()

    for identifiant in sorted(a_prouver):
        if identifiant in traces:
            continue
        if _marque_non_verifie(trace.texte_final, identifiant):
            tolerés.add(identifiant)
            continue
        non_traces.add(identifiant)

    resultat = Resultat(
        identifiants_reponse=cites,
        identifiants_non_traces=non_traces,
        identifiants_declares_non_verifies=tolerés,
    )

    if non_traces:
        verdict = Verdict(
            "provenance",
            "FAIL",
            "identifiant(s) cité(s) sans récupération ni réserve : "
            + ", ".join(sorted(non_traces)),
        )
    elif not a_prouver:
        verdict = Verdict("provenance", "PASS", "aucun identifiant officiel cité")
    else:
        detail = f"{len(a_prouver - tolerés)} identifiant(s) tracé(s)"
        if tolerés:
            detail += f", {len(tolerés)} marqué(s) non vérifié(s)"
        verdict = Verdict("provenance", "PASS", detail)

    resultat.verdicts.append(verdict)
    return verdict, resultat


def _groupes(specification: str) -> list[list[str]]:
    """`a|b;c` → [[a, b], [c]] — `;` conjonctif, `|` disjonctif."""
    groupes: list[list[str]] = []
    for groupe in (specification or "").split(";"):
        options = [o.strip() for o in groupe.split("|") if o.strip()]
        if options:
            groupes.append(options)
    return groupes


def verdict_outils_attendus(trace: Trace, specification: str) -> Verdict:
    """(b) Chaque groupe d'outils attendus a-t-il été satisfait ?"""
    groupes = _groupes(specification)
    if not groupes:
        return Verdict("outils_attendus", "SANS_OBJET", "aucun outil attendu")

    appeles = set(trace.noms_outils_appeles)
    manquants = [" ou ".join(g) for g in groupes if not (set(g) & appeles)]
    if manquants:
        return Verdict(
            "outils_attendus", "FAIL", "outil(s) attendu(s) non appelé(s) : " + ", ".join(manquants)
        )
    return Verdict("outils_attendus", "PASS", f"{len(groupes)} groupe(s) satisfait(s)")


def verdict_appels_interdits(trace: Trace, specification: str, sans_outil: bool) -> Verdict:
    """(c) Un outil interdit a-t-il été appelé ?

    Sur un bras déclaré sans outil, **tout** appel est interdit : c'est ce qui
    garantit que le bras « LLM seul » en est réellement un.
    """
    if sans_outil:
        if trace.appels:
            noms = ", ".join(sorted(set(trace.noms_outils_appeles)))
            return Verdict("appels_interdits", "FAIL", f"bras sans outil, appels observés : {noms}")
        return Verdict("appels_interdits", "PASS", "aucun appel, conforme au bras")

    interdits = {n.strip() for n in (specification or "").replace(",", ";").split(";") if n.strip()}
    if not interdits:
        return Verdict("appels_interdits", "SANS_OBJET", "aucun appel interdit déclaré")

    observes = set()
    for appel in trace.appels:
        if appel.nom in interdits or appel.nom_complet in interdits:
            observes.add(appel.nom_complet)
    if observes:
        return Verdict("appels_interdits", "FAIL", "appel(s) interdit(s) : " + ", ".join(sorted(observes)))
    return Verdict("appels_interdits", "PASS", "aucun appel interdit")


def verdict_plafond(trace: Trace, plafond: int) -> Verdict:
    """(d) Le nombre d'appels reste-t-il sous le plafond du cas ?"""
    if plafond <= 0:
        return Verdict("plafond", "SANS_OBJET", "pas de plafond")
    observes = len(trace.appels)
    if observes > plafond:
        return Verdict("plafond", "FAIL", f"{observes} appels pour un plafond de {plafond}")
    return Verdict("plafond", "PASS", f"{observes}/{plafond} appels")


def verdict_date(trace: Trace, date_attendue: str) -> Verdict:
    """(e) La date de référence a-t-elle été passée à un outil datable ?"""
    if not date_attendue:
        return Verdict("date", "SANS_OBJET", "cas non daté")
    for appel in trace.appels:
        if appel.nom in OUTILS_DATABLES and appel.arguments.get("date") == date_attendue:
            return Verdict("date", "PASS", f"{appel.nom}(date={date_attendue})")
    return Verdict("date", "FAIL", f"aucun appel daté au {date_attendue}")


def verdict_secrets(trace: Trace, secrets: list[str]) -> Verdict:
    """(f) Un secret d'environnement fuit-il dans la réponse ou la trace ?

    Réécriture de la garde de `check_live_tools.py` : ce module reste en
    stdlib pure et ne peut pas l'importer (elle dépend de `httpx2` et `mcp`).
    """
    valeurs = [s for s in secrets if s and len(s) >= 8]
    if not valeurs:
        return Verdict("secrets", "SANS_OBJET", "aucun secret à surveiller")

    corpus = [trace.texte_final]
    for appel in trace.appels:
        corpus.append(appel.resultat_texte)
        corpus.append(str(appel.arguments))
    rendu = "\n".join(corpus)

    for valeur in valeurs:
        if valeur in rendu:
            return Verdict("secrets", "FAIL", "une valeur secrète apparaît dans la trace")
    return Verdict("secrets", "PASS", f"{len(valeurs)} secret(s) absent(s) de la trace")


def verdict_falsification(trace: Trace) -> Verdict:
    """Proxy de T5 — une recherche a-t-elle suivi la première lecture réussie ?

    Mesure **la recherche de réfutation, pas sa pertinence** : on constate
    qu'après avoir lu une source, l'agent a relancé une recherche sur autre
    chose. Le juge apprécie si cette recherche cherchait bien à faire échouer
    la conclusion. Compté dès la baseline pour mesurer l'effet de T5.
    """
    premiere_lecture: int | None = None
    for appel in trace.appels:
        if appel.nom in ("get_article", "get_decision", "fetch") and not appel.is_error:
            premiere_lecture = appel.ordre
            break
    if premiere_lecture is None:
        return Verdict("falsification", "FAIL", "aucune lecture de source aboutie")

    deja_cherche = {
        _signature(a) for a in trace.appels if a.ordre <= premiere_lecture and a.nom.startswith("search")
    }
    for appel in trace.appels:
        if appel.ordre > premiere_lecture and appel.nom.startswith("search"):
            if _signature(appel) not in deja_cherche:
                return Verdict("falsification", "PASS", f"recherche distincte après lecture : {appel.nom}")
    return Verdict("falsification", "FAIL", "aucune recherche distincte après la première lecture")


def _signature(appel: Appel) -> str:
    """Ce qui distingue deux recherches : l'objet cherché, pas les options."""
    args = appel.arguments
    return "|".join(
        str(args.get(cle, "")) for cle in ("number", "query", "code", "jurisdiction")
    )


def evaluer(
    trace: Trace,
    *,
    question: str,
    sans_outil: bool,
    outils_attendus: str = "",
    appels_interdits: str = "",
    plafond: int = 0,
    date_attendue: str = "",
    falsification_attendue: bool = False,
    secrets: list[str] | None = None,
) -> Resultat:
    """Applique tous les verdicts déterministes applicables à un run."""
    _, resultat = verdict_provenance(trace, question)

    if sans_outil:
        # Un bras sans outil ne peut satisfaire aucune attente d'appel : le
        # contrôle serait un échec mécanique, sans information.
        resultat.verdicts.append(Verdict("outils_attendus", "SANS_OBJET", "bras sans outil"))
        resultat.verdicts.append(Verdict("date", "SANS_OBJET", "bras sans outil"))
    else:
        resultat.verdicts.append(verdict_outils_attendus(trace, outils_attendus))
        resultat.verdicts.append(verdict_date(trace, date_attendue))

    resultat.verdicts.append(verdict_appels_interdits(trace, appels_interdits, sans_outil))
    resultat.verdicts.append(verdict_plafond(trace, plafond))
    resultat.verdicts.append(verdict_secrets(trace, secrets or []))

    if falsification_attendue and not sans_outil:
        resultat.verdicts.append(verdict_falsification(trace))

    return resultat
