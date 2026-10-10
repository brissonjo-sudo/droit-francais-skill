"""Contrôle hors réseau d'un relevé privé ; aucune autorisation de collecte."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path
from bench.identite_gemini import modele_exact, numero_projet

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / "tests/bench/runs"
EXEMPLE = ROOT / "tests/campaign/quotas-gemini.example.json"
CHAMPS = {"schema", "auth", "projet_ref", "cle_projet_confirmee", "niveau",
          "modele", "observe_le", "source", "preuve", "limites",
          "autres_limites_verifiees", "autres_limites", "numero_projet", "rattachement_valide_par"}


def chemin_local(path: Path) -> Path:
    """Les relevés privés et leurs preuves doivent rester dans l'état ignoré."""
    target = path.resolve()
    if not target.is_relative_to(LOCAL.resolve()):
        raise ValueError("utiliser un fichier sous tests/bench/runs, hors du dépôt public")
    return target


def initialiser(sortie: Path) -> None:
    """Créer un formulaire vide, sans deviner quotas, modèle ou projet."""
    target = chemin_local(sortie)
    if target.exists():
        raise ValueError("relevé existant : aucune écriture")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Mode x : ne pas écraser un relevé créé entre le contrôle et l'ouverture.
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(EXEMPLE.read_text(encoding="utf-8"))


def verifier(preuve: Path, *, maintenant: dt.datetime | None = None) -> dict:
    """Contrôler la cohérence déclarée et les octets de preuve, sans authentifier."""
    path = chemin_local(preuve)
    try:
        data = json.loads(path.read_bytes())
    except (ValueError, UnicodeError) as exc:
        raise ValueError("relevé JSON illisible ; son contenu n'est pas affiché") from exc
    return verifier_donnees(data, path, maintenant=maintenant)


def verifier_donnees(data: dict, path: Path, *, maintenant: dt.datetime | None = None,
                     preuve_octets: bytes | None = None) -> dict:
    """Valider les octets déjà capturés ; pas de fenêtre validation/instantané."""
    if not isinstance(data, dict) or set(data) != CHAMPS:
        raise ValueError("structure de relevé invalide ; ne pas inclure de secret")
    erreurs = []
    if type(data["schema"]) is not int or data["schema"] != 2:
        erreurs.append("schéma inconnu")
    if data["auth"] != "cle_api_gratuite" or data["niveau"] != "free":
        erreurs.append("clé gratuite et niveau free requis")
    if (not isinstance(data["projet_ref"], str)
            or not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", data["projet_ref"])
            or data["cle_projet_confirmee"] is not True):
        erreurs.append("rattachement de la clé au projet non confirmé")
    try:
        numero_projet(data["numero_projet"])
    except ValueError:
        erreurs.append("numéro de projet Google confirmé requis")
    if not isinstance(data["rattachement_valide_par"], str) or not data["rattachement_valide_par"].strip():
        erreurs.append("titulaire ayant validé le rattachement requis")
    modele = data["modele"]
    try:
        modele_exact(modele)
    except ValueError:
        erreurs.append("identifiant Flash exact requis, sans alias auto")
    if data["source"] != "https://aistudio.google.com/rate-limit":
        erreurs.append("relevé des limites actives AI Studio requis")
    now = maintenant or dt.datetime.now(dt.timezone.utc)
    if now.utcoffset() is None:
        raise ValueError("horloge de contrôle sans fuseau")
    try:
        observe = dt.datetime.fromisoformat(data["observe_le"])
        if observe.utcoffset() is None or not dt.timedelta(0) <= now - observe <= dt.timedelta(hours=24):
            raise ValueError()
    except (ValueError, TypeError):
        erreurs.append("date avec fuseau requise, non future et datant de moins de 24 heures")
    limites = data["limites"]
    if (not isinstance(limites, dict) or set(limites) != {"rpm", "tpm_entree", "rpd"}
            or any(type(v) is not int or v <= 0 for v in limites.values())):
        erreurs.append("RPM, TPM d'entrée et RPD positifs à relever, sans valeurs supposées")
    if data["autres_limites_verifiees"] is not True or not isinstance(data["autres_limites"], list):
        erreurs.append("autres limites du modèle à vérifier explicitement")
    elif data["autres_limites"]:
        erreurs.append("limites supplémentaires déclarées : prise en charge à examiner avant paramétrage")
    piece = data["preuve"]
    if not isinstance(piece, dict) or set(piece) != {"fichier", "sha256"}:
        erreurs.append("structure de preuve locale invalide")
    else:
        try:
            if not isinstance(piece["fichier"], str) or not piece["fichier"] or not re.fullmatch(r"[a-f0-9]{64}", piece["sha256"]):
                raise ValueError()
            artifact = chemin_local(path.parent / piece["fichier"])
            octets = preuve_octets if preuve_octets is not None else artifact.read_bytes()
            if artifact == path or hashlib.sha256(octets).hexdigest() != piece["sha256"]:
                raise ValueError()
        except (ValueError, OSError, TypeError):
            erreurs.append("preuve absente, hors état local ou empreinte différente")
    # Ne restituer ni projet, clé, chemin privé, pièce brute ou contenu du relevé.
    return {"statut": "releve_declare_coherent" if not erreurs else "releve_incomplet_ou_invalide",
            "controle_hors_reseau": True, "collecte_autorisee": False,
            "cle_chargee_environnement": bool(os.environ.get("GEMINI_API_KEY")),
            "problemes_releve": erreurs,
            "reste_a_qualifier": ["authentification gratuite et correspondance de la clé",
                                  "cadence et tokens à chaque requête, reprises internes incluses",
                                  "compteur quotidien au fuseau Pacifique et données de fuseau Windows",
                                  "préflights, corrigés humains et pilote"]}
