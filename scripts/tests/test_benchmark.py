import copy
import importlib.util
import json
import sys
import tempfile
import shutil
import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from benchmark_support import ROOT, read, validate_operator, validate_pair, validate_schema, verify_evidence
from benchmark import capture, telemetry
import benchmark


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load("validator", "validate-experiment-result.py")
evaluation = load("evaluation", "evaluate-product.py")


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.m = read(ROOT / "experiments/examples/run-manifest.example.json")
        self.r = read(ROOT / "experiments/examples/hardware-feature-result.example.json")

    def test_examples(self):
        validator.validate_manifest(self.m)
        validator.validate_result(self.r, self.m)
        validate_pair(self.m, self.r)

    def test_old_id_rejected(self):
        self.m["run_id"] = "20260911T000000Z-example"
        with self.assertRaises(ValueError):
            validator.validate_manifest(self.m)

    def test_unknown_field_rejected(self):
        self.m["agent"]["invented"] = True
        with self.assertRaises(ValueError):
            validator.validate_manifest(self.m)

    def test_end_before_start(self):
        self.m["execution"]["ended_at"] = "2026-09-10T00:00:00Z"
        with self.assertRaises(ValueError):
            validate_operator(self.m)

    def test_bad_elapsed(self):
        self.m["measurement"]["wall_clock_seconds"] = 1
        with self.assertRaises(ValueError):
            validate_operator(self.m)

    def test_prepared_null_measurements(self):
        self.m["operator"].update(status="prepared", exit_code=None)
        self.m["execution"].update(started_at=None, ended_at=None)
        self.m["measurement"].update(wall_clock_seconds=None, tool_calls=None, failed_commands=None, user_interventions=None)
        validator.validate_manifest(self.m)

    def test_timeout_without_result(self):
        self.m["operator"].update(status="timeout", reason="limit", exit_code=1)
        validator.validate_manifest(self.m)

    def test_missing_failure_reason(self):
        self.m["operator"]["status"] = "timeout"
        with self.assertRaises(ValueError):
            validate_operator(self.m)

    def test_run_date_uses_kst(self):
        self.m["execution"].update(started_at="2026-09-10T15:00:00Z", ended_at="2026-09-10T15:10:00Z")
        validate_operator(self.m)
        self.m["execution"]["started_at"] = "2026-09-10T14:59:00Z"
        with self.assertRaises(ValueError):
            validate_operator(self.m)

    def test_pair_status_mismatch(self):
        self.m["outputs"]["build_status"] = "pass"
        with self.assertRaises(ValueError):
            validate_pair(self.m, self.r)

    def test_evidence_escape(self):
        self.m["operator"]["evidence"] = {"../secret": "0"*64}
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
            verify_evidence(self.m, folder)

    def test_strict_rfc3339(self):
        self.m["execution"]["started_at"] = "2026-09-11"
        with self.assertRaises(ValueError):
            validator.validate_manifest(self.m)


