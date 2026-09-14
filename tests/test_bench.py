#!/usr/bin/env python3
"""test_bench.py — garde-fous du harnais agentique, entièrement hors réseau.

Trois familles, dans l'esprit du reste du dépôt :

1. **Le parseur ne ment pas sur ce qui s'est passé** — les fixtures de
   `fixtures/bench/` reproduisent le format relevé sur des runs réels de la
   CLI 2.1.133, y compris un flux tronqué et un échec d'authentification.
2. **Les verdicts se déclenchent** — chaque contrôle est éprouvé sur une trace
   qui le viole *et* sur une trace qui le respecte. Un vérificateur qui ne se
   déclenche jamais ne protège de rien (`test_affirmations.py`).
3. **Aucun secret ne fuit** — ni dans la ligne de commande, ni dans ce qui est
   envoyé au juge.

Un méta-test vérifie en outre que le corpus couvre les six outils du serveur
MCP, sur le patron de `test_live_probe.py`.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
RACINE = TESTS.parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(RACINE))

from bench import agents, cases, juge, verdicts  # noqa: E402
from bench.cadence import Cadence  # noqa: E402
from bench.flux import Appel, Trace, analyser, identifiants  # noqa: E402
from bench.journal import Journal, deja_faits  # noqa: E402
from bench.resume import agreger, comparer, rendre  # noqa: E402

FIXTURES = TESTS / "fixtures" / "bench"
CORPUS = TESTS / "bench-cases.csv"


def _trace_avec(appels: list[Appel], texte: str, **kwargs) -> Trace:
    return Trace(appels=appels, texte_final=texte, **kwargs)


def _appel(ordre, nom, arguments=None, resultat="", erreur=False) -> Appel:
    return Appel(
        ordre=ordre,
        nom_complet=f"mcp__droit-francais__{nom}",
        arguments=arguments or {},
        resultat_texte=resultat,
        is_error=erreur,
    )


class LectureDuFlux(unittest.TestCase):
    """Le parseur restitue ce que l'agent a fait, sans l'inventer."""

    def test_flux_nominal_relie_chaque_resultat_a_son_appel(self):
        trace = analyser((FIXTURES / "stream-C-nominal.jsonl").read_text(encoding="utf-8"))
        self.assertEqual(trace.noms_outils_appeles, ["search_articles", "get_article"])
        self.assertTrue(trace.mcp_connecte)
        self.assertEqual(trace.modele, "claude-sonnet-4-6")
        self.assertEqual(trace.num_turns, 3)
        self.assertEqual(trace.duration_ms, 18234)
        self.assertAlmostEqual(trace.total_cost_usd, 0.041)
        self.assertIn("LEGIARTI000029946370", trace.appels[0].identifiants_renvoyes)
        self.assertIn("LEGIARTI000029946370", trace.texte_final)

    def test_un_resultat_en_erreur_ne_prouve_aucune_provenance(self):
        trace = analyser((FIXTURES / "stream-C-erreur-outil.jsonl").read_text(encoding="utf-8"))
        self.assertTrue(trace.appels[0].is_error)
        self.assertEqual(trace.appels[0].identifiants_renvoyes, set())
        self.assertEqual(trace.identifiants_traces(), set())

    def test_bras_sans_outil_ne_produit_aucun_appel(self):
        trace = analyser((FIXTURES / "stream-A-sans-outil.jsonl").read_text(encoding="utf-8"))
        self.assertEqual(trace.appels, [])
        self.assertFalse(trace.mcp_connecte)
        self.assertEqual(trace.outils_disponibles, [])

    def test_flux_tronque_reste_analysable_et_compte_ses_pertes(self):
        trace = analyser((FIXTURES / "stream-tronque.jsonl").read_text(encoding="utf-8"))
        self.assertEqual(trace.lignes_illisibles, 1)
        self.assertEqual(len(trace.appels), 1)
        # Sans événement `result`, la réponse se lit sur le dernier bloc de texte.
        self.assertEqual(trace.texte_final, "Réponse partielle avant coupure.")

    def test_echec_authentification_est_visible_dans_la_trace(self):
        trace = analyser((FIXTURES / "stream-auth-echec.jsonl").read_text(encoding="utf-8"))
        self.assertTrue(trace.is_error)
        self.assertEqual(trace.api_error_status, 401)

    def test_identifiants_couvrent_les_formes_officielles(self):
        texte = (
            "LEGIARTI000029946370, JORFTEXT000000320196, CETATEXT000042687547, "
            "pourvoi 18-84.234, ECLI:FR:CCASS:2019:CR00123"
        )
        trouves = identifiants(texte)
        self.assertIn("LEGIARTI000029946370", trouves)
        self.assertIn("JORFTEXT000000320196", trouves)
        self.assertIn("CETATEXT000042687547", trouves)
        self.assertIn("18-84.234", trouves)


class VerdictProvenance(unittest.TestCase):
    """Le contrôle central : l'identifiant cité vient-il d'un outil ?"""

    IDENT = "LEGIARTI000029946370"

    def test_identifiant_recupere_puis_cite_passe(self):
        trace = _trace_avec(
            [_appel(0, "search_articles", resultat=f'{{"id":"{self.IDENT}"}}')],
            f"L'article L. 2212-2 CGCT ({self.IDENT}) dispose que...",
        )
        verdict, _ = verdicts.verdict_provenance(trace, "Que dit L. 2212-2 CGCT ?")
        self.assertEqual(verdict.statut, "PASS")

    def test_identifiant_cite_sans_appel_echoue(self):
        trace = _trace_avec([], f"L'article porte l'identifiant {self.IDENT}.")
        verdict, resultat = verdicts.verdict_provenance(trace, "Quel est l'identifiant ?")
        self.assertEqual(verdict.statut, "FAIL")
        self.assertIn(self.IDENT, resultat.identifiants_non_traces)

    def test_identifiant_fourni_dans_la_question_n_est_pas_une_invention(self):
        trace = _trace_avec([], f"L'article {self.IDENT} que vous citez concerne la police municipale.")
        verdict, _ = verdicts.verdict_provenance(trace, f"Que dit l'article {self.IDENT} ?")
        self.assertEqual(verdict.statut, "PASS")

    def test_identifiant_marque_non_verifie_est_tolere_et_compte(self):
        trace = _trace_avec([], f"{self.IDENT} — identifiant non vérifié, à confirmer sur Légifrance.")
        verdict, resultat = verdicts.verdict_provenance(trace, "Quel identifiant ?")
        self.assertEqual(verdict.statut, "PASS")
        self.assertIn(self.IDENT, resultat.identifiants_declares_non_verifies)
        self.assertEqual(resultat.identifiants_non_traces, set())

    def test_identifiant_issu_d_un_appel_en_erreur_ne_couvre_pas(self):
        trace = _trace_avec(
            [_appel(0, "get_article", resultat=f"erreur sur {self.IDENT}", erreur=True)],
            f"L'identifiant est {self.IDENT}.",
        )
        verdict, _ = verdicts.verdict_provenance(trace, "Quel identifiant ?")
        self.assertEqual(verdict.statut, "FAIL")

    def test_identifiant_seulement_present_dans_les_arguments_ne_couvre_pas(self):
        """Un identifiant inventé, soumis à un outil qui le rejette, ne se valide pas lui-même."""
        trace = _trace_avec(
            [_appel(0, "get_article", arguments={"id": self.IDENT}, resultat="aucun résultat")],
            f"L'identifiant est {self.IDENT}.",
        )
        verdict, _ = verdicts.verdict_provenance(trace, "Quel identifiant ?")
        self.assertEqual(verdict.statut, "FAIL")


class AutresVerdicts(unittest.TestCase):
    """Chaque contrôle est éprouvé dans les deux sens."""

    def test_groupe_disjonctif_satisfait_par_une_seule_option(self):
        trace = _trace_avec([_appel(0, "search")], "…")
        self.assertEqual(
            verdicts.verdict_outils_attendus(trace, "search_articles|search").statut, "PASS"
        )

    def test_groupe_conjonctif_non_satisfait_echoue(self):
        trace = _trace_avec([_appel(0, "search")], "…")
        verdict = verdicts.verdict_outils_attendus(trace, "search_articles|search;get_article")
        self.assertEqual(verdict.statut, "FAIL")
        self.assertIn("get_article", verdict.detail)

    def test_bras_sans_outil_avec_appel_est_un_echec(self):
        trace = _trace_avec([_appel(0, "search")], "…")
        verdict = verdicts.verdict_appels_interdits(trace, "", sans_outil=True)
        self.assertEqual(verdict.statut, "FAIL")

    def test_bras_sans_outil_sans_appel_passe(self):
        verdict = verdicts.verdict_appels_interdits(_trace_avec([], "…"), "", sans_outil=True)
        self.assertEqual(verdict.statut, "PASS")

    def test_appel_interdit_nomme_est_detecte(self):
        trace = Trace(appels=[Appel(0, "WebSearch", {})], texte_final="…")
        self.assertEqual(
            verdicts.verdict_appels_interdits(trace, "WebSearch;WebFetch", sans_outil=False).statut,
            "FAIL",
        )

    def test_plafond_depasse(self):
        trace = _trace_avec([_appel(i, "search") for i in range(5)], "…")
        self.assertEqual(verdicts.verdict_plafond(trace, 3).statut, "FAIL")
        self.assertEqual(verdicts.verdict_plafond(trace, 5).statut, "PASS")

    def test_date_attendue_sur_get_article_ou_search_articles(self):
        avec = _trace_avec([_appel(0, "search_articles", {"number": "62-2", "date": "2010-01-01"})], "…")
        sans = _trace_avec([_appel(0, "search_articles", {"number": "62-2"})], "…")
        self.assertEqual(verdicts.verdict_date(avec, "2010-01-01").statut, "PASS")
        self.assertEqual(verdicts.verdict_date(sans, "2010-01-01").statut, "FAIL")
        self.assertEqual(verdicts.verdict_date(sans, "").statut, "SANS_OBJET")

    def test_un_secret_present_dans_la_trace_est_signale(self):
        trace = _trace_avec([_appel(0, "search", resultat="jeton=SECRET-abcdef123456")], "…")
        self.assertEqual(verdicts.verdict_secrets(trace, ["SECRET-abcdef123456"]).statut, "FAIL")
        self.assertEqual(verdicts.verdict_secrets(trace, ["AUTRE-valeur-longue"]).statut, "PASS")

    def test_falsification_exige_une_recherche_distincte_apres_lecture(self):
        confirmation = _trace_avec(
            [
                _appel(0, "search_articles", {"number": "L2212-2"}, resultat="ok"),
                _appel(1, "get_article", {"id": "LEGIARTI000029946370"}, resultat="texte"),
            ],
            "…",
        )
        falsification = _trace_avec(
            [
                _appel(0, "search_articles", {"number": "L2212-2"}, resultat="ok"),
                _appel(1, "get_article", {"id": "LEGIARTI000029946370"}, resultat="texte"),
                _appel(2, "search_case_law", {"query": "police spéciale antennes relais"}, resultat="ok"),
            ],
            "…",
        )
        self.assertEqual(verdicts.verdict_falsification(confirmation).statut, "FAIL")
        self.assertEqual(verdicts.verdict_falsification(falsification).statut, "PASS")

    def test_evaluer_neutralise_les_attentes_d_outil_sur_un_bras_sans_outil(self):
        """Sinon un bras sans outil échouerait mécaniquement, sans rien mesurer."""
        resultat = verdicts.evaluer(
            _trace_avec([], "Je ne peux pas vérifier."),
            question="Quel identifiant ?",
            sans_outil=True,
            outils_attendus="search_articles;get_article",
            date_attendue="2010-01-01",
            plafond=6,
        )
        statuts = resultat.par_nom()
        self.assertEqual(statuts["outils_attendus"], "SANS_OBJET")
        self.assertEqual(statuts["date"], "SANS_OBJET")
        self.assertTrue(resultat.passe)


class DecouverteDesOutils(unittest.TestCase):
    """Les outils MCP sont différés derrière `ToolSearch` : conséquences."""

    def _outil(self, ordre, nom, resultat=""):
        return Appel(ordre=ordre, nom_complet=nom, arguments={}, resultat_texte=resultat)

    def test_la_decouverte_ne_compte_pas_dans_le_plafond(self):
        """Elle est imposée par la CLI, pas choisie par le modèle."""
        trace = _trace_avec(
            [self._outil(0, "ToolSearch"), _appel(1, "search_articles"), _appel(2, "get_article")],
            "…",
        )
        self.assertEqual(len(trace.appels), 3)
        self.assertEqual(len(trace.appels_sources), 2)
        self.assertEqual(verdicts.verdict_plafond(trace, 2).statut, "PASS")

    def test_une_decouverte_seule_ne_viole_pas_un_bras_sans_outil(self):
        trace = _trace_avec([self._outil(0, "ToolSearch")], "…")
        self.assertEqual(verdicts.verdict_appels_interdits(trace, "", sans_outil=True).statut, "PASS")

    def test_connecteur_juge_present_des_qu_un_outil_mcp_repond(self):
        trace = _trace_avec([_appel(0, "search_articles", resultat="ok")], "…")
        self.assertFalse(agents._connecteur_absent(trace))

    def test_connecteur_juge_absent_si_la_recherche_ne_le_trouve_pas(self):
        trace = _trace_avec([self._outil(0, "ToolSearch", resultat='{"results": []}')], "…")
        self.assertTrue(agents._connecteur_absent(trace))

    def test_connecteur_juge_present_si_la_recherche_le_mentionne(self):
        resultat = '[{"type":"tool_reference","tool_name":"mcp__droit-francais__search_articles"}]'
        trace = _trace_avec([self._outil(0, "ToolSearch", resultat=resultat)], "…")
        self.assertFalse(agents._connecteur_absent(trace))

    def test_un_modele_qui_ne_cherche_rien_n_est_pas_une_panne(self):
        """Ne pas chercher est un choix méthodologique : un échec, pas une panne."""
        self.assertFalse(agents._connecteur_absent(_trace_avec([], "Je m'abstiens.")))

    def test_init_sans_serveur_declare_ne_vaut_pas_panne(self):
        """`init.mcp_servers` est vide même quand le connecteur répond."""
        execution = agents.Execution(
            trace=_trace_avec([_appel(0, "search_articles", resultat="ok")], "Réponse.", mcp_connecte=False),
            flux_brut="",
            code_retour=0,
        )
        agents._classer(execution, "C")
        self.assertEqual(execution.statut, "ok")

    def test_identifiant_judilibre_est_reconnu(self):
        self.assertIn("5fca896542d4057b05893539", identifiants("décision 5fca896542d4057b05893539"))


class HallucinationReelle(unittest.TestCase):
    """Flux d'un run réel : le harnais attrape ce pour quoi il a été écrit.

    Bras C, connecteur joignable, `ToolSearch` offert à l'init et le préambule
    ordonnant de charger les outils. Le modèle n'a appelé aucun outil et a cité
    un identifiant en le présentant comme récupéré. Le cas est figé ici pour
    qu'une régression du détecteur se voie.
    """

    def setUp(self):
        chemin = FIXTURES / "stream-C-hallucination-reelle.jsonl"
        self.trace = analyser(chemin.read_text(encoding="utf-8"))

    def test_l_outil_de_decouverte_etait_bien_offert(self):
        """Sinon l'échec serait un défaut de montage, pas de méthode."""
        self.assertEqual(self.trace.outils_disponibles, ["ToolSearch"])

    def test_aucun_outil_n_a_ete_appele(self):
        self.assertEqual(self.trace.appels, [])

    def test_la_reponse_cite_un_identifiant(self):
        self.assertTrue(any(i.startswith("LEGIARTI") for i in identifiants(self.trace.texte_final)))

    def test_le_verdict_de_provenance_echoue(self):
        verdict, resultat = verdicts.verdict_provenance(
            self.trace, "[lookup] Que dit l'article L. 2212-2 du Code général des collectivités territoriales ?"
        )
        self.assertEqual(verdict.statut, "FAIL")
        self.assertTrue(resultat.identifiants_non_traces)

    def test_le_run_n_est_pas_classe_en_panne(self):
        """Le modèle n'a pas cherché : c'est un échec de méthode, pas une panne."""
        execution = agents.Execution(trace=self.trace, flux_brut="", code_retour=0)
        agents._classer(execution, "C")
        self.assertEqual(execution.statut, "ok")

    def test_la_fixture_ne_contient_aucun_jeton(self):
        brut = (FIXTURES / "stream-C-hallucination-reelle.jsonl").read_text(encoding="utf-8")
        for motif in ("sk-ant-", "Bearer ey", "AUTH0_CLIENT_SECRET="):
            with self.subTest(motif=motif):
                self.assertNotIn(motif, brut)


