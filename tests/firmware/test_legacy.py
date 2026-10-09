"""Run the frozen section-5 matrix through the linked C legacy adapter."""
import runpy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
EVALUATOR = runpy.run_path(str(ROOT / "scripts/evaluate-product.py"))


class LegacySeamTests(unittest.TestCase):
    def test_all_frozen_cases(self):
        exe = ROOT / "tests/firmware/.build/cdm-host.exe"
        results = EVALUATOR["evaluate"]([str(exe)], ROOT)
        failures = [r for r in results if r["status"] != "pass"]
        self.assertEqual(len(results), 29)
        self.assertEqual(failures, [])
