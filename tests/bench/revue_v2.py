"""Avis humains séparés et révisions auditables ; aucun auteur automatique."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from bench import etude_v2
from bench.journal import Journal

AXES = {"exactitude", "applicabilite", "fidelite_sources", "conclusion", "abstention"}


def axes_valides(value: object) -> bool:
    return isinstance(value, dict) and set(value) == AXES and all(x in ("correct", "faux", "indetermine") for x in value.values())


def avis(path: Path | None, resultats: dict, juges: dict) -> dict:
    """Une révision est liée au résultat, au juge et à l'avis humain précédent."""
    from bench.campaign import digest
    latest = {}
    for r in etude_v2.lire(path) if path is not None else []:
        key = r.get("identite")
        if key not in resultats or key not in juges:
            raise ValueError("avis humain orphelin")
        prev = latest.get(key)
        try:
            day = dt.date.fromisoformat(r["date_validation"])
            if day > dt.datetime.now(dt.timezone.utc).date() or (prev and day < dt.date.fromisoformat(prev["date_validation"])):
                raise ValueError()
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError("date humaine ISO requise") from exc
        if (not r.get("relecteur_humain", "").strip() or not r.get("justification_humaine", "").strip()
                or r.get("validation_humaine") is not True or r.get("avis_final") is not True
                or r.get("arbitrage") not in ("confirmer_juge", "corriger_juge") or not axes_valides(r.get("axes"))):
            raise ValueError("arbitrage humain explicite et justifié requis")
        if r.get("revision") != (prev["revision"] + 1 if prev else 1) or r.get("precedent_sha256") != (digest(prev) if prev else ""):
            raise ValueError("révision humaine rompue ou dupliquée")
        if r.get("resultat_sha256") != digest(resultats[key]) or r.get("jugement_sha256") != digest(juges[key]):
            raise ValueError("avis humain périmé")
        if r["arbitrage"] == "confirmer_juge" and r["axes"] != juges[key].get("axes"):
            raise ValueError("confirmation humaine différente du jugement")
        if r["arbitrage"] == "corriger_juge" and r["axes"] == juges[key].get("axes"):
            raise ValueError("correction humaine sans changement d'axes")
        latest[key] = r
    return latest


def ajouter(path: Path, row: dict, resultats: dict, juges: dict, *, state: Path, charger=None) -> None:
    """Le fichier d'entrée est rédigé par l'humain ; aucun champ complété ici."""
    from bench.campaign import confiner
    confiner(path, state)
    with etude_v2.verrou(state):
        if charger is not None:
            resultats, juges = charger()
        old = etude_v2.lire(path)
        # Valider la chaîne entière avant de réserver la nouvelle ligne.
        import tempfile
        import json
        with tempfile.TemporaryDirectory(dir=state) as d:
            check = Path(d) / "avis.jsonl"
            check.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in old + [row]), encoding="utf-8", newline="\n")
            avis(check, resultats, juges)
        Journal(path).ajouter(row)
