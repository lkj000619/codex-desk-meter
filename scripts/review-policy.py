"""Record an explicit operator policy judgment beside a terminal run manifest."""
import argparse
import json

from benchmark_support import read
from policy_review import create_review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--decision", required=True, help="JSON: status, reviewer, reason, user_interventions, intervention_review, evidence [{path, sha256}]")
    args = parser.parse_args()
    try:
        print(json.dumps({"policy_review": str(create_review(args.manifest, read(args.decision)))}))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"policy review rejected: {exc}\n")


if __name__ == "__main__":
    main()
