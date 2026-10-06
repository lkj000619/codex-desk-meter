"""Credential-free fixture collection, normalization, and cdm/1 framing."""

from __future__ import annotations

import copy
import json
import math
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "cdm/1"
MAX_FRAME_BYTES = 65_536
STALE_AFTER_SECONDS = 300


class CollectionError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise CollectionError("TIMESTAMP_INVALID", f"{field} must be an RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CollectionError("TIMESTAMP_INVALID", f"{field} is invalid: {value!r}") from exc
    if parsed.tzinfo is None:
        raise CollectionError("TIMESTAMP_INVALID", f"{field} needs an explicit timezone")
    return parsed.astimezone(timezone.utc)


def _require_number(value: Any, field: str, nullable: bool, maximum: float | None = None) -> None:
    if value is None and nullable:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise CollectionError("VALUE_INVALID", f"{field} must be a nonnegative number or null")
    if maximum is not None and value > maximum:
        raise CollectionError("PERCENT_INVALID", f"{field} is outside [0, {maximum}]")


def validate_snapshot(snapshot: dict[str, Any], reference_time: datetime | None = None) -> None:
    required = {
        "schema_version", "snapshot_id", "provider_id", "agent_id", "host_id", "model_id",
        "account_profile_id", "source_kind", "metric_kind", "unit", "status", "observed_at",
        "windows", "stale", "last_good_at", "error_code", "error_reason",
    }
    if set(snapshot) != required or snapshot.get("schema_version") != 1:
        raise CollectionError("SNAPSHOT_SCHEMA_INVALID", "snapshot keys or schema_version do not match UsageSnapshot")
    status = snapshot["status"]
    if status not in {"available", "unavailable", "unsupported", "unauthorized", "error", "stale"}:
        raise CollectionError("SNAPSHOT_SCHEMA_INVALID", "unknown provider status")
    if not isinstance(snapshot["windows"], list) or not isinstance(snapshot["stale"], bool):
        raise CollectionError("SNAPSHOT_SCHEMA_INVALID", "windows must be an array and stale a boolean")
    observed = parse_time(snapshot["observed_at"], "observed_at") if snapshot["observed_at"] is not None else None
    last_good = parse_time(snapshot["last_good_at"], "last_good_at") if snapshot["last_good_at"] is not None else None
    if observed and last_good and last_good > observed:
        raise CollectionError("TIMESTAMP_ORDER", "last_good_at is after observed_at")
    if status == "available" and (snapshot["stale"] or snapshot["error_code"] is not None):
        raise CollectionError("STATUS_STALE_MISMATCH", "available data cannot carry stale/error state")
    if status == "stale" and (not snapshot["stale"] or last_good is None):
        raise CollectionError("LAST_GOOD_REQUIRED", "stale data needs stale=true and last_good_at")
    if status in {"unavailable", "unsupported", "unauthorized", "error", "stale"}:
        if not snapshot["error_code"] or not snapshot["error_reason"]:
            raise CollectionError("ERROR_REASON_REQUIRED", f"{status} data needs error_code and error_reason")
    if observed is not None:
        age = ((reference_time or utc_now()).astimezone(timezone.utc) - observed).total_seconds()
        if age < 0:
            raise CollectionError("FUTURE_TIMESTAMP", "observed_at is after the collector reference time")
        if status == "available" and age >= STALE_AFTER_SECONDS:
            raise CollectionError("STALE_THRESHOLD_EXCEEDED", "available snapshot is at least 300 seconds old")
        if snapshot["stale"] and age < STALE_AFTER_SECONDS:
            raise CollectionError("STALE_THRESHOLD_NOT_REACHED", "stale snapshot is younger than 300 seconds")
    seen: set[str] = set()
    for window in snapshot["windows"]:
        expected = {"window_id", "label", "used_units", "remaining_units", "limit_units", "unit", "percent_used", "percent_remaining", "resets_at"}
        allowed = expected | {"reset_status"}
        if not isinstance(window, dict) or not expected.issubset(window) or not set(window).issubset(allowed):
            raise CollectionError("WINDOW_SCHEMA_INVALID", "quota window keys do not match the contract")
        window_id = window["window_id"]
        if not isinstance(window_id, str) or not window_id or window_id in seen:
            raise CollectionError("DUPLICATE_WINDOW", "window_id is empty or duplicated")
        seen.add(window_id)
        unit = window["unit"]
        if unit not in {"percent", "token", "credit", "unknown"}:
            raise CollectionError("UNIT_INVALID", "unknown window unit")
        absolute = [window[key] for key in ("used_units", "remaining_units", "limit_units")]
        for key, value in zip(("used_units", "remaining_units", "limit_units"), absolute):
            _require_number(value, key, nullable=True)
        if unit == "percent" and any(value is not None for value in absolute):
            raise CollectionError("UNIT_VALUE_MISMATCH", "percent window contains absolute units")
        if unit in {"token", "credit"} and any(value is None for value in absolute):
            raise CollectionError("ABSOLUTE_VALUE_MISSING", f"{unit} window needs all absolute values")
        if unit == "unknown" and any(value is not None for value in absolute):
            raise CollectionError("UNIT_VALUE_MISMATCH", "unknown unit contains absolute values")
        if all(value is not None for value in absolute) and abs(absolute[0] + absolute[1] - absolute[2]) > 0.01:
            raise CollectionError("ABSOLUTE_BALANCE_MISMATCH", "used plus remaining differs from limit")
        used, remaining = window["percent_used"], window["percent_remaining"]
        _require_number(used, "percent_used", nullable=True, maximum=100)
        _require_number(remaining, "percent_remaining", nullable=True, maximum=100)
        if (used is None) != (remaining is None):
            raise CollectionError("PERCENTAGE_INVALID", "percentage values must both be null or present")
        if used is not None and abs(used + remaining - 100) > 0.01:
            raise CollectionError("PERCENTAGE_INCONSISTENT", "used and remaining percentages must sum to 100")
        if window["resets_at"] is not None:
            parse_time(window["resets_at"], "resets_at")


def normalize_legacy_usage(body: dict[str, Any], snapshot_id: str = "fixture-personal-usage",
                           reference_time: datetime | None = None) -> dict[str, Any]:
    captured_at = body.get("captured_at")
    if captured_at is None:
        raise CollectionError("CAPTURE_TIME_MISSING", "fixture captured_at is null or missing")
    windows = []
    for window in body.get("windows", []):
        windows.append({
            "window_id": window["id"], "label": window["label"],
            "used_units": None, "remaining_units": None, "limit_units": None,
            "unit": "percent", "percent_used": window["percent_used"],
            "percent_remaining": window["percent_remaining"], "resets_at": window.get("resets_at"),
        })
    observed = parse_time(captured_at, "captured_at")
    is_stale = ((reference_time or utc_now()).astimezone(timezone.utc) - observed).total_seconds() >= STALE_AFTER_SECONDS
    result = {
        "schema_version": 1, "snapshot_id": snapshot_id, "provider_id": "openai",
        "agent_id": "codex-cli", "host_id": "terminal", "model_id": "codex-fixture",
        "account_profile_id": "synthetic-example", "source_kind": "fixture",
        "metric_kind": "quota_window", "unit": "percent",
        "status": "stale" if is_stale else "available", "observed_at": captured_at,
        "windows": windows, "stale": is_stale, "last_good_at": captured_at,
        "error_code": "SOURCE_STALE" if is_stale else None,
        "error_reason": "Source capture is at least 300 seconds old" if is_stale else None,
    }
    validate_snapshot(result, reference_time)
    return result


def normalize_global_reset(body: dict[str, Any], reference_time: datetime | None = None) -> dict[str, Any]:
    source = body.get("source", body.get("provider"))
    captured_at = body.get("captured_at", body.get("fetched_at"))
    if not isinstance(captured_at, str):
        raise CollectionError("CAPTURE_TIME_MISSING", "global reset captured_at is null or missing")
    parse_time(captured_at, "captured_at")
    latest = body.get("latest_reset_at", body.get("last_reset_at"))
    if latest is not None:
        parse_time(latest, "latest_reset_at")
    for name in ("forecast_24h_percent", "forecast_48h_percent"):
        _require_number(body.get(name), name, nullable=True, maximum=100)
    if not isinstance(source, str) or not source:
        raise CollectionError("GLOBAL_RESET_INVALID", "global source is missing")
    reference = (reference_time or utc_now()).astimezone(timezone.utc)
    if parse_time(captured_at, "captured_at") > reference:
        raise CollectionError("FUTURE_TIMESTAMP", "captured_at is after the normalization reference")
    stale = bool(body.get("stale", False)) or (reference - parse_time(captured_at, "captured_at")).total_seconds() >= STALE_AFTER_SECONDS
    error_code = body.get("error_code") or ("SOURCE_STALE" if stale else None)
    result = {
        "schema_version": 1, "source": source, "captured_at": captured_at,
        "latest_reset_at": latest, "forecast_24h_percent": body.get("forecast_24h_percent"),
        "forecast_48h_percent": body.get("forecast_48h_percent"),
        "forecast_is_schedule": False, "stale": stale,
        "error_code": error_code,
    }
    return result


@dataclass
class CollectionResult:
    usage: list[dict[str, Any]] = field(default_factory=list)
    global_resets: list[dict[str, Any]] = field(default_factory=list)
    failures: list[dict[str, str]] = field(default_factory=list)

    @property
    def payload(self) -> dict[str, Any]:
        return {"usage": copy.deepcopy(self.usage), "global_resets": copy.deepcopy(self.global_resets)}


class FixtureCollector:
    """Loads only configured repository fixtures and isolates each adapter error."""

    def __init__(self, registry: Path | str | None = None):
        self.registry = Path(registry or ROOT / "pc" / "fixture-set.json").resolve()
        if not self.registry.is_relative_to(ROOT):
            raise CollectionError("REGISTRY_PATH_UNSAFE", "fixture registry must stay in the checkout")
        self.last_good: dict[str, list[dict[str, Any]]] = {}
        self.last_good_global: dict[str, dict[str, Any]] = {}

    def _load(self, relative: str) -> Any:
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT):
            raise CollectionError("FIXTURE_PATH_UNSAFE", "fixture path escapes the checkout")
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CollectionError("FIXTURE_LOAD_FAILED", f"{relative}: {exc}") from exc

    def collect(self, reference_time: datetime | None = None) -> CollectionResult:
        reference = (reference_time or utc_now()).astimezone(timezone.utc)
        result = CollectionResult()
        try:
            registry = json.loads(self.registry.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CollectionError("REGISTRY_LOAD_FAILED", str(exc)) from exc
        for relative in registry.get("provider_fixtures", []):
            adapter_id = Path(relative).stem
            try:
                raw = self._load(relative)
                entries = raw if isinstance(raw, list) else [raw]
                normalized = []
                for entry in entries:
                    if not isinstance(entry, dict):
                        raise CollectionError("SNAPSHOT_SCHEMA_INVALID", "provider fixture item is not an object")
                    snapshot = normalize_legacy_usage(entry, f"{adapter_id}-legacy", reference) if "status" not in entry else copy.deepcopy(entry)
                    observed_value = snapshot.get("observed_at")
                    if observed_value is not None:
                        observed = parse_time(observed_value, "observed_at")
                        if observed > reference:
                            raise CollectionError("FUTURE_TIMESTAMP", "observed_at is after collection reference")
                        age = (reference - observed).total_seconds()
                        if snapshot.get("status") == "available" and age >= STALE_AFTER_SECONDS:
                            snapshot.update(status="stale", stale=True, error_code="SOURCE_STALE",
                                            error_reason="Source capture is at least 300 seconds old",
                                            last_good_at=snapshot.get("last_good_at") or observed_value)
                    validate_snapshot(snapshot, reference)
                    normalized.append(snapshot)
                self.last_good[adapter_id] = copy.deepcopy(normalized)
                result.usage.extend(normalized)
            except (CollectionError, KeyError, TypeError, ValueError) as exc:
                code = exc.code if isinstance(exc, CollectionError) else "ADAPTER_FAILURE"
                result.failures.append({"adapter_id": adapter_id, "code": code, "message": str(exc)})
                prior_entries = self.last_good.get(adapter_id)
                if prior_entries:
                    for prior in prior_entries:
                        failed = copy.deepcopy(prior)
                        failed.update(status="error", stale=bool(prior.get("stale")), error_code=code,
                                      error_reason="Adapter failed; showing its last good source values",
                                      last_good_at=prior.get("last_good_at") or prior.get("observed_at"))
                        result.usage.append(failed)
        for relative in registry.get("global_reset_fixtures", []):
            adapter_id = Path(relative).stem
            try:
                reset = normalize_global_reset(self._load(relative), reference)
                if parse_time(reset["captured_at"], "captured_at") > reference:
                    raise CollectionError("FUTURE_TIMESTAMP", "global captured_at is after collection reference")
                self.last_good_global[adapter_id] = copy.deepcopy(reset)
                result.global_resets.append(reset)
            except (CollectionError, KeyError, TypeError, ValueError) as exc:
                code = exc.code if isinstance(exc, CollectionError) else "ADAPTER_FAILURE"
                result.failures.append({"adapter_id": adapter_id, "code": code, "message": str(exc)})
                prior = self.last_good_global.get(adapter_id)
                if prior:
                    failed = copy.deepcopy(prior)
                    failed.update(stale=True, error_code=code)
                    result.global_resets.append(failed)
        return result


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def crc32_hex(value: bytes) -> str:
    return f"{zlib.crc32(value) & 0xFFFFFFFF:08X}"


def build_frame(payload: dict[str, Any], sequence: int, sent_at: str) -> dict[str, Any]:
    if isinstance(sequence, bool) or not isinstance(sequence, int) or not 0 <= sequence <= 0xFFFFFFFF:
        raise CollectionError("SEQUENCE_INVALID", "sequence must be uint32")
    reference = parse_time(sent_at, "sent_at")
    if not isinstance(payload.get("usage"), list) or not isinstance(payload.get("global_resets"), list):
        raise CollectionError("PAYLOAD_INVALID", "payload needs usage and global_resets arrays")
    for snapshot in payload["usage"]:
        validate_snapshot(snapshot, reference)
    for reset in payload["global_resets"]:
        required = {"schema_version", "source", "captured_at", "latest_reset_at", "forecast_24h_percent",
                    "forecast_48h_percent", "forecast_is_schedule", "stale", "error_code"}
        if not isinstance(reset, dict) or set(reset) != required or reset["schema_version"] != 1 or reset["forecast_is_schedule"] is not False:
            raise CollectionError("GLOBAL_RESET_INVALID", "global reset fields do not match cdm/1")
        captured = parse_time(reset["captured_at"], "captured_at")
        if captured > reference:
            raise CollectionError("FUTURE_TIMESTAMP", "global captured_at is after sent_at")
        if reset["latest_reset_at"] is not None:
            parse_time(reset["latest_reset_at"], "latest_reset_at")
        for field_name in ("forecast_24h_percent", "forecast_48h_percent"):
            _require_number(reset[field_name], field_name, nullable=True, maximum=100)
        if not isinstance(reset["source"], str) or not reset["source"] or not isinstance(reset["stale"], bool):
            raise CollectionError("GLOBAL_RESET_INVALID", "global source and stale state are invalid")
    unsigned = {"protocol": PROTOCOL, "sequence": sequence, "sent_at": sent_at, "payload": payload}
    return {**unsigned, "integrity": {"algorithm": "crc32", "value": crc32_hex(canonical_json(unsigned))}}


def encode_frame(frame: dict[str, Any]) -> bytes:
    unsigned = {key: value for key, value in frame.items() if key != "integrity"}
    expected = crc32_hex(canonical_json(unsigned))
    if frame.get("integrity") != {"algorithm": "crc32", "value": expected}:
        raise CollectionError("CRC_MISMATCH", "frame integrity does not match canonical envelope")
    line = canonical_json(frame) + b"\n"
    if len(line) > MAX_FRAME_BYTES:
        raise CollectionError("FRAME_OVERSIZED", f"frame exceeds {MAX_FRAME_BYTES} bytes")
    return line
