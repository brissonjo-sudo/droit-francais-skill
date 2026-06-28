#!/usr/bin/env python3
"""run_eval.py — harnais d'évaluation du skill recherche-juridique.

Lit `eval-modes-erreur.csv` (une sonde par mode d'erreur + contrôles
transverses) et vérifie le comportement du skill.

Deux modes
----------
1. Hors-ligne (défaut) — n'appelle aucun modèle : affiche chaque sonde, le
   comportement attendu et les motifs (regex) attendus/interdits. Sert de
   check-list reproductible pour une évaluation manuelle.

2. En direct (`--live`) — envoie chaque sonde à l'API Anthropic en utilisant
   `skill/SKILL.md` comme prompt système, puis applique les heuristiques
   regex. Variables d'environnement :
       ANTHROPIC_API_KEY   (obligatoire en --live)
       ANTHROPIC_MODEL     (optionnel ; défaut : claude-opus-4-8)
   Aucune dépendance externe : appel HTTP via urllib.

Heuristique de réussite (par sonde)
-----------------------------------
    PASS  ⇔  (motifs_attendus vide OU au moins un attendu présent)
             ET (motifs_interdits vide OU aucun interdit présent)

Les regex sont insensibles à la casse. Un motif « attendu » est une
alternation (``a|b|c``) : une seule branche suffit.

Usage
-----
    python tests/run_eval.py                 # check-list hors-ligne
    python tests/run_eval.py --live          # éval réelle via l'API
    python tests/run_eval.py --live --model claude-opus-4-8
    python tests/run_eval.py --only 1,5,P    # sous-ensemble de modes

Code de sortie : 0 si toutes les sondes exécutées passent (ou mode hors-ligne),
1 si au moins une sonde échoue en --live.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = Path(__file__).resolve().parent / "eval-modes-erreur.csv"
SKILL_PATH = ROOT / "skill" / "SKILL.md"
API_URL = "https://api.anthropic.com/v1/messages"


def load_cases(only: set[str] | None) -> list[dict]:
    with CSV_PATH.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if only:
        rows = [r for r in rows if r["Mode"] in only]
    return rows


def check(text: str, attendus: str, interdits: str) -> tuple[bool, str]:
    """Applique les heuristiques regex et renvoie (pass, explication)."""
    reasons = []
    ok = True
    if attendus.strip():
        if re.search(attendus, text, re.IGNORECASE):
            reasons.append("attendu ✓")
        else:
            ok = False
            reasons.append(f"attendu manquant ({attendus})")
    if interdits.strip():
        m = re.search(interdits, text, re.IGNORECASE)
        if m:
            ok = False
            reasons.append(f"interdit présent ({m.group(0)!r})")
        else:
            reasons.append("interdit absent ✓")
    return ok, " ; ".join(reasons)


def call_model(system: str, prompt: str, model: str, api_key: str) -> str:
    body = json.dumps(
        {
            "model": model,
            "max_tokens": 2048,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return "".join(
        block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
    )


def run_offline(cases: list[dict]) -> int:
    print(f"Check-list hors-ligne — {len(cases)} sonde(s)\n" + "=" * 60)
    for c in cases:
        print(f"\n[Mode {c['Mode']}] {c['Intitule']}")
        print(f"  Sonde     : {c['Question sonde']}")
        print(f"  Attendu   : {c['Comportement attendu']}")
        print(f"  Motifs ✓  : {c['Motifs attendus'] or '—'}")
        print(f"  Motifs ✗  : {c['Motifs interdits'] or '—'}")
    print("\n" + "=" * 60)
    print("Mode hors-ligne : exécuter chaque sonde manuellement (ou --live).")
    return 0


def run_live(cases: list[dict], model: str) -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY manquant pour le mode --live.", file=sys.stderr)
        return 2
    if not SKILL_PATH.exists():
        print(f"❌ SKILL.md introuvable : {SKILL_PATH}", file=sys.stderr)
        return 2
    system = SKILL_PATH.read_text(encoding="utf-8")
    print(f"Éval en direct — modèle {model} — {len(cases)} sonde(s)\n" + "=" * 60)
    failures = 0
    for c in cases:
        try:
            answer = call_model(system, c["Question sonde"], model, api_key)
        except urllib.error.HTTPError as exc:
            print(f"[Mode {c['Mode']}] ❌ HTTP {exc.code}: {exc.read()[:200]!r}")
            failures += 1
            continue
        except urllib.error.URLError as exc:
            print(f"[Mode {c['Mode']}] ❌ réseau: {exc.reason}")
            failures += 1
            continue
        ok, why = check(answer, c["Motifs attendus"], c["Motifs interdits"])
        status = "✅ PASS" if ok else "❌ FAIL"
        if not ok:
            failures += 1
        print(f"[Mode {c['Mode']}] {status} — {c['Intitule']}")
        print(f"    {why}")
        if not ok:
            print(f"    extrait : {answer[:200].replace(chr(10), ' ')}…")
    print("\n" + "=" * 60)
    total = len(cases)
    print(f"Résultat : {total - failures}/{total} sondes passées.")
    return 1 if failures else 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Éval du skill recherche-juridique.")
    p.add_argument("--live", action="store_true", help="Appeler l'API Anthropic.")
    p.add_argument(
        "--model",
        default=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8"),
        help="Modèle (défaut : claude-opus-4-8 ou $ANTHROPIC_MODEL).",
    )
    p.add_argument("--only", help="Sous-ensemble de modes, ex. '1,5,P'.")
    args = p.parse_args(argv)
    only = {s.strip() for s in args.only.split(",")} if args.only else None
    cases = load_cases(only)
    if not cases:
        print("Aucune sonde sélectionnée.", file=sys.stderr)
        return 2
    return run_live(cases, args.model) if args.live else run_offline(cases)


if __name__ == "__main__":
    sys.exit(main())
