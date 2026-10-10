"""Prototype REST Gemini contrôlé par requête ; gel de collecte toujours fermé."""
from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
import copy
import hashlib
import json
import math
import os
import time
from pathlib import Path

from bench import gemini_http, native, profils_gemini, quotas_gemini
from bench.contexte import ContexteExecution, etat_canonique
from bench.liaisons_gemini import lier
from bench.budget_gemini import ArretBudget, Budget
from bench.flux import Appel, PREFIXE_MCP, Trace
from bench.confidentialite import verifier


def verifier_secrets(client, valeur) -> None:
    """Arrêter avant journalisation ou transmission si un secret connu apparaît."""
    key = getattr(client, "_cle", None)
    try:
        verifier(valeur, key if isinstance(key, str) else None)
    except ValueError:
        raise ArretBudget("secret connu : transfert ou journalisation interdits", "isolation") from None


class Client:
    """Profil fixe ; chaque tokenizer et génération est réservé et compté."""

    def __init__(self, cle: str, modele: str, budget: Budget, garde=None, transport=None):
        self._cle, self.modele, self.budget = cle, modele, budget
        self.requetes = 0
        self.garde = garde or (lambda: None)
        self.transport = transport or gemini_http.Transport()
        self.contexte: ContexteExecution | None = None

    async def generer(self, charge: dict, *, echeance: float) -> tuple[dict, int]:
        """Mesure préalable puis génération ; aucun repli, retry ou remboursement."""
        # countTokens est compté comme une requête RPM/RPD par prudence.
        # Son coût éventuel en TPM ou quota propre reste à vérifier : ces
        # compteurs ne constituent donc pas encore une qualification fournisseur.
        verifier_secrets(self, charge)
        self.avant(echeance)
        if self.contexte is None:
            raise ArretBudget("contexte réservé par le lanceur requis", "profil")
        from bench.etude_v2 import verifier_contexte
        try:
            verifier_contexte(self.contexte)
        except (ValueError, KeyError, OSError):
            raise ArretBudget("réservation durable absente ou clôturée", "profil") from None
        with self.budget.tentative(0, "countTokens", attempt_id=self.contexte.attempt_id):
            self.requetes += 1
            try:
                tokens = await self.transport.compter(self._cle, self.modele, charge, echeance=echeance)
            except gemini_http.ErreurGemini as exc:
                if exc.statut == 429:
                    self.budget.bloquer(429)
                raise
        reserve = math.ceil(tokens * 1.10) + 32
        self.avant(echeance)
        with self.budget.tentative(reserve, "generateContent", attempt_id=self.contexte.attempt_id) as at:
            self.requetes += 1
            try:
                response = await self.transport.appeler(self._cle, self.modele, "generateContent", charge, echeance=echeance)
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

    def avant(self, echeance: float) -> None:
        self.budget.verifier_arret()
        self.garde()
        if time.monotonic() >= echeance:
            raise gemini_http.ErreurGemini(categorie="delai")


def preparer_client(registre: Path, profil: str) -> Client:
    """Aucune clé chargée avant vérification du registre et des relevés privés."""
    checked = profils_gemini.charger(registre, profil)
    selected = checked["selection"]
    declared = selected["declare"]
    budget = Budget(selected["numero"], declared["modele"], declared["limites"])
    budget.verifier_arret()
    key = os.environ.get(selected["row"]["cle_env"], "")
    if not key or len(key) < 8 or "\n" in key or "\r" in key:
        raise ValueError("clé du profil absente ou invalide ; aucun appel")
    snapshots = checked["snapshots"]
    baseline = lier(key, selected["numero"], declared["modele"], declared["limites"], budget.racine)
    budget = Budget(selected["numero"], declared["modele"], baseline)

    def garde():
        try:
            if (any(p.read_bytes() != original for p, original in snapshots.items())
                    or profils_gemini.verifier(checked["path"], profil)["statut"] != "profils_declares_coherents"):
                raise ValueError()
        except (OSError, ValueError):
            raise ArretBudget("profil modifié ou relevé périmé : arrêt", "profil") from None

    return Client(key, declared["modele"], budget, garde)


async def boucle(client: Client, *, prompt: str, bras: str, plafond: int,
                 instructions: str, outils: list[dict], appeler_outil=None,
                 echeance: float, effort: str = "high"):
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
            if time.monotonic() >= echeance:
                raise gemini_http.ErreurGemini(categorie="delai")
            response, counted = await client.generer(copy.deepcopy(charge), echeance=echeance)
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
            events.append({"tour": turn + 1, "moteur": "gemini-rest-v2", "modele": trace.modele,
                           "tokens_countTokens": counted, "usage": response.get("usageMetadata", {}),
                           "appels": calls, "texte": text})
            trace.usage = {"requêtes_HTTP": client.requetes, "tours": events,
                           "catalogue_sha256": hashlib.sha256(json.dumps(outils, sort_keys=True).encode()).hexdigest()}
            if response.get("budget_arret"):
                raise ArretBudget("budget arrêté après réponse", "budget")
            if trace.modele != client.modele:
                raise ArretBudget("modèle effectif absent ou différent : arrêt sans repli", "modele")
            if candidate.get("finishReason") != "STOP":
                raise ValueError("réponse bloquée ou tronquée")
            if not calls:
                if not text:
                    raise ValueError("réponse visible absente")
                execution = Execution(trace, json.dumps(events, ensure_ascii=False), 0)
                _classer(execution, bras)
                if execution.statut != "ok":
                    execution.categorie_infra = "transport"
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
                restant = echeance - time.monotonic()
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
    except (Exception, asyncio.CancelledError) as exc:
        # Aucun message d'exception provenant du serveur ou du transport.
        trace.is_error = True
        categorie = getattr(exc, "categorie", "delai" if isinstance(exc, (TimeoutError, asyncio.CancelledError)) else "outil")
        return Execution(trace, json.dumps(events, ensure_ascii=False), 2, statut="infra_error",
                         motif_infra="arrêt REST ; examen requis", categorie_infra=categorie)
    finally:
        trace.duration_ms = int((time.monotonic() - start) * 1000)


