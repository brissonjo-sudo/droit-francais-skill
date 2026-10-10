#!/usr/bin/env python3
"""Préparer et exécuter la campagne des 18 modes, sans verdict fictif."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
from bench import ablation, campaign


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("verifier")
    freeze = sub.add_parser("figer")
    freeze.add_argument("--config", type=Path, required=True)
    freeze.add_argument("--sortie", type=Path, required=True)
    for action in ("preflight", "collecter"):
        p = sub.add_parser(action)
        p.add_argument("--gel", type=Path, required=True)
        p.add_argument("--famille", choices=campaign.FAMILLES, required=True)
        if action == "collecter":
            p.add_argument("--phase", choices=("pilote", "principale"), required=True)
    review = sub.add_parser("paquet-revue")
    review.add_argument("--resultats", type=Path, nargs="+", required=True)
    review.add_argument("--sortie", type=Path, required=True)
    judge = sub.add_parser("juger")
    judge.add_argument("--gel", type=Path, required=True)
    judge.add_argument("--paquet", type=Path, required=True)
    judge.add_argument("--famille", choices=campaign.FAMILLES, required=True)
    judge.add_argument("--sortie", type=Path, required=True)
    report = sub.add_parser("rapport")
    report.add_argument("--resultats", type=Path, nargs="+", required=True)
    report.add_argument("--revues", type=Path, required=True)
    report.add_argument("--sortie", type=Path, required=True)
    abl = sub.add_parser("preparer-ablation")
    abl.add_argument("--gel", type=Path, required=True)
    abl.add_argument("--recettes", type=Path, required=True)
    abl.add_argument("--rapport", type=Path, required=True)
    abl.add_argument("--dossier", type=Path, required=True)
    run_abl = sub.add_parser("ablation")
    run_abl.add_argument("--gel", type=Path, required=True)
    run_abl.add_argument("--plan", type=Path, required=True)
    run_abl.add_argument("--famille", choices=campaign.FAMILLES, required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "verifier":
            cases = campaign.corpus()
            print(json.dumps({"cas": len(cases), "modes": 18, "reponses_principales": 864,
                              "corriges_valides": sum(campaign.gold_pret(c) for c in cases),
                              "statut": "preparation"}, ensure_ascii=False))
        elif args.action == "figer":
            gel = campaign.figer(args.config, args.sortie)
            print(gel["series_sha256"])
        elif args.action == "preflight":
            print(campaign.preflight(campaign.read_json(args.gel), args.famille))
        elif args.action == "collecter":
            print(f"{campaign.collecter(campaign.read_json(args.gel), args.famille, args.phase)} réponses écrites")
        elif args.action == "paquet-revue":
            campaign.paquet_revue(args.resultats, args.sortie)
        elif args.action == "juger":
            count = campaign.juger_paquet(campaign.read_json(args.gel), args.paquet, args.famille, args.sortie)
            print(f"{count} jugements écrits")
        elif args.action == "preparer-ablation":
            result = ablation.preparer(campaign.read_json(args.gel), args.recettes, args.rapport, args.dossier)
            print(f"{result['reponses_max']} réponses expérimentales prévues")
        elif args.action == "ablation":
            count = ablation.collecter(campaign.read_json(args.gel), args.plan, args.famille)
            print(f"{count} réponses expérimentales écrites")
        else:
            campaign.write_json(args.sortie, campaign.rapport(args.resultats, args.revues))
    except (ValueError, KeyError, OSError) as exc:
        print(f"Arrêt : {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
