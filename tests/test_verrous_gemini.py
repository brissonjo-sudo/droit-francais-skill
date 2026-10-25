"""Exclusion OS réellement exercée entre processus ; aucun service distant."""
import subprocess
import sys
import tempfile
import time
import unittest
import json
import hashlib
import socket
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import etude_v2, verrous_gemini
from bench import budget_gemini, quotas_gemini, profils_gemini
from _gemini_test_helpers import ecrire_profil


class VerrousProcessusTests(unittest.TestCase):
    def tenir_transition(self, root):
        code = """import sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from bench.etude_v2 import verrou_transition
root=Path(sys.argv[2])
with verrou_transition(root):
    (root/'pret').write_text('synthétique')
    time.sleep(.35)
"""
        child = subprocess.Popen([sys.executable, "-c", code, str(Path(__file__).resolve().parent), str(root)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(lambda: child.kill() if child.poll() is None else None)
        deadline = time.monotonic()+5
        while not (root / "pret").exists() and time.monotonic() < deadline and child.poll() is None:
            time.sleep(.01)
        self.assertTrue((root / "pret").exists())
        return child

    def terminer(self, child):
        out, err = child.communicate(timeout=5)
        self.assertEqual(0, child.returncode, err.decode(errors="replace"))

    def test_acquisition_attend_un_autre_processus_puis_reussit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            child = self.tenir_transition(root)
            start = time.monotonic()
            with etude_v2.verrou_transition(root):
                elapsed = time.monotonic()-start
            self.assertGreater(elapsed, .05)
            self.assertLess(elapsed, 2)
            self.terminer(child)

    def test_liberation_attend_un_autre_processus_sans_laisser_orphelin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "requete.lock"
            with verrous_gemini.verrou(root, path, attempt_id="TEST"):
                child = self.tenir_transition(root)
                start = time.monotonic()
            self.assertGreater(time.monotonic()-start, .05)
            self.assertFalse(path.exists())
            self.terminer(child)

    def test_lever_arret_preserve_budget_et_audite_empreinte_sous_exclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            budget = budget_gemini.Budget("123456789", "gemini-3.8-flash",
                {"rpm": 100, "rpd": 100, "tpm_entree": 100000}, _state=root)
            with budget.tentative(100, "generateContent", attempt_id="TEST"):
                budget.bloquer(429, attempt_id="TEST")
            before, stop = budget.journal.read_bytes(), budget.arret.read_bytes()
            with self.assertRaises(ValueError):
                verrous_gemini.lever_arret(budget, "TEST", "processus encore vivant")
            with mock.patch.object(etude_v2, "processus_actif", return_value=False):
                verrous_gemini.lever_arret(budget, "TEST", "fin de quota contrôlée")
            self.assertFalse(budget.arret.exists())
            self.assertEqual(before, budget.journal.read_bytes())
            receipt = etude_v2.lire(root / "reprises-gemini.jsonl")[0]
            self.assertEqual(hashlib.sha256(stop).hexdigest(), receipt["arret_sha256"])
            self.assertEqual("TEST", receipt["auteur_humain"])
            budget.verifier_arret()

    def test_lever_arret_refuse_requete_active_et_verrou_vide_ambigu(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            budget = budget_gemini.Budget("123456789", "gemini-3.8-flash",
                {"rpm": 100, "rpd": 100, "tpm_entree": 100000}, _state=root)
            budget.bloquer(429)
            lock = budget.dossier / "requete.lock"
            for content in (b"", json.dumps({"pid": 999999, "hote": socket.gethostname()}).encode()):
                lock.write_bytes(content)
                with mock.patch.object(etude_v2, "processus_actif", return_value=False):
                    with self.assertRaises(ValueError):
                        verrous_gemini.lever_arret(budget, "TEST", "reprise tardive")
                self.assertTrue(budget.arret.exists())
            self.assertFalse((root / "reprises-gemini.jsonl").exists())

    def test_verrou_vide_retrait_humain_audite_et_quota_perime_maintenance_seulement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = ecrire_profil(root)
            releve = root / "releve.json"
            data = json.loads(releve.read_bytes())
            data["observe_le"] = "2025-01-01T00:00:00+00:00"
            releve.write_text(json.dumps(data))
            lock = root / "profils.lock"
            lock.write_bytes(b"")
            proof = root / "processus.txt"
            proof.write_text("PREUVE HUMAINE SYNTHETIQUE absence de processus")
            with mock.patch.object(quotas_gemini, "LOCAL", root):
                with self.assertRaises(ValueError):
                    profils_gemini.charger(registry, "profil-01")
                self.assertEqual("123456789", profils_gemini.identite_maintenance(registry, "profil-01")["numero"])
                with self.assertRaises(ValueError):
                    verrous_gemini.retirer(root, lock, "TEST", "vide sans preuve")
                verrous_gemini.retirer(root, lock, "TEST", "processus examinés", preuve_absence_processus=proof)
            self.assertFalse(lock.exists())
            row = etude_v2.lire(root / "recuperations-gemini.jsonl")[0]
            self.assertTrue(row["verrou"]["verrou_vide"])
            self.assertEqual(hashlib.sha256(b"").hexdigest(), row["verrou_sha256"])
