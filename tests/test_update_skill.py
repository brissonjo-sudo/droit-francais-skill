#!/usr/bin/env python3
"""Tests hors réseau du lanceur de mise à jour optionnelle ``update_skill.py``.

Aucun test ne lance ``npx`` : ``subprocess.run`` et ``shutil.which`` sont
simulés, et chaque test travaille dans un faux dossier de skill temporaire,
jamais dans ``skill/`` du dépôt.
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import update_skill  # noqa: E402

#: Chemin tel que le rend ``shutil.which`` sous Windows. La commande doit le
#: reprendre : ``subprocess.run(["npx", ...])`` sans shell ne trouve pas
#: ``npx.cmd`` et lève ``FileNotFoundError`` (constaté le 14 septembre 2026).
NPX_RESOLU = r"C:\node\npx.CMD"
COMMANDE_ATTENDUE = [NPX_RESOLU, "skills", "update", "recherche-juridique", "-y", "-g"]


class FauxSkill(unittest.TestCase):
    """Installe un skill factice sous un faux ``~/.claude/skills``."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name).resolve()
        self.racine = self.home / ".claude" / "skills" / "recherche-juridique"
        (self.racine / "scripts").mkdir(parents=True)
        self.ecrire_version("3.4.0")
        self.config = self.racine / ".recherche-juridique-update.json"
        self.profil = self.racine / "profil.md"
        self.env = self.racine / "scripts" / ".env"
        for patch in (
            mock.patch.object(update_skill, "SKILL_ROOT", self.racine),
            mock.patch.object(update_skill, "CONFIG", self.config),
            mock.patch.object(update_skill, "PERSONAL_FILES", (self.profil, self.env)),
            mock.patch.object(update_skill.Path, "home", return_value=self.home),
        ):
            patch.start()
            self.addCleanup(patch.stop)

    def ecrire_version(self, version: str) -> None:
        (self.racine / "SKILL.md").write_text(
            f"---\nname: recherche-juridique\nmetadata:\n  version: {version}\n---\n",
            encoding="utf-8",
        )

    def activer(self, **extra) -> None:
        self.config.write_text(json.dumps({"automatic": True, **extra}), encoding="utf-8")

    def lancer(self) -> tuple[int, str]:
        sortie = io.StringIO()
        with contextlib.redirect_stdout(sortie):
            code = update_skill.main()
        return code, sortie.getvalue()


class LectureVersionTests(FauxSkill):
    def test_lit_la_version_du_frontmatter(self):
        self.assertEqual(update_skill.read_version(), "3.4.0")

    def test_version_inconnue_si_skill_md_absent(self):
        (self.racine / "SKILL.md").unlink()
        self.assertEqual(update_skill.read_version(), "inconnue")


class ConfigurationTests(FauxSkill):
    def test_absente_vaut_mode_desactive_et_silencieux(self):
        sortie = io.StringIO()
        with contextlib.redirect_stdout(sortie):
            self.assertIsNone(update_skill.load_config())
        self.assertEqual(sortie.getvalue(), "")

    def test_json_illisible_est_signale_sans_activer(self):
        self.config.write_text("{automatic: true", encoding="utf-8")
        sortie = io.StringIO()
        with contextlib.redirect_stdout(sortie):
            self.assertIsNone(update_skill.load_config())
        self.assertIn("UPDATE_SKIPPED", sortie.getvalue())

    def test_seul_le_booleen_true_active(self):
        for contenu in ({"automatic": False}, {"automatic": "true"}, {"automatic": 1}, [True], {}):
            with self.subTest(contenu=contenu):
                self.config.write_text(json.dumps(contenu), encoding="utf-8")
                self.assertIsNone(update_skill.load_config())
        self.activer()
        self.assertEqual(update_skill.load_config(), {"automatic": True})


class EcheanceTests(unittest.TestCase):
    MAINTENANT = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)

    def echu(self, valeur) -> bool:
        return update_skill.due({"last_attempt_at": valeur}, self.MAINTENANT)

    def test_premiere_tentative_est_due(self):
        self.assertTrue(update_skill.due({}, self.MAINTENANT))

    def test_moins_de_24_heures_n_est_pas_du(self):
        self.assertFalse(self.echu("2026-09-13T12:00:01Z"))

    def test_24_heures_pile_est_du(self):
        self.assertTrue(self.echu("2026-09-13T12:00:00Z"))

    def test_fuseau_non_utc_est_converti(self):
        # 13:30 à Paris (+02:00) = 11:30 UTC, soit 30 minutes avant MAINTENANT.
        self.assertFalse(self.echu("2026-09-14T13:30:00+02:00"))

    def test_date_invalide_naive_ou_non_textuelle_est_due(self):
        for valeur in ("hier", "2026-09-14T11:00:00", 1757851200, None):
            with self.subTest(valeur=valeur):
                self.assertTrue(self.echu(valeur))


class PerimetreTests(FauxSkill):
    def test_installation_globale_reconnue(self):
        for dossier in (".claude", ".codex", ".cursor", ".copilot"):
            with self.subTest(dossier=dossier):
                racine = self.home / dossier / "skills" / "recherche-juridique"
                with mock.patch.object(update_skill, "SKILL_ROOT", racine):
                    self.assertEqual(update_skill.scope_argument(), "-g")

    def test_emplacements_ambigus_refuses(self):
        ailleurs = Path(tempfile.gettempdir()).resolve().parent / "hors-home"
        for racine in (
            self.home / "projet" / ".claude" / "skills" / "recherche-juridique",
            self.home / ".claude" / "recherche-juridique",
            self.home / ".autre" / "skills" / "recherche-juridique",
            ailleurs,
        ):
            with self.subTest(racine=racine), mock.patch.object(update_skill, "SKILL_ROOT", racine):
                self.assertIsNone(update_skill.scope_argument())


