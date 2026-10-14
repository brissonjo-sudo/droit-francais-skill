"""Les artefacts privés ne masquent jamais une cible publique cassée."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_links


class MarkdownLinksTests(unittest.TestCase):
    def test_clone_sous_parent_runs_garde_tous_les_documents_publics(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "runs" / "clone"
            (root / "docs" / "runs").mkdir(parents=True)
            (root / "tests" / "bench" / "runs").mkdir(parents=True)
            public = root / "docs" / "runs" / "guide.md"
            public.write_text("[Absent](absent.md)\n", encoding="utf-8")
            private = root / "tests" / "bench" / "runs" / "draft.md"
            private.write_text("[Privé](absent.md)\n", encoding="utf-8")
            readme = root / "README.md"
            readme.write_text("[Guide](docs/runs/guide.md)\n", encoding="utf-8")
            with mock.patch.object(check_links, "ROOT", root):
                self.assertCountEqual([readme, public], check_links.iter_markdown())
                self.assertEqual([], check_links.check_file(readme))
                self.assertEqual(1, len(check_links.check_file(public)))
                self.assertEqual(1, check_links.main())
                public.write_text("Guide public.\n", encoding="utf-8")
                self.assertEqual(0, check_links.main())


if __name__ == "__main__":
    unittest.main()
