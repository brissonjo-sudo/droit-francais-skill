"""Empreinte des interpréteurs et CLI réellement utilisés, sans secret."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


class ControleIndisponible(ValueError):
    """Sonde passagère indisponible, sans preuve d'une dérive de runtime."""


def executable(path: str) -> dict:
    """Résoudre un chemin puis figer ses octets ; aucun alias système implicite."""
    found = shutil.which(path)
    if not found:
        raise ValueError("exécutable introuvable")
    actual = Path(found).resolve()
    if not actual.is_file():
        raise ValueError("exécutable non régulier")
    return {"path": str(actual), "sha256": hashlib.sha256(actual.read_bytes()).hexdigest()}


def python_runtime(path: str, *, echeance_monotone: float | None = None) -> dict:
    """Figer toutes les versions de distributions du Python choisi pour MCP."""
    timeout = 15 if echeance_monotone is None else min(15, echeance_monotone - time.monotonic())
    if timeout <= 0:
        raise ControleIndisponible("échéance de contrôle runtime atteinte ; aucune dérive attestée")
    try:
        result = subprocess.run([path, "-c", (
            "import sys,json,importlib.metadata as m;"
            "print(json.dumps({'version':sys.version,'executable':sys.executable,"
            "'distributions':sorted((d.metadata['Name'].lower(),d.version) for d in m.distributions())}))"
        )], capture_output=True, encoding="utf-8", timeout=timeout, shell=False)
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise ControleIndisponible("sonde runtime indisponible ; réessayer sans invalidation") from exc
    if result.returncode:
        raise ValueError("environnement Python non inspectable")
    try:
        info = json.loads(result.stdout)
    except ValueError as exc:
        raise ValueError("empreinte Python invalide") from exc
    return {"lanceur": executable(path), "interpreteur": executable(info["executable"]), **info}


def relever(config: dict, *, echeance_monotone: float | None = None) -> dict:
    """Le moteur REST n'a pas de CLI ; son code et le SDK sont figés autrement."""
    clients = {}
    for f in config["familles"]:
        if f["moteur"] == "cli-native":
            clients[f["nom"]] = executable(f["executable"])
    return {"python_mcp": python_runtime(config.get("python_mcp", sys.executable), echeance_monotone=echeance_monotone),
            "python_harnais": python_runtime(sys.executable, echeance_monotone=echeance_monotone), "clients": clients,
            "timeout_s": config.get("timeout_s", 300)}
