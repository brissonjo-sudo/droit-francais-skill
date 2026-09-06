#!/usr/bin/env python3
"""cadence.py — respect du quota d'appels du serveur MCP.

`mcp_server/runtime.py` limite un principal authentifié à
``MCP_USER_CALLS_PER_MINUTE`` appels par minute (défaut : 20). Un benchmark
qui l'ignore ne mesure plus le skill : il mesure un étranglement, et les cas
sortent en `infra_error` au lieu de dire quoi que ce soit sur la méthode.

Le seau réserve le **plafond d'appels** du cas avant de le lancer, puis
corrige avec la consommation réelle. Réserver après coup laisserait un cas
bavard dépasser le quota au milieu de son exécution, quand il est trop tard.

L'horloge est injectable pour que le comportement soit testable sans attendre.

Stdlib uniquement.
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable

# Marge sous le quota serveur : une seconde d'écart d'horloge entre le poste
# et Render suffirait à faire passer le 20ᵉ appel dans la fenêtre précédente.
APPELS_PAR_MINUTE = 18
FENETRE_S = 60.0


class Cadence:
    """Seau glissant sur une fenêtre d'une minute."""

    def __init__(
        self,
        *,
        appels_par_minute: int = APPELS_PAR_MINUTE,
        horloge: Callable[[], float] | None = None,
        attente: Callable[[float], None] | None = None,
    ) -> None:
        self.appels_par_minute = max(1, appels_par_minute)
        self._horloge = horloge or time.monotonic
        self._attente = attente or time.sleep
        self._evenements: deque[tuple[float, int]] = deque()
        self.attente_cumulee_s = 0.0

    def _purger(self) -> None:
        limite = self._horloge() - FENETRE_S
        while self._evenements and self._evenements[0][0] <= limite:
            self._evenements.popleft()

    @property
    def consommes(self) -> int:
        self._purger()
        return sum(nombre for _, nombre in self._evenements)

    def reserver(self, nombre: int) -> float:
        """Attend, si nécessaire, d'avoir la place pour ``nombre`` appels.

        Rend la durée d'attente observée — consignée dans le résumé, parce
        qu'un benchmark majoritairement passé à attendre doit se voir.
        """
        nombre = max(1, min(nombre, self.appels_par_minute))
        attendu = 0.0
        while True:
            self._purger()
            if self.consommes + nombre <= self.appels_par_minute:
                self._evenements.append((self._horloge(), nombre))
                self.attente_cumulee_s += attendu
                return attendu
            # Attendre que le plus ancien événement sorte de la fenêtre.
            plus_ancien = self._evenements[0][0]
            delai = max(0.0, plus_ancien + FENETRE_S - self._horloge()) + 0.05
            self._attente(delai)
            attendu += delai

    def corriger(self, reserve: int, reel: int) -> None:
        """Aligne la réservation sur la consommation constatée."""
        if not self._evenements:
            return
        horodatage, nombre = self._evenements[-1]
        ajuste = max(0, nombre - reserve + max(0, reel))
        if ajuste == 0:
            self._evenements.pop()
        else:
            self._evenements[-1] = (horodatage, ajuste)
