"""Non-régressions du gel, des quotas et de l'absence de faux verdicts."""
from __future__ import annotations
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
from bench import agents, campaign, native
from bench.flux import Appel, PREFIXE_MCP, Trace
from bench.preconditions import catalogue


class CampagneTests(unittest.TestCase):
    def test_catalogue_reel_gelable_avec_sdk_epingle(self):
        from mcp_server.catalog import EXPECTED_TOOLS
        tools = catalogue(ROOT, sys.executable)
        self.assertEqual({t["name"] for t in tools}, EXPECTED_TOOLS)
        self.assertTrue(all(isinstance(t["inputSchema"], dict) for t in tools))

    def test_gold_brouillon_ne_permet_aucune_mesure(self):
        cases = campaign.corpus()
        self.assertEqual(len(cases), 36)
        self.assertFalse(any(campaign.gold_pret(c) for c in cases))

    def test_nom_humain_seul_ne_valide_pas_le_gold(self):
        c = copy.deepcopy(campaign.corpus()[0])
        c["gold"]["valide_par"] = "relecteur"
        c["gold"]["statut"] = "valide"
        self.assertFalse(campaign.gold_pret(c))

    def test_identite_change_avec_candidat_et_phase(self):
        args = ["sha", "claude", "M01-a", "C", 1, "principale"]
        base = campaign.identite(*args)
        for i, changed in ((0, "sha2"), (1, "codex"), (3, "D"), (4, 2), (5, "pilote")):
            alt = args.copy()
            alt[i] = changed
            self.assertNotEqual(base, campaign.identite(*alt))

    def test_limite_journaliere_commune_et_reprise_lendemain(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for i in range(100):
                campaign.reserver_budget(root, str(i), jour="2026-10-10")
            with self.assertRaisesRegex(ValueError, "journalière"):
                campaign.reserver_budget(root, "codex", jour="2026-10-10")
            campaign.reserver_budget(root, "nouveau", jour="2026-10-11")
            self.assertEqual(len(campaign.lire_strict(root / "budget.jsonl")), 101)

    def test_journal_tronque_bloque_le_contournement_du_budget(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "budget.jsonl").write_text('{"jour":', encoding="utf-8")
            with self.assertRaises(ValueError):
                campaign.reserver_budget(root, "x")

    def test_verrou_interdit_collecte_concurrente(self):
        with tempfile.TemporaryDirectory() as d:
            with campaign.verrou(Path(d)):
                with self.assertRaises(ValueError):
                    with campaign.verrou(Path(d)):
                        self.fail()

    def test_un_changement_octet_arrete_le_gel(self):
        data = {"schema": 1, "fichiers": {"skill/SKILL.md": "old"}}
        data["series_sha256"] = campaign.digest(data)
        with mock.patch.object(campaign, "fichiers_figes", return_value={"skill/SKILL.md": "new"}):
            with self.assertRaisesRegex(ValueError, "modifié"):
                campaign.verifier_gel(data)

    def test_modele_inconnu_ou_alias_ne_qualifie_pas_preflight(self):
        f = {"nom": "codex", "modele_demande": "gpt-exact", "version_cli": "1"}
        row = {"modele_effectif": None, "version_cli": "1", "statut_technique": "ok",
               "controles_procedure": {"isolation_appels": True, "flux_lisible": True}, "appels": []}
        receipt = {"series_sha256": "sha", "famille": "codex", "revue_isolation_par": "humain",
                   "preuve_isolation": "preuve", "auth_abonnement_confirmee": True,
                   "autorise_collecte": True, "runs": [{**row, "bras": "A"}, {**row, "bras": "C"}]}
        self.assertFalse(campaign.preflight_pret(receipt, {"series_sha256": "sha"}, f))

    def test_reponse_correcte_sans_outil_reste_a_juger_sur_le_fond(self):
        tr = Trace(texte_final="LEGIARTI000006417749")
        proc = campaign.controles(tr, "A")
        self.assertEqual(proc["provenance"], "FAIL")
        f = {"nom": "codex", "modele_demande": "gpt", "version_cli": "1", "raisonnement": "low"}
        row = campaign.ligne_execution(agents.Execution(tr, "", 0), f=f, bras="A")
        self.assertIsNone(row["verdict_juridique"])
        self.assertNotIn("pass", row)

    def test_erreur_outil_et_reponse_sont_conservees_ensemble(self):
        tr = Trace(texte_final="Le texte inventé autorise tout.", appels=[Appel(0, PREFIXE_MCP + "get_article", {}, "quota", True)])
        execution = agents.Execution(tr, "", 1, statut="infra_error", motif_infra="quota")
        f = {"nom": "gemini", "modele_demande": "gemini", "version_cli": "1", "raisonnement": "defaut_cli"}
        row = campaign.ligne_execution(execution, f=f, bras="C")
        self.assertTrue(row["panne_et_reponse"])
        self.assertIn("inventé", row["reponse"])

    def test_resultat_claude_partiel_n_est_pas_un_succes_technique(self):
        tr = Trace(texte_final="Une réponse partielle")
        f = {"nom": "claude", "modele_demande": "exact", "version_cli": "1", "raisonnement": "low"}
        row = campaign.ligne_execution(agents.Execution(tr, '{"type":"assistant"}', 0), f=f, bras="A")
        self.assertEqual(row["statut_technique"], "infra_error")
        self.assertTrue(row["panne_et_reponse"])

    def test_un_outil_etranger_invalide_isolation(self):
        trace = Trace(appels=[Appel(0, "WebSearch", {})])
        self.assertFalse(campaign.controles(trace, "C")["isolation_appels"])

    def test_bras_D_ne_dit_pas_aucun_outil(self):
        prompt = native.instructions("D")
        self.assertIn("MCP", prompt)
        self.assertNotIn("aucun outil", prompt.lower())
        options = agents.Options(executable="claude")
        cmd = agents.construire_commande(bras="D", plafond=12, options=options, chemin_config_mcp=Path("mcp.json"))
        self.assertIn("ToolSearch", cmd)
        self.assertTrue(any("bras-D.md" in s for s in cmd))

    def test_environment_ne_route_pas_vers_api_payante(self):
        with mock.patch.dict("os.environ", {"OPENAI_API_KEY": "secret", "GEMINI_API_KEY": "secret",
                                          "CLAUDE_CODE_OAUTH_TOKEN": "oauth"}, clear=True):
            env = native.environnement_abonnement()
            self.assertNotIn("OPENAI_API_KEY", env)
            self.assertNotIn("GEMINI_API_KEY", env)
            self.assertEqual(env["CLAUDE_CODE_OAUTH_TOKEN"], "oauth")

    def test_secret_ne_persiste_pas_dans_resultat(self):
        with mock.patch.dict("os.environ", {"MCP_ACCESS_TOKEN": "secret-test-long"}, clear=True):
            data = campaign.nettoyer({"reponse": "secret-test-long"})
            self.assertNotIn("secret-test-long", json.dumps(data))

    def test_codex_commande_isolement_et_pas_de_fallback(self):
        cmd = native.commande_codex("codex", "gpt-exact", Path("system.md"), "C",
                                    agents.Options(mcp_local=True))
        self.assertIn("--ignore-user-config", cmd)
        self.assertIn("--ephemeral", cmd)
        self.assertIn("features.shell_tool=false", cmd)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", cmd)

    def test_codex_modele_absent_n_est_pas_reconstitue(self):
        # Fixture de contrat synthétique, pas une preuve d'exécution native.
        flux = '\n'.join(json.dumps(v) for v in [
            {"type": "thread.started", "thread_id": "x"},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "réponse"}},
            {"type": "turn.completed", "usage": {"input_tokens": 4}}])
        trace = native.analyser_natif(flux, "codex")
        self.assertEqual(trace.texte_final, "réponse")
        self.assertEqual(trace.modele, "")
        self.assertFalse(trace.is_error)

    def test_gemini_changement_modele_detecte_dans_stats(self):
        flux = '\n'.join(json.dumps(v) for v in [
            {"type": "init", "model": "gemini-demande"},
            {"type": "message", "role": "assistant", "content": "réponse"},
            {"type": "result", "status": "success", "stats": {"models": {"gemini-autre": {}}}}])
        self.assertEqual(native.analyser_natif(flux, "gemini").modele, "gemini-autre")

    def test_gemini_trace_mcp_normalisee_sans_accepter_serveur_etranger(self):
        flux = '\n'.join(json.dumps(v) for v in [
            {"type": "tool_use", "tool_id": "1", "tool_name": "mcp_droit-francais_get_article", "parameters": {"id": "x"}},
            {"type": "tool_result", "tool_id": "1", "status": "success", "output": "LEGIARTI000006417749"},
            {"type": "result", "status": "success", "stats": {}}])
        trace = native.analyser_natif(flux, "gemini")
        self.assertEqual(trace.appels[0].nom, "get_article")
        self.assertIn("LEGIARTI000006417749", trace.identifiants_traces())

    def test_flux_natif_tronque_est_infra_sans_perdre_texte(self):
        trace = native.analyser_natif('{"type":"message","role":"assistant","content":"partiel"}', "gemini")
        self.assertTrue(trace.is_error)
        self.assertEqual(trace.texte_final, "partiel")

    def test_rapport_vide_n_invente_ni_utilite_ni_exemple(self):
        with tempfile.TemporaryDirectory() as d:
            reviews = Path(d) / "revues.json"
            reviews.write_text("[]", encoding="utf-8")
            report = campaign.rapport([], reviews)
            self.assertEqual(report["statut"], "revue_incomplete")
            self.assertEqual(report["exemples_readme"], [])
            self.assertTrue(all(m["utilite"] == "preuves_insuffisantes" for m in report["par_mode"]))

    def test_paquet_aveugle_ne_contient_pas_le_bras_ni_la_famille(self):
        with tempfile.TemporaryDirectory() as d:
            output, target = Path(d) / "runs.jsonl", Path(d) / "paquet.json"
            row = {"identite": "abc", "id": "M01-a", "famille": "claude", "bras": "C",
                   "statut_technique": "ok", "reponse": "réponse"}
            output.write_text(json.dumps(row) + "\n", encoding="utf-8")
            campaign.paquet_revue([output], target)
            packet = campaign.read_json(target)[0]
            self.assertNotIn("famille", packet)
            self.assertNotIn("bras", packet)
            self.assertTrue(target.with_name("paquet-mapping-prive.json").exists())



    def test_timeout_claude_conserve_la_reponse_partielle(self):
        import subprocess
        flux = json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "réponse inventée partielle"}]}})
        with mock.patch("bench.agents.subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 1, output=flux)):
            result = agents.ClaudeHeadless().executer(prompt="x", bras="A", plafond=0,
                options=agents.Options(executable="claude", garder_flux=True))
        self.assertEqual(result.statut, "infra_error")
        self.assertIn("partielle", result.trace.texte_final)
        self.assertIn("partielle", result.flux_brut)

    def test_le_juge_ne_peut_pas_s_autodeclarer_humain(self):
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            item = {"token": "t", "question": "question", "gold": {}, "reponse": "texte"}
            packet = state / "paquet.json"
            campaign.write_json(packet, [item])
            campaign.write_json(state / "paquet-mapping-prive.json", [
                {"token": "t", "identite": "run", "famille": "claude", "series_sha256": "sha",
                 "paquet_sha256": campaign.digest(item)}])
            receipt = state / "sha/preflight-codex.json"
            campaign.write_json(receipt, {})
            target = state / "judge.jsonl"
            f = {"nom": "codex", "modele_demande": "gpt-exact", "executable": "codex",
                 "version_cli": "1", "raisonnement": "defaut_cli"}
            gel = {"series_sha256": "sha", "config": {"familles": [f]}}
            answer = {"axes": {a: "correct" for a in campaign.AXES},
                      "justification": "avis", "relecteur_humain": "fausse signature"}
            execution = agents.Execution(Trace(modele="gpt-exact", texte_final=json.dumps(answer)), "", 0)
            backend = mock.Mock()
            backend.executer.return_value = execution
            with (mock.patch.object(campaign, "verifier_gel"),
                  mock.patch.object(campaign, "gold_pret", return_value=True),
                  mock.patch.object(campaign, "version_cli", return_value="1"),
                  mock.patch.object(campaign, "preflight_pret", return_value=True),
                  mock.patch("bench.preconditions.abonnement", return_value=True),
                  mock.patch("bench.agents.backend", return_value=backend)):
                self.assertEqual(campaign.juger_paquet(gel, packet, "codex", target, state=state), 1)
            row = campaign.lire_strict(target)[0]
            self.assertEqual(row["relecteur_humain"], "")
            self.assertEqual(row["justification_humaine"], "")
            self.assertEqual(len(campaign.lire_strict(state / "budget.jsonl")), 1)
            prompt = backend.executer.call_args.kwargs["prompt"]
            self.assertNotIn("claude", prompt)
            self.assertNotIn('"bras"', prompt)

    def test_ablation_interdit_suppression_approximative_et_preserve_skill(self):
        from bench import ablation
        before = (ROOT / "skill/SKILL.md").read_bytes()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            recipe, report = root / "recette.json", root / "rapport.json"
            campaign.write_json(report, {"statut": "revue_complete_a_valider", "series_sha256": "sha"})
            campaign.write_json(recipe, [{"mode": 1, "valide_par": "humain", "raison": "ambigu",
                "regles_partagees": ["P1"], "passages_exacts": ["ABSENT_DU_SKILL"]}])
            with mock.patch.object(campaign, "verifier_gel"):
                with self.assertRaisesRegex(ValueError, "absent ou ambigu"):
                    ablation.preparer({"series_sha256": "sha"}, recipe, report, root / "experience")
            self.assertEqual((ROOT / "skill/SKILL.md").read_bytes(), before)

    def test_ablation_refuse_rapport_d_un_autre_candidat(self):
        from bench import ablation
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            campaign.write_json(root / "rapport.json", {"statut": "revue_complete_a_valider", "series_sha256": "autre"})
            with mock.patch.object(campaign, "verifier_gel"):
                with self.assertRaises(ValueError):
                    ablation.preparer({"series_sha256": "sha"}, root / "absent.json", root / "rapport.json", root / "experience")


if __name__ == "__main__":
    unittest.main()
