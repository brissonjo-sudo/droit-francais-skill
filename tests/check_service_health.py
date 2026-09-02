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

``/health`` est mesuré **deux fois de suite**, et c'est le second appel qui dit
si le service va bien. Une instance qui dort rend la première mesure sans
rapport avec son état : les 1er et 2 septembre 2026, quatre réveils de 32,4 à
32,7 s ont été consignés comme « service indisponible en pratique » alors que
le service répondait en 0,2 s à la requête suivante. Un réveil et une panne
demandent des décisions opposées — changer d'hébergement dans un cas, ouvrir un
incident dans l'autre — donc la sonde les sépare : un premier appel lent suivi
d'un appel rapide est un **réveil**, signalé avec sa durée et sans faire échouer
la sonde ; un second appel lent est une **latence à chaud**, qui reste un
défaut.
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
#: MCP aura renoncé bien avant. Appliqué à la latence **à chaud** ; sur la
#: première mesure, ce seuil qualifie la gravité du réveil sans le requalifier
#: en panne.
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

    sante = f"{base_url}/health"
    code, duree, _charge = _mesurer(sante)
    rapport["health_code"] = code
    rapport["health_latence_s"] = round(duree, 3)
    if code != 200:
        rapport["defauts"].append(f"/health répond {code}")

    # Second appel immédiat : c'est lui qui porte l'état réel du service, la
    # première mesure ayant pu ne mesurer qu'un démarrage d'instance.
    code_chaud, duree_chaud, charge_chaud = _mesurer(sante)
    rapport["health_code_chaud"] = code_chaud
    rapport["health_latence_chaud_s"] = round(duree_chaud, 3)
    if code_chaud != 200:
        rapport["defauts"].append(f"/health répond {code_chaud} au second appel")
    else:
        # Le second appel décrit l'instance réellement disponible. Valider sa
        # charge — et non celle du réveil — évite à la fois un faux négatif si
        # la configuration chaude est mauvaise, et un faux positif si la
        # première réponse transitoire est incomplète.
        rapport["version"] = (charge_chaud or {}).get("version")
        rapport["auth"] = (charge_chaud or {}).get("auth")
        if not rapport["version"]:
            rapport["defauts"].append("version absente de /health au second appel")
        if rapport["auth"] != "oauth":
            rapport["defauts"].append(
                "authentification au second appel en mode "
                f"{rapport['auth']!r} au lieu de « oauth »"
            )

    reveil = duree > SEUIL_REVEIL_S and duree_chaud <= SEUIL_REVEIL_S
    rapport["reveil"] = reveil
    rapport["reveil_s"] = round(duree, 3) if reveil else None
    if reveil:
        gravite = " au-delà du seuil d'alerte" if duree > SEUIL_ALERTE_S else ""
        rapport["avertissements"].append(
            f"réveil d'instance mesuré à {duree:.1f} s{gravite} ; "
            f"service à {duree_chaud:.2f} s à chaud"
        )
    elif duree_chaud > SEUIL_ALERTE_S:
        rapport["defauts"].append(
            f"latence à chaud de {duree_chaud:.1f} s : service indisponible en pratique"
        )
    elif duree_chaud > SEUIL_REVEIL_S:
        rapport["avertissements"].append(
            f"latence à chaud de {duree_chaud:.1f} s : au-delà de la référence"
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
        print(f"{'Latence à chaud':22}: {rapport['health_latence_chaud_s']} s")
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
