"""Operator review gates quality, while preserving the cost ledger."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_support import digest, read

spec = importlib.util.spec_from_file_location("policy_summary", ROOT / "scripts/summarize-benchmark.py")
summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary)


class PolicyReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "run-manifest.json"
        self.manifest = read(ROOT / "experiments/examples/run-manifest.example.json")
        self.manifest["operator"].update(phase="benchmark", policy_review_required=True)
        self.manifest["execution"]["worktree"] = str(self.root / "checkout")
        self.manifest["measurement"]["tokens"].update(input=50, output=25, total=75)
        for name, data in (("stdout.jsonl", b'{"no_denies":true}\n'), ("stderr.txt", b""),
                           ("prompt.txt", b"task"), ("profile.json", b'{"model":"test"}')):
            (self.root / name).write_bytes(data)
            self.manifest["operator"]["evidence"][name] = digest(data)
        self.manifest["execution"]["profile_sha256"] = digest(b'{"model":"test"}')
        self.manifest["agent"]["configuration_sha256"] = digest(b'{"model":"test"}')
        (self.root / "hardware-feature.json").write_text(json.dumps(read(ROOT / "experiments/examples/hardware-feature-result.example.json")), encoding="utf-8")
        (self.root / "operator-notes.txt").write_text("Reviewed full logs, task access and interventions.", encoding="utf-8")
        self.decision = {"status": "eligible", "reviewer": "operator@example", "reason": "Full transcript and access reviewed.",
                         "user_interventions": 0, "intervention_review": "No external implementation feedback or code edits.",
                         "evidence": [{"path": "operator-notes.txt", "sha256": digest((self.root / "operator-notes.txt").read_bytes())}]}
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.manifest), encoding="utf-8")

    def review(self):
        decision_path = self.root / "decision.json"
        decision_path.write_text(json.dumps(self.decision), encoding="utf-8")
        return subprocess.run([sys.executable, str(ROOT / "scripts/review-policy.py"), "--manifest", str(self.path),
                               "--decision", str(decision_path)], capture_output=True, text=True)

    def test_missing_review_excludes_quality_but_keeps_costs_and_reason(self):
        records, excluded = summary.collect_records([self.path])
        self.assertEqual(records, [])
        self.assertEqual(excluded.get("policy"), 1)
        attempts, _ = summary.collect_attempts([self.path])
        self.assertEqual(len(attempts), 1)
        self.assertEqual((attempts[0]["seconds"], attempts[0]["tokens"]), (600, 75))
        self.assertFalse(attempts[0]["policy_eligible"])
        self.assertIn("missing", summary.render_attempt_summary(attempts, {}).lower())

    def test_legacy_run_remains_eligible_without_review(self):
        del self.manifest["operator"]["policy_review_required"]
        self.save()
        self.assertEqual(len(summary.collect_records([self.path])[0]), 1)

    def test_operator_review_allows_quality_without_mutating_manifest(self):
        before = self.path.read_bytes()
        result = self.review()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(len(summary.collect_records([self.path])[0]), 1)
        self.assertNotEqual(self.review().returncode, 0, "review history must not be overwritten")

    def test_invalid_and_unverified_decisions_preserve_attempts(self):
        for status in ("invalid_for_comparison", "unverified"):
            with self.subTest(status=status):
                self.decision["status"] = status
                result = self.review()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(summary.collect_records([self.path])[1].get("policy"), 1)
                attempts, _ = summary.collect_attempts([self.path])
                self.assertEqual(attempts[0]["policy_status"], status)
                self.assertEqual(attempts[0]["tokens"], 75)
                (self.root / "policy-review.json").unlink()

    def test_tampering_with_bound_identity_logs_or_review_fails_closed(self):
        result = self.review()
        self.assertEqual(result.returncode, 0, result.stderr)
        original = copy.deepcopy(self.manifest)
        for group, field, value in (("execution", "profile_sha256", "a"*64),
                                     ("execution", "input_bundle_sha256", "b"*64),
                                     ("measurement", "user_interventions", 1)):
            self.manifest[group][field] = value
            self.save()
            self.assertEqual(summary.collect_records([self.path])[0], [], field)
            self.manifest = copy.deepcopy(original)
        self.save()
        for name in ("stdout.jsonl", "operator-notes.txt", "policy-review.json"):
            path = self.root / name
            before = path.read_bytes()
            path.write_bytes(before.replace(b"eligible", b"unverified") if name == "policy-review.json" else b"changed")
            self.assertEqual(summary.collect_records([self.path])[0], [], name)
            path.write_bytes(before)

    def test_review_rejects_unknown_interventions_and_candidate_owned_storage(self):
        self.manifest["measurement"]["user_interventions"] = None
        self.decision["user_interventions"] = None
        self.save()
        self.assertNotEqual(self.review().returncode, 0)
        self.manifest["measurement"]["user_interventions"] = 0
        self.decision["user_interventions"] = 0
        self.manifest["execution"]["worktree"] = str(self.root)
        self.save()
        self.assertNotEqual(self.review().returncode, 0)

    def test_operator_can_review_unknown_telemetry_without_changing_terminal_manifest(self):
        self.manifest["measurement"]["user_interventions"] = None
        self.save()
        before = self.path.read_bytes()
        result = self.review()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(len(summary.collect_records([self.path])[0]), 1)
        review = read(self.root / "policy-review.json")
        self.assertIsNone(review["binding"]["user_interventions"])
        self.assertEqual(review["decision"]["user_interventions"], 0)

    def test_operator_cannot_contradict_known_intervention_count(self):
        self.manifest["measurement"]["user_interventions"] = 1
        self.save()
        self.assertNotEqual(self.review().returncode, 0)
        self.assertFalse((self.root / "policy-review.json").exists())

    def test_reference_pass_does_not_bypass_missing_review_in_prefix(self):
        attempts = []
        for number in range(2):
            manifest = copy.deepcopy(self.manifest)
            manifest["operator"]["comparison"] = {"comparison_id": "series", "round": number, "reference_status": "pass", "reference_inputs_sha256": "a"*64}
            attempts.append({"manifest": manifest, "path": self.path, "seconds": 600, "tokens": 75})
        report = {"run_id": self.manifest["run_id"], "reference_inputs_sha256": "a"*64,
                  "items": {key: {"status": "pass", "evidence": self.decision["evidence"]} for key in ("RM1", "RM2", "RM3", "RM4", "RM5")}}
        report_path = self.root / "reference-review.json"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        attempts[1]["manifest"]["operator"]["evidence"]["reference-review.json"] = digest(report_path.read_bytes())
        # A legacy final round cannot retroactively authorize an unreviewed initial round.
        del attempts[1]["manifest"]["operator"]["policy_review_required"]
        series = summary.comparison_series(attempts)[0]
        self.assertIsNone(series["reference_round"])
        self.assertEqual(series["total_seconds"], 1200)


if __name__ == "__main__":
    unittest.main()
