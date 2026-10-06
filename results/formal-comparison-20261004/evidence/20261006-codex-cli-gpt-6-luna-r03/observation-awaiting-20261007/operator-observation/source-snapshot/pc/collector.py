"""Command-line fixture collector. It never contacts an account or provider."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import FixtureCollector, parse_time, timestamp, utc_now


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--profile", choices=("all", "common"), default="all")
    parser.add_argument("--reference-time", help="fixed RFC3339 UTC for reproducible fixture collection")
    args = parser.parse_args()
    reference = parse_time(args.reference_time, "reference_time") if args.reference_time else None
    collector = FixtureCollector(args.registry)
    if args.profile == "common":
        if reference is None:
            parser.error("--profile common requires --reference-time")
        collected = collector.collect_common(reference)
    else:
        collected = collector.collect(reference)
    result = {
        "captured_at": timestamp(utc_now()),
        "payload": collected.payload,
        "failures": collected.failures,
    }
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 1 if collected.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
