import json
from pathlib import Path
import sys
import tempfile
import unittest
import shutil
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import benchmark
from benchmark_support import ROOT, digest, read


class CandidateBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"
        self.root.mkdir()
        self.checkout = Path(self.temp.name) / "checkout"
        self.checkout.mkdir()
        self.policy_path = self.root / "experiments/config/agent-inputs.json"
        self.policy_path.parent.mkdir(parents=True)
        self.allowed = ["experiments/prompts/version-2-agent-task.md", "docs/PRODUCT_CONTRACT.md",
                        "docs/hardware/version-2-capabilities.md", "experiments/fixtures/input.json"]
        for name in self.allowed + ["docs/experiments/evidence/previous.md", "results/old.json",
                                    "README.md", "scripts/benchmark.py"]:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("baseline " + name, encoding="utf-8")
        self.write_policy()

    def write_policy(self, files=None):
        self.policy_path.write_text(json.dumps({"schema_version": 1,
            "required_markdown": self.allowed[:3], "files": files or self.allowed}), encoding="utf-8")

    def test_only_declared_inputs_are_copied_and_hashed(self):
        inventory = benchmark.materialize_candidate_inputs(self.root, self.checkout)
        self.assertEqual(set(inventory["files"]), set(self.allowed))
        self.assertEqual({p.relative_to(self.checkout).as_posix() for p in self.checkout.rglob("*")
                          if p.is_file()}, set(self.allowed))
        for name, sha in inventory["files"].items():
            self.assertEqual(sha, digest((self.checkout / name).read_bytes()))
        self.assertEqual(inventory["policy_sha256"], digest(self.policy_path.read_bytes()))

    def test_missing_required_input_fails_before_copy(self):
        (self.root / self.allowed[-1]).unlink()
        with self.assertRaisesRegex(ValueError, "missing"):
            benchmark.materialize_candidate_inputs(self.root, self.checkout)
        self.assertEqual(list(self.checkout.iterdir()), [])

    def test_unlisted_markdown_and_history_are_rejected(self):
        for extra in ["README.md", "docs/experiments/evidence/previous.md", "results/old.json",
                      "scripts/benchmark.py", "experiments/schema/runner-profile.schema.json",
                      "experiments/examples/run-manifest.example.json",
                      "../outside.txt", "/absolute.txt", "C:/outside.txt"]:
            with self.subTest(extra=extra):
                if extra.startswith("experiments/"):
                    path = self.root / extra
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text('{}')
                self.write_policy(self.allowed + [extra])
                with self.assertRaises(ValueError):
                    benchmark.materialize_candidate_inputs(self.root, self.checkout)
                self.assertEqual(list(self.checkout.iterdir()), [])

    def test_symlink_escape_is_rejected(self):
        path = self.root / self.allowed[-1]
        outside = Path(self.temp.name) / "outside.json"
        outside.write_text("private")
        path.unlink()
        try:
            path.symlink_to(outside)
        except OSError:
            self.skipTest("symlink creation unavailable")
        with self.assertRaises(ValueError):
            benchmark.materialize_candidate_inputs(self.root, self.checkout)

    def test_repository_policy_has_exactly_three_markdown_inputs(self):
        policy = read(ROOT / "experiments/config/agent-inputs.json")
        inventory = benchmark.candidate_input_inventory(ROOT)
        markdown = {name for name in inventory["files"] if name.endswith(".md")}
        self.assertEqual(markdown, set(policy["required_markdown"]))
        self.assertEqual(len(markdown), 3)
        self.assertNotIn("docs/experiments/comparison-operating-contract.md", inventory["files"])

    def test_support_tool_change_changes_frozen_bundle_hash(self):
        for name in ["experiments", "docs", "scripts"]:
            shutil.copytree(ROOT / name, self.root / name, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("evidence", "__pycache__"))
        profile = self.root / "experiments/config/runner-profile.example.json"
        before = benchmark.input_bundle_hashes(self.root, profile, "frozen", "a" * 40)
        tool = self.root / "scripts/host_device_pipeline.py"
        tool.write_bytes(tool.read_bytes() + b"\n# changed support input\n")
        after = benchmark.input_bundle_hashes(self.root, profile, "frozen", "a" * 40)
        self.assertNotEqual(before["input_bundle_sha256"], after["input_bundle_sha256"])
        self.assertEqual(before["fixture_sha256"], after["fixture_sha256"])

    def test_historical_snapshot_without_policy_keeps_original_hash_contract(self):
        for name in ["experiments", "docs", "scripts"]:
            shutil.copytree(ROOT / name, self.root / name, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("evidence", "__pycache__"))
        self.policy_path.unlink()
        profile = self.root / "experiments/config/runner-profile.example.json"
        before = benchmark.input_bundle_hashes(self.root, profile, "frozen", "a" * 40)
        tool = self.root / "scripts/host_device_pipeline.py"
        tool.write_bytes(tool.read_bytes() + b"\n# not part of historical bundle\n")
        after = benchmark.input_bundle_hashes(self.root, profile, "frozen", "a" * 40)
        self.assertEqual(before, after)

    def test_delivered_tools_work_without_operator_checkout(self):
        benchmark.materialize_candidate_inputs(ROOT, self.checkout)
        self.assertTrue((self.checkout / "experiments/config/host-toolchain.json").is_file())
        self.assertFalse((self.checkout / "experiments/schema/runner-profile.schema.json").exists())
        # Synthetic result examples reference maintainer evidence deliberately
        # excluded from candidates. Validate fixture data through the shipped API.
        code = ("import importlib.util; "
                "s=importlib.util.spec_from_file_location('validator','scripts/validate-end-to-end-result.py'); "
                "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
                "m.validate_fixture_matrix('experiments/fixtures/provider-fixture-matrix.json')")
        result = subprocess.run([sys.executable, "-c", code],
            cwd=self.checkout, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        result = subprocess.run([sys.executable, "scripts/run-host-device-pipeline.py", "--help"],
            cwd=self.checkout, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
