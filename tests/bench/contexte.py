"""Contrats v2 communs aux moteurs ; aucune clé ni preuve privée en sortie."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

CATEGORIES_INFRA = frozenset({"quota_429", "budget", "delai", "transport", "interruption",
    "isolation", "contamination", "gel", "runtime", "modele", "outil", "profil"})
IRRECUPERABLES = frozenset({"isolation", "contamination", "gel", "runtime", "modele"})


def etat_canonique() -> Path:
    """Même racine utilisateur pour tous les worktrees ; pas d'option CLI."""
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return (base / "droit-francais" / "bench-v2").resolve()


@dataclass(frozen=True)
class ContexteExecution:
    """Une tentative d'étude déjà réservée ; HTTP a ses réservations distinctes."""

    series_sha256: str
    identite: str
    attempt_id: str
    tentative: int
    modele: str
    moteur: str
    echeance_monotone: float
    reservation: dict
    racine_etat: Path
