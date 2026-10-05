"""Offline fixture collector and persistent cdm/1 USB sender.

Use --port only during operator hardware testing. No account credentials are used.
"""
import argparse
import copy
import datetime as dt
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import zlib

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "experiments" / "fixtures"
MAX_FRAME = 65536
IDENTITY = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
STATUS = {"available", "unavailable", "unsupported", "unauthorized", "error", "stale"}
SOURCE_KIND = {"fixture", "local_runtime", "provider_api", "ide_telemetry", "unknown"}
METRIC_KIND = {"quota_window", "token_balance", "credits", "session_telemetry"}
UNIT = {"percent", "token", "credit", "unknown"}


def valid_number(value, high=None):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0 and (high is None or value <= high)


def identity(value, nullable=False):
    return value is None and nullable or isinstance(value, str) and IDENTITY.fullmatch(value) is not None


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value):
        raise ValueError("timestamp missing")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone missing")
    return parsed.astimezone(dt.timezone.utc)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def usage_adapter(raw, reference_time):
    """Validate fixture truth without manufacturing missing quota windows or units."""
    required = {"schema_version", "snapshot_id", "provider_id", "agent_id", "host_id", "model_id", "account_profile_id", "source_kind", "metric_kind", "unit", "status", "observed_at", "windows", "stale", "last_good_at", "error_code", "error_reason"}
    if not isinstance(raw, dict) or set(raw) != required or raw["schema_version"] != 1 or not isinstance(raw["windows"], list):
        raise ValueError("SCHEMA_INVALID")
    if not isinstance(raw["snapshot_id"], str) or not IDENTIFIER.fullmatch(raw["snapshot_id"]):
        raise ValueError("SCHEMA_INVALID")
    if not identity(raw["provider_id"]) or not all(identity(raw[key], True) for key in ("agent_id", "host_id", "account_profile_id")):
        raise ValueError("SCHEMA_INVALID")
    if raw["model_id"] is not None and (not isinstance(raw["model_id"], str) or not raw["model_id"]):
        raise ValueError("SCHEMA_INVALID")
    if not all(isinstance(raw[key], str) for key in ("source_kind", "metric_kind", "unit", "status")) or raw["source_kind"] not in SOURCE_KIND or raw["metric_kind"] not in METRIC_KIND or raw["unit"] not in UNIT or raw["status"] not in STATUS or not isinstance(raw["stale"], bool):
        raise ValueError("SCHEMA_INVALID")
    for key in ("error_code", "error_reason"):
        if raw[key] is not None and (not isinstance(raw[key], str) or not raw[key]):
            raise ValueError("SCHEMA_INVALID")
    if raw["error_code"] is not None and not re.fullmatch(r"[A-Z][A-Z0-9_.-]*", raw["error_code"]):
        raise ValueError("SCHEMA_INVALID")
    if raw["status"] == "stale" and not raw["stale"]:
        raise ValueError("SCHEMA_INVALID")
    if raw["status"] == "available" and (not raw["agent_id"] or not raw["host_id"]):
        raise ValueError("MISSING_IDENTITY")
    observed = timestamp(raw["observed_at"]) if raw["observed_at"] is not None else None
    last_good = timestamp(raw["last_good_at"]) if raw["last_good_at"] is not None else None
    if any(value and value > reference_time for value in (observed, last_good)):
        raise ValueError("FUTURE_TIMESTAMP")
    age = (reference_time - observed).total_seconds() if observed else None
    if raw["status"] == "available" and age is not None and age >= 300:
        raise ValueError("STALE_THRESHOLD_EXCEEDED")
    seen = set()
    for w in raw["windows"]:
        keys = {"window_id", "label", "used_units", "remaining_units", "limit_units", "unit", "percent_used", "percent_remaining", "resets_at"}
        if not isinstance(w, dict) or not keys.issubset(w) or set(w) - keys - {"reset_status"}:
            raise ValueError("SCHEMA_INVALID")
        if not isinstance(w["window_id"], str) or not re.fullmatch(r"[a-z0-9][a-z0-9._:-]*", w["window_id"]) or not isinstance(w["label"], str) or not w["label"] or w["unit"] not in UNIT:
            raise ValueError("SCHEMA_INVALID")
        if "reset_status" in w and w["reset_status"] not in {"unknown", "scheduled", "expired"}:
            raise ValueError("SCHEMA_INVALID")
        key = (raw["provider_id"], raw["agent_id"], raw["host_id"], w["window_id"])
        if key in seen:
            raise ValueError("DUPLICATE_WINDOW")
        seen.add(key)
        for field in ("percent_used", "percent_remaining"):
            value = w[field]
            if value is not None and not valid_number(value, 100):
                raise ValueError("SCHEMA_INVALID")
        values = [w[k] for k in ("used_units", "remaining_units", "limit_units")]
        if any(value is not None and not valid_number(value) for value in values):
            raise ValueError("SCHEMA_INVALID")
        if all(v is not None for v in values) and abs(values[0] + values[1] - values[2]) > .01:
            raise ValueError("ABSOLUTE_BALANCE_MISMATCH")
        if w["percent_used"] is not None and w["percent_remaining"] is not None:
            if abs(w["percent_used"] + w["percent_remaining"] - 100) > .01:
                raise ValueError("PERCENT_BALANCE_MISMATCH")
        if w["resets_at"] is not None:
            reset = timestamp(w["resets_at"])
            w["reset_status"] = "scheduled" if reset > reference_time else "expired"
        else:
            w["reset_status"] = "unknown"
    return raw


