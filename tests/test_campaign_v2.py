"""Régressions réelles du collecteur/journal ; moteurs simulés, aucun appel externe."""
from __future__ import annotations

import contextlib
import copy
import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from bench import agents, campaign, etude_v2, revue_v2, ablation
from bench.contexte import ContexteExecution
from bench.flux import Trace, Appel, PREFIXE_MCP


class CampaignV2(unittest.TestCase):
    def config(self):
        cfg = campaign.read_json(ROOT / "tests/campaign/config.example.json")
        for f in cfg["familles"]:
            f.update(modele_demande=f["nom"] + "-exact", executable=f["nom"], raisonnement="high", version_cli="1")
        cfg["familles"][2].update(gemini_registre="registre-prive", gemini_profil="projet", qualification_sha256=campaign.digest({"modele": "gemini-exact"}))
        return cfg

    def contexte(self, state, backend=None):
        cfg = self.config()
        cases = [campaign.corpus()[0]]
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(campaign, "corpus", return_value=cases))
        gel = {"schema": 2, "series_sha256": "s", "config": cfg, "runtime": {}, "runtime_sha256": "runtime",
               "racine_etat": str(state), "plan": campaign.planifier(cfg)}
        for family in campaign.FAMILLES:
            campaign.write_json(state / f"s/preflight-{family}.json", {})
        for target, value in (("bench.campaign.verifier_gel", None), ("bench.campaign.verifier_runtime", None),
                              ("bench.campaign.gold_pret", True), ("bench.campaign.preflight_pret", True),
                              ("bench.campaign.version_cli", "1"), ("bench.preconditions.abonnement", True),
                              ("bench.campaign.qualification_gemini", {"modele": "gemini-exact"})):
            stack.enter_context(mock.patch(target, return_value=value))
        calls = []
        def simulated(**kw):
            options = kw["options"]
            etude_v2.verifier_contexte(options.contexte)
            calls.append((options.modele, kw["bras"], options.contexte))
            trace = Trace(modele=options.modele, texte_final="réponse")
            if kw["bras"] in ("C", "D"):
                trace.appels = [Appel(0, PREFIXE_MCP + "get_article", {}, "texte officiel")]
            return agents.Execution(trace, '{"type":"result","is_error":false}', 0)
        engine = backend or mock.Mock()
        if backend is None:
            engine.executer.side_effect = simulated
        stack.enter_context(mock.patch.object(agents, "backend", return_value=engine))
        return gel, stack, engine, calls

    def reservation(self, state, identity="id", output=None):
        return etude_v2.reserver(state, identity, serie="s", meta={"famille": "claude", "id": "M01-a",
            "bras": "A", "repetition": 1, "phase": "pilote", "modele": "claude-exact",
            "moteur": "cli-native", "output": str((output or state / "s/out.jsonl").resolve())})

    def test_collecteur_ne_rejoue_jamais_un_succes_acquis(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            gel, stack, engine, calls = self.contexte(state)
            with stack:
                self.assertEqual(4, campaign.collecter(gel, "claude", "pilote", state=state))
                self.assertEqual(4, campaign.collecter(gel, "claude", "pilote", state=state))
                self.assertEqual(0, campaign.collecter(gel, "claude", "pilote", state=state))
            ids = [c[2].identite for c in calls]
            self.assertEqual(8, len(set(ids)))
            self.assertEqual(8, len(etude_v2.reservations(state)))

    def test_entrelacement_reel_familles_et_repetitions(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            gel, stack, engine, calls = self.contexte(state)
            with stack:
                self.assertEqual(24, campaign.collecter_entrelace(gel, "pilote", state=state))
                self.assertEqual(0, campaign.collecter_entrelace(gel, "pilote", state=state))
            actual = [x[0].split("-")[0] for x in calls]
            self.assertEqual([f for f in ("claude", "codex", "gemini", "codex", "gemini", "claude") for _ in range(4)], actual)
            self.assertEqual([1] * 12 + [2] * 12, [x[2].reservation["repetition"] for x in calls])

    def test_concurrence_deux_collecteurs_sans_rejeu(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            gel, stack, engine, calls = self.contexte(state)
            arrived, release = threading.Event(), threading.Event()
            original = engine.executer.side_effect
            def pause(**kw):
                arrived.set()
                if not release.wait(5):
                    raise RuntimeError("barrière de test expirée")
                return original(**kw)
            engine.executer.side_effect = pause
            errors = []
            def run():
                try:
                    campaign.collecter(gel, "claude", "pilote", state=state)
                except Exception as e:
                    errors.append(e)
            with stack:
                worker = threading.Thread(target=run)
                worker.start()
                self.assertTrue(arrived.wait(5))
                try:
                    with self.assertRaisesRegex(ValueError, "verrou"):
                        campaign.collecter(gel, "claude", "pilote", state=state)
                finally:
                    release.set()
                    worker.join(5)
                self.assertFalse(worker.is_alive())
                self.assertEqual([], errors)
                self.assertEqual(4, campaign.collecter(gel, "claude", "pilote", state=state))
            self.assertEqual(8, len(calls))
            self.assertEqual(8, len({x[2].identite for x in calls}))

    def test_crash_reservation_comptee_cloture_explicite_et_plafond(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            engine = mock.Mock()
            engine.executer.side_effect = KeyboardInterrupt()
            gel, stack, _, _ = self.contexte(state, engine)
            with stack:
                with self.assertRaises(KeyboardInterrupt):
                    campaign.collecter(gel, "claude", "pilote", state=state)
                with self.assertRaisesRegex(ValueError, "indéterminée"):
                    campaign.collecter(gel, "claude", "pilote", state=state)
                r = etude_v2.reservations(state)[0]
                etude_v2.clore_interruption(state, r["attempt_id"], "Relecteur", "Processus terminé, aucun résultat durable")
                with self.assertRaises(KeyboardInterrupt):
                    campaign.collecter(gel, "claude", "pilote", state=state)
                r2 = etude_v2.reservations(state)[1]
                etude_v2.clore_interruption(state, r2["attempt_id"], "Relecteur", "Processus terminé")
                with self.assertRaisesRegex(ValueError, "deux tentatives"):
                    campaign.collecter(gel, "claude", "pilote", state=state)
                etude_v2.declarer_manquant(state, "s", r["identite"], "Relecteur", "Deux interruptions ; paire exclue")
                self.assertIn(r["identite"], etude_v2.manquants(state, "s"))
            self.assertEqual(2, engine.executer.call_count)

    def test_crash_apres_resultat_durable_preserve_le_succes(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            gel, stack, engine, calls = self.contexte(state)
            with stack:
                with mock.patch.object(etude_v2, "clore", side_effect=KeyboardInterrupt()):
                    with self.assertRaises(KeyboardInterrupt):
                        campaign.collecter(gel, "claude", "pilote", state=state)
                r = etude_v2.reservations(state)[0]
                etude_v2.clore_interruption(state, r["attempt_id"], "Relecteur", "Résultat complet retrouvé")
                self.assertEqual("ok", etude_v2.clotures(state)[r["attempt_id"]]["statut"])
                campaign.collecter(gel, "claude", "pilote", state=state)
            self.assertEqual(1, sum(x[2].identite == r["identite"] for x in calls))

    def test_contamination_invalide_definitivement_la_serie(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            engine = mock.Mock()
            engine.executer.return_value = agents.Execution(Trace(modele="claude-exact",
                texte_final=campaign.read_json(campaign.CORPUS)["temoin_corriges"]), '{"type":"result"}', 0)
            gel, stack, _, _ = self.contexte(state, engine)
            with stack:
                with self.assertRaises(campaign.ArretCollecte):
                    campaign.collecter(gel, "claude", "pilote", state=state)
                with self.assertRaisesRegex(ValueError, "définitivement"):
                    campaign.collecter(gel, "claude", "pilote", state=state)
            self.assertEqual(1, engine.executer.call_count)
            self.assertEqual("contamination", etude_v2.lire(state / "s/invalidations.jsonl")[0]["categorie_infra"])

    def test_deux_pannes_reprise_apres_declaration_motivee(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            gel, stack, engine, calls = self.contexte(state)
            original = engine.executer.side_effect
            attempts = [0]
            def fail_twice(**kw):
                attempts[0] += 1
                result = original(**kw)
                if attempts[0] <= 2:
                    result.statut, result.categorie_infra = "infra_error", "transport"
                return result
            engine.executer.side_effect = fail_twice
            with stack:
                for _ in range(2):
                    with self.assertRaises(campaign.ArretCollecte):
                        campaign.collecter(gel, "claude", "pilote", state=state)
                key = etude_v2.reservations(state)[0]["identite"]
                with self.assertRaises(ValueError):
                    etude_v2.declarer_manquant(state, "s", key, "", "motif")
                etude_v2.declarer_manquant(state, "s", key, "Relecteur", "Deux pannes, sans imputation")
                self.assertEqual(4, campaign.collecter(gel, "claude", "pilote", state=state))

    def test_budget100_global_avant_appel_et_reprise_lendemain(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            with etude_v2.verrou(state):
                for n in range(100):
                    r = etude_v2.reserver(state, str(n), serie="s", meta={}, jour="2026-10-10")
                    etude_v2.clore(state, r, statut="infra_error", categorie="transport")
                with self.assertRaisesRegex(ValueError, "100"):
                    etude_v2.reserver(state, "autre", serie="s", meta={}, jour="2026-10-10")
                etude_v2.reserver(state, "autre", serie="s", meta={}, jour="2026-10-11")
            self.assertEqual(101, len(etude_v2.reservations(state)))

    def test_gel_ou_runtime_changes_arret_avant_appel(self):
        for category, target in (("gel", "verifier_gel"), ("runtime", "verifier_runtime")):
            with self.subTest(category=category), tempfile.TemporaryDirectory() as d:
                state = Path(d)
                gel, stack, engine, calls = self.contexte(state)
                with stack, mock.patch.object(campaign, target, side_effect=ValueError(category + " modifié")):
                    with self.assertRaises(ValueError):
                        campaign.collecter(gel, "claude", "pilote", state=state)
                engine.executer.assert_not_called()
                self.assertEqual(category, etude_v2.lire(state / "s/invalidations.jsonl")[0]["categorie_infra"])

    def test_runtime_change_pendant_reponse_invalide(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            gel, stack, engine, calls = self.contexte(state)
            with stack, mock.patch.object(campaign, "verifier_runtime", side_effect=[None, None, ValueError("runtime modifié")]):
                with self.assertRaises(campaign.ArretCollecte):
                    campaign.collecter(gel, "claude", "pilote", state=state)
            self.assertEqual(1, len(calls))
            self.assertTrue(etude_v2.lire(state / "s/invalidations.jsonl"))

    def test_anciens_journaux_et_gels_refuses_sans_migration(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "budget.jsonl"
            path.write_text('{"jour":"2026-10-10","identite":"x"}\n', encoding="utf-8")
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "migration"):
                etude_v2.reservations(Path(d))
            self.assertEqual(before, path.read_bytes())
        with self.assertRaisesRegex(ValueError, "antérieurs"):
            campaign.verifier_gel({"schema": 1})

    def test_parametres_alias_moteur_et_budget_inconnus_refuses(self):
        cfg = self.config()
        campaign.valider_config(cfg)
        for change in ({"ordre_collecte": "ancien"}, {"max_tentatives_par_identite": 3}, {"non_supporte": 1}, {"timeout_s": 0}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                campaign.valider_config({**cfg, **change})
        for alias in ("AUTO", "SoNnEt", "BEST", "x-latest"):
            value = copy.deepcopy(cfg)
            value["familles"][0]["modele_demande"] = alias
            with self.assertRaisesRegex(ValueError, "alias"):
                campaign.valider_config(value)

    def test_racine_etat_confinement_et_contextes_durables(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            with self.assertRaisesRegex(ValueError, "hors"):
                campaign.confiner(state.parent / "preuve.json", state)
            with etude_v2.verrou(state):
                r = self.reservation(state)
                ctx = ContexteExecution("s", "id", r["attempt_id"], 1, "claude-exact", "cli-native", time.monotonic() + 1, r, state)
                etude_v2.verifier_contexte(ctx)
                etude_v2.clore(state, r, statut="infra_error", categorie="delai")
                with self.assertRaisesRegex(ValueError, "clôturée"):
                    etude_v2.verifier_contexte(ctx)

    def test_journal_tronque_et_categorie_infra_inconnue_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            (state / "budget.jsonl").write_text('{"schema":2,', encoding="utf-8")
            with self.assertRaises(ValueError):
                etude_v2.reservations(state)
            (state / "budget.jsonl").unlink()
            with etude_v2.verrou(state):
                r = self.reservation(state)
                with self.assertRaisesRegex(ValueError, "catégorie"):
                    etude_v2.clore(state, r, statut="infra_error", categorie="invente")

    def test_paquet_exclut_pannes_sel_prive_non_deductible(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            p = state / "s/results.jsonl"
            with etude_v2.verrou(state):
                for n, status in enumerate(("ok", "infra_error")):
                    reservation = self.reservation(state, "id" + str(n), p)
                    row = {**reservation, "statut_technique": status, "reponse": "texte",
                           "categorie_infra": "transport" if status == "infra_error" else ""}
                    try:
                        campaign.acquerir(state, p, row, reservation)
                    except campaign.ArretCollecte:
                        pass
            target = state / "packet.json"
            campaign.paquet_revue([p], target, state=state)
            packet = campaign.read_json(target)
            self.assertEqual(1, len(packet))
            self.assertNotIn("famille", packet[0])
            self.assertNotIn("bras", packet[0])
            self.assertNotEqual(campaign.digest(["aveugle", "id0"]), packet[0]["token"])
            self.assertFalse(target.with_name("packet-mapping-prive.json").exists())
            self.assertIn("sel", campaign.read_json(campaign.mapping_prive(target, state)))
            self.assertEqual(1, len(campaign.read_json(state / "prive" / (campaign.digest(str(target.resolve())) + "-incidents-humains.json"))))

    def test_revue_humaine_separee_revision_arbitrage_prioritaire(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            result = {"identite": "id", "reponse": "texte"}
            judge = {"identite": "id", "axes": {a: "faux" for a in campaign.AXES}}
            row = {"schema": 2, "identite": "id", "relecteur_humain": "Juriste", "justification_humaine": "Source et faits relus",
                "date_validation": "2026-10-10", "validation_humaine": True, "avis_final": True,
                "arbitrage": "corriger_juge", "axes": {a: "correct" for a in campaign.AXES},
                "revision": 1, "precedent_sha256": "", "resultat_sha256": campaign.digest(result), "jugement_sha256": campaign.digest(judge)}
            path = state / "humains.jsonl"
            revue_v2.ajouter(path, row, {"id": result}, {"id": judge}, state=state)
            second = {**row, "revision": 2, "precedent_sha256": campaign.digest(row), "justification_humaine": "Seconde relecture"}
            revue_v2.ajouter(path, second, {"id": result}, {"id": judge}, state=state)
            self.assertEqual(second, revue_v2.avis(path, {"id": result}, {"id": judge})["id"])
            self.assertEqual(2, len(etude_v2.lire(path)))
            with self.assertRaisesRegex(ValueError, "révision|Révision"):
                revue_v2.ajouter(path, second, {"id": result}, {"id": judge}, state=state)
            with self.assertRaisesRegex(ValueError, "périmé"):
                revue_v2.avis(path, {"id": {**result, "reponse": "modifiée"}}, {"id": judge})

    def test_verrou_abandonne_ne_retire_jamais_processus_actif(self):
        import os
        import socket
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            lock = state / "collection.lock"
            campaign.write_json(lock, {"schema": 2, "pid": os.getpid(), "hote": socket.gethostname(), "token": "x"})
            with self.assertRaisesRegex(ValueError, "actif"):
                etude_v2.retirer_verrou_abandonne(state, "Humain", "Contrôle")
            self.assertTrue(lock.exists())
            with mock.patch.object(etude_v2, "processus_actif", return_value=False):
                etude_v2.retirer_verrou_abandonne(state, "Humain", "PID terminé vérifié")
            self.assertFalse(lock.exists())

    def test_juge_ne_peut_pas_s_autodeclarer_humain_et_pas_rejoue(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            gel, stack, engine, calls = self.contexte(state)
            result_path = state / "s/pilote-claude.jsonl"
            packet = state / "paquet.json"
            target = state / "juges.jsonl"
            with stack:
                campaign.collecter(gel, "claude", "pilote", state=state)
                campaign.paquet_revue([result_path], packet, state=state)
                def judge(**kw):
                    etude_v2.verifier_contexte(kw["options"].contexte)
                    data = {"axes": {a: "correct" for a in campaign.AXES}, "justification": "Lecture",
                            "relecteur_humain": "fausse signature", "validation_humaine": True, "avis_final": True}
                    return agents.Execution(Trace(modele="codex-exact", texte_final=json.dumps(data)), "", 0)
                engine.executer.side_effect = judge
                self.assertEqual(4, campaign.juger_paquet(gel, packet, "codex", target, state=state))
                count = engine.executer.call_count
                self.assertEqual(0, campaign.juger_paquet(gel, packet, "codex", target, state=state))
                self.assertEqual(count, engine.executer.call_count)
            rows = etude_v2.lire(target)
            self.assertTrue(all("relecteur_humain" not in r and "validation_humaine" not in r for r in rows))

    def test_rapport_arbitrage_final_humain_prime_sur_juge(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            gel, stack, engine, calls = self.contexte(state)
            with stack, mock.patch.object(campaign, "pret_collecte"):
                campaign.collecter(gel, "claude", "principale", state=state)
                results = state / "s/principale-claude.jsonl"
                row = etude_v2.lire(results)[0]
                key = row["identite"]
                packet = state / "paquet.json"
                campaign.paquet_revue([results], packet, state=state)
                def judge_model(**kw):
                    etude_v2.verifier_contexte(kw["options"].contexte)
                    answer = {"axes": {a: "faux" for a in campaign.AXES}, "justification": "Lecture"}
                    return agents.Execution(Trace(modele="codex-exact", texte_final=json.dumps(answer)), "", 0)
                engine.executer.side_effect = judge_model
                reviews = state / "juges.jsonl"
                campaign.juger_paquet(gel, packet, "codex", reviews, state=state)
                judge = next(r for r in etude_v2.lire(reviews) if r["identite"] == key)
                h = {"schema": 2, "identite": key, "revision": 1, "precedent_sha256": "",
                    "relecteur_humain": "Juriste", "justification_humaine": "Source comparée",
                    "date_validation": "2026-10-10", "validation_humaine": True, "avis_final": True,
                    "arbitrage": "corriger_juge", "axes": {a: "correct" for a in campaign.AXES},
                    "resultat_sha256": campaign.digest(row), "jugement_sha256": campaign.digest(judge)}
                human = state / "humains.jsonl"
                revue_v2.ajouter(human, h, {key: row}, {key: judge}, state=state)
                report = campaign.rapport([results], reviews, humains=human, frozen=gel, state=state)
            mode = report["par_mode"][0]
            self.assertEqual(1, mode["effectifs"]["correct"])
            self.assertEqual(3, mode["effectifs"].get("revue_humaine_requise", 0))
            self.assertEqual("revue_incomplete", report["statut"])
            self.assertEqual([], report["exemples_readme"])
            self.assertTrue(report["taux_manquants_par_strate"])

    def test_ablation_contaminee_invalidee_et_passages_exacts(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            gel, stack, engine, calls = self.contexte(state)
            recipe = state / "recette.json"
            report = state / "rapport.json"
            campaign.write_json(report, {"statut": "revue_complete_a_valider", "series_sha256": "s"})
            before = (ROOT / "skill/SKILL.md").read_bytes()
            campaign.write_json(recipe, [{"mode": 1, "valide_par": "Humain", "raison": "Test d'attribution",
                "regles_partagees": ["P1"], "passages_exacts": ["ABSENT_DU_SKILL"]}])
            with stack:
                with self.assertRaisesRegex(ValueError, "provenance privée"):
                    ablation.preparer(gel, recipe, report, state / "experience-fabriquee", state=state)
                with mock.patch.object(campaign, "verifier_rapport_acquis"):
                    with self.assertRaisesRegex(ValueError, "absent ou ambigu"):
                        ablation.preparer(gel, recipe, report, state / "experience-invalide", state=state)
                campaign.write_json(report, {"statut": "revue_complete_a_valider", "series_sha256": "autre"})
                with self.assertRaisesRegex(ValueError, "principale complète"):
                    ablation.preparer(gel, recipe, report, state / "experience-autre", state=state)
                text = "variante fixe"
                path = state / "variant.md"
                path.write_text(text, encoding="utf-8")
                import hashlib
                plan = {"schema": 2, "series_sha256": "s", "variantes": [{"mode": 1, "path": str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}]}
                plan["plan_sha256"] = campaign.digest(plan)
                plan_path = state / "plan.json"
                campaign.write_json(plan_path, plan)
                engine.executer.return_value = agents.Execution(Trace(modele="claude-exact",
                    texte_final=campaign.read_json(campaign.CORPUS)["temoin_corriges"]), '{"type":"result"}', 0)
                engine.executer.side_effect = None
                with mock.patch.object(campaign, "pret_collecte"), mock.patch.object(ablation, "verifier_rapport_plan"):
                    with self.assertRaises(campaign.ArretCollecte):
                        ablation.collecter(gel, plan_path, "claude", state=state)
                row = etude_v2.lire(state / "s" / f"ablation-{plan['plan_sha256']}-claude.jsonl")[0]
                self.assertEqual("infra_error", row["statut_technique"])
                self.assertEqual("contamination", row["categorie_infra"])
                self.assertEqual(before, (ROOT / "skill/SKILL.md").read_bytes())

    def test_atomicite_json_interruption_preserve_ancien_document(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "gel.json"
            campaign.write_json(path, {"valeur": "avant"})
            before = path.read_bytes()
            with mock.patch.object(etude_v2.os, "replace", side_effect=OSError("interruption simulée")):
                with self.assertRaises(OSError):
                    campaign.write_json(path, {"valeur": "après"})
            self.assertEqual(before, path.read_bytes())
            self.assertEqual([path], list(Path(d).iterdir()))

    def test_recuperations_concurrentes_ne_suppriment_pas_nouveau_verrou(self):
        import os
        import socket
        from bench.journal import Journal
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            campaign.write_json(state / "collection.lock", {"schema": 2, "pid": os.getpid(),
                "hote": socket.gethostname(), "token": "ancien"})
            original = Journal.ajouter
            def interleave(journal, row):
                with self.assertRaisesRegex(ValueError, "transition"):
                    etude_v2.retirer_verrou_abandonne(state, "B", "Contrôle concurrent")
                with self.assertRaisesRegex(ValueError, "transition"):
                    with etude_v2.verrou(state):
                        self.fail("acquisition concurrente impossible")
                original(journal, row)
            with mock.patch.object(etude_v2, "processus_actif", return_value=False), mock.patch.object(Journal, "ajouter", interleave):
                etude_v2.retirer_verrou_abandonne(state, "A", "PID terminé")
            self.assertEqual(1, len(etude_v2.lire(state / "recuperations.jsonl")))
            with etude_v2.verrou(state):
                self.assertTrue((state / "collection.lock").exists())
            self.assertFalse((state / "collection.lock").exists())

    def test_deadline_absolue_borne_native_apres_verifications(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            gel, stack, engine, calls = self.contexte(state)
            with stack, etude_v2.verrou(state):
                r = self.reservation(state)
                f = gel["config"]["familles"][0]
                options = campaign.options_pour(gel, f)
                options.contexte = ContexteExecution("s", r["identite"], r["attempt_id"], 1,
                    "claude-exact", "cli-native", 100, r, state)
                with mock.patch.object(campaign.time, "monotonic", side_effect=[98, 99, 99.5]):
                    campaign.executer_fige(gel, f, prompt="x", bras="A", plafond=0, options=options)
                self.assertEqual(1, engine.executer.call_args.kwargs["options"].timeout_s)
                count = engine.executer.call_count
                with mock.patch.object(campaign.time, "monotonic", return_value=101):
                    response = campaign.executer_fige(gel, f, prompt="x", bras="A", plafond=0, options=options)
                self.assertEqual("delai", response.categorie_infra)
                self.assertEqual(count, engine.executer.call_count)
                self.assertFalse(etude_v2.lire(state / "s/invalidations.jsonl"))

    def test_preflight_recu_autoritaire_et_vraie_lecture_source(self):
        validator = campaign.preflight_pret
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            gel, stack, engine, calls = self.contexte(state)
            with stack:
                path = campaign.preflight(gel, "claude", state=state)
                receipt = campaign.read_json(path)
                receipt.update(revue_isolation_par="Humain", preuve_isolation="Lecture traces",
                               auth_confirmee=True, autorise_collecte=True)
                f = gel["config"]["familles"][0]
                self.assertTrue(validator(receipt, gel, f, state=state))
                changed = copy.deepcopy(receipt)
                changed["runs"][1]["reponse"] = "succès fabriqué"
                self.assertFalse(validator(changed, gel, f, state=state))
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            gel, stack, engine, calls = self.contexte(state)
            def no_source(**kw):
                trace = Trace(modele="claude-exact", texte_final="contrôle")
                if kw["bras"] == "C":
                    trace.appels = [Appel(0, "ToolSearch", {}, "outil trouvé")]
                return agents.Execution(trace, '{"type":"result"}', 0)
            engine.executer.side_effect = no_source
            with stack:
                with self.assertRaises(campaign.ArretCollecte):
                    campaign.preflight(gel, "claude", state=state)
                path = state / "s/preflight-claude.json"
                receipt = campaign.read_json(path)
                receipt.update(revue_isolation_par="Humain", preuve_isolation="Lecture traces",
                               auth_confirmee=True, autorise_collecte=True)
                self.assertFalse(validator(receipt, gel, gel["config"]["familles"][0], state=state))
                def with_source(**kw):
                    trace = Trace(modele="claude-exact", texte_final="source")
                    trace.appels = [Appel(0, PREFIXE_MCP + "get_article", {}, "texte officiel")]
                    return agents.Execution(trace, '{"type":"result"}', 0)
                engine.executer.side_effect = with_source
                campaign.preflight(gel, "claude", state=state)
                receipt = campaign.read_json(path)
                receipt.update(revue_isolation_par="Humain", preuve_isolation="Lecture traces",
                               auth_confirmee=True, autorise_collecte=True)
                self.assertTrue(validator(receipt, gel, gel["config"]["familles"][0], state=state))
                self.assertEqual(3, len(etude_v2.reservations(state)))

    def test_rapport_refuse_identite_reconstruite_et_jugement_non_cloture(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            gel, stack, engine, calls = self.contexte(state)
            with stack, mock.patch.object(campaign, "pret_collecte"):
                campaign.collecter(gel, "claude", "principale", state=state)
                results = state / "s/principale-claude.jsonl"
                before = results.read_bytes()
                rows = etude_v2.lire(results)
                rows[0]["identite"] = "reconstruite"
                results.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "clôture cohérente"):
                    campaign.rapport([results], state / "juges.jsonl", frozen=gel, state=state)
                results.write_bytes(before)
                packet = state / "packet.json"
                campaign.paquet_revue([results], packet, state=state)
                engine.executer.side_effect = lambda **kw: agents.Execution(Trace(modele="codex-exact",
                    texte_final=json.dumps({"axes": {a: "correct" for a in campaign.AXES}})), "", 0)
                target = state / "juges.jsonl"
                with mock.patch.object(etude_v2, "clore", side_effect=KeyboardInterrupt):
                    with self.assertRaises(KeyboardInterrupt):
                        campaign.juger_paquet(gel, packet, "codex", target, state=state)
                with self.assertRaisesRegex(ValueError, "clôture cohérente"):
                    campaign.rapport([results], target, frozen=gel, state=state)
                judge = etude_v2.lire(target)[0]
                etude_v2.clore_interruption(state, judge["attempt_id"], "Humain", "PID terminé")
                self.assertEqual("revue_incomplete", campaign.rapport([results], target, frozen=gel, state=state)["statut"])

    def test_date_humaine_future_refusee(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "humains.jsonl"
            path.write_text(json.dumps({"schema": 2, "identite": "id", "date_validation": "2999-01-01"}) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "date humaine"):
                revue_v2.avis(path, {"id": {}}, {"id": {}})


if __name__ == "__main__":
    unittest.main()
