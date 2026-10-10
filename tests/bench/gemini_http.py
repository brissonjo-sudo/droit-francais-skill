"""Transport Gemini REST borné, sans SDK, redirect, retry ni endpoint variable."""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request

from bench.catalogue_gemini import SansRedirection


class ErreurGemini(RuntimeError):
    """Diagnostic assaini : aucun corps, secret, en-tête ou URL d'erreur."""

    def __init__(self, statut: int | None = None):
        self.statut = statut
        super().__init__(f"Gemini HTTP {statut}" if statut else "Transport ou réponse Gemini invalide")


def modele_exact(modele: str) -> None:
    """Exiger un identifiant Flash explicite avant de construire une URL."""
    if (not isinstance(modele, str)
            or not re.fullmatch(r"gemini-[0-9][a-z0-9.-]{0,90}flash[a-z0-9.-]{0,30}", modele)
            or "latest" in modele):
        raise ValueError("identifiant Flash exact requis")


def appeler(cle: str, modele: str, methode: str, charge: dict, *, echeance: float | None = None) -> dict:
    """Un seul POST HTTPS, délai borné, taille bornée et erreur sans contenu."""
    modele_exact(modele)
    if methode not in ("countTokens", "generateContent"):
        raise ValueError("méthode Gemini non autorisée")
    if not cle or len(cle) < 8 or "\n" in cle or "\r" in cle:
        raise ValueError("clé absente ou invalide ; valeur non affichée")
    encoded = json.dumps(charge, ensure_ascii=False).encode("utf-8")
    if len(encoded) > 2_000_000 or cle.encode() in encoded:
        raise ValueError("charge trop volumineuse ou contenant le secret")
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{modele}:{methode}",
        data=encoded, headers={"x-goog-api-key": cle, "Content-Type": "application/json"}, method="POST")
    remaining = min(30, echeance - time.monotonic()) if echeance is not None else 30
    if remaining <= 0:
        raise ErreurGemini()
    try:
        with urllib.request.build_opener(SansRedirection()).open(request, timeout=remaining) as response:
            chunks, size = [], 0
            while True:
                if echeance is not None and time.monotonic() >= echeance:
                    raise ValueError()
                # read1 évite une succession illimitée de lectures internes.
                chunk = (response.read1 if hasattr(response, "read1") else response.read)(65536)
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                if size > 2_000_000:
                    raise ValueError()
            raw = b"".join(chunks)
        if len(raw) > 2_000_000 or cle.encode() in raw:
            raise ValueError()
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise ValueError()
        return result
    except urllib.error.HTTPError as exc:
        raise ErreurGemini(exc.code) from None
    except (ValueError, TypeError, UnicodeError, OSError):
        raise ErreurGemini() from None


def compter(cle: str, modele: str, requete: dict, *, echeance: float | None = None) -> int:
    """Compter une requête complète, instructions et déclarations incluses."""
    data = appeler(cle, modele, "countTokens", {
        "generateContentRequest": {**requete, "model": f"models/{modele}"}}, echeance=echeance)
    value = data.get("totalTokens")
    if type(value) is not int or value <= 0:
        raise ErreurGemini()
    return value
