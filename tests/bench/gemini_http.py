"""Transport REST asynchrone : échéance totale, sans retry, proxy ou redirect."""
from __future__ import annotations

import asyncio
import json
import time

import httpx

from bench.identite_gemini import modele_exact

HTTP_TOTAL_S = 120
MAX_BYTES = 2_000_000
ORIGINE = "https://generativelanguage.googleapis.com/v1beta"


class ErreurGemini(RuntimeError):
    """Diagnostic fermé, sans corps, secret, en-tête ou URL d'erreur."""

    def __init__(self, statut: int | None = None, categorie: str = "transport"):
        self.statut = statut
        self.categorie = "quota_429" if statut == 429 else categorie
        super().__init__(f"Gemini HTTP {statut}" if statut else "Transport ou réponse Gemini invalide")


class Transport:
    """Un client par cas/sonde ; les réservations sont effectuées par l'appelant."""

    def __init__(self, *, client: httpx.AsyncClient | None = None):
        self.client = client or httpx.AsyncClient(
            trust_env=False, follow_redirects=False,
            transport=httpx.AsyncHTTPTransport(retries=0),
            timeout=httpx.Timeout(120, connect=10, write=30, pool=5))

    async def fermer(self) -> None:
        await self.client.aclose()

    async def appeler(self, cle: str, modele: str | None, methode: str, charge: dict | None,
                      *, echeance: float) -> dict:
        """Une opération et sa lecture entière sous une seule échéance absolue."""
        if methode not in ("countTokens", "generateContent", "models.list"):
            raise ValueError("méthode Gemini non autorisée")
        if not cle or len(cle) < 8 or "\n" in cle or "\r" in cle:
            raise ValueError("clé absente ou invalide ; valeur non affichée")
        if methode == "models.list":
            url, method, encoded = ORIGINE + "/models?pageSize=1000", "GET", None
        else:
            modele_exact(modele)
            url, method = f"{ORIGINE}/models/{modele}:{methode}", "POST"
            encoded = json.dumps(charge, ensure_ascii=False).encode("utf-8")
            if len(encoded) > MAX_BYTES or cle.encode() in encoded:
                raise ValueError("charge trop volumineuse ou contenant le secret")
        fin = min(echeance, time.monotonic() + HTTP_TOTAL_S)
        if fin <= time.monotonic():
            raise ErreurGemini(categorie="delai")
        try:
            async with asyncio.timeout_at(fin):
                async with self.client.stream(method, url, content=encoded,
                        headers={"x-goog-api-key": cle, "Content-Type": "application/json"}) as response:
                    if response.status_code != 200:
                        raise ErreurGemini(response.status_code)
                    chunks, size = [], 0
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        if time.monotonic() >= fin:
                            raise ErreurGemini(categorie="delai")
                        size += len(chunk)
                        if size > MAX_BYTES:
                            raise ErreurGemini()
                        chunks.append(chunk)
                    raw = b"".join(chunks)
                if cle.encode() in raw:
                    raise ErreurGemini(categorie="isolation")
                result = json.loads(raw)
                if not isinstance(result, dict):
                    raise ErreurGemini()
                if time.monotonic() >= fin:
                    raise ErreurGemini(categorie="delai")
                return result
        except (TimeoutError, httpx.TimeoutException):
            raise ErreurGemini(categorie="delai") from None
        except (httpx.HTTPError, ValueError, TypeError, UnicodeError):
            raise ErreurGemini() from None

    async def compter(self, cle: str, modele: str, requete: dict, *, echeance: float) -> int:
        data = await self.appeler(cle, modele, "countTokens", {
            "generateContentRequest": {**requete, "model": f"models/{modele}"}}, echeance=echeance)
        value = data.get("totalTokens")
        if type(value) is not int or value <= 0:
            raise ErreurGemini()
        return value
