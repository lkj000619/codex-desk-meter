import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_support import digest, read, save
from benchmark import profile_digest


class ComparisonManagerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("comparison_manager"), "comparison manager is missing")
        self.manager = importlib.import_module("comparison_manager")
        self.temp = tempfile.TemporaryDirectory(prefix="meter-comparison-", dir="C:/Windows/Temp" if os.name == "nt" else None)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.first = self.root / "first"
        self.first.mkdir()
        checkout = self.first / "checkout"
        checkout.mkdir()
        (checkout / "product.txt").write_text("first implementation", encoding="utf-8")
        self.git("init", cwd=checkout)
        self.git("add", ".", cwd=checkout)
        self.git("-c", "user.name=Test", "-c", "user.email=test@localhost", "commit", "-m", "initial", cwd=checkout)
        manifest = read(ROOT / "experiments/examples/run-manifest.example.json")
        from datetime import datetime
        from benchmark_support import KST
        manifest["run_id"] = datetime.now(KST).strftime("%Y%m%d") + "-example-cli-example-model-r01"
        manifest["experiment_id"] = "version-2-end-to-end-v1"
        manifest["operator"].update(phase="benchmark", status="prepared", exit_code=None, reason=None,
                                    local_base_commit=self.git("rev-parse", "HEAD", cwd=checkout), evidence={})
        manifest["execution"].update(worktree=str(checkout), started_at=None, ended_at=None, timeout_seconds=7200)
        manifest["measurement"]["wall_clock_seconds"] = None
        manifest["outputs"].update(structured_result=f"results/{manifest['run_id']}/end-to-end-result.json",
                                   selection_document=f"docs/agent-runs/{manifest['run_id']}/hardware-feature-selection.md")
        save(self.first / "run-manifest.json", manifest)
        save(self.first / "profile.json", read(ROOT / "experiments/config/verified-profiles-candidate/codex-cli-sol-medium.candidate.json"))
        (self.first / "prompt.txt").write_text("initial prompt", encoding="utf-8")
        manifest["agent"]["configuration_sha256"] = digest((self.first / "profile.json").read_bytes())
        manifest["execution"]["profile_sha256"] = profile_digest(read(self.first / "profile.json"))
        manifest["operator"]["delivered_prompt_sha256"] = digest((self.first / "prompt.txt").read_bytes())
        save(self.first / "run-manifest.json", manifest)
        shutil.copytree(ROOT / "experiments/reference/codex-7923f96", self.root / "reference")
        self.reference = self.root / "reference/reference-inputs.json"
        self.ledger = self.root / "comparison.json"
        self.manager.init_comparison(self.ledger, self.first, self.reference)

    def git(self, *args, cwd):
        return subprocess.check_output(["git", *args], cwd=cwd, text=True, encoding="utf-8", stderr=subprocess.DEVNULL).strip()

    def terminal(self, directory, elapsed=600, status="timeout"):
        manifest = read(directory / "run-manifest.json")
        from datetime import datetime, timedelta, timezone
        start = datetime.strptime(manifest["run_id"][:8], "%Y%m%d").replace(tzinfo=timezone.utc)
        manifest["execution"].update(started_at=start.isoformat().replace("+00:00", "Z"),
                                    ended_at=(start + timedelta(seconds=elapsed)).isoformat().replace("+00:00", "Z"))
        manifest["measurement"]["wall_clock_seconds"] = elapsed
        manifest["operator"].update(status=status, exit_code=None if status == "timeout" else 0,
                                    reason="timeout" if status == "timeout" else None)
        save(directory / "run-manifest.json", manifest)
        self.manager.finish_run(directory)

    def review(self, directory, status="fail"):
        manifest = read(directory / "run-manifest.json")
        evidence = directory / "observation.txt"
        evidence.write_text("operator observation", encoding="utf-8")
        report = {"run_id": manifest["run_id"], "reference_inputs_sha256": read(self.ledger)["reference_inputs_sha256"],
                  "items": {key: {"status": status, "evidence": [{"path": "observation.txt", "sha256": digest(evidence.read_bytes())}]}
                            for key in ["RM1", "RM2", "RM3", "RM4", "RM5"]}}
        self.manager.review_run(directory, report)

    def feedback(self, directory):
        state = read(self.ledger)
        previous = state["runs"][-1]
        return {"previous_run_id": previous["run_id"], "previous_commit": previous["implementation_commit"],
                "target_ids": ["RM3"], "observed": "display absent", "expected": "visible fixture values",
                "evidence": [{"path": str(directory / "observation.txt"),
                              "sha256": digest((directory / "observation.txt").read_bytes())}]}

    def test_initial_limit_and_concurrent_execution_are_enforced(self):
        self.assertEqual(self.manager.start_run(self.first), 7200)
        with self.assertRaisesRegex(ValueError, "running|already"):
            self.manager.start_run(self.first)

    def test_reference_files_are_frozen_and_tampering_blocks_execution(self):
        state = read(self.ledger)
        frozen = Path(state["reference_inputs"]).parent / "expected-frames.jsonl"
        self.assertTrue(frozen.is_file())
        (self.reference.parent / "expected-frames.jsonl").write_bytes(b"original changed")
        frozen.write_bytes(b"frozen changed")
        with self.assertRaisesRegex(ValueError, "reference|hash"):
            self.manager.start_run(self.first)

    def test_initial_reference_cannot_disagree_with_prepared_baseline_reference(self):
        manifest = read(self.first / "run-manifest.json")
        manifest["operator"].pop("comparison")
        manifest["operator"]["evidence"]["reference/reference-inputs.json"] = "b"*64
        save(self.first / "run-manifest.json", manifest)
        with self.assertRaisesRegex(ValueError, "baseline reference"):
            self.manager.init_comparison(self.root / "different.json", self.first, self.reference)

    def test_followup_rejects_replaced_candidate_inventory(self):
        inventory = self.first / "candidate-inputs.json"
        save(inventory, {"files": {"product.txt": digest(b"first implementation")}})
        manifest = read(self.first / "run-manifest.json")
        manifest["operator"]["evidence"][inventory.name] = digest(inventory.read_bytes())
        save(self.first / "run-manifest.json", manifest)
        self.manager.start_run(self.first)
        self.terminal(self.first)
        self.review(self.first)
        save(inventory, {"files": {}})
        with self.assertRaisesRegex(ValueError, "hash|evidence"):
            self.manager.prepare_followup(self.ledger, self.root / "runs", self.feedback(self.first))

    def test_package_restores_reference_review_dependencies_and_frozen_stimulus(self):
        from evidence_package import create_package, restore_package
        self.manager.start_run(self.first)
        self.terminal(self.first)
        self.review(self.first)
        package = self.root / "package"
        created = create_package(self.first, package)
        self.assertIn("operator/observation.txt", read(package / "package-manifest.json")["files"])
        self.assertIn("operator/reference/expected-frames.jsonl", read(package / "package-manifest.json")["files"])
        (self.first / "checkout").rename(self.first / "unavailable")
        restore_package(package, self.root / "restored", created["package_manifest_sha256"])
        self.assertEqual((self.root / "restored/operator/observation.txt").read_text(), "operator observation")

    def test_terminal_cost_cannot_change_before_reference_review(self):
        self.manager.start_run(self.first)
        self.terminal(self.first)
        manifest = read(self.first / "run-manifest.json")
        manifest["measurement"]["tokens"]["input"] = 123
        save(self.first / "run-manifest.json", manifest)
        with self.assertRaisesRegex(ValueError, "terminal.*changed"):
            self.review(self.first)

    def test_timeout_cost_is_charged_and_followup_starts_from_frozen_source(self):
        self.manager.start_run(self.first)
        self.terminal(self.first)
        self.review(self.first)
        first_commit = read(self.ledger)["runs"][0]["implementation_commit"]
        followup = self.manager.prepare_followup(self.ledger, self.root / "runs", self.feedback(self.first))
        manifest = read(followup / "run-manifest.json")
        self.assertEqual(manifest["operator"]["comparison"]["starting_commit"], first_commit)
        self.assertEqual((Path(manifest["execution"]["worktree"]) / "product.txt").read_text(), "first implementation")
        self.assertIn("visible fixture values", (followup / "prompt.txt").read_text(encoding="utf-8"))
        self.manager.start_run(followup)
        self.terminal(followup, elapsed=7000)
        self.review(followup)
        third = self.manager.prepare_followup(self.ledger, self.root / "runs", self.feedback(followup))
        self.assertEqual(self.manager.start_run(third), 200)
        self.terminal(third, elapsed=200)
        self.review(third)
        with self.assertRaisesRegex(ValueError, "budget"):
            self.manager.prepare_followup(self.ledger, self.root / "runs", self.feedback(third))

    def test_fourth_remediation_and_reached_reference_stop_the_series(self):
        directory = self.first
        for number in range(4):
            self.manager.start_run(directory)
            self.terminal(directory, elapsed=10)
            self.review(directory)
            if number < 3:
                directory = self.manager.prepare_followup(self.ledger, self.root / "runs", self.feedback(directory))
        with self.assertRaisesRegex(ValueError, "round"):
            self.manager.prepare_followup(self.ledger, self.root / "runs", self.feedback(directory))

    def test_reference_pass_requires_hashed_evidence_and_blocks_next_round(self):
        self.manager.start_run(self.first)
        self.terminal(self.first, status="completed")
        self.review(self.first, status="pass")
        self.assertEqual(read(self.ledger)["state"], "reached")
        with self.assertRaisesRegex(ValueError, "reached"):
            self.manager.prepare_followup(self.ledger, self.root / "runs", self.feedback(self.first))

    def test_missing_review_or_modified_profile_cannot_start_followup(self):
        self.manager.start_run(self.first)
        self.terminal(self.first)
        with self.assertRaisesRegex(ValueError, "review"):
            self.manager.prepare_followup(self.ledger, self.root / "runs", {})
        self.review(self.first)
        followup = self.manager.prepare_followup(self.ledger, self.root / "runs", self.feedback(self.first))
        profile = read(followup / "profile.json")
        profile["model"] = "different-model"
        save(followup / "profile.json", profile)
        with self.assertRaisesRegex(ValueError, "profile"):
            self.manager.start_run(followup)

    def test_runner_uses_infrastructure_receipt_and_records_the_actual_execution(self):
        import benchmark
        from types import SimpleNamespace
        profile = read(self.first / "profile.json")
        profile.update(argv=[sys.executable, "-c", "print('offline dummy process')"],
                       version_argv=[sys.executable, "--version"],
                       agent_version=subprocess.check_output([sys.executable, "--version"], text=True).strip())
        save(self.first / "profile.json", profile)
        manifest = read(self.first / "run-manifest.json")
        manifest["agent"]["configuration_sha256"] = digest((self.first / "profile.json").read_bytes())
        manifest["execution"]["profile_sha256"] = profile_digest(profile)
        manifest["execution"]["timeout_seconds"] = 99999
        save(self.first / "run-manifest.json", manifest)
        state = read(self.ledger)
        state["profile_sha256"] = profile_digest(profile)
        save(self.ledger, state)
        (self.root / "capability.txt").write_text("synthetic test-only capability evidence", encoding="utf-8")
        receipt = {"access_policy": "prompt-and-log", "base_commit": manifest["execution"]["base_commit"],
                   "profile_sha256": manifest["execution"]["profile_sha256"], "infrastructure_ready": True,
                   "comparison_id": state["comparison_id"], "input_bundle_sha256": state["input_bundle_sha256"],
                   "reference_inputs_sha256": state["reference_inputs_sha256"], "pilot_pass": False,
                   "checks": dict.fromkeys(["idf_build", "compiler", "ninja", "git", "temp_write",
                                            "network_policy", "settings_inventory", "prompt_scope", "activity_logging"], "pass"),
                   "evidence": {"capability.txt": digest((self.root / "capability.txt").read_bytes())},
                   "capabilities": {key: {"status": "pass", "evidence": "capability.txt"} for key in
                                    ["read", "write", "list", "host_build", "host_test", "idf_build", "vendor_reference", "telemetry", "settings"]}}
        receipt["checks"]["read_isolation"] = "not_enforced"
        save(self.root / "receipt.json", receipt)
        self.assertEqual(benchmark.execute(SimpleNamespace(directory=str(self.first), receipt=str(self.root / "receipt.json"))), 0)
        state = read(self.ledger)
        self.assertEqual(state["runs"][0]["status"], "completed")
        self.assertGreater(state["runs"][0]["elapsed_seconds"], 0)
        self.assertEqual(read(self.first / "run-manifest.json")["execution"]["timeout_seconds"], 7200)
        self.assertIn("execution-preflight.json", read(self.first / "run-manifest.json")["operator"]["evidence"])
        self.assertIn("preflight-evidence/capability.txt", read(self.first / "run-manifest.json")["operator"]["evidence"])
