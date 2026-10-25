"""Sonde unique des candidats Flash explicites ; aucune génération ni retry."""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import sys
import time
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bench import gemini_http, quotas_gemini
from bench.identite_gemini import modele_exact

LOCAL = quotas_gemini.LOCAL


async def lire(client) -> dict:
    """Le même vrai Budget que génération/countTokens, jamais un budget de clé."""
    fin = time.monotonic() + gemini_http.HTTP_TOTAL_S
    try:
        client.avant(fin)
        with client.budget.tentative(0, "models.list"):
            try:
                data = await client.transport.appeler(client._cle, None, "models.list", None, echeance=fin)
            except gemini_http.ErreurGemini as exc:
                if exc.statut == 429:
                    client.budget.bloquer(429)
                raise
        if not isinstance(data.get("models"), list):
            raise ValueError("structure du catalogue invalide")
        models = []
        for row in data["models"]:
            if not isinstance(row, dict):
                raise ValueError("structure du modèle invalide")
            name = row.get("name", "")
            try:
                if not isinstance(name, str) or not name.startswith("models/"):
                    continue
                modele_exact(name[7:])
            except ValueError:
                continue
            values = {"modele": name[7:],
                      "generate_content_declare": "generateContent" in row.get("supportedGenerationMethods", []),
                      "input_token_limit": row.get("inputTokenLimit"), "output_token_limit": row.get("outputTokenLimit")}
            for field in ("input_token_limit", "output_token_limit"):
                if type(values[field]) is not int or values[field] <= 0:
                    values[field] = None
            models.append(values)
        return {"schema": 2, "statut": "catalogue_lu", "observe_le": dt.datetime.now(dt.timezone.utc).isoformat(),
                "requêtes_HTTP": 1, "generations": 0, "collecte_autorisee": False,
                "quotas_actifs_et_projet_attestes": False, "catalogue_complet": not bool(data.get("nextPageToken")),
                "filtre": "Flash explicites hors alias", "modeles": models}
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
        result = asyncio.run(lire(preparer_client(args.registre, args.profil)))
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except gemini_http.ErreurGemini as exc:
        print(f"Arrêt : {exc.categorie} ; aucun corps d'erreur affiché", file=sys.stderr)
        return 2
    except (ValueError, TypeError, OSError):
        print("Arrêt : profil, budget ou réponse invalides ; aucune valeur sensible affichée", file=sys.stderr)
        return 2
    print(f"Catalogue lu : {len(result['modeles'])} candidats Flash ; zéro génération, collecte non autorisée")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
