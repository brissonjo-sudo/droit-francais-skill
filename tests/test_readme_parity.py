"""Vérifier surtout les dérives refusées, avec des README factices."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_readme_parity import NAVIGATION, check_pair, main

FR = NAVIGATION + '''
# Produit v0.9.0
## Installer
| Canal | État |
|---|---|
| Local | Candidat |
[Guide](docs/installation.md)
[Source](https://example.test/documentation)
```bash
# Installer
codex plugin add produit@catalogue  # exemple
```
'''
EN = FR.replace("Produit", "Product").replace("Installer", "Install").replace(
    "Canal", "Channel").replace("État", "Status").replace("Candidat", "Candidate").replace(
    "[Guide]", "[Guide in French]").replace("# exemple", "# example")


class ReadmeParityTests(unittest.TestCase):
    def test_traduction_prose_et_commentaires_autorisee(self):
        self.assertEqual([], check_pair(FR, EN))

    def test_chemins_langue_et_ancres_de_titre_traduites_autorises(self):
        self.assertEqual([], check_pair(FR + '[Suite](#installer)\n',
            EN.replace('docs/installation.md', 'docs/installation.en.md') + '[Next](#install)\n'))
        self.assertTrue(check_pair(FR + '[Suite](#installer)\n', EN + '[Next](#product-v090)\n'))

    def test_derives_refusees_sans_changer_les_comptages(self):
        for old, new, field in (("## Install", "### Install", "titres"),
                ("| Local | Candidate |", "| Local | Candidate | Extra |", "tableaux"),
                ("```bash", "```powershell", "blocs"),
                ("produit@catalogue", "autre@catalogue", "commandes"),
                ("docs/installation.md", "docs/autre.md", "liens"),
                ("https://example.test/documentation", "https://example.test/autre", "liens"),
                ("v0.9.0", "v0.8.0", "versions")):
            with self.subTest(field=field, old=old):
                self.assertTrue(any(field in p for p in check_pair(FR, EN.replace(old, new))))

    def test_tableau_bloc_ou_titre_retire_refuse(self):
        for cut in ("## Install\n", "| Local | Candidate |\n", "```bash\n# Install\ncodex plugin add produit@catalogue  # example\n```\n"):
            with self.subTest(cut=cut):
                self.assertTrue(check_pair(FR, EN.replace(cut, "")))

    def test_navigation_obligatoire_et_cibles_inchangees(self):
        self.assertTrue(check_pair(FR, EN.replace(NAVIGATION, "")))
        self.assertTrue(check_pair(FR, EN.replace("README.en.md", "README.english.md")))

    def test_titre_dans_bloc_non_compte_et_bloc_non_cloture_refuse(self):
        self.assertEqual([], check_pair(FR, EN.replace("# Install", "# English explanation")))
        self.assertTrue(check_pair(FR, EN.rsplit("```", 1)[0]))

    def test_readmes_reels(self):
        self.assertEqual(0, main())


if __name__ == "__main__":
    unittest.main()
