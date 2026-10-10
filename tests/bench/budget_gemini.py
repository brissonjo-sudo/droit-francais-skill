"""Budget REST privé par projet/modèle, réservé avant envoi et jamais remboursé."""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import math
import os
import re
from functools import lru_cache
from importlib import metadata, resources
from pathlib import Path
from zoneinfo import ZoneInfo

from bench import gemini_http, quotas_gemini
from bench.journal import Journal

TZDATA_VERSION = "2026.5"


@lru_cache(maxsize=1)
def pacifique() -> ZoneInfo:
    """Charger la même base IANA figée sous Windows et Linux, sans TZPATH hôte."""
    try:
        if metadata.version("tzdata") != TZDATA_VERSION:
            raise ValueError()
        with resources.files("tzdata").joinpath("zoneinfo/America/Los_Angeles").open("rb") as stream:
            return ZoneInfo.from_file(stream, key="America/Los_Angeles")
    except (metadata.PackageNotFoundError, OSError, ValueError) as exc:
        raise ValueError("installer les données de fuseau figées de requirements-bench.txt") from exc


def jour_pacifique(instant: dt.datetime) -> str:
    """Jour de quota Google avec changements d'heure ; jamais un jour UTC."""
    if instant.utcoffset() is None:
        raise ValueError("horloge sans fuseau")
    return instant.astimezone(pacifique()).date().isoformat()


class ArretBudget(ValueError):
    """Arrêt assaini : pas d'attente ni de relance interne implicite."""


class Budget:
    """Un journal commun à toutes les clés d'un même projet et modèle."""

    def __init__(self, state: Path, projet: str, modele: str, limites: dict, *,
                 marge_pourcent: int = 20, horloge=None):
        gemini_http.modele_exact(modele)
        if not isinstance(projet, str) or not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", projet):
            raise ValueError("projet confirmé requis")
        if (not isinstance(limites, dict) or set(limites) != {"rpm", "tpm_entree", "rpd"}
                or any(type(n) is not int or n <= 0 for n in limites.values())
                or type(marge_pourcent) is not int or not 20 <= marge_pourcent <= 90):
            raise ValueError("limites positives et marge de 20 à 90 pour cent requises")
        self.capacite = {k: max(1, v * (100 - marge_pourcent) // 100) for k, v in limites.items()}
        identity = hashlib.sha256(f"{projet}\n{modele}".encode()).hexdigest()
        self.dossier = quotas_gemini.chemin_local(state / identity)
        self.journal = self.dossier / "requetes.jsonl"
        self.arret = self.dossier / "arret.json"
        self.horloge = horloge or (lambda: dt.datetime.now(dt.timezone.utc))
        pacifique()

    def _lire(self, now: dt.datetime) -> list[dict]:
        if not self.journal.exists():
            return []
        try:
            rows = [json.loads(line) for line in self.journal.read_text(encoding="utf-8").splitlines()]
            for row in rows:
                if (not isinstance(row, dict) or set(row) != {"instant", "jour", "requetes", "tokens", "type"}
                        or type(row["instant"]) not in (float, int) or not math.isfinite(row["instant"])
                        or row["instant"] > now.timestamp()
                        or type(row["requetes"]) is not int or row["requetes"] not in (0, 1)
                        or type(row["tokens"]) is not int or row["tokens"] < 0
                        or row["type"] not in ("countTokens", "generateContent", "surplus")
                        or row["jour"] != jour_pacifique(dt.datetime.fromtimestamp(row["instant"], dt.timezone.utc))):
                    raise ValueError()
            return rows
        except (ValueError, TypeError, KeyError, OverflowError, OSError) as exc:
            raise ArretBudget("journal invalide ou horloge reculée : examen explicite requis") from exc

    def _ajouter(self, instant: dt.datetime, requetes: int, tokens: int, kind: str) -> None:
        Journal(self.journal).ajouter({"instant": instant.timestamp(), "jour": jour_pacifique(instant),
                                      "requetes": requetes, "tokens": tokens, "type": kind})

    def bloquer(self, statut: int) -> None:
        """Persistant après 429 ou dépassement mesuré ; aucune autre clé ne l'efface."""
        if not self.arret.exists():
            with self.arret.open("x", encoding="utf-8", newline="\n") as handle:
                json.dump({"statut": statut, "reprise": "examen_explicite_requis"}, handle)
                handle.flush()
                os.fsync(handle.fileno())

    @contextlib.contextmanager
    def tentative(self, tokens_entree: int, kind: str):
        """Réserver sous verrou conservé pendant HTTP ; l'interruption garde le débit."""
        if type(tokens_entree) is not int or tokens_entree < 0 or kind not in ("countTokens", "generateContent"):
            raise ValueError("réservation invalide")
        self.dossier.mkdir(parents=True, exist_ok=True)
        lock = self.dossier / "requete.lock"
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise ArretBudget("requête concurrente ou verrou interrompu : examiner le processus") from exc
        try:
            os.close(fd)
            now = self.horloge()
            day = jour_pacifique(now)
            rows = self._lire(now)
            if self.arret.exists():
                raise ArretBudget("projet/modèle arrêté : reprise explicite requise")
            recent = [r for r in rows if now.timestamp() - r["instant"] < 60]
            if sum(r["requetes"] for r in rows if r["jour"] == day) + 1 > self.capacite["rpd"]:
                raise ArretBudget("budget RPD Pacifique atteint")
            if sum(r["requetes"] for r in recent) + 1 > self.capacite["rpm"]:
                raise ArretBudget("budget RPM atteint ; aucune requête envoyée")
            if sum(r["tokens"] for r in recent) + tokens_entree > self.capacite["tpm_entree"]:
                raise ArretBudget("budget TPM d'entrée atteint ; aucune requête envoyée")
            self._ajouter(now, 1, tokens_entree, kind)
            yield now
        finally:
            lock.unlink()

    def usage(self, reservation: dt.datetime, reserve: int, mesure: int) -> None:
        """Ne jamais rembourser ; inscrire le surplus et arrêter avant un nouvel appel."""
        if type(mesure) is not int or mesure < 0:
            self.bloquer(0)
            raise ArretBudget("usage d'entrée absent ou invalide")
        if mesure > reserve:
            # Prendre la date la plus récente si la réponse franchit minuit.
            self._ajouter(self.horloge(), 0, mesure - reserve, "surplus")
            self.bloquer(0)
            raise ArretBudget("usage supérieur à la réservation : arrêt pour examen")
