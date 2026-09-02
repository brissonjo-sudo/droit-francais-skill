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
  porte au moins un défaut, **un réveil d'instance au-delà du seuil d'alerte
  ou un p95 à chaud supérieur à 2 s**, ou si sa couverture est insuffisante —
  c'est le verdict de la période d'observation, et il reprend les quatre
  conditions écrites dans
  ``docs/exploitation.md``.

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
SEUIL_DERIVE_P95_S = 2.0
ECART_MAX_COUVERTURE = dt.timedelta(hours=6)


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
    if "health_code_chaud" in mesure:
        # Un appel qui n'a pas abouti mesure la vitesse d'un refus, pas celle
        # du service : l'inclure ferait baisser la médiane pendant une panne.
        if mesure.get("health_code_chaud") != 200:
            return None
        chaud = mesure.get("health_latence_chaud_s")
        return float(chaud) if isinstance(chaud, (int, float)) else None
    chaud = mesure.get("health_latence_chaud_s")
    if isinstance(chaud, (int, float)):
        return float(chaud)
    latence = mesure.get("health_latence_s")
    if isinstance(latence, (int, float)) and _reveil_s(mesure) is None:
        return float(latence)
    return None


def _defauts_effectifs(mesure: dict) -> list[str]:
    """Retire seulement l'ancien faux défaut de latence requalifié en réveil.

    Avant le double appel, une latence lente était toujours enregistrée comme
    panne. Si cette ancienne mesure est maintenant reconnaissable comme réveil,
    ce diagnostic historique devient caduc ; tout autre défaut (HTTP, OAuth,
    charge invalide…) reste bloquant.
    """
    defauts = [str(d) for d in (mesure.get("defauts") or [])]
    if "reveil" in mesure or _reveil_s(mesure) is None:
        return defauts
    return [
        d
        for d in defauts
        if not (d.startswith("latence de ") and "service indisponible" in d)
    ]


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


def _defauts_couverture(
    moments: list[dt.datetime],
    jours: int | None,
    maintenant: dt.datetime | None = None,
) -> list[str]:
    """Refuse qu'une fenêtre vide ou trouée soit présentée comme observée.

    Le cron GitHub est en meilleur effort. Une tolérance de six heures couvre
    ses retards mesurés (deux à quatre heures) sans permettre qu'une poignée de
    mesures fasse artificiellement foi pour sept jours.
    """
    if jours is None:
        return []
    if not moments:
        return [f"aucune mesure exploitable sur les {jours} derniers jours"]
    maintenant = maintenant or dt.datetime.now(dt.timezone.utc)
    ordonnes = sorted(moments)
    defauts = []
    debut_attendu = maintenant - dt.timedelta(days=jours)
    if ordonnes[0] > debut_attendu + ECART_MAX_COUVERTURE:
        defauts.append(
            f"début de fenêtre trop récent ({ordonnes[0]:%Y-%m-%d %H:%M} UTC)"
        )
    if maintenant - ordonnes[-1] > ECART_MAX_COUVERTURE:
        defauts.append(
            f"dernière mesure trop ancienne ({ordonnes[-1]:%Y-%m-%d %H:%M} UTC)"
        )
    for precedent, suivant in zip(ordonnes, ordonnes[1:]):
        ecart = suivant - precedent
        if ecart > ECART_MAX_COUVERTURE:
            defauts.append(
                f"trou de {ecart.total_seconds() / 3600:.1f} h entre "
                f"{precedent:%Y-%m-%d %H:%M} et {suivant:%Y-%m-%d %H:%M} UTC"
            )
    return defauts