def global_adapter(raw):
    if raw.get("source") != "codex-resets.com" or raw.get("captured_at") is None:
        raise ValueError("GLOBAL_CAPTURE_MISSING")
    timestamp(raw["captured_at"])
    if raw.get("latest_reset_at") is not None:
        timestamp(raw["latest_reset_at"])
    return {"schema_version": 1, "source": raw["source"], "captured_at": raw["captured_at"],
            "latest_reset_at": raw.get("latest_reset_at"), "forecast_24h_percent": None,
            "forecast_48h_percent": None, "forecast_is_schedule": False,
            "stale": bool(raw.get("stale", False)), "error_code": raw.get("error_code")}


def collect(reference_time, fixture_dir=FIXTURES, transition_stale=False, fixture_paths=None, cache=None):
    matrix = json.loads((fixture_dir / "provider-fixture-matrix.json").read_text(encoding="utf-8"))
    usage, errors = [], []
    paths = fixture_paths if fixture_paths is not None else ["providers/multi-provider-healthy.json"]
    for name in paths:
        path = fixture_dir / name
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            snapshots = raw if isinstance(raw, list) else raw.get("snapshots", [raw])
            validated = []
            for snapshot in snapshots:
                snapshot = copy.deepcopy(snapshot)
                if transition_stale and snapshot.get("status") == "available" and snapshot.get("observed_at"):
                    if (reference_time - timestamp(snapshot["observed_at"])).total_seconds() >= 300:
                        snapshot.update(status="stale", stale=True, error_code="SOURCE_STALE", error_reason="Fixture observation is at least 300 seconds old")
                validated.append(usage_adapter(snapshot, reference_time))
            usage.extend(validated)
            if cache is not None:
                cache[name] = copy.deepcopy(validated)
        except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
            errors.append({"source": name, "error": str(exc)})
            for previous in cache.get(name, []) if cache is not None else []:
                retained = copy.deepcopy(previous)
                retained.update(status="error", stale=True, error_code="COLLECT_ERROR", error_reason=str(exc))
                usage.append(retained)
    try:
        global_reset = global_adapter(json.loads((fixture_dir / "codex-resets-history.json").read_text(encoding="utf-8")))
        if transition_stale and (reference_time - timestamp(global_reset["captured_at"])).total_seconds() >= 300:
            global_reset.update(stale=True, error_code="SOURCE_STALE")
        globals_ = [global_reset]
        if cache is not None:
            cache["codex-resets.com"] = copy.deepcopy(global_reset)
    except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        errors.append({"source": "codex-resets.com", "error": str(exc)})
        previous = cache.get("codex-resets.com") if cache is not None else None
        globals_ = [dict(previous, stale=True, error_code="COLLECT_ERROR")] if previous else []
    return {"usage": usage, "global_resets": globals_}, errors


