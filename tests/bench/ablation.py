"""Variantes expérimentales séparées ; aucune modification du skill canonique."""
from __future__ import annotations
import hashlib
import sys
from pathlib import Path

from bench import agents, campaign, native
from bench.journal import Journal
from bench.preconditions import abonnement


def preparer(gel: dict, recipes_path: Path, report_path: Path, target: Path) -> dict:
    campaign.verifier_gel(gel)
    report = campaign.read_json(report_path)
    if report.get("statut") != "revue_complete_a_valider" or report.get("series_sha256") != gel["series_sha256"]:
        raise ValueError("analyse principale complète requise avant ablation")
    recipes = campaign.read_json(recipes_path)
    if not 1 <= len(recipes) <= 6 or len({r["mode"] for r in recipes}) != len(recipes):
        raise ValueError("un à six modes distincts au maximum")
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
    plan = {"schema": 1, "series_sha256": gel["series_sha256"], "variantes": variants,
            "comparaison": "C principal acquis versus C avec variante expérimentale",
            "reponses_max": len(variants) * 2 * 2 * 3,
            "rapport_principal_sha256": campaign.digest(report)}
    plan["plan_sha256"] = campaign.digest(plan)
    campaign.write_json(target / "plan.json", plan)
    return plan


def collecter(gel: dict, plan_path: Path, famille: str, *, state: Path = campaign.STATE) -> int:
    campaign.verifier_gel(gel)
    plan = campaign.read_json(plan_path)
    if plan["series_sha256"] != gel["series_sha256"] or campaign.digest({k: v for k, v in plan.items() if k != "plan_sha256"}) != plan["plan_sha256"]:
        raise ValueError("plan expérimental modifié ou autre candidat")
    f = next(f for f in gel["config"]["familles"] if f["nom"] == famille)
    receipt = state / gel["series_sha256"] / f"preflight-{famille}.json"
    if (not abonnement(famille, f["executable"]) or campaign.version_cli(f["executable"]) != f["version_cli"]
            or not receipt.exists() or not campaign.preflight_pret(campaign.read_json(receipt), gel, f)):
        raise ValueError("client expérimental non qualifié")
    cases = campaign.corpus()
    if not all(campaign.gold_pret(c) for c in cases):
        raise ValueError("corrigés non validés")
    target = state / gel["series_sha256"] / f"ablation-{plan['plan_sha256']}-{famille}.jsonl"
    historique = campaign.lire_strict(target)
    from collections import Counter
    tentatives = Counter(r["identite"] for r in historique)
    done = {r["identite"] for r in campaign.dernieres_tentatives(historique)
            if r["statut_technique"] == "ok"}
    count = 0
    with campaign.verrou(state):
        for variant in plan["variantes"]:
            path = Path(variant["path"])
            if hashlib.sha256(path.read_bytes()).hexdigest() != variant["sha256"]:
                raise ValueError("variante expérimentale modifiée")
            options = agents.Options(modele=f["modele_demande"], executable=f["executable"], mcp_local=True,
                garder_flux=True, abonnement_seul=True, effort=f["raisonnement"], methode_experimentale=str(path),
                interpreteur_python=gel["config"].get("python_mcp", sys.executable))
            for c in (c for c in cases if c["mode"] == variant["mode"]):
                for rep in (1, 2):
                    key = campaign.identite(plan["plan_sha256"], famille, c["id"], "C", rep, "ablation")
                    if key in done:
                        continue
                    if tentatives[key] >= 2:
                        raise campaign.ArretCollecte("deux pannes d'ablation : examen de la série requis")
                    if hashlib.sha256(path.read_bytes()).hexdigest() != variant["sha256"]:
                        raise ValueError("variante modifiée avant exécution")
                    campaign.reserver_budget(state, key)
                    execution = campaign.executer_fige(gel, f, prompt=campaign.prompt_cas(c), bras="C",
                                                                 plafond=12, options=options)
                    row = campaign.ligne_execution(execution, f=f, bras="C")
                    if row["modele_effectif"] != f["modele_demande"]:
                        row["statut_technique"] = "infra_error"
                        row["motif_infra"] = "modèle effectif différent ou inconnu"
                    row.update(identite=key, series_sha256=gel["series_sha256"], id=c["id"], mode=c["mode"],
                               bras="C", repetition=rep, phase="ablation", variante_sha256=variant["sha256"],
                               plan_sha256=plan["plan_sha256"])
                    row["tentative"] = tentatives[key] + 1
                    Journal(target).ajouter(row)
                    count += 1
                    if row["statut_technique"] != "ok" or not row["controles_procedure"]["isolation_appels"]:
                        raise campaign.ArretCollecte("ablation interrompue ; tentative conservée")
    return count
