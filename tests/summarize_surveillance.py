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
  porte au moins un défaut **ou un réveil d'instance au-delà du seuil
  d'alerte** — c'est le verdict de la période d'observation, et il reprend les
  deux conditions écrites dans ``docs/exploitation.md``.

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

#: Mêmes seuils que la sonde : au-delà du premier, la mesure sort de la
#: référence à chaud ; au-delà du second, un client MCP a renoncé.
SEUIL_REVEIL_S = 2.0
SEUIL_ALERTE_S = 30.0


def _reveil_s(mesure: dict) -> float | None:
    """Durée du réveil consigné par la mesure, si elle en porte un.

    Les mesures antérieures au 2 septembre 2026 n'ont pas de champ ``reveil`` :
    la sonde ne faisait qu'un appel et rangeait un démarrage d'instance parmi
    les défauts. Elles sont relues sur leur latence, faute de mieux, pour que
    la série reste continue.
    """
    latence = mesure.get("health_latence_s")
    if not isinstance(latence, (int, float)):
        return None
    if "reveil" in mesure:
        return float(latence) if mesure.get("reveil") else None
    return float(latence) if latence > SEUIL_REVEIL_S else None


def _latence_chaud(mesure: dict) -> float | None:
    """Latence du service hors démarrage d'instance, ou ``None`` si inconnue.

    Une mesure d'avant le 2 septembre 2026 ne porte qu'un appel. S'il fut
    rapide, il vaut mesure à chaud. S'il fut lent, on ne sait pas départager un
    réveil d'une lenteur réelle : la mesure est écartée des statistiques plutôt
    que comptée deux fois, en réveil et en indisponibilité.
    """
    chaud = mesure.get("health_latence_chaud_s")
    if isinstance(chaud, (int, float)):
        return float(chaud)
    latence = mesure.get("health_latence_s")
    if isinstance(latence, (int, float)) and _reveil_s(mesure) is None:
        return float(latence)
    return None


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
    """Rend le résumé Markdown et le nombre de mesures bloquantes.

    Est bloquante une mesure en défaut, **et** un réveil d'instance au-delà du
    seuil d'alerte : le critère de publication écrit dans `exploitation.md`
    exige les deux, et un réveil de trente secondes suffit à faire conclure à
    un relecteur que le service ne fonctionne pas.
    """
    fenetre = f"{jours} derniers jours" if jours else "toute la série"
    if not mesures:
        return f"## Surveillance — {fenetre}\n\nAucune mesure.\n", 0

    # La latence qui décrit le service est celle à chaud : la première mesure
    # peut n'être qu'un démarrage d'instance.
    latences = [v for v in (_latence_chaud(m) for m in mesures) if v is not None]
    en_defaut = [m for m in mesures if m.get("defauts")]
    duree_reveils = [d for d in (_reveil_s(m) for m in mesures) if d is not None]
    reveils = len(duree_reveils)
    reveils_graves = [d for d in duree_reveils if d > SEUIL_ALERTE_S]
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
            f"- Latence `/health` à chaud ({len(latences)} mesures) : "
            f"médiane {centile(latences, 0.5):.2f} s, "
            f"p95 {centile(latences, 0.95):.2f} s, max {max(latences):.2f} s"
        )
        lignes.append(
            f"- Indisponibilités à chaud (> {SEUIL_ALERTE_S:g} s) : {indisponibles}"
        )
    if duree_reveils:
        lignes.append(
            f"- **Réveils d'instance : {reveils}**, de {min(duree_reveils):.1f} à "
            f"{max(duree_reveils):.1f} s — dont **{len(reveils_graves)} au-delà de "
            f"{SEUIL_ALERTE_S:g} s**"
        )
    else:
        lignes.append("- Réveils d'instance : aucun")

    par_jour: dict[str, list[dict]] = defaultdict(list)
    for mesure in mesures:
        moment = _horodatage(mesure)
        par_jour[moment.strftime("%Y-%m-%d") if moment else "sans date"].append(mesure)
    lignes += [
        "",
        "| Jour | Mesures | Défauts | p95 à chaud (s) | Réveils | Réveil max (s) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for jour in sorted(par_jour):
        du_jour = par_jour[jour]
        lat = [v for v in (_latence_chaud(m) for m in du_jour) if v is not None]
        eveils = [d for d in (_reveil_s(m) for m in du_jour) if d is not None]
        pire = f"{max(eveils):.1f}" if eveils else "—"
        p95 = f"{centile(lat, 0.95):.2f}" if lat else "—"
        lignes.append(
            f"| {jour} | {len(du_jour)} | "
            f"{sum(1 for m in du_jour if m.get('defauts'))} | "
            f"{p95} | {len(eveils)} | {pire} |"
        )

    if en_defaut:
        lignes += ["", "### Défauts relevés (les 10 derniers)", ""]
        for mesure in en_defaut[-10:]:
            quand = mesure.get("horodatage", "?")
            lignes.append(f"- `{quand}` — " + " ; ".join(str(d) for d in mesure["defauts"]))

    return "\n".join(lignes) + "\n", len(en_defaut) + len(reveils_graves)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Résume une série de mesures de check_service_health.py --json"
    )
    parser.add_argument("journal", help="Fichier JSONL, ou - pour l'entrée standard.")
    parser.add_argument("--jours", type=int, help="Ne retenir que les N derniers jours.")
    parser.add_argument(
        "--exiger-sans-defaut",
        action="store_true",
        help=(
            "Code de sortie 1 si la fenêtre porte un défaut ou un réveil "
            "au-delà du seuil d'alerte."
        ),
    )
    args = parser.parse_args()

    mesures = filtrer(lire(args.journal), args.jours)
    texte, bloquantes = resumer(mesures, args.jours)
    print(texte)
    if args.exiger_sans_defaut and bloquantes:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
