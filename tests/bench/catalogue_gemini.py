"""Lecture unique du catalogue Gemini ; aucun appel de génération ni retry."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000"
LOCAL = Path(__file__).resolve().parents[2] / "tests/bench/runs"


class SansRedirection(urllib.request.HTTPRedirectHandler):
    """Ne jamais transférer l'en-tête secret à une autre destination."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "redirection refusée", headers, fp)


def lire(cle: str) -> dict:
    """Un GET borné, suivi d'une liste blanche de métadonnées publiques."""
    if not cle or len(cle) < 8 or "\n" in cle or "\r" in cle:
        raise ValueError("GEMINI_API_KEY absente ou invalide ; valeur non affichée")
    req = urllib.request.Request(ENDPOINT, headers={"x-goog-api-key": cle}, method="GET")
    opener = urllib.request.build_opener(SansRedirection())
    with opener.open(req, timeout=20) as response:
        payload = response.read(2_000_001)
    if len(payload) > 2_000_000:
        raise ValueError("catalogue trop volumineux")
    data = json.loads(payload)
    if not isinstance(data, dict) or not isinstance(data.get("models"), list):
        raise ValueError("structure du catalogue invalide")
    models = []
    for row in data["models"]:
        if not isinstance(row, dict):
            raise ValueError("structure de modèle invalide")
        name = row.get("name", "")
        if not isinstance(name, str) or not re.fullmatch(r"models/gemini-[a-z0-9.-]{1,100}", name):
            continue
        # Pas de description libre, projet, quota supposé ou corps d'erreur.
        values = {"modele": name.removeprefix("models/"),
                  "generate_content_declare": "generateContent" in row.get("supportedGenerationMethods", []),
                  "input_token_limit": row.get("inputTokenLimit"),
                  "output_token_limit": row.get("outputTokenLimit")}
        for key in ("input_token_limit", "output_token_limit"):
            if type(values[key]) is not int or values[key] <= 0:
                values[key] = None
        models.append(values)
    result = {"schema": 1, "statut": "catalogue_lu", "observe_le": dt.datetime.now(dt.timezone.utc).isoformat(),
              "requêtes_HTTP": 1, "generations": 0, "collecte_autorisee": False,
              "quotas_actifs_et_projet_attestes": False,
              "catalogue_complet": not bool(data.get("nextPageToken")), "modeles": models}
    if cle in json.dumps(result):
        raise ValueError("résultat refusé pour protection du secret")
    return result


def main(argv=None) -> int:
    """Écrire seulement une observation assainie dans l'état local ignoré."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sortie", required=True, type=Path)
    args = parser.parse_args(argv)
    target = args.sortie.resolve()
    if not target.is_relative_to(LOCAL.resolve()) or target.exists():
        print("Arrêt : sortie neuve requise sous tests/bench/runs", file=sys.stderr)
        return 2
    try:
        result = lire(os.environ.get("GEMINI_API_KEY", ""))
    except urllib.error.HTTPError as exc:
        print(f"Arrêt : Gemini HTTP {exc.code} ; aucun corps d'erreur affiché", file=sys.stderr)
        return 2
    except (ValueError, TypeError, OSError, urllib.error.URLError):
        print("Arrêt : clé absente, réseau ou catalogue invalide ; aucune valeur sensible affichée", file=sys.stderr)
        return 2
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"Catalogue lu : {len(result['modeles'])} modèles Gemini déclarés ; zéro génération, quotas non attestés")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
