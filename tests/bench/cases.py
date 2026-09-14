#!/usr/bin/env python3
"""cases.py — lecture et validation du corpus `bench-cases.csv`.

Reprend le principe de `run_eval.py::load_cases` : **un CSV mal formé est une
erreur, pas un avertissement**. Une colonne excédentaire (virgule non
échappée) tronque silencieusement les motifs des colonnes suivantes ; la
v3.2.0 a corrigé exactement ce défaut sur `eval-modes-erreur.csv`.

Le corpus est un fichier distinct de `eval-modes-erreur.csv`, pour trois
raisons : `run_eval.load_cases` rejette les colonnes excédentaires et
casserait ; la sémantique des interdits diffère avec et sans outils (voir
`tests/README.md`) ; et l'évaluation hors-ligne reste jouée en CI telle
quelle.

Stdlib uniquement.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

COLONNES = (
    "Id",
    "Mode",
    "Intitule",
    "Question sonde",
    "Comportement attendu",
    "Motifs attendus",
    "Motifs interdits",
    "Bras",
    "Outils attendus",
    "Appels interdits",
    "Plafond appels",
    "Date attendue",
    "Identifiants attendus",
    "Provenance requise",
    "Falsification attendue",
    "Documents",
    "Valide par",
)

BRAS_CONNUS = ("A", "B", "C")
PLAFOND_DEFAUT = 12
MOTIF_ID = re.compile(r"^[A-Za-z][A-Za-z0-9]*-?[a-z0-9]*$")
MOTIF_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class CorpusInvalide(Exception):
    """Le corpus ne peut pas être exécuté en l'état."""


@dataclass(frozen=True)
class Cas:
    """Une sonde du benchmark."""

    id: str
    mode: str
    intitule: str
    question: str
    comportement_attendu: str
    motifs_attendus: str
    motifs_interdits: str
    bras: tuple[str, ...]
    outils_attendus: str
    appels_interdits: str
    plafond_appels: int
    date_attendue: str
    identifiants_attendus: tuple[str, ...]
    provenance_requise: bool
    falsification_attendue: bool
    documents: tuple[str, ...]
    valide_par: str

    @property
    def valide(self) -> bool:
        """Le fond juridique a-t-il été validé par un relecteur humain ?"""
        return bool(self.valide_par.strip())


def _bool(valeur: str) -> bool:
    return valeur.strip().lower() in ("oui", "true", "1", "yes")


def _liste(valeur: str) -> tuple[str, ...]:
    return tuple(v.strip() for v in (valeur or "").replace(",", ";").split(";") if v.strip())


def charger(
    chemin: Path,
    *,
    outils_connus: frozenset[str] | None = None,
    racine_documents: Path | None = None,
) -> list[Cas]:
    """Lit le corpus, valide chaque ligne, et lève à la première incohérence.

    ``outils_connus`` doit être `mcp_server.catalog.EXPECTED_TOOLS` : un outil
    attendu qui n'existe pas côté serveur est une sonde qui ne passera jamais,
    et le dire à la lecture évite d'en chercher la cause dans le skill.
    """
    if not chemin.is_file():
        raise CorpusInvalide(f"corpus introuvable : {chemin}")

    with chemin.open(encoding="utf-8", newline="") as flux:
        lecteur = csv.DictReader(flux)
        entetes = tuple(lecteur.fieldnames or ())
        if entetes != COLONNES:
            manquantes = [c for c in COLONNES if c not in entetes]
            surnumeraires = [c for c in entetes if c not in COLONNES]
            details = []
            if manquantes:
                details.append("manquante(s) : " + ", ".join(manquantes))
            if surnumeraires:
                details.append("inconnue(s) : " + ", ".join(surnumeraires))
            if not details:
                details.append("ordre des colonnes différent de la référence")
            raise CorpusInvalide("en-tête du corpus non conforme — " + " ; ".join(details))

        cas: list[Cas] = []
        vus: set[str] = set()
        for numero, ligne in enumerate(lecteur, start=2):
            # DictReader met None en clé quand une ligne a trop de champs :
            # c'est le signe d'une virgule non échappée, qui décale tout.
            if None in ligne:
                raise CorpusInvalide(
                    f"ligne {numero} : champs excédentaires — un séparateur non échappé "
                    "décalerait silencieusement les colonnes suivantes"
                )
            cas.append(_construire(ligne, numero, vus, outils_connus, racine_documents))

    if not cas:
        raise CorpusInvalide("corpus vide")
    return cas


