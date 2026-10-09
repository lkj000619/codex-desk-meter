"""Canonical JSON encoding, CRC32 checksum, schema validation, and frame formatting."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "experiments" / "schema"
PROTOCOL = "cdm/1"
MAX_SEQUENCE = 2**32 - 1
SEQUENCE_HALF_RANGE = 2**31
MAX_FRAME_BYTES = 64 * 1024
STALE_THRESHOLD_SECONDS = 300
DEFAULT_SENT_AT = "2026-09-10T00:00:00Z"
IDENTITY_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class FrameError(ValueError):
    """Protocol / schema / frame error."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def fail(code: str, message: str) -> None:
    raise FrameError(code, message)


def canonical_json(value: Any) -> bytes:
    """Return the exact UTF-8 bytes covered by the protocol checksum."""
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        fail("CANONICAL_JSON_INVALID", str(error))
    raise AssertionError("unreachable")


def crc32_hex(value: bytes) -> str:
    """Return 8-character uppercase hex CRC32."""
    return f"{zlib.crc32(value) & 0xFFFFFFFF:08X}"


def sha256_hex(value: bytes) -> str:
    """Return lowercase hex SHA-256."""
    return hashlib.sha256(value).hexdigest()


def load_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        fail("FILE_NOT_FOUND", str(path))
    except json.JSONDecodeError as error:
        fail("INVALID_JSON", f"{path}: {error}")
    raise AssertionError("unreachable")


