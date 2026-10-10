"""Réservations durables d'étude : une tentative ne disparaît pas après crash."""
from __future__ import annotations

import contextlib
import datetime as dt
import json
import os
import secrets
import tempfile
import socket
from pathlib import Path

from bench.contexte import IRRECUPERABLES
from bench.journal import Journal


def lire(path: Path) -> list[dict]:
    """Lecture stricte ; les données antérieures au schéma v2 sont refusées."""
    if not path.exists():
        return []
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            if not isinstance(r, dict) or r.get("schema") != 2:
                raise ValueError()
        except ValueError as exc:
            raise ValueError(f"journal v2 invalide ligne {i} ; conserver et examiner, aucune migration implicite") from exc
        rows.append(r)
    return rows


def atomique(path: Path, value: object) -> None:
    """Remplacement atomique sur le même volume ; jamais de JSON partiel acquis."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".ecriture-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextlib.contextmanager
def verrou_transition(state: Path):
    """Exclusion OS courte ; fichier persistant, verrou libéré même après crash."""
    state.mkdir(parents=True, exist_ok=True)
    with (state / "transition.lock").open("a+b") as guard:
        guard.seek(0, 2)
        if not guard.tell():
            guard.write(b"0")
            guard.flush()
        guard.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(guard.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(guard.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError("transition de verrou active ; réessayer explicitement") from exc
        try:
            yield
        finally:
            guard.seek(0)
            if os.name == "nt":
                msvcrt.locking(guard.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(guard.fileno(), fcntl.LOCK_UN)


@contextlib.contextmanager
def verrou(state: Path):
    """Le verrou englobe lecture, réservation, appel, résultat et clôture."""
    state.mkdir(parents=True, exist_ok=True)
    lock = state / "collection.lock"
    token = secrets.token_hex(16)
    with verrou_transition(state):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise ValueError("collecte active ou verrou abandonné ; récupération explicite requise") from exc
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump({"schema": 2, "pid": os.getpid(), "token": token,
                       "hote": socket.gethostname(), "cree_utc": maintenant()}, stream)
            stream.flush()
            os.fsync(stream.fileno())
    try:
        yield
    finally:
        with verrou_transition(state):
            if lock.exists() and json.loads(lock.read_text(encoding="utf-8")).get("token") == token:
                lock.unlink()


def maintenant() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def invalidations(state: Path, serie: str, *, phase: str | None = None) -> list[dict]:
    rows = lire(state / serie / "invalidations.jsonl")
    if any(not r.get("phase") for r in rows):
        raise ValueError("invalidation ancienne sans phase ; examen explicite requis")
    return [r for r in rows if phase is None or r["phase"] == phase]


def sain(state: Path, serie: str, *, phase: str | None = None) -> None:
    """Une série invalidée n'est jamais réactivée par une relance."""
    if invalidations(state, serie, phase=phase):
        raise ValueError("phase définitivement invalidée ; nouvelle série requise pour cette phase")


def invalider(state: Path, serie: str, categorie: str, motif: str, *, phase: str) -> None:
    if categorie not in IRRECUPERABLES:
        raise ValueError("catégorie non invalidante")
    Journal(state / serie / "invalidations.jsonl").ajouter({"schema": 2,
        "categorie_infra": categorie, "motif": motif, "phase": phase, "horodatage": maintenant()})


