"""Qualification technique REST distincte des golds et de Gemini CLI."""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import hashlib
import json
import sys
import subprocess
import time
import uuid
import re
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bench import campaign, etude_v2, profils_gemini, quotas_gemini
from bench.contexte import ContexteExecution, etat_canonique
from bench.journal import Journal
from bench.budget_gemini import Budget


def source_reussie(row: dict) -> bool:
    """Une vraie lecture réussie ; un nom d'outil seul n'établit pas l'accès."""
    return any(a["erreur"] is False and bool(a["resultat"]) and
               (a["outil"].endswith("get_article") or a["outil"].endswith("fetch"))
               for a in row["appels"])


def serie_qualification(data: dict) -> str:
    base = campaign.digest(["qualification-rest-v2", data["candidat_sha256"], data["runtime_sha256"],
                            data["numero_projet"], data["modele"], data["raisonnement"]])
    renewal = data.get("requalification")
    if renewal is None:
        return base
    if (not isinstance(renewal, dict) or set(renewal) != {"schema", "nonce", "base_sha256", "serie_precedente",
            "cree_utc", "auteur_humain", "motif"} or renewal["schema"] != 2 or renewal["base_sha256"] != base
            or not re.fullmatch(r"[a-f0-9]{32}", renewal["nonce"])
            or not renewal["auteur_humain"].strip() or not renewal["motif"].strip()
            or dt.datetime.fromisoformat(renewal["cree_utc"]).utcoffset() is None):
        raise ValueError("requalification incohérente")
    return campaign.digest([base, renewal["nonce"]])


def renouveler(state: Path, data: dict, precedent: Path, auteur: str, motif: str) -> dict:
    """Deux pannes clôturées autorisent une nouvelle identité déclarée, sans reset."""
    if not auteur.strip() or not motif.strip():
        raise ValueError("auteur humain et motif de requalification requis")
    old = json.loads(quotas_gemini.chemin_local(precedent).read_bytes())
    if old.get("statut") != "a_relire" or any(old.get(k) != data[k] for k in (
            "schema", "moteur", "candidat_sha256", "runtime_sha256", "modele", "numero_projet", "raisonnement")):
        raise ValueError("ancien reçu incompatible ou déjà validé")
    previous = serie_qualification(old)
    etude_v2.sain(state, previous, phase="technique")
    etude_v2.verifier_attentes(state, previous, phase="technique")
    done = etude_v2.clotures(state)
    rows = [r for r in etude_v2.reservations(state) if r["series_sha256"] == previous and r["phase"] == "technique"]
    if not any(len(group := [r for r in rows if r["bras"] == arm]) == 2 and
               all(done[r["attempt_id"]]["statut"] == "infra_error" for r in group) for arm in "ABCD"):
        raise ValueError("deux pannes clôturées d'un bras requises avant requalification")
    renewal = {"schema": 2, "nonce": uuid.uuid4().hex, "base_sha256": serie_qualification(data),
               "serie_precedente": previous, "cree_utc": etude_v2.maintenant(), "auteur_humain": auteur, "motif": motif}
    Journal(state / "requalifications-gemini.jsonl").ajouter(renewal)
    return renewal


