import unittest
import json
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import importlib
eval_mod = importlib.import_module("evaluate-product")
cases = eval_mod.cases
check = eval_mod.check

class TestLegacyAdapter(unittest.TestCase):
    def test_all_evaluation_cases(self):
        adapter_bin = ROOT / "build-host" / "meter_legacy_adapter.exe"
        self.assertTrue(adapter_bin.is_file(), f"Adapter binary {adapter_bin} not found")

        for name, source, events, stale, body, mode in cases():
            with self.subTest(case=name):
                p = subprocess.run(
                    [str(adapter_bin)],
                    cwd=str(ROOT),
                    input=json.dumps(dict(source=source, events=events)),
                    encoding="utf-8",
                    capture_output=True,
                    timeout=30,
                    check=True,
                )
                outputs = json.loads(p.stdout)
                try:
                    check(outputs, stale, body, mode)
                except ValueError as exc:
                    self.fail(f"Case {name} failed: {exc}\nStdout: {p.stdout}\nStderr: {p.stderr}")

if __name__ == "__main__":
    unittest.main()
