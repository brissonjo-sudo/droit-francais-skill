"""Empreinte des interpréteurs et CLI réellement utilisés, sans secret."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def executable(path: str) -> dict:
    """Résoudre un chemin puis figer ses octets ; aucun alias système implicite."""
    found = shutil.which(path)
    if not found:
        raise ValueError("exécutable introuvable")
    actual = Path(found).resolve()
    if not actual.is_file():
        raise ValueError("exécutable non régulier")
    return {"path": str(actual), "sha256": hashlib.sha256(actual.read_bytes()).hexdigest()}


def python_runtime(path: str) -> dict:
    """Figer toutes les versions de distributions du Python choisi pour MCP."""
    result = subprocess.run([path, "-c", (
        "import sys,json,importlib.metadata as m;"
        "print(json.dumps({'version':sys.version,'executable':sys.executable,"
        "'distributions':sorted((d.metadata['Name'].lower(),d.version) for d in m.distributions())}))"
    )], capture_output=True, encoding="utf-8", timeout=15, shell=False)
    if result.returncode:
        raise ValueError("environnement Python non inspectable")
    try:
        info = json.loads(result.stdout)
    except ValueError as exc:
        raise ValueError("empreinte Python invalide") from exc
    return {"lanceur": executable(path), "interpreteur": executable(info["executable"]), **info}


def relever(config: dict) -> dict:
    """Le moteur REST n'a pas de CLI ; son code et le SDK sont figés autrement."""
    clients = {}
    for f in config["familles"]:
        if f["moteur"] == "cli-native":
            clients[f["nom"]] = executable(f["executable"])
    return {"python_mcp": python_runtime(config.get("python_mcp", sys.executable)),
            "python_harnais": python_runtime(sys.executable), "clients": clients}
