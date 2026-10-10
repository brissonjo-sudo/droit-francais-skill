"""Qualification technique REST distincte des golds et de Gemini CLI."""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import hashlib
import json
import sys
import time
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
        serie = campaign.digest(["qualification-rest-v2", data["candidat_sha256"], runtime_sha256,
                                 row["numero"], data["modele"], data["raisonnement"]])
        catalogue = None
        for r in runs:
            if (r["statut_technique"] != "ok" or r["modele_effectif"] != data["modele"]
                    or r["code_retour"] != 0 or not r["controles_procedure"]["isolation_appels"]
                    or r["origine"] != "transport_REST"):
                raise ValueError()
            receipt = next((x for x in etude_v2.reservations(etat_canonique())
                            if x["attempt_id"] == r["attempt_id"]), None)
            done = etude_v2.clotures(etat_canonique()).get(r["attempt_id"])
            if (not receipt or not done or done["statut"] != "ok" or receipt.get("moteur") != "gemini-rest-v2"
                    or receipt.get("modele") != data["modele"] or receipt.get("bras") != r["bras"]
                    or receipt.get("series_sha256") != serie
                    or receipt.get("identite") != campaign.digest([serie, r["bras"]])
                    or done.get("preuve_sha256") != campaign.digest(r)):
                raise ValueError()
            etude_v2.sain(etat_canonique(), receipt["series_sha256"])
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


def executer(registre: Path, profil: str, config: Path, sortie: Path) -> dict:
    """Commandée explicitement après quotas confirmés ; quatre réponses techniques."""
    from bench import agents, gemini_rest, runtime_v2
    target = quotas_gemini.chemin_local(sortie)
    checked = profils_gemini.charger(registre, profil)
    selected = checked["selection"]
    cfg = campaign.read_json(config)
    family = next(f for f in cfg["familles"] if f["nom"] == "gemini")
    if (family["moteur"] != "gemini-rest-v2" or family["auth"] != "cle_api_gratuite"
            or family["raisonnement"] not in ("low", "medium", "high")
            or family["modele_demande"] != selected["declare"]["modele"]):
        raise ValueError("configuration REST explicite compatible requise")
    runtime = runtime_v2.relever(cfg)
    fingerprint = campaign.digest(runtime)
    candidate = campaign.digest(campaign.fichiers_figes())
    model = selected["declare"]["modele"]
    serie = campaign.digest(["qualification-rest-v2", candidate, fingerprint, selected["numero"], model, family["raisonnement"]])
    state = etat_canonique()
    journal = state / serie / "qualification-gemini.jsonl"
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
            previous = json.loads(target.read_bytes())
            if (any(previous.get(k) != data[k] for k in ("schema", "moteur", "runtime_sha256", "candidat_sha256", "modele", "numero_projet", "raisonnement"))
                    or previous.get("statut") != "a_relire"):
                raise ValueError("reçu existant incompatible ou validé : aucune écriture")
            data = previous
        etude_v2.verifier_attentes(state, serie)
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
                                    model, "gemini-rest-v2", time.monotonic()+300, reservation, state)
            options = agents.Options(modele=model, mcp_local=True, garder_flux=True,
                interpreteur_python=cfg.get("python_mcp", sys.executable), effort=family["raisonnement"],
                fournir_references=True, contexte=ctx)
            execution = asyncio.run(gemini_rest.executer_mcp(client, prompt=prompt, bras=bras, plafond=12, options=options))
            row = campaign.ligne_execution(execution, f={**family, "version_cli": "sans_CLI"}, bras=bras)
            row.update(schema=2, series_sha256=serie, identite=identity, tentative=ctx.tentative,
                       bras=bras, attempt_id=ctx.attempt_id, origine="transport_REST")
            if (row["modele_effectif"] != model or not row["controles_procedure"]["isolation_appels"]):
                row["statut_technique"] = execution.statut = "infra_error"
                row["categorie_infra"] = execution.categorie_infra = "isolation"
                etude_v2.invalider(state, serie, "isolation", "modèle ou isolation non conforme pendant qualification")
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
            if campaign.digest(runtime_v2.relever(cfg)) != fingerprint or campaign.digest(campaign.fichiers_figes()) != candidate:
                row["statut_technique"] = execution.statut = "infra_error"
                row["categorie_infra"] = execution.categorie_infra = "runtime"
                row["motif_infra"] = "runtime ou candidat modifié pendant la qualification"
                etude_v2.invalider(state, serie, "runtime", row["motif_infra"])
            Journal(journal).ajouter(row)
            data["runs"] = [r for r in data["runs"] if r["bras"] != bras] + [row]
            data["runs"].sort(key=lambda r: r["bras"])
            etude_v2.atomique(target, data)
            if execution.categorie_infra in {"isolation", "contamination", "gel", "runtime", "modele"}:
                etude_v2.invalider(state, serie, execution.categorie_infra, "qualification technique invalidante")
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
    args = parser.parse_args(argv)
    try:
        result = executer(args.registre, args.profil, args.config, args.sortie)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["technique_ok"] else 2
    except (ValueError, KeyError, OSError):
        print("Qualification refusée : profil, quotas, runtime ou preuves invalides ; examen requis", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
