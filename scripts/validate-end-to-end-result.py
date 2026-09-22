"""Validate the synthetic end-to-end contract and provider snapshots.

The validator intentionally performs checks that JSON Schema cannot express:
identity joins, evidence paths, status/evidence/reason pairing, provider/host
separation, duplicate windows, timestamp freshness, telemetry provenance, and
the product-pass gate.  It never reads credentials or contacts a provider.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "experiments" / "examples"
SCHEMA_DIR = ROOT / "experiments" / "schema"
STATUSES = {"pass", "partial", "fail", "not_run", "blocked", "timeout"}
PROVIDER_STATUSES = {"available", "unavailable", "unsupported", "unauthorized", "error", "stale"}
HOST_IDS = {"terminal", "orca", "antigravity", "vscode"}
PROVIDER_IDS = {"openai", "anthropic", "google"}
IDENTITY_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ABSOLUTE_BALANCE_TOLERANCE = 0.01
STALE_THRESHOLD_SECONDS = 300


class ValidationError(ValueError):
    """A stable, machine-readable validation failure."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def fail(code: str, message: str) -> None:
    raise ValidationError(code, message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        fail("FILE_NOT_FOUND", str(path))
        raise AssertionError from exc
    except json.JSONDecodeError as exc:
        fail("INVALID_JSON", f"{path}: {exc}")
        raise AssertionError from exc


def schema_validate(value: Any, filename: str) -> None:
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as exc:
        fail("SCHEMA_ENGINE_UNAVAILABLE", "install scripts/requirements-benchmark.txt")
        raise AssertionError from exc

    schema = load_json(SCHEMA_DIR / filename)
    try:
        Draft202012Validator.check_schema(schema)
        errors = sorted(
            Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
            key=lambda error: list(error.absolute_path),
        )
    except (TypeError, ValueError) as exc:
        fail("SCHEMA_ENGINE_ERROR", f"{filename}: {exc}")
        raise AssertionError from exc
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        fail("SCHEMA_INVALID", f"{filename}:{location}: {error.message}")


def parse_timestamp(value: Any, where: str, nullable: bool = False) -> datetime | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        fail("TIMESTAMP_INVALID", f"{where} must be an RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        fail("TIMESTAMP_INVALID", f"{where} is not RFC3339: {value!r}")
        raise AssertionError from exc
    if parsed.tzinfo is None:
        fail("TIMESTAMP_INVALID", f"{where} must include a timezone")
    return parsed.astimezone(timezone.utc)


def as_of(value: str | datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = parse_timestamp(value, "reference_time")
        assert parsed is not None
    return parsed.astimezone(timezone.utc)


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def relative_path(value: Any, where: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        fail("EVIDENCE_PATH_INVALID", f"{where} must be a relative path")
    # Evidence is deliberately portable and must not escape the selected root.
    path = Path(value)
    if path.is_absolute() or re.match(r"^[A-Za-z]:", value) or "\\" in value:
        fail("EVIDENCE_PATH_INVALID", f"{where} must use a relative POSIX path")
    if any(part in {"", ".", ".."} for part in path.parts):
        fail("EVIDENCE_PATH_INVALID", f"{where} contains an unsafe path")
    return path


def check_evidence(paths: Iterable[str], where: str, evidence_root: Path) -> None:
    root = evidence_root.resolve()
    for index, value in enumerate(paths):
        path = relative_path(value, f"{where}[{index}]")
        resolved = (root / path).resolve()
        if not resolved.is_relative_to(root) or not resolved.is_file():
            fail("EVIDENCE_NOT_FOUND", f"{where}[{index}] does not exist: {value}")


def check_status_entry(entry: dict[str, Any], where: str, evidence_root: Path) -> None:
    status = entry["status"]
    evidence = entry["evidence"]
    reason = entry["reason"]
    check_evidence(evidence, f"{where}.evidence", evidence_root)
    if status == "pass" and not evidence:
        fail("EVIDENCE_REQUIRED", f"{where} is pass but has no evidence")
    if status != "pass" and not nonempty(reason):
        fail("REASON_REQUIRED", f"{where} is {status} but has no reason")


def check_identity(
    provider_id: Any,
    agent_id: Any,
    host_id: Any,
    model_id: Any,
    account_profile_id: Any,
    where: str,
    status: str,
) -> None:
    if not nonempty(provider_id):
        fail("IDENTITY_REQUIRED", f"{where} requires provider identity")
    if status == "available" and (not nonempty(agent_id) or not nonempty(host_id)):
        fail("IDENTITY_REQUIRED", f"{where} requires agent and host identity for available data")
    for field, value in (("provider_id", provider_id), ("agent_id", agent_id), ("host_id", host_id)):
        if value is not None and (not nonempty(value) or not IDENTITY_RE.fullmatch(value)):
            fail("IDENTITY_INVALID", f"{where}.{field} is null or not a normalized identity")
    if model_id is not None and not nonempty(model_id):
        fail("IDENTITY_INVALID", f"{where}.model_id must be null or non-empty")
    if account_profile_id is not None and not IDENTITY_RE.fullmatch(account_profile_id):
        fail("IDENTITY_INVALID", f"{where}.account_profile_id is not a pseudonymous alias")
    if provider_id == host_id:
        fail("IDENTITY_PROVIDER_HOST_COLLISION", f"{where} uses one value for provider and host")
    if provider_id in HOST_IDS:
        fail("IDENTITY_PROVIDER_HOST_COLLISION", f"{where}.provider_id is a host identifier")
    if host_id in PROVIDER_IDS:
        fail("IDENTITY_PROVIDER_HOST_COLLISION", f"{where}.host_id is a provider identifier")
    if status == "available" and account_profile_id is None:
        fail("IDENTITY_REQUIRED", f"{where}.account_profile_id is required for available data")


def check_window(window: dict[str, Any], where: str, reference: datetime) -> None:
    unit = window["unit"]
    absolute = [window["used_units"], window["remaining_units"], window["limit_units"]]
    percentages = [window["percent_used"], window["percent_remaining"]]
    if unit == "percent" and any(value is not None for value in absolute):
        fail("UNIT_VALUE_MISMATCH", f"{where} percent window contains absolute units")
    if unit in {"token", "credit"} and any(value is None for value in absolute):
        fail("ABSOLUTE_VALUE_MISSING", f"{where} {unit} window requires used, remaining, and limit")
    if unit == "unknown" and any(value is not None for value in absolute):
        fail("UNIT_VALUE_MISMATCH", f"{where} unknown unit contains absolute units")
    if (percentages[0] is None) != (percentages[1] is None):
        fail("PERCENTAGE_INVALID", f"{where} contains an invalid percentage pair")
    if all(value is not None for value in percentages):
        assert percentages[0] is not None and percentages[1] is not None
        if abs((percentages[0] + percentages[1]) - 100) > 0.01:
            fail("PERCENTAGE_INCONSISTENT", f"{where} used and remaining percentages do not sum to 100")
    if all(value is not None for value in absolute):
        assert absolute[0] is not None and absolute[1] is not None and absolute[2] is not None
        if abs((absolute[0] + absolute[1]) - absolute[2]) > ABSOLUTE_BALANCE_TOLERANCE:
            fail(
                "ABSOLUTE_BALANCE_MISMATCH",
                f"{where} used plus remaining must equal limit within {ABSOLUTE_BALANCE_TOLERANCE}",
            )
    reset = parse_timestamp(window["resets_at"], f"{where}.resets_at", nullable=True)
    reset_status = window.get("reset_status")
    if reset_status is not None:
        expected = "unknown" if reset is None else ("scheduled" if reset >= reference else "expired")
        if reset_status != expected:
            fail("RESET_STATUS_MISMATCH", f"{where}.reset_status must be {expected!r}")


def classify_reset(value: str | None, reference_time: str | datetime | None = None) -> str:
    """Classify a reset without treating a legitimate future reset as invalid."""

    reset = parse_timestamp(value, "reset", nullable=True)
    if reset is None:
        return "unknown"
    return "scheduled" if reset >= as_of(reference_time) else "expired"


def validate_snapshot(snapshot: dict[str, Any], reference_time: str | datetime | None = None) -> None:
    """Validate one normalized UsageSnapshot through its public contract."""

    schema_validate(snapshot, "usage-snapshot.schema.json")
    reference = as_of(reference_time)
    status = snapshot["status"]
    check_identity(
        snapshot["provider_id"],
        snapshot["agent_id"],
        snapshot["host_id"],
        snapshot["model_id"],
        snapshot["account_profile_id"],
        "snapshot",
        status,
    )
    observed = parse_timestamp(snapshot["observed_at"], "snapshot.observed_at", nullable=True)
    last_good = parse_timestamp(snapshot["last_good_at"], "snapshot.last_good_at", nullable=True)
    if observed is not None and observed > reference:
        fail("FUTURE_TIMESTAMP", "snapshot.observed_at is after the reference time")
    if last_good is not None and last_good > reference:
        fail("FUTURE_TIMESTAMP", "snapshot.last_good_at is after the reference time")
    if observed is not None and last_good is not None and last_good > observed:
        fail("TIMESTAMP_ORDER", "snapshot.last_good_at is later than observed_at")
    if status == "available" and snapshot["stale"]:
        fail("STATUS_STALE_MISMATCH", "available snapshot cannot set stale=true")
    if status == "stale" and not snapshot["stale"]:
        fail("STATUS_STALE_MISMATCH", "stale snapshot must set stale=true")
    if status in {"unavailable", "unsupported", "unauthorized", "error", "stale"}:
        if not nonempty(snapshot["error_code"]) or not nonempty(snapshot["error_reason"]):
            fail("ERROR_REASON_REQUIRED", f"{status} snapshot requires error_code and error_reason")
    if status == "available" and snapshot["error_code"] is not None:
        fail("ERROR_STATE_MISMATCH", "available snapshot cannot carry error_code")
    if status == "stale" and last_good is None:
        fail("LAST_GOOD_REQUIRED", "stale snapshot requires last_good_at")
    if observed is not None:
        age_seconds = (reference - observed).total_seconds()
        if age_seconds < 0:
            fail("FUTURE_TIMESTAMP", "snapshot.observed_at is after the reference time")
        if status == "available" and age_seconds >= STALE_THRESHOLD_SECONDS:
            fail("STALE_THRESHOLD_EXCEEDED", f"available snapshot is at least {STALE_THRESHOLD_SECONDS} seconds old")
        if snapshot["stale"] and age_seconds < STALE_THRESHOLD_SECONDS:
            fail("STALE_THRESHOLD_NOT_REACHED", f"stale snapshot is younger than {STALE_THRESHOLD_SECONDS} seconds")
    window_ids: set[str] = set()
    for index, window in enumerate(snapshot["windows"]):
        where = f"snapshot.windows[{index}]"
        if window["window_id"] in window_ids:
            fail("DUPLICATE_WINDOW", f"duplicate window_id {window['window_id']!r}")
        window_ids.add(window["window_id"])
        check_window(window, where, reference)
    if snapshot["unit"] == "percent" and any(window["unit"] not in {"percent", "unknown"} for window in snapshot["windows"]):
        fail("UNIT_VALUE_MISMATCH", "snapshot.unit=percent conflicts with a non-percent window")
    if snapshot["unit"] == "token" and any(window["unit"] not in {"token", "unknown"} for window in snapshot["windows"]):
        fail("UNIT_VALUE_MISMATCH", "snapshot.unit=token conflicts with a non-token window")


def _load_manifest(manifest: dict[str, Any] | Path | str | None) -> dict[str, Any] | None:
    if manifest is None:
        return None
    if isinstance(manifest, (Path, str)):
        value = load_json(Path(manifest))
    else:
        value = manifest
    if not isinstance(value, dict):
        fail("MANIFEST_INVALID", "manifest must be a JSON object")
    schema_validate(value, "end-to-end-manifest.schema.json")
    return value


def _check_join(result: dict[str, Any], manifest: dict[str, Any] | None) -> None:
    if result["manifest"]["id"] != result["manifest_id"]:
        fail("RESULT_ID_MISMATCH", "manifest.id must equal manifest_id")
    if result["manifest"]["experiment_id"] != result["experiment_id"]:
        fail("EXPERIMENT_ID_MISMATCH", "manifest experiment_id does not match result")
    if result["manifest"]["baseline_id"] != result["baseline_id"]:
        fail("BASELINE_MISMATCH", "manifest baseline_id does not match result")
    if result["baseline"]["id"] != result["baseline_id"]:
        fail("BASELINE_MISMATCH", "baseline.id does not match result")
    if not nonempty(result["baseline"].get("ref")):
        fail("BASELINE_REF_REQUIRED", "baseline.ref is required for reproducible joins")
    if result["baseline"]["experiment_id"] != result["experiment_id"]:
        fail("EXPERIMENT_ID_MISMATCH", "baseline experiment_id does not match result")
    if manifest is None:
        fail("MANIFEST_REQUIRED", "an external manifest is required")
    if manifest["manifest_id"] != result["manifest_id"]:
        fail("RESULT_ID_MISMATCH", "external manifest ID does not match result")
    if manifest["run_id"] != result["run_id"]:
        fail("RUN_ID_MISMATCH", "external manifest run_id does not match result")
    if manifest["experiment_id"] != result["experiment_id"]:
        fail("EXPERIMENT_ID_MISMATCH", "external manifest experiment does not match result")
    if manifest["baseline_id"] != result["baseline_id"]:
        fail("BASELINE_MISMATCH", "external manifest baseline does not match result")
    if manifest["baseline_ref"] != result["baseline"]["ref"]:
        fail("BASELINE_REF_MISMATCH", "external manifest baseline_ref does not match result baseline.ref")
    result_reference = manifest.get("result_id", manifest.get("result_reference"))
    if result_reference != result["result_id"]:
        fail("RESULT_ID_MISMATCH", "external manifest result reference does not match result")
    if manifest["execution"]["base_commit"] != result["baseline"]["commit"]:
        fail("BASE_COMMIT_MISMATCH", "external manifest base_commit does not match result baseline commit")


def _check_provider_matrix(result: dict[str, Any], evidence_root: Path) -> None:
    seen: set[tuple[Any, ...]] = set()
    for index, entry in enumerate(result["provider_matrix"]):
        where = f"provider_matrix[{index}]"
        check_identity(
            entry["provider_id"],
            entry["agent_id"],
            entry["host_id"],
            entry["model_id"],
            entry["account_profile_id"],
            where,
            entry["status"],
        )
        identity = (
            entry["provider_id"],
            entry["agent_id"],
            entry["host_id"],
            entry["model_id"],
            entry["account_profile_id"],
            entry["metric_kind"],
            entry["source_kind"],
            entry["source_id"],
            tuple(sorted(entry["window_ids"])),
        )
        if identity in seen:
            fail("DUPLICATE_PROVIDER", f"duplicate provider identity {identity}")
        seen.add(identity)
        check_evidence(entry["snapshot_paths"], f"{where}.snapshot_paths", evidence_root)
        check_evidence(entry["evidence"], f"{where}.evidence", evidence_root)
        if entry["source_kind"] == "fixture":
            _check_fixture_snapshot_join(entry, where, evidence_root)
        if entry["status"] == "available" and not entry["evidence"]:
            fail("EVIDENCE_REQUIRED", f"{where} is available but has no evidence")
        if entry["status"] != "available" and not nonempty(entry["reason"]):
            fail("REASON_REQUIRED", f"{where} is {entry['status']} but has no reason")


def _check_fixture_snapshot_join(entry: dict[str, Any], where: str, evidence_root: Path) -> None:
    """Ensure fixture evidence actually describes the claimed provider result."""

    if not entry["snapshot_paths"]:
        fail("FIXTURE_EVIDENCE_REQUIRED", f"{where} fixture source has no snapshot_paths")
    expected_identity = tuple(
        entry[field]
        for field in ("provider_id", "agent_id", "host_id", "model_id", "account_profile_id", "metric_kind")
    )
    expected_windows = set(entry["window_ids"])
    matches = 0
    for index, relative in enumerate(entry["snapshot_paths"]):
        path = evidence_root / relative_path(relative, f"{where}.snapshot_paths[{index}]")
        try:
            value = load_json(path)
        except ValidationError as error:
            fail("FIXTURE_EVIDENCE_INVALID", f"{where}.snapshot_paths[{index}] is not valid JSON: {error.message}")
        snapshots = value if isinstance(value, list) else [value]
        if not snapshots or not all(isinstance(snapshot, dict) for snapshot in snapshots):
            fail("FIXTURE_EVIDENCE_INVALID", f"{where}.snapshot_paths[{index}] must contain snapshot objects")
        for snapshot in snapshots:
            identity = tuple(snapshot.get(field) for field in ("provider_id", "agent_id", "host_id", "model_id", "account_profile_id", "metric_kind"))
            # A nullable identity in an unavailable/unsupported entry means
            # that the source could not identify that dimension.  Treat it as
            # an unknown (wildcard) during the join, while still rejecting a
            # conflicting non-null claim.
            if any(expected is not None and expected != actual for expected, actual in zip(expected_identity, identity)):
                continue
            matches += 1
            if snapshot.get("status") != entry["status"]:
                fail("EVIDENCE_STATUS_MISMATCH", f"{where} status does not match fixture evidence")
            actual_windows = {window.get("window_id") for window in snapshot.get("windows", [])}
            if actual_windows != expected_windows:
                fail("EVIDENCE_WINDOW_MISMATCH", f"{where} window_ids do not match fixture evidence")
    if matches == 0:
        fail("EVIDENCE_IDENTITY_MISMATCH", f"{where} identity does not match fixture evidence")


def _check_telemetry(result: dict[str, Any], evidence_root: Path) -> None:
    telemetry = result["telemetry"]
    tokens = telemetry["agent_tokens"]
    check_evidence(telemetry["evidence"], "telemetry.evidence", evidence_root)
    values = [tokens.get(key) for key in ("input", "output", "cached", "reasoning", "provider_total", "total")]
    if telemetry["token_total_definition"] != "input_plus_output_excludes_cached_and_reasoning":
        fail("TOKEN_TOTAL_DEFINITION_INVALID", "agent token total definition is not the declared contract")
    if telemetry["provider_total_definition"] != "provider_reported_total_preserved_without_recomputation":
        fail("PROVIDER_TOTAL_DEFINITION_INVALID", "provider_total definition is not the declared contract")
    if any(value is not None for value in values) and not telemetry["evidence"]:
        fail("TOKEN_TELEMETRY_UNAVAILABLE", "agent token values require telemetry evidence")
    if any(value is None for value in values) and not nonempty(telemetry["availability_reason"]):
        fail("TOKEN_TELEMETRY_REASON_REQUIRED", "null token values require availability_reason")
    if any(value is not None for value in values):
        normalized = (tokens.get("input"), tokens.get("output"), tokens.get("total"))
        if any(value is not None for value in normalized) and any(value is None for value in normalized):
            fail("TOKEN_TOTAL_INCOMPLETE", "input, output, and normalized total are required together")
        if all(value is not None for value in normalized) and tokens["total"] != tokens["input"] + tokens["output"]:
            fail("TOKEN_TOTAL_MISMATCH", "agent token total must equal input plus output")
    if telemetry["wall_clock_seconds"] is not None and not telemetry["evidence"]:
        fail("TELEMETRY_EVIDENCE_REQUIRED", "wall-clock telemetry requires evidence")


def _check_product_pass(result: dict[str, Any]) -> None:
    if not result["product_pass"]:
        return
    if any(result["feature_results"][key]["status"] != "pass" for key in (f"F{i}" for i in range(1, 10))):
        fail("PRODUCT_PASS_REQUIRES_FEATURES", "product_pass requires F1-F9 to pass")
    if any(result["integration_results"][key]["status"] != "pass" for key in (f"I{i}" for i in range(1, 5))):
        fail("PRODUCT_PASS_REQUIRES_INTEGRATION", "product_pass requires I1-I4 to pass")
    for key in ("build", "host", "transport", "hardware"):
        if result[key]["status"] != "pass":
            fail("PRODUCT_PASS_REQUIRES_VALIDATION", f"product_pass requires {key}.status=pass")
    if result["transport"]["choice"] is None:
        fail("PRODUCT_PASS_REQUIRES_TRANSPORT", "product_pass requires a selected transport")
    if any(score["score"] is None or not score["evidence"] for score in result["gui_scores"].values()):
        fail("PRODUCT_PASS_REQUIRES_GUI", "product_pass requires scored GUI rubric items with evidence")


def _check_core_results(result: dict[str, Any], evidence_root: Path) -> None:
    core = result["core_results"]
    expected = {f"C{i}" for i in range(1, 9)}
    if set(core) != expected:
        fail("CORE_RESULTS_INCOMPLETE", "core_results must contain exactly C1-C8")
    for key, entry in core.items():
        check_status_entry(entry, f"core_results.{key}", evidence_root)
    if result["product_pass"] and any(core[key]["status"] != "pass" for key in sorted(core)):
        fail("PRODUCT_PASS_REQUIRES_CORE_RESULTS", "product_pass requires C1-C8 to pass")


def _check_f9_details(result: dict[str, Any], evidence_root: Path) -> None:
    f9 = result["feature_results"]["F9"]
    details = f9.get("details")
    if details is None:
        if f9["status"] in {"pass", "partial"} or result["product_pass"]:
            fail("F9_DETAILS_REQUIRED", "a passing F9 requires candidate and score evidence")
        return
    if details.get("candidate_count") != 3 or not isinstance(details.get("candidates"), list) or len(details["candidates"]) != 3:
        fail("F9_CANDIDATES_INVALID", "F9 details must contain exactly three candidates")
    ids = []
    for index, candidate in enumerate(details["candidates"]):
        required_text = ("id", "name", "user_value", "implementation_cost", "risk", "verification_method")
        if not isinstance(candidate, dict) or any(not nonempty(candidate.get(key)) for key in required_text):
            fail("F9_CANDIDATE_INVALID", f"F9 candidate {index} needs structured value, cost, risk, and verification fields")
        if candidate["id"] in ids:
            fail("F9_CANDIDATE_DUPLICATE", f"duplicate F9 candidate {candidate['id']}")
        ids.append(candidate["id"])
        if candidate.get("selection_status") not in {"selected", "rejected"}:
            fail("F9_SELECTION_INVALID", f"F9 candidate {candidate['id']} has an invalid selection_status")
        if not nonempty(candidate.get("selection_reason")) and not nonempty(candidate.get("selection_document")):
            fail("F9_SELECTION_EVIDENCE_REQUIRED", f"F9 candidate {candidate['id']} needs a selection/rejection reason or document reference")
        if nonempty(candidate.get("selection_document")):
            check_evidence(
                [candidate["selection_document"]],
                f"feature_results.F9.details.candidates[{index}].selection_document",
                evidence_root,
            )
        check_evidence(candidate.get("evidence", []), f"feature_results.F9.details.candidates[{index}].evidence", evidence_root)
        if not candidate.get("evidence"):
            fail("F9_EVIDENCE_REQUIRED", f"F9 candidate {candidate['id']} has no evidence")
    selected = details.get("selected_candidate")
    if selected is not None and selected not in ids:
        fail("F9_SELECTION_INVALID", "selected F9 candidate must reference one candidate")
    selected_by_status = [candidate["id"] for candidate in details["candidates"] if candidate["selection_status"] == "selected"]
    if len(selected_by_status) > 1:
        fail("F9_SELECTION_INVALID", "F9 details may select at most one candidate")
    if selected is not None and selected_by_status != [selected]:
        fail("F9_SELECTION_INVALID", "selected_candidate must agree with candidate selection_status")
    if selected is None and selected_by_status:
        fail("F9_SELECTION_INVALID", "candidate selection_status must agree with selected_candidate")
    if f9["status"] == "pass" and (selected is None or selected_by_status != [selected]):
        fail("F9_SELECTION_REQUIRED", "passing F9 requires one selected candidate")
    breakdown = details.get("score_breakdown")
    score_fields = ("hardware_understanding", "user_value", "selection_logic", "implementation_completeness", "separation_portability")
    if not isinstance(breakdown, dict) or any(field not in breakdown for field in (*score_fields, "total")):
        fail("F9_SCORE_INVALID", "F9 details require the canonical five-part score breakdown and total")
    expected_total = sum(breakdown[field] for field in score_fields)
    if breakdown["total"] != expected_total:
        fail("F9_SCORE_TOTAL_MISMATCH", "F9 score_breakdown.total must equal the five rubric scores")


def validate_result(
    result: dict[str, Any],
    manifest: dict[str, Any] | Path | str | None = None,
    evidence_root: Path | str | None = None,
    manifest_root: Path | str | None = None,
) -> None:
    """Validate one end-to-end result and all of its semantic joins."""

    if not isinstance(result, dict):
        fail("RESULT_INVALID", "top-level result must be an object")
    schema_validate(result, "end-to-end-result.schema.json")
    root = Path(evidence_root or ROOT).resolve()
    manifest_evidence_root = Path(manifest_root or root).resolve()
    external_manifest = _load_manifest(manifest)
    if external_manifest is None:
        manifest_path = manifest_evidence_root / relative_path(result["manifest"]["path"], "manifest.path")
        external_manifest = _load_manifest(manifest_path)
    _check_join(result, external_manifest)
    check_evidence([result["manifest"]["path"]], "manifest.path", manifest_evidence_root)
    for group_name, group in (("feature_results", result["feature_results"]), ("integration_results", result["integration_results"])):
        for key, entry in group.items():
            check_status_entry(entry, f"{group_name}.{key}", root)
    for key, score in result["gui_scores"].items():
        check_evidence(score["evidence"], f"gui_scores.{key}.evidence", root)
        if score["score"] is None and not nonempty(score["reason"]):
            fail("GUI_SCORE_REASON_REQUIRED", f"gui_scores.{key} is unassessed without a reason")
        if score["score"] is not None and not score["evidence"]:
            fail("EVIDENCE_REQUIRED", f"gui_scores.{key} has a score but no evidence")
    _check_provider_matrix(result, root)
    for key in ("build", "host", "transport", "hardware"):
        check_status_entry(result[key], key, root)
    if result["transport"]["status"] == "not_run" and result["transport"]["choice"] is not None:
        fail("TRANSPORT_CHOICE_WITHOUT_VALIDATION", "not_run transport must not select a transport")
    _check_telemetry(result, root)
    _check_core_results(result, root)
    _check_f9_details(result, root)
    _check_product_pass(result)


def validate_fixture_file(path: Path, reference_time: str | datetime | None = None) -> None:
    value = load_json(path)
    if isinstance(value, list):
        if len(value) < 3 or not all(isinstance(entry, dict) for entry in value):
            fail("FIXTURE_INVALID", f"{path} multi-provider input must contain at least three snapshots")
        providers = {entry.get("provider_id") for entry in value}
        if not {"openai", "anthropic", "google"}.issubset(providers):
            fail("FIXTURE_INVALID", f"{path} must include OpenAI, Anthropic, and Google snapshots")
        for entry in value:
            validate_snapshot(entry, reference_time=reference_time)
        return
    if not isinstance(value, dict):
        fail("FIXTURE_INVALID", f"{path} must contain one UsageSnapshot object or a snapshot array")
    validate_snapshot(value, reference_time=reference_time)


def validate_fixture_matrix(matrix_path: Path | str | None = None) -> None:
    """Check every fixture against its machine-readable expected outcome."""

    path = Path(matrix_path or ROOT / "experiments" / "fixtures" / "provider-fixture-matrix.json")
    matrix = load_json(path)
    schema_validate(matrix, "provider-fixture-matrix.schema.json")
    if not isinstance(matrix, dict) or not isinstance(matrix.get("fixtures"), list):
        fail("FIXTURE_MATRIX_INVALID", f"{path} must contain a fixtures array")
    reference = matrix.get("reference_time")
    seen_paths: set[str] = set()
    for index, entry in enumerate(matrix["fixtures"]):
        where = f"fixtures[{index}]"
        if not isinstance(entry, dict) or not nonempty(entry.get("path")):
            fail("FIXTURE_MATRIX_INVALID", f"{where}.path is required")
        expected = entry.get("expected")
        expected_code = entry.get("error_code")
        if expected not in {"valid", "invalid"}:
            fail("FIXTURE_MATRIX_INVALID", f"{where}.expected must be valid or invalid")
        if entry["path"] in seen_paths:
            fail("FIXTURE_MATRIX_INVALID", f"{where}.path is duplicated: {entry['path']}")
        seen_paths.add(entry["path"])
        if expected == "invalid" and not nonempty(expected_code):
            fail("FIXTURE_MATRIX_INVALID", f"{where}.error_code is required for invalid fixtures")
        fixture_path = (path.parent / relative_path(entry["path"], f"{where}.path")).resolve()
        if not fixture_path.is_file():
            fail("FILE_NOT_FOUND", f"{where} fixture does not exist: {entry['path']}")
        try:
            validate_fixture_file(fixture_path, reference_time=reference)
        except ValidationError as error:
            if expected != "invalid" or expected_code != error.code:
                fail("FIXTURE_EXPECTATION_MISMATCH", f"{where} expected {expected}/{expected_code}, got {error.code}")
        else:
            if expected != "valid":
                fail("FIXTURE_EXPECTATION_MISMATCH", f"{where} expected an invalid fixture")
            fixture_value = load_json(fixture_path)
            actual = fixture_value.get("error_code") if isinstance(fixture_value, dict) else None
            if expected_code != actual:
                fail("FIXTURE_EXPECTATION_MISMATCH", f"{where} expected error_code {expected_code!r}, got {actual!r}")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, default=EXAMPLES / "end-to-end-result.example.json")
    parser.add_argument("--manifest", type=Path, help="external manifest identity JSON (defaults to result.manifest.path)")
    parser.add_argument("--evidence-root", type=Path, default=ROOT)
    parser.add_argument("--fixture", action="append", type=Path, help="validate a provider snapshot")
    parser.add_argument("--matrix", type=Path, help="validate the machine-readable provider fixture matrix")
    parser.add_argument("--reference-time", help="RFC3339 reference time for fixture freshness checks")
    args = parser.parse_args()
    try:
        result = load_json(args.result)
        validate_result(result, manifest=args.manifest, evidence_root=args.evidence_root)
        for fixture in args.fixture or []:
            validate_fixture_file(fixture, reference_time=args.reference_time)
        if args.matrix is not None:
            validate_fixture_matrix(args.matrix)
    except ValidationError as exc:
        print(f"INVALID [{exc.code}]: {exc.message}", file=sys.stderr)
        return 1
    print(f"VALID: {args.result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
