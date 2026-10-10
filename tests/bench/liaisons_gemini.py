"""Liaisons privées clé/numéro de projet ; aucune valeur ne quitte le poste."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import uuid
import secrets
from pathlib import Path

from bench.budget_gemini import ArretBudget
from bench.verrous_gemini import verrou
from bench.identite_gemini import numero_projet, modele_exact


def lier(cle: str, numero: str, modele: str, limites: dict, racine: Path) -> dict:
    """Même clé sous un autre numéro ou baisse de quota : examen explicite."""
    numero = numero_projet(numero)
    modele_exact(modele)
    racine.mkdir(parents=True, exist_ok=True)
    lock, path = racine / "profils.lock", racine / "liaisons-gemini.json"
    with verrou(racine, lock):
        return _lier(cle, numero, modele, limites, path)


def _lier(cle: str, numero: str, modele: str, limites: dict, path: Path) -> dict:
    try:
        existing = path.exists()
        data = json.loads(path.read_bytes()) if existing else {"schema": 3, "cles": {}, "limites": {}}
        if (not isinstance(data, dict) or set(data) != {"schema", "cles", "limites"} or data["schema"] != 3
                or not isinstance(data["cles"], dict) or not isinstance(data["limites"], dict)):
            raise ValueError()
        salt_path = path.with_name("liaisons-gemini.hmac")
        if not salt_path.exists():
            if existing:
                raise ValueError("sel perdu : aucune recréation")
            fd = os.open(salt_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(secrets.token_bytes(32))
                handle.flush()
                os.fsync(handle.fileno())
        salt = salt_path.read_bytes()
        if len(salt) != 32 or (os.name != "nt" and salt_path.stat().st_mode & 0o077):
            raise ValueError()
        fingerprint = hmac.new(salt, cle.encode(), hashlib.sha256).hexdigest()
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
            fd = os.open(temp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(data, handle, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)
        return baseline
    except (ValueError, TypeError, OSError):
        raise ArretBudget("liaisons privées invalides : examen manuel", "profil") from None
