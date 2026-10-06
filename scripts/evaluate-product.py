"""Operator black-box regression against an adapter linked to production code.

The adapter receives {source, events:[{now,body,error}]} on stdin and returns
one normalized snapshot per event as a JSON array. See evaluation-contract.md.
"""
import argparse
import copy
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from benchmark_support import ROOT, digest, read, save


def at(stamp, seconds):
    return (datetime.fromisoformat(stamp.replace("Z", "+00:00")) + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def cases():
    for filename in ("personal-usage.json", "codex-reset-forecast.json", "codex-resets-history.json"):
        body = read(ROOT / "experiments/fixtures" / filename)
        source = body["source"]
        stamp = body["captured_at"]
        def event(seconds=0, payload=body, error=None):
            return dict(now=at(stamp, seconds), body=payload, error=error)
        yield filename + ":freshness", source, [event(n) for n in (0, 299, 300)], [False, False, True], body, "freshness"
        bad = copy.deepcopy(body)
        bad["captured_at"] = "invalid-date"
        missing = copy.deepcopy(body)
        del missing["captured_at"]
        future = copy.deepcopy(body)
        future["captured_at"] = at(stamp, 60)
        malformed = [bad, missing, future, "{broken", ""]
        if source == "fixture":
            invalid = copy.deepcopy(body)
            invalid["windows"][0]["percent_used"] = 101
            malformed.append(invalid)
        if source == "codex-reset.com":
            invalid = copy.deepcopy(body)
            invalid["forecast_24h_percent"] = -1
            malformed.append(invalid)
        for index, invalid in enumerate(malformed):
            yield filename + f":invalid-{index}", source, [event(), event(1, invalid), event(2)], [False]*3, body, "recovery"
        for error in ("dns", "tls", "http_500"):
            yield filename + ":" + error, source, [event(), event(1, None, error), event(2)], [False]*3, body, "recovery"


def check(outputs, stale, body, mode):
    if not isinstance(outputs, list) or len(outputs) != 3:
        raise ValueError("expected three snapshots")
    for i, snapshot in enumerate(outputs):
        if snapshot["stale"] is not stale[i]:
            raise ValueError(f"stale mismatch at event {i}")
        expected_error = mode == "recovery" and i == 1
        if bool(snapshot["error_code"]) != expected_error:
            raise ValueError(f"error/recovery mismatch at event {i}")
        if body["source"] == "fixture":
            if snapshot["source"] != "fixture" or snapshot["windows"] != body["windows"]:
                raise ValueError("usage values/nulls not preserved")
            if snapshot["observed_at"] != body["captured_at"]:
                raise ValueError("observation time changed")
        else:
            expected = dict(provider=body["source"], fetched_at=body["captured_at"],
                            latest_reset_at=body.get("last_reset_at", body.get("latest_reset_at")),
                            forecast_24h_percent=body.get("forecast_24h_percent"),
                            forecast_48h_percent=body.get("forecast_48h_percent"), forecast_is_schedule=False)
            for key, value in expected.items():
                if snapshot[key] != value:
                    raise ValueError(f"{key} not preserved")


def evaluate(argv, cwd):
    results = []
    for name, source, events, stale, body, mode in cases():
        try:
            p = subprocess.run(argv, cwd=cwd, input=json.dumps(dict(source=source, events=events)),
                               encoding="utf-8", capture_output=True, timeout=30, check=True)
            check(json.loads(p.stdout), stale, body, mode)
            results.append(dict(case=name, status="pass"))
        except (ValueError, KeyError, TypeError, subprocess.SubprocessError, OSError) as exc:
            results.append(dict(case=name, status="fail", reason=str(exc)))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter-config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    config = read(args.adapter_config)
    # Review must identify the production modules and link/build evidence.
    root = Path(config["checkout"]).resolve()
    for name, expected in config["production_files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or digest(path.read_bytes()) != expected:
            raise ValueError(f"production provenance mismatch: {name}")
    if not config["production_files"] or not config.get("reviewer") or not config.get("link_evidence"):
        raise ValueError("operator review of production linkage required")
    evidence = Path(config["link_evidence"])
    if digest(evidence.read_bytes()) != config["link_evidence_sha256"]:
        raise ValueError("link evidence changed")
    results = evaluate(config["argv"], root)
    save(args.output, dict(evaluation_version=1, adapter_config_sha256=digest(args.adapter_config.read_bytes()),
                          cases=results, hardware_status="not_run", product_pass=False))
    return int(any(r["status"] != "pass" for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
