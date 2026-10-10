"""Une seule politique de secrets pour les transports, traces et journaux."""
from __future__ import annotations

import json
import os


def valeurs_secretes(supplement: str | None = None) -> tuple[str, ...]:
    """Inclure aussi les identifiants d'accès des API juridiques."""
    connus = {"LEGIFRANCE_CLIENT_ID", "LEGIFRANCE_CLIENT_SECRET", "JUDILIBRE_KEY_ID", "PISTE_KEY_ID",
              "CLAUDE_CODE_OAUTH_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
              "GITHUB_TOKEN", "GH_TOKEN", "MCP_ACCESS_TOKEN", "MCP_TOKEN", "AUTH0_CLIENT_SECRET"}
    values = {v for k, v in os.environ.items() if len(v) >= 8 and (
        k.upper() in connus or k.upper() == "GEMINI_API_KEY" or k.upper().startswith("GEMINI_API_KEY_"))}
    if isinstance(supplement, str) and len(supplement) >= 8:
        values.add(supplement)
    return tuple(sorted(values, key=len, reverse=True))


def expurger(texte: str) -> str:
    """Nettoyer les textes avant persistance, y compris les JSON échappés."""
    for value in valeurs_secretes():
        for forme in formes(value):
            texte = texte.replace(forme, "[SECRET_EXPURGE]")
    return texte


def formes(value: str) -> tuple[str, ...]:
    """Couvrir aussi les flux JSON imbriqués dans un autre journal JSON."""
    values = {value}
    for _ in range(4):
        values.update(json.dumps(v, ensure_ascii=a)[1:-1] for v in tuple(values) for a in (False, True))
    return tuple(sorted(values, key=len, reverse=True))


def verifier(valeur, supplement: str | None = None) -> None:
    """Bloquer tout objet contenant un secret connu avant transfert."""
    texte = json.dumps(valeur, ensure_ascii=False)
    if any(f in texte for s in valeurs_secretes(supplement) for f in formes(s)):
        raise ValueError("secret détecté : contenu non transmis et non journalisé")
