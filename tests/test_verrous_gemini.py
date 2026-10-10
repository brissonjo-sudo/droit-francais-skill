"""Exclusion OS réellement exercée entre processus ; aucun service distant."""
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import etude_v2


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
        try:
            from bench import verrous_gemini
        except ImportError:
            self.skipTest("verrou Gemini fourni par le lot #117 non encore intégré")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "requete.lock"
            with verrous_gemini.verrou(root, path, attempt_id="TEST"):
                child = self.tenir_transition(root)
                start = time.monotonic()
            self.assertGreater(time.monotonic()-start, .05)
            self.assertFalse(path.exists())
            self.terminer(child)
