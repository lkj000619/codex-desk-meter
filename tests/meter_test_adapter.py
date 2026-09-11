"""Host evaluation adapter for Codex Desk Meter Version 2.
Implements the contract defined in docs/experiments/evaluation-contract.md.
"""
import sys
import json
import copy
from datetime import datetime

def parse_iso(ts):
    if not ts or not isinstance(ts, str):
        return None
    try:
        clean = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except Exception:
        return None

def is_valid_iso(ts):
    return parse_iso(ts) is not None

def main():
    raw = sys.stdin.read()
    if not raw.strip():
        sys.stderr.write("adapter: empty input\n")
        sys.exit(1)

    req = json.loads(raw)
    source = req.get("source")
    events = req.get("events", [])

    snapshots = []
    current_snap = None

    for evt in events:
        now_str = evt.get("now")
        body = evt.get("body")
        err = evt.get("error")

        now_dt = parse_iso(now_str)

        if err:
            # Outage event: preserve last known good data, set error_code
            if current_snap is None:
                current_snap = {}
            snap = copy.deepcopy(current_snap)
            snap["error_code"] = err
            # Stale status for outage
            obs_dt = parse_iso(snap.get("observed_at") or snap.get("fetched_at"))
            if now_dt and obs_dt:
                snap["stale"] = (now_dt - obs_dt).total_seconds() >= 300
            else:
                snap["stale"] = False
            snapshots.append(snap)
            continue

        # Payload validation
        if not isinstance(body, dict):
            # broken json, empty string, etc.
            if current_snap is None:
                current_snap = {}
            snap = copy.deepcopy(current_snap)
            snap["error_code"] = "parse_error"
            obs_dt = parse_iso(snap.get("observed_at") or snap.get("fetched_at"))
            if now_dt and obs_dt:
                snap["stale"] = (now_dt - obs_dt).total_seconds() >= 300
            else:
                snap["stale"] = False
            snapshots.append(snap)
            continue

        cap_str = body.get("captured_at")
        cap_dt = parse_iso(cap_str)
        if not cap_dt or not is_valid_iso(cap_str):
            # bad or missing date
            snap = copy.deepcopy(current_snap) if current_snap else {}
            snap["error_code"] = "invalid_date"
            obs_dt = parse_iso(snap.get("observed_at") or snap.get("fetched_at"))
            if now_dt and obs_dt:
                snap["stale"] = (now_dt - obs_dt).total_seconds() >= 300
            else:
                snap["stale"] = False
            snapshots.append(snap)
            continue

        if now_dt and (now_dt < cap_dt):
            # future date
            snap = copy.deepcopy(current_snap) if current_snap else {}
            snap["error_code"] = "future_date"
            obs_dt = parse_iso(snap.get("observed_at") or snap.get("fetched_at"))
            if now_dt and obs_dt:
                snap["stale"] = (now_dt - obs_dt).total_seconds() >= 300
            else:
                snap["stale"] = False
            snapshots.append(snap)
            continue

        # Check range errors
        range_err = False
        if source == "fixture":
            windows = body.get("windows", [])
            for w in windows:
                pu = w.get("percent_used")
                pr = w.get("percent_remaining")
                if pu is not None and (pu < 0 or pu > 100):
                    range_err = True
                    break
                if pr is not None and (pr < 0 or pr > 100):
                    range_err = True
                    break
        elif source == "codex-reset.com":
            f24 = body.get("forecast_24h_percent")
            f48 = body.get("forecast_48h_percent")
            if f24 is not None and (f24 < 0 or f24 > 100):
                range_err = True
            if f48 is not None and (f48 < 0 or f48 > 100):
                range_err = True

        if range_err:
            snap = copy.deepcopy(current_snap) if current_snap else {}
            snap["error_code"] = "out_of_range"
            obs_dt = parse_iso(snap.get("observed_at") or snap.get("fetched_at"))
            if now_dt and obs_dt:
                snap["stale"] = (now_dt - obs_dt).total_seconds() >= 300
            else:
                snap["stale"] = False
            snapshots.append(snap)
            continue

        # Valid payload! Update current_snap
        stale = False
        if now_dt and cap_dt:
            stale = (now_dt - cap_dt).total_seconds() >= 300

        if source == "fixture":
            current_snap = {
                "source": body.get("source", "fixture"),
                "observed_at": body.get("captured_at"),
                "windows": copy.deepcopy(body.get("windows", [])),
                "stale": stale,
                "error_code": None
            }
        else:
            current_snap = {
                "provider": body.get("source"),
                "latest_reset_at": body.get("last_reset_at") if "last_reset_at" in body else body.get("latest_reset_at"),
                "fetched_at": body.get("captured_at"),
                "forecast_24h_percent": body.get("forecast_24h_percent"),
                "forecast_48h_percent": body.get("forecast_48h_percent"),
                "forecast_is_schedule": False,
                "stale": stale,
                "error_code": None
            }

        snapshots.append(copy.deepcopy(current_snap))

    print(json.dumps(snapshots))

if __name__ == "__main__":
    main()
