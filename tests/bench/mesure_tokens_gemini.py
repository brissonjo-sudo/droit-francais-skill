"""Sonde technique unique de tokens sur le corpus public ; zéro génération."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bench import campaign, gemini_http, native, quotas_gemini

MODELE = "gemini-3.8-flash"


def preparer() -> tuple[dict, dict]:
    """Sélection déterministe par taille UTF-8, sans prétendre au maximum tokens."""
    cases = campaign.corpus()
    case = max(cases, key=lambda c: (len(campaign.prompt_cas(c).encode("utf-8")), c["id"]))
    systeme = native.instructions("B", references=True)
    prompt = campaign.prompt_cas(case)
    request = {"systemInstruction": {"parts": [{"text": systeme}]},
               "contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    raw = json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    metadata = {"modele": MODELE, "bras": "B", "cas": case["id"],
                "selection": "plus_grand_prompt_UTF8_du_corpus_pas_maximum_tokens",
                "requete_sha256": hashlib.sha256(raw).hexdigest(), "requete_octets_UTF8": len(raw),
                "corpus_sha256": hashlib.sha256(campaign.CORPUS.read_bytes()).hexdigest(),
                "outils_inclus": False, "historique_apres_outils_inclus": False}
    return request, metadata


def mesurer(cle: str, budget) -> dict:
    """Une requête de tokenizer, sans lire de corrigé ni générer de réponse."""
    request, result = preparer()
    with budget.tentative(0, "countTokens"):
        try:
            tokens = gemini_http.compter(cle, MODELE, request)
        except gemini_http.ErreurGemini as exc:
            if exc.statut == 429:
                budget.bloquer(429)
            raise
    result.update(tokens_entree=tokens,
                  observe_le=dt.datetime.now(dt.timezone.utc).isoformat(),
                  requetes_HTTP=1, generations=0, collecte_autorisee=False,
                  quotas_actifs_et_projet_attestes=False)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sortie", required=True, type=Path)
    parser.add_argument("--registre", required=True, type=Path)
    parser.add_argument("--profil", required=True)
    parser.add_argument("--budget-state", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        target = quotas_gemini.chemin_local(args.sortie)
        if target.exists():
            raise ValueError("sortie existante : aucune écriture")
        from bench.gemini_rest import preparer_client
        client = preparer_client(args.registre, args.profil, args.budget_state)
        client.garde()
        if client.modele != MODELE:
            raise ValueError("profil incompatible avec cette mesure")
        result = mesurer(client._cle, client.budget)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except gemini_http.ErreurGemini as exc:
        print(f"Arrêt : {exc} ; aucune reprise", file=sys.stderr)
        return 2
    except (ValueError, OSError):
        print("Arrêt : clé, charge ou sortie invalide ; aucun contenu privé affiché", file=sys.stderr)
        return 2
    print(f"Entrée mesurée : {result['tokens_entree']} tokens ; zéro génération, quotas non attestés")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
