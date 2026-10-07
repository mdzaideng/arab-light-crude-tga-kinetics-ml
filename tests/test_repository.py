from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryIntegrityTests(unittest.TestCase):
    def test_required_files_exist(self):
        required = [
            "README.md",
            "LICENSE",
            "CITATION.cff",
            "requirements.txt",
            "run_all.py",
            "render_publication_figures.py",
            "src/kinetics/run_all_latest.py",
            "src/ml/run_ml_analysis.py",
            "results/kinetics/Arab_Light_Kinetics_Consolidated_Results.xlsx",
            "results/ml/Arab_Light_TGA_ML_REVISED_Results_FINAL_WITH_FIGURES.xlsx",
        ]
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_prohibited_files_are_absent(self):
        names = {path.name for path in ROOT.rglob("*") if path.is_file()}
        prohibited = {
            "Arab_Light_TGA_Canonical_Data.xlsx",
            "Arab_Light_Kinetics_Source_FWO_KAS_Starink.xlsx",
            "arab_light_TGA_cleaned_ML_ready_v2.xlsx",
        }
        self.assertFalse(names & prohibited)
        self.assertFalse(list(ROOT.rglob("*.docx")))
        self.assertFalse(list(ROOT.rglob(".ipynb_checkpoints")))
        # NOTE: this test itself is a .py file, so *running* it under
        # unittest/pytest recompiles this module to bytecode, which can
        # create tests/__pycache__ as a side effect of the very act of
        # checking. That transient artifact is gitignored and never part of
        # a release archive, so it is not a real prohibition violation and
        # is excluded here. Everywhere else in the tree, a __pycache__ can
        # only exist because something was actually executed and its
        # bytecode was left behind before packaging -- which IS a real
        # release hygiene bug (see RELEASE_CHECKLIST.md: clear caches
        # before zipping) -- so those are still caught.
        generated_caches = [
            path for path in ROOT.rglob("__pycache__")
            if path.parts[-2:] != ("tests", "__pycache__")
        ]
        self.assertFalse(generated_caches, f"Cache directories found: {generated_caches}")

    def test_python_sources_compile(self):
        for path in ROOT.rglob("*.py"):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_json_and_notebook_files_parse(self):
        for path in list(ROOT.rglob("*.json")) + list(ROOT.rglob("*.ipynb")):
            json.loads(path.read_text(encoding="utf-8"))

    def test_csv_files_have_headers(self):
        for path in ROOT.rglob("*.csv"):
            with path.open(newline="", encoding="utf-8-sig") as stream:
                rows = csv.reader(stream)
                header = next(rows, None)
            self.assertTrue(header, str(path))

    def test_publication_pngs_are_valid(self):
        main = sorted((ROOT / "figures" / "main").glob("Figure*.png"))
        supplementary = sorted((ROOT / "figures" / "supplementary").glob("FigureS*.png"))
        self.assertEqual(len(main), 9)
        self.assertEqual(len(supplementary), 8)
        for path in main + supplementary:
            self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n", str(path))

    def test_publication_figures_rendered_in_times_new_roman(self):
        # Written by render_publication_figures.py; fails for preview renders made with a fallback font.
        log = json.loads((ROOT / "figures" / "RENDER_LOG.json").read_text(encoding="utf-8"))
        self.assertEqual(log["font_family"], "Times New Roman", f"figures rendered with {log['font_family']}")
        self.assertFalse(log["fallback_allowed"])
        self.assertEqual(len(log["figures"]), 21)

    def test_active_python_has_no_colab_or_windows_paths(self):
        forbidden = ["/content/drive", "C:\\\\Users\\\\"]
        for path in (ROOT / "src").rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for marker in forbidden:
                self.assertNotIn(marker, text, str(path))


if __name__ == "__main__":
    unittest.main()
