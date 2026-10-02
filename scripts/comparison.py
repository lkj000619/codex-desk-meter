"""Manage an operator-owned comparison without starting a model implicitly."""
import argparse
import json
from pathlib import Path

import comparison_manager as manager
from benchmark_support import read, save


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="attach a prepared benchmark run to frozen reference inputs")
    init.add_argument("--ledger", required=True, type=Path)
    init.add_argument("--directory", required=True, type=Path)
    init.add_argument("--reference-inputs", required=True, type=Path)
    follow = sub.add_parser("prepare-next", help="prepare own previous source; never executes it")
    follow.add_argument("--ledger", required=True, type=Path)
    follow.add_argument("--root", required=True, type=Path)
    follow.add_argument("--feedback", required=True, type=Path)
    review = sub.add_parser("review", help="freeze terminal source and record RM1-RM5 operator evidence")
    review.add_argument("--directory", required=True, type=Path)
    review.add_argument("--report", required=True, type=Path)
    recover = sub.add_parser("reconcile", help="join an interrupted ledger to an existing terminal manifest")
    recover.add_argument("--directory", required=True, type=Path)
    show = sub.add_parser("show")
    show.add_argument("--ledger", required=True, type=Path)
    stop = sub.add_parser("stop", help="prevent further rounds; an active process still needs operator interruption")
    stop.add_argument("--ledger", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            output = manager.init_comparison(args.ledger, args.directory, args.reference_inputs)
        elif args.command == "prepare-next":
            output = {"directory": str(manager.prepare_followup(args.ledger, args.root, read(args.feedback)))}
        elif args.command == "review":
            manager.review_run(args.directory, read(args.report))
            output = {"reviewed": True}
        elif args.command == "reconcile":
            manager.finish_run(args.directory)
            output = {"reconciled": True}
        elif args.command == "stop":
            with manager.locked(args.ledger):
                output = manager._load(args.ledger)
                output["state"] = "stopped"
                save(args.ledger, output)
        else:
            output = manager._load(args.ledger)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({"status": "rejected", "reason": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
