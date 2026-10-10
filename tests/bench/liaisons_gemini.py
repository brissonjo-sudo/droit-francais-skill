"""Liaisons privées clé/numéro de projet ; aucune valeur ne quitte le poste."""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path

from bench.budget_gemini import ArretBudget
from bench.verrous_gemini import verrou


def lier(cle: str, numero: str, modele: str, limites: dict, racine: Path) -> dict:
    """Même clé sous un autre numéro ou baisse de quota : examen explicite."""
    racine.mkdir(parents=True, exist_ok=True)
    lock, path = racine / "profils.lock", racine / "liaisons-gemini.json"
    with verrou(racine, lock):
        return _lier(cle, numero, modele, limites, path)


def _lier(cle: str, numero: str, modele: str, limites: dict, path: Path) -> dict:
    try:
        data = json.loads(path.read_bytes()) if path.exists() else {"schema": 2, "cles": {}, "limites": {}}
        if (not isinstance(data, dict) or set(data) != {"schema", "cles", "limites"} or data["schema"] != 2
                or not isinstance(data["cles"], dict) or not isinstance(data["limites"], dict)):
            raise ValueError()
        fingerprint = hashlib.sha256(cle.encode()).hexdigest()
        if fingerprint in data["cles"] and data["cles"][fingerprint] != numero:
            raise ArretBudget("clé déjà liée à un autre numéro : examen explicite", "profil")
        identity = hashlib.sha256(f"{numero}\n{modele}".encode()).hexdigest()
        baseline = data["limites"].get(identity, limites)
        if (not isinstance(baseline, dict) or set(baseline) != set(limites)
                or any(type(v) is not int or v <= 0 for v in baseline.values())):
            raise ValueError()
        if any(limites[k] < baseline[k] for k in limites):
            raise ArretBudget("quota inférieur au plafond initial : arrêt pour examen", "profil")
        data["cles"][fingerprint] = numero
        data["limites"][identity] = baseline
        temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
        try:
            with temp.open("x", encoding="utf-8", newline="\n") as handle:
                json.dump(data, handle, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)
        return baseline
    except (ValueError, TypeError, OSError):
        raise ArretBudget("liaisons privées invalides : examen manuel", "profil") from None
