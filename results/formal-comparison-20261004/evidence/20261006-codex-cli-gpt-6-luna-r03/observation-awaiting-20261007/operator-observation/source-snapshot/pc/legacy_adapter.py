"""Offline stdin/stdout compatibility seam for the fixed legacy fixture contract."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pc.pipeline import CollectionError, normalize_global_reset, normalize_legacy_usage, parse_time


def _failure_code(event: dict[str, Any], exc: Exception | None = None) -> str:
    external = event.get("error")
    if external in ("dns", "tls", "http_500"):
        return {"dns": "DNS_FAILURE", "tls": "TLS_FAILURE", "http_500": "HTTP_500"}[external]
    if isinstance(exc, CollectionError):
        return exc.code
    return "ADAPTER_FAILURE"


def _normalize(source: str, body: Any, reference: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise CollectionError("INPUT_INVALID", "body must be a JSON object")
    if source == "fixture":
        if body.get("source") != source:
            raise CollectionError("SOURCE_ID_MISMATCH", "fixture source identity changed")
        snapshot = normalize_legacy_usage(body, reference_time=reference)
        return {
            "source": "fixture",
            "windows": copy.deepcopy(body.get("windows", [])),
            "observed_at": body.get("captured_at"),
            "stale": snapshot["stale"],
            "error_code": None,
        }
    reset = normalize_global_reset(body, reference)
    if reset["source"] != source:
        raise CollectionError("SOURCE_ID_MISMATCH", "global source identity changed")
    return {
        "provider": reset["source"],
        "fetched_at": reset["captured_at"],
        "latest_reset_at": reset["latest_reset_at"],
        "forecast_24h_percent": reset["forecast_24h_percent"],
        "forecast_48h_percent": reset["forecast_48h_percent"],
        "forecast_is_schedule": False,
        "stale": reset["stale"],
        "error_code": reset["error_code"],
    }


def process_request(request: Any) -> list[dict[str, Any]]:
    if not isinstance(request, dict) or not isinstance(request.get("source"), str):
        raise CollectionError("INPUT_INVALID", "request requires a source string and events array")
    source = request["source"]
    if source not in {"fixture", "codex-reset.com", "codex-resets.com"}:
        raise CollectionError("SOURCE_UNSUPPORTED", "source is not a fixed offline adapter")
    events = request.get("events")
    if not isinstance(events, list):
        raise CollectionError("INPUT_INVALID", "events must be an array")
    last_good: dict[str, Any] | None = None
    outputs: list[dict[str, Any]] = []
    for index, event in enumerate(events):
        if not isinstance(event, dict) or not isinstance(event.get("now"), str):
            raise CollectionError("INPUT_INVALID", f"events[{index}] requires an RFC3339 now")
        reference = parse_time(event["now"], f"events[{index}].now")
        error: Exception | None = None
        if event.get("error") is not None:
            error = CollectionError("SOURCE_ERROR", "source request failed")
            code = _failure_code(event, error)
        else:
            try:
                current = _normalize(source, event.get("body"), reference)
            except (CollectionError, KeyError, TypeError, ValueError) as exc:
                error = exc
                code = _failure_code(event, exc)
            else:
                last_good = copy.deepcopy(current)
                outputs.append(current)
                print(f"source={source} event={index} status=ok stale={str(current['stale']).lower()}", file=sys.stderr)
                continue

        if last_good is None:
            if source == "fixture":
                current = {"source": source, "windows": [], "observed_at": None, "stale": False}
            else:
                current = {
                    "provider": source, "fetched_at": None, "latest_reset_at": None,
                    "forecast_24h_percent": None, "forecast_48h_percent": None,
                    "forecast_is_schedule": False, "stale": False,
                }
        else:
            current = copy.deepcopy(last_good)
        current["error_code"] = code
        outputs.append(current)
        print(f"source={source} event={index} status=error code={code} stale={str(current['stale']).lower()}", file=sys.stderr)
    return outputs


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        request = json.loads(sys.stdin.read())
        outputs = process_request(request)
    except (json.JSONDecodeError, CollectionError, UnicodeError) as exc:
        print(f"legacy adapter error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(outputs, ensure_ascii=False, allow_nan=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