def verifier(registre: Path, profil: str, *, runtime_sha256: str) -> dict:
    """Exiger quatre vrais reçus techniques relus ; aucune validation juridique."""
    selected = profils_gemini.charger(registre, profil)
    row = selected["selection"]
    Budget(row["numero"], row["declare"]["modele"], row["declare"]["limites"]).verifier_arret()
    relative = row["row"]["qualification"]
    if not relative:
        raise ValueError("qualification REST absente ; aucune collecte")
    path = quotas_gemini.chemin_local(selected["path"].parent / relative)
    try:
        raw = path.read_bytes()
        data = json.loads(raw)
        if (data.get("schema") != 2 or data.get("moteur") != "gemini-rest-v2"
                or data.get("runtime_sha256") != runtime_sha256
                or data.get("candidat_sha256") != campaign.digest(campaign.fichiers_figes())
                or data.get("modele") != row["declare"]["modele"]
                or data.get("numero_projet") != row["numero"]
                or data.get("raisonnement") not in ("low", "medium", "high")):
            raise ValueError()
        validation = data["validation"]
        when = dt.datetime.fromisoformat(validation["date_validation"])
        if (data["statut"] != "valide" or not isinstance(validation["valide_par"], str)
                or not validation["valide_par"].strip() or when.utcoffset() is None
                or when > dt.datetime.now(dt.timezone.utc)
                or validation["auth_free_confirmee"] is not True
                or validation["isolation_confirmee"] is not True):
            raise ValueError()
        runs = data["runs"]
        if not isinstance(runs, list) or [r["bras"] for r in runs] != ["A", "B", "C", "D"]:
            raise ValueError()
        serie = serie_qualification(data)
        if data.get("requalification") is not None and data["requalification"] not in etude_v2.lire(etat_canonique() / "requalifications-gemini.jsonl"):
            raise ValueError()
        catalogue = None
        for r in runs:
            if (r["statut_technique"] != "ok" or r["modele_effectif"] != data["modele"]
                    or r["code_retour"] != 0 or not r["controles_procedure"]["isolation_appels"]
                    or r["origine"] != "transport_REST"):
                raise ValueError()
            receipt = next((x for x in etude_v2.reservations(etat_canonique())
                            if x["attempt_id"] == r["attempt_id"]), None)
            done = etude_v2.clotures(etat_canonique()).get(r["attempt_id"])
            engagement = etude_v2.engagements(etat_canonique()).get(r["attempt_id"])
            if (not receipt or not done or done["statut"] != "ok" or receipt.get("moteur") != "gemini-rest-v2"
                    or receipt.get("modele") != data["modele"] or receipt.get("bras") != r["bras"]
                    or receipt.get("series_sha256") != serie
                    or receipt.get("identite") != campaign.digest([serie, r["bras"]])
                    or receipt.get("phase") != "technique"
                    or any(r.get(k) != receipt[k] for k in ("series_sha256", "identite", "tentative", "phase"))
                    or not engagement or engagement.get("resultat_sha256") != campaign.digest(r)
                    or done.get("preuve_sha256") != campaign.digest(r)):
                raise ValueError()
            etude_v2.sain(etat_canonique(), receipt["series_sha256"], phase="technique")
            if r["bras"] in ("C", "D"):
                if not source_reussie(r):
                    raise ValueError()
                current = r["usage"]["catalogue_sha256"]
                if not isinstance(current, str) or not current or (catalogue and catalogue != current):
                    raise ValueError()
                catalogue = current
        return {"statut": "qualification_technique_validee", "moteur": "gemini-rest-v2",
                "modele": data["modele"], "runtime_sha256": runtime_sha256,
                "raisonnement": data["raisonnement"],
                "qualification_sha256": hashlib.sha256(raw).hexdigest(), "catalogue_sha256": catalogue,
                "validation_juridique": False}
    except (ValueError, KeyError, TypeError, AttributeError, OSError):
        raise ValueError("qualification REST incomplète, modifiée ou non relue ; aucune collecte") from None


