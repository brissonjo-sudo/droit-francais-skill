"""Prototype REST Gemini contrôlé par requête ; gel de collecte toujours fermé."""
from __future__ import annotations

import asyncio
import copy
import json
import math
import os
import time
from pathlib import Path

from bench import gemini_http, native, profils_gemini, quotas_gemini
from bench.budget_gemini import ArretBudget, Budget
from bench.flux import Appel, PREFIXE_MCP, Trace


def verifier_secrets(client, valeur) -> None:
    """Arrêter avant journalisation ou transmission si un secret connu apparaît."""
    secrets = [v for k, v in os.environ.items() if len(v) >= 8 and (
        any(m in k.upper() for m in ("TOKEN", "SECRET", "API_KEY"))
        or k in ("LEGIFRANCE_CLIENT_ID", "JUDILIBRE_KEY_ID", "PISTE_KEY_ID"))]
    key = getattr(client, "_cle", None)
    if isinstance(key, str) and len(key) >= 8:
        secrets.append(key)
    texte = json.dumps(valeur, ensure_ascii=False)
    if any(secret in texte for secret in secrets):
        raise ValueError("secret détecté : contenu non transmis et non journalisé")


class Client:
    """Profil fixe ; chaque tokenizer et génération est réservé et compté."""

    def __init__(self, cle: str, modele: str, budget: Budget, garde=None):
        self._cle, self.modele, self.budget = cle, modele, budget
        self.requetes = 0
        self.garde = garde or (lambda: None)

    def generer(self, charge: dict) -> tuple[dict, int]:
        """Mesure préalable puis génération ; aucun repli, retry ou remboursement."""
        # countTokens est compté comme une requête RPM/RPD par prudence.
        # Son coût éventuel en TPM ou quota propre reste à vérifier : ces
        # compteurs ne constituent donc pas encore une qualification fournisseur.
        verifier_secrets(self, charge)
        self.garde()
        with self.budget.tentative(0, "countTokens"):
            self.requetes += 1
            try:
                tokens = gemini_http.compter(self._cle, self.modele, charge)
            except gemini_http.ErreurGemini as exc:
                if exc.statut == 429:
                    self.budget.bloquer(429)
                raise
        reserve = math.ceil(tokens * 1.10) + 32
        self.garde()
        with self.budget.tentative(reserve, "generateContent") as at:
            self.requetes += 1
            try:
                response = gemini_http.appeler(self._cle, self.modele, "generateContent", charge)
            except gemini_http.ErreurGemini as exc:
                if exc.statut == 429:
                    self.budget.bloquer(429)
                raise
            usage = response.get("usageMetadata", {})
            try:
                self.budget.usage(at, reserve, usage.get("promptTokenCount") if isinstance(usage, dict) else None)
            except ArretBudget:
                response["budget_arret"] = True
        return response, tokens


def preparer_client(registre: Path, profil: str, state: Path) -> Client:
    """Aucune clé chargée avant vérification du registre et des relevés privés."""
    check = profils_gemini.verifier(registre, profil)
    if check["statut"] != "profils_declares_coherents" or not check["selection_explicitement_coherente"]:
        raise ValueError("profils ou quotas incomplets : aucun appel")
    path = quotas_gemini.chemin_local(registre)
    rows = json.loads(path.read_text(encoding="utf-8"))["profils"]
    selected = next(r for r in rows if r["profil"] == profil)
    evidence = quotas_gemini.chemin_local(path.parent / selected["releve"])
    declared = json.loads(evidence.read_text(encoding="utf-8"))
    key = os.environ.get(selected["cle_env"], "")
    if not key or len(key) < 8 or "\n" in key or "\r" in key:
        raise ValueError("clé du profil absente ou invalide ; aucun appel")
    snapshots = {p: p.read_bytes() for p in (path, evidence)}

    def garde():
        if (any(p.read_bytes() != original for p, original in snapshots.items())
                or profils_gemini.verifier(path, profil)["statut"] != "profils_declares_coherents"):
            raise ValueError("profil modifié ou relevé périmé : arrêt")

    return Client(key, declared["modele"], Budget(state, declared["projet_ref"],
                                                declared["modele"], declared["limites"]), garde)


