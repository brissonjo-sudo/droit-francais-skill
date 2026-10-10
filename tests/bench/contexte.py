"""Contrats v2 communs aux moteurs ; aucune clé ni preuve privée en sortie."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

CATEGORIES_INFRA = frozenset({"quota_429", "budget", "delai", "transport", "interruption",
    "isolation", "contamination", "gel", "runtime", "modele", "outil", "profil",
    "reponse_tronquee", "reponse_bloquee", "format_jugement"})
IRRECUPERABLES = frozenset({"isolation", "contamination", "gel", "runtime", "modele"})


def etat_canonique() -> Path:
    """Identité OS stable ; HOME/XDG/LOCALAPPDATA ne changent pas les compteurs."""
    if os.name == "nt":
        import ctypes
        import uuid
        identifiant = (ctypes.c_ubyte * 16).from_buffer_copy(uuid.UUID("f1b32785-6fba-4fcf-9d55-7b8e7f157091").bytes_le)
        pointer = ctypes.c_void_p()
        shell = ctypes.WinDLL("shell32")
        shell.SHGetKnownFolderPath.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
        shell.SHGetKnownFolderPath.restype = ctypes.c_long
        ole = ctypes.WinDLL("ole32")
        ole.CoTaskMemFree.argtypes = [ctypes.c_void_p]
        try:
            if shell.SHGetKnownFolderPath(identifiant, 0, None, ctypes.byref(pointer)) != 0:
                raise ValueError("identité de stockage OS indisponible")
            base = Path(ctypes.wstring_at(pointer))
        finally:
            ole.CoTaskMemFree(pointer)
    else:
        import pwd
        base = Path(pwd.getpwuid(os.getuid()).pw_dir) / ".local" / "state"
    return (base / "droit-francais" / "bench-v2").resolve()


def assurer_ancre(state: Path, *, auteur: str = "", motif: str = "") -> None:
    """Sous verrou, uniquement pour la racine production ; aucun effet à l'import."""
    if state.resolve() != etat_canonique():
        return  # injection explicite d'état réservée aux API de tests, jamais CLI
    import json
    from bench import etude_v2
    from bench.journal import Journal
    anchor = state.parent / "bench-v2-ancre.json"
    if anchor.exists():
        record = json.loads(anchor.read_text(encoding="utf-8"))
        if record.get("schema") != 2 or record.get("racine") != str(state.resolve()):
            raise ValueError("ancre différente ; aucun nouveau compteur autorisé")
        return
    historical = [p for p in state.rglob("*") if p.is_file() and p.name not in ("collection.lock", "transition.lock")]
    if historical and (not auteur.strip() or not motif.strip()):
        raise ValueError("état historique sans ancre ; rattachement humain audité requis, aucun reset")
    if historical:
        etude_v2.reservations(state)  # un budget illisible n'est jamais rattaché comme vide
        Journal(state / "rattachements.jsonl").ajouter({"schema": 2, "auteur_humain": auteur,
            "motif": motif, "horodatage": etude_v2.maintenant(), "racine": str(state.resolve())})
    etude_v2.atomique(anchor, {"schema": 2, "racine": str(state.resolve()), "cree_utc": etude_v2.maintenant()})


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
