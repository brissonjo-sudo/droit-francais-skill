"""Gate de qualification : preuves privées synthétiques et journal réel."""
import copy
import datetime as dt
import json
import sys
import tempfile
import unittest
import asyncio
import types
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import campaign, etude_v2, budget_gemini, qualification_gemini, quotas_gemini
from bench import agents, gemini_rest
from bench.flux import Trace, Appel
from _gemini_test_helpers import ecrire_profil
import bench


class QualificationGeminiTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.registry = ecrire_profil(self.root)
        for module, field in ((quotas_gemini, "LOCAL"), (qualification_gemini, "etat_canonique"),
                              (budget_gemini, "etat_canonique")):
            patch = mock.patch.object(module, field, return_value=self.root) if field == "etat_canonique" else mock.patch.object(module, field, self.root)
            patch.start()
            self.addCleanup(patch.stop)
        self.path = self.root / "qualification.json"
        self.data = {"schema": 2, "moteur": "gemini-rest-v2", "modele": "gemini-3.8-flash",
            "numero_projet": "123456789", "runtime_sha256": "runtime-synthetique",
            "raisonnement": "high",
            "candidat_sha256": campaign.digest(campaign.fichiers_figes()), "statut": "valide", "runs": [],
            "validation": {"valide_par": "RELECTEUR SYNTHETIQUE", "date_validation": dt.datetime.now(dt.timezone.utc).isoformat(),
                           "auth_free_confirmee": True, "isolation_confirmee": True}}
        with etude_v2.verrou(self.root):
            serie = campaign.digest(["qualification-rest-v2", self.data["candidat_sha256"], self.data["runtime_sha256"],
                self.data["numero_projet"], self.data["modele"], self.data["raisonnement"]])
            for bras in "ABCD":
                r = etude_v2.reserver(self.root, campaign.digest([serie, bras]), serie=serie, meta={
                    "modele": self.data["modele"], "moteur": "gemini-rest-v2", "bras": bras, "output": str(self.root / "journal.jsonl")})
                row = {"bras": bras, "attempt_id": r["attempt_id"], "statut_technique": "ok", "origine": "transport_REST",
                    "modele_effectif": self.data["modele"], "code_retour": 0,
                    "controles_procedure": {"isolation_appels": True}, "usage": {"catalogue_sha256": "catalogue-synthétique"},
                    "appels": [] if bras in "AB" else [{"outil": "mcp__droit-francais__get_article", "resultat": "SOURCE SYNTHETIQUE", "erreur": False}]}
                self.data["runs"].append(row)
                etude_v2.clore(self.root, r, statut="ok", preuve=campaign.digest(row))
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.data), encoding="utf-8")

    def check(self):
        return qualification_gemini.verifier(self.registry, "profil-01", runtime_sha256="runtime-synthetique")

    def test_gate_recu_journal_reels_coherents_mais_pas_validation_juridique(self):
        result = self.check()
        self.assertEqual("qualification_technique_validee", result["statut"])
        self.assertFalse(result["validation_juridique"])
        self.assertNotIn("123456789", json.dumps(result))

    def test_recu_modifie_ou_forge_sans_reservation_refuse(self):
        for field, value in (("attempt_id", "forge"), ("modele_effectif", "gemini-3.5-flash"), ("code_retour", 2)):
            before = copy.deepcopy(self.data)
            self.data["runs"][0][field] = value
            self.save()
            with self.assertRaises(ValueError):
                self.check()
            self.data = before
        self.data["runs"][0]["reponse"] = "ajout après clôture"
        self.save()
        with self.assertRaises(ValueError):
            self.check()

    def test_projet_modele_runtime_et_revue_humaine_obligatoires(self):
        for field, value in (("numero_projet", "987654321"), ("modele", "gemini-3.5-flash"),
                             ("runtime_sha256", "autre"), ("statut", "a_relire")):
            old = self.data[field]
            self.data[field] = value
            self.save()
            with self.assertRaises(ValueError):
                self.check()
            self.data[field] = old
        self.data["validation"]["valide_par"] = ""
        self.save()
        with self.assertRaises(ValueError):
            self.check()

    def test_arret_429_gate_avant_reservation_et_transport(self):
        budget = budget_gemini.Budget("123456789", "gemini-3.8-flash", {"rpm": 100, "rpd": 100, "tpm_entree": 100000})
        budget.dossier.mkdir(parents=True)
        budget.bloquer(429)
        before = len(etude_v2.reservations(self.root))
        with self.assertRaises(budget_gemini.ArretBudget) as error:
            self.check()
        self.assertEqual("quota_429", error.exception.categorie)
        self.assertEqual(before, len(etude_v2.reservations(self.root)))

    def test_qualifier_cli_quatre_reponses_avec_derniere_panne_retourne_2(self):
        with mock.patch.object(qualification_gemini, "executer", return_value={"reponses_techniques": 4, "technique_ok": False}):
            code = qualification_gemini.main(["--registre", "r", "--profil", "profil-01", "--config", "c", "--sortie", "s"])
        self.assertEqual(2, code)

    def test_relabelisation_runtime_sans_nouvelle_qualification_refusee(self):
        self.data["runtime_sha256"] = "runtime-modifie"
        self.save()
        with self.assertRaises(ValueError):
            qualification_gemini.verifier(self.registry, "profil-01", runtime_sha256="runtime-modifie")

    def chemin_technique(self, *, crash=False, derniere_panne=False, source_absente=False,
                        reprendre=False, runtime_modifie=False, catalogue_modifie=False, invalider_complete=False):
        root = self.root / "technique"
        registry = ecrire_profil(root)
        state = root / "etat"
        target = root / "recu.json"
        cfg = root / "config.json"
        cfg.write_text(json.dumps({"familles": [{"nom": "gemini", "moteur": "gemini-rest-v2",
            "modele_demande": "gemini-3.8-flash", "auth": "cle_api_gratuite", "raisonnement": "high"}]}))
        appels_c = 0
        async def simulated(client, *, prompt, bras, plafond, options):
            nonlocal appels_c
            await client.transport.fermer()
            trace = Trace(texte_final="REPONSE TECHNIQUE SYNTHETIQUE", modele="gemini-3.8-flash")
            trace.usage = {"catalogue_sha256": "catalogue-synthétique"}
            if bras in "CD":
                trace.appels = [Appel(0, "mcp__droit-francais__get_article", {}, "SOURCE SYNTHETIQUE", False)]
            if bras == "C":
                appels_c += 1
                if source_absente and appels_c == 1:
                    trace.appels[0] = Appel(0, "mcp__droit-francais__get_article", {}, "ERREUR SYNTHETIQUE", True)
            if catalogue_modifie and bras == "D":
                trace.usage["catalogue_sha256"] = "autre-catalogue"
            failed = derniere_panne and bras == "D"
            return agents.Execution(trace, "FLUX SYNTHETIQUE", 2 if failed else 0,
                statut="infra_error" if failed else "ok", categorie_infra="transport" if failed else "")
        runtime = types.ModuleType("bench.runtime_v2")
        runtime.relever = mock.Mock(side_effect=[{"runtime": "initial"}, {"runtime": "modifié"}]) if runtime_modifie else lambda config: {"runtime": "synthétique"}
        with (mock.patch.dict(sys.modules, {"bench.runtime_v2": runtime}),
              mock.patch.object(bench, "runtime_v2", runtime, create=True),
              mock.patch.object(budget_gemini, "etat_canonique", return_value=state),
              mock.patch.object(qualification_gemini, "etat_canonique", return_value=state),
              mock.patch.dict("os.environ", {"GEMINI_API_KEY": "secret-test"}, clear=True),
              mock.patch.object(gemini_rest, "executer_mcp", side_effect=simulated)):
            if crash:
                original = etude_v2.atomique
                def ecrire(path, data):
                    if crash is True or len(data["runs"]) == 4:
                        raise OSError("crash synthétique")
                    original(path, data)
                with mock.patch.object(etude_v2, "atomique", side_effect=ecrire):
                    with self.assertRaises(OSError):
                        qualification_gemini.executer(registry, "profil-01", cfg, target)
                if crash == "D":
                    self.assertEqual(3, len(json.loads(target.read_bytes())["runs"]))
                    last = etude_v2.reservations(state)[-1]
                    etude_v2.clore_interruption(state, last["attempt_id"], "TEST", "crash après D")
                    result = qualification_gemini.executer(registry, "profil-01", cfg, target)
                    self.assertTrue(result["technique_ok"])
            else:
                result = qualification_gemini.executer(registry, "profil-01", cfg, target)
                self.assertEqual(not any((derniere_panne, source_absente, runtime_modifie, catalogue_modifie)), result["technique_ok"])
                if reprendre:
                    result = qualification_gemini.executer(registry, "profil-01", cfg, target)
                    self.assertTrue(result["technique_ok"])
                if invalider_complete:
                    serie = etude_v2.reservations(state)[0]["series_sha256"]
                    etude_v2.invalider(state, serie, "runtime", "invalidation synthétique après quatre bras")
                    before = target.read_bytes()
                    with mock.patch.object(gemini_rest, "preparer_client") as prepare:
                        with self.assertRaisesRegex(ValueError, "invalidée"):
                            qualification_gemini.executer(registry, "profil-01", cfg, target)
                        prepare.assert_not_called()
                    self.assertEqual(before, target.read_bytes())
        return state, target

    def test_chemin_quatre_bras_reel_journal_et_quatrieme_panne(self):
        state, target = self.chemin_technique(derniere_panne=True)
        self.assertEqual(4, len(etude_v2.reservations(state)))
        self.assertEqual(4, len(etude_v2.clotures(state)))
        data = json.loads(target.read_bytes())
        self.assertEqual("a_relire", data["statut"])
        self.assertFalse(data["validation"]["auth_free_confirmee"])
        self.assertEqual("infra_error", data["runs"][-1]["statut_technique"])

    def test_crash_apres_raw_avant_recu_est_recouvrable(self):
        state, target = self.chemin_technique(crash=True)
        reservation = etude_v2.reservations(state)[0]
        self.assertFalse(target.exists())
        self.assertEqual(1, len(etude_v2.lire(Path(reservation["output"]))))
        self.assertFalse(etude_v2.clotures(state))
        etude_v2.clore_interruption(state, reservation["attempt_id"], "RELECTEUR SYNTHETIQUE", "crash de test")
        self.assertEqual("ok", etude_v2.clotures(state)[reservation["attempt_id"]]["statut"])

    def test_source_en_erreur_cloture_outil_et_seconde_tentative_possible(self):
        state, target = self.chemin_technique(source_absente=True, reprendre=True)
        receipts = etude_v2.reservations(state)
        self.assertEqual(5, len(receipts))
        c = [r for r in receipts if r["bras"] == "C"]
        self.assertEqual([1, 2], [r["tentative"] for r in c])
        first = etude_v2.clotures(state)[c[0]["attempt_id"]]
        self.assertEqual("infra_error", first["statut"])
        self.assertEqual("outil", first["categorie_infra"])
        self.assertEqual(4, len(json.loads(target.read_bytes())["runs"]))

    def test_crash_dernier_raw_reprise_reconstruit_recu_sans_nouvelle_reservation(self):
        state, target = self.chemin_technique(crash="D")
        self.assertEqual(4, len(etude_v2.reservations(state)))
        self.assertEqual(4, len(etude_v2.clotures(state)))
        self.assertEqual(4, len(json.loads(target.read_bytes())["runs"]))

    def test_serie_invalidee_refuse_meme_avec_quatre_bras_acquis(self):
        state, target = self.chemin_technique(invalider_complete=True)
        self.assertEqual(4, len(etude_v2.reservations(state)))
        self.assertEqual(4, len(etude_v2.clotures(state)))

    def test_runtime_modifie_invalide_la_serie_avant_cloture(self):
        state, target = self.chemin_technique(runtime_modifie=True)
        receipt = etude_v2.reservations(state)[0]
        with self.assertRaises(ValueError):
            etude_v2.sain(state, receipt["series_sha256"])
        self.assertEqual("runtime", etude_v2.clotures(state)[receipt["attempt_id"]]["categorie_infra"])

    def test_catalogue_cd_different_invalide_la_serie(self):
        state, target = self.chemin_technique(catalogue_modifie=True)
        self.assertEqual("gel", json.loads(target.read_bytes())["runs"][-1]["categorie_infra"])
        with self.assertRaises(ValueError):
            etude_v2.sain(state, etude_v2.reservations(state)[0]["series_sha256"])
