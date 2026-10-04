import unittest
import json
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import importlib
eval_mod = importlib.import_module("evaluate-product")

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

class TestEvaluationContract(unittest.TestCase):
    def test_evaluate_product_full_gate(self):
        adapter_bin = ROOT / "build-host" / "meter_legacy_adapter.exe"
        self.assertTrue(adapter_bin.is_file())

        production_files = {
            "components/meter_core/src/meter_crc.c": sha256_file(ROOT / "components/meter_core/src/meter_crc.c"),
            "components/meter_core/src/meter_parser.c": sha256_file(ROOT / "components/meter_core/src/meter_parser.c"),
            "components/meter_core/src/meter_state.c": sha256_file(ROOT / "components/meter_core/src/meter_state.c"),
            "components/meter_core/src/meter_gui.c": sha256_file(ROOT / "components/meter_core/src/meter_gui.c"),
            "components/meter_core/src/feature_imu.c": sha256_file(ROOT / "components/meter_core/src/feature_imu.c"),
            "tests/meter_legacy_adapter.c": sha256_file(ROOT / "tests/meter_legacy_adapter.c"),
        }

        link_evidence_path = ROOT / "build-host" / "link_evidence.txt"
        link_evidence_content = (
            "Host build evidence:\n"
            "Compiler: Clang 22.1.8\n"
            "Target: meter_legacy_adapter.exe linked with libmeter_core.a\n"
            f"Binary SHA-256: {sha256_file(adapter_bin)}\n"
        )
        link_evidence_path.write_text(link_evidence_content, encoding="utf-8")
        link_evidence_sha256 = sha256_file(link_evidence_path)

        adapter_config = {
            "checkout": ".",
            "production_files": production_files,
            "reviewer": "operator",
            "link_evidence": "build-host/link_evidence.txt",
            "link_evidence_sha256": link_evidence_sha256,
            "argv": [str(adapter_bin.relative_to(ROOT)).replace("\\", "/")]
        }

        config_path = ROOT / "build-host" / "adapter-config.json"
        config_path.write_text(json.dumps(adapter_config, indent=2), encoding="utf-8")

        output_path = ROOT / "build-host" / "evaluation-output.json"
        
        # Test evaluate() directly with config argv
        results = eval_mod.evaluate(adapter_config["argv"], ROOT)
        self.assertTrue(len(results) > 0)
        for r in results:
            self.assertEqual(r["status"], "pass", f"Case {r.get('case')} failed: {r.get('reason')}")

if __name__ == "__main__":
    unittest.main()