def _construire(
    ligne: dict[str, str],
    numero: int,
    vus: set[str],
    outils_connus: frozenset[str] | None,
    racine_documents: Path | None,
) -> Cas:
    def champ(nom: str) -> str:
        return (ligne.get(nom) or "").strip()

    identifiant = champ("Id")
    if not identifiant:
        raise CorpusInvalide(f"ligne {numero} : colonne Id vide")
    if not MOTIF_ID.match(identifiant):
        raise CorpusInvalide(f"ligne {numero} : Id « {identifiant} » hors format attendu (ex. M03-b)")
    if identifiant in vus:
        raise CorpusInvalide(f"ligne {numero} : Id « {identifiant} » en double — la reprise s'appuie dessus")
    vus.add(identifiant)

    if not champ("Question sonde"):
        raise CorpusInvalide(f"ligne {numero} ({identifiant}) : question sonde vide")
    if not champ("Comportement attendu"):
        raise CorpusInvalide(
            f"ligne {numero} ({identifiant}) : comportement attendu vide — le juge n'aurait rien à vérifier"
        )

    brut_bras = champ("Bras") or "A,B,C"
    bras = _liste(brut_bras)
    inconnus = [b for b in bras if b not in BRAS_CONNUS]
    if inconnus:
        raise CorpusInvalide(f"ligne {numero} ({identifiant}) : bras inconnu(s) {inconnus}")

    outils = champ("Outils attendus")
    if outils and outils_connus is not None:
        noms = {o.strip() for groupe in outils.split(";") for o in groupe.split("|") if o.strip()}
        absents = sorted(noms - set(outils_connus))
        if absents:
            raise CorpusInvalide(
                f"ligne {numero} ({identifiant}) : outil(s) inconnu(s) du serveur MCP {absents}"
            )

    date = champ("Date attendue")
    if date and not MOTIF_DATE.match(date):
        raise CorpusInvalide(f"ligne {numero} ({identifiant}) : date « {date} » non ISO (AAAA-MM-JJ)")

    plafond_brut = champ("Plafond appels")
    try:
        plafond = int(plafond_brut) if plafond_brut else PLAFOND_DEFAUT
    except ValueError as exc:
        raise CorpusInvalide(
            f"ligne {numero} ({identifiant}) : plafond « {plafond_brut} » non entier"
        ) from exc

    documents = _liste(champ("Documents"))
    if documents and racine_documents is not None:
        absents = [d for d in documents if not (racine_documents / d).is_file()]
        if absents:
            raise CorpusInvalide(
                f"ligne {numero} ({identifiant}) : document(s) introuvable(s) {absents}"
            )

    return Cas(
        id=identifiant,
        mode=champ("Mode"),
        intitule=champ("Intitule"),
        question=champ("Question sonde"),
        comportement_attendu=champ("Comportement attendu"),
        motifs_attendus=champ("Motifs attendus"),
        motifs_interdits=champ("Motifs interdits"),
        bras=bras,
        outils_attendus=outils,
        appels_interdits=champ("Appels interdits"),
        plafond_appels=plafond,
        date_attendue=date,
        identifiants_attendus=_liste(champ("Identifiants attendus")),
        provenance_requise=_bool(champ("Provenance requise")),
        falsification_attendue=_bool(champ("Falsification attendue")),
        documents=documents,
        valide_par=champ("Valide par"),
    )


def filtrer(
    cas: list[Cas],
    *,
    seulement: str | None = None,
    bras: str | None = None,
    inclure_brouillons: bool = False,
) -> list[Cas]:
    """Restreint le corpus : `--only`, `--bras`, et validation par l'expert.

    Par défaut, seules les lignes validées tournent : une baseline construite
    sur des sondes dont le fond juridique n'a pas été relu mesurerait le skill
    contre une attente fausse.
    """
    retenus = cas
    if not inclure_brouillons:
        retenus = [c for c in retenus if c.valide]

    if seulement:
        cles = {c.strip() for c in seulement.split(",") if c.strip()}
        retenus = [c for c in retenus if c.id in cles or c.mode in cles]

    if bras:
        demandes = {b.strip() for b in bras.split(",") if b.strip()}
        retenus = [c for c in retenus if set(c.bras) & demandes]

    return retenus
