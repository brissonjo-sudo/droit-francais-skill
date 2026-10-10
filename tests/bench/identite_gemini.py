"""Identifiants fournisseur communs ; aucune clé ni sélection automatique."""
from __future__ import annotations

import re


def modele_exact(modele: str) -> str:
    """Exiger un identifiant Flash explicite, sans alias latest/auto."""
    if (not isinstance(modele, str)
            or not re.fullmatch(r"gemini-[0-9][a-z0-9.-]{0,90}flash[a-z0-9.-]{0,30}", modele)
            or "latest" in modele or "auto" in modele):
        raise ValueError("identifiant Flash exact requis")
    return modele


def numero_projet(value: str) -> str:
    """Normaliser le numéro déclaré ; cette fonction n'authentifie pas Google."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,20}", value) or int(value) <= 0:
        raise ValueError("numéro de projet Google positif confirmé requis")
    return str(int(value))