def reservations(state: Path) -> list[dict]:
    rows = lire(state / "budget.jsonl")
    ids = [r.get("attempt_id") for r in rows]
    if any(not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("réservations dupliquées ou incomplètes")
    return rows


def verifier_contexte(ctx) -> None:
    """Sans réacquérir le verrou déjà tenu par le lanceur : preuve active exacte."""
    sain(ctx.racine_etat, ctx.series_sha256, phase=ctx.reservation["phase"])
    rows = [r for r in reservations(ctx.racine_etat) if r["attempt_id"] == ctx.attempt_id]
    if len(rows) != 1 or rows[0] != ctx.reservation:
        raise ValueError("contexte sans réservation durable exacte")
    r = rows[0]
    if (r["identite"] != ctx.identite or r["series_sha256"] != ctx.series_sha256
            or r["tentative"] != ctx.tentative or r.get("modele") != ctx.modele or r.get("moteur") != ctx.moteur):
        raise ValueError("contexte incohérent avec sa réservation")
    if ctx.attempt_id in clotures(ctx.racine_etat):
        raise ValueError("contexte de tentative déjà clôturée")


def clotures(state: Path) -> dict[str, dict]:
    rows = lire(state / "clotures.jsonl")
    ids = [r["attempt_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("clôture dupliquée")
    known = {r["attempt_id"] for r in reservations(state)}
    if set(ids) - known:
        raise ValueError("clôture sans réservation")
    return dict(zip(ids, rows))


def verifier_attentes(state: Path, serie: str, *, phase: str | None = None) -> None:
    done = clotures(state)
    if any(r["series_sha256"] == serie and (phase is None or r["phase"] == phase) and r["attempt_id"] not in done for r in reservations(state)):
        raise ValueError("tentative indéterminée après interruption ; clôturer explicitement avant reprise")


def reserver(state: Path, identity: str, *, serie: str, meta: dict,
             jour: str | None = None) -> dict:
    """Sous verrou ; seul point de réservation de l'étude, jamais remboursé."""
    from bench.contexte import assurer_ancre
    assurer_ancre(state)
    if not isinstance(meta.get("phase"), str) or not meta["phase"]:
        raise ValueError("phase de réservation obligatoire")
    sain(state, serie, phase=meta["phase"])
    verifier_attentes(state, serie, phase=meta["phase"])
    rows = reservations(state)
    done = clotures(state)
    previous = [r for r in rows if r["identite"] == identity]
    if any(done.get(r["attempt_id"], {}).get("statut") == "ok" for r in previous):
        raise ValueError("une réponse acquise ne peut pas être rejouée")
    if len(previous) >= 2:
        raise ValueError("deux tentatives réservées ; déclaration humaine de donnée manquante requise")
    day = jour or dt.datetime.now(dt.timezone.utc).date().isoformat()
    if rows and day < max(r["jour"] for r in rows):
        raise ValueError("horloge reculée ; budget indisponible")
    if sum(r["jour"] == day for r in rows) >= 100:
        raise ValueError("limite de 100 tentatives/jour UTC atteinte")
    row = {**meta, "schema": 2, "jour": day, "horodatage": maintenant(),
           "identite": identity, "series_sha256": serie,
           "attempt_id": secrets.token_hex(20), "tentative": len(previous) + 1}
    Journal(state / "budget.jsonl").ajouter(row)
    return row


def clore(state: Path, reservation: dict, *, statut: str, categorie: str = "", preuve: str = "") -> None:
    from bench.contexte import CATEGORIES_INFRA
    if statut not in ("ok", "infra_error") or (statut == "ok" and categorie) or (statut == "infra_error" and categorie not in CATEGORIES_INFRA):
        raise ValueError("statut ou catégorie de clôture invalide")
    if reservation["attempt_id"] in clotures(state):
        raise ValueError("tentative déjà clôturée")
    Journal(state / "clotures.jsonl").ajouter({"schema": 2,
        "attempt_id": reservation["attempt_id"], "identite": reservation["identite"],
        "statut": statut, "categorie_infra": categorie, "preuve_sha256": preuve,
        "horodatage": maintenant()})


def engagements(state: Path) -> dict[str, dict]:
    rows = lire(state / "engagements.jsonl")
    keys = [r["attempt_id"] for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("engagement de résultat dupliqué")
    return dict(zip(keys, rows))


def engager_resultat(state: Path, reservation: dict, sha256: str) -> None:
    if len(sha256) != 64 or any(c not in "0123456789abcdef" for c in sha256):
        raise ValueError("empreinte de résultat invalide")
    if reservation not in reservations(state) or reservation["attempt_id"] in clotures(state):
        raise ValueError("réservation active exacte requise")
    if reservation["attempt_id"] in engagements(state):
        raise ValueError("résultat déjà engagé ; récupération explicite requise")
    Journal(state / "engagements.jsonl").ajouter({"schema": 2, "attempt_id": reservation["attempt_id"],
        "resultat_sha256": sha256, "horodatage": maintenant()})


def manquants(state: Path, serie: str, *, phase: str | None = None) -> dict[str, dict]:
    rows = lire(state / serie / "manquants.jsonl")
    if any(not r.get("phase") for r in rows):
        raise ValueError("manquant ancien sans phase ; examen explicite requis")
    rows = [r for r in rows if phase is None or r["phase"] == phase]
    keys = [r["identite"] for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("déclaration de manquant dupliquée")
    return dict(zip(keys, rows))


def declarer_manquant(state: Path, serie: str, identity: str, auteur: str, motif: str) -> None:
    if not auteur.strip() or not motif.strip():
        raise ValueError("auteur humain et motif requis")
    with verrou(state):
        rows = [r for r in reservations(state) if r["series_sha256"] == serie and r["identite"] == identity]
        if not rows or len({r["phase"] for r in rows}) != 1:
            raise ValueError("identité sans phase réservée unique")
        phase = rows[0]["phase"]
        sain(state, serie, phase=phase)
        verifier_attentes(state, serie, phase=phase)
        done = clotures(state)
        if len(rows) != 2 or any(done[r["attempt_id"]]["statut"] == "ok" for r in rows):
            raise ValueError("deux pannes clôturées requises ; un succès ne devient pas manquant")
        if identity in manquants(state, serie):
            raise ValueError("déclaration déjà acquise")
        Journal(state / serie / "manquants.jsonl").ajouter({"schema": 2,
            "identite": identity, "phase": phase, "auteur_humain": auteur, "motif": motif,
            "attempt_ids": [r["attempt_id"] for r in rows], "horodatage": maintenant()})


def processus_actif(pid: int) -> bool:
    """Incertitude d'accès => actif ; aucun PID n'est terminé par cette lecture."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        api = ctypes.WinDLL("kernel32", use_last_error=True)
        api.OpenProcess.restype = wintypes.HANDLE
        api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        api.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        api.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = api.OpenProcess(0x1000, False, pid)
        if not handle:
            return ctypes.get_last_error() != 87
        try:
            code = wintypes.DWORD()
            return not api.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value == 259
        finally:
            api.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def retirer_verrou_abandonne(state: Path, auteur: str, motif: str) -> None:
    if not auteur.strip() or not motif.strip():
        raise ValueError("auteur humain et motif requis")
    with verrou_transition(state):
        path = state / "collection.lock"
        before = path.read_bytes()
        info = json.loads(before)
        if info.get("schema") != 2 or info.get("hote") != socket.gethostname() or processus_actif(info["pid"]):
            raise ValueError("processus encore actif ou verrou ancien non qualifié")
        if path.read_bytes() != before:
            raise ValueError("verrou changé pendant le contrôle")
        Journal(state / "recuperations.jsonl").ajouter({"schema": 2, "verrou": info,
            "auteur_humain": auteur, "motif": motif, "horodatage": maintenant()})
        path.unlink()


def clore_interruption(state: Path, attempt_id: str, auteur: str, motif: str) -> None:
    """Résultat déjà écrit : conserver son statut ; sinon panne indéterminée clôturée."""
    if not auteur.strip() or not motif.strip():
        raise ValueError("auteur humain et motif requis")
    with verrou(state):
        rows = [r for r in reservations(state) if r["attempt_id"] == attempt_id]
        if len(rows) != 1:
            raise ValueError("réservation inconnue")
        r = rows[0]
        output = Path(r["output"])
        if not output.resolve().is_relative_to(state.resolve()):
            raise ValueError("résultat hors état privé")
        found = [x for x in lire(output) if x.get("attempt_id") == attempt_id]
        if len(found) > 1:
            raise ValueError("résultat dupliqué")
        from bench.campaign import digest
        if found:
            x = found[0]
            if engagements(state).get(attempt_id, {}).get("resultat_sha256") != digest(x):
                raise ValueError("résultat sans engagement préalable exact ; fabrication ou corruption possible")
            for key in ("series_sha256", "identite", "tentative"):
                expected = r.get("resultat_identite", r["identite"]) if key == "identite" else r[key]
                if x.get(key) != expected:
                    raise ValueError("résultat durable incohérent avec sa réservation")
            statut = x.get("statut_technique", x.get("statut_juge"))
            categorie = x.get("categorie_infra", "")
            if categorie in IRRECUPERABLES and x.get("exposition_modele") is True:
                invalider(state, r["series_sha256"], categorie, "récupération d'un résultat invalidant", phase=r["phase"])
            clore(state, r, statut=statut, categorie=categorie, preuve=digest(x))
        else:
            clore(state, r, statut="infra_error", categorie="interruption")
        Journal(state / "recuperations.jsonl").ajouter({"schema": 2,
            "attempt_id": attempt_id, "auteur_humain": auteur, "motif": motif, "horodatage": maintenant()})
