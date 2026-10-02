from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_support import digest, read, save
from host_device_pipeline import build_frame, encode_frame


class ProductionEvaluationTests(unittest.TestCase):
    def request(self):
        snapshot = read(ROOT / "experiments/fixtures/providers/codex-percent-window.json")
        wires = []
        for sequence, remaining in ((1, 80), (2, 60)):
            snapshot["windows"][0].update(percent_used=100-remaining, percent_remaining=remaining)
            wires.append(encode_frame(build_frame({"usage": [snapshot], "global_resets": []}, sequence, "2026-09-10T00:00:01Z")).decode("utf-8"))
        return {"reference_time": "2026-09-10T00:00:01Z", "monotonic_anchor": 10,
                "events": [{"seconds": 10, "wire": wires[0]}, {"seconds": 11, "wire": wires[1]}, {"seconds": 310}]}

    def test_constant_display_and_receive_age_only_implementations_fail(self):
        from production_evaluation import expected_trace, evaluate_trace
        expected = expected_trace(self.request())
        key = "openai/codex-cli/acct-demo-openai/five-hour"
        self.assertEqual(expected[0]["display_values"][key]["percent_remaining"], 80)
        self.assertEqual(expected[1]["display_values"][key]["percent_remaining"], 60)
        self.assertTrue(evaluate_trace(self.request(), {"views": expected})["conformance_pass"])
        expected[1]["display_values"] = expected[0]["display_values"]
        result = evaluate_trace(self.request(), {"views": expected})
        self.assertFalse(result["conformance_pass"])
        self.assertFalse(result["product_pass"])
        expected = expected_trace(self.request())
        self.assertTrue(expected[-1]["source_stale"])
        self.assertFalse(expected[-1]["receive_stale"])
        expected[-1]["source_stale"] = False
        self.assertFalse(evaluate_trace(self.request(), {"views": expected})["conformance_pass"])

    def test_actual_adapter_process_logs_failure_and_retains_source_provenance(self):
        from production_evaluation import run_adapter
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "product.py"
            source.write_text("import pathlib,sys\npathlib.Path(sys.argv[2]).write_text('{\"views\": []}')\nprint('test-only production seam')\n", encoding="utf-8")
            (root / "link.txt").write_text("test-only linkage", encoding="utf-8")
            save(root / "adapter.json", {"linkage_reviewed": True, "argv": [sys.executable, str(source), "{stimulus}", "{output}"],
                 "production_files": {"product.py": digest(source.read_bytes())}, "linkage_evidence": {"link.txt": digest((root / "link.txt").read_bytes())}})
            save(root / "request.json", self.request())
            report = run_adapter(root, root / "adapter.json", root / "request.json", root / "output")
            self.assertEqual(report["status"], "evaluated")
            self.assertFalse(report["conformance_pass"])
            self.assertIn("stdout.log", report["evidence"])

    def test_optical_requires_acceptance_correct_values_and_bound_media(self):
        from production_evaluation import join_optical
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "video.mp4").write_bytes(b"test-only media")
            (root / "alignment.txt").write_text("test-only clock alignment", encoding="utf-8")
            capture = {"status": "captured", "frames": [{"sequence": 1, "frame_sha256": "a"*64,
                       "accepted_at_seconds": 1, "write_at_seconds": 0.5}], "evidence": {}}
            wire = self.request()["events"][0]["wire"].encode("utf-8")
            (root / "sent-frames.jsonl").write_bytes(wire)
            capture["frames"][0]["frame_sha256"] = digest(wire)
            capture["evidence"]["sent-frames.jsonl"] = digest(wire)
            save(root / "capture.json", capture)
            observed = {"capture_sha256": digest((root / "capture.json").read_bytes()),
                        "clock_alignment": {"status": "verified", "evidence": {"path": "alignment.txt", "sha256": digest((root / "alignment.txt").read_bytes())}},
                        "observations": [{"sequence": 1, "frame_sha256": digest(wire), "seconds": 1.8,
                        "expected_values": {"openai/codex-cli/acct-demo-openai/five-hour": {"percent_remaining": 80}},
                        "observed_values": {"openai/codex-cli/acct-demo-openai/five-hour": {"percent_remaining": 80}},
                        "evidence": {"path": "video.mp4", "sha256": digest((root / "video.mp4").read_bytes())}}]}
            result = join_optical(root / "capture.json", observed)
            self.assertEqual(result["optical_status"], "pass")
            self.assertAlmostEqual(result["observations"][0]["accept_to_visible_seconds"], 0.8)
            self.assertFalse(result["product_pass"])
            key = "openai/codex-cli/acct-demo-openai/five-hour"
            observed["observations"][0]["observed_values"][key]["percent_remaining"] = 42
            self.assertEqual(join_optical(root / "capture.json", observed)["optical_status"], "fail")
            observed["observations"][0]["expected_values"][key]["percent_remaining"] = 42
            with self.assertRaisesRegex(ValueError, "expected.*stimulus"):
                join_optical(root / "capture.json", observed)
            capture["frames"][0]["accepted_at_seconds"] = None
            save(root / "capture.json", capture)
            observed["capture_sha256"] = digest((root / "capture.json").read_bytes())
            with self.assertRaisesRegex(ValueError, "accepted"):
                join_optical(root / "capture.json", observed)
