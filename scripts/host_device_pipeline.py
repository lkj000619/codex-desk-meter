"""Offline host-to-device pipeline primitives for the maintainer pre-experiment.

This module deliberately stops at a deterministic host simulation boundary.  It reads
repository fixtures, emits a versioned JSON/CRC frame, writes only to an injected
loopback serial object in tests, and models the receiver state that a later firmware
implementation must conform to.  It never contacts a provider and never opens a
serial port unless a caller explicitly invokes :meth:`SerialBridge.send`.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "experiments" / "schema"
PROVIDER_FIXTURE_ROOT = ROOT / "experiments" / "fixtures" / "providers"
PROTOCOL = "cdm/1"
MAX_SEQUENCE = 2**32 - 1
SEQUENCE_HALF_RANGE = 2**31
MAX_FRAME_BYTES = 64 * 1024
STALE_THRESHOLD_SECONDS = 300
DEFAULT_SENT_AT = "2026-09-10T00:00:00Z"
IDENTITY_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class PipelineError(ValueError):
    """Stable error returned at an offline pipeline seam."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class FixtureAdapter(Protocol):
    """Narrow extension seam for a later owner-approved adapter."""

    adapter_id: str
    provider_id: str
    agent_id: str | None
    host_id: str | None

    def collect(self) -> list[dict[str, Any]]:
        ...


def _fail(code: str, message: str) -> None:
    raise PipelineError(code, message)


def _display_path(path: Path) -> str:
    """Return a portable path without leaking an absolute user path."""

    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return "<outside-repository>"


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        _fail("FIXTURE_NOT_FOUND", _display_path(path))
    except json.JSONDecodeError as error:
        _fail("FIXTURE_INVALID_JSON", f"{_display_path(path)}: {error}")
    raise AssertionError("unreachable")


def _schema_validate(value: Any, filename: str, code: str) -> None:
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        _fail("SCHEMA_ENGINE_UNAVAILABLE", "install scripts/requirements-benchmark.txt")
    schema = _load_json(SCHEMA_DIR / filename)
    try:
        Draft202012Validator.check_schema(schema)
        errors = sorted(
            Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
            key=lambda error: list(error.absolute_path),
        )
    except (TypeError, ValueError) as error:
        _fail("SCHEMA_ENGINE_ERROR", f"{filename}: {error}")
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        _fail(code, f"{filename}:{location}: {error.message}")


