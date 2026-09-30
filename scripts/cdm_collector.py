#!/usr/bin/env python3
"""Offline Codex Desk Meter fixture collector and cdm/1 serial sender."""

from __future__ import annotations

import argparse
import contextlib
import ctypes
import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import re
import shutil
import sys
import tempfile
import time
import zlib
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
MAX_FRAME_BYTES = 65_536
STALE_AFTER_SECONDS = 300
U32_MASK = 0xFFFFFFFF


class CollectionError(ValueError):
    def __init__(self, message: str, code: str = "COLLECTION_INVALID"):
        super().__init__(message)
        self.code = code


class SequenceStateError(RuntimeError):
    pass


def parse_timestamp(value: Any, field: str) -> dt.datetime:
    if not isinstance(value, str):
        raise CollectionError(f"{field} must be an RFC3339 timestamp", "INVALID_TIMESTAMP")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CollectionError(f"{field} is not a valid RFC3339 timestamp", "INVALID_TIMESTAMP") from exc
    if parsed.tzinfo is None:
        raise CollectionError(f"{field} must include a timezone", "INVALID_TIMESTAMP")
    return parsed.astimezone(dt.timezone.utc)


def _finite_number_or_none(value: Any, name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise CollectionError(f"{name} must be a finite non-negative number or null", "SCHEMA_INVALID")
    return value


def normalize_snapshot(raw: dict[str, Any], *, snapshot_id: str | None = None,
                       observed_at: str | None = None,
                       reference_time: str | None = None, mark_stale: bool = True) -> dict[str, Any]:
    """Validate a schema-shaped source result and preserve its declared units."""
    required = {
        "provider_id", "agent_id", "host_id", "model_id", "account_profile_id",
        "source_kind", "metric_kind", "unit", "status", "observed_at", "windows",
    }
    missing = required - raw.keys()
    if missing:
        raise CollectionError(f"missing snapshot fields: {', '.join(sorted(missing))}", "SCHEMA_INVALID")
    candidate = dict(raw)
    candidate["schema_version"] = 1
    candidate["snapshot_id"] = snapshot_id or candidate.get("snapshot_id") or "fixture-" + str(candidate["provider_id"])
    candidate["observed_at"] = observed_at if observed_at is not None else candidate["observed_at"]
    candidate.setdefault("stale", candidate["status"] == "stale")
    candidate.setdefault("last_good_at", candidate["observed_at"] if candidate["status"] == "available" else None)
    candidate.setdefault("error_code", None)
    candidate.setdefault("error_reason", None)
    reference = parse_timestamp(reference_time, "reference_time") if reference_time else dt.datetime.now(dt.timezone.utc)

    enums = {
        "source_kind": {"fixture", "local_runtime", "provider_api", "ide_telemetry", "unknown"},
        "metric_kind": {"quota_window", "token_balance", "credits", "session_telemetry"},
        "unit": {"percent", "token", "credit", "unknown"},
        "status": {"available", "unavailable", "unsupported", "unauthorized", "error", "stale"},
    }
    for key, values in enums.items():
        if candidate[key] not in values:
            raise CollectionError(f"invalid {key}: {candidate[key]!r}", "SCHEMA_INVALID")
    if not isinstance(candidate["provider_id"], str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", candidate["provider_id"]):
        raise CollectionError("provider_id is not a normalized identity", "SCHEMA_INVALID")
    for key in ("agent_id", "host_id", "account_profile_id"):
        value = candidate[key]
        if value is not None and (not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", value)):
            raise CollectionError(f"{key} is not a normalized identity", "SCHEMA_INVALID")
    if candidate["observed_at"] is not None:
        observed = parse_timestamp(candidate["observed_at"], "observed_at")
        if observed > reference:
            raise CollectionError("observed_at is in the future", "FUTURE_TIMESTAMP")
        if candidate["status"] == "available" and (reference - observed).total_seconds() >= STALE_AFTER_SECONDS:
            if not mark_stale:
                raise CollectionError("available snapshot exceeds the 300 second stale threshold", "STALE_THRESHOLD_EXCEEDED")
            candidate["status"] = "stale"
            candidate["stale"] = True
            candidate["error_code"] = "SOURCE_STALE"
            candidate["error_reason"] = "The source observation is at least 300 seconds old; its value is retained as stale."
    elif candidate["status"] == "available":
        raise CollectionError("available snapshot requires observed_at", "SCHEMA_INVALID")
    if not isinstance(candidate["windows"], list):
        raise CollectionError("windows must be an array", "SCHEMA_INVALID")

    seen_windows: set[str] = set()
    normalized_windows = []
    for item in candidate["windows"]:
        if not isinstance(item, dict):
            raise CollectionError("each quota window must be an object", "SCHEMA_INVALID")
        window = dict(item)
        for key in ("window_id", "label", "unit"):
            if not isinstance(window.get(key), str) or not window[key]:
                raise CollectionError(f"quota window requires {key}", "SCHEMA_INVALID")
        if window["window_id"] in seen_windows:
            raise CollectionError(f"duplicate window id {window['window_id']}", "DUPLICATE_WINDOW")
        seen_windows.add(window["window_id"])
        if window["unit"] not in {"percent", "token", "credit", "unknown"}:
            raise CollectionError("invalid quota window unit", "SCHEMA_INVALID")
        for key in ("used_units", "remaining_units", "limit_units", "percent_used", "percent_remaining"):
            window.setdefault(key, None)
            _finite_number_or_none(window[key], key)
        for key in ("percent_used", "percent_remaining"):
            if window[key] is not None and window[key] > 100:
                raise CollectionError(f"{key} exceeds 100", "SCHEMA_INVALID")
        window.setdefault("resets_at", None)
        if window["resets_at"] is not None:
            reset_time = parse_timestamp(window["resets_at"], "resets_at")
            window["reset_status"] = "scheduled" if reset_time > reference else "expired"
        else:
            window["reset_status"] = "unknown"
        if window["reset_status"] not in {"unknown", "scheduled", "expired"}:
            raise CollectionError("invalid reset_status", "SCHEMA_INVALID")
        units = (window["used_units"], window["remaining_units"], window["limit_units"])
        if all(value is not None for value in units) and abs(units[0] + units[1] - units[2]) > 0.01:
            raise CollectionError("absolute quota balance does not equal its limit", "ABSOLUTE_BALANCE_MISMATCH")
        normalized_windows.append(window)
    candidate["windows"] = normalized_windows
    if candidate["status"] in {"unavailable", "unsupported", "unauthorized", "error", "stale"}:
        if not candidate.get("error_code") or not candidate.get("error_reason"):
            raise CollectionError("non-available snapshot requires an error code and reason", "SCHEMA_INVALID")
    candidate["stale"] = bool(candidate["stale"] or candidate["status"] == "stale")
    if candidate["status"] == "stale" and not candidate["stale"]:
        raise CollectionError("stale status requires stale=true", "SCHEMA_INVALID")
    return candidate


class FixtureRegistry:
    """Reads only valid cases declared by the checked-in synthetic fixture matrix."""

    def __init__(self, fixture_dir: pathlib.Path | str):
        self.fixture_dir = pathlib.Path(fixture_dir)
        self.matrix_path = self.fixture_dir.parent / "provider-fixture-matrix.json"

    def collect_all(self) -> list[dict[str, Any]]:
        matrix = json.loads(self.matrix_path.read_text(encoding="utf-8"))
        reference_time = matrix["reference_time"]
        collected: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        for entry in matrix["fixtures"]:
            if entry["expected"] != "valid":
                continue
            path = (self.fixture_dir.parent / entry["path"]).resolve()
            if self.fixture_dir.parent.resolve() not in path.parents:
                raise CollectionError("fixture path escaped the checked-in directory", "FIXTURE_PATH_INVALID")
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                records = raw if isinstance(raw, list) else [raw]
                for index, item in enumerate(records):
                    collected.append(normalize_snapshot(item, reference_time=reference_time, mark_stale=False,
                                                        snapshot_id=item.get("snapshot_id") or f"fixture-{path.stem}-{index}"))
            except (OSError, json.JSONDecodeError, CollectionError) as exc:
                errors.append({"fixture": path.name, "reason": str(exc)})
        if errors:
            raise CollectionError("valid fixture matrix cases failed: " + json.dumps(errors, ensure_ascii=False), "FIXTURE_MATRIX_INVALID")
        return collected


def normalize_personal_usage(raw: dict[str, Any]) -> dict[str, Any]:
    windows = []
    for source in raw.get("windows", []):
        windows.append({
            "window_id": source["id"], "label": source["label"],
            "used_units": None, "remaining_units": None, "limit_units": None,
            "unit": "percent", "percent_used": source.get("percent_used"),
            "percent_remaining": source.get("percent_remaining"),
            "resets_at": source.get("resets_at"),
        })
    status = "error" if raw.get("error_code") else "available"
    error_code = raw.get("error_code")
    return normalize_snapshot({
        "provider_id": "openai", "agent_id": "codex-cli", "host_id": "terminal",
        "model_id": None, "account_profile_id": None, "source_kind": "fixture",
        "metric_kind": "quota_window", "unit": "percent", "status": status,
        "observed_at": raw.get("captured_at"), "windows": windows,
        "stale": bool(raw.get("stale")), "last_good_at": raw.get("captured_at") if not error_code else None,
        "error_code": error_code, "error_reason": "The synthetic personal-usage fixture reports an error." if error_code else None,
    }, snapshot_id="fixture-personal-usage")


def normalize_global_reset(raw: dict[str, Any], *, source: str | None = None) -> dict[str, Any]:
    value = {
        "schema_version": 1,
        "source": source or raw.get("source", "codex-resets.com"),
        "captured_at": raw.get("captured_at"),
        "latest_reset_at": raw.get("latest_reset_at", raw.get("last_reset_at")),
        "forecast_24h_percent": raw.get("forecast_24h_percent"),
        "forecast_48h_percent": raw.get("forecast_48h_percent"),
        "forecast_is_schedule": False,
        "stale": bool(raw.get("stale", False)),
        "error_code": raw.get("error_code"),
    }
    if not value["captured_at"]:
        raise CollectionError("global reset snapshot has no captured_at", "SCHEMA_INVALID")
    parse_timestamp(value["captured_at"], "captured_at")
    reference = dt.datetime.now(dt.timezone.utc)
    if parse_timestamp(value["captured_at"], "captured_at") > reference:
        raise CollectionError("global reset captured_at is in the future", "FUTURE_TIMESTAMP")
    if value["latest_reset_at"] is not None and parse_timestamp(value["latest_reset_at"], "latest_reset_at") > reference:
        raise CollectionError("latest_reset_at is in the future", "FUTURE_TIMESTAMP")
    value["stale"] = value["stale"] or (reference - parse_timestamp(value["captured_at"], "captured_at")).total_seconds() >= STALE_AFTER_SECONDS
    if value["latest_reset_at"] is not None:
        parse_timestamp(value["latest_reset_at"], "latest_reset_at")
    for key in ("forecast_24h_percent", "forecast_48h_percent"):
        value[key] = _finite_number_or_none(value[key], key)
        if value[key] is not None and value[key] > 100:
            raise CollectionError(f"{key} exceeds 100", "SCHEMA_INVALID")
    if value["source"] not in {"codex-resets.com", "codex-reset.com"}:
        raise CollectionError("unsupported global reset source", "SCHEMA_INVALID")
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def crc32_without_integrity(frame: dict[str, Any]) -> str:
    body = {key: value for key, value in frame.items() if key != "integrity"}
    return f"{zlib.crc32(canonical_json(body).encode('utf-8')) & U32_MASK:08X}"


def make_frame(usage: list[dict[str, Any]], global_resets: list[dict[str, Any]], *,
               sequence: int, sent_at: str | None = None) -> dict[str, Any]:
    if not 0 <= sequence <= U32_MASK:
        raise ValueError("sequence must be an unsigned 32-bit integer")
    envelope = {
        "protocol": "cdm/1", "sequence": sequence,
        "sent_at": sent_at or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "payload": {"usage": usage, "global_resets": global_resets},
    }
    return {**envelope, "integrity": {"algorithm": "crc32", "value": crc32_without_integrity(envelope)}}


def encode_frame(frame: dict[str, Any]) -> bytes:
    line = canonical_json(frame).encode("utf-8") + b"\n"
    if len(line) > MAX_FRAME_BYTES:
        raise CollectionError("frame exceeds the 65536 byte line limit", "FRAME_TOO_LARGE")
    return line


def _atomic_json_write(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: pathlib.Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=path.parent,
                                         prefix=path.name + ".", suffix=".tmp", delete=False) as file:
            temporary = pathlib.Path(file.name)
            json.dump(value, file, sort_keys=True, separators=(",", ":"))
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def initialize_sender_state(path: pathlib.Path | str, *, receiver_known_empty: bool) -> None:
    target = pathlib.Path(path)
    if not receiver_known_empty:
        raise SequenceStateError("receiver sequence state must be known empty before initialization")
    if target.exists():
        raise SequenceStateError("sender state already exists; initialization never overwrites it")
    _atomic_json_write(target, {"schema_version": 1, "last_reserved": None})


class SenderSequence:
    def __init__(self, path: pathlib.Path | str):
        self.path = pathlib.Path(path)

    @contextlib.contextmanager
    def exclusive(self):
        lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_file = lock_path.open("a+b")
        try:
            if lock_file.seek(0, os.SEEK_END) == 0:
                lock_file.write(b"\0")
                lock_file.flush()
            lock_file.seek(0)
            if os.name == "nt":
                import msvcrt
                try:
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError as exc:
                    raise SequenceStateError("another collector already owns this device alias") from exc
            else:
                import fcntl
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise SequenceStateError("another collector already owns this device alias") from exc
            yield
        finally:
            try:
                lock_file.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
            lock_file.close()

    def _reserve_locked(self) -> int:
        if not self.path.exists():
            raise SequenceStateError("sender state is missing; initialize only after confirming an empty receiver")
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
            if state.get("schema_version") != 1 or not (state.get("last_reserved") is None or
                    (isinstance(state["last_reserved"], int) and not isinstance(state["last_reserved"], bool) and
                     0 <= state["last_reserved"] <= U32_MASK)):
                raise ValueError("invalid state values")
        except (OSError, json.JSONDecodeError, AttributeError, ValueError, TypeError) as exc:
            raise SequenceStateError(f"sender state is corrupt: {exc}") from exc
        previous = state["last_reserved"]
        sequence = 0 if previous is None else (previous + 1) & U32_MASK
        _atomic_json_write(self.path, {"schema_version": 1, "last_reserved": sequence})
        return sequence

    def reserve(self) -> int:
        with self.exclusive():
            return self._reserve_locked()


class WindowsSerial:
    """Minimal Win32 COM writer. The device is opened only from explicit --send."""

    def __init__(self, port: str, baud: int = 115200):
        if os.name != "nt":
            raise OSError("the built-in serial backend currently supports Windows only")
        self.port = port
        self.baud = baud
        self.handle = None

    def open(self, timeout_seconds: float = 5.0) -> None:
        import subprocess

        mode_executable = shutil.which("mode.com")
        if mode_executable is None:
            raise FileNotFoundError("Windows mode.com executable was not found on PATH")
        deadline = time.monotonic() + timeout_seconds
        last_error = "port not available"
        while time.monotonic() < deadline:
            config = subprocess.run([mode_executable, self.port, f"BAUD={self.baud}", "PARITY=n", "DATA=8", "STOP=1"],
                                    capture_output=True, text=True, check=False)
            if config.returncode == 0:
                kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
                kernel32.CreateFileW.restype = ctypes.c_void_p
                handle = kernel32.CreateFileW("\\\\.\\" + self.port, 0x40000000, 0, None, 3, 0, None)
                if handle not in (None, ctypes.c_void_p(-1).value):
                    self.handle = (kernel32, handle)
                    return
                last_error = f"CreateFileW failed with WinError {ctypes.get_last_error()}"
            else:
                last_error = (config.stderr or config.stdout or "mode failed").strip()
            time.sleep(min(1.0, max(0.0, deadline - time.monotonic())))
        raise OSError(f"could not open {self.port} within {timeout_seconds:g}s: {last_error}")

    def write(self, data: bytes) -> int:
        if self.handle is None:
            raise OSError("serial port is not open")
        kernel32, handle = self.handle
        written = ctypes.c_ulong()
        buffer = ctypes.create_string_buffer(data)
        ok = kernel32.WriteFile(ctypes.c_void_p(handle), buffer, len(data), ctypes.byref(written), None)
        if not ok or written.value != len(data):
            raise OSError(f"WriteFile failed or wrote {written.value}/{len(data)} bytes; WinError {ctypes.get_last_error()}")
        return written.value

    def close(self) -> None:
        if self.handle is not None:
            kernel32, handle = self.handle
            kernel32.CloseHandle(ctypes.c_void_p(handle))
            self.handle = None


class MemorySerial:
    """Test-only sink used to exercise the same complete-line writer."""
    def __init__(self):
        self.data = bytearray()

    def write(self, data: bytes) -> int:
        self.data.extend(data)
        return len(data)


def write_frame(transport: Any, frame: dict[str, Any]) -> int:
    wire = encode_frame(frame)
    written = transport.write(wire)
    if written != len(wire):
        raise OSError(f"short serial write: {written}/{len(wire)} bytes")
    return written


def append_serial_log(path: pathlib.Path | str, *, port: str, fixture_paths: list[pathlib.Path],
                      frame: dict[str, Any], bytes_written: int) -> None:
    fixture_root = (ROOT / "experiments" / "fixtures").resolve()
    inputs = []
    for source in fixture_paths:
        source = source.resolve()
        if fixture_root not in source.parents:
            raise CollectionError("serial audit log accepts only checked-in fixture inputs", "FIXTURE_PATH_INVALID")
        raw = source.read_bytes()
        inputs.append({"path": source.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(raw).hexdigest(),
                       "raw_utf8": raw.decode("utf-8")})
    wire = encode_frame(frame)
    record = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "transport": "usb-serial-cdm-1", "port": port, "baud": 115200,
        "acceptance": "unconfirmed_no_device_ack", "sequence": frame["sequence"],
        "fixture_inputs": inputs, "frame_sha256": hashlib.sha256(wire).hexdigest(),
        "frame_json": canonical_json(frame), "bytes_written": bytes_written,
    }
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        output.flush()
        os.fsync(output.fileno())


def selected_fixture_paths(args: argparse.Namespace) -> list[pathlib.Path]:
    fixture_root = (ROOT / "experiments" / "fixtures").resolve()
    selected: list[pathlib.Path] = []
    if args.all_provider_fixtures:
        matrix = json.loads((fixture_root / "provider-fixture-matrix.json").read_text(encoding="utf-8"))
        selected.extend((fixture_root / entry["path"]).resolve() for entry in matrix["fixtures"] if entry["expected"] == "valid")
        selected.append(fixture_root / "provider-fixture-matrix.json")
        if not args.omit_global_reset:
            selected.append(fixture_root / "codex-resets-history.json")
    elif args.fixture:
        for name in args.fixture:
            path = pathlib.Path(name)
            selected.append((path if path.is_absolute() else ROOT / path).resolve())
        if not args.omit_global_reset and not any("reset" in path.name for path in selected):
            selected.extend([fixture_root / "codex-reset-forecast.json", fixture_root / "codex-resets-history.json"])
    else:
        selected.extend([fixture_root / "personal-usage.json", fixture_root / "codex-reset-forecast.json", fixture_root / "codex-resets-history.json"])
    if any(fixture_root not in path.parents for path in selected):
        raise CollectionError("only repository fixture files can be collected", "FIXTURE_PATH_INVALID")
    return list(dict.fromkeys(selected))


def collect_cli_fixtures(args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    usage: list[dict[str, Any]] = []
    resets: list[dict[str, Any]] = []
    if args.all_provider_fixtures:
        usage.extend(FixtureRegistry(ROOT / "experiments" / "fixtures" / "providers").collect_all())
    elif args.fixture:
        for fixture_name in args.fixture:
            path = pathlib.Path(fixture_name)
            if not path.is_absolute():
                path = ROOT / path
            path = path.resolve()
            if (ROOT / "experiments" / "fixtures").resolve() not in path.parents:
                raise CollectionError("only checked-in experiment fixtures can be collected", "FIXTURE_PATH_INVALID")
            raw = json.loads(path.read_text(encoding="utf-8"))
            if path.name == "personal-usage.json":
                usage.append(normalize_personal_usage(raw))
            elif path.parent.name == "providers":
                items = raw if isinstance(raw, list) else [raw]
                usage.extend(normalize_snapshot(item) for item in items)
            elif "reset" in path.name:
                resets.append(normalize_global_reset(raw))
            else:
                raise CollectionError(f"no fixture adapter for {path}", "UNSUPPORTED_FIXTURE")
    else:
        usage.append(normalize_personal_usage(json.loads((ROOT / "experiments/fixtures/personal-usage.json").read_text(encoding="utf-8"))))
        resets.append(normalize_global_reset(json.loads((ROOT / "experiments/fixtures/codex-reset-forecast.json").read_text(encoding="utf-8"))))
        resets.append(normalize_global_reset(json.loads((ROOT / "experiments/fixtures/codex-resets-history.json").read_text(encoding="utf-8"))))
    if not resets and not args.omit_global_reset:
        resets.append(normalize_global_reset(json.loads((ROOT / "experiments/fixtures/codex-reset-forecast.json").read_text(encoding="utf-8"))))
        resets.append(normalize_global_reset(json.loads((ROOT / "experiments/fixtures/codex-resets-history.json").read_text(encoding="utf-8"))))
    return usage, resets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect offline Codex Desk Meter fixtures and optionally send one cdm/1 frame.")
    parser.add_argument("--fixture", action="append", help="fixture path; repeat for provider and reset inputs")
    parser.add_argument("--all-provider-fixtures", action="store_true", help="collect valid cases from the checked-in provider fixture matrix")
    parser.add_argument("--omit-global-reset", action="store_true")
    parser.add_argument("--device-alias", default="desk-meter", help="stable physical-device name for sequence persistence")
    parser.add_argument("--state-file", type=pathlib.Path, help="sender sequence state file (default: .cdm-state/<alias>.json)")
    parser.add_argument("--initialize-empty-receiver", action="store_true", help="create initial sequence state only after operator confirms receiver is empty")
    parser.add_argument("--send", action="store_true", help="open the named serial port and send the frame")
    parser.add_argument("--watch", action="store_true", help="recollect and send repeatedly at the selected interval")
    parser.add_argument("--interval-seconds", type=int, default=60, help="watch interval, 5..60 seconds")
    parser.add_argument("--port", help="explicit Windows serial port, e.g. COM3; required with --send")
    parser.add_argument("--log-file", type=pathlib.Path, help="append raw fixture/frame audit records (default: logs/cdm-serial.jsonl)")
    args = parser.parse_args(argv)
    try:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", args.device_alias):
            raise SequenceStateError("device alias must contain only letters, digits, dot, underscore, or dash")
        if args.watch and (not args.send or not 5 <= args.interval_seconds <= 60):
            parser.error("--watch requires --send and --interval-seconds from 5 through 60")
        state = args.state_file or (ROOT / ".cdm-state" / f"{args.device_alias}.json")
        if args.send and not args.port:
            parser.error("--send requires an explicit --port")
        if args.initialize_empty_receiver:
            initialize_sender_state(state, receiver_known_empty=True)
        if args.send:
            transport = WindowsSerial(args.port)
            sequence_state = SenderSequence(state)
            try:
                transport.open(timeout_seconds=5.0)
                with sequence_state.exclusive():
                    while True:
                        usage, resets = collect_cli_fixtures(args)
                        sequence = sequence_state._reserve_locked()
                        frame = make_frame(usage, resets, sequence=sequence)
                        wire_size = len(encode_frame(frame))
                        written = write_frame(transport, frame)
                        log_path = args.log_file or (ROOT / "logs" / "cdm-serial.jsonl")
                        append_serial_log(log_path, port=args.port, fixture_paths=selected_fixture_paths(args),
                                          frame=frame, bytes_written=written)
                        print(f"provider_snapshots={len(usage)} global_resets={len(resets)} sequence={sequence} bytes={wire_size}")
                        print(f"host_write=complete bytes={written} port={args.port} baud=115200; cdm/1 has no device acknowledgement")
                        if not args.watch:
                            break
                        time.sleep(args.interval_seconds)
            finally:
                transport.close()
        else:
            usage, resets = collect_cli_fixtures(args)
            frame = make_frame(usage, resets, sequence=0)
            wire = encode_frame(frame)
            print(f"provider_snapshots={len(usage)} global_resets={len(resets)} bytes={len(wire)}", file=sys.stderr)
            print("support=offline_fixture_only; live account collection is not implemented and no credentials or network source were accessed", file=sys.stderr)
            sys.stdout.buffer.write(wire)
        return 0
    except (OSError, json.JSONDecodeError, CollectionError, SequenceStateError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