async def executer_mcp(client: Client, *, prompt: str, bras: str, plafond: int,
                       options):
    """Assainir aussi les erreurs d'ouverture et de fermeture du transport MCP."""
    from bench.agents import Execution
    start = time.monotonic()
    result = None
    try:
        ctx = options.contexte
        if (not isinstance(ctx, ContexteExecution) or ctx.moteur != "gemini-rest-v2"
                or ctx.modele != client.modele or not ctx.attempt_id or not ctx.identite
                or not ctx.reservation or ctx.racine_etat.resolve() != client.budget.racine):
            raise ArretBudget("contexte du lanceur absent ou incohérent", "profil")
        if options.effort not in ("low", "medium", "high"):
            raise ArretBudget("effort REST explicite requis", "profil")
        client.contexte = ctx
        client.avant(ctx.echeance_monotone)
        from bench.etude_v2 import verifier_contexte
        try:
            verifier_contexte(ctx)
        except ValueError as exc:
            raise ArretBudget("contexte sans réservation durable active", "profil") from exc
        async with asyncio.timeout_at(ctx.echeance_monotone):
            result = await _executer_mcp(client, prompt=prompt, bras=bras, plafond=plafond, options=options)
    except (Exception, asyncio.CancelledError) as exc:
        categorie = getattr(exc, "categorie", "delai" if isinstance(exc, (TimeoutError, asyncio.CancelledError)) else "outil")
        result = Execution(Trace(is_error=True), "", 2, statut="infra_error",
                         motif_infra="initialisation ou fermeture REST/MCP impossible ; examen requis",
                         categorie_infra=categorie)
    finally:
        try:
            fin_nettoyage = getattr(client, "fin_nettoyage", None)
            if type(fin_nettoyage) not in (int, float):
                fin_nettoyage = time.monotonic()+5
            async with asyncio.timeout_at(fin_nettoyage):
                await client.transport.fermer()
        except (Exception, asyncio.CancelledError):
            if result is None:
                result = Execution(Trace(is_error=True), "", 2)
            result.statut, result.categorie_infra = "infra_error", "transport"
            result.motif_infra = "fermeture du transport impossible ; examen requis"
    result.trace.duration_ms = int((time.monotonic() - start) * 1000)
    return result


async def _executer_mcp(client: Client, *, prompt: str, bras: str, plafond: int,
                        options):
    """Ouvrir seulement le MCP stdio du candidat ; aucun serveur distant."""
    systeme = native.instructions(bras, options.fournir_references, options.methode_experimentale)
    echeance = options.contexte.echeance_monotone
    if bras in ("A", "B"):
        return await boucle(client, prompt=prompt, bras=bras, plafond=plafond,
                            instructions=systeme, outils=[], echeance=echeance, effort=options.effort)
    if not options.mcp_local:
        raise ValueError("MCP local du candidat requis")
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from bench.agents import RACINE
    env = environnement_mcp()
    params = StdioServerParameters(command=options.interpreteur_python or "python",
                                  args=[str(RACINE / "mcp_server/server.py")], cwd=str(RACINE), env=env)
    stack = AsyncExitStack()
    try:
        reader, writer = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(reader, writer))
        await asyncio.wait_for(session.initialize(), timeout=min(30, max(0, echeance-time.monotonic())))
        tools = await asyncio.wait_for(session.list_tools(), timeout=min(30, max(0, echeance-time.monotonic())))
        declarations = [{"name": t.name, "description": t.description or "",
                         "parametersJsonSchema": t.input_schema} for t in tools.tools]

        async def call(name, args):
            result = await session.call_tool(name, args)
            text = "\n".join(block.text for block in result.content if getattr(block, "type", "") == "text")
            return text, bool(result.isError)

        return await boucle(client, prompt=prompt, bras=bras, plafond=plafond, instructions=systeme,
                            outils=declarations, appeler_outil=call, echeance=echeance,
                            effort=options.effort)
    finally:
        client.fin_nettoyage = time.monotonic()+5
        async with asyncio.timeout_at(client.fin_nettoyage):
            await stack.aclose()


def environnement_mcp() -> dict[str, str]:
    """Seuls OS/Python et sources prévues ; aucun secret de modèle/OAuth/GitHub."""
    names = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "HOME",
             "USERPROFILE", "LANG", "LC_ALL", "PYTHONUTF8", "PYTHONIOENCODING",
             "LEGIFRANCE_CLIENT_ID", "LEGIFRANCE_CLIENT_SECRET", "LEGIFRANCE_ENV",
             "JUDILIBRE_KEY_ID", "PISTE_KEY_ID", "JUDILIBRE_ENV", "MCP_JUDILIBRE_SUPPRESSED_IDS"}
    env = {k: v for k, v in os.environ.items() if k.upper() in names}
    env.update(MCP_ENV="test", MCP_AUTH_MODE="disabled", LEGIFRANCE_NO_DOTENV="1")
    return env