class RunnerTests(unittest.TestCase):
    def test_utf8_input_and_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            result = capture([sys.executable, "-c", "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read()); sys.exit(7)"],
                             path, "한글 입력".encode(), path, 5)
            self.assertEqual(result["code"], 7)
            self.assertEqual(result["status"], "environment_failed")
            self.assertEqual((path / "stdout.jsonl").read_bytes(), "한글 입력".encode())

    def test_timeout(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            result = capture([sys.executable, "-c", "import time; time.sleep(30)"], path, b"", path, 0.2)
            self.assertEqual(result["status"], "timeout")
            self.assertLess(result["elapsed"], 15)

    def test_missing_executable(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            result = capture([str(path / "not-installed.exe")], path, b"", path, 2)
            self.assertEqual(result["status"], "environment_failed")

    def test_tokens_do_not_double_count_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.jsonl"
            event = {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 20, "cached_input_tokens": 80}}
            path.write_text(json.dumps(event) + "\n", encoding="utf-8")
            tokens = telemetry(path, "codex")
            self.assertEqual(tokens["total"], 120)
            self.assertEqual(tokens["cached"], 80)
            self.assertIsNone(tokens["reasoning"])

    def test_missing_telemetry_is_null(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.jsonl"
            path.write_text("invalid event\n", encoding="utf-8")
            self.assertIsNone(telemetry(path, "gemini")["total"])


class EvaluatorTests(unittest.TestCase):
    def test_wrong_stale_is_detected(self):
        _, _, _, expected, body, mode = next(evaluation.cases())
        snapshot = dict(source="fixture", windows=body["windows"], observed_at=body["captured_at"], stale=False, error_code=None)
        with self.assertRaises(ValueError):
            evaluation.check([copy.deepcopy(snapshot) for _ in range(3)], expected, body, mode)

    def test_recovery_requires_error_and_preserved_values(self):
        body = read(ROOT / "experiments/fixtures/personal-usage.json")
        snapshot = dict(source="fixture", windows=body["windows"], observed_at=body["captured_at"], stale=False, error_code=None)
        values = [copy.deepcopy(snapshot) for _ in range(3)]
        values[1]["error_code"] = "dns"
        evaluation.check(values, [False]*3, body, "recovery")
        values[1]["windows"][0]["percent_used"] = 0
        with self.assertRaises(ValueError):
            evaluation.check(values, [False]*3, body, "recovery")


class IsolationTests(unittest.TestCase):
    def test_prepare_reserves_ids_and_excludes_parent_history(self):
        with tempfile.TemporaryDirectory(prefix="meter-test-") as folder:
            root = Path(folder)
            repo = root / "repo"
            repo.mkdir()
            shutil.copytree(ROOT / "experiments", repo / "experiments")
            subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@localhost", "commit", "-m", "baseline"], check=True, capture_output=True)
            profile = dict(provider="example", product="example-cli", interface="cli", agent_version="test",
                           model="example-model", model_slug="example-model", reasoning="fixed", branch_owner="example",
                           branch_product="example-cli", cohort="test", adapter="codex", argv=[sys.executable],
                           version_argv=[sys.executable, "--version"], sandbox_policy="test", approval_policy="test",
                           network_mode="offline-fixture", settings_inventory=dict(skills="none", mcp="none", memory="none",
                           user_instructions="none", cache="cold", routing="fixed"))
            profile_path = root / "profile.json"
            profile_path.write_text(json.dumps(profile), encoding="utf-8")
            args = SimpleNamespace(baseline="HEAD", profile=str(profile_path), root=str(root / "runs"),
                                   phase="pilot", seed=1, timeout=5, port=None)
            original_git = benchmark.git
            # git's default argument was bound at module import; explicitly redirect it.
            def test_git(*args, cwd=None):
                return original_git(*args, cwd=repo if cwd is None else cwd)
            with patch.object(benchmark, "ROOT", repo), patch.object(benchmark, "git", test_git):
                benchmark.prepare(args)
                benchmark.prepare(args)
            runs = sorted((root / "runs").iterdir())
            self.assertTrue(runs[0].name.endswith("r01"))
            self.assertTrue(runs[1].name.endswith("r02"))
            for run in runs:
                self.assertEqual(original_git("rev-list", "--count", "HEAD", cwd=run / "checkout"), "1")
                self.assertEqual(original_git("remote", cwd=run / "checkout"), "")
                self.assertFalse((run / "checkout/run-manifest.json").exists())
                self.assertNotIn(b"<run-id>", (run / "prompt.txt").read_bytes())
            for index, run in enumerate(runs):
                m = read(run / "run-manifest.json")
                m["execution"].update(started_at=benchmark.now(), ended_at=benchmark.now())
                m["measurement"]["wall_clock_seconds"] = 0
                m["operator"].update(status="aborted", reason="synthetic archive test")
                (run / "run-manifest.json").write_text(json.dumps(m), encoding="utf-8")
                (run / "checkout" / f"implementation-{index}.txt").write_text("synthetic", encoding="utf-8")
                benchmark.archive_run(SimpleNamespace(directory=str(run), archive=str(root / "archive.git")))
            branch = m["execution"]["branch"]
            files = original_git("ls-tree", "-r", "--name-only", branch, cwd=root / "archive.git")
            self.assertIn(f"results/{runs[0].name}/run-manifest.json", files)
            self.assertIn(f"results/{runs[1].name}/run-manifest.json", files)
            self.assertIn("implementation-1.txt", files)
            self.assertNotIn("implementation-0.txt", files)


if __name__ == "__main__":
    unittest.main()
