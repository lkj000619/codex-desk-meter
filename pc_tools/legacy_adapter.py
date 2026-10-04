"""Legacy provider/global seam for scripts/evaluate-product.py.

Reads stdin UTF-8 JSON {source, events:[{now, body, error}]} and writes one
normalized snapshot per event to stdout. Fresh state per invocation; events
share one last-good within the invocation. Never contacts a provider.
"""
from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timezone


def parse_ts(value) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    return dt.astimezone(timezone.utc)


def age_seconds(now: datetime, captured: datetime) -> float:
    return (now - captured).total_seconds()


def fixture_snapshot(body: dict, now: datetime, error_code, last_good) -> dict:
    captured_raw = body.get("captured_at") if isinstance(body, dict) else None
    captured = parse_ts(captured_raw)
    windows = body.get("windows") if isinstance(body, dict) else None
    if last_good is not None and (not isinstance(body, dict) or captured is None
                                  or not isinstance(windows, list)):
        out = copy.deepcopy(last_good)
        out["stale"] = False
        out["error_code"] = error_code or "CAPTURED_AT_INVALID"
        return out
    assert isinstance(body, dict) and captured is not None
    # Percent range guard (legacy seam scope: 0..100).
    bad = False
    for w in windows:
        for key in ("percent_used", "percent_remaining"):
            v = w.get(key)
            if v is not None and (not isinstance(v, (int, float)) or not 0 <= v <= 100):
                bad = True
    now_dt = now
    stale = age_seconds(now_dt, captured) >= 300
    if bad or (error_code is not None) or (captured > now_dt):
        out = {
            "source": "fixture",
            "windows": copy.deepcopy(windows),
            "observed_at": captured_raw,
            "stale": False,
            "error_code": error_code or ("PERCENT_OUT_OF_RANGE" if bad else "FUTURE_CAPTURED_AT"),
        }
        return out
    return {"source": "fixture", "windows": copy.deepcopy(windows),
            "observed_at": captured_raw, "stale": stale, "error_code": None}


def global_snapshot(source: str, body: dict, now: datetime, error_code, last_good) -> dict:
    captured_raw = body.get("captured_at") if isinstance(body, dict) else None
    captured = parse_ts(captured_raw)
    if last_good is not None and (not isinstance(body, dict) or captured is None):
        out = copy.deepcopy(last_good)
        out["stale"] = False
        out["error_code"] = error_code or "CAPTURED_AT_INVALID"
        return out
    assert isinstance(body, dict) and captured is not None
    latest = body.get("last_reset_at", body.get("latest_reset_at"))
    f24 = body.get("forecast_24h_percent")
    f48 = body.get("forecast_48h_percent")
    bad_forecast = any(v is not None and (not isinstance(v, (int, float)) or not 0 <= v <= 100)
                       for v in (f24, f48))
    stale = age_seconds(now, captured) >= 300
    if bad_forecast or error_code is not None or captured > now:
        return {"provider": source, "fetched_at": captured_raw,
                "latest_reset_at": latest,
                "forecast_24h_percent": f24, "forecast_48h_percent": f48,
                "forecast_is_schedule": False, "stale": False,
                "error_code": error_code or ("FORECAST_OUT_OF_RANGE" if bad_forecast
                                             else "FUTURE_CAPTURED_AT")}
    return {"provider": source, "fetched_at": captured_raw,
            "latest_reset_at": latest,
            "forecast_24h_percent": f24, "forecast_48h_percent": f48,
            "forecast_is_schedule": False, "stale": stale, "error_code": None}


def error_code_for(name: str | None) -> str | None:
    if name is None:
        return None
    return {"dns": "DNS_ERROR", "tls": "TLS_ERROR",
            "http_500": "HTTP_500"}.get(name, "TRANSPORT_ERROR")


def adapt(payload: dict) -> list[dict]:
    source = payload["source"]
    events = payload["events"]
    out: list[dict] = []
    last_good = None
    for ev in events:
        now = parse_ts(ev["now"])
        assert now is not None, "event now must be RFC3339"
        body = ev.get("body")
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                body = {"__malformed__": True}
        err = error_code_for(ev.get("error"))
        if source == "fixture":
            if isinstance(body, dict) and "__malformed__" in body:
                snap = copy.deepcopy(last_good) if last_good else {
                    "source": "fixture", "windows": [], "observed_at": None,
                    "stale": False}
                snap["stale"] = False
                snap["error_code"] = "MALFORMED_BODY"
            elif err is not None and last_good is not None:
                # Transport error: keep last-good values, flag the error.
                snap = copy.deepcopy(last_good)
                snap["stale"] = False
                snap["error_code"] = err
            elif (not isinstance(body, dict) or body.get("captured_at") is None) and last_good is None:
                # Missing captured_at on first sight: error snapshot.
                snap = {"source": "fixture", "windows": [],
                        "observed_at": None, "stale": False,
                        "error_code": "CAPTURED_AT_INVALID"}
            else:
                snap = fixture_snapshot(body, now, err, last_good)
            if snap.get("error_code") is None and isinstance(body, dict) and parse_ts(body.get("captured_at")) is not None:
                last_good = copy.deepcopy(snap)
                last_good["error_code"] = None
            elif last_good is None and snap.get("error_code") is None:
                last_good = copy.deepcopy(snap)
            out.append(snap)
        else:
            if isinstance(body, dict) and "__malformed__" in body:
                snap = copy.deepcopy(last_good) if last_good else {
                    "provider": source, "fetched_at": None,
                    "latest_reset_at": None, "forecast_24h_percent": None,
                    "forecast_48h_percent": None, "forecast_is_schedule": False,
                    "stale": False}
                snap["stale"] = False
                snap["error_code"] = "MALFORMED_BODY"
            elif body is None and err is not None and last_good is not None:
                snap = copy.deepcopy(last_good)
                snap["stale"] = False
                snap["error_code"] = err
            else:
                snap = global_snapshot(source, body, now, err, last_good)
            if snap.get("error_code") is None and isinstance(body, dict) and parse_ts(body.get("captured_at")) is not None:
                last_good = copy.deepcopy(snap)
            elif last_good is None and snap.get("error_code") is None:
                last_good = copy.deepcopy(snap)
            out.append(snap)
    return out


def main() -> int:
    raw = sys.stdin.read()
    payload = json.loads(raw)
    snapshots = adapt(payload)
    sys.stdout.write(json.dumps(snapshots, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
