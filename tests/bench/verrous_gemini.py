"""Transitions atomiques des verrous privés ; récupération humaine sans remboursement."""
from __future__ import annotations

import argparse
import contextlib
import json
import hashlib
import os
import socket
import sys
import uuid
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bench import etude_v2
from bench.journal import Journal


class ErreurVerrou(ValueError):
    categorie = "budget"


@contextlib.contextmanager
def transition(racine: Path):
    with contextlib.ExitStack() as stack:
        try:
            stack.enter_context(etude_v2.verrou_transition(racine))
        except ValueError as exc:
            raise ErreurVerrou("transition concurrente : examen explicite requis") from exc
        yield


@contextlib.contextmanager
def verrou(racine: Path, path: Path, *, attempt_id: str = "liaison"):
    """Créer et retirer sous le même verrou OS que la récupération explicite."""
    token = uuid.uuid4().hex
    with transition(racine):
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise ErreurVerrou("requête concurrente ou verrou interrompu : examen manuel requis") from None
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump({"schema": 2, "pid": os.getpid(), "hote": socket.gethostname(),
                       "cree_le": etude_v2.maintenant(), "nonce": token, "attempt_id": attempt_id}, handle)
            handle.flush()
            os.fsync(handle.fileno())
    try:
        yield
    finally:
        with transition(racine):
            if path.exists() and json.loads(path.read_bytes()).get("nonce") == token:
                path.unlink()


def retirer(racine: Path, path: Path, auteur: str, motif: str, *, preuve_absence_processus: Path | None = None) -> None:
    """PID mort sur ce poste, reçu humain durable ; aucune expiration automatique."""
    if not auteur.strip() or not motif.strip():
        raise ValueError("auteur humain et motif requis")
    path = path.resolve()
    if not path.is_relative_to(racine.resolve()) or path.name not in {"requete.lock", "profils.lock"}:
        raise ValueError("verrou Gemini privé requis")
    with transition(racine):
        raw = path.read_bytes()
        if not raw:
            if preuve_absence_processus is None:
                raise ValueError("verrou vide : preuve humaine d'absence de processus requise")
            from bench.quotas_gemini import chemin_local
            proof = chemin_local(preuve_absence_processus).read_bytes()
            if not proof:
                raise ValueError("preuve humaine vide")
            info = {"verrou_vide": True, "preuve_absence_processus_sha256": hashlib.sha256(proof).hexdigest()}
        else:
            info = json.loads(raw)
        if raw and (info.get("schema") != 2 or info.get("hote") != socket.gethostname()
                or type(info.get("pid")) is not int or info["pid"] <= 0
                or not isinstance(info.get("nonce"), str) or not info["nonce"]
                or etude_v2.processus_actif(info["pid"])):
            raise ValueError("processus actif, distant ou verrou non qualifié : aucun retrait")
        Journal(racine / "recuperations-gemini.jsonl").ajouter({"schema": 2,
            "verrou": info, "type_verrou": path.name, "auteur_humain": auteur,
            "verrou_sha256": hashlib.sha256(raw).hexdigest(),
            "motif": motif, "horodatage": etude_v2.maintenant()})
        path.unlink()


def lever_arret(budget, auteur: str, motif: str) -> None:
    """Reprise explicite après examen : journaliser avant retrait, aucun reset."""
    if not auteur.strip() or not motif.strip():
        raise ValueError("auteur humain et motif requis")
    with transition(budget.racine):
        for lock in (budget.dossier / "requete.lock", budget.racine / "profils.lock", budget.racine / "collection.lock"):
            if lock.exists():
                raise ValueError("requête, collecte ou liaison active/ambiguë : récupérer son verrou avant reprise")
        raw = budget.arret.read_bytes()
        info = json.loads(raw)
        if (not isinstance(info, dict) or info.get("schema") != 2 or info.get("hote") != socket.gethostname()
                or type(info.get("pid")) is not int or info["pid"] <= 0
                or type(info.get("statut")) is not int or info["statut"] not in (0, 429)
                or etude_v2.processus_actif(info["pid"])):
            raise ValueError("créateur actif ou arrêt ancien/ambigu : examen requis")
        Journal(budget.racine / "reprises-gemini.jsonl").ajouter({"schema": 2,
            "numero_projet": budget.projet, "modele": budget.modele,
            "arret_sha256": hashlib.sha256(raw).hexdigest(), "arret": info,
            "auteur_humain": auteur, "motif": motif, "horodatage": etude_v2.maintenant()})
        budget.arret.unlink()


def main(argv=None) -> int:
    from bench import profils_gemini
    from bench.budget_gemini import Budget
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registre", type=Path, required=True)
    parser.add_argument("--profil", required=True)
    parser.add_argument("--operation", choices=("retirer-verrou", "lever-arret"), default="retirer-verrou")
    parser.add_argument("--type", choices=("requete", "profils"), default="requete")
    parser.add_argument("--preuve-absence-processus", type=Path)
    parser.add_argument("--auteur", required=True)
    parser.add_argument("--motif", required=True)
    args = parser.parse_args(argv)
    try:
        row = profils_gemini.identite_maintenance(args.registre, args.profil)
        budget = Budget(row["numero"], row["declare"]["modele"], row["declare"]["limites"])
        path = budget.dossier / "requete.lock" if args.type == "requete" else budget.racine / "profils.lock"
        if args.operation == "lever-arret":
            lever_arret(budget, args.auteur, args.motif)
            print("Arrêt levé explicitement ; budgets et résultats conservés, aucune requête")
        else:
            retirer(budget.racine, path, args.auteur, args.motif, preuve_absence_processus=args.preuve_absence_processus)
            print("Verrou abandonné retiré ; budgets, résultats et arrêt de quota conservés")
        return 0
    except (ValueError, OSError, KeyError):
        print("Retrait refusé : profil, preuve ou processus à examiner")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
