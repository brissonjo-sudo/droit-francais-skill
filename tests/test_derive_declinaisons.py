"""Garde-fou de dérive entre le noyau `skill/` et ses déclinaisons.

Chaque déclinaison doit suivre la même version MAJEUR.MINEUR que le noyau et
garder ses invariants : marqueur de provenance, cinq balises, neuf étapes et,
pour les déclinaisons branchées sur le serveur MCP, les douze outils publiés.

Une déclinaison pas encore alignée porte `@unittest.expectedFailure`. Une fois
alignée, unittest signale un succès inattendu et l'exécution échoue tant que le
décorateur n'est pas retiré : c'est le cliquet.

Lecture de texte seulement, sans import du serveur ni dépendance.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOYAU = ROOT / "skill" / "SKILL.md"
CATALOGUE = ROOT / "mcp_server" / "catalog.py"

MARQUEUR = "⚠️ non vérifié — identifiant non récupéré"
BALISES = ("[lookup]", "[express]", "[complet]", "[syllogisme]", "[opérationnel]")


def lire(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8")


def majeur_mineur(version: str) -> str:
    return ".".join(version.split(".")[:2])


def version_noyau() -> str:
    trouve = re.search(r"^\s*version:\s*(\d+\.\d+\.\d+)\s*$", lire(NOYAU), re.M)
    assert trouve, "version introuvable dans skill/SKILL.md"
    return trouve[1]


def etapes(texte: str) -> list[str]:
    """Numéros d'étape portés par des intitulés `## Étape …` à `#### Étape …`."""
    return re.findall(r"^#{2,4} Étape (\d+(?: bis)?)\b", texte, re.M)


def outils_publies() -> list[str]:
    bloc = re.search(r"TOOL_NAMES[^=]*=\s*\((.*?)\)", lire(CATALOGUE), re.S)
    assert bloc, "TOOL_NAMES introuvable dans mcp_server/catalog.py"
    return re.findall(r'"([a-z_]+)"', bloc[1])


def ecarts_skill(dossier: str, *, outils_mcp: bool) -> list[str]:
    texte = lire(ROOT / dossier / "SKILL.md")
    ecarts = []
    base = re.search(r"^\s*base_version:\s*(\S+)\s*$", texte, re.M)
    attendue = majeur_mineur(version_noyau())
    if not base or majeur_mineur(base[1]) != attendue:
        ecarts.append(f"base_version {base[1] if base else 'absente'} != {attendue}.x")
    if MARQUEUR not in texte:
        ecarts.append("marqueur de provenance du noyau absent")
    ecarts += [f"balise {b} absente" for b in BALISES if b not in texte]
    manquantes = [e for e in etapes(lire(NOYAU)) if e not in etapes(texte)]
    ecarts += [f"étape {e} absente" for e in manquantes]
    if outils_mcp:
        ecarts += [f"outil {o} absent" for o in outils_publies() if f"`{o}`" not in texte]
    return ecarts


class NoyauTests(unittest.TestCase):
    """Les références du garde-fou doivent exister dans le noyau lui-même."""

    def test_noyau_porte_les_invariants(self):
        texte = lire(NOYAU)
        self.assertIn(MARQUEUR, texte)
        for balise in BALISES:
            self.assertIn(balise, texte)
        self.assertEqual(9, len(etapes(texte)))
        self.assertEqual(12, len(outils_publies()))


class DeriveDeclinaisonsTests(unittest.TestCase):
    def test_grok(self):
        self.assertEqual([], ecarts_skill("grok_skill", outils_mcp=False))

    def test_vibe(self):
        self.assertEqual([], ecarts_skill("vibe_skill", outils_mcp=False))

    def test_gemini_skill(self):
        self.assertEqual([], ecarts_skill("gemini_skill", outils_mcp=True))

    @unittest.expectedFailure
    def test_manus(self):
        self.assertEqual([], ecarts_skill("manus_skill", outils_mcp=True))

    def test_gemini_agent(self):
        texte = lire(ROOT / "gemini_agent" / "legal_agent_config.py")
        ecarts = []
        version = re.search(r"\bv(\d+\.\d+)\.\d+\b", texte)
        attendue = majeur_mineur(version_noyau())
        if not version or version[1] != attendue:
            ecarts.append(f"version du prompt {version[0] if version else 'absente'} != v{attendue}.x")
        if MARQUEUR not in texte:
            ecarts.append("marqueur de provenance du noyau absent")
        ecarts += [f"balise {b} absente" for b in BALISES if b not in texte]
        self.assertEqual([], ecarts)


if __name__ == "__main__":
    unittest.main()
