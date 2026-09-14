#!/usr/bin/env python3
"""resume.py — agrégats, résumé Markdown et comparaison à une baseline.

Reprend le patron de `summarize_surveillance.py` : lire un JSONL, en tirer un
Markdown lisible dans `$GITHUB_STEP_SUMMARY`, et rendre un code de sortie qui
bloque sur seuil.

Deux principes de lecture :

- **Un mode, pas un cas.** Avec trois sondes par mode et plusieurs
  répétitions, le score qui compte est celui du mode ; un cas isolé qui bascule
  est du bruit.
- **Une régression, c'est un cas-équivalent perdu.** Avec trois sondes et trois
  répétitions, un mode vaut 9 runs : une baisse d'un neuvième est un
  basculement réel, en deçà c'est la variance du modèle.

Les `infra_error` sont comptés à part et **exclus** des taux : une instance
endormie ne dit rien de la méthode.

Stdlib uniquement.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bench.journal import lire  # noqa: E402

# Un cas-équivalent sur 9 runs par mode (3 sondes × 3 répétitions). Une baisse
# d'exactement un cas-équivalent reste de la variance ; il faut la dépasser.
SEUIL_REGRESSION = 1.0 / 9.0

# Tolérance de comparaison : `8/9 - 9/9` vaut -0.11111111111111116 en binaire,
# soit un cheveu de plus que `1/9`. Sans elle, le basculement d'un seul run
# serait déclaré régression — exactement ce que le seuil vise à écarter.
EPSILON = 1e-9


def centile(valeurs: list[float], fraction: float) -> float:
    """Centile par interpolation basse, comme `summarize_surveillance`."""
    if not valeurs:
        return 0.0
    ordonnees = sorted(valeurs)
    if len(ordonnees) == 1:
        return ordonnees[0]
    position = fraction * (len(ordonnees) - 1)
    bas = int(position)
    haut = min(bas + 1, len(ordonnees) - 1)
    poids = position - bas
    return ordonnees[bas] * (1 - poids) + ordonnees[haut] * poids


def agreger(lignes: list[dict[str, Any]]) -> dict[str, Any]:
    """Calcule les agrégats d'un run, par bras et par mode."""
    exploitables = [l for l in lignes if l.get("statut") != "infra_error"]
    pannes = [l for l in lignes if l.get("statut") == "infra_error"]

    par_bras_mode: dict[tuple[str, str], list[bool]] = defaultdict(list)
    par_bras: dict[str, list[bool]] = defaultdict(list)
    verdicts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    durees: dict[str, list[float]] = defaultdict(list)
    couts: dict[str, float] = defaultdict(float)
    abstentions: dict[str, list[bool]] = defaultdict(list)

    for ligne in exploitables:
        bras = str(ligne.get("bras", "?"))
        mode = str(ligne.get("mode", "?"))
        reussi = bool(ligne.get("pass"))
        par_bras_mode[(bras, mode)].append(reussi)
        par_bras[bras].append(reussi)
        for nom, statut in (ligne.get("verdicts") or {}).items():
            verdicts[nom][statut] += 1
        duree = ligne.get("duration_ms")
        if isinstance(duree, (int, float)) and duree > 0:
            durees[bras].append(float(duree))
        cout = ligne.get("total_cost_usd")
        if isinstance(cout, (int, float)):
            couts[bras] += float(cout)
        if bras in ("A", "B"):
            # Sur un bras sans outil, ne citer aucun identifiant non tracé est
            # le comportement recherché : c'est l'abstention correcte.
            abstentions[bras].append(not ligne.get("identifiants_non_traces"))

    return {
        "runs": len(lignes),
        "exploitables": len(exploitables),
        "pannes": len(pannes),
        "motifs_pannes": _compter(l.get("motif_infra", "?") for l in pannes),
        "taux_bras": {b: _taux(v) for b, v in sorted(par_bras.items())},
        "taux_bras_mode": {f"{b}/{m}": _taux(v) for (b, m), v in sorted(par_bras_mode.items())},
        "effectif_bras_mode": {f"{b}/{m}": len(v) for (b, m), v in sorted(par_bras_mode.items())},
        "verdicts": {n: dict(s) for n, s in sorted(verdicts.items())},
        "duree_mediane_ms": {b: centile(v, 0.5) for b, v in sorted(durees.items())},
        "duree_p95_ms": {b: centile(v, 0.95) for b, v in sorted(durees.items())},
        "cout_usd": dict(sorted(couts.items())),
        "abstention_correcte": {b: _taux(v) for b, v in sorted(abstentions.items())},
        "modeles": sorted({str(l.get("modele", "")) for l in lignes if l.get("modele")}),
        "skill_sha256": sorted({str(l.get("skill_sha256", "")) for l in lignes if l.get("skill_sha256")}),
    }


def _taux(valeurs: list[bool]) -> float:
    return (sum(1 for v in valeurs if v) / len(valeurs)) if valeurs else 0.0


def _compter(valeurs) -> dict[str, int]:
    compte: dict[str, int] = defaultdict(int)
    for valeur in valeurs:
        compte[str(valeur)] += 1
    return dict(sorted(compte.items(), key=lambda kv: -kv[1]))


