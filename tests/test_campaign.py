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
    def test_gold_brouillon_ne_permet_aucune_mesure(self):
        cases = campaign.corpus()
        self.assertEqual(len(cases), 36)
        self.assertFalse(any(campaign.gold_pret(c) for c in cases))

    def test_gel_refuse_fable_avant_tout_appel_modele(self):
        config = campaign.read_json(ROOT / "tests/campaign/config.example.json")
        config["familles"][0].update(modele_demande="claude-fable-5-1",
                                    executable="claude", raisonnement="high")
        with tempfile.TemporaryDirectory() as dossier:
            path = Path(dossier) / "config.json"
            campaign.write_json(path, config)
            with self.assertRaisesRegex(ValueError, "périmètre"), mock.patch.object(campaign, "version_cli") as version:
                campaign.figer(path, Path(dossier) / "gel.json")
            version.assert_not_called()

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

    def test_verrou_interdit_collecte_concurrente(self):
        with tempfile.TemporaryDirectory() as d:
            with campaign.verrou(Path(d)):
                with self.assertRaises(ValueError):
                    with campaign.verrou(Path(d)):
                        self.fail()

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
            reviews = Path(d) / "revues.jsonl"
            reviews.write_text("", encoding="utf-8")
            report = campaign.rapport([], reviews, state=Path(d))
            self.assertEqual(report["statut"], "revue_incomplete")
            self.assertEqual(report["exemples_readme"], [])
            self.assertTrue(all(m["utilite"] == "preuves_insuffisantes" for m in report["par_mode"]))

    def test_timeout_claude_conserve_la_reponse_partielle(self):
        import subprocess
        flux = json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "réponse inventée partielle"}]}})
        with mock.patch("bench.agents.subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 1, output=flux)):
            result = agents.ClaudeHeadless().executer(prompt="x", bras="A", plafond=0,
                options=agents.Options(executable="claude", garder_flux=True))
        self.assertEqual(result.statut, "infra_error")
        self.assertIn("partielle", result.trace.texte_final)
        self.assertIn("partielle", result.flux_brut)



if __name__ == "__main__":
    unittest.main()