def resumer(mesures: list[dict], jours: int | None) -> tuple[str, int]:
    """Rend le résumé Markdown et le nombre de conditions bloquantes.

    Sont bloquants : une couverture insuffisante, au moins un défaut, un réveil
    d'instance au-delà du seuil d'alerte, ou un p95 à chaud au-delà de la
    référence. Le résultat ne cherche pas à compter deux fois une même mesure ;
    le CLI n'utilise que zéro/non-zéro.
    """
    fenetre = f"{jours} derniers jours" if jours else "toute la série"
    if not mesures:
        couverture = _defauts_couverture([], jours)
        lignes = [f"## Surveillance — {fenetre}", "", "Aucune mesure."]
        if couverture:
            lignes += ["", "- **Couverture insuffisante** : " + couverture[0]]
        return "\n".join(lignes) + "\n", int(bool(couverture))

    # La latence qui décrit le service est celle à chaud : la première mesure
    # peut n'être qu'un démarrage d'instance.
    latences = [v for v in (_latence_chaud(m) for m in mesures) if v is not None]
    en_defaut = [(m, _defauts_effectifs(m)) for m in mesures if _defauts_effectifs(m)]
    duree_reveils = [d for d in (_reveil_s(m) for m in mesures) if d is not None]
    reveils = len(duree_reveils)
    reveils_graves = [d for d in duree_reveils if d > SEUIL_ALERTE_S]
    indisponibles = sum(1 for v in latences if v > SEUIL_ALERTE_S)
    moments = [m for m in (_horodatage(x) for x in mesures) if m is not None]
    defauts_couverture = _defauts_couverture(moments, jours)
    versions = sorted({str(m.get("version")) for m in mesures if m.get("version")})

    lignes = [f"## Surveillance — {fenetre}", ""]
    if moments:
        lignes.append(
            f"- Période : du {min(moments):%Y-%m-%d %H:%M} au "
            f"{max(moments):%Y-%m-%d %H:%M} UTC"
        )
    lignes.append(f"- Mesures : {len(mesures)}")
    if defauts_couverture:
        lignes.append("- **Couverture : INSUFFISANTE**")
        lignes.extend(f"  - {d}" for d in defauts_couverture)
    elif jours is not None:
        lignes.append("- Couverture : complète (aucun trou supérieur à 6 h)")
    lignes.append(f"- Versions vues : {', '.join(versions) or '?'}")
    lignes.append(
        f"- Défauts : **{len(en_defaut)}**"
        + ("" if not en_defaut else " — voir ci-dessous")
    )
    p95 = centile(latences, 0.95) if latences else None
    derive_p95 = p95 is not None and p95 > SEUIL_DERIVE_P95_S
    if latences:
        lignes.append(
            f"- Latence `/health` à chaud ({len(latences)} mesures) : "
            f"médiane {centile(latences, 0.5):.2f} s, "
            f"p95 {p95:.2f} s, max {max(latences):.2f} s"
        )
        lignes.append(
            f"- Indisponibilités à chaud (> {SEUIL_ALERTE_S:g} s) : {indisponibles}"
        )
        if derive_p95:
            lignes.append(
                f"- **Dérive bloquante : p95 à chaud > {SEUIL_DERIVE_P95_S:g} s**"
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
        # Nom distinct de « p95 » : celui de la fenêtre est un float déjà
        # calculé, et le réutiliser ici en ferait silencieusement une chaîne.
        p95_jour = f"{centile(lat, 0.95):.2f}" if lat else "—"
        lignes.append(
            f"| {jour} | {len(du_jour)} | "
            f"{sum(1 for m in du_jour if _defauts_effectifs(m))} | "
            f"{p95_jour} | {len(eveils)} | {pire} |"
        )

    if en_defaut:
        lignes += ["", "### Défauts relevés (les 10 derniers)", ""]
        for mesure, defauts in en_defaut[-10:]:
            quand = mesure.get("horodatage", "?")
            lignes.append(f"- `{quand}` — " + " ; ".join(defauts))

    conditions_bloquantes = sum(
        (bool(en_defaut), bool(reveils_graves), derive_p95, bool(defauts_couverture))
    )
    return "\n".join(lignes) + "\n", conditions_bloquantes


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
            "Code de sortie 1 si la couverture est insuffisante ou si la fenêtre "
            "porte un défaut, un réveil grave ou une dérive du p95 à chaud."
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
