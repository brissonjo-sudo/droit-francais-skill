"""Sonde technique unique de tokens sur le corpus public ; zéro génération."""
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

from bench import campaign, gemini_http, native, quotas_gemini
from bench.identite_gemini import modele_exact


def preparer(modele: str) -> tuple[dict, dict]:
    """Sélection UTF-8 déterministe ; ni maximum de tokens ni corrigé envoyé."""
    modele_exact(modele)
    case = max(campaign.corpus(), key=lambda c: (len(campaign.prompt_cas(c).encode()), c["id"]))
    request = {"systemInstruction": {"parts": [{"text": native.instructions("B", references=True)}]},
               "contents": [{"role": "user", "parts": [{"text": campaign.prompt_cas(case)}]}]}
    raw = json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return request, {"modele": modele, "bras": "B", "cas": case["id"],
                    "selection": "plus_grand_prompt_UTF8_du_corpus_pas_maximum_tokens",
                    "requete_sha256": hashlib.sha256(raw).hexdigest(), "requete_octets_UTF8": len(raw),
                    "corpus_sha256": hashlib.sha256(campaign.CORPUS.read_bytes()).hexdigest(),
                    "outils_inclus": False, "historique_apres_outils_inclus": False}


async def mesurer(client) -> dict:
    request, result = preparer(client.modele)
    fin = time.monotonic() + gemini_http.HTTP_TOTAL_S
    try:
        client.avant(fin)
        with client.budget.tentative(0, "countTokens"):
            try:
                tokens = await client.transport.compter(client._cle, client.modele, request, echeance=fin)
            except gemini_http.ErreurGemini as exc:
                if exc.statut == 429:
                    client.budget.bloquer(429)
                raise
        result.update(tokens_entree=tokens, observe_le=dt.datetime.now(dt.timezone.utc).isoformat(),
                      requetes_HTTP=1, generations=0, collecte_autorisee=False,
                      quotas_actifs_et_projet_attestes=False)
        return result
    finally:
        async with asyncio.timeout(5):
            await client.transport.fermer()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sortie", required=True, type=Path)
    parser.add_argument("--registre", required=True, type=Path)
    parser.add_argument("--profil", required=True)
    args = parser.parse_args(argv)
    try:
        target = quotas_gemini.chemin_local(args.sortie)
        if target.exists():
            raise ValueError("sortie existante")
        from bench.gemini_rest import preparer_client
        result = asyncio.run(mesurer(preparer_client(args.registre, args.profil)))
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except gemini_http.ErreurGemini as exc:
        print(f"Arrêt : {exc.categorie} ; aucune reprise", file=sys.stderr)
        return 2
    except (ValueError, OSError):
        print("Arrêt : profil, budget ou réponse invalides ; aucun contenu privé affiché", file=sys.stderr)
        return 2
    print(f"Entrée mesurée : {result['tokens_entree']} tokens ; zéro génération, collecte non autorisée")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
