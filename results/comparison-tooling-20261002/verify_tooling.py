"""Local-only verification. Never invoke a model or access a hardware port."""
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_support import digest, read, save
from reference_inputs import validate_reference
from benchmark import candidate_input_inventory

results = []


def run(name, arguments, expected=0):
    command = [sys.executable, "-X", "utf8", *map(str, arguments)]
    completed = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"), timeout=180)
    (OUT / (name + ".log")).write_bytes(completed.stdout)
    result = {"name": name, "command": command, "exit_code": completed.returncode,
              "expected": expected, "log_sha256": digest(completed.stdout)}
    results.append(result)
    print(name, completed.returncode, flush=True)
    if completed.returncode != expected:
        raise RuntimeError(name + " unexpected exit code; see saved log")
    return completed.stdout.decode("utf-8")


def main():
    suite = run("unittest-final", ["-m", "unittest", "discover", "-s", "scripts/tests", "-v"])
    count = int(re.search(r"Ran (\d+) tests", suite).group(1))
    skipped = int(re.search(r"skipped=(\d+)", suite).group(1)) if "skipped=" in suite else 0
    run("e2e-example", ["scripts/validate-end-to-end-result.py"])
    run("provider-matrix", ["scripts/validate-end-to-end-result.py", "--matrix", "experiments/fixtures/provider-fixture-matrix.json"])
    invalid = read(ROOT / "experiments/examples/end-to-end-result.example.json")
    invalid["product_pass"] = True
    save(OUT / "invalid-product-pass.json", invalid)
    run("negative-product-pass", ["scripts/validate-end-to-end-result.py", "--result", OUT / "invalid-product-pass.json",
                                 "--manifest", "experiments/examples/end-to-end-manifest.example.json", "--evidence-root", ROOT], 1)
    for name in ("comparison.py", "observe-product.py", "evaluate-production.py", "package-evidence.py", "reference_inputs.py", "summarize-benchmark.py"):
        run("help-" + name.removesuffix(".py"), ["scripts/" + name, "--help"])
    reference_path = ROOT / "experiments/reference/codex-7923f96/reference-inputs.json"
    reference, files = validate_reference(reference_path)
    replay = OUT / "reference-oracle.json"
    if replay.exists():
        replay.unlink()  # Only this verifier's generated offline output.
    run("reference-replay", ["scripts/observe-product.py", "--frames", reference_path.parent / "expected-frames.jsonl",
                            "--reference-time", reference["reference_time"], "--schedule", reference_path.parent / "schedule.json", "--output", replay])
    oracle = read(replay)
    assert [item["accepted"] for item in oracle["frames"]] == [True, True]
    assert all(item["source_stale"] for item in oracle["frames"])
    run("send-without-port-rejected", ["scripts/observe-product.py", "--frames", reference_path.parent / "expected-frames.jsonl",
                                      "--send", "--output", OUT / "unused-no-port"], 1)
    # CLI packaging uses a controlled incomplete example, never a real candidate.
    spec = importlib.util.spec_from_file_location("package_fixture", ROOT / "scripts/tests/test_evidence_package.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fixture = module.EvidencePackageTests()
    fixture.setUp()
    try:
        created = json.loads(run("package-create-cli", ["scripts/package-evidence.py", "create", "--directory", fixture.run, "--output", fixture.path]))
        (fixture.run / "checkout").rename(fixture.run / "unavailable-original")
        restored = json.loads(run("package-restore-cli", ["scripts/package-evidence.py", "restore", "--package", fixture.path,
                             "--output", fixture.root / "restored", "--expected-sha256", created["package_manifest_sha256"]]))
        assert restored["result_valid"] and restored["manifest_identity_verified"] and not restored["original_checkout_used"]
        run("package-untrusted-hash-rejected", ["scripts/package-evidence.py", "restore", "--package", fixture.path,
             "--output", fixture.root / "rejected", "--expected-sha256", "0"*64], 1)
    finally:
        fixture.doCleanups()
    inventory = candidate_input_inventory(ROOT)
    markdown = [name for name in inventory["files"] if name.endswith(".md")]
    assert len(markdown) == 3
    assert not any(name.startswith("experiments/reference/") or name == "scripts/comparison_manager.py" for name in inventory["files"])
    links, broken = 0, []
    names = subprocess.check_output(["rg", "--files", "--hidden", "-g", "*.md", "-g", "!.git", "-g", "!.superpowers"], cwd=ROOT, text=True, encoding="utf-8").splitlines()
    for name in names:
        source = ROOT / name
        content = source.read_text(encoding="utf-8-sig")
        for match in re.finditer(r"\[[^\]]*\]\((<[^>]+>|[^)]+)\)", content):
            target = match.group(1).strip().strip("<>")
            if target.startswith(("http:", "https:", "mailto:", "app:", "#")) or not target:
                continue
            target = unquote(target.split("#", 1)[0])
            if not target:
                continue
            links += 1
            path = Path(target)
            if not path.is_absolute():
                path = source.parent / path
            if not path.exists():
                broken.append({"source": name, "target": target})
    if broken:
        raise RuntimeError("broken links: " + json.dumps(broken, ensure_ascii=True))
    check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True)
    assert check.returncode == 0, check.stdout.decode("utf-8")
    save(OUT / "evidence.json", {"verified_on": "2026-10-02", "tests": count, "passed": count-skipped, "skipped": skipped,
          "checks": results, "reference_inputs_sha256": digest(reference_path.read_bytes()),
          "reference_files": {name: digest((reference_path.parent / name).read_bytes()) for name in files},
          "reference_sequences": reference["receiver_accepted_sequences"], "reference_offsets": reference["monotonic_offsets"],
          "reference_source_status": reference["source_status"], "restoration": restored,
          "candidate_files": len(inventory["files"]), "candidate_markdown": markdown, "markdown_files": len(names),
          "local_links_checked": links, "broken_links": broken, "git_diff_check": "pass",
          "model_calls": 0, "hardware_accessed": False, "scope": "Operator tooling only; controlled subprocess/adapter/media tests are not product or live capability evidence"})
    print(json.dumps({"tests": count, "passed": count-skipped, "skipped": skipped, "links": links, "status": "verified"}))


if __name__ == "__main__":
    main()
