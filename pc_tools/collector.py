"""Offline fixture collector + normalizer (candidate product, PC side).

Reads only checkout fixtures. Preserves source/time/unit/error, never invents
windows or values, never touches credentials or the network.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDER_ROOT = ROOT / "experiments" / "fixtures" / "providers"
FIXTURE_ROOT = ROOT / "experiments" / "fixtures"
STALE_SECONDS = 300
ABS_TOL = 0.01

DEFAULT_PROVIDER_FIXTURES = [
    "codex-percent-window.json",
    "claude-code-windows.json",
    "gemini-cli-unsupported.json",
    "antigravity-cli-unsupported.json",
    "orca-host-claude-code.json",
]
DEFAULT_GLOBAL_FIXTURES = [
    "codex-reset-forecast.json",
    "codex-resets-history.json",
]


class CollectError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def parse_ts(value, where: str) -> datetime:
    if not isinstance(value, str):
        raise CollectError("TIMESTAMP_INVALID", f"{where} must be RFC3339")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise CollectError("TIMESTAMP_INVALID", f"{where} is not RFC3339: {value!r}")
    if dt.tzinfo is None:
        raise CollectError("TIMESTAMP_INVALID", f"{where} must include a timezone")
    return dt.astimezone(timezone.utc)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise CollectError("FIXTURE_NOT_FOUND", str(path))
    except json.JSONDecodeError as exc:
        raise CollectError("FIXTURE_INVALID_JSON", f"{path}: {exc}")


def check_snapshot(snap: dict, reference: datetime) -> str | None:
    """Return an error_code string for invalid snapshots, else None.

    Valid snapshots (including error-carrying ones like unsupported/stale) pass
    schema-shape checks here; semantic violations return codes matching the
    provider-fixture-matrix vocabulary.
    """
    if not isinstance(snap, dict):
        return "SCHEMA_INVALID"
    for key in ("snapshot_id", "provider_id", "status", "observed_at", "windows",
                "stale", "last_good_at", "error_code"):
        if key not in snap:
            return "SCHEMA_INVALID"
    for w in snap.get("windows", []):
        for num_key in ("percent_used", "percent_remaining"):
            v = w.get(num_key)
            if v is not None and not isinstance(v, bool):
                if not isinstance(v, (int, float)) or not (0 <= v <= 100):
                    return "SCHEMA_INVALID"
        for num_key in ("used_units", "remaining_units", "limit_units"):
            v = w.get(num_key)
            if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0):
                return "SCHEMA_INVALID"
        pu, pr = w.get("percent_used"), w.get("percent_remaining")
        if pu is not None and pr is not None:
            if abs((pu + pr) - 100) > 0.01:
                return "SCHEMA_INVALID"
        uu, ru, lu = w.get("used_units"), w.get("remaining_units"), w.get("limit_units")
        if uu is not None and ru is not None and lu is not None:
            if abs((uu + ru) - lu) > ABS_TOL:
                return "ABSOLUTE_BALANCE_MISMATCH"
    ids = [w.get("window_id") for w in snap.get("windows", [])]
    if len(ids) != len(set(ids)):
        return "DUPLICATE_WINDOW"
    obs_raw = snap.get("observed_at")
    if obs_raw is not None:
        try:
            obs = parse_ts(obs_raw, "observed_at")
        except CollectError:
            return "SCHEMA_INVALID"
        if obs > reference:
            return "FUTURE_TIMESTAMP"
        age = (reference - obs).total_seconds()
        if snap.get("status") == "available" and age >= STALE_SECONDS:
            return "STALE_THRESHOLD_EXCEEDED"
    lg_raw = snap.get("last_good_at")
    if lg_raw is not None:
        try:
            lg = parse_ts(lg_raw, "last_good_at")
        except CollectError:
            return "SCHEMA_INVALID"
        if lg > reference:
            return "FUTURE_TIMESTAMP"
    return None


def collect_providers(names: list[str], reference: datetime):
    snapshots: list[dict] = []
    failures: list[dict] = []
    for name in names:
        path = (PROVIDER_ROOT / name).resolve()
        if not str(path).startswith(str(PROVIDER_ROOT.resolve())):
            failures.append({"adapter_id": name, "code": "FIXTURE_PATH_UNSAFE",
                             "message": "fixture must stay under providers/"})
            continue
        try:
            value = load_json(path)
            entries = value if isinstance(value, list) else [value]
            for entry in entries:
                code = check_snapshot(entry, reference)
                if code:
                    raise CollectError(code, f"{name} rejected: {code}")
                snapshots.append(copy.deepcopy(entry))
        except CollectError as exc:
            failures.append({"adapter_id": name, "code": exc.code, "message": str(exc)})
    return snapshots, failures


def normalize_global_reset(raw: dict) -> dict:
    """Wire model: logical provider->source, fetched_at->captured_at, v1."""
    if not isinstance(raw, dict):
        raise CollectError("GLOBAL_RESET_INVALID", "global reset input must be an object")
    for wire, logical in (("source", "provider"), ("captured_at", "fetched_at"),
                          ("latest_reset_at", "last_reset_at")):
        if wire in raw and logical in raw and raw[wire] != raw[logical]:
            raise CollectError("GLOBAL_RESET_ALIAS_CONFLICT", f"{wire} and {logical} disagree")
    captured = raw.get("captured_at", raw.get("fetched_at"))
    if captured is None:
        raise CollectError("CAPTURED_AT_REQUIRED", "captured_at is null: no valid wire")
    return {
        "schema_version": 1,
        "source": raw.get("source", raw.get("provider")),
        "captured_at": captured,
        "latest_reset_at": raw.get("latest_reset_at", raw.get("last_reset_at")),
        "forecast_24h_percent": raw.get("forecast_24h_percent"),
        "forecast_48h_percent": raw.get("forecast_48h_percent"),
        "forecast_is_schedule": False,
        "stale": bool(raw.get("stale", False)),
        "error_code": raw.get("error_code"),
    }


def collect_globals(names: list[str]):
    resets: list[dict] = []
    failures: list[dict] = []
    for name in names:
        try:
            raw = load_json(FIXTURE_ROOT / name)
            resets.append(normalize_global_reset(raw))
        except CollectError as exc:
            failures.append({"adapter_id": name, "code": exc.code, "message": str(exc)})
    return resets, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="append", default=None,
                        help="provider fixture file name under experiments/fixtures/providers")
    parser.add_argument("--global-fixture", action="append", default=None)
    parser.add_argument("--reference-time", default="2026-09-10T00:04:59Z")
    parser.add_argument("--out-payload", type=Path, default=None)
    parser.add_argument("--out-report", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        reference = parse_ts(args.reference_time, "reference_time")
    except CollectError as exc:
        print(json.dumps({"status": "rejected", "error_code": exc.code}),
              file=sys.stderr)
        return 1
    providers = args.fixture or DEFAULT_PROVIDER_FIXTURES
    globals_ = args.global_fixture or DEFAULT_GLOBAL_FIXTURES
    snapshots, pfails = collect_providers(providers, reference)
    resets, gfails = collect_globals(globals_)
    payload = {"usage": snapshots, "global_resets": resets}
    report = {"status": "collected", "snapshots": len(snapshots),
              "global_resets": len(resets),
              "failures": pfails + gfails}
    line = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    if args.out_payload is not None:
        args.out_payload.write_text(line + "\n", encoding="utf-8")
    else:
        sys.stdout.write(line + "\n")
    if args.out_report is not None:
        args.out_report.write_text(json.dumps(report, ensure_ascii=False,
                                              sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True), file=sys.stderr)
    return 0 if not (pfails or gfails) else 2


if __name__ == "__main__":
    raise SystemExit(main())