def schema_validate(value: Any, schema_filename: str, error_code: str = "SCHEMA_INVALID") -> None:
    """Validate JSON object against schema in experiments/schema."""
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        fail("SCHEMA_ENGINE_UNAVAILABLE", "jsonschema package is required")

    schema_path = SCHEMA_DIR / schema_filename
    schema = load_json_file(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        errors = sorted(validator.iter_errors(value), key=lambda err: list(err.absolute_path))
    except (TypeError, ValueError) as error:
        fail("SCHEMA_ENGINE_ERROR", f"{schema_filename}: {error}")

    if errors:
        first_err = errors[0]
        location = ".".join(str(p) for p in first_err.absolute_path) or "$"
        fail(error_code, f"{schema_filename}:{location}: {first_err.message}")


def parse_rfc3339(ts_str: str) -> datetime:
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            fail("TIMESTAMP_NO_TZ", f"timestamp {ts_str} missing timezone")
        return dt.astimezone(timezone.utc)
    except Exception as exc:
        fail("INVALID_TIMESTAMP_FORMAT", f"{ts_str}: {exc}")
    raise AssertionError("unreachable")


def semantic_validate_snapshot(snapshot: dict[str, Any], reference_time: str | None = None) -> None:
    """Strict semantic validation extending JSON schema constraints."""
    schema_validate(snapshot, "usage-snapshot.schema.json", "SNAPSHOT_SCHEMA_INVALID")

    # Time checks vs reference_time
    ref_dt = None
    if reference_time:
        ref_dt = parse_rfc3339(reference_time)

    obs_str = snapshot.get("observed_at")
    if obs_str and ref_dt:
        obs_dt = parse_rfc3339(obs_str)
        if obs_dt > ref_dt:
            fail("SEMANTIC_FUTURE_TIMESTAMP", f"observed_at {obs_str} is in future of reference {reference_time}")

    lg_str = snapshot.get("last_good_at")
    if lg_str and ref_dt:
        lg_dt = parse_rfc3339(lg_str)
        if lg_dt > ref_dt:
            fail("SEMANTIC_FUTURE_TIMESTAMP", f"last_good_at {lg_str} is in future of reference {reference_time}")

    status = snapshot.get("status")
    # P2 rule: available source must have non-null agent_id and host_id
    if status == "available":
        if snapshot.get("agent_id") is None:
            fail("SEMANTIC_AVAILABLE_AGENT_REQUIRED", "agent_id must not be null when status is available")
        if snapshot.get("host_id") is None:
            fail("SEMANTIC_AVAILABLE_HOST_REQUIRED", "host_id must not be null when status is available")

    metric_kind = snapshot.get("metric_kind")
    windows = snapshot.get("windows", [])
    if metric_kind == "session_telemetry":
        # Required unique session channels
        required_channels = {"input", "output", "cached_input", "reasoning_output", "source_total", "normalized_total"}
        seen_channels = set()
        channel_units = {}

        for win in windows:
            wid = win.get("window_id")
            if wid not in required_channels:
                fail("SEMANTIC_UNKNOWN_SESSION_CHANNEL", f"unrecognized session telemetry channel {wid!r}")
            if wid in seen_channels:
                fail("SEMANTIC_DUPLICATE_SESSION_CHANNEL", f"duplicate session telemetry channel {wid!r}")
            seen_channels.add(wid)

            units = win.get("used_units")
            channel_units[wid] = units

            for null_field in ("remaining_units", "limit_units", "percent_used", "percent_remaining", "resets_at"):
                if win.get(null_field) is not None:
                    fail("SEMANTIC_SESSION_FIELD_NOT_NULL", f"session telemetry window {wid} must have {null_field} null")

        # Invariant checks for session channels
        if seen_channels == required_channels:
            in_t = channel_units.get("input") or 0
            out_t = channel_units.get("output") or 0
            cached_t = channel_units.get("cached_input")
            reason_t = channel_units.get("reasoning_output")
            norm_t = channel_units.get("normalized_total") or 0

            if cached_t is not None and cached_t > in_t:
                fail("SEMANTIC_CACHE_EXCEEDS_INPUT", f"cached_input ({cached_t}) > input ({in_t})")
            if reason_t is not None and reason_t > out_t:
                fail("SEMANTIC_REASONING_EXCEEDS_OUTPUT", f"reasoning_output ({reason_t}) > output ({out_t})")
            if norm_t != (in_t + out_t):
                fail("SEMANTIC_NORMALIZED_TOTAL_MISMATCH", f"normalized_total ({norm_t}) != input + output ({in_t + out_t})")

    elif metric_kind == "quota_window":
        for win in windows:
            # Check percent relations if both present
            p_used = win.get("percent_used")
            p_rem = win.get("percent_remaining")
            if p_used is not None and p_rem is not None:
                # Sum should be approximately 100
                if abs((p_used + p_rem) - 100.0) > 0.05:
                    fail("SEMANTIC_PERCENT_SUM_MISMATCH", f"percent_used ({p_used}) + percent_remaining ({p_rem}) != 100")


def unsigned_frame(frame: dict[str, Any]) -> dict[str, Any]:
    unsigned = copy.deepcopy(frame)
    unsigned.pop("integrity", None)
    return unsigned


def check_integrity(frame: dict[str, Any]) -> None:
    if "integrity" not in frame or "value" not in frame["integrity"]:
        fail("INTEGRITY_MISSING", "frame integrity value is missing")
    actual = frame["integrity"]["value"]
    expected = crc32_hex(canonical_json(unsigned_frame(frame)))
    if actual != expected:
        fail("CRC_MISMATCH", f"expected {expected}, got {actual}")


def validate_envelope_time_invariant(payload: dict[str, Any], sent_at: str) -> None:
    """Validate that observations, last goods, and resets do not violate frame envelope time."""
    sent_dt = parse_rfc3339(sent_at)
    usage = payload.get("usage", [])
    for snapshot in usage:
        obs_str = snapshot.get("observed_at")
        if obs_str:
            obs_dt = parse_rfc3339(obs_str)
            if obs_dt > sent_dt:
                fail("SNAPSHOT_INVALID", f"snapshot {snapshot.get('snapshot_id')} observed_at {obs_str} is in future of sent_at {sent_at}")
        lg_str = snapshot.get("last_good_at")
        if lg_str:
            lg_dt = parse_rfc3339(lg_str)
            if lg_dt > sent_dt:
                fail("SNAPSHOT_INVALID", f"snapshot {snapshot.get('snapshot_id')} last_good_at {lg_str} is in future of sent_at {sent_at}")
        for win in snapshot.get("windows", []):
            rst_str = win.get("resets_at")
            rs = win.get("reset_status")
            if rst_str and rs:
                rst_dt = parse_rfc3339(rst_str)
                if rs == "scheduled" and rst_dt <= sent_dt:
                    fail("SNAPSHOT_INVALID", f"scheduled window {win.get('window_id')} resets_at {rst_str} <= sent_at {sent_at}")
                elif rs == "expired" and rst_dt > sent_dt:
                    fail("SNAPSHOT_INVALID", f"expired window {win.get('window_id')} resets_at {rst_str} > sent_at {sent_at}")

    global_resets = payload.get("global_resets", [])
    for reset in global_resets:
        cap_str = reset.get("captured_at")
        if cap_str:
            cap_dt = parse_rfc3339(cap_str)
            if cap_dt > sent_dt:
                fail("GLOBAL_INVALID", f"global reset captured_at {cap_str} is in future of sent_at {sent_at}")
        latest_reset_str = reset.get("latest_reset_at")
        if latest_reset_str:
            lr_dt = parse_rfc3339(latest_reset_str)
            if lr_dt > sent_dt:
                fail("GLOBAL_INVALID", f"global reset latest_reset_at {latest_reset_str} is in future of sent_at {sent_at}")


def build_frame(payload: dict[str, Any], sequence: int, sent_at: str, reference_time: str | None = None) -> dict[str, Any]:
    """Construct, validate and checksum a cdm/1 frame."""
    if not isinstance(payload, dict):
        fail("PAYLOAD_INVALID", "payload must be an object")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or not (0 <= sequence <= MAX_SEQUENCE):
        fail("SEQUENCE_INVALID", f"sequence must be in [0, {MAX_SEQUENCE}]")
    if not isinstance(sent_at, str):
        fail("TIMESTAMP_INVALID", "sent_at must be RFC3339 string")

    usage = payload.get("usage")
    global_resets = payload.get("global_resets")
    if not isinstance(usage, list) or not isinstance(global_resets, list):
        fail("PAYLOAD_INVALID", "payload requires usage and global_resets arrays")

    validate_envelope_time_invariant(payload, sent_at)

    for snapshot in usage:
        semantic_validate_snapshot(snapshot, reference_time=reference_time)

    for reset in global_resets:
        schema_validate(
            {
                "protocol": PROTOCOL,
                "sequence": 0,
                "sent_at": DEFAULT_SENT_AT,
                "payload": {"usage": [], "global_resets": [reset]},
                "integrity": {"algorithm": "crc32", "value": "00000000"},
            },
            "cdm-frame.schema.json",
            "FRAME_SCHEMA_INVALID",
        )

    frame = {
        "protocol": PROTOCOL,
        "sequence": sequence,
        "sent_at": sent_at,
        "payload": copy.deepcopy(payload),
        "integrity": {"algorithm": "crc32", "value": "00000000"},
    }

    schema_validate(frame, "cdm-frame.schema.json", "FRAME_SCHEMA_INVALID")
    frame["integrity"]["value"] = crc32_hex(canonical_json(unsigned_frame(frame)))
    schema_validate(frame, "cdm-frame.schema.json", "FRAME_SCHEMA_INVALID")
    return frame


def encode_frame(frame: dict[str, Any], reference_time: str | None = None) -> bytes:
    """Encode a validated frame into canonical UTF-8 bytes with single trailing LF, max 64KB."""
    schema_validate(frame, "cdm-frame.schema.json", "FRAME_SCHEMA_INVALID")
    for s in frame["payload"]["usage"]:
        semantic_validate_snapshot(s, reference_time=reference_time)
    check_integrity(frame)

    line = canonical_json(frame) + b"\n"
    if len(line) > MAX_FRAME_BYTES:
        fail("FRAME_OVERSIZED", f"encoded frame is {len(line)} bytes, exceeds {MAX_FRAME_BYTES}")
    return line


def decode_frame(line: bytes | bytearray | str, reference_time: str | None = None) -> dict[str, Any]:
    """Decode and strictly validate raw frame line."""
    if isinstance(line, str):
        line = line.encode("utf-8")
    raw = bytes(line)
    if len(raw) > MAX_FRAME_BYTES:
        fail("FRAME_OVERSIZED", f"encoded frame is {len(raw)} bytes, exceeds {MAX_FRAME_BYTES}")
    if not raw.endswith(b"\n"):
        fail("FRAME_TRUNCATED", "frame line must end with newline LF")
    if raw.count(b"\n") != 1:
        fail("FRAME_NEWLINE_INVALID", "frame line must contain exactly one newline LF")

    try:
        text = raw[:-1].decode("utf-8")
    except UnicodeDecodeError as err:
        fail("INVALID_UTF8", str(err))

    try:
        frame = json.loads(text)
    except json.JSONDecodeError as err:
        fail("MALFORMED_JSON", str(err))

    if not isinstance(frame, dict):
        fail("FRAME_SCHEMA_INVALID", "frame must be a JSON object")
    if frame.get("protocol") != PROTOCOL:
        fail("UNSUPPORTED_VERSION", f"unsupported protocol {frame.get('protocol')!r}")

    schema_validate(frame, "cdm-frame.schema.json", "FRAME_SCHEMA_INVALID")
    validate_envelope_time_invariant(frame["payload"], frame["sent_at"])
    for s in frame["payload"]["usage"]:
        semantic_validate_snapshot(s, reference_time=reference_time)
    check_integrity(frame)

    if raw[:-1] != canonical_json(frame):
        fail("NON_CANONICAL_FRAME", "frame bytes do not match canonical JSON format")

    return frame


def sequence_is_newer(candidate: int, current: int) -> bool:
    """True iff 0 < (candidate - current) mod 2^32 < 2^31."""
    if not isinstance(candidate, int) or isinstance(candidate, bool) or not (0 <= candidate <= MAX_SEQUENCE):
        fail("SEQUENCE_INVALID", f"candidate sequence must be uint32: {candidate}")
    if not isinstance(current, int) or isinstance(current, bool) or not (0 <= current <= MAX_SEQUENCE):
        fail("SEQUENCE_INVALID", f"current sequence must be uint32: {current}")
    distance = (candidate - current) & MAX_SEQUENCE
    return 0 < distance < SEQUENCE_HALF_RANGE