async def boucle(client: Client, *, prompt: str, bras: str, plafond: int,
                 instructions: str, outils: list[dict], appeler_outil=None,
                 timeout_s: int = 300, effort: str = "high"):
    """Boucle de fonction MCP uniquement ; signatures conservées sans modification."""
    from bench.agents import Execution, _classer
    from mcp_server.catalog import EXPECTED_TOOLS
    if bras not in ("A", "B", "C", "D") or effort not in ("low", "medium", "high"):
        raise ValueError("bras ou thinking explicite invalide")
    with_tools = bras in ("C", "D")
    names = {t["name"] for t in outils}
    if (with_tools and (names != EXPECTED_TOOLS or len(outils) != len(EXPECTED_TOOLS) or appeler_outil is None)
            or not with_tools and (outils or appeler_outil is not None)):
        raise ValueError("catalogue ou isolation des outils invalide")
    if type(plafond) is not int or not 0 <= plafond <= 12:
        raise ValueError("plafond d'outils entre zéro et douze requis")
    charge = {"systemInstruction": {"parts": [{"text": instructions}]},
              "contents": [{"role": "user", "parts": [{"text": prompt}]}],
              "generationConfig": {"maxOutputTokens": 16384, "thinkingConfig": {"thinkingLevel": effort}}}
    if with_tools:
        charge["tools"] = [{"functionDeclarations": outils}]
    trace, events = Trace(), []
    trace.outils_disponibles = [PREFIXE_MCP + n for n in sorted(names)]
    trace.mcp_connecte = with_tools
    start = time.monotonic()
    try:
        for turn in range(plafond + 2):
            if time.monotonic() - start >= timeout_s:
                raise ValueError("temps de cas atteint")
            response, counted = await asyncio.to_thread(client.generer, copy.deepcopy(charge))
            verifier_secrets(client, response)
            trace.num_turns += 1
            observed = response.get("modelVersion")
            trace.modele = observed if isinstance(observed, str) else ""
            candidates = response.get("candidates", [])
            if not isinstance(candidates, list) or len(candidates) != 1:
                raise ValueError("candidat absent ou multiple")
            candidate = candidates[0]
            if not isinstance(candidate, dict):
                raise ValueError("candidat invalide")
            content = candidate.get("content", {})
            if not isinstance(content, dict):
                raise ValueError("contenu Gemini invalide")
            parts = content.get("parts", [])
            if (not isinstance(content, dict) or content.get("role") != "model"
                    or not isinstance(parts, list) or not parts or any(not isinstance(p, dict) for p in parts)):
                raise ValueError("contenu Gemini invalide")
            text = "".join(p["text"] for p in parts if isinstance(p.get("text"), str) and not p.get("thought"))
            calls = [p["functionCall"] for p in parts if "functionCall" in p]
            if text:
                trace.texte_final += text
            events.append({"tour": turn + 1, "moteur": "gemini-rest-v1", "modele": trace.modele,
                           "tokens_countTokens": counted, "usage": response.get("usageMetadata", {}),
                           "appels": calls, "texte": text})
            trace.usage = {"requêtes_HTTP": client.requetes, "tours": events}
            if response.get("budget_arret"):
                raise ValueError("budget arrêté après réponse")
            if trace.modele != client.modele:
                raise ValueError("modèle effectif absent ou différent : arrêt sans repli")
            if candidate.get("finishReason") != "STOP":
                raise ValueError("réponse bloquée ou tronquée")
            if not calls:
                if not text:
                    raise ValueError("réponse visible absente")
                execution = Execution(trace, json.dumps(events, ensure_ascii=False), 0)
                _classer(execution, bras)
                return execution
            if not with_tools or len(trace.appels) + len(calls) > plafond:
                raise ValueError("outil interdit ou plafond atteint")
            # Valider tous les appels avant d'en exécuter un seul.
            for call in calls:
                if (not isinstance(call, dict) or call.get("name") not in names
                        or not isinstance(call.get("args", {}), dict)):
                    raise ValueError("fonction hors catalogue ou arguments invalides")
            charge["contents"].append(copy.deepcopy(content))
            answers = []
            for call in calls:
                restant = timeout_s - (time.monotonic() - start)
                if restant <= 0:
                    raise ValueError("temps de cas atteint")
                output, error = await asyncio.wait_for(
                    appeler_outil(call["name"], call.get("args", {})), timeout=min(30, restant))
                verifier_secrets(client, output)
                if not isinstance(output, str) or type(error) is not bool:
                    raise ValueError("résultat MCP invalide")
                trace.appels.append(Appel(len(trace.appels), PREFIXE_MCP + call["name"],
                                          call.get("args", {}), output, error))
                if error:
                    raise ValueError("erreur MCP : arrêt du cas sans reprise")
                answer = {"name": call["name"], "response": {"result": output}}
                if "id" in call:
                    answer["id"] = call["id"]
                answers.append({"functionResponse": answer})
            charge["contents"].append({"role": "user", "parts": answers})
        raise ValueError("plafond de tours atteint")
    except Exception:
        # Aucun message d'exception provenant du serveur ou du transport.
        trace.is_error = True
        return Execution(trace, json.dumps(events, ensure_ascii=False), 2, statut="infra_error",
                         motif_infra="arrêt REST, budget, modèle, réponse ou outil ; examen requis")
    finally:
        trace.duration_ms = int((time.monotonic() - start) * 1000)


async def executer_mcp(client: Client, *, prompt: str, bras: str, plafond: int,
                       options):
    """Assainir aussi les erreurs d'ouverture et de fermeture du transport MCP."""
    from bench.agents import Execution
    try:
        return await _executer_mcp(client, prompt=prompt, bras=bras, plafond=plafond, options=options)
    except Exception:
        return Execution(Trace(is_error=True), "", 2, statut="infra_error",
                         motif_infra="initialisation ou fermeture REST/MCP impossible ; examen requis")


async def _executer_mcp(client: Client, *, prompt: str, bras: str, plafond: int,
                        options):
    """Ouvrir seulement le MCP stdio du candidat ; aucun serveur distant."""
    systeme = native.instructions(bras, options.fournir_references, options.methode_experimentale)
    if bras in ("A", "B"):
        return await boucle(client, prompt=prompt, bras=bras, plafond=plafond,
                            instructions=systeme, outils=[], timeout_s=options.timeout_s, effort=options.effort)
    if not options.mcp_local:
        raise ValueError("MCP local du candidat requis")
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from bench.agents import RACINE
    env = {**native.environnement_abonnement(), "MCP_ENV": "test", "MCP_AUTH_MODE": "disabled"}
    params = StdioServerParameters(command=options.interpreteur_python or "python",
                                  args=[str(RACINE / "mcp_server/server.py")], cwd=str(RACINE), env=env)
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await session.list_tools()
            declarations = [{"name": t.name, "description": t.description or "",
                             "parametersJsonSchema": t.input_schema} for t in tools.tools]

            async def call(name, args):
                result = await session.call_tool(name, args)
                text = "\n".join(block.text for block in result.content if getattr(block, "type", "") == "text")
                return text, bool(result.isError)

            return await boucle(client, prompt=prompt, bras=bras, plafond=plafond, instructions=systeme,
                                outils=declarations, appeler_outil=call, timeout_s=options.timeout_s,
                                effort=options.effort)
