import copy
import contextlib
import io
import importlib.util
import json
import os
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


def ascii_temp_dir():
    """Use an ASCII-only test root so production path policy is exercised honestly."""

    if os.name == "nt":
        candidate = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "Temp"
    else:
        candidate = Path("/tmp")
    if not candidate.is_dir() or not str(candidate).isascii():
        raise RuntimeError(f"ASCII test temp directory is unavailable: {candidate}")
    return candidate


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
    def test_opencode_provider_total_and_reasoning_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "stdout.jsonl"
            event = {"type": "step_finish", "part": {"tokens": {
                "total": 2065, "input": 2005, "output": 15,
                "reasoning": 45, "cache": {"read": 0, "write": 0}}}}
            path.write_text(json.dumps(event) + "\n" + json.dumps(event), encoding="utf-8")
            measured = telemetry(path, "opencode")
            self.assertEqual(measured["provider_total"], 4130)
            self.assertEqual(measured["total"], 4040)
            self.assertEqual(measured["input"], 4010)
            self.assertEqual(measured["reasoning"], 90)
            self.assertEqual(measured["cached"], 0)

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
            self.assertIsNone(tokens["provider_total"])
            self.assertIsNone(tokens["reasoning"])

    def test_missing_telemetry_is_null(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.jsonl"
            path.write_text("invalid event\n", encoding="utf-8")
            self.assertIsNone(telemetry(path, "gemini")["total"])

    def test_antigravity_mock_stream_preserves_one_shot_prompt_and_unknown_metrics(self):
        prompt = "AGY one-shot 한글 prompt".encode("utf-8")
        mock = (
            "import hashlib,json,sys; "
            "body=sys.stdin.buffer.read(); "
            "print(json.dumps({'type':'mock.completed','input_bytes':len(body),"
            "'prompt_sha256':hashlib.sha256(body).hexdigest()}))"
        )
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            result = capture([sys.executable, "-c", mock], path, prompt, path, 5)
            self.assertEqual(result["status"], "completed")
            events = (path / "stdout.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(events), 1)
            event = json.loads(events[0])
            self.assertEqual(event["input_bytes"], len(prompt))
            self.assertEqual(event["prompt_sha256"], benchmark.digest(prompt))

            tokens = telemetry(path / "stdout.jsonl", "antigravity")
            self.assertTrue(all(tokens[key] is None for key in (
                "input", "output", "cached", "reasoning", "provider_total", "total"
            )))
            self.assertEqual(
                benchmark.command_metrics(path / "stdout.jsonl", "antigravity"),
                {"tool_calls": None, "failed_commands": None},
            )

    def test_command_metrics_ignores_malformed_items(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.jsonl"
            path.write_text(
                json.dumps({"type": "thread.started"})
                + "\n"
                + json.dumps({"type": "item.completed", "item": None})
                + "\n"
                + json.dumps({"type": "item.completed", "item": {"type": "command_execution"}})
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(benchmark.command_metrics(path, "codex"), {"tool_calls": 0, "failed_commands": 0})


class PreflightPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "probe.txt").write_bytes(b"offline preflight")
        self.manifest = read(ROOT / "experiments/examples/run-manifest.example.json")
        self.profile = {"sandbox_policy": "prompt-and-log"}
        self.receipt = {
            "access_policy": "prompt-and-log",
            "base_commit": self.manifest["execution"]["base_commit"],
            "profile_sha256": self.manifest["execution"]["profile_sha256"],
            "checks": dict.fromkeys(
                ["idf_build", "compiler", "ninja", "git", "temp_write",
                 "network_policy", "settings_inventory", "prompt_scope", "activity_logging"], "pass"),
            "evidence": {"probe.txt": benchmark.digest(b"offline preflight")},
        }
        self.receipt["checks"]["read_isolation"] = "not_enforced"

    def validate(self):
        benchmark.validate_preflight_receipt(self.receipt, self.manifest, self.profile, self.root)

    def test_prompt_and_log_accepts_no_os_isolation(self):
        self.validate()

    def test_prompt_scope_and_logging_required(self):
        for key in ("prompt_scope", "activity_logging"):
            with self.subTest(key=key):
                self.receipt["checks"][key] = "not_run"
                with self.assertRaises(ValueError):
                    self.validate()
                self.receipt["checks"][key] = "pass"

    def test_prompt_mode_cannot_claim_os_isolation(self):
        self.receipt["checks"]["read_isolation"] = "pass"
        with self.assertRaises(ValueError):
            self.validate()

    def test_external_sandbox_requires_real_isolation(self):
        self.receipt["access_policy"] = self.profile["sandbox_policy"] = "external-sandbox"
        with self.assertRaises(ValueError):
            self.validate()
        self.receipt["checks"]["read_isolation"] = "pass"
        self.validate()

    def test_policy_and_baseline_profile_binding(self):
        for key in ("access_policy", "base_commit", "profile_sha256"):
            with self.subTest(key=key):
                original = self.receipt[key]
                self.receipt[key] = "wrong"
                with self.assertRaises(ValueError):
                    self.validate()
                self.receipt[key] = original

    def test_receipt_binds_semantic_execution_profile_hash(self):
        semantic_hash = benchmark.profile_digest(self.profile)
        reformatted = json.loads(json.dumps(self.profile, indent=4))
        self.assertEqual(semantic_hash, benchmark.profile_digest(reformatted))
        self.manifest["execution"]["profile_sha256"] = semantic_hash
        self.receipt["profile_sha256"] = semantic_hash
        # Deliberately make the saved JSON byte hash different. Receipt
        # validation must use execution.profile_sha256, not this field.
        self.manifest["agent"]["configuration_sha256"] = "f" * 64
        self.validate()

        self.manifest["execution"]["profile_sha256"] = "e" * 64
        with self.assertRaisesRegex(ValueError, "preflight receipt mismatch: profile_sha256"):
            self.validate()

    def test_policy_must_match_profile(self):
        self.profile["sandbox_policy"] = "external-sandbox"
        with self.assertRaises(ValueError):
            self.validate()

    def test_evidence_hash_is_verified(self):
        (self.root / "probe.txt").write_bytes(b"changed evidence")
        with self.assertRaises(ValueError):
            self.validate()


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


class ResolvedProfileTests(unittest.TestCase):
    def setUp(self):
        self.profile = read(ROOT / "experiments/config/runner-profile.example.json")
        self.profile.update(agent_version="test", model="example-model", model_slug="example-model",
                            reasoning="fixed", argv=[sys.executable], version_argv=[sys.executable, "--version"],
                            approval_policy="workspace-write", settings_inventory=dict(
                                skills="disabled", mcp="disabled", memory="none", user_instructions="none",
                                cache="cold", routing="fixed"))

    def test_unresolved_model_and_embedded_settings_are_rejected(self):
        benchmark.validate_resolved_profile(self.profile)
        for marker in ("user-confirm-required", "operator-check-required", "pending"):
            profile = copy.deepcopy(self.profile)
            profile["settings_inventory"]["skills"] = f"disabled by policy; {marker}"
            with self.assertRaisesRegex(ValueError, "unresolved settings"):
                benchmark.validate_resolved_profile(profile)
        self.profile["model"] = "user-confirm-required"
        with self.assertRaises(ValueError):
            benchmark.validate_resolved_profile(self.profile)

    def test_antigravity_input_must_match_plain_stdin_delivery(self):
        self.profile.update(adapter="antigravity", argv=["agy.exe", "--print", "--input-format",
                                                       "stream-json", "--output-format", "stream-json"])
        with self.assertRaisesRegex(ValueError, "plain UTF-8"):
            benchmark.validate_resolved_profile(self.profile)
        self.profile["argv"][3] = "text"
        benchmark.validate_resolved_profile(self.profile)

    def test_draft_profiles_are_schema_valid_but_not_executable(self):
        for path in (ROOT / "experiments/config/verified-profiles-draft").glob("*.json"):
            profile = read(path)
            validate_schema(profile, "runner-profile.schema.json")
            with self.assertRaises(ValueError):
                benchmark.validate_resolved_profile(profile)


class InputBundleCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="meter-check-", dir=ascii_temp_dir())
        self.addCleanup(self.temp.cleanup)
        self.profile = read(ROOT / "experiments/config/runner-profile.example.json")
        self.profile.update(
            agent_version="test",
            model="example-model",
            model_slug="example-model",
            reasoning="fixed",
            argv=[sys.executable],
            version_argv=[sys.executable, "--version"],
            approval_policy="workspace-write",
            settings_inventory=dict(
                skills="disabled", mcp="disabled", memory="none", user_instructions="none",
                cache="cold", routing="fixed",
            ),
        )
        self.profile_path = Path(self.temp.name) / "profile.json"
        self.profile_path.write_text(json.dumps(self.profile), encoding="utf-8")

    def args(self, baseline="HEAD"):
        return SimpleNamespace(baseline=baseline, profile=str(self.profile_path))

    def test_check_hashes_full_bundle_without_reserving_or_mutating(self):
        before = sorted(path.name for path in ROOT.iterdir())
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            benchmark.check_inputs(self.args())
        after = sorted(path.name for path in ROOT.iterdir())
        self.assertEqual(before, after)
        record = json.loads(output.getvalue())
        self.assertFalse(record["run_id_reserved"])
        self.assertFalse(record["worktree_touched"])
        for key in ("prompt_sha256", "config_sha256", "fixture_sha256", "schema_sha256", "evaluation_criteria_sha256", "profile_sha256", "input_bundle_sha256"):
            self.assertRegex(record[key], r"^[a-f0-9]{64}$")
        self.assertEqual(record["profile_sha256"], benchmark.profile_digest(self.profile))

    def test_check_rejects_invalid_profile(self):
        invalid = copy.deepcopy(self.profile)
        invalid["model"] = "operator-check-required"
        self.profile_path.write_text(json.dumps(invalid), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unresolved settings"):
            benchmark.check_inputs(self.args())

    def test_check_rejects_invalid_baseline(self):
        with self.assertRaises(subprocess.CalledProcessError):
            benchmark.check_inputs(self.args("not-a-real-baseline-ref"))


class IsolationTests(unittest.TestCase):
    def test_prepare_reserves_ids_and_excludes_parent_history(self):
        with tempfile.TemporaryDirectory(prefix="meter-test-", dir=ascii_temp_dir()) as folder:
            root = Path(folder)
            repo = root / "repo"
            repo.mkdir()
            shutil.copytree(ROOT / "experiments", repo / "experiments")
            shutil.copytree(ROOT / "docs", repo / "docs")
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
                check_output = io.StringIO()
                with contextlib.redirect_stdout(check_output):
                    benchmark.check_inputs(SimpleNamespace(baseline="HEAD", profile=str(profile_path)))
                checked = json.loads(check_output.getvalue())
                benchmark.prepare(args)
                benchmark.prepare(args)
                bad_profile = dict(profile, model="operator-check-required")
                bad_profile_path = root / "bad-profile.json"
                bad_profile_path.write_text(json.dumps(bad_profile), encoding="utf-8")
                with self.assertRaises(ValueError):
                    benchmark.prepare(SimpleNamespace(**{**vars(args), "profile": str(bad_profile_path)}))
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
                fixture_lines = [
                    f"{benchmark.digest(path.read_bytes())}  {path.relative_to(run / 'checkout').as_posix()}"
                    for path in sorted((run / "checkout" / "experiments" / "fixtures").rglob("*.json"))
                ]
                expected_fixture_hash = benchmark.digest(("\n".join(fixture_lines) + "\n").encode())
                self.assertEqual(m["execution"]["fixture_sha256"], expected_fixture_hash)
                hashes = benchmark.input_bundle_hashes(
                    run / "checkout", run / "profile.json", m["baseline_ref"], m["execution"]["base_commit"]
                )
                for key, expected in hashes.items():
                    self.assertEqual(m["execution"][key], expected)
                if index == 0:
                    for key in hashes:
                        self.assertEqual(checked[key], m["execution"][key])
                    self.assertEqual(checked["baseline_commit"], m["execution"]["base_commit"])
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


class E2EArchiveContractTests(unittest.TestCase):
    def test_archive_semantic_join_and_final_mutation_validation(self):
        result = read(ROOT / "experiments/examples/end-to-end-result.example.json")
        evaluation_manifest = read(ROOT / "experiments/examples/end-to-end-manifest.example.json")
        run_manifest = {
            "run_id": result["run_id"],
            "experiment_id": result["experiment_id"],
            "baseline_id": result["baseline_id"],
            "baseline_ref": result["baseline"]["ref"],
            "execution": {"base_commit": result["baseline"]["commit"]},
            "outputs": {"evaluation_manifest": f"results/{result['run_id']}/e2e-evaluation-manifest.json"},
        }
        with tempfile.TemporaryDirectory(prefix="meter-e2e-archive-", dir=ascii_temp_dir()) as folder:
            directory = Path(folder)
            (directory / "e2e-evaluation-manifest.json").write_text(json.dumps(evaluation_manifest), encoding="utf-8")
            benchmark._check_e2e_manifest_join(evaluation_manifest, run_manifest, result)
            benchmark._validate_final_e2e_candidate(result, evaluation_manifest, run_manifest, ROOT, directory)
            self.assertEqual(result["manifest"]["path"], run_manifest["outputs"]["evaluation_manifest"])

    def test_archive_uses_integration_evidence_not_product_pass_for_test_status(self):
        result = read(ROOT / "experiments/examples/end-to-end-result.example.json")
        result["product_pass"] = True
        self.assertEqual(benchmark.derive_e2e_automated_test_status(result), "partial")


if __name__ == "__main__":
    unittest.main()
