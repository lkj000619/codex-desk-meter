"""Send one freshly collected offline snapshot to an explicitly selected port."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import FixtureCollector, parse_time
from .sender import send_payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="operator-selected COM port")
    parser.add_argument("--device-alias", required=True)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--raw-log", type=Path)
    parser.add_argument("--device-log", type=Path,
                        help="append optional ESP_LOG lines; these are diagnostics, not an ACK")
    parser.add_argument("--capture-device-log-seconds", type=float, default=2.0,
                        help="seconds to read ESP_LOG diagnostics after each write; 0 disables capture")
    parser.add_argument("--profile", choices=("all", "common"), default="all")
    parser.add_argument("--reference-time", help="fixed RFC3339 UTC for reproducible fixture normalization")
    parser.add_argument("--sent-at", help="RFC3339 UTC placed in cdm/1; defaults to current UTC")
    parser.add_argument("--initialize-empty-receiver", action="store_true",
                        help="first run only, after confirming that this receiver has no accepted sequence")
    args = parser.parse_args()
    reference = parse_time(args.reference_time, "reference_time") if args.reference_time else None
    if args.profile == "common" and reference is None:
        parser.error("--profile common requires --reference-time")
    collector = FixtureCollector(args.registry)
    collected = collector.collect_common(reference) if args.profile == "common" else collector.collect(reference)
    if collected.failures:
        print(json.dumps({"status": "collection_error", "failures": collected.failures}, ensure_ascii=False))
        return 2
    try:
        result = send_payload(collected.payload, args.port, args.device_alias, args.state,
                              args.raw_log, args.initialize_empty_receiver, sent_at=args.sent_at,
                              capture_device_logs_seconds=args.capture_device_log_seconds,
                              device_log_path=args.device_log)
    except (RuntimeError, ValueError, OSError) as exc:
        print(json.dumps({"status": "send_error", "message": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
