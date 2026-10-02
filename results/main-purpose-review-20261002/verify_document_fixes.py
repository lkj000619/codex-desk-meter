"""Offline verification of document fixes; writes only sibling evidence/log files.

Run: python results/main-purpose-review-20261002/verify_document_fixes.py
No candidate agent, serial access, device flash, or network operation is performed.
"""
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
import benchmark


def command(args):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return {"argv": args, "exit_code": result.returncode,
            "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def read_json(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8-sig"))


def document_links():
    names = set(subprocess.check_output(["git", "ls-files"], cwd=ROOT,
                                       text=True, encoding="utf-8").splitlines())
    names.update(["AGENTS.md", "docs/plans/2026-10-02-experiment-contract-remediation.md"])
    names.update(path.relative_to(ROOT).as_posix() for path in (ROOT / "results").rglob("*.md"))
    documents = sorted(name for name in names if name.endswith(".md") and (ROOT / name).is_file())
    links, obsolete = [], []
    for name in documents:
        content = (ROOT / name).read_text(encoding="utf-8-sig")
        for match in re.finditer(r"\[[^\]\n]+\]\((<[^>]+>|[^)\n]+)\)", content):
            target = match.group(1).strip("<>")
            if re.match(r"^(https?://|mailto:|#)", target):
                continue
            target = unquote(target.split("#")[0])
            path = Path(target) if re.match(r"^[A-Za-z]:/", target) else ROOT / Path(name).parent / target
            item = {"file": name, "line": content.count("\n", 0, match.start()) + 1,
                    "target": target, "exists": path.exists()}
            links.append(item)
            if "superpowers/plans/" in target:
                obsolete.append(item)
    return {"document_count": len(documents), "local_file_links": len(links),
            "missing_links": [item for item in links if not item["exists"]],
            "obsolete_plan_links": obsolete,
            "scope": "existing tracked MD, new AGENTS/plan, and local results MD; file targets only"}


def input_preview(head):
    profile = ROOT / "experiments/config/verified-profiles-candidate/codex-cli-sol-medium.candidate.json"
    current = benchmark.candidate_input_inventory(ROOT)
    with tempfile.TemporaryDirectory(prefix="meter-doc-inputs-") as temporary:
        snapshot = Path(temporary)
        benchmark._extract_archive(snapshot, head)
        before = benchmark.candidate_input_inventory(snapshot)
        old_hashes = benchmark.input_bundle_hashes(snapshot, profile, head, head)
        changed = []
        for name in before["files"]:
            if name.endswith(".md"):
                text = (ROOT / name).read_text(encoding="utf-8")
                (snapshot / name).write_text(text, encoding="utf-8", newline="\n")
                if benchmark.digest((snapshot / name).read_bytes()) != before["files"][name]:
                    changed.append(name)
        preview = benchmark.input_bundle_hashes(snapshot, profile, head, head)
    return {"candidate_files": len(current["files"]),
            "candidate_markdown": [name for name in current["files"] if name.endswith(".md")],
            "modified_candidate_markdown": changed, "head_hashes": old_hashes,
            "normalized_document_preview_hashes": preview,
            "bundle_hash_changed": old_hashes["input_bundle_sha256"] != preview["input_bundle_sha256"],
            "scope": "preview uses HEAD snapshot plus LF-normalized candidate MD; no new baseline frozen"}


def fixture_values():
    codex = read_json("experiments/fixtures/providers/codex-percent-window.json")
    claude = read_json("experiments/fixtures/providers/claude-code-windows.json")
    history = read_json("experiments/fixtures/codex-resets-history.json")
    captured = datetime.fromisoformat(history["captured_at"].replace("Z", "+00:00"))
    reset = datetime.fromisoformat(history["latest_reset_at"].replace("Z", "+00:00"))
    elapsed = int((captured - reset).total_seconds())
    expected_codex = [(window["percent_used"], window["percent_remaining"]) for window in codex["windows"]]
    expected_claude = [(window["percent_used"], window["percent_remaining"]) for window in claude["windows"]]
    content = (ROOT / "docs/experiments/evaluation-contract.md").read_text(encoding="utf-8")
    assert expected_codex == [(20, 80)]
    assert expected_claude == [(35, 65), (40, 60), (10, 90)]
    assert elapsed == 226687 and f"{elapsed:,}" in content
    return {"codex_percent_used_remaining": expected_codex,
            "claude_percent_used_remaining": expected_claude, "global_elapsed_seconds": elapsed}


def main():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    evidence = {"head": head, "links": document_links(), "inputs": input_preview(head),
                "fixture_values": fixture_values()}
    checks = []
    checks.append(command([sys.executable, "scripts/validate-end-to-end-result.py"]))
    checks.append(command([sys.executable, "scripts/validate-end-to-end-result.py", "--matrix",
                           "experiments/fixtures/provider-fixture-matrix.json"]))
    checks.append(command([sys.executable, "scripts/validate-end-to-end-result.py", "--result",
                           "experiments/examples/invalid/invalid-product-pass.example.json"]))
    evidence["schema_checks"] = checks
    evidence["diff_check"] = command(["git", "-c", "core.safecrlf=false", "diff", "--check"])
    preserved = command(["git", "diff", "--name-only", "--", "scripts", "experiments/schema",
                         "experiments/fixtures", "docs/experiments/evidence", "docs/archive"])
    evidence["preserved_code_schema_fixture_evidence_archive"] = not preserved["stdout"]
    unit = command([sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests", "-v"])
    (OUTPUT / "document-fixes-unittest.log").write_text(unit["stdout"] + "\n" + unit["stderr"] + "\n",
                                                       encoding="utf-8")
    evidence["unittest"] = {"argv": unit["argv"], "exit_code": unit["exit_code"],
                            "tail": unit["stderr"].splitlines()[-5:]}
    failures = []
    if evidence["links"]["missing_links"] or evidence["links"]["obsolete_plan_links"]:
        failures.append("local file links")
    if (len(evidence["inputs"]["candidate_markdown"]) != 3
            or not evidence["inputs"]["bundle_hash_changed"]):
        failures.append("candidate inventory/hash preview")
    if checks[0]["exit_code"] or checks[1]["exit_code"] or checks[2]["exit_code"] != 1:
        failures.append("schema checks")
    if evidence["diff_check"]["exit_code"] or not evidence["preserved_code_schema_fixture_evidence_archive"]:
        failures.append("change scope/whitespace")
    if (ROOT / "docs/superpowers").exists():
        failures.append("old plan directory")
    if unit["exit_code"]:
        failures.append("existing unit suite")
    evidence["failures"] = failures
    (OUTPUT / "document-fixes-evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
                                                        encoding="utf-8")
    print(json.dumps({"failures": failures, "links": evidence["links"],
                      "inputs": {key: value for key, value in evidence["inputs"].items() if "hashes" not in key},
                      "fixture_values": evidence["fixture_values"], "unittest": evidence["unittest"]},
                     ensure_ascii=False, indent=2))
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
