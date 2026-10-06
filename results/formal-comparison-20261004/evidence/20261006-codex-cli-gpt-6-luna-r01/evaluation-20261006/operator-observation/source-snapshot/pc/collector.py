"""Command-line fixture collector. It never contacts an account or provider."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import FixtureCollector, timestamp, utc_now


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    collected = FixtureCollector(args.registry).collect()
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
