"""Run a reviewed production adapter or join operator optical annotations."""
import argparse
import json
from pathlib import Path

from benchmark_support import read
from production_evaluation import join_optical, run_adapter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    trace = commands.add_parser("trace")
    for name in ("checkout", "adapter", "stimulus", "output"):
        trace.add_argument("--" + name, type=Path, required=True)
    optical = commands.add_parser("optical")
    for name in ("capture", "annotations", "output"):
        optical.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "trace":
            report = run_adapter(args.checkout, args.adapter, args.stimulus, args.output)
            passed = report["conformance_pass"]
        else:
            report = join_optical(args.capture, read(args.annotations))
            with args.output.open("x", encoding="utf-8") as output:
                output.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
            passed = report["optical_status"] == "pass"
        print(json.dumps({"scope_pass": passed, "product_pass": False}))
        return 0 if passed else 1
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"status": "rejected", "reason": str(error)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
