"""Profils privés v2 : numéro de projet canonique et instantanés validés."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path

from bench import quotas_gemini
from bench.identite_gemini import numero_projet

EXEMPLE = Path(__file__).resolve().parents[2] / "tests/campaign/profils-gemini.example.json"


def initialiser(sortie: Path) -> None:
    target = quotas_gemini.chemin_local(sortie)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(EXEMPLE.read_text(encoding="utf-8"))
    except OSError:
        raise ValueError("registre existant ou création impossible ; aucun chemin affiché") from None


def charger(registre: Path, profil: str | None = None, *, maintenant: dt.datetime | None = None) -> dict:
    """Capturer puis valider les mêmes octets, sans charger de clé."""
    path = quotas_gemini.chemin_local(registre)
    snapshots = {}

    def lire(p):
        p = quotas_gemini.chemin_local(p)
        if p not in snapshots:
            snapshots[p] = p.read_bytes()
        return snapshots[p]

    try:
        data = json.loads(lire(path))
        if (not isinstance(data, dict) or set(data) != {"schema", "profils"} or data["schema"] != 2
                or not isinstance(data["profils"], list) or not 1 <= len(data["profils"]) <= 20):
            raise ValueError()
        rows, ids, envs, limits, projects = [], set(), set(), {}, {}
        for row in data["profils"]:
            if (not isinstance(row, dict) or set(row) != {"profil", "cle_env", "releve", "qualification"}
                    or not isinstance(row["profil"], str) or not re.fullmatch(r"profil-[0-9]{2}", row["profil"])
                    or not isinstance(row["cle_env"], str)
                    or not re.fullmatch(r"GEMINI_API_KEY(?:_[A-Z0-9_]{1,60})?", row["cle_env"])
                    or row["profil"] in ids or row["cle_env"] in envs
                    or not isinstance(row["releve"], str) or not row["releve"]
                    or not isinstance(row["qualification"], str)):
                raise ValueError()
            ids.add(row["profil"])
            envs.add(row["cle_env"])
            evidence = quotas_gemini.chemin_local(path.parent / row["releve"])
            if evidence == path:
                raise ValueError()
            declared = json.loads(lire(evidence))
            piece = quotas_gemini.chemin_local(evidence.parent / declared["preuve"]["fichier"])
            check = quotas_gemini.verifier_donnees(declared, evidence,
                maintenant=maintenant, preuve_octets=lire(piece))
            if check["problemes_releve"]:
                raise ValueError("relevé incomplet, périmé ou preuve invalide")
            number = numero_projet(declared["numero_projet"])
            key = (number, declared["modele"])
            if key in limits and limits[key] != declared["limites"]:
                raise ValueError("limites contradictoires pour le même numéro de projet/modèle")
            limits[key] = declared["limites"]
            # Un project ID ne peut être déclaré sous plusieurs numéros.
            if declared["projet_ref"] in projects and projects[declared["projet_ref"]] != number:
                raise ValueError("numéros de projet contradictoires")
            projects[declared["projet_ref"]] = number
            rows.append({"row": row, "declare": declared, "numero": number})
        if len({r["declare"]["modele"] for r in rows}) != 1:
            raise ValueError("modèles différents : séries distinctes")
        selected = next((r for r in rows if r["row"]["profil"] == profil), None)
        if profil is not None and selected is None:
            raise ValueError("profil absent")
        return {"path": path, "snapshots": snapshots, "profils": rows, "selection": selected}
    except (OSError, KeyError, TypeError, UnicodeError, ValueError):
        raise ValueError("registre ou preuves privés incomplets/invalides ; aucun contenu affiché") from None


def verifier(registre: Path, profil: str | None = None, *, maintenant: dt.datetime | None = None) -> dict:
    """Sortie assainie ; la cohérence n'autorise aucune collecte."""
    try:
        checked = charger(registre, profil, maintenant=maintenant)
    except ValueError:
        return {"statut": "profils_incomplets_ou_invalides", "controle_hors_reseau": True,
                "collecte_autorisee": False, "selection_explicitement_coherente": False,
                "problemes_registre": ["registre ou preuves incomplets/invalides"]}
    groups = {}
    rows = []
    for r in checked["profils"]:
        group = groups.setdefault(r["numero"], f"groupe-{len(groups) + 1:02}")
        rows.append({"profil": r["row"]["profil"], "groupe_quota_declare": group,
                     "releve_coherent": True, "cle_disponible": bool(os.environ.get(r["row"]["cle_env"])),
                     "problemes_releve": []})
    return {"statut": "profils_declares_coherents", "controle_hors_reseau": True,
            "collecte_autorisee": False, "selection_explicitement_coherente": profil is not None,
            "profil_selectionne": profil, "groupes_quota_declares": len(groups),
            "rotation_automatique": False, "limite_globale_reponses_jour_UTC": 100,
            "profils": rows, "problemes_registre": []}
