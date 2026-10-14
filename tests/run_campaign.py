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
from bench import ablation, campaign, corriges, etude_v2, revue_v2, approbations_v2, contexte


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("verifier")
    sub.add_parser("etat")
    gold_review = sub.add_parser("corriges")
    gold_review.add_argument("--sortie", type=Path, required=True)
    freeze = sub.add_parser("figer")
    freeze.add_argument("--config", type=Path, required=True)
    freeze.add_argument("--sortie", type=Path, required=True)
    for action in ("preflight", "collecter"):
        p = sub.add_parser(action)
        p.add_argument("--gel", type=Path, required=True)
        p.add_argument("--famille", choices=campaign.FAMILLES, required=True)
        if action == "collecter":
            p.add_argument("--phase", choices=("pilote", "principale"), required=True)
    entrelace = sub.add_parser("collecter-entrelace")
    entrelace.add_argument("--gel", type=Path, required=True)
    entrelace.add_argument("--phase", choices=("pilote", "principale"), required=True)
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
    report.add_argument("--revues-humaines", type=Path)
    report.add_argument("--gel", type=Path, required=True)
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
    compare = sub.add_parser("comparer-ablation")
    for name in ("gel", "plan", "revues", "revues-humaines", "sortie"):
        compare.add_argument("--" + name, type=Path, required=True)
    prep = sub.add_parser("preparer-approbation")
    prep.add_argument("--gel", type=Path, required=True)
    prep.add_argument("--famille", choices=campaign.FAMILLES, required=True)
    prep.add_argument("--type", choices=("preflight", "pilote"), required=True)
    prep.add_argument("--sortie", type=Path, required=True)
    approve = sub.add_parser("approuver-recu")
    approve.add_argument("--gel", type=Path, required=True)
    approve.add_argument("--avis", type=Path, required=True)
    for action in ("clore-interruption", "declarer-manquant", "recuperer-verrou", "quarantainer-journal", "rattacher-etat"):
        p = sub.add_parser(action)
        p.add_argument("--auteur-humain", required=True)
        p.add_argument("--motif", required=True)
        if action == "clore-interruption":
            p.add_argument("--attempt-id", required=True)
        elif action == "declarer-manquant":
            p.add_argument("--gel", type=Path, required=True)
            p.add_argument("--identite", required=True)
        elif action == "quarantainer-journal":
            p.add_argument("--journal", type=Path, required=True)
    human = sub.add_parser("ajouter-revue-humaine")
    human.add_argument("--avis", type=Path, required=True)
    human.add_argument("--resultats", nargs="+", type=Path, required=True)
    human.add_argument("--revues", type=Path, required=True)
    human.add_argument("--sortie", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "etat":
            print(campaign.STATE)
        elif args.action == "verifier":
            cases = campaign.corpus()
            print(json.dumps({"cas": len(cases), "modes": 18, "reponses_principales": 864,
                              "corriges_valides": sum(campaign.gold_pret(c) for c in cases),
                              "statut": "preparation"}, ensure_ascii=False))
        elif args.action == "corriges":
            print(f"{corriges.exporter(args.sortie)} corrigés exportés, sans validation automatique")
        elif args.action == "figer":
            gel = campaign.figer(args.config, args.sortie)
            print(gel["series_sha256"])
        elif args.action == "preflight":
            receipt = campaign.preflight(campaign.read_json(args.gel), args.famille)
            print(receipt)
            if any(r["statut_technique"] != "ok" for r in campaign.read_json(receipt)["runs"]):
                return 2
        elif args.action == "collecter":
            print(f"{campaign.collecter(campaign.read_json(args.gel), args.famille, args.phase)} réponses écrites")
        elif args.action == "collecter-entrelace":
            print(f"{campaign.collecter_entrelace(campaign.read_json(args.gel), args.phase)} réponses écrites")
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
        elif args.action == "comparer-ablation":
            ablation.comparer(campaign.read_json(args.gel), args.plan, args.revues, args.revues_humaines, args.sortie)
        elif args.action == "preparer-approbation":
            approbations_v2.preparer(campaign.read_json(args.gel), args.famille, args.type, args.sortie)
        elif args.action == "approuver-recu":
            approbations_v2.approuver(campaign.read_json(args.gel), campaign.read_json(args.avis))
        elif args.action == "clore-interruption":
            etude_v2.clore_interruption(campaign.STATE, args.attempt_id, args.auteur_humain, args.motif)
        elif args.action == "declarer-manquant":
            gel = campaign.read_json(args.gel)
            etude_v2.declarer_manquant(campaign.STATE, gel["series_sha256"], args.identite, args.auteur_humain, args.motif)
        elif args.action == "recuperer-verrou":
            etude_v2.retirer_verrou_abandonne(campaign.STATE, args.auteur_humain, args.motif)
        elif args.action == "quarantainer-journal":
            etude_v2.quarantainer_journal(campaign.STATE, args.journal, args.auteur_humain, args.motif)
        elif args.action == "rattacher-etat":
            with etude_v2.verrou(campaign.STATE):
                contexte.assurer_ancre(campaign.STATE, auteur=args.auteur_humain, motif=args.motif)
        elif args.action == "ajouter-revue-humaine":
            def charger():
                results = campaign.dernieres_tentatives([r for p in args.resultats for r in campaign.historique_acquis(p, campaign.STATE)])
                judges = campaign.dernieres_tentatives_juges(campaign.historique_acquis(args.revues, campaign.STATE, statut="statut_juge"))
                return {r["identite"]: r for r in results}, {r["identite"]: r for r in judges}
            revue_v2.ajouter(args.sortie, campaign.read_json(args.avis), {}, {}, state=campaign.STATE, charger=charger)
        else:
            campaign.rapport(args.resultats, args.revues, humains=args.revues_humaines,
                frozen=campaign.read_json(args.gel), sortie=args.sortie)
    except (ValueError, KeyError, OSError) as exc:
        print(f"Arrêt : {str(exc) if not isinstance(exc, OSError) else 'lecture ou écriture privée impossible ; consulter localement les permissions et fichiers'}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
