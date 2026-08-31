#!/usr/bin/env python3
"""Sonde de surveillance du service déployé, sans jeton ni secret.

Destinée à l'exploitation courante : elle mesure la disponibilité et la latence
des routes publiques, et rejoue les contrôles de métadonnées OAuth. Elle
n'appelle aucun outil, donc ne consomme aucun quota PISTE — contrairement à
``check_live_tools.py``, qu'elle ne remplace pas.

    python tests/check_service_health.py
    python tests/check_service_health.py --json >> surveillance.jsonl

La sortie ``--json`` est une ligne par exécution, faite pour être accumulée et
relue : c'est ainsi qu'une dérive de latence devient visible, là où une mesure
isolée ne dit rien.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent
if str(ICI) not in sys.path:
    sys.path.insert(0, str(ICI))

from check_oauth_metadata import MetadataError, verify  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_PAR_DEFAUT = "https://droit-francais-skill.onrender.com"

#: Au-delà, la première requête a probablement réveillé une instance en veille.
#: Ce n'est pas une panne : c'est le comportement documenté d'une instance
#: Render gratuite, et la raison pour laquelle une revue publique demande une
#: instance qui ne s'endort pas.
SEUIL_REVEIL_S = 2.0

#: Au-delà, le service est considéré comme indisponible en pratique : un client
#: MCP aura renoncé bien avant.
SEUIL_ALERTE_S = 30.0

TIMEOUT = 90


def _mesurer(url: str) -> tuple[int, float, dict | None]:
    """Retourne (code HTTP, durée en secondes, charge JSON si lisible)."""
    debut = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as reponse:
            brut = reponse.read()
            duree = time.monotonic() - debut
            code = reponse.status
    except urllib.error.HTTPError as erreur:
        return erreur.code, time.monotonic() - debut, None
    try:
        return code, duree, json.loads(brut)
    except ValueError:
        return code, duree, None


def sonder(base_url: str) -> dict:
    """Collecte l'état du service. Ne lève pas : les défauts sont dans le rapport."""
    base_url = base_url.rstrip("/")
    rapport: dict = {"base_url": base_url, "defauts": [], "avertissements": []}

    code, duree, charge = _mesurer(f"{base_url}/health")
    rapport["health_code"] = code
    rapport["health_latence_s"] = round(duree, 3)
    if code != 200:
        rapport["defauts"].append(f"/health répond {code}")
    else:
        rapport["version"] = (charge or {}).get("version")
        rapport["auth"] = (charge or {}).get("auth")
        if rapport["auth"] != "oauth":
            rapport["defauts"].append(
                f"authentification en mode {rapport['auth']!r} au lieu de « oauth »"
            )

    if duree > SEUIL_ALERTE_S:
        rapport["defauts"].append(
            f"latence de {duree:.1f} s : service indisponible en pratique"
        )
    elif duree > SEUIL_REVEIL_S:
        rapport["avertissements"].append(
            f"latence de {duree:.1f} s : instance probablement réveillée de veille"
        )

    # Les contrôles de métadonnées et le refus anonyme sont déjà écrits et
    # éprouvés : les rejouer ici plutôt que d'en tenir une seconde version.
    # Sa sortie est capturée : ce module rend son propre rapport, et une ligne
    # parasite casserait le journal JSON que l'on accumule.
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            verify(base_url, expected_issuer=None, discover=True)
        rapport["metadonnees"] = "conformes"
    except MetadataError as exc:
        rapport["metadonnees"] = "defaut"
        rapport["defauts"].append(str(exc).splitlines()[0])
    except Exception as exc:
        rapport["metadonnees"] = "injoignable"
        rapport["defauts"].append(f"{type(exc).__name__} sur les métadonnées")

    return rapport


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Surveille la disponibilité et la latence du service déployé"
    )
    parser.add_argument("base_url", nargs="?", default=BASE_PAR_DEFAUT)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Sortie sur une ligne JSON, à accumuler dans un journal.",
    )
    parser.add_argument(
        "--horodatage",
        help="Horodatage ISO à inscrire dans la sortie JSON (fourni par l'appelant).",
    )
    args = parser.parse_args()

    rapport = sonder(args.base_url)
    if args.horodatage:
        rapport["horodatage"] = args.horodatage

    if args.json:
        print(json.dumps(rapport, ensure_ascii=False, sort_keys=True))
    else:
        etat = "ok" if not rapport["defauts"] else "DEFAUT"
        print(f"{'État':22}: {etat}")
        print(f"{'Version':22}: {rapport.get('version', '?')}")
        print(f"{'Authentification':22}: {rapport.get('auth', '?')}")
        print(f"{'Latence /health':22}: {rapport['health_latence_s']} s")
        print(f"{'Métadonnées OAuth':22}: {rapport.get('metadonnees', '?')}")
        for message in rapport["avertissements"]:
            print(f"⚠️  {message}")
        for message in rapport["defauts"]:
            print(f"❌ {message}")
        if not rapport["defauts"]:
            print("✅ Service disponible et conforme.")

    return 1 if rapport["defauts"] else 0


if __name__ == "__main__":
    sys.exit(main())
