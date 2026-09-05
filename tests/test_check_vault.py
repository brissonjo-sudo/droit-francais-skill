#!/usr/bin/env python3
"""Le contrôleur de maillage doit échouer sur chaque défaut qu'il annonce.

Un vérificateur qui passe toujours ne vérifie rien. Chaque invariant est donc
éprouvé sur un vault de test qui le viole, et sur un vault qui le respecte.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

import check_vault  # noqa: E402

SECTION = check_vault.TITRE_SECTION
DECLARATION = check_vault.SECTION_DECLARATION


def note(*corps: str) -> str:
    return "\n".join(corps) + "\n"


def index(*, declare: str = "`mode 1`–`mode 14`", liens: str = "- [[alpha]]") -> str:
    return note(
        "# Index",
        "",
        DECLARATION,
        "",
        f"Les notions {declare} vivent dans les agrégats.",
        "",
        SECTION,
        "",
        liens,
    )


class MaillageVaultTests(unittest.TestCase):
    def _vault(self, fichiers: dict[str, str]) -> Path:
        dossier = Path(tempfile.mkdtemp())
        for nom, contenu in fichiers.items():
            (dossier / f"{nom}.md").write_text(contenu, encoding="utf-8")
        return dossier

    def _defauts(self, fichiers: dict[str, str]) -> list[str]:
        return check_vault.controler(self._vault(fichiers))

    def test_maillage_sain_ne_produit_aucun_defaut(self) -> None:
        defauts = self._defauts(
            {
                check_vault.INDEX: index(),
                "alpha": note("# Alpha", "", SECTION, "", "- [[index-recherche-juridique]]"),
            }
        )
        self.assertEqual([], defauts)

    def test_section_de_liens_absente_est_signalee(self) -> None:
        defauts = self._defauts(
            {
                check_vault.INDEX: index(),
                "alpha": note("# Alpha", "", "## Liens", "", "- [[index-recherche-juridique]]"),
            }
        )
        self.assertTrue(any("section" in d and "alpha" in d for d in defauts), defauts)

    def test_note_orpheline_est_signalee(self) -> None:
        defauts = self._defauts(
            {
                check_vault.INDEX: index(),
                "alpha": note("# Alpha", "", SECTION, "", "- [[index-recherche-juridique]]"),
                "orpheline": note(
                    "# Orpheline", "", SECTION, "", "- [[index-recherche-juridique]]"
                ),
            }
        )
        self.assertTrue(any("orpheline" in d and "entrant" in d for d in defauts), defauts)

    def test_cul_de_sac_est_signale(self) -> None:
        defauts = self._defauts(
            {
                check_vault.INDEX: index(liens="- [[alpha]]\n- [[impasse]]"),
                "alpha": note("# Alpha", "", SECTION, "", "- [[index-recherche-juridique]]"),
                "impasse": note("# Impasse", "", SECTION, "", "Aucun lien ici."),
            }
        )
        self.assertTrue(any("impasse" in d and "cul-de-sac" in d for d in defauts), defauts)

    def test_lien_non_resolu_non_declare_est_signale(self) -> None:
        defauts = self._defauts(
            {
                check_vault.INDEX: index(),
                "alpha": note(
                    "# Alpha",
                    "",
                    SECTION,
                    "",
                    "- [[index-recherche-juridique]]",
                    "- [[note-jamais-creee]]",
                ),
            }
        )
        self.assertTrue(any("note-jamais-creee" in d for d in defauts), defauts)

    def test_notion_declaree_dans_l_index_est_toleree(self) -> None:
        """« mode 1 »–« mode 14 » déclaré couvre « mode 10 » sans l'énumérer."""
        defauts = self._defauts(
            {
                check_vault.INDEX: index(),
                "alpha": note(
                    "# Alpha", "", SECTION, "", "- [[index-recherche-juridique]]", "- [[mode 10]]"
                ),
            }
        )
        self.assertEqual([], defauts)

    def test_notion_retiree_de_l_index_cesse_d_etre_toleree(self) -> None:
        """La tolérance vient de l'index : la retirer doit refaire échouer."""
        defauts = self._defauts(
            {
                check_vault.INDEX: index(declare="`P1`–`P7`"),
                "alpha": note(
                    "# Alpha", "", SECTION, "", "- [[index-recherche-juridique]]", "- [[mode 10]]"
                ),
            }
        )
        self.assertTrue(any("mode 10" in d for d in defauts), defauts)

    def test_wikilien_dans_du_code_n_est_pas_un_lien(self) -> None:
        """Obsidian n'interprète pas un wikilien en code : le compter comme
        lien sortant masquerait un cul-de-sac, et comme lien non résolu
        signalerait un nœud fantôme qui n'existe pas."""
        defauts = self._defauts(
            {
                check_vault.INDEX: index(liens="- [[alpha]]\n- [[impasse]]"),
                "alpha": note("# Alpha", "", SECTION, "", "- [[index-recherche-juridique]]"),
                "impasse": note(
                    "# Impasse", "", SECTION, "", "Écrire `[[cible-inexistante]]` en code."
                ),
            }
        )
        self.assertTrue(any("impasse" in d and "cul-de-sac" in d for d in defauts), defauts)
        self.assertFalse(any("cible-inexistante" in d for d in defauts), defauts)

    def test_alias_et_ancre_sont_reduits_au_nom_de_note(self) -> None:
        defauts = self._defauts(
            {
                check_vault.INDEX: index(liens="- [[alpha|voir Alpha]]"),
                "alpha": note(
                    "# Alpha", "", SECTION, "", "- [[index-recherche-juridique#Liens]]"
                ),
            }
        )
        self.assertEqual([], defauts)

    def test_auto_lien_ne_sauve_pas_une_orpheline(self) -> None:
        defauts = self._defauts(
            {
                check_vault.INDEX: index(),
                "alpha": note("# Alpha", "", SECTION, "", "- [[index-recherche-juridique]]"),
                "narcisse": note(
                    "# Narcisse",
                    "",
                    SECTION,
                    "",
                    "- [[narcisse]]",
                    "- [[index-recherche-juridique]]",
                ),
            }
        )
        self.assertTrue(any("narcisse" in d and "entrant" in d for d in defauts), defauts)

    def test_le_vault_reel_du_depot_tient(self) -> None:
        self.assertEqual([], check_vault.controler(ROOT / "vault"))


if __name__ == "__main__":
    unittest.main()