def comparer(courant: dict[str, Any], baseline: dict[str, Any]) -> list[dict[str, Any]]:
    """Deltas par bras×mode, régressions d'abord."""
    deltas: list[dict[str, Any]] = []
    cles = set(courant["taux_bras_mode"]) | set(baseline["taux_bras_mode"])
    for cle in sorted(cles):
        avant = baseline["taux_bras_mode"].get(cle)
        apres = courant["taux_bras_mode"].get(cle)
        if avant is None or apres is None:
            deltas.append({"cle": cle, "avant": avant, "apres": apres, "delta": None, "etat": "absent"})
            continue
        ecart = apres - avant
        if ecart < -(SEUIL_REGRESSION + EPSILON):
            etat = "régression"
        elif ecart > SEUIL_REGRESSION + EPSILON:
            etat = "progrès"
        else:
            etat = "stable"
        deltas.append({"cle": cle, "avant": avant, "apres": apres, "delta": ecart, "etat": etat})
    deltas.sort(key=lambda d: (d["etat"] != "régression", d["cle"]))
    return deltas


def rendre(agregats: dict[str, Any], deltas: list[dict[str, Any]] | None = None) -> str:
    """Résumé Markdown."""
    lignes = ["# Benchmark agentique — résumé", ""]

    if agregats["skill_sha256"]:
        empreintes = ", ".join(s[:12] for s in agregats["skill_sha256"])
        lignes.append(f"- Empreinte `skill/SKILL.md` : `{empreintes}`")
    if agregats["modeles"]:
        lignes.append(f"- Modèle(s) évalué(s) : {', '.join(agregats['modeles'])}")
    lignes.append(
        f"- {agregats['exploitables']} run(s) exploitable(s) sur {agregats['runs']}"
        f" — {agregats['pannes']} panne(s) d'infrastructure"
    )
    if agregats["motifs_pannes"]:
        details = ", ".join(f"{m} ×{n}" for m, n in agregats["motifs_pannes"].items())
        lignes.append(f"- Motifs de panne : {details}")
    lignes.append("")

    lignes += ["## Taux de réussite par bras", "", "| Bras | Réussite | Durée médiane | p95 | Coût |", "|---|---|---|---|---|"]
    for bras, taux in agregats["taux_bras"].items():
        mediane = agregats["duree_mediane_ms"].get(bras, 0) / 1000
        p95 = agregats["duree_p95_ms"].get(bras, 0) / 1000
        cout = agregats["cout_usd"].get(bras, 0.0)
        lignes.append(f"| {bras} | {taux:.0%} | {mediane:.0f} s | {p95:.0f} s | {cout:.2f} $ |")
    lignes.append("")

    if agregats["abstention_correcte"]:
        lignes += ["## Abstention correcte (bras sans outil)", ""]
        for bras, taux in agregats["abstention_correcte"].items():
            lignes.append(f"- Bras {bras} : {taux:.0%} des réponses ne citent aucun identifiant non tracé")
        lignes.append("")

    lignes += ["## Verdicts déterministes", "", "| Contrôle | PASS | FAIL | Sans objet |", "|---|---|---|---|"]
    for nom, statuts in agregats["verdicts"].items():
        lignes.append(
            f"| {nom} | {statuts.get('PASS', 0)} | {statuts.get('FAIL', 0)} | {statuts.get('SANS_OBJET', 0)} |"
        )
    lignes.append("")

    lignes += ["## Réussite par bras et par mode", "", "| Bras / mode | Réussite | Runs |", "|---|---|---|"]
    for cle, taux in agregats["taux_bras_mode"].items():
        effectif = agregats["effectif_bras_mode"].get(cle, 0)
        lignes.append(f"| {cle} | {taux:.0%} | {effectif} |")
    lignes.append("")

    if deltas:
        regressions = [d for d in deltas if d["etat"] == "régression"]
        lignes += ["## Comparaison à la baseline", ""]
        lignes.append(
            f"{len(regressions)} régression(s) au-delà du seuil d'un cas-équivalent "
            f"({SEUIL_REGRESSION:.0%})."
        )
        lignes += ["", "| Bras / mode | Avant | Après | Delta | État |", "|---|---|---|---|---|"]
        for delta in deltas:
            if delta["etat"] == "stable":
                continue
            avant = f"{delta['avant']:.0%}" if delta["avant"] is not None else "—"
            apres = f"{delta['apres']:.0%}" if delta["apres"] is not None else "—"
            ecart = f"{delta['delta']:+.0%}" if delta["delta"] is not None else "—"
            lignes.append(f"| {delta['cle']} | {avant} | {apres} | {ecart} | {delta['etat']} |")
        lignes.append("")

    return "\n".join(lignes)


def main(argv: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(description="Résume un run de benchmark agentique.")
    analyseur.add_argument("source", help="JSONL produit par run_bench.py")
    analyseur.add_argument("--baseline", help="JSONL de référence à comparer")
    analyseur.add_argument("--json", action="store_true", help="Sortie JSON des agrégats.")
    analyseur.add_argument(
        "--regressions-acceptees",
        default="",
        help="Clés bras/mode dont la régression est assumée (séparées par des virgules).",
    )
    arguments = analyseur.parse_args(argv)

    lignes = lire(arguments.source)
    if not lignes:
        print(f"❌ aucun run exploitable dans {arguments.source}", file=sys.stderr)
        return 2

    agregats = agreger(lignes)
    deltas = None
    if arguments.baseline:
        reference = lire(arguments.baseline)
        if not reference:
            print(f"❌ baseline vide : {arguments.baseline}", file=sys.stderr)
            return 2
        deltas = comparer(agregats, agreger(reference))

    if arguments.json:
        print(json.dumps({"agregats": agregats, "deltas": deltas}, ensure_ascii=False))
    else:
        print(rendre(agregats, deltas))

    if deltas:
        acceptees = {c.strip() for c in arguments.regressions_acceptees.split(",") if c.strip()}
        bloquantes = [d for d in deltas if d["etat"] == "régression" and d["cle"] not in acceptees]
        if bloquantes:
            print(
                "❌ régression(s) non expliquée(s) : " + ", ".join(d["cle"] for d in bloquantes),
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
