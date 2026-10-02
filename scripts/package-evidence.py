"""Create or restore a portable operator evidence package."""
import argparse
import json
import subprocess
from pathlib import Path

from evidence_package import create_package, restore_package


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("--directory", required=True, type=Path)
    create.add_argument("--output", required=True, type=Path)
    restore = sub.add_parser("restore")
    restore.add_argument("--package", required=True, type=Path)
    restore.add_argument("--output", required=True, type=Path)
    restore.add_argument("--expected-sha256", required=True, help="trusted manifest hash recorded when packaging")
    args = parser.parse_args(argv)
    try:
        output = (create_package(args.directory, args.output) if args.command == "create"
                  else restore_package(args.package, args.output, args.expected_sha256))
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "rejected", "reason": str(error)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
