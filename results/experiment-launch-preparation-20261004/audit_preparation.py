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

    source_files = [p for p in operator.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    freeze = read(destination / "evidence/freeze.json")
    outcomes = []
    common = None
    for row in freeze["series"]:
        target = Path(row["profile"]).stem
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
        subprocess.run(["git", "clone", "--quiet", str(run/'candidate-source.bundle'), str(checkout)], check=True)
        extract(run / "candidate-source.zip", checkout)
        subprocess.run(["git", "remote", "remove", "origin"], cwd=checkout, check=True)
        # Refresh Git's cached CRLF classification after restoring raw bytes.
        # The normalized tree must remain identical to the original commit.
        subprocess.run(["git", "add", "--all"], cwd=checkout, check=True, capture_output=True)
        tree = subprocess.check_output(["git", "write-tree"], cwd=checkout, text=True).strip()
        assert tree == subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=checkout, text=True).strip()
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=checkout, text=True).strip()
        assert head == original["operator"]["local_base_commit"]
        assert subprocess.check_output(["git", "rev-list", "--count", "HEAD"], cwd=checkout, text=True).strip() == "1"
        assert not subprocess.check_output(["git", "status", "--porcelain"], cwd=checkout)
        manifest["execution"]["worktree"] = str(checkout)
        benchmark.verify_agent_inputs(run, manifest)
        benchmark.verify_evidence(original, run)
        from operator_baseline import verify
        assert verify(original, run)
        assert original['operator']['policy_review_required'] is True
        assert sha(run / "profile.json") == original["agent"]["configuration_sha256"]
        assert sha(run / "prompt.txt") == original["operator"]["delivered_prompt_sha256"]
        files = read(run / "candidate-inputs.json")["files"]
        assert len(files) == 57
        assert len([name for name in files if name.endswith(".md")]) == 3
        if common is None:
            common = files
        assert files == common
        ledger = read(run / "comparison-ledger.json")
        assert ledger["base_commit"] == freeze["base_commit"]
        assert ledger["profile_sha256"] == original["execution"]["profile_sha256"]
        assert ledger["input_bundle_sha256"] == original["execution"]["input_bundle_sha256"]
        assert ledger["limits"] == {"initial_seconds":7200,"remediation_seconds":7200,"remediation_rounds":3}
        assert ledger["runs"][0]["reserved_seconds"] == 0
        assert ledger["runs"][0]["elapsed_seconds"] is None
        from comparison_manager import _load, _entry
        ledger['reference_inputs'] = str(run/'reference/reference-inputs.json')
        ledger['runs'][0]['directory'] = str(run)
        recovered_ledger = run/'recovered-ledger.json'
        recovered_ledger.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
        manifest['operator']['comparison']['ledger'] = str(recovered_ledger)
        _entry(_load(recovered_ledger),manifest,run)
        assert sha(run/'common-task.txt') == ledger['common_task_sha256']
        receipt_root = destination / "evidence"
        assert sha(receipt_root / (target + "-receipt.json")) == row['receipt_sha256']
        receipt = read(receipt_root / (target + "-receipt.json"))
        benchmark.validate_preflight_receipt(receipt, original, profile, receipt_root)
        capability=read(destination / "evidence/capability-summary.json")[target]
        for relative,expected in capability["artifact_sha256"].items():
            assert sha(receipt_root / "evidence/probes" / capability["probe"] / "artifacts" / relative) == expected
        outcomes.append({"target": target, "receipt": "pass", "candidate_input_count": len(files),
                         "candidate_commit": head, "status": "prepared", "product_executed": False})
    result = {"scope": "independent preparation restore; no provider execution or hardware operation",
              "package_sha256": sha(package), "baseline_commit": freeze["base_commit"],
              "package_files_checked": len(inventory["files"]), "source_files_checked": len(source_files),
              "runs": outcomes, "result": "pass", "original_repository_required": False}
    (destination / "audit-result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.package.resolve(), args.destination.resolve()), indent=2))