class LectureDuCorpus(unittest.TestCase):
    """Un corpus mal formé doit être refusé, pas interprété au mieux."""

    ENTETE = ",".join(cases.COLONNES)
    LIGNE = (
        "M01-a,1,Intitulé,Question ?,Comportement attendu,,,\"A,B,C\","
        "search_articles,,6,,,oui,non,,JB:2026-09-06"
    )

    def _corpus(self, contenu: str) -> Path:
        dossier = Path(tempfile.mkdtemp(prefix="bench-corpus-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(dossier, ignore_errors=True))
        chemin = dossier / "cas.csv"
        chemin.write_text(contenu, encoding="utf-8")
        return chemin

    def test_ligne_valide_est_lue(self):
        corpus = cases.charger(self._corpus(f"{self.ENTETE}\n{self.LIGNE}\n"))
        self.assertEqual(corpus[0].id, "M01-a")
        self.assertEqual(corpus[0].bras, ("A", "B", "C"))
        self.assertTrue(corpus[0].provenance_requise)
        self.assertTrue(corpus[0].valide)

    def test_champ_excedentaire_est_refuse(self):
        """Une virgule non échappée décalerait silencieusement les colonnes."""
        with self.assertRaises(cases.CorpusInvalide) as capture:
            cases.charger(self._corpus(f"{self.ENTETE}\n{self.LIGNE},surnumeraire\n"))
        self.assertIn("excédentaires", str(capture.exception))

    def test_identifiant_en_double_est_refuse(self):
        with self.assertRaises(cases.CorpusInvalide) as capture:
            cases.charger(self._corpus(f"{self.ENTETE}\n{self.LIGNE}\n{self.LIGNE}\n"))
        self.assertIn("double", str(capture.exception))

    def test_outil_inconnu_du_serveur_est_refuse(self):
        ligne = self.LIGNE.replace(",search_articles,", ",search_inexistant,")
        with self.assertRaises(cases.CorpusInvalide) as capture:
            cases.charger(
                self._corpus(f"{self.ENTETE}\n{ligne}\n"),
                outils_connus=frozenset({"search_articles", "get_article"}),
            )
        self.assertIn("search_inexistant", str(capture.exception))

    def test_date_non_iso_est_refusee(self):
        ligne = self.LIGNE.replace(",6,,,oui", ",6,01/01/2010,,oui")
        with self.assertRaises(cases.CorpusInvalide):
            cases.charger(self._corpus(f"{self.ENTETE}\n{ligne}\n"))

    def test_entete_non_conforme_est_refusee(self):
        with self.assertRaises(cases.CorpusInvalide) as capture:
            cases.charger(self._corpus("Id,Mode\nM01-a,1\n"))
        self.assertIn("en-tête", str(capture.exception))

    def test_les_brouillons_sont_ecartes_par_defaut(self):
        brouillon = self.LIGNE.replace("M01-a", "M01-b").replace(",JB:2026-09-06", ",")
        corpus = cases.charger(self._corpus(f"{self.ENTETE}\n{self.LIGNE}\n{brouillon}\n"))
        self.assertEqual(len(corpus), 2)
        self.assertEqual([c.id for c in cases.filtrer(corpus)], ["M01-a"])
        self.assertEqual(len(cases.filtrer(corpus, inclure_brouillons=True)), 2)


class LigneDeCommande(unittest.TestCase):
    """Ce qui isole les bras se lit dans la commande, et aucun secret n'y figure."""

    OPTIONS = agents.Options(modele="sonnet", executable="/faux/claude")

    def _commande(self, bras: str, config=None) -> list[str]:
        return agents.construire_commande(
            bras=bras, plafond=6, options=self.OPTIONS, chemin_config_mcp=config
        )

    def test_le_skill_passe_par_fichier_et_jamais_en_argument(self):
        """SKILL.md pèse ~47 ko : au-delà de la limite d'argv sous Windows."""
        commande = self._commande("B")
        self.assertIn("--system-prompt-file", commande)
        self.assertNotIn("--system-prompt", commande)
        self.assertTrue(any(a.endswith("SKILL.md") for a in commande))

    def test_bras_A_n_a_ni_skill_ni_mcp(self):
        commande = self._commande("A")
        self.assertFalse(any(a.endswith("SKILL.md") for a in commande))
        self.assertNotIn("--mcp-config", commande)

    def test_bras_sans_outil_desactive_les_outils_integres(self):
        for bras in ("A", "B"):
            with self.subTest(bras=bras):
                commande = self._commande(bras)
                self.assertIn("--tools", commande)
                self.assertEqual(commande[commande.index("--tools") + 1], "")
                self.assertNotIn("--mcp-config", commande)

    def test_le_bras_C_garde_l_outil_de_decouverte(self):
        """Les outils MCP sont différés : sans ToolSearch ils sont hors d'atteinte.

        Vérifié par run réel : `--tools ""` sur le bras C donne zéro appel, et
        le bras mesure alors un bras sans outils.
        """
        commande = self._commande("C", Path("/tmp/mcp.json"))
        self.assertEqual(commande[commande.index("--tools") + 1], "ToolSearch")

    def test_bras_C_restreint_les_outils_au_connecteur(self):
        commande = self._commande("C", Path("/tmp/mcp.json"))
        self.assertIn("--mcp-config", commande)
        self.assertIn("mcp__droit-francais__*", commande)
        self.assertIn("--disallowedTools", commande)
        self.assertIn("WebSearch", commande)

    def test_les_reglages_du_poste_sont_neutralises(self):
        """Sans cela, le skill installé chez l'utilisateur contaminerait le bras A."""
        commande = self._commande("A")
        self.assertIn("--setting-sources", commande)
        self.assertEqual(commande[commande.index("--setting-sources") + 1], "")

    def test_aucun_repli_de_modele(self):
        """Un basculement silencieux rendrait deux baselines incomparables."""
        self.assertNotIn("--fallback-model", self._commande("C", Path("/tmp/mcp.json")))

    def test_le_bras_C_exige_une_configuration_mcp(self):
        with self.assertRaises(ValueError):
            self._commande("C")

    def test_aucun_secret_dans_la_commande(self):
        with mock.patch.dict("os.environ", {"MCP_ACCESS_TOKEN": "jeton-tres-secret-123456"}):
            commande = self._commande("C", Path("/tmp/mcp.json"))
        self.assertFalse(any("jeton-tres-secret" in a for a in commande))

    def test_la_configuration_mcp_ne_porte_qu_un_marqueur(self):
        with mock.patch.dict("os.environ", {"MCP_ACCESS_TOKEN": "jeton-tres-secret-123456"}):
            rendu = json.dumps(agents.config_mcp(self.OPTIONS))
        self.assertIn("${MCP_ACCESS_TOKEN}", rendu)
        self.assertNotIn("jeton-tres-secret", rendu)

    def test_le_serveur_local_recoit_un_interpreteur_explicite(self):
        """Le `python` du PATH POSIX n'est pas celui que voit un processus Windows."""
        options = agents.Options(mcp_local=True, interpreteur_python="C:/py/python.exe")
        serveur = agents.config_mcp(options)["mcpServers"]["droit-francais"]
        self.assertEqual(serveur["command"], "C:/py/python.exe")
        self.assertEqual(serveur["type"], "stdio")


class Juge(unittest.TestCase):
    """Le juge voit la trace, et rien de ce qu'il ne doit pas voir."""

    def test_le_resume_de_trace_ne_recopie_pas_les_sources(self):
        trace = _trace_avec(
            [_appel(0, "get_article", {"id": "LEGIARTI000029946370"}, resultat="TEXTE INTEGRAL " * 50)],
            "…",
        )
        resume = juge.resumer_trace(trace)
        self.assertIn("get_article", resume)
        self.assertIn("LEGIARTI000029946370", resume)
        self.assertNotIn("TEXTE INTEGRAL", resume)

    def test_le_resume_signale_les_appels_en_erreur(self):
        trace = _trace_avec([_appel(0, "search", resultat="429", erreur=True)], "…")
        self.assertIn("erreur", juge.resumer_trace(trace))

    def test_aucun_secret_ne_part_vers_le_juge(self):
        secret = "jeton-tres-secret-123456"
        trace = _trace_avec([_appel(0, "search", {"query": "test"}, resultat=f"Bearer {secret}")], "Réponse.")
        with mock.patch.dict("os.environ", {"MCP_ACCESS_TOKEN": secret}):
            entree = juge.construire_entree(
                bras="C", comportement_attendu="…", trace=trace, reponse="Réponse."
            )
        self.assertNotIn(secret, entree)

    def test_le_bras_est_transmis_au_juge(self):
        entree = juge.construire_entree(
            bras="A", comportement_attendu="Abstention.", trace=Trace(), reponse="…"
        )
        self.assertIn("aucun skill, aucun outil", entree)

    def test_sortie_structuree_est_lue(self):
        sortie = json.dumps(
            {"structured_output": {"verdict": "PASS", "raison": "Source tracée.", "axe_defaillant": "aucun"}}
        )
        avis = juge.extraire_avis(sortie)
        self.assertTrue(avis.passe)
        self.assertEqual(avis.raison, "Source tracée.")

    def test_json_noye_dans_du_texte_est_recupere(self):
        avis = juge.extraire_avis('Voici mon verdict :\n{"verdict":"FAIL","raison":"Non sourcé.","axe_defaillant":"source"}\nFin.')
        self.assertFalse(avis.passe)
        self.assertEqual(avis.axe_defaillant, "source")

    def test_sortie_illisible_ne_passe_pas_par_defaut(self):
        """Un juge muet ne doit jamais valider un cas."""
        avis = juge.extraire_avis("le modèle n'a rien renvoyé d'exploitable")
        self.assertFalse(avis.passe)
        self.assertTrue(avis.erreur)

    def test_la_commande_du_juge_impose_le_schema_et_aucun_outil(self):
        commande = juge.construire_commande("opus", executable="/faux/claude")
        self.assertIn("--json-schema", commande)
        self.assertIn("--tools", commande)
        self.assertEqual(commande[commande.index("--tools") + 1], "")


class CadenceEtJournal(unittest.TestCase):
    """Quota et reprise, avec une horloge injectée : aucun temps réel consommé."""

    def test_la_cadence_attend_quand_le_seau_est_plein(self):
        temps = [0.0]
        attentes: list[float] = []

        def horloge():
            return temps[0]

        def attendre(delai):
            attentes.append(delai)
            temps[0] += delai

        cadence = Cadence(appels_par_minute=4, horloge=horloge, attente=attendre)
        cadence.reserver(3)
        self.assertEqual(attentes, [])
        cadence.reserver(3)  # 3 + 3 > 4 : doit attendre la sortie de fenêtre
        self.assertTrue(attentes)
        self.assertGreater(temps[0], 60.0)

    def test_la_correction_libere_la_reserve_non_consommee(self):
        temps = [0.0]
        cadence = Cadence(appels_par_minute=10, horloge=lambda: temps[0], attente=lambda d: None)
        cadence.reserver(8)
        self.assertEqual(cadence.consommes, 8)
        cadence.corriger(8, 2)
        self.assertEqual(cadence.consommes, 2)

    def test_la_reprise_saute_les_runs_acquis_mais_rejoue_les_pannes(self):
        dossier = Path(tempfile.mkdtemp(prefix="bench-journal-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(dossier, ignore_errors=True))
        chemin = dossier / "run.jsonl"
        journal = Journal(chemin)
        journal.ajouter({"agent": "claude", "modele": "s", "bras": "C", "id": "L-1", "repetition": 1, "statut": "ok"})
        journal.ajouter(
            {"agent": "claude", "modele": "s", "bras": "C", "id": "M01-a", "repetition": 1, "statut": "infra_error"}
        )
        acquis = deja_faits(chemin)
        self.assertIn(("claude", "s", "C", "L-1", 1), acquis)
        self.assertNotIn(("claude", "s", "C", "M01-a", 1), acquis)

    def test_une_ligne_tronquee_ne_perd_pas_le_reste_du_journal(self):
        dossier = Path(tempfile.mkdtemp(prefix="bench-journal-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(dossier, ignore_errors=True))
        chemin = dossier / "run.jsonl"
        chemin.write_text('{"id":"A","statut":"ok"}\n{"id":"B","statut"\n', encoding="utf-8")
        from bench.journal import lire

        self.assertEqual([l["id"] for l in lire(chemin)], ["A"])


class Resume(unittest.TestCase):
    """Les agrégats disent la vérité sur ce qui est mesuré et ce qui ne l'est pas."""

    def _runs(self, bras, mode, reussites, statut="ok"):
        return [
            {
                "bras": bras,
                "mode": mode,
                "pass": r,
                "statut": statut,
                "modele": "claude-sonnet-4-6",
                "skill_sha256": "abc123",
                "duration_ms": 1000,
                "total_cost_usd": 0.01,
                "verdicts": {"provenance": "PASS" if r else "FAIL"},
                "identifiants_non_traces": [] if r else ["LEGIARTI000029946370"],
            }
            for r in reussites
        ]

    def test_les_pannes_sont_exclues_des_taux(self):
        lignes = self._runs("C", "1", [True, True]) + self._runs("C", "1", [False], statut="infra_error")
        agregats = agreger(lignes)
        self.assertEqual(agregats["pannes"], 1)
        self.assertEqual(agregats["taux_bras_mode"]["C/1"], 1.0)

    def test_une_baisse_superieure_a_un_cas_equivalent_est_une_regression(self):
        avant = agreger(self._runs("C", "3", [True] * 9))
        apres = agreger(self._runs("C", "3", [True] * 7 + [False] * 2))
        deltas = comparer(apres, avant)
        self.assertEqual([d["etat"] for d in deltas], ["régression"])

    def test_une_variation_d_un_seul_run_reste_stable(self):
        avant = agreger(self._runs("C", "3", [True] * 9))
        apres = agreger(self._runs("C", "3", [True] * 8 + [False]))
        self.assertEqual(comparer(apres, avant)[0]["etat"], "stable")

    def test_l_abstention_correcte_n_est_mesuree_que_sans_outil(self):
        agregats = agreger(self._runs("A", "1", [True, False]) + self._runs("C", "1", [True]))
        self.assertIn("A", agregats["abstention_correcte"])
        self.assertNotIn("C", agregats["abstention_correcte"])

    def test_le_rendu_markdown_mentionne_l_empreinte_du_skill(self):
        rendu = rendre(agreger(self._runs("C", "1", [True])))
        self.assertIn("abc123", rendu)
        self.assertIn("Taux de réussite par bras", rendu)


class ChargementDesIdentifiants(unittest.TestCase):
    """Les `.env` alimentent le harnais sans jamais écraser l'environnement."""

    def test_une_variable_exportee_prime_sur_le_fichier(self):
        """En CI, les secrets viennent du coffre : le disque ne doit rien écraser."""
        sys.path.insert(0, str(RACINE / "skill" / "scripts"))
        from droit_francais.config import load_dotenv

        dossier = Path(tempfile.mkdtemp(prefix="bench-env-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(dossier, ignore_errors=True))
        (dossier / ".env").write_text("AUTH0_CLIENT_ID=valeur-du-fichier\n", encoding="utf-8")

        with mock.patch.dict("os.environ", {"AUTH0_CLIENT_ID": "valeur-exportee"}, clear=False):
            load_dotenv(script_dir=dossier)
            import os

            self.assertEqual(os.environ["AUTH0_CLIENT_ID"], "valeur-exportee")

    def test_le_modele_racine_declare_les_variables_du_bras_C(self):
        modele = (RACINE / ".env.example").read_text(encoding="utf-8")
        for nom in (
            "AUTH0_CLIENT_ID",
            "AUTH0_CLIENT_SECRET",
            "MCP_ACCESS_TOKEN",
            "CLAUDE_CODE_OAUTH_TOKEN",
        ):
            with self.subTest(variable=nom):
                self.assertIn(f"{nom}=", modele)

    def test_le_modele_racine_ne_porte_aucune_valeur(self):
        """Un modèle est une liste de noms ; une valeur qui s'y glisse fuit."""
        for ligne in (RACINE / ".env.example").read_text(encoding="utf-8").splitlines():
            ligne = ligne.strip()
            if ligne and not ligne.startswith("#") and "=" in ligne:
                with self.subTest(ligne=ligne):
                    self.assertEqual(ligne.partition("=")[2].strip(), "")

    def test_un_jeton_claude_range_dans_MCP_ACCESS_TOKEN_est_refuse(self):
        """Sinon il part vers le serveur MCP et revient en 401, sans explication."""
        from bench.jeton import JetonIndisponible, obtenir

        with mock.patch.dict("os.environ", {"MCP_ACCESS_TOKEN": "sk-ant-oat01-" + "x" * 90}):
            with self.assertRaises(JetonIndisponible) as capture:
                obtenir()
        message = str(capture.exception)
        self.assertIn("CLAUDE_CODE_OAUTH_TOKEN", message)
        self.assertNotIn("xxxx", message)  # la valeur ne doit pas figurer dans le message

    def test_un_jeton_mcp_legitime_est_accepte(self):
        from bench.jeton import obtenir

        with mock.patch.dict("os.environ", {"MCP_ACCESS_TOKEN": "eyJhbGciOiJSUzI1NiJ9.charge.signature"}):
            self.assertTrue(obtenir().valeur.startswith("eyJ"))

    def test_aucun_env_reel_n_est_suivi_par_git(self):
        """Le modèle est commité ; un `.env` renseigné ne doit jamais l'être.

        Le contrôle porte sur les noms que `.gitignore` vise — `.env` et
        `.env.*` — et non sur tout fichier dont le nom finit par « .env » :
        `tests/fixtures/sample.env` est une fixture publique, sans secret.
        """
        import subprocess

        suivis = subprocess.run(
            ["git", "ls-files"],
            cwd=RACINE,
            capture_output=True,
            encoding="utf-8",
            check=False,
        ).stdout.split()
        fautifs = [
            fichier
            for fichier in suivis
            if (base := fichier.rsplit("/", 1)[-1]) == ".env"
            or (base.startswith(".env.") and base != ".env.example")
        ]
        self.assertEqual(fautifs, [])


class CouvertureDuCorpus(unittest.TestCase):
    """Méta-tests sur le corpus livré, patron de `test_live_probe.py`."""

    def setUp(self):
        self.corpus = cases.charger(CORPUS)

    def test_le_corpus_du_depot_est_lisible(self):
        self.assertGreater(len(self.corpus), 0)

    def test_chaque_cas_cite_un_outil_connu_du_serveur(self):
        from mcp_server.catalog import EXPECTED_TOOLS

        for cas in self.corpus:
            for groupe in cas.outils_attendus.split(";"):
                for outil in groupe.split("|"):
                    if outil.strip():
                        with self.subTest(cas=cas.id, outil=outil):
                            self.assertIn(outil.strip(), EXPECTED_TOOLS)

    def test_tout_cas_datant_une_attente_porte_une_date_iso(self):
        for cas in self.corpus:
            if cas.date_attendue:
                with self.subTest(cas=cas.id):
                    self.assertRegex(cas.date_attendue, r"^\d{4}-\d{2}-\d{2}$")

    def test_les_documents_references_existent(self):
        racine = FIXTURES / "corpus"
        for cas in self.corpus:
            for document in cas.documents:
                with self.subTest(cas=cas.id, document=document):
                    self.assertTrue((racine / document).is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
