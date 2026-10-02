"""Offline evidence for the 2026-10-02 main review; never launches agents or opens serial.

Run from any directory with: python <path-to-this-file>
Only review evidence in this directory and temporary files are written.
"""
from __future__ import annotations

import collections
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from unittest.mock import patch
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
import benchmark
import host_device_pipeline as pipeline


def load_module(filename: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


validator = load_module("validate-end-to-end-result.py", "review_validator")
summary = load_module("summarize-benchmark.py", "review_summary")
evaluator = load_module("evaluate-product.py", "review_evaluator")


def read(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def command(args: list[str]):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return {"argv": args, "exit_code": result.returncode,
            "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def document_audit():
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True, encoding="utf-8").splitlines()
    markdown = [name for name in tracked if name.endswith(".md")]
    active = [name for name in markdown if "/archive/" not in name and "/evidence/" not in name]
    links = []
    blocks = collections.defaultdict(set)
    for name in markdown + ["results/agy-codex-progress-comparison-20261001.md",
                            "results/opencode-first-output-review-20261001.md"]:
        if not (ROOT / name).exists():
            continue
        contents = (ROOT / name).read_text(encoding="utf-8")
        for match in re.finditer(r"\[[^\]\n]+\]\((<[^>]+>|[^)\n]+)\)", contents):
            target = match.group(1).strip("<>")
            if re.match(r"^(https?://|mailto:|#)", target):
                continue
            target = unquote(target.split("#")[0])
            absolute = bool(re.match(r"^[A-Za-z]:/", target))
            path = Path(target) if absolute else ROOT / Path(name).parent / target
            links.append({"file": name, "line": contents.count("\n", 0, match.start()) + 1,
                          "target": target, "exists": path.exists(), "absolute": absolute,
                          "tracked_document": name in markdown, "active_document": name in active})
        if name in active:
            for block in re.split(r"\n\s*\n", contents):
                normalized = re.sub(r"\s+", " ", block).strip()
                if len(normalized) > 90 and not normalized.startswith(("#", "```", "|", ">")):
                    blocks[normalized].add(name)
    duplicates = [{"text": text, "files": sorted(files)} for text, files in blocks.items() if len(files) > 1]
    lengths = []
    for name in ["README.md", "docs/DOCUMENTATION_MAP.md", "docs/PRODUCT_CONTRACT.md",
                 "experiments/prompts/version-2-agent-task.md", "docs/hardware/version-2-capabilities.md",
                 "docs/experiments/integration-contract.md", "docs/experiments/host-device-pipeline-contract.md"]:
        old = subprocess.check_output(["git", "show", "d6da44a:" + name], cwd=ROOT, text=True, encoding="utf-8")
        lengths.append({"file": name, "before_lines": len(old.splitlines()),
                        "after_lines": len((ROOT / name).read_text(encoding="utf-8").splitlines())})
    return {"tracked_markdown_count": len(markdown), "active_markdown_count": len(active),
            "active_local_link_count": sum(link["active_document"] for link in links),
            "active_absolute_link_count": sum(link["active_document"] and link["absolute"] for link in links),
            "missing_links": [link for link in links if not link["exists"]],
            "exact_paragraph_duplicates": duplicates,
            "duplicate_scan_definition": "active tracked MD only; whitespace-normalized prose paragraphs >90 chars; excludes heading/code/table/quote starts",
            "line_counts_against_d6da44a": lengths}


def receiver_probe():
    reference = "2026-09-10T00:10:00Z"
    results = []
    for label, observed in [("old_source_new_frame", "2026-09-10T00:00:00Z"),
                            ("future_source_current_frame", "2026-09-10T00:11:00Z")]:
        snapshot = read("experiments/fixtures/providers/codex-percent-window.json")
        snapshot.update(observed_at=observed, last_good_at=observed)
        frame = pipeline.build_frame({"usage": [snapshot], "global_resets": []}, 1, reference)
        outcome = pipeline.ReferenceReceiver().receive(pipeline.encode_frame(frame), reference)
        try:
            validator.validate_snapshot(snapshot, reference_time=reference)
            semantic = "accepted"
        except validator.ValidationError as error:
            semantic = error.code
        results.append({"case": label, "reference_time": reference, "observed_at": observed,
                        "sent_at": reference, "receiver_accepted": outcome.accepted,
                        "receiver_stale": outcome.stale, "snapshot_stale": snapshot["stale"],
                        "snapshot_semantic_validation": semantic})
    return results


def summary_probe():
    """Use schema-valid synthetic manifests and stub only product-result loading."""
    with tempfile.TemporaryDirectory(prefix="meter-review-summary-") as folder:
        paths = []
        for index, status in [(1, "completed"), (2, "timeout")]:
            manifest = read("experiments/examples/run-manifest.example.json")
            manifest["operator"].update(phase="benchmark", status=status, repetition=index,
                                        reason="synthetic timeout" if status == "timeout" else None,
                                        exit_code=None if status == "timeout" else 0)
            manifest["run_id"] = "20260911-example-cli-example-model-r0" + str(index)
            manifest["outputs"].update(
                selection_document=f"docs/agent-runs/{manifest['run_id']}/hardware-feature-selection.md",
                structured_result=f"results/{manifest['run_id']}/hardware-feature.json")
            if status == "timeout":
                manifest["execution"]["timeout_seconds"] = 600
            benchmark.validate_schema(manifest, "run-manifest.schema.json")
            benchmark.validate_operator(manifest)
            path = Path(folder) / (status + ".json")
            path.write_text(json.dumps(manifest), encoding="utf-8")
            paths.append(path)
        synthetic_result = read("experiments/examples/hardware-feature-result.example.json")
        for entry in synthetic_result["core_requirements"].values():
            entry["status"] = "pass"
        with patch.object(summary, "_load_valid_result", return_value=synthetic_result):
            records, excluded = summary.collect_records(paths)
        rendered = summary.render_summary(records, excluded, min_repetitions=1)
        return {"synthetic": True, "stub": "product result loading only; run schemas and operator semantics validated",
                "attempted": 2, "successful": 1, "attempt_success_ratio": 0.5,
                "summary_included": len(records), "excluded": excluded, "rendered_summary": rendered}


def main():
    evidence = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "reviewed_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
                "python": sys.version, "documents": document_audit(),
                "candidate_input_count": len(benchmark.candidate_input_inventory(ROOT)["files"]),
                "candidate_markdown": list(benchmark.CANDIDATE_MARKDOWN),
                "legacy_evaluator_case_count": len(list(evaluator.cases())),
                "receiver_semantic_probes": receiver_probe(), "summary_attempt_probe": summary_probe()}
    index = read("docs/hardware/vendor-source-index.json")
    vendor_root = Path(index["source_root"])
    missing, mismatches = [], []
    vendor_files = [entry for entries in index["files"].values() for entry in entries]
    for entry in vendor_files:
        relative, expected = entry["path"], entry["sha256"]
        path = vendor_root / relative
        if not path.is_file():
            missing.append(relative)
        elif hashlib.sha256(path.read_bytes()).hexdigest().lower() != expected.lower():
            mismatches.append(relative)
    evidence["vendor_sources"] = {"count": len(vendor_files), "missing": missing, "hash_mismatches": mismatches}
    evidence["historical_evidence_blob_changes"] = subprocess.check_output(
        ["git", "diff", "--name-only", "d6da44a", "HEAD", "--", "docs/experiments/evidence"],
        cwd=ROOT, text=True, encoding="utf-8").splitlines()
    history_path = Path("C:/Espressif/benchmark-runs/20261001-opencode-remediation-r06/hardware-upload-01/board-verification.json")
    if history_path.is_file():
        history = json.loads(history_path.read_text(encoding="utf-8-sig"))
        evidence["saved_opencode_r06_board_record"] = {
            "path": str(history_path), "sha256": hashlib.sha256(history_path.read_bytes()).hexdigest(),
            "implementation_commit": history["implementation_commit"],
            "optical_lcd_verification": history["optical_lcd_verification"],
            "full_product_pass": history["full_product_pass"],
            "owner_optical_observation": history.get("owner_optical_observation"),
            "scope": "read existing evidence; no new board measurement"}
    checks = []
    for args in [[], ["--matrix", "experiments/fixtures/provider-fixture-matrix.json"],
                 ["--result", "experiments/examples/invalid/invalid-product-pass.example.json"]]:
        checks.append(command([sys.executable, "scripts/validate-end-to-end-result.py", *args]))
    check = command([sys.executable, "scripts/benchmark.py", "check", "--baseline", evidence["reviewed_commit"],
                     "--profile", "experiments/config/verified-profiles-candidate/codex-cli-sol-medium.candidate.json"])
    if check["exit_code"] == 0:
        check["parsed"] = json.loads(check["stdout"])
        del check["stdout"]
    checks.append(check)
    frame = OUTPUT / "host-frame.jsonl"
    report = OUTPUT / "host-report.json"
    dry = command([sys.executable, "scripts/run-host-device-pipeline.py", "--dry-run",
                   "--output", str(frame), "--report-output", str(report)])
    if report.exists():
        dry["report"] = json.loads(report.read_text(encoding="utf-8"))
    checks.append(dry)
    evidence["checks"] = checks
    assert [check["exit_code"] for check in checks] == [0, 0, 1, 0, 0]
    assert "PRODUCT_PASS_REQUIRES_CORE_RESULTS" in checks[2]["stderr"]
    assert dry["report"]["device_accessed"] is False
    assert dry["report"]["collection_failures"] == []
    (OUTPUT / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"commit": evidence["reviewed_commit"], "candidate_files": evidence["candidate_input_count"],
                      "active_md": evidence["documents"]["active_markdown_count"],
                      "missing_links": evidence["documents"]["missing_links"],
                      "vendor": evidence["vendor_sources"], "receiver_probes": evidence["receiver_semantic_probes"],
                      "summary_exclusions": evidence["summary_attempt_probe"]["excluded"],
                      "check_exit_codes": [check["exit_code"] for check in checks]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