def executer(registre: Path, profil: str, config: Path, sortie: Path, *,
             requalifier_depuis: Path | None = None, auteur: str = "", motif: str = "") -> dict:
    """Commandée explicitement après quotas confirmés ; quatre réponses techniques."""
    from bench import agents, gemini_rest, runtime_v2
    target = quotas_gemini.chemin_local(sortie)
    checked = profils_gemini.charger(registre, profil)
    selected = checked["selection"]
    cfg = campaign.read_json(config)
    timeout = cfg.get("timeout_s", 300)
    if type(timeout) is not int or not 1 <= timeout <= 3600:
        raise ValueError("timeout_s entier entre 1 et 3600 requis")
    family = next(f for f in cfg["familles"] if f["nom"] == "gemini")
    if (family["moteur"] != "gemini-rest-v2" or family["auth"] != "cle_api_gratuite"
            or family["raisonnement"] not in ("low", "medium", "high")
            or family["modele_demande"] != selected["declare"]["modele"]):
        raise ValueError("configuration REST explicite compatible requise")
    runtime = runtime_v2.relever(cfg)
    fingerprint = campaign.digest(runtime)
    candidate = campaign.digest(campaign.fichiers_figes())
    model = selected["declare"]["modele"]
    state = etat_canonique()
    prompts = {"A": "Réponds seulement : contrôle technique. Aucun avis juridique.",
               "B": "Réponds seulement : contrôle technique. Aucun avis juridique.",
               "C": "Recherche puis lis l'article 1240 du Code civil avec le connecteur local ; restitue son identifiant et ses métadonnées, sans avis juridique.",
               "D": "Recherche puis lis l'article 1240 du Code civil avec le connecteur local ; restitue son identifiant et ses métadonnées, sans avis juridique."}
    data = {"schema": 2, "moteur": "gemini-rest-v2", "runtime_sha256": fingerprint,
            "candidat_sha256": candidate, "modele": model, "numero_projet": selected["numero"],
            "raisonnement": family["raisonnement"],
            "statut": "a_relire", "runs": [], "validation": {"valide_par": "", "date_validation": "",
            "auth_free_confirmee": False, "isolation_confirmee": False}}
    with etude_v2.verrou(state):
        if target.exists():
            if requalifier_depuis is not None:
                raise ValueError("requalification exige un nouveau reçu ; aucun écrasement")
            previous = json.loads(target.read_bytes())
            if (any(previous.get(k) != data[k] for k in ("schema", "moteur", "runtime_sha256", "candidat_sha256", "modele", "numero_projet", "raisonnement"))
                    or previous.get("statut") != "a_relire"):
                raise ValueError("reçu existant incompatible ou validé : aucune écriture")
            data = previous
        elif requalifier_depuis is not None:
            data["requalification"] = renouveler(state, data, requalifier_depuis, auteur, motif)
            etude_v2.atomique(target, data)
        serie = serie_qualification(data)
        journal = state / serie / "qualification-gemini.jsonl"
        etude_v2.sain(state, serie, phase="technique")
        etude_v2.verifier_attentes(state, serie, phase="technique")
        # Après une clôture explicite d'interruption, le journal durable fait
        # foi même si le reçu JSON n'avait pas encore été remplacé.
        latest = {r["bras"]: r for r in etude_v2.lire(journal)}
        if latest:
            data["runs"] = sorted(latest.values(), key=lambda r: r["bras"])
        for bras, prompt in prompts.items():
            old = next((r for r in data["runs"] if r["bras"] == bras), None)
            if old and old["statut_technique"] == "ok":
                continue
            client = gemini_rest.preparer_client(registre, profil)
            try:
                client.budget.verifier_arret()
                identity = campaign.digest([serie, bras])
                reservation = etude_v2.reserver(state, identity, serie=serie, meta={"famille": "gemini",
                    "id": "qualification-"+bras, "bras": bras, "repetition": 1, "phase": "technique",
                    "modele": model, "moteur": "gemini-rest-v2", "output": str(journal)})
            except Exception:
                asyncio.run(client.transport.fermer())
                raise
            ctx = ContexteExecution(serie, identity, reservation["attempt_id"], reservation["tentative"],
                                    model, "gemini-rest-v2", time.monotonic()+timeout, reservation, state)
            options = agents.Options(modele=model, mcp_local=True, garder_flux=True,
                interpreteur_python=cfg.get("python_mcp", sys.executable), effort=family["raisonnement"],
                fournir_references=True, contexte=ctx)
            execution = asyncio.run(gemini_rest.executer_mcp(client, prompt=prompt, bras=bras, plafond=12, options=options))
            row = campaign.ligne_execution(execution, f={**family, "version_cli": "sans_CLI"}, bras=bras)
            row.update(schema=2, series_sha256=serie, identite=identity, tentative=ctx.tentative,
                       bras=bras, attempt_id=ctx.attempt_id, origine="transport_REST", phase="technique")
            if (row["modele_effectif"] != model or not row["controles_procedure"]["isolation_appels"]):
                row["statut_technique"] = execution.statut = "infra_error"
                row["categorie_infra"] = execution.categorie_infra = "isolation"
                etude_v2.invalider(state, serie, "isolation", "modèle ou isolation non conforme pendant qualification", phase="technique")
            elif execution.statut != "ok":
                row["categorie_infra"] = execution.categorie_infra or "transport"
                execution.categorie_infra = row["categorie_infra"]
            elif bras in ("C", "D") and not source_reussie(row):
                row["statut_technique"] = execution.statut = "infra_error"
                row["categorie_infra"] = execution.categorie_infra = "outil"
                row["motif_infra"] = "aucune lecture de source réussie pendant qualification"
            elif bras in ("C", "D") and not row["usage"].get("catalogue_sha256"):
                row["statut_technique"] = execution.statut = "infra_error"
                row["categorie_infra"] = execution.categorie_infra = "gel"
                row["motif_infra"] = "empreinte catalogue MCP absente pendant qualification"
            elif bras == "D" and row["usage"].get("catalogue_sha256") != next(
                    r["usage"].get("catalogue_sha256") for r in data["runs"] if r["bras"] == "C"):
                row["statut_technique"] = execution.statut = "infra_error"
                row["categorie_infra"] = execution.categorie_infra = "gel"
                row["motif_infra"] = "catalogue MCP modifié pendant qualification"
            runtime_change = False
            try:
                if time.monotonic() >= ctx.echeance_monotone:
                    raise TimeoutError("échéance du cas atteinte")
                runtime_change = campaign.digest(runtime_v2.relever(cfg, echeance_monotone=ctx.echeance_monotone)) != fingerprint
                if time.monotonic() >= ctx.echeance_monotone:
                    raise TimeoutError("échéance du contrôle atteinte")
            except (runtime_v2.ControleIndisponible, subprocess.TimeoutExpired, TimeoutError):
                # Une sonde indisponible ne prouve aucune dérive. Conserver le
                # résultat acquis et sa réservation, puis permettre une reprise.
                if execution.categorie_infra not in {"isolation", "contamination", "gel", "runtime", "modele"}:
                    row["statut_technique"] = execution.statut = "infra_error"
                    row["categorie_infra"] = execution.categorie_infra = "delai"
                    row["motif_infra"] = "contrôle final du runtime indisponible ; résultat conservé"
            if runtime_change or campaign.digest(campaign.fichiers_figes()) != candidate:
                row["statut_technique"] = execution.statut = "infra_error"
                row["categorie_infra"] = execution.categorie_infra = "runtime"
                row["motif_infra"] = "runtime ou candidat modifié pendant la qualification"
                etude_v2.invalider(state, serie, "runtime", row["motif_infra"], phase="technique")
            etude_v2.engager_resultat(state, reservation, campaign.digest(row))
            Journal(journal).ajouter(row)
            data["runs"] = [r for r in data["runs"] if r["bras"] != bras] + [row]
            data["runs"].sort(key=lambda r: r["bras"])
            etude_v2.atomique(target, data)
            if execution.categorie_infra in {"isolation", "contamination", "gel", "runtime", "modele"}:
                etude_v2.invalider(state, serie, execution.categorie_infra, "qualification technique invalidante", phase="technique")
            etude_v2.clore(state, reservation, statut=execution.statut,
                categorie=execution.categorie_infra if execution.statut != "ok" else "",
                preuve=campaign.digest(row))
            if execution.statut != "ok":
                break
        # Même après récupération du dernier bras, reconstruire le reçu dérivé
        # depuis le journal durable ; aucun ancien JSON partiel n'est conservé.
        etude_v2.atomique(target, data)
    technique_ok = (len(data["runs"]) == 4 and all(r["statut_technique"] == "ok" for r in data["runs"])
                    and all(source_reussie(r) for r in data["runs"] if r["bras"] in ("C", "D"))
                    and len({r["usage"].get("catalogue_sha256") for r in data["runs"] if r["bras"] in ("C", "D")}) == 1)
    return {"statut": "a_relire", "reponses_techniques": len(data["runs"]), "collecte_autorisee": False,
            "technique_ok": technique_ok,
            "runtime_sha256": fingerprint}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registre", required=True, type=Path)
    parser.add_argument("--profil", required=True)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--sortie", required=True, type=Path)
    parser.add_argument("--requalifier-depuis", type=Path)
    parser.add_argument("--auteur", default="")
    parser.add_argument("--motif", default="")
    args = parser.parse_args(argv)
    try:
        result = executer(args.registre, args.profil, args.config, args.sortie,
                         requalifier_depuis=args.requalifier_depuis, auteur=args.auteur, motif=args.motif)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["technique_ok"] else 2
    except (ValueError, KeyError, OSError):
        print("Qualification refusée : profil, quotas, runtime ou preuves invalides ; examen requis", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
