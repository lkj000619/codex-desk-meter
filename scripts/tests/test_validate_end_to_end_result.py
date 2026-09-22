import importlib.util
import copy
import json
import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_end_to_end_result", SCRIPTS / "validate-end-to-end-result.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validator = load_validator()


def read_json(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


class EndToEndResultTests(unittest.TestCase):
    def test_valid_examples(self):
        for relative_path in (
            "experiments/examples/end-to-end-result.example.json",
            "experiments/examples/end-to-end-hardware-not-run.example.json",
        ):
            result = read_json(relative_path)
            validator.validate_result(result, evidence_root=ROOT)

    def test_invalid_examples_report_stable_codes(self):
        expected = {
            "pass-without-evidence.example.json": "EVIDENCE_REQUIRED",
            "missing-identity.example.json": "IDENTITY_REQUIRED",
            "fabricated-token.example.json": "TOKEN_TELEMETRY_UNAVAILABLE",
            "invalid-product-pass.example.json": "PRODUCT_PASS_REQUIRES_CORE_RESULTS",
        }
        for filename, code in expected.items():
            result = read_json(f"experiments/examples/invalid/{filename}")
            with self.subTest(filename=filename):
                with self.assertRaises(validator.ValidationError) as context:
                    validator.validate_result(result, evidence_root=ROOT)
                self.assertEqual(context.exception.code, code)

    def test_provider_and_host_are_distinct(self):
        result = read_json("experiments/examples/end-to-end-result.example.json")
        result["provider_matrix"][0]["host_id"] = result["provider_matrix"][0]["provider_id"]
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_result(result, evidence_root=ROOT)
        self.assertEqual(context.exception.code, "IDENTITY_PROVIDER_HOST_COLLISION")

    def test_missing_evidence_path_is_rejected(self):
        result = read_json("experiments/examples/end-to-end-result.example.json")
        result["feature_results"]["F1"]["evidence"] = ["does-not-exist.txt"]
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_result(result, evidence_root=ROOT)
        self.assertEqual(context.exception.code, "EVIDENCE_NOT_FOUND")

    def test_fixture_schema_and_semantics(self):
        validator.validate_fixture_matrix(ROOT / "experiments/fixtures/provider-fixture-matrix.json")

        valid = read_json("experiments/fixtures/providers/codex-percent-window.json")
        validator.validate_snapshot(valid, reference_time="2026-09-10T00:04:59Z")

        duplicate = read_json("experiments/fixtures/providers/duplicate-provider-window.json")
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_snapshot(duplicate, reference_time="2026-09-10T00:04:59Z")
        self.assertEqual(context.exception.code, "DUPLICATE_WINDOW")

        future = read_json("experiments/fixtures/providers/future-observed-reset.json")
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_snapshot(future, reference_time="2026-09-11T00:00:00Z")
        self.assertEqual(context.exception.code, "FUTURE_TIMESTAMP")

        out_of_range = read_json("experiments/fixtures/providers/out-of-range-percent.json")
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_snapshot(out_of_range, reference_time="2026-09-11T00:00:00Z")
        self.assertEqual(context.exception.code, "SCHEMA_INVALID")

    def test_single_input_multi_provider_fixture_is_genuine(self):
        fixture = read_json("experiments/fixtures/providers/multi-provider-healthy.json")
        self.assertIsInstance(fixture, list)
        self.assertGreaterEqual(len(fixture), 3)
        self.assertEqual({entry["provider_id"] for entry in fixture}, {"openai", "anthropic", "google"})
        self.assertEqual({entry["agent_id"] for entry in fixture}, {"codex-cli", "claude-code", "gemini-cli"})
        validator.validate_fixture_file(
            ROOT / "experiments/fixtures/providers/multi-provider-healthy.json",
            reference_time="2026-09-10T00:04:59Z",
        )

    def test_external_manifest_is_schema_validated_and_joined(self):
        result = read_json("experiments/examples/end-to-end-result.example.json")
        manifest = read_json("experiments/examples/end-to-end-manifest.example.json")
        validator.validate_result(result, manifest=manifest, evidence_root=ROOT)

        mutations = (
            ("run_id", "RUN_ID_MISMATCH"),
            ("result_id", "RESULT_ID_MISMATCH"),
            ("experiment_id", "EXPERIMENT_ID_MISMATCH"),
            ("baseline_id", "BASELINE_MISMATCH"),
            ("baseline_ref", "BASELINE_REF_MISMATCH"),
        )
        for field, code in mutations:
            mutated = copy.deepcopy(manifest)
            mutated[field] = "mismatched-value"
            with self.subTest(field=field):
                with self.assertRaises(validator.ValidationError) as context:
                    validator.validate_result(result, manifest=mutated, evidence_root=ROOT)
                self.assertEqual(context.exception.code, code)

        base_commit = copy.deepcopy(manifest)
        base_commit["execution"]["base_commit"] = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_result(result, manifest=base_commit, evidence_root=ROOT)
        self.assertEqual(context.exception.code, "BASE_COMMIT_MISMATCH")

        empty = {}
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_result(result, manifest=empty, evidence_root=ROOT)
        self.assertEqual(context.exception.code, "SCHEMA_INVALID")

        by_reference = copy.deepcopy(manifest)
        by_reference.pop("result_id")
        by_reference["result_reference"] = result["result_id"]
        validator.validate_result(result, manifest=by_reference, evidence_root=ROOT)

        both_references = copy.deepcopy(manifest)
        both_references["result_reference"] = result["result_id"]
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_result(result, manifest=both_references, evidence_root=ROOT)
        self.assertEqual(context.exception.code, "SCHEMA_INVALID")

    def test_provider_duplicate_identity_is_complete(self):
        result = read_json("experiments/examples/end-to-end-result.example.json")
        distinct_model = copy.deepcopy(result["provider_matrix"][0])
        distinct_model["model_id"] = "codex-another-model"
        result["provider_matrix"].append(distinct_model)
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_result(result, evidence_root=ROOT)
        self.assertEqual(context.exception.code, "EVIDENCE_IDENTITY_MISMATCH")

        result = read_json("experiments/examples/end-to-end-result.example.json")
        result["provider_matrix"].append(copy.deepcopy(result["provider_matrix"][0]))
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_result(result, evidence_root=ROOT)
        self.assertEqual(context.exception.code, "DUPLICATE_PROVIDER")

    def test_absolute_units_use_tolerant_balance_arithmetic(self):
        snapshot = read_json("experiments/fixtures/providers/absolute-token-balance.json")
        validator.validate_snapshot(snapshot, reference_time="2026-09-10T00:04:59Z")
        snapshot["windows"][0]["remaining_units"] += 0.005
        validator.validate_snapshot(snapshot, reference_time="2026-09-10T00:04:59Z")
        snapshot["windows"][0]["remaining_units"] += 1
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_snapshot(snapshot, reference_time="2026-09-10T00:04:59Z")
        self.assertEqual(context.exception.code, "ABSOLUTE_BALANCE_MISMATCH")

    def test_future_and_expired_reset_times_are_classified(self):
        snapshot = read_json("experiments/fixtures/providers/codex-percent-window.json")
        snapshot["windows"][0]["resets_at"] = "2026-09-12T00:00:00Z"
        validator.validate_snapshot(snapshot, reference_time="2026-09-10T00:04:59Z")
        self.assertEqual(
            validator.classify_reset(snapshot["windows"][0]["resets_at"], "2026-09-10T00:04:59Z"),
            "scheduled",
        )
        snapshot["windows"][0]["resets_at"] = "2026-09-09T00:00:00Z"
        validator.validate_snapshot(snapshot, reference_time="2026-09-10T00:04:59Z")
        self.assertEqual(
            validator.classify_reset(snapshot["windows"][0]["resets_at"], "2026-09-10T00:04:59Z"),
            "expired",
        )

    def test_nullable_context_is_allowed_only_for_unavailable_sources(self):
        unsupported = read_json("experiments/fixtures/providers/gemini-cli-unsupported.json")
        unsupported["agent_id"] = None
        unsupported["host_id"] = None
        validator.validate_snapshot(unsupported, reference_time="2026-09-10T00:04:59Z")

        available = read_json("experiments/fixtures/providers/codex-percent-window.json")
        available["agent_id"] = None
        available["host_id"] = None
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_snapshot(available, reference_time="2026-09-10T00:04:59Z")
        self.assertEqual(context.exception.code, "IDENTITY_REQUIRED")

        result = read_json("experiments/examples/end-to-end-result.example.json")
        result["provider_matrix"][3]["agent_id"] = None
        result["provider_matrix"][3]["host_id"] = None
        validator.validate_result(result, evidence_root=ROOT)

    def test_stale_threshold_is_relative_to_reference_time(self):
        fresh = read_json("experiments/fixtures/providers/codex-percent-window.json")
        validator.validate_snapshot(fresh, reference_time="2026-09-10T00:04:59Z")
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_snapshot(fresh, reference_time="2026-09-10T00:05:00Z")
        self.assertEqual(context.exception.code, "STALE_THRESHOLD_EXCEEDED")

        stale = read_json("experiments/fixtures/providers/provider-stale.json")
        validator.validate_snapshot(stale, reference_time="2026-09-11T00:00:00Z")

    def test_agent_token_total_excludes_cached_and_reasoning(self):
        result = read_json("experiments/examples/end-to-end-result.example.json")
        result["telemetry"]["agent_tokens"] = {
            "input": 100,
            "output": 20,
            "cached": 80,
            "reasoning": 5,
            "provider_total": None,
            "total": 120,
        }
        result["telemetry"]["token_total_definition"] = "input_plus_output_excludes_cached_and_reasoning"
        result["telemetry"]["evidence"] = ["experiments/examples/README.md"]
        validator.validate_result(result, evidence_root=ROOT)

        result["telemetry"]["agent_tokens"]["total"] = 205
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_result(result, evidence_root=ROOT)
        self.assertEqual(context.exception.code, "TOKEN_TOTAL_MISMATCH")

    def test_provider_total_is_preserved_separately_from_normalized_total(self):
        result = read_json("experiments/examples/end-to-end-result.example.json")
        result["telemetry"]["agent_tokens"] = {
            "input": 2005,
            "output": 15,
            "cached": 0,
            "reasoning": 45,
            "provider_total": 2065,
            "total": 2020,
        }
        result["telemetry"]["provider_total_definition"] = "provider_reported_total_preserved_without_recomputation"
        result["telemetry"]["evidence"] = ["experiments/examples/README.md"]
        validator.validate_result(result, evidence_root=ROOT)

        missing = read_json("experiments/examples/end-to-end-result.example.json")
        missing["telemetry"]["agent_tokens"].pop("provider_total")
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_result(missing, evidence_root=ROOT)
        self.assertEqual(context.exception.code, "SCHEMA_INVALID")

    def test_product_pass_requires_individual_core_results(self):
        result = read_json("experiments/examples/end-to-end-result.example.json")
        result["product_pass"] = True
        result.pop("core_results")
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_result(result, evidence_root=ROOT)
        self.assertEqual(context.exception.code, "SCHEMA_INVALID")

    def test_core_results_are_required_for_non_passing_results(self):
        result = read_json("experiments/examples/end-to-end-result.example.json")
        result.pop("core_results")
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_result(result, evidence_root=ROOT)
        self.assertEqual(context.exception.code, "SCHEMA_INVALID")

    def test_f9_details_require_three_evidenced_candidates(self):
        result = read_json("experiments/examples/end-to-end-result.example.json")
        evidence = ["experiments/examples/README.md"]
        result["feature_results"]["F9"]["details"] = {
            "candidate_count": 3,
            "candidates": [
                {"id": "imu", "name": "IMU", "user_value": "value", "implementation_cost": "cost", "risk": "risk", "verification_method": "method", "selection_status": "rejected", "selection_reason": "less useful", "evidence": evidence},
                {"id": "rtc", "name": "RTC", "user_value": "value", "implementation_cost": "cost", "risk": "risk", "verification_method": "method", "selection_status": "rejected", "selection_reason": "higher risk", "evidence": evidence},
                {"id": "battery", "name": "Battery", "user_value": "value", "implementation_cost": "cost", "risk": "risk", "verification_method": "method", "selection_status": "rejected", "selection_reason": "not portable", "evidence": evidence},
            ],
            "selected_candidate": None,
            "score_breakdown": {"hardware_understanding": 0, "user_value": 0, "selection_logic": 0, "implementation_completeness": 0, "separation_portability": 0, "total": 0},
        }
        validator.validate_result(result, evidence_root=ROOT)

    def test_f9_score_total_is_the_canonical_sum(self):
        result = read_json("experiments/examples/end-to-end-result.example.json")
        evidence = ["experiments/examples/README.md"]
        result["feature_results"]["F9"] = {
            "status": "partial", "scope": "autonomy", "evidence": evidence,
            "reason": "candidate assessment only", "details": {
                "candidate_count": 3,
                "candidates": [
                    {"id": "a", "name": "A", "user_value": "value", "implementation_cost": "cost", "risk": "risk", "verification_method": "method", "selection_status": "rejected", "selection_reason": "not selected", "evidence": evidence},
                    {"id": "b", "name": "B", "user_value": "value", "implementation_cost": "cost", "risk": "risk", "verification_method": "method", "selection_status": "rejected", "selection_reason": "not selected", "evidence": evidence},
                    {"id": "c", "name": "C", "user_value": "value", "implementation_cost": "cost", "risk": "risk", "verification_method": "method", "selection_status": "rejected", "selection_reason": "not selected", "evidence": evidence},
                ],
                "selected_candidate": None,
                "score_breakdown": {"hardware_understanding": 5, "user_value": 5, "selection_logic": 5, "implementation_completeness": 10, "separation_portability": 5, "total": 29},
            }
        }
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_result(result, evidence_root=ROOT)
        self.assertEqual(context.exception.code, "F9_SCORE_TOTAL_MISMATCH")
        result["feature_results"]["F9"]["details"]["score_breakdown"]["total"] = 30
        validator.validate_result(result, evidence_root=ROOT)

    def test_f9_details_are_forbidden_on_f1_to_f8(self):
        result = read_json("experiments/examples/end-to-end-result.example.json")
        result["feature_results"]["F1"]["details"] = {
            "candidate_count": 3,
            "candidates": [],
            "selected_candidate": None,
            "score_breakdown": {"hardware_understanding": 0, "user_value": 0, "selection_logic": 0, "implementation_completeness": 0, "separation_portability": 0, "total": 0},
        }
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_result(result, evidence_root=ROOT)
        self.assertEqual(context.exception.code, "SCHEMA_INVALID")

    def test_fixture_evidence_must_match_provider_identity_and_windows(self):
        result = read_json("experiments/examples/end-to-end-result.example.json")
        result["provider_matrix"][0]["provider_id"] = "anthropic"
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_result(result, evidence_root=ROOT)
        self.assertEqual(context.exception.code, "EVIDENCE_IDENTITY_MISMATCH")

    def test_product_pass_requires_gui_scores_and_evidence(self):
        result = read_json("experiments/examples/end-to-end-result.example.json")
        evidence = "experiments/examples/README.md"
        for entry in result["feature_results"].values():
            entry.update(status="pass", evidence=[evidence], reason=None)
        for entry in result["integration_results"].values():
            entry.update(status="pass", evidence=[evidence], reason=None)
        for key in ("build", "host", "transport", "hardware"):
            result[key].update(status="pass", evidence=[evidence], reason=None)
        result["transport"]["choice"] = "usb-serial"
        result["core_results"] = {
            f"C{i}": {"status": "pass", "scope": "core", "evidence": [evidence], "reason": None}
            for i in range(1, 9)
        }
        result["feature_results"]["F9"]["details"] = {
            "candidate_count": 3,
            "candidates": [
                {"id": "a", "name": "A", "user_value": "value", "implementation_cost": "cost", "risk": "risk", "verification_method": "method", "selection_status": "selected", "selection_reason": "best", "evidence": [evidence]},
                {"id": "b", "name": "B", "user_value": "value", "implementation_cost": "cost", "risk": "risk", "verification_method": "method", "selection_status": "rejected", "selection_reason": "less useful", "evidence": [evidence]},
                {"id": "c", "name": "C", "user_value": "value", "implementation_cost": "cost", "risk": "risk", "verification_method": "method", "selection_status": "rejected", "selection_reason": "higher risk", "evidence": [evidence]},
            ],
            "selected_candidate": "a",
            "score_breakdown": {"hardware_understanding": 5, "user_value": 5, "selection_logic": 5, "implementation_completeness": 10, "separation_portability": 5, "total": 30},
        }
        result["product_pass"] = True
        with self.assertRaises(validator.ValidationError) as context:
            validator.validate_result(result, evidence_root=ROOT)
        self.assertEqual(context.exception.code, "PRODUCT_PASS_REQUIRES_GUI")

    def test_historical_validator_examples_remain_untouched(self):
        historical = SCRIPTS / "validate-experiment-result.py"
        completed = __import__("subprocess").run(
            [sys.executable, str(historical)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