class SauvegardeTests(FauxSkill):
    def test_fichiers_personnels_restaures_apres_ecrasement_ou_suppression(self):
        self.profil.write_text("profil de Jo", encoding="utf-8")
        self.env.write_text("PISTE_CLIENT_ID=x", encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            sauvegardes = update_skill.backup_personal_files(Path(tmp))
            self.profil.write_text("profil neutre", encoding="utf-8")
            self.env.unlink()
            update_skill.restore_personal_files(sauvegardes)
        self.assertEqual(self.profil.read_text(encoding="utf-8"), "profil de Jo")
        self.assertEqual(self.env.read_text(encoding="utf-8"), "PISTE_CLIENT_ID=x")

    def test_fichier_absent_n_est_pas_cree(self):
        with tempfile.TemporaryDirectory() as tmp:
            sauvegardes = update_skill.backup_personal_files(Path(tmp))
            update_skill.restore_personal_files(sauvegardes)
        self.assertEqual(sauvegardes, [])
        self.assertFalse(self.profil.exists())
        self.assertFalse(self.env.exists())


class LanceurTests(FauxSkill):
    def setUp(self):
        super().setUp()
        patch_which = mock.patch.object(update_skill.shutil, "which", return_value=NPX_RESOLU)
        self.which = patch_which.start()
        self.addCleanup(patch_which.stop)
        patch_run = mock.patch.object(update_skill.subprocess, "run")
        self.run = patch_run.start()
        self.addCleanup(patch_run.stop)

    def resultat(self, code: int = 0):
        return subprocess.CompletedProcess(COMMANDE_ATTENDUE, code, "", "")

    def derniere_tentative(self):
        return json.loads(self.config.read_text(encoding="utf-8")).get("last_attempt_at")

    def test_mode_desactive_ne_lance_rien(self):
        self.assertEqual(self.lancer(), (0, ""))
        self.run.assert_not_called()

    def test_tentative_recente_ne_relance_pas(self):
        recente = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        self.activer(last_attempt_at=recente)
        self.assertEqual(self.lancer(), (0, ""))
        self.run.assert_not_called()

    def test_installation_non_globale_ignoree(self):
        self.activer()
        locale = self.home / "projet" / ".claude" / "skills" / "recherche-juridique"
        with mock.patch.object(update_skill, "SKILL_ROOT", locale):
            code, sortie = self.lancer()
        self.assertEqual(code, 0)
        self.assertIn("UPDATE_SKIPPED", sortie)
        self.run.assert_not_called()

    def test_npx_absent_ignore(self):
        self.activer()
        self.which.return_value = None
        code, sortie = self.lancer()
        self.assertEqual(code, 0)
        self.assertIn("UPDATE_SKIPPED npx indisponible", sortie)
        self.run.assert_not_called()

    def test_mise_a_jour_appliquee_restaure_le_profil_et_date_la_tentative(self):
        self.activer()
        self.profil.write_text("profil de Jo", encoding="utf-8")

        def mise_a_jour(commande, **options):
            # Le CLI réinstalle le skill : nouvelle version, profil écrasé.
            self.ecrire_version("3.5.0")
            self.profil.write_text("profil neutre", encoding="utf-8")
            return self.resultat(0)

        self.run.side_effect = mise_a_jour
        code, sortie = self.lancer()

        self.assertEqual(code, 0)
        self.assertEqual(sortie.strip(), "UPDATE_APPLIED recherche-juridique 3.4.0 → 3.5.0")
        self.assertEqual(self.run.call_args.args[0], COMMANDE_ATTENDUE)
        self.assertEqual(self.profil.read_text(encoding="utf-8"), "profil de Jo")
        self.assertIsNotNone(self.derniere_tentative())
        self.assertTrue(json.loads(self.config.read_text(encoding="utf-8"))["automatic"])

    def test_aucune_nouvelle_version_reste_silencieux(self):
        self.activer()
        self.run.return_value = self.resultat(0)
        self.assertEqual(self.lancer(), (0, ""))
        self.assertIsNotNone(self.derniere_tentative())

    def test_refus_du_cli_signale_et_date_la_tentative(self):
        self.activer()
        self.run.return_value = self.resultat(1)
        code, sortie = self.lancer()
        self.assertEqual(code, 0)
        self.assertIn("UPDATE_FAILED", sortie)
        self.assertIsNotNone(self.derniere_tentative())

    def test_lancement_impossible_restaure_quand_meme_le_profil(self):
        self.activer()
        self.profil.write_text("profil de Jo", encoding="utf-8")

        def echec(commande, **options):
            self.profil.unlink()
            raise FileNotFoundError("npx")

        self.run.side_effect = echec
        code, sortie = self.lancer()
        self.assertEqual(code, 0)
        self.assertIn("UPDATE_FAILED lancement impossible", sortie)
        self.assertEqual(self.profil.read_text(encoding="utf-8"), "profil de Jo")
        # Sans date, un lancement toujours impossible serait retenté à chaque usage.
        self.assertIsNotNone(self.derniere_tentative())


if __name__ == "__main__":
    unittest.main()
