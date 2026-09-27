import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import benchmark
from benchmark_support import ROOT, read, verify_evidence


class AgentInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        self.checkout = self.run / "checkout"
        self.checkout.mkdir()
        self.manifest = read(ROOT / "experiments/examples/run-manifest.example.json")
        self.manifest["execution"]["worktree"] = str(self.checkout)
        self.manifest["operator"]["evidence"] = {}
        self.manifest["experiment_id"] = "version-2-end-to-end-v1"
        self.manifest["outputs"]["evaluation_manifest"] = "results/test/e2e-evaluation-manifest.json"
        evaluation = {"schema_version": 1, "manifest_id": self.manifest["run_id"],
                      "run_id": self.manifest["run_id"], "result_reference": self.manifest["run_id"],
                      "baseline_id": self.manifest["baseline_id"],
                      "baseline_ref": self.manifest["baseline_ref"],
                      "experiment_id": self.manifest["experiment_id"],
                      "execution": {"base_commit": self.manifest["execution"]["base_commit"]}}
        benchmark.save(self.run / "e2e-evaluation-manifest.json", evaluation)

    def test_identity_is_available_inside_checkout_without_measurements(self):
        benchmark.prepare_agent_inputs(self.run, self.manifest)
        context = read(self.checkout / ".benchmark-inputs/run-context.json")
        self.assertEqual(context["baseline"]["commit"], self.manifest["execution"]["base_commit"])
        self.assertEqual(context["run_id"], self.manifest["run_id"])
        self.assertNotIn("measurement", context)
        self.assertNotIn("operator", context)
        self.assertNotIn("worktree", context)
        benchmark.verify_agent_inputs(self.run, self.manifest)
        verify_evidence(self.manifest, self.run)

    def test_agent_edit_of_context_is_rejected(self):
        benchmark.prepare_agent_inputs(self.run, self.manifest)
        (self.checkout / ".benchmark-inputs/run-context.json").write_text('{}')
        with self.assertRaisesRegex(ValueError, "immutable agent input"):
            benchmark.verify_agent_inputs(self.run, self.manifest)

    def test_agent_edit_of_evaluation_identity_is_rejected(self):
        benchmark.prepare_agent_inputs(self.run, self.manifest)
        (self.checkout / ".benchmark-inputs/e2e-evaluation-manifest.json").write_text('{}')
        with self.assertRaisesRegex(ValueError, "immutable agent input"):
            benchmark.verify_agent_inputs(self.run, self.manifest)

    def test_external_context_tamper_is_rejected_by_hash(self):
        benchmark.prepare_agent_inputs(self.run, self.manifest)
        (self.run / "agent-context.json").write_text('{}')
        with self.assertRaisesRegex(ValueError, "evidence hash mismatch"):
            benchmark.verify_agent_inputs(self.run, self.manifest)
