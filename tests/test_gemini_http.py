"""Transport asynchrone exercé sans Google, réponse entière sous échéance."""
import asyncio
import json
import sys
import time
import unittest
from pathlib import Path
from unittest import mock
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import gemini_http


class GeminiHttpTests(unittest.IsolatedAsyncioTestCase):
    def transport(self, handler):
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False, trust_env=False)
        t = gemini_http.Transport(client=client)
        self.addAsyncCleanup(t.fermer)
        return t

    async def test_count_charge_complete_secret_uniquement_entete(self):
        requests = []
        async def handler(req):
            requests.append(req)
            return httpx.Response(200, json={"totalTokens": 123})
        t = self.transport(handler)
        data = {"systemInstruction": {"parts": [{"text": "méthode"}]}, "contents": []}
        self.assertEqual(123, await t.compter("secret-test", "gemini-3.8-flash", data, echeance=time.monotonic()+1))
        self.assertEqual(1, len(requests))
        req = requests[0]
        self.assertEqual("POST", req.method)
        self.assertNotIn("secret-test", str(req.url)+req.content.decode())
        self.assertEqual("secret-test", req.headers["x-goog-api-key"])
        self.assertEqual(data["systemInstruction"], json.loads(req.content)["generateContentRequest"]["systemInstruction"])

    async def test_alias_methodes_deadline_refuses_avant_transport(self):
        handler = mock.AsyncMock()
        t = self.transport(handler)
        for model in ("auto", "gemini-3.8-flash-latest", "gemini-3.8-flash/../evil", "gemini-3.1-pro"):
            with self.assertRaises(ValueError):
                await t.appeler("secret-test", model, "countTokens", {}, echeance=time.monotonic()+1)
        with self.assertRaises(ValueError):
            await t.appeler("secret-test", "gemini-3.8-flash", "autre", {}, echeance=time.monotonic()+1)
        with self.assertRaises(gemini_http.ErreurGemini) as error:
            await t.appeler("secret-test", "gemini-3.8-flash", "countTokens", {}, echeance=0)
        self.assertEqual("delai", error.exception.categorie)
        handler.assert_not_called()

    async def test_429_et_redirect_ne_font_qu_un_envoi(self):
        for status in (429, 302, 307):
            requests = []
            async def handler(req):
                requests.append(req)
                return httpx.Response(status, text="secret-test", headers={"Location": "https://ailleurs.invalid"})
            t = self.transport(handler)
            with self.assertRaises(gemini_http.ErreurGemini) as error:
                await t.compter("secret-test", "gemini-3.8-flash", {}, echeance=time.monotonic()+1)
            self.assertEqual(status, error.exception.statut)
            self.assertNotIn("secret-test", str(error.exception))
            self.assertEqual(1, len(requests))

    async def test_secret_charge_et_reponse_refuse(self):
        handler = mock.AsyncMock(return_value=httpx.Response(200, json={"text": "secret-test"}))
        t = self.transport(handler)
        with self.assertRaises(ValueError):
            await t.appeler("secret-test", "gemini-3.8-flash", "countTokens", {"text": "secret-test"}, echeance=time.monotonic()+1)
        handler.assert_not_called()
        with self.assertRaises(gemini_http.ErreurGemini) as error:
            await t.appeler("secret-test", "gemini-3.8-flash", "countTokens", {}, echeance=time.monotonic()+1)
        self.assertEqual("isolation", error.exception.categorie)

    async def test_corps_lent_regulier_est_annule_et_ferme(self):
        class Lent(httpx.AsyncByteStream):
            ferme = False
            async def __aiter__(self):
                for _ in range(100):
                    await asyncio.sleep(.01)
                    yield b" " * 65536
            async def aclose(self):
                self.ferme = True
        stream = Lent()
        t = self.transport(lambda req: httpx.Response(200, stream=stream))
        debut = time.monotonic()
        with mock.patch.object(gemini_http, "HTTP_TOTAL_S", .04):
            with self.assertRaises(gemini_http.ErreurGemini) as error:
                await t.appeler("secret-test", "gemini-3.8-flash", "countTokens", {}, echeance=debut+2)
        self.assertEqual("delai", error.exception.categorie)
        self.assertLess(time.monotonic()-debut, .3)
        self.assertTrue(stream.ferme)

    async def test_reponse_trop_grande_et_compteur_invalide(self):
        t = self.transport(lambda req: httpx.Response(200, content=b"x"*(gemini_http.MAX_BYTES+1)))
        with self.assertRaises(gemini_http.ErreurGemini):
            await t.compter("secret-test", "gemini-3.8-flash", {}, echeance=time.monotonic()+1)
        for value in (None, True, 0, "10", -1):
            t = self.transport(lambda req, value=value: httpx.Response(200, json={"totalTokens": value}))
            with self.assertRaises(gemini_http.ErreurGemini):
                await t.compter("secret-test", "gemini-3.8-flash", {}, echeance=time.monotonic()+1)
