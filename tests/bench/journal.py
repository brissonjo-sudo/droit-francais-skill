#!/usr/bin/env python3
"""journal.py — persistance JSONL des résultats et reprise d'un run.

Reprend le patron de `check_service_health.py` + `summarize_surveillance.py` :
**une ligne JSON par mesure, écrite au fil de l'eau**. Un run de baseline dure
plusieurs heures ; s'il échoue à la 400ᵉ sonde, tout ce qui précède doit être
acquis, et la reprise doit sauter ce qui est déjà fait.

La clé de reprise est ``(agent, modèle, bras, id, répétition)``. Les lignes en
`infra_error` ne comptent pas comme faites : une instance endormie ou un quota
atteint doit être rejoué, sinon la panne se fige dans la baseline.

Stdlib uniquement.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

Cle = tuple[str, str, str, str, int]


def cle_de(ligne: dict[str, Any]) -> Cle:
    """Identité d'un run, pour la reprise et la comparaison."""
    return (
        str(ligne.get("agent", "")),
        str(ligne.get("modele", "")),
        str(ligne.get("bras", "")),
        str(ligne.get("id", "")),
        int(ligne.get("repetition", 1) or 1),
    )


def lire(chemin: Path | str) -> list[dict[str, Any]]:
    """Lit un JSONL en ignorant les lignes illisibles.

    Un fichier interrompu en cours d'écriture se termine par une ligne
    tronquée : la rejeter vaut mieux que perdre tout ce qui précède.
    """
    fichier = Path(chemin)
    if not fichier.is_file():
        return []
    lignes: list[dict[str, Any]] = []
    with fichier.open(encoding="utf-8") as flux:
        for brute in flux:
            brute = brute.strip()
            if not brute:
                continue
            try:
                charge = json.loads(brute)
            except (ValueError, TypeError):
                continue
            if isinstance(charge, dict):
                lignes.append(charge)
    return lignes


def deja_faits(chemin: Path | str) -> set[Cle]:
    """Runs acquis d'un JSONL : tout sauf les pannes d'infrastructure."""
    return {
        cle_de(ligne)
        for ligne in lire(chemin)
        if ligne.get("statut") != "infra_error"
    }


class Journal:
    """Écriture incrémentale, une ligne par run."""

    def __init__(self, chemin: Path | str) -> None:
        self.chemin = Path(chemin)
        self.chemin.parent.mkdir(parents=True, exist_ok=True)
        self.ecrites = 0

    def ajouter(self, ligne: dict[str, Any]) -> None:
        """Ajoute une ligne et la pousse sur disque immédiatement.

        Le `flush` + `fsync` coûte peu au regard d'un run de plusieurs
        secondes, et garantit qu'une interruption brutale ne perd pas la
        dernière mesure.
        """
        with self.chemin.open("a", encoding="utf-8") as flux:
            flux.write(json.dumps(ligne, ensure_ascii=False) + "\n")
            flux.flush()
            os.fsync(flux.fileno())
        self.ecrites += 1

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(lire(self.chemin))
