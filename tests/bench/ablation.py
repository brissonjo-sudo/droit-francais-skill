"""Variantes expérimentales séparées ; aucune modification du skill canonique."""
from __future__ import annotations
import hashlib
import sys
from pathlib import Path

from bench import agents, campaign, native
from bench.journal import Journal
from bench.preconditions import abonnement


def preparer(gel: dict, recipes_path: Path, report_path: Path, target: Path, *, state: Path = campaign.STATE) -> dict:
    with campaign.verrou(state):
        return _preparer(gel, recipes_path, report_path, target, state=state)


def _preparer(gel: dict, recipes_path: Path, report_path: Path, target: Path, *, state: Path) -> dict:
    campaign.verifier_gel(gel)
    campaign.etude_v2.sain(state, gel["series_sha256"])
    report = campaign.read_json(campaign.confiner(report_path, state))
    if report.get("statut") != "revue_complete_a_valider" or report.get("series_sha256") != gel["series_sha256"]:
        raise ValueError("analyse principale complète requise avant ablation")
    campaign.verifier_rapport_acquis(report, gel, state)
    recipes = campaign.read_json(recipes_path)
    if not 1 <= len(recipes) <= gel["config"]["ablation"]["max_modes"] or len({r["mode"] for r in recipes}) != len(recipes):
        raise ValueError("un à six modes distincts au maximum")
    campaign.confiner(target, state)
    if target.exists():
        raise ValueError("dossier expérimental existant")
    base = native.methode(True)
    variants = []
    for recipe in recipes:
        if recipe["mode"] not in range(1, 19) or not recipe.get("valide_par"):
            raise ValueError("mode ou revue humaine de l'ablation manquant")
        if not recipe.get("raison") or not recipe.get("regles_partagees") or not recipe.get("passages_exacts"):
            raise ValueError("attribution et passages retirés doivent être documentés")
        text = base
        for passage in recipe["passages_exacts"]:
            if not isinstance(passage, str) or not passage or text.count(passage) != 1:
                raise ValueError("passage absent ou ambigu ; aucune suppression approximative")
            text = text.replace(passage, "")
        path = target / f"mode-{recipe['mode']:02d}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        variants.append({"mode": recipe["mode"], "path": str(path.resolve()),
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "recette": recipe})
    plan = {"schema": 2, "series_sha256": gel["series_sha256"], "variantes": variants,
            "comparaison": "C principal acquis versus C avec variante expérimentale",
            "reponses_max": len(variants) * 2 * gel["config"]["ablation"]["repetitions"] * len(gel["config"]["familles"]),
            "rapport_principal_sha256": campaign.digest(report), "rapport_principal_path": str(report_path.resolve())}
    plan["plan_sha256"] = campaign.digest(plan)
    campaign.write_json(target / "plan.json", plan)
    return plan


def verifier_rapport_plan(plan: dict, gel: dict, state: Path) -> None:
    report = campaign.read_json(campaign.confiner(Path(plan["rapport_principal_path"]), state))
    if report.get("statut") != "revue_complete_a_valider" or campaign.digest(report) != plan["rapport_principal_sha256"]:
        raise ValueError("analyse principale changée ou incomplète")
    campaign.verifier_rapport_acquis(report, gel, state)


def collecter(gel: dict, plan_path: Path, famille: str, *, state: Path = campaign.STATE) -> int:
    campaign.confiner(plan_path, state)
    plan = campaign.read_json(plan_path)
    if plan.get("schema") != 2 or plan["series_sha256"] != gel["series_sha256"] or campaign.digest({k: v for k, v in plan.items() if k != "plan_sha256"}) != plan["plan_sha256"]:
        raise ValueError("plan expérimental v2 modifié ou autre candidat")
    f = next(f for f in gel["config"]["familles"] if f["nom"] == famille)
    target = state / gel["series_sha256"] / f"ablation-{plan['plan_sha256']}-{famille}.jsonl"
    count = 0
    with campaign.verrou(state):
        campaign.pret_collecte(gel, "principale", state)
        verifier_rapport_plan(plan, gel, state)
        done = {r["identite"] for r in campaign.resultats_acquis(target, state) if r["statut_technique"] == "ok"}
        missing = campaign.etude_v2.manquants(state, gel["series_sha256"])
        cases = {c["id"]: c for c in campaign.corpus()}
        variants = {v["mode"]: v for v in plan["variantes"]}
        for unit in gel["plan"]["principale"]:
            if unit["famille"] != famille or unit["bras"] != "C" or unit["mode"] not in variants:
                continue
            variant = variants[unit["mode"]]
            path = campaign.confiner(Path(variant["path"]), state)
            if hashlib.sha256(path.read_bytes()).hexdigest() != variant["sha256"]:
                campaign.etude_v2.invalider(state, gel["series_sha256"], "gel", "variante expérimentale modifiée")
                raise ValueError("variante expérimentale modifiée")
            unit = {**unit, "phase": "ablation"}
            key = campaign.identite(plan["plan_sha256"], famille, unit["id"], "C", unit["repetition"], "ablation")
            if key in done or key in missing:
                continue
            options = campaign.options_pour(gel, f)
            options.methode_experimentale = str(path)
            row, reservation = campaign.effectuer(gel, f, unit, target, state,
                prompt=campaign.prompt_cas(cases[unit["id"]]), options=options, identity=key)
            row.update(variante_sha256=variant["sha256"], plan_sha256=plan["plan_sha256"])
            if hashlib.sha256(path.read_bytes()).hexdigest() != variant["sha256"]:
                row.update(statut_technique="infra_error", categorie_infra="gel", motif_infra="variante modifiée pendant l'appel")
            campaign.acquerir(state, target, row, reservation)
            count += 1
            if count >= 4:
                break
    return count
