"""Outils (tool calling) de l'agent juridique Gemini.

Chaque fonction ci-dessous est le contrat exposé au modèle : le SDK
`google-genai` génère automatiquement la déclaration de fonction (nom,
paramètres, description) à partir de la signature typée et de la docstring.
Les deux doivent donc rester synchronisées avec l'implémentation réelle —
un changement de signature change ce que le modèle est autorisé à appeler.

Squelette volontairement non connecté : le corps de chaque fonction renvoie
un mock explicite. Voir le README du package pour brancher une vraie API
(Légifrance/PISTE, Judilibre, ou toute base de jurisprudence équivalente).
"""

from __future__ import annotations

from typing import Any


def search_legal_database(query: str) -> dict[str, Any]:
    """Recherche des lois, articles de codes et textes réglementaires en vigueur.

    L'agent DOIT appeler cet outil avant toute affirmation sur le droit
    positif (texte de loi, article de code, décret, arrêté, règlement) :
    il ne doit jamais répondre à partir de sa seule mémoire d'entraînement,
    qui peut être obsolète ou fausse.

    Args:
        query: Requête en langage naturel ou référence explicite (ex.
            "article 1240 du Code civil", "responsabilité du fait des
            produits défectueux", "RGPD article 6").

    Returns:
        Un dictionnaire avec :
        - "query": la requête telle que reçue.
        - "results": liste de textes trouvés, chacun avec au minimum
          "title", "reference" (ex. "Code civil, art. 1240"), "text_excerpt",
          "source_url" et "in_force" (bool, statut de vigueur à la date
          de la recherche).
        - "connected": False tant que l'API réelle n'est pas branchée.

    Raises:
        NotImplementedError: implicitement, via le mock — remplacer ce
            corps par un appel HTTP réel avant tout usage en production.
    """
    # TODO: brancher une API réelle (ex. Légifrance/PISTE) et retirer ce mock.
    return {
        "query": query,
        "results": [],
        "connected": False,
    }


def search_case_law(query: str) -> dict[str, Any]:
    """Recherche la jurisprudence et les décisions de justice pertinentes.

    L'agent DOIT appeler cet outil avant de citer une décision de justice
    (arrêt, jugement, avis) : nom, juridiction, date et numéro doivent
    provenir de ce résultat, jamais être reconstitués de mémoire.

    Args:
        query: Requête en langage naturel décrivant les faits, la question
            de droit ou une référence partielle (ex. "arrêt Cour de
            cassation sur la clause abusive dans un contrat de bail").

    Returns:
        Un dictionnaire avec :
        - "query": la requête telle que reçue.
        - "results": liste de décisions trouvées, chacune avec au minimum
          "jurisdiction" (juridiction), "date", "case_number" (numéro de
          pourvoi ou de rôle), "summary" et "source_url".
        - "connected": False tant que l'API réelle n'est pas branchée.

    Raises:
        NotImplementedError: implicitement, via le mock — remplacer ce
            corps par un appel HTTP réel avant tout usage en production.
    """
    # TODO: brancher une API réelle (ex. Judilibre) et retirer ce mock.
    return {
        "query": query,
        "results": [],
        "connected": False,
    }
