"""Offline review probes: synthetic records only, no agent or device invocation."""
import ast
import importlib.util
import json
from fnmatch import fnmatchcase
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_support import digest, read, save


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def summary_probe():
    summary = module(ROOT / "scripts/summarize-benchmark.py", "review_summary")
    with tempfile.TemporaryDirectory(prefix="meter-policy-review-") as folder:
        root = Path(folder)
        m = read(ROOT / "experiments/examples/run-manifest.example.json")
        run_id = "20260911-e2e-contract-policy-probe-r01"
        m.update(run_id=run_id, experiment_id="version-2-end-to-end-v1")
        m["agent"].update(provider="example", product="example-cli", interface="cli", model="example-model", reasoning="fixed")
        m["execution"].update(base_commit="34a1790ffeb31d47c1ae78c78a14d7cf4e318c6f", worktree=str(ROOT))
        m["operator"].update(phase="benchmark", status="completed", repetition=1, exit_code=0)
        m["outputs"].update(selection_document=f"docs/agent-runs/{run_id}/hardware-feature-selection.md",
                            structured_result=f"results/{run_id}/end-to-end-result.json",
                            evaluation_manifest=f"results/{run_id}/e2e-evaluation-manifest.json")
        m["measurement"].update(wall_clock_seconds=600, user_interventions=1)
        r = read(ROOT / "experiments/examples/end-to-end-result.example.json")
        e = read(ROOT / "experiments/examples/end-to-end-manifest.example.json")
        r.update(result_id=run_id, run_id=run_id, manifest_id=run_id, baseline_id=m["baseline_id"])
        r["manifest"].update(id=run_id, baseline_id=m["baseline_id"])
        r["baseline"].update(id=m["baseline_id"], ref=m["baseline_ref"], commit=m["execution"]["base_commit"])
        e.update(manifest_id=run_id, run_id=run_id, result_id=run_id,
                 baseline_id=m["baseline_id"], baseline_ref=m["baseline_ref"])
        e["execution"]["base_commit"] = m["execution"]["base_commit"]
        save(root / "end-to-end-result.json", r)
        save(root / "e2e-evaluation-manifest.json", e)
        save(root / "run-manifest.json", m)
        unreviewed, _ = summary.collect_records([root / "run-manifest.json"])
        save(root / "policy-review.json", {"status": "invalid_for_comparison", "reason": "synthetic external implementation feedback"})
        m["operator"]["evidence"]["policy-review.json"] = digest((root / "policy-review.json").read_bytes())
        save(root / "run-manifest.json", m)
        reviewed, excluded = summary.collect_records([root / "run-manifest.json"])
        return {"unreviewed_included": len(unreviewed), "known_violation_included": len(reviewed), "excluded": excluded}


def followup_probe():
    tests = module(ROOT / "scripts/tests/test_comparison_manager.py", "review_comparison_fixture")
    fixture = tests.ComparisonManagerTests()
    try:
        fixture.setUp()
        fixture.manager.start_run(fixture.first)
        fixture.terminal(fixture.first)
        fixture.review(fixture.first)
        followup = fixture.manager.prepare_followup(fixture.ledger, fixture.root / "runs", fixture.feedback(fixture.first))
        prompt = (followup / "prompt.txt").read_text(encoding="utf-8")
        return {"generated_prompt": prompt, "contains_common_task": "Version 2 구현 과제" in prompt,
                "instructs_read_common_task": "version-2-agent-task.md" in prompt,
                "contains_serial_ban": "serial port" in prompt,
                "contains_permission_denial_rule": "권한 거부" in prompt}
    finally:
        fixture.doCleanups()


def permission_probe():
    p = read(ROOT / "experiments/config/next-profiles-20261003/opencode-muse.json")
    literals = [n.value for n in ast.walk(ast.parse(p["argv"][2]))
                if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith('{"plugin"')]
    policy = json.loads(literals[0])["permission"]
    def decision(rules, command):
        outcome = "deny"
        for pattern, value in rules.items():
            if fnmatchcase(command, pattern):
                outcome = value
        return outcome
    agy = read(ROOT / "experiments/config/agy-pilot-permissions.json")["allow"]
    def agy_allowed(command):
        return any(re.fullmatch(rule[14:-1], command) if rule.startswith("command(regex:")
                   else rule == "command(" + command + ")" for rule in agy if rule.startswith("command("))
    return {"opencode_py_compile": decision(policy["bash"], "python -m py_compile scripts/collector.py"),
            "opencode_old_ref_diff": decision(policy["bash"], "git diff HEAD~1"),
            "opencode_sdk_external_directory": decision(policy["external_directory"], "C:/Espressif/v5.3.2/esp-idf/components"),
            "opencode_edit": policy["edit"], "agy_bounded_git_log_allowed": agy_allowed("git log -n 1")}


def wrapper_probe():
    from agy_pilot_environment import scoped_environment, verify_scoped_environment
    tests = module(ROOT / "scripts/tests/test_agy_pilot_environment.py", "review_agy_fixture")
    with tempfile.TemporaryDirectory(prefix="meter-wrapper-review-") as folder:
        root = Path(folder)
        gemini, _, _, _, policy = tests.AgyPilotEnvironmentTests().fixture(root)
        first = scoped_environment(gemini, policy, root / "backup-a")
        second = scoped_environment(gemini, policy, root / "backup-b")
        first.__enter__()
        second.__enter__()
        first.__exit__(None, None, None)
        try:
            verify_scoped_environment(gemini, policy)
            state = "still scoped"
        except ValueError as error:
            state = str(error)
        try:
            second.__exit__(None, None, None)
            restore = "success"
        except ValueError as error:
            restore = str(error)
        return {"second_wrapper_admitted": True, "after_first_exits": state, "second_restore": restore}


def cli_probe():
    result = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts/benchmark.py"),
                             "run", "--directory", "REVIEW-NONEXISTENT", "--receipt", "REVIEW-NONEXISTENT.json"],
                            capture_output=True, text=True, encoding="utf-8")
    return {"documented_run_syntax_exit": result.returncode, "stderr": result.stderr.strip()}


if __name__ == "__main__":
    report = {"scope": "offline synthetic probes; no model call, serial port, or persistent run",
              "summary": summary_probe(), "followup": followup_probe(), "permissions": permission_probe(),
              "wrapper": wrapper_probe(), "cli": cli_probe()}
    Path(__file__).with_name("probes.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
