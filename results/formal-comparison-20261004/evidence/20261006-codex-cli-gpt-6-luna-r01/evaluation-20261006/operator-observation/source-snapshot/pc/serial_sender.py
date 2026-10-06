"""Send one freshly collected offline snapshot to an explicitly selected port."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import FixtureCollector
from .sender import send_payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="operator-selected COM port")
    parser.add_argument("--device-alias", required=True)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--raw-log", type=Path)
    parser.add_argument("--initialize-empty-receiver", action="store_true",
                        help="first run only, after confirming that this receiver has no accepted sequence")
    args = parser.parse_args()
    collected = FixtureCollector(args.registry).collect()
    if collected.failures:
        print(json.dumps({"status": "collection_error", "failures": collected.failures}, ensure_ascii=False))
        return 2
    try:
        result = send_payload(collected.payload, args.port, args.device_alias, args.state,
                              args.raw_log, args.initialize_empty_receiver)
    except (RuntimeError, ValueError, OSError) as exc:
        print(json.dumps({"status": "send_error", "message": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
