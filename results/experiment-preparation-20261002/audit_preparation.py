"""Restore and verify preparation bytes. Never launches a provider or a board."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def extract(archive, root):
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            target = (root / item.filename).resolve()
            if not target.is_relative_to(root.resolve()):
                raise ValueError("unsafe archive path")
        z.extractall(root)


def audit(package, destination):
    if destination.exists():
        raise ValueError("restore destination must be new; preserve earlier audits")
    destination.mkdir(parents=True)
    extract(package, destination)
    inventory = read(destination / "package-inventory.json")
    for relative, expected in inventory["files"].items():
        if sha(destination / relative) != expected:
            raise ValueError("package byte mismatch: " + relative)
    extract(destination / "operator-source.zip", destination / "operator")
    operator = destination / "operator"
    # Import only the recovered frozen source, without the original repository.
    sys.path.insert(0, str(operator / "scripts"))
    import benchmark
    from benchmark_support import validate_operator, validate_schema

    source_inventory = read(destination / "operator-source-inventory.json")
    for relative, expected in source_inventory["files"].items():
        if sha(operator / relative) != expected:
            raise ValueError("frozen operator source mismatch: " + relative)
    freeze = read(destination / "evidence/freeze.json")
    outcomes = []
    common = None
    for row in freeze["runs"]:
        target = row["target"]
        run = destination / "runs" / target
        original = read(run / "run-manifest.json")
        manifest = copy.deepcopy(original)
        profile = read(run / "profile.json")
        validate_schema(original, "run-manifest.schema.json")
        validate_operator(original)
        benchmark.validate_resolved_profile(profile)
        assert original["operator"]["status"] == "prepared"
        assert original["execution"]["started_at"] is None
        assert original["outputs"]["implementation_commit"] is None
        checkout = run / "checkout"
        extract(run / "candidate-source.zip", checkout)
        subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
        # Preserve original working bytes, including CRLF generated metadata;
        # reproduce the original Windows index normalization without checkout.
        subprocess.run(["git", "config", "core.autocrlf", "true"], cwd=checkout, check=True)
        subprocess.run(["git", "config", "core.safecrlf", "false"], cwd=checkout, check=True)
        subprocess.run(["git", "add", "."], cwd=checkout, check=True)
        tree = subprocess.check_output(["git", "write-tree"], cwd=checkout, text=True).strip()
        raw_commit = (run / "candidate-commit.raw").read_bytes()
        assert raw_commit.splitlines()[0] == ("tree " + tree).encode("ascii")
        commit = subprocess.check_output(["git", "hash-object", "-w", "-t", "commit", "--stdin"],
                                         input=raw_commit, cwd=checkout).decode().strip()
        assert commit == original["operator"]["local_base_commit"]
        # Original parent history is intentionally omitted; retain the original
        # commit as an explicitly shallow snapshot, not a newly authored commit.
        (checkout / ".git/shallow").write_text(commit + "\n", encoding="ascii")
        subprocess.run(["git", "update-ref", "HEAD", commit], cwd=checkout, check=True)
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=checkout, text=True).strip()
        assert head == original["operator"]["local_base_commit"]
        assert not subprocess.check_output(["git", "status", "--porcelain"], cwd=checkout)
        manifest["execution"]["worktree"] = str(checkout)
        benchmark.verify_agent_inputs(run, manifest)
        benchmark.verify_evidence(original, run)
        assert sha(run / "profile.json") == original["agent"]["configuration_sha256"]
        assert sha(run / "prompt.txt") == original["operator"]["delivered_prompt_sha256"]
        files = read(run / "candidate-inputs.json")["files"]
        assert len(files) == 57
        assert len([name for name in files if name.endswith(".md")]) == 3
        if common is None:
            common = files
        assert files == common
        ledger = read(run / "comparison-ledger.json")
        assert ledger["base_commit"] == freeze["baseline_commit"]
        assert ledger["profile_sha256"] == original["execution"]["profile_sha256"]
        assert ledger["input_bundle_sha256"] == original["execution"]["input_bundle_sha256"]
        assert ledger["limits"] == freeze["limits_per_candidate"]
        assert ledger["runs"][0]["reserved_seconds"] == 0
        assert ledger["runs"][0]["elapsed_seconds"] is None
        receipt_root = destination / "evidence/receipts"
        receipt = read(receipt_root / (target + ".json"))
        benchmark.validate_preflight_receipt(receipt, original, profile, receipt_root)
        capability=read(destination / "evidence/capability-summary.json")[target]
        for relative,expected in capability["artifact_sha256"].items():
            assert sha(receipt_root / "evidence/probes" / row["selected_probe"] / "artifacts" / relative) == expected
        outcomes.append({"target": target, "receipt": "pass", "candidate_input_count": len(files),
                         "candidate_commit": head, "status": "prepared", "product_executed": False})
    result = {"scope": "independent preparation restore; no provider execution or hardware operation",
              "package_sha256": sha(package), "baseline_commit": freeze["baseline_commit"],
              "package_files_checked": len(inventory["files"]), "source_files_checked": len(source_inventory["files"]),
              "runs": outcomes, "result": "pass", "original_repository_required": False}
    (destination / "audit-result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.package.resolve(), args.destination.resolve()), indent=2))
