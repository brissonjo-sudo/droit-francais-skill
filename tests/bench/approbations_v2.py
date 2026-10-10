"""Instantanés de preuves et approbations humaines explicitement auditables."""
from __future__ import annotations

from pathlib import Path
import datetime as dt
from bench import campaign, etude_v2
from bench.journal import Journal

CHAMPS = {"schema", "type", "famille", "series_sha256", "instantane", "resultats_sha256", "cree_utc",
    "valide_par", "justification", "preuve_isolation", "auth_confirmee", "autorise_collecte"}


def preuves(gel: dict, famille: str, type_recu: str, state: Path) -> dict:
    if famille not in campaign.FAMILLES or type_recu not in ("preflight", "pilote"):
        raise ValueError("type ou famille d'approbation inconnue")
    series = gel["series_sha256"]
    name = f"preflight-traces-{famille}.jsonl" if type_recu == "preflight" else f"pilote-{famille}.jsonl"
    rows = campaign.historique_acquis(state / series / name, state)
    if not rows:
        raise ValueError("preuves acquises manquantes")
    absent = etude_v2.manquants(state, series, phase="pilote") if type_recu == "pilote" else {}
    family_ids = {r["identite"] for r in etude_v2.reservations(state)
        if r["series_sha256"] == series and r.get("famille") == famille and r["phase"] == "pilote"}
    return {"resultats": rows, "manquants": [r for k, r in absent.items() if k in family_ids]}


def preparer(gel: dict, famille: str, type_recu: str, sortie: Path, *, state: Path = campaign.STATE) -> dict:
    with etude_v2.verrou(state):
        campaign.verifier_gel(gel)
        if sortie.exists():
            raise ValueError("instantané existant immuable")
        snapshot = preuves(gel, famille, type_recu, state)
        row = {"schema": 2, "type": type_recu, "famille": famille, "series_sha256": gel["series_sha256"],
            "instantane": snapshot, "resultats_sha256": campaign.digest(snapshot), "cree_utc": etude_v2.maintenant(),
            "valide_par": "", "justification": "", "preuve_isolation": "", "auth_confirmee": False, "autorise_collecte": False}
        campaign.write_json(campaign.confiner(sortie, state), row)
        return row


def historique(state: Path, serie: str) -> list[dict]:
    rows = etude_v2.lire(state / serie / "approbations.jsonl")
    previous = ""
    for row in rows:
        if row.get("precedent_sha256") != previous:
            raise ValueError("historique d'approbation rompu")
        previous = campaign.digest(row)
    return rows


def approuver(gel: dict, avis: dict, *, state: Path = campaign.STATE) -> None:
    if set(avis) - CHAMPS or avis.get("schema") != 2 or avis.get("series_sha256") != gel["series_sha256"]:
        raise ValueError("avis d'approbation invalide ou champ inconnu")
    if not avis.get("valide_par", "").strip() or not avis.get("justification", "").strip() or avis.get("autorise_collecte") is not True:
        raise ValueError("accord humain nommé, motivé et explicite requis")
    try:
        created = dt.datetime.fromisoformat(avis["cree_utc"])
        if created.utcoffset() != dt.timedelta(0) or created > dt.datetime.now(dt.timezone.utc):
            raise ValueError()
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("date UTC d'instantané valide et non future requise") from exc
    with etude_v2.verrou(state):
        snapshot = preuves(gel, avis["famille"], avis["type"], state)
        if avis.get("instantane") != snapshot or avis.get("resultats_sha256") != campaign.digest(snapshot):
            raise ValueError("instantané d'approbation périmé")
        if avis["type"] == "preflight" and (avis.get("auth_confirmee") is not True or not avis.get("preuve_isolation")):
            raise ValueError("authentification et preuve d'isolation humaines requises")
        if avis["type"] == "preflight":
            latest = campaign.dernieres_tentatives(snapshot["resultats"])
            if (len(latest) != 2 or {r["bras"] for r in latest} != {"A", "C"}
                    or any(r["statut_technique"] != "ok" for r in latest)
                    or not any(campaign.source_lue(r) for r in latest if r["bras"] == "C")):
                raise ValueError("deux bras techniques réussis et source lue requis")
        rows = historique(state, gel["series_sha256"])
        entry = {"schema": 2, "avis": avis, "approuve_utc": etude_v2.maintenant(),
            "revision": len(rows) + 1, "precedent_sha256": campaign.digest(rows[-1]) if rows else ""}
        Journal(state / gel["series_sha256"] / "approbations.jsonl").ajouter(entry)
        if avis["type"] == "preflight":
            path = state / gel["series_sha256"] / f"preflight-{avis['famille']}.json"
            receipt = campaign.read_json(path)
            receipt.update(revue_isolation_par=avis["valide_par"], preuve_isolation=avis["preuve_isolation"],
                auth_confirmee=True, autorise_collecte=True, approbation_sha256=campaign.digest(entry))
        else:
            path = state / gel["series_sha256"] / f"pilote-{avis['famille']}-revue.json"
            receipt = {**avis, "approbation_sha256": campaign.digest(entry)}
        campaign.write_json(path, receipt)


def verifier(recu: dict, gel: dict, famille: str, type_recu: str, state: Path) -> bool:
    matches = [r for r in historique(state, gel["series_sha256"]) if campaign.digest(r) == recu.get("approbation_sha256")]
    if len(matches) != 1:
        return False
    a = matches[0]["avis"]
    snapshot = preuves(gel, famille, type_recu, state)
    return (a["famille"] == famille and a["type"] == type_recu and a["instantane"] == snapshot
            and a["resultats_sha256"] == campaign.digest(snapshot) and a.get("autorise_collecte") is True
            and bool(a.get("valide_par")) and bool(a.get("justification")))