def frame(sequence, payload, sent_at):
    envelope = {"protocol": "cdm/1", "sequence": sequence, "sent_at": sent_at, "payload": payload}
    crc = zlib.crc32(canonical(envelope)) & 0xffffffff
    whole = dict(envelope, integrity={"algorithm": "crc32", "value": f"{crc:08X}"})
    data = canonical(whole) + b"\n"
    if len(data) > MAX_FRAME:
        raise ValueError("FRAME_TOO_LONG")
    return data


def reserve_sequence(state_path, alias, receiver_empty=False):
    """Reserve before write; a failed serial write still consumes its sequence."""
    if not alias or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in alias):
        raise ValueError("device alias must be lowercase letters, digits, '-' or '_'")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("alias") != alias or not isinstance(state.get("last_reserved"), int) or not 0 <= state["last_reserved"] <= 0xffffffff:
            raise ValueError("SENDER_STATE_CORRUPT")
        number = (state["last_reserved"] + 1) & 0xffffffff
    elif receiver_empty:
        number = 0
    else:
        raise ValueError("SENDER_STATE_MISSING: verify receiver state empty before --receiver-empty")
    temporary = state_path.with_suffix(state_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as output:
        json.dump({"alias": alias, "last_reserved": number}, output)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, state_path)
    return number


def send(port, alias, state_path, receiver_empty, manual=False, interval=60, log_path=None, fixture_paths=None):
    try:
        import serial
    except ImportError as exc:
        raise RuntimeError("pyserial is required for operator hardware runs") from exc
    if interval > 60 or interval <= 0:
        raise ValueError("interval must be 1..60 seconds")
    cache = {}
    while True:
        try:
            device = serial.Serial(port=None, baudrate=115200, bytesize=8, parity="N", stopbits=1, timeout=1, write_timeout=2, rtscts=False, xonxoff=False)
            device.dtr = False
            device.rts = False
            device.port = port
            with device:
                while True:
                    now = dt.datetime.now(dt.timezone.utc)
                    payload, errors = collect(now, transition_stale=True, fixture_paths=fixture_paths, cache=cache)
                    sequence = reserve_sequence(state_path, alias, receiver_empty)
                    receiver_empty = False
                    data = frame(sequence, payload, now.isoformat().replace("+00:00", "Z"))
                    receipt = {"sequence": sequence, "sent_at": now.isoformat(), "bytes": len(data), "frame_hex": data.hex(), "errors": errors}
                    try:
                        device.write(data)
                        device.flush()
                        receipt["write"] = "host_completed_no_device_ack"
                    except serial.SerialException as exc:
                        receipt["write"] = "failed"
                        receipt["error"] = str(exc)
                        raise
                    finally:
                        if log_path:
                            with log_path.open("a", encoding="utf-8") as log:
                                log.write(json.dumps(receipt, ensure_ascii=False) + "\n")
                    if manual:
                        return
                    time.sleep(interval)
        except serial.SerialException as exc:
            print(f"serial reconnect: {exc}", file=sys.stderr)
            if manual:
                raise
            time.sleep(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", help="operator selected COM port")
    parser.add_argument("--alias", default="desk-meter")
    parser.add_argument("--state", type=Path, default=Path("sender-state.json"))
    parser.add_argument("--receiver-empty", action="store_true")
    parser.add_argument("--manual", action="store_true")
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--fixture", action="append", help="relative provider fixture path; repeat for separate sources")
    args = parser.parse_args()
    if args.preview:
        payload, errors = collect(timestamp(json.loads((FIXTURES / "provider-fixture-matrix.json").read_text())["reference_time"]), fixture_paths=args.fixture)
        print(json.dumps({"payload": payload, "errors": errors}, ensure_ascii=False, indent=2))
    elif args.port:
        send(args.port, args.alias, args.state, args.receiver_empty, args.manual, args.interval, args.log, args.fixture)
    else:
        parser.error("--port or --preview required")


if __name__ == "__main__":
    main()
