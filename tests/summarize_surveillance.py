#!/usr/bin/env python3
"""Résume une série de mesures de ``check_service_health.py --json``.

Une mesure isolée ne dit rien d'une latence ; c'est la série qui parle. Ce
script lit un journal JSONL — une ligne par exécution de la sonde — et rend un
résumé Markdown : nombre de mesures, défauts, latence médiane et au 95ᵉ
centile, réveils d'instance, ventilation par jour.

    python tests/summarize_surveillance.py surveillance.jsonl
    git show origin/surveillance:surveillance.jsonl | python tests/summarize_surveillance.py -

Options :

* ``--jours N`` ne retient que les mesures des N derniers jours (d'après leur
  horodatage) ;
* ``--exiger-sans-defaut`` rend un code de sortie 1 si la fenêtre retenue
  porte au moins un défaut — c'est le verdict de la période d'observation.

Sans dépendance externe.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

#: Mêmes seuils que la sonde : au-delà du premier, l'instance a probablement
#: été réveillée de veille ; au-delà du second, elle est indisponible en
#: pratique.
SEUIL_REVEIL_S = 2.0
SEUIL_ALERTE_S = 30.0


def lire(source: str) -> list[dict]:
    """Lit le journal (chemin ou ``-`` pour l'entrée standard), ligne à ligne.

    Une ligne illisible est comptée et ignorée plutôt que de faire échouer le
    résumé : un journal accumulé par un automate peut porter une ligne
    tronquée, et ce n'est pas une raison pour perdre les autres.
    """
    texte = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    mesures: list[dict] = []
    illisibles = 0
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        if not ligne:
            continue
        try:
            mesure = json.loads(ligne)
        except ValueError:
            illisibles += 1
            continue
        if isinstance(mesure, dict):
            mesures.append(mesure)
    if illisibles:
        print(f"> {illisibles} ligne(s) illisible(s) ignorée(s).\n")
    return mesures


def _horodatage(mesure: dict) -> dt.datetime | None:
    brut = mesure.get("horodatage")
    if not brut:
        return None
    try:
        moment = dt.datetime.fromisoformat(str(brut).replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=dt.timezone.utc)
    return moment


def filtrer(mesures: list[dict], jours: int | None) -> list[dict]:
    if not jours:
        return mesures
    limite = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=jours)
    retenues = []
    for mesure in mesures:
        moment = _horodatage(mesure)
        # Une mesure sans horodatage exploitable est conservée : l'exclure
        # ferait disparaître un défaut de la fenêtre par simple accident de
        # format.
        if moment is None or moment >= limite:
            retenues.append(mesure)
    return retenues


def centile(valeurs: list[float], fraction: float) -> float:
    if not valeurs:
        return 0.0
    ordonnees = sorted(valeurs)
    rang = max(0, min(len(ordonnees) - 1, round(fraction * (len(ordonnees) - 1))))
    return ordonnees[rang]


def resumer(mesures: list[dict], jours: int | None) -> tuple[str, int]:
    """Rend le résumé Markdown et le nombre de mesures en défaut."""
    fenetre = f"{jours} derniers jours" if jours else "toute la série"
    if not mesures:
        return f"## Surveillance — {fenetre}\n\nAucune mesure.\n", 0

    latences = [
        float(m["health_latence_s"])
        for m in mesures
        if isinstance(m.get("health_latence_s"), (int, float))
    ]
    en_defaut = [m for m in mesures if m.get("defauts")]
    reveils = sum(1 for v in latences if SEUIL_REVEIL_S < v <= SEUIL_ALERTE_S)
    indisponibles = sum(1 for v in latences if v > SEUIL_ALERTE_S)
    moments = [m for m in (_horodatage(x) for x in mesures) if m is not None]
    versions = sorted({str(m.get("version")) for m in mesures if m.get("version")})

    lignes = [f"## Surveillance — {fenetre}", ""]
    if moments:
        lignes.append(
            f"- Période : du {min(moments):%Y-%m-%d %H:%M} au "
            f"{max(moments):%Y-%m-%d %H:%M} UTC"
        )
    lignes.append(f"- Mesures : {len(mesures)}")
    lignes.append(f"- Versions vues : {', '.join(versions) or '?'}")
    lignes.append(
        f"- Défauts : **{len(en_defaut)}**"
        + ("" if not en_defaut else " — voir ci-dessous")
    )
    if latences:
        lignes.append(
            f"- Latence `/health` : médiane {centile(latences, 0.5):.2f} s, "
            f"p95 {centile(latences, 0.95):.2f} s, max {max(latences):.2f} s"
        )
        lignes.append(
            f"- Réveils probables (> {SEUIL_REVEIL_S:g} s) : {reveils} ; "
            f"indisponibilités (> {SEUIL_ALERTE_S:g} s) : {indisponibles}"
        )

    par_jour: dict[str, list[dict]] = defaultdict(list)
    for mesure in mesures:
        moment = _horodatage(mesure)
        par_jour[moment.strftime("%Y-%m-%d") if moment else "sans date"].append(mesure)
    lignes += ["", "| Jour | Mesures | Défauts | p95 (s) | Réveils |", "|---|---:|---:|---:|---:|"]
    for jour in sorted(par_jour):
        du_jour = par_jour[jour]
        lat = [
            float(m["health_latence_s"])
            for m in du_jour
            if isinstance(m.get("health_latence_s"), (int, float))
        ]
        lignes.append(
            f"| {jour} | {len(du_jour)} | {sum(1 for m in du_jour if m.get('defauts'))} | "
            f"{centile(lat, 0.95):.2f} | {sum(1 for v in lat if v > SEUIL_REVEIL_S)} |"
        )

    if en_defaut:
        lignes += ["", "### Défauts relevés (les 10 derniers)", ""]
        for mesure in en_defaut[-10:]:
            quand = mesure.get("horodatage", "?")
            lignes.append(f"- `{quand}` — " + " ; ".join(str(d) for d in mesure["defauts"]))

    return "\n".join(lignes) + "\n", len(en_defaut)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Résume une série de mesures de check_service_health.py --json"
    )
    parser.add_argument("journal", help="Fichier JSONL, ou - pour l'entrée standard.")
    parser.add_argument("--jours", type=int, help="Ne retenir que les N derniers jours.")
    parser.add_argument(
        "--exiger-sans-defaut",
        action="store_true",
        help="Code de sortie 1 si la fenêtre retenue porte au moins un défaut.",
    )
    args = parser.parse_args()

    mesures = filtrer(lire(args.journal), args.jours)
    texte, defauts = resumer(mesures, args.jours)
    print(texte)
    if args.exiger_sans_defaut and defauts:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