def _parse_timestamp(value: Any, where: str) -> datetime:
    if not isinstance(value, str):
        _fail("TIMESTAMP_INVALID", f"{where} must be RFC3339")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        _fail("TIMESTAMP_INVALID", f"{where} is not RFC3339: {value!r}")
        raise AssertionError from error
    if parsed.tzinfo is None:
        _fail("TIMESTAMP_INVALID", f"{where} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _as_of(value: str | datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = _parse_timestamp(value, "reference_time")
    return parsed.astimezone(timezone.utc)


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
        _fail("CANONICAL_JSON_INVALID", str(error))
    raise AssertionError("unreachable")


def crc32_hex(value: bytes) -> str:
    return f"{zlib.crc32(value) & 0xFFFFFFFF:08X}"


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _validate_snapshot(snapshot: dict[str, Any]) -> None:
    _schema_validate(snapshot, "usage-snapshot.schema.json", "SNAPSHOT_SCHEMA_INVALID")


def _normalize_global_reset(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail("GLOBAL_RESET_INVALID", "global reset input must be an object")
    normalized = {
        "schema_version": 1,
        "source": value.get("source"),
        "captured_at": value.get("captured_at", value.get("fetched_at")),
        "latest_reset_at": value.get("latest_reset_at", value.get("last_reset_at")),
        "forecast_24h_percent": value.get("forecast_24h_percent"),
        "forecast_48h_percent": value.get("forecast_48h_percent"),
        "forecast_is_schedule": value.get("forecast_is_schedule", False),
        "stale": value.get("stale", False),
        "error_code": value.get("error_code"),
    }
    return normalized


def _validate_global_reset(value: dict[str, Any]) -> None:
    frame = {
        "protocol": PROTOCOL,
        "sequence": 0,
        "sent_at": DEFAULT_SENT_AT,
        "payload": {"usage": [], "global_resets": [value]},
        "integrity": {"algorithm": "crc32", "value": "00000000"},
    }
    _schema_validate(frame, "cdm-frame.schema.json", "FRAME_SCHEMA_INVALID")


@dataclass
class CollectionResult:
    snapshots: list[dict[str, Any]]
    global_resets: list[dict[str, Any]]
    failures: list[dict[str, str]] = field(default_factory=list)

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "usage": copy.deepcopy(self.snapshots),
            "global_resets": copy.deepcopy(self.global_resets),
        }


class FixtureFileAdapter:
    """Narrow fixture adapter interface used by the registry."""

    def __init__(self, adapter_id: str, path: Path, fixture_root: Path | None = None):
        self.adapter_id = adapter_id
        self.path = Path(path)
        self.fixture_root = Path(fixture_root or PROVIDER_FIXTURE_ROOT).resolve()
        self.provider_id = adapter_id
        self.agent_id = "fixture"
        self.host_id = "terminal"

    def collect(self) -> list[dict[str, Any]]:
        resolved = self.path.resolve()
        if not resolved.is_relative_to(self.fixture_root):
            _fail("FIXTURE_PATH_UNSAFE", "provider fixture must stay under the repository provider-fixtures directory")
        value = _load_json(resolved)
        entries = value if isinstance(value, list) else [value]
        if not all(isinstance(entry, dict) for entry in entries):
            _fail("FIXTURE_INVALID", f"{_display_path(resolved)} must contain snapshot objects")
        for entry in entries:
            _validate_snapshot(entry)
        return copy.deepcopy(entries)


class GlobalResetFixtureAdapter:
    """Adapter for one independently typed, credential-free reset fixture."""

    def __init__(self, adapter_id: str, path: Path):
        self.adapter_id = adapter_id
        self.path = Path(path)

    def collect(self) -> dict[str, Any]:
        normalized = _normalize_global_reset(_load_json(self.path))
        _validate_global_reset(normalized)
        return normalized


def _error_snapshot(adapter: Any, reference_time: str | datetime | None, code: str, message: str) -> dict[str, Any]:
    observed_at = _as_of(reference_time).isoformat().replace("+00:00", "Z")
    provider_id = getattr(adapter, "provider_id", "unknown-provider")
    agent_id = getattr(adapter, "agent_id", None)
    host_id = getattr(adapter, "host_id", None)
    if not isinstance(provider_id, str) or not IDENTITY_RE.fullmatch(provider_id):
        provider_id = "unknown-provider"
    if not isinstance(agent_id, str) or not IDENTITY_RE.fullmatch(agent_id):
        agent_id = None
    if not isinstance(host_id, str) or not IDENTITY_RE.fullmatch(host_id):
        host_id = None
    raw_snapshot_id = f"fixture-error-{getattr(adapter, 'adapter_id', 'unknown')}"
    snapshot_id = re.sub(r"[^A-Za-z0-9._:-]+", "-", raw_snapshot_id).strip("-") or "fixture-error-unknown"
    return {
        "schema_version": 1,
        "snapshot_id": snapshot_id,
        "provider_id": provider_id,
        "agent_id": agent_id,
        "host_id": host_id,
        "model_id": None,
        "account_profile_id": None,
        "source_kind": "fixture",
        "metric_kind": "quota_window",
        "unit": "unknown",
        "status": "error",
        "observed_at": observed_at,
        "windows": [],
        "stale": False,
        "last_good_at": None,
        "error_code": code,
        "error_reason": message,
    }


class FixtureRegistry:
    """Collect snapshots and reset inputs without aborting on one adapter failure."""

    def __init__(
        self,
        adapters: Iterable[FixtureAdapter],
        global_reset_adapters: Iterable[Any] | None = None,
        reference_time: str | datetime | None = None,
    ):
        self.adapters = list(adapters)
        self.global_reset_adapters = list(global_reset_adapters or [])
        self.reference_time = reference_time

    @classmethod
    def with_defaults(cls, root: Path | str = ROOT, reference_time: str | datetime | None = None) -> "FixtureRegistry":
        root = Path(root)
        provider_root = root / "experiments" / "fixtures" / "providers"
        adapters = [
            FixtureFileAdapter("codex", provider_root / "codex-percent-window.json", provider_root),
            FixtureFileAdapter("claude-code", provider_root / "claude-code-windows.json", provider_root),
            FixtureFileAdapter("gemini-cli", provider_root / "gemini-cli-unsupported.json", provider_root),
            FixtureFileAdapter("orca-claude-code", provider_root / "orca-host-claude-code.json", provider_root),
        ]
        reset_root = root / "experiments" / "fixtures"
        resets = [
            GlobalResetFixtureAdapter("codex-reset-forecast", reset_root / "codex-reset-forecast.json"),
            GlobalResetFixtureAdapter("codex-resets-history", reset_root / "codex-resets-history.json"),
        ]
        return cls(adapters, resets, reference_time=reference_time)

    def collect(self) -> CollectionResult:
        snapshots: list[dict[str, Any]] = []
        global_resets: list[dict[str, Any]] = []
        failures: list[dict[str, str]] = []
        for adapter in self.adapters:
            try:
                entries = adapter.collect()
                if isinstance(entries, dict):
                    entries = [entries]
                for snapshot in entries:
                    _validate_snapshot(snapshot)
                    snapshots.append(copy.deepcopy(snapshot))
            except PipelineError as error:
                failures.append({"adapter_id": adapter.adapter_id, "code": error.code, "message": error.message})
                snapshots.append(_error_snapshot(adapter, self.reference_time, error.code, error.message))
            except Exception as error:  # adapter boundary turns failures into data
                message = str(error)
                failures.append({"adapter_id": adapter.adapter_id, "code": "ADAPTER_FAILURE", "message": message})
                snapshots.append(_error_snapshot(adapter, self.reference_time, "ADAPTER_FAILURE", message))
        for adapter in self.global_reset_adapters:
            try:
                reset = adapter.collect()
                _validate_global_reset(reset)
                global_resets.append(copy.deepcopy(reset))
            except PipelineError as error:
                failures.append({"adapter_id": adapter.adapter_id, "code": error.code, "message": error.message})
                global_resets.append(
                    _normalize_global_reset(
                        {
                            "source": adapter.adapter_id,
                            "captured_at": _as_of(self.reference_time).isoformat().replace("+00:00", "Z"),
                            "error_code": error.code,
                            "stale": True,
                        }
                    )
                )
            except Exception as error:
                message = str(error)
                failures.append({"adapter_id": adapter.adapter_id, "code": "ADAPTER_FAILURE", "message": message})
                global_resets.append(
                    _normalize_global_reset(
                        {
                            "source": adapter.adapter_id,
                            "captured_at": _as_of(self.reference_time).isoformat().replace("+00:00", "Z"),
                            "error_code": "ADAPTER_FAILURE",
                            "stale": True,
                        }
                    )
                )
        return CollectionResult(snapshots, global_resets, failures)


def _unsigned_frame(frame: dict[str, Any]) -> dict[str, Any]:
    unsigned = copy.deepcopy(frame)
    unsigned.pop("integrity", None)
    return unsigned


def _check_integrity(frame: dict[str, Any]) -> None:
    actual = frame["integrity"]["value"]
    expected = crc32_hex(canonical_json(_unsigned_frame(frame)))
    if actual != expected:
        _fail("CRC_MISMATCH", f"expected {expected}, got {actual}")


def build_frame(payload: dict[str, Any], sequence: int, sent_at: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        _fail("PAYLOAD_INVALID", "payload must be an object")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or not 0 <= sequence <= MAX_SEQUENCE:
        _fail("SEQUENCE_INVALID", f"sequence must be in [0, {MAX_SEQUENCE}]")
    if not isinstance(sent_at, str):
        _fail("TIMESTAMP_INVALID", "sent_at must be RFC3339")
    usage = payload.get("usage")
    resets = payload.get("global_resets")
    if not isinstance(usage, list) or not isinstance(resets, list):
        _fail("PAYLOAD_INVALID", "payload requires usage and global_resets arrays")
    for snapshot in usage:
        if not isinstance(snapshot, dict):
            _fail("SNAPSHOT_SCHEMA_INVALID", "payload.usage items must be objects")
        _validate_snapshot(snapshot)
    for reset in resets:
        if not isinstance(reset, dict):
            _fail("FRAME_SCHEMA_INVALID", "payload.global_resets items must be objects")
        _validate_global_reset(reset)
    frame = {
        "protocol": PROTOCOL,
        "sequence": sequence,
        "sent_at": sent_at,
        "payload": copy.deepcopy(payload),
        "integrity": {"algorithm": "crc32", "value": "00000000"},
    }
    _schema_validate(frame, "cdm-frame.schema.json", "FRAME_SCHEMA_INVALID")
    frame["integrity"]["value"] = crc32_hex(canonical_json(_unsigned_frame(frame)))
    _schema_validate(frame, "cdm-frame.schema.json", "FRAME_SCHEMA_INVALID")
    return frame


def encode_frame(frame: dict[str, Any]) -> bytes:
    if not isinstance(frame, dict):
        _fail("FRAME_INVALID", "frame must be an object")
    _schema_validate(frame, "cdm-frame.schema.json", "FRAME_SCHEMA_INVALID")
    for snapshot in frame["payload"]["usage"]:
        _validate_snapshot(snapshot)
    _check_integrity(frame)
    line = canonical_json(frame) + b"\n"
    if len(line) > MAX_FRAME_BYTES:
        _fail("FRAME_OVERSIZED", f"encoded frame exceeds {MAX_FRAME_BYTES} bytes")
    return line


def decode_frame_line(line: bytes | bytearray | str) -> dict[str, Any]:
    if isinstance(line, str):
        line = line.encode("utf-8")
    if not isinstance(line, (bytes, bytearray)):
        _fail("FRAME_INVALID", "frame line must be bytes or text")
    raw = bytes(line)
    if len(raw) > MAX_FRAME_BYTES:
        _fail("FRAME_OVERSIZED", f"encoded frame exceeds {MAX_FRAME_BYTES} bytes")
    if not raw.endswith(b"\n"):
        _fail("FRAME_TRUNCATED", "frame line must end with one newline")
    if raw.count(b"\n") != 1:
        _fail("FRAME_NEWLINE_INVALID", "frame line must contain exactly one newline")
    try:
        text = raw[:-1].decode("utf-8")
    except UnicodeDecodeError as error:
        _fail("INVALID_UTF8", str(error))
    try:
        frame = json.loads(text)
    except json.JSONDecodeError as error:
        _fail("MALFORMED_JSON", str(error))
    if not isinstance(frame, dict):
        _fail("FRAME_SCHEMA_INVALID", "frame must be an object")
    if frame.get("protocol") != PROTOCOL:
        _fail("UNSUPPORTED_VERSION", f"unsupported protocol {frame.get('protocol')!r}")
    _schema_validate(frame, "cdm-frame.schema.json", "FRAME_SCHEMA_INVALID")
    for snapshot in frame["payload"]["usage"]:
        _validate_snapshot(snapshot)
    _check_integrity(frame)
    if raw[:-1] != canonical_json(frame):
        _fail("NON_CANONICAL_FRAME", "frame bytes do not use the required canonical JSON encoding")
    return frame


def sequence_is_newer(candidate: int, current: int) -> bool:
    if (
        isinstance(candidate, bool)
        or isinstance(current, bool)
        or not isinstance(candidate, int)
        or not isinstance(current, int)
        or not 0 <= candidate <= MAX_SEQUENCE
        or not 0 <= current <= MAX_SEQUENCE
    ):
        _fail("SEQUENCE_INVALID", "sequence must fit uint32")
    distance = (candidate - current) & MAX_SEQUENCE
    return 0 < distance < SEQUENCE_HALF_RANGE


@dataclass
class ReceiverState:
    sequence: int | None = None
    payload: dict[str, Any] | None = None
    sent_at: datetime | None = None
    stale: bool = False
    last_good_sha256: str | None = None
    last_error: str | None = None


@dataclass
class ReceiveResult:
    accepted: bool
    code: str | None
    stale: bool
    state: ReceiverState


class ReferenceReceiver:
    """Host-only conformance model for a future ESP32 receiver."""

    def __init__(self):
        self.state = ReceiverState()

    def _update_stale(self, reference_time: str | datetime | None) -> None:
        if self.state.sent_at is None:
            return
        reference = _as_of(reference_time)
        age = (reference - self.state.sent_at).total_seconds()
        self.state.stale = age >= STALE_THRESHOLD_SECONDS

    def advance(self, reference_time: str | datetime | None = None) -> ReceiverState:
        self._update_stale(reference_time)
        return self.state

    def receive(self, line: bytes | bytearray | str, reference_time: str | datetime | None = None) -> ReceiveResult:
        self._update_stale(reference_time)
        try:
            frame = decode_frame_line(line)
            observed = _parse_timestamp(frame["sent_at"], "sent_at")
            reference = _as_of(reference_time)
            if observed > reference:
                _fail("FUTURE_TIMESTAMP", "sent_at is after the reference time")
            sequence = frame["sequence"]
            if self.state.sequence is not None:
                if sequence == self.state.sequence:
                    _fail("DUPLICATE_SEQUENCE", f"sequence {sequence} was already accepted")
                if not sequence_is_newer(sequence, self.state.sequence):
                    _fail("OUT_OF_ORDER_SEQUENCE", f"sequence {sequence} is not newer than {self.state.sequence}")
            self.state.sequence = sequence
            self.state.payload = copy.deepcopy(frame["payload"])
            self.state.sent_at = observed
            self.state.stale = (reference - observed).total_seconds() >= STALE_THRESHOLD_SECONDS
            self.state.last_good_sha256 = sha256(bytes(line, "utf-8") if isinstance(line, str) else bytes(line))
            self.state.last_error = None
            return ReceiveResult(True, None, self.state.stale, self.state)
        except PipelineError as error:
            self.state.last_error = error.code
            return ReceiveResult(False, error.code, self.state.stale, self.state)


@dataclass
class BridgeOutcome:
    mode: str
    status: str
    bytes_written: int
    frame_sha256: str
    device_accessed: bool
    output_path: str | None = None
    error_code: str | None = None
    line: bytes = field(repr=False, default=b"")


class LoopbackSerial:
    """In-memory serial sink used by tests; it has no OS/device side effects."""

    def __init__(self):
        self.writes: list[bytes] = []

    def write(self, data: bytes) -> int:
        self.writes.append(bytes(data))
        return len(data)


class SerialBridge:
    def render(self, frame: dict[str, Any], output_path: Path | str | None = None) -> BridgeOutcome:
        line = encode_frame(frame)
        path_text = None
        if output_path is not None:
            path = Path(output_path)
            path.write_bytes(line)
            path_text = path.as_posix()
        return BridgeOutcome("dry_run", "rendered", len(line), sha256(line), False, path_text, line=line)

    def send_loopback(self, frame: dict[str, Any], serial: LoopbackSerial) -> BridgeOutcome:
        line = encode_frame(frame)
        written = serial.write(line)
        if written != len(line):
            _fail("SERIAL_WRITE_INCOMPLETE", f"wrote {written} of {len(line)} bytes")
        return BridgeOutcome("loopback", "sent", written, sha256(line), False, line=line)

    def send(
        self,
        frame: dict[str, Any],
        port: str | None,
        serial_factory: Callable[[str], Any] | None = None,
    ) -> BridgeOutcome:
        if not isinstance(port, str) or not port.strip():
            _fail("PORT_REQUIRED", "a real send requires an explicit serial port")
        if serial_factory is None:
            _fail("SERIAL_BACKEND_UNAVAILABLE", "real serial access requires an injected owner-approved backend")
        line = encode_frame(frame)
        serial = serial_factory(port)
        written = serial.write(line)
        if written != len(line):
            _fail("SERIAL_WRITE_INCOMPLETE", f"wrote {written} of {len(line)} bytes")
        return BridgeOutcome("serial", "sent", written, sha256(line), True, line=line)


def open_owner_serial(port: str) -> Any:
    """Open a serial backend only when a later owner explicitly requests a send."""

    try:
        import serial
    except ImportError:
        _fail("SERIAL_BACKEND_UNAVAILABLE", "install the owner-approved serial backend")
    return serial.Serial(port=port, baudrate=115200, timeout=1)
