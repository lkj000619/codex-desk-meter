"""Prepare isolated baseline snapshots and capture operator-owned execution records.

No shell interpolation. Logs stay outside the agent checkout. Default access policy
uses prompt restrictions and activity logs; OS sandbox read isolation is optional.
"""
import argparse
import importlib.util
import io
import json
import os
import re
import signal
import subprocess
import sys
import time
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from benchmark_support import ROOT, KST, digest, read, save, validate_operator, validate_schema


UNRESOLVED_PROFILE_VALUES = {
    "operator-check-required", "user-confirm-required", "pending", "unverified",
    "explicit-policy-required-before-run",
}

EVALUATION_CRITERIA_PATHS = (
    "docs/PRODUCT_CONTRACT.md",
    "docs/experiments/evaluation-contract.md",
    "docs/experiments/feature-comparison.md",
    "docs/experiments/hardware-feature-discovery.md",
)


def _hash_group(root, paths):
    root = Path(root).resolve()
    lines = []
    for relative in sorted(paths):
        path = root / relative
        if not path.is_file():
            raise ValueError(f"required R1 input is missing: {relative}")
        lines.append(f"{digest(path.read_bytes())}  {relative}")
    return digest(("\n".join(lines) + "\n").encode())


def profile_digest(profile):
    """Hash profile meaning, not incidental JSON whitespace or key order."""
    canonical = json.dumps(profile, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return digest(canonical.encode("utf-8"))


def _extract_archive(destination, base):
    destination = Path(destination).resolve()
    archive = subprocess.check_output(["git", "archive", "--format=zip", base], cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for entry in z.infolist():
            if not (destination / entry.filename).resolve().is_relative_to(destination):
                raise ValueError("unsafe archive entry")
        z.extractall(destination)


def input_bundle_hashes(root, profile_path, baseline_ref, baseline_commit):
    """Hash the complete R1 bundle with the same content basis for check/prepare."""
    root = Path(root).resolve()
    profile = read(profile_path)
    fixture_paths = sorted(
        path.relative_to(root).as_posix()
        for path in (root / "experiments/fixtures").rglob("*.json")
    )
    schema_paths = sorted(
        path.relative_to(root).as_posix()
        for path in (root / "experiments/schema").rglob("*.json")
    )
    evaluation_paths = list(EVALUATION_CRITERIA_PATHS)
    values = {
        "prompt_sha256": digest((root / "experiments/prompts/version-2-agent-task.md").read_bytes()),
        "config_sha256": digest((root / "experiments/config/version-2-baseline.yaml").read_bytes()),
        "fixture_sha256": _hash_group(root, fixture_paths),
        "schema_sha256": _hash_group(root, schema_paths),
        "evaluation_criteria_sha256": _hash_group(root, evaluation_paths),
        "profile_sha256": profile_digest(profile),
    }
    bundle_lines = [
        f"baseline_ref={baseline_ref}",
        f"baseline_commit={baseline_commit}",
    ] + [f"{key}={values[key]}" for key in (
        "prompt_sha256",
        "config_sha256",
        "fixture_sha256",
        "schema_sha256",
        "evaluation_criteria_sha256",
        "profile_sha256",
    )]
    values["input_bundle_sha256"] = digest(("\n".join(bundle_lines) + "\n").encode())
    return values


def validate_resolved_profile(profile):
    """Reject unresolved execution settings before reserving a run or launching it."""
    validate_schema(profile, "runner-profile.schema.json")
    values = [profile[k] for k in ("model", "agent_version", "reasoning", "model_slug",
                                   "sandbox_policy", "approval_policy")]
    values.extend(profile["argv"])
    values.extend(profile["version_argv"])
    values.extend(profile["settings_inventory"].values())
    for value in values:
        if "<" in value or ">" in value or any(marker in value.lower() for marker in UNRESOLVED_PROFILE_VALUES):
            raise ValueError("replace profile placeholders and unresolved settings with operator-verified values")
    argv = profile["argv"]
    if profile["adapter"] == "antigravity" and "stream-json" in argv:
        if "--input-format" in argv and argv[argv.index("--input-format") + 1:][:1] == ["stream-json"]:
            raise ValueError("runner delivers plain UTF-8 stdin; Antigravity requires --input-format text")


def check_inputs(a):
    """Validate future-run inputs without reserving a run ID or touching a checkout."""
    baseline = git("rev-parse", "--verify", a.baseline + "^{commit}")
    profile_path = Path(a.profile).resolve()
    profile = read(profile_path)
    validate_resolved_profile(profile)
    model_slug = slug(profile["model_slug"])
    product = slug(profile["product"])
    # Hash the selected baseline snapshot, not the possibly dirty current
    # checkout. The temporary extraction is read-only with respect to the
    # repository and does not reserve a run ID or create a worktree.
    with tempfile.TemporaryDirectory(prefix="meter-input-check-") as temp:
        snapshot = Path(temp) / "checkout"
        snapshot.mkdir()
        _extract_archive(snapshot, baseline)
        hashes = input_bundle_hashes(snapshot, profile_path, a.baseline, baseline)
    print(json.dumps({
        "status": "inputs_valid",
        "run_id_reserved": False,
        "worktree_touched": False,
        "baseline_ref": a.baseline,
        "baseline_commit": baseline,
        "profile": str(profile_path),
        "product": product,
        "model_slug": model_slug,
        **hashes,
        "next": "freeze baseline, obtain profile-bound receipt and explicit approval, then run prepare",
    }, ensure_ascii=True, indent=2))


def git(*args, cwd=ROOT):
    return subprocess.check_output(["git", *args], cwd=cwd, encoding="utf-8").strip()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def slug(s):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", s):
        raise ValueError(f"invalid slug: {s}")
    return s


def prepare(a):
    if git("status", "--porcelain"):
        raise ValueError("commit changes before preparing a baseline run")
    base = git("rev-parse", "--verify", a.baseline + "^{commit}")
    if base != git("rev-parse", "HEAD"):
        raise ValueError("run prepare from the selected baseline checkout")
    profile_path = Path(a.profile).resolve()
    profile = read(profile_path)
    validate_resolved_profile(profile)
    model_slug = slug(profile["model_slug"])
    product = slug(profile["product"])
    root = Path(a.root).resolve()
    if not str(root).isascii() or root.is_relative_to(ROOT) or ROOT.is_relative_to(root):
        raise ValueError("run root must be a separate ASCII directory outside this repository")
    root.mkdir(parents=True, exist_ok=True)
    date = datetime.now(KST).strftime("%Y%m%d")
    prefix = f"{date}-{product}-{model_slug}"
    # mkdir is the reservation: failed preparations consume IDs, never overwrite.
    for repetition in range(1, 100):
        run_id = f"{prefix}-r{repetition:02d}"
        directory = root / run_id
        try:
            directory.mkdir()
            break
        except FileExistsError:
            continue
    else:
        raise ValueError("daily repetition slots exhausted")
    checkout = directory / "checkout"
    checkout.mkdir()
    _extract_archive(checkout, base)
    git("init", cwd=checkout)
    git("add", ".", cwd=checkout)
    git("-c", "user.name=Benchmark", "-c", "user.email=benchmark@localhost", "commit", "-m", "Isolated baseline snapshot", cwd=checkout)
    local_base = git("rev-parse", "HEAD", cwd=checkout)
    template = (checkout / "experiments/prompts/version-2-agent-task.md").read_bytes()
    prompt = template.decode("utf-8").replace("<run-id>", run_id).encode("utf-8")
    (directory / "prompt.txt").write_bytes(prompt)
    save(directory / "profile.json", profile)
    m = read(checkout / "experiments/examples/run-manifest.example.json")
    if profile["cohort"] == "version-2-end-to-end-v1":
        m["experiment_id"] = "version-2-end-to-end-v1"
    m["run_id"] = run_id
    m["baseline_id"] = a.baseline
    m["baseline_ref"] = a.baseline
    m["agent"].update({k: profile[k] for k in ("provider", "product", "interface", "agent_version", "model", "reasoning")})
    m["agent"]["configuration_sha256"] = digest((directory / "profile.json").read_bytes())
    hashes = input_bundle_hashes(checkout, directory / "profile.json", a.baseline, base)
    e = m["execution"]
    e.update(started_at=None, ended_at=None, base_commit=base, **hashes,
             branch=f"experiment/{slug(profile['branch_owner'])}/{slug(profile['branch_product'])}/{model_slug}",
             worktree=str(checkout), host=os.environ.get("COMPUTERNAME", "unknown"),
             sandbox_policy=profile["sandbox_policy"], approval_policy=profile["approval_policy"],
             network_mode=profile["network_mode"], timeout_seconds=a.timeout)
    m["operator"] = dict(phase=a.phase, status="prepared", reason=None, repetition=repetition,
                         cohort=profile["cohort"], seed=a.seed, exit_code=None,
                         delivered_prompt_sha256=digest(prompt), local_base_commit=local_base, evidence={})
    m["hardware"]["port"] = a.port
    m["measurement"].update(wall_clock_seconds=None, tool_calls=None, failed_commands=None, user_interventions=None)
    m["measurement"]["tokens"]["availability_note"] = "Not yet executed."
    m["measurement"]["tokens"]["provider_total"] = None
    m["measurement"]["tokens"]["provider_total_definition"] = "provider_reported_total_preserved_without_recomputation"
    m["outputs"].update(selection_document=f"docs/agent-runs/{run_id}/hardware-feature-selection.md",
                         structured_result=f"results/{run_id}/hardware-feature.json")
    if m["experiment_id"] == "version-2-end-to-end-v1":
        m["outputs"]["structured_result"] = f"results/{run_id}/end-to-end-result.json"
        m["outputs"]["evaluation_manifest"] = f"results/{run_id}/e2e-evaluation-manifest.json"
        save(directory / "e2e-evaluation-manifest.json", {
            "schema_version": 1,
            "manifest_id": run_id,
            "run_id": run_id,
            "result_reference": run_id,
            "baseline_id": a.baseline,
            "baseline_ref": a.baseline,
            "experiment_id": m["experiment_id"],
            "execution": {"base_commit": base},
        })
    validate_schema(m, "run-manifest.schema.json")
    validate_operator(m)
    save(directory / "run-manifest.json", m)
    print(directory)


def stop_tree(process):
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=True)
    else:
        os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=15)


def capture(argv, cwd, prompt, directory, timeout, env=None):
    start = now()
    tick = time.monotonic()
    state, reason, code = "completed", None, None
    with (directory / "stdout.jsonl").open("xb") as out, (directory / "stderr.txt").open("xb") as err:
        p = None
        try:
            p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=out, stderr=err,
                                 start_new_session=os.name != "nt")
            p.communicate(prompt, timeout=timeout)
            code = p.returncode
            if code != 0:
                state, reason = "environment_failed", f"agent exited with code {code}; inspect evidence"
        except subprocess.TimeoutExpired:
            stop_tree(p)
            state, reason, code = "timeout", "hard timeout", p.returncode
        except KeyboardInterrupt:
            if p is not None:
                stop_tree(p)
            state, reason, code = "aborted", "operator interruption", None if p is None else p.returncode
        except OSError as exc:
            state, reason = "environment_failed", str(exc)
    return dict(start=start, end=now(), elapsed=time.monotonic() - tick, status=state, reason=reason, code=code)


def _antigravity_events(path):
    """Read AGY's documented headless NDJSON without treating diagnostics as events."""
    events = []
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        try:
            event = json.loads(line)
        except ValueError as exc:
            raise ValueError("AGY stdout contains a non-JSON event") from exc
        if not isinstance(event, dict):
            raise ValueError("AGY stdout event is not an object")
        events.append(event)
    return events


def inspect_antigravity_stream(path, expected_permission_mode=None, expected_model=None,
                               reject_permission_errors=True):
    """Require the init and one successful terminal result of a one-shot AGY run."""
    events = _antigravity_events(path)
    if len(events) < 2 or events[0].get("event") != "init" or events[-1].get("event") != "result":
        raise ValueError("AGY stream needs an init and terminal result")
    if sum(event.get("event") == "init" for event in events) != 1 or sum(
            event.get("event") == "result" for event in events) != 1:
        raise ValueError("AGY stream must contain exactly one init and one result")
    init = events[0].get("init")
    if not isinstance(init, dict) or not isinstance(init.get("permission_mode"), str):
        raise ValueError("AGY init lacks an effective permission mode")
    if expected_permission_mode is not None and init["permission_mode"] != expected_permission_mode:
        raise ValueError("AGY effective permission mode does not match profile")
    if expected_model is not None and init.get("model") != expected_model:
        raise ValueError("AGY effective model does not match profile")
    result = events[-1].get("result")
    if not isinstance(result, dict) or result.get("status") != "SUCCESS":
        raise ValueError("AGY terminal result is not SUCCESS")
    if result.get("num_turns") != 1:
        raise ValueError("AGY one-shot run must report exactly one turn")
    for event in events:
        step = event.get("step_update")
        if event.get("event") != "step_update" or not isinstance(step, dict):
            continue
        if step.get("state") != "DONE" or step.get("step_type") != "tool":
            continue
        tool_info = step.get("tool_info")
        error = tool_info.get("error") if isinstance(tool_info, dict) else None
        error_type = error.get("type", "") if isinstance(error, dict) else ""
        if reject_permission_errors and isinstance(error_type, str) and any(
                marker in error_type.lower() for marker in ("permission", "approval", "accessdenied")):
            raise ValueError("AGY tool permission denied; inspect raw evidence")
    return result


def telemetry(path, adapter):
    tokens = dict(input=None, output=None, cached=None, reasoning=None, provider_total=None, total=None,
                  provider_total_definition="provider_reported_total_preserved_without_recomputation",
                  availability_note="No supported usage event; see raw stdout.")
    events = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
            if isinstance(event, dict):
                events.append(event)
        except ValueError:
            continue
    # Codex turn.completed usage is per turn. Cache is a subset of input.
    if adapter == "codex":
        usages = [e["usage"] for e in events if e.get("type") == "turn.completed" and isinstance(e.get("usage"), dict)]
        if usages:
            for target, source in (("input", "input_tokens"), ("output", "output_tokens"), ("cached", "cached_input_tokens")):
                values = [u.get(source) for u in usages]
                if all(type(v) is int and v >= 0 for v in values):
                    tokens[target] = sum(values)
            provider_totals = [u.get("total_tokens", u.get("total")) for u in usages]
            if all(type(v) is int and v >= 0 for v in provider_totals):
                tokens["provider_total"] = sum(provider_totals)
            if tokens["input"] is not None and tokens["output"] is not None:
                tokens["total"] = tokens["input"] + tokens["output"]
            tokens["availability_note"] = "Codex turn.completed usage; cached is included in input; reasoning unavailable."
    if adapter == "opencode":
        # step_finish contains per-step provider usage; cache read/write are separate.
        usages = [e["part"]["tokens"] for e in events
                  if e.get("type") == "step_finish"
                  and isinstance(e.get("part"), dict)
                  and isinstance(e["part"].get("tokens"), dict)]
        if usages:
            for target in ("input", "output", "reasoning"):
                values = [u.get(target) for u in usages]
                if all(type(v) is int and v >= 0 for v in values):
                    tokens[target] = sum(values)
            values = [u.get("total") for u in usages]
            if all(type(v) is int and v >= 0 for v in values):
                tokens["provider_total"] = sum(values)
            if all(type(u.get("input")) is int and type(u.get("output")) is int
                   and u.get("input") >= 0 and u.get("output") >= 0 for u in usages):
                tokens["total"] = sum(u["input"] + u["output"] for u in usages)
            values = [u.get("cache", {}).get("read") for u in usages
                      if isinstance(u.get("cache", {}), dict)]
            if len(values) == len(usages) and all(type(v) is int and v >= 0 for v in values):
                tokens["cached"] = sum(values)
            tokens["availability_note"] = (
                "OpenCode step_finish provider usage; provider_total preserves the raw total, "
                "total is normalized input+output and excludes cache/reasoning; cache write is raw-log-only."
            )
    if adapter == "antigravity":
        try:
            usage = inspect_antigravity_stream(path, reject_permission_errors=False).get("usage")
        except (UnicodeError, ValueError):
            usage = None
        if isinstance(usage, dict):
            for target, source in (("input", "input_tokens"), ("output", "output_tokens"),
                                   ("cached", "cache_read_tokens"), ("reasoning", "thinking_tokens"),
                                   ("provider_total", "total_tokens")):
                value = usage.get(source)
                if type(value) is int and value >= 0:
                    tokens[target] = value
            if tokens["input"] is not None and tokens["output"] is not None:
                tokens["total"] = tokens["input"] + tokens["output"]
            tokens["availability_note"] = (
                "AGY one-shot terminal result usage; provider_total preserves raw total_tokens; "
                "total is normalized input+output; cache_read and thinking are annotations."
            )
    return tokens


def command_metrics(path, adapter):
    if adapter == "antigravity":
        try:
            inspect_antigravity_stream(path, reject_permission_errors=False)
            events = _antigravity_events(path)
        except (UnicodeError, ValueError):
            return dict(tool_calls=None, failed_commands=None)
        tools = {}
        for event in events:
            step = event.get("step_update")
            if event.get("event") != "step_update" or not isinstance(step, dict):
                continue
            if step.get("state") == "DONE" and step.get("step_type") == "tool" and type(step.get("step_index")) is int:
                tools[step["step_index"]] = step
        failed = sum(
            isinstance(step.get("tool_info"), dict) and bool(step["tool_info"].get("error"))
            for step in tools.values()
            if step.get("tool_name") == "run_command"
        )
        return dict(tool_calls=len(tools), failed_commands=failed)
    if adapter != "codex":
        return dict(tool_calls=None, failed_commands=None)
    items = {}
    valid_stream = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if not isinstance(e, dict):
            continue
        valid_stream |= e.get("type") == "thread.started"
        item = e.get("item", {})
        if not isinstance(item, dict):
            continue
        if e.get("type") == "item.completed" and item.get("type") in {"command_execution", "mcp_tool_call", "web_search", "file_change"}:
            item_id = item.get("id")
            if isinstance(item_id, str) and item_id:
                items[item_id] = item
    if not valid_stream:
        return dict(tool_calls=None, failed_commands=None)
    commands = [i for i in items.values() if i["type"] == "command_execution"]
    failed = sum(i.get("exit_code") not in (0, None) for i in commands)
    return dict(tool_calls=len(items), failed_commands=failed)


def validate_preflight_receipt(receipt, manifest, profile, evidence_root):
    """Validate the selected access policy; prompt restrictions are not OS isolation."""
    mode = receipt.get("access_policy")
    if mode not in {"prompt-and-log", "external-sandbox"}:
        raise ValueError("preflight requires an explicit supported access_policy")
    if profile["sandbox_policy"] != mode:
        raise ValueError("preflight access policy does not match profile")
    # The receipt binds to the semantic profile hash used by check/prepare.
    # agent.configuration_sha256 remains a separate byte-integrity guard for
    # the saved profile file and is checked by execute().
    for key, expected in (("base_commit", manifest["execution"]["base_commit"]),
                          ("profile_sha256", manifest["execution"]["profile_sha256"])):
        if receipt.get(key) != expected:
            raise ValueError(f"preflight receipt mismatch: {key}")
    checks = receipt.get("checks")
    if not isinstance(checks, dict):
        raise ValueError("preflight checks must be an object")
    required = ["idf_build", "compiler", "ninja", "git", "temp_write",
                "network_policy", "settings_inventory"]
    if mode == "prompt-and-log":
        required += ["prompt_scope", "activity_logging"]
        if checks.get("read_isolation") != "not_enforced":
            raise ValueError("prompt-and-log must record read_isolation as not_enforced")
    else:
        required += ["read_isolation"]
    for check in required:
        if checks.get(check) != "pass":
            raise ValueError(f"preflight has not passed: {check}")
    if not receipt.get("evidence"):
        raise ValueError("preflight receipt needs evidence file hashes")
    from benchmark_support import verify_evidence
    verify_evidence({"operator": {"evidence": receipt["evidence"]}}, evidence_root)


def execute(a):
    directory = Path(a.directory).resolve()
    m = read(directory / "run-manifest.json")
    profile = read(directory / "profile.json")
    validate_schema(m, "run-manifest.schema.json")
    validate_resolved_profile(profile)
    validate_operator(m)
    if m["operator"]["status"] != "prepared":
        raise ValueError("run can only execute once")
    if datetime.now(KST).strftime("%Y%m%d") != m["run_id"][:8]:
        raise ValueError("prepared on a different date; reserve a new run")
    checkout = Path(m["execution"]["worktree"])
    if git("status", "--porcelain", cwd=checkout) or git("rev-parse", "HEAD", cwd=checkout) != m["operator"]["local_base_commit"]:
        raise ValueError("checkout changed since preparation")
    if digest((directory / "profile.json").read_bytes()) != m["agent"]["configuration_sha256"]:
        raise ValueError("profile changed since preparation")
    prompt = (directory / "prompt.txt").read_bytes()
    if digest(prompt) != m["operator"]["delivered_prompt_sha256"]:
        raise ValueError("delivered prompt changed")
    receipt = read(a.receipt)
    if m["operator"]["phase"] == "benchmark" and receipt.get("pilot_pass") is not True:
        raise ValueError("benchmark requires reviewed pilot pass in the receipt")
    validate_preflight_receipt(receipt, m, profile, Path(a.receipt).resolve().parent)
    argv = [s.replace("{checkout}", str(checkout)).replace("{model}", profile["model"]) for s in profile["argv"]]
    agent_env = os.environ.copy()
    if profile["adapter"] == "antigravity":
        from agy_pilot_environment import verify_scoped_environment
        policy_path = ROOT / "experiments/config/agy-pilot-permissions.json"
        verify_scoped_environment(Path.home() / ".gemini", policy_path)
        agent_env["AGY_CLI_DISABLE_AUTO_UPDATE"] = "true"
    actual_version = subprocess.check_output(profile["version_argv"], encoding="utf-8", timeout=30,
                                             env=agent_env).strip()
    if actual_version != profile["agent_version"]:
        raise ValueError(f"CLI version mismatch: {actual_version}")
    m["operator"]["status"] = "running"
    m["execution"]["started_at"] = now()
    save(directory / "run-manifest.json", m)
    r = capture(argv, checkout, prompt, directory, m["execution"]["timeout_seconds"], env=agent_env)
    if profile["adapter"] == "antigravity" and r["status"] == "completed":
        try:
            inspect_antigravity_stream(
                directory / "stdout.jsonl", expected_permission_mode=profile["approval_policy"],
                expected_model=profile["model"]
            )
        except (UnicodeError, ValueError) as exc:
            r["status"], r["reason"] = "environment_failed", str(exc)
    m["execution"].update(started_at=r["start"], ended_at=r["end"])
    m["operator"].update(status=r["status"], reason=r["reason"], exit_code=r["code"])
    m["measurement"]["wall_clock_seconds"] = r["elapsed"]
    m["measurement"]["tokens"] = telemetry(directory / "stdout.jsonl", profile["adapter"])
    m["measurement"].update(command_metrics(directory / "stdout.jsonl", profile["adapter"]))
    for name in ("stdout.jsonl", "stderr.txt", "prompt.txt", "profile.json"):
        m["operator"]["evidence"][name] = digest((directory / name).read_bytes())
    save(directory / "run-manifest.json", m)
    validate_operator(m)
    print(json.dumps(r))
    return 0 if r["status"] == "completed" else 1


def _load_e2e_validator():
    path = Path(__file__).with_name("validate-end-to-end-result.py")
    spec = importlib.util.spec_from_file_location("benchmark_e2e_validator", path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise ValueError("cannot load end-to-end semantic validator")
    spec.loader.exec_module(module)
    return module


def _check_e2e_manifest_join(manifest, run_manifest, candidate):
    result_reference = manifest.get("result_id", manifest.get("result_reference"))
    if (
        manifest["run_id"] != run_manifest["run_id"]
        or manifest["manifest_id"] != run_manifest["run_id"]
        or manifest["experiment_id"] != run_manifest["experiment_id"]
        or manifest["baseline_id"] != run_manifest["baseline_id"]
        or manifest["baseline_ref"] != run_manifest["baseline_ref"]
        or manifest["baseline_id"] != candidate["baseline_id"]
        or manifest["baseline_ref"] != candidate["baseline"]["ref"]
        or manifest["execution"]["base_commit"] != run_manifest["execution"]["base_commit"]
        or manifest["execution"]["base_commit"] != candidate["baseline"]["commit"]
        or result_reference != candidate["result_id"]
        or candidate["run_id"] != run_manifest["run_id"]
        or candidate["experiment_id"] != run_manifest["experiment_id"]
        or candidate["manifest_id"] != manifest["manifest_id"]
        or candidate["manifest"]["id"] != candidate["manifest_id"]
        or candidate["manifest"]["experiment_id"] != manifest["experiment_id"]
        or candidate["manifest"]["baseline_id"] != manifest["baseline_id"]
    ):
        raise ValueError("E2E result/manifest identity mismatch")


def _validate_final_e2e_candidate(candidate, evaluation_manifest, run_manifest, checkout, directory):
    validator = _load_e2e_validator()
    candidate["manifest"]["path"] = "e2e-evaluation-manifest.json"
    validator.validate_result(
        candidate,
        manifest=evaluation_manifest,
        evidence_root=checkout,
        manifest_root=directory,
    )
    # Validate the exact post-mutation archive path before it is written to the
    # bare archive index. The source result remains untouched throughout.
    candidate["manifest"]["path"] = run_manifest["outputs"]["evaluation_manifest"]
    with tempfile.TemporaryDirectory(prefix="meter-e2e-final-") as temp:
        final_root = Path(temp)
        final_manifest = final_root / run_manifest["outputs"]["evaluation_manifest"]
        final_manifest.parent.mkdir(parents=True, exist_ok=True)
        save(final_manifest, evaluation_manifest)
        validator.validate_result(
            candidate,
            manifest=evaluation_manifest,
            evidence_root=checkout,
            manifest_root=final_root,
        )


def derive_e2e_automated_test_status(candidate):
    """Derive test status from integration test entries and their evidence only."""
    entries = list(candidate.get("integration_results", {}).values())
    if not entries or all(entry["status"] == "not_run" for entry in entries):
        return "not_run"
    statuses = {entry["status"] for entry in entries}
    if "timeout" in statuses:
        return "timeout"
    if "fail" in statuses:
        return "fail"
    if all(entry["status"] == "pass" and entry["evidence"] for entry in entries):
        return "pass"
    return "partial"


def archive_run(a):
    """Create a local bundle plus a stable branch in a dedicated bare archive.

    Raw logs never enter Git automatically. Review and redact an export directory
    first. Keep originals outside the repository and publish only reviewed files.
    """
    directory = Path(a.directory).resolve()
    m = read(directory / "run-manifest.json")
    validate_operator(m)
    if m["operator"]["status"] in {"prepared", "running"}:
        raise ValueError("cannot archive an unfinished run")
    checkout = Path(m["execution"]["worktree"])
    bundle = directory / "implementation.bundle"
    if bundle.exists():
        raise ValueError("archive already exists")
    # Commit source changes, respecting ignore rules. Review is required before this command.
    git("add", "--all", cwd=checkout)
    if git("diff", "--cached", "--name-only", cwd=checkout):
        git("-c", "user.name=Benchmark", "-c", "user.email=benchmark@localhost", "commit", "-m", f"Implementation {m['run_id']}", cwd=checkout)
    implementation = git("rev-parse", "HEAD", cwd=checkout)
    m["outputs"]["implementation_commit"] = implementation
    save(directory / "run-manifest.json", m)
    git("bundle", "create", str(bundle), "HEAD", cwd=checkout)
    m["operator"]["evidence"]["implementation.bundle"] = digest(bundle.read_bytes())
    result_path = checkout / m["outputs"]["structured_result"]
    normalized_result = None
    evaluation_manifest = None
    if m["experiment_id"] == "version-2-end-to-end-v1":
        evaluation_path = directory / "e2e-evaluation-manifest.json"
        if not evaluation_path.is_file():
            raise ValueError("E2E archive requires the generated evaluation manifest")
        evaluation_manifest = read(evaluation_path)
        validate_schema(evaluation_manifest, "end-to-end-manifest.schema.json")
        if (evaluation_manifest["run_id"] != m["run_id"]
                or evaluation_manifest["experiment_id"] != m["experiment_id"]
                or evaluation_manifest["execution"]["base_commit"] != m["execution"]["base_commit"]):
            raise ValueError("E2E evaluation manifest identity mismatch")
    if result_path.is_file():
        candidate = read(result_path)
        try:
            schema_name = ("end-to-end-result.schema.json" if m["experiment_id"] == "version-2-end-to-end-v1"
                           else "hardware-feature-result.schema.json")
            validate_schema(candidate, schema_name)
            if candidate.get("run_id") != m["run_id"] or candidate.get("experiment_id") != m["experiment_id"]:
                raise ValueError("result ID mismatch")
            if evaluation_manifest is not None:
                _check_e2e_manifest_join(evaluation_manifest, m, candidate)
                _validate_final_e2e_candidate(candidate, evaluation_manifest, m, checkout, directory)
            else:
                candidate["implementation"]["commit"] = implementation
            normalized_result = candidate
            if evaluation_manifest is None:
                m["outputs"].update(build_status=candidate["implementation"]["build"]["status"],
                                     automated_test_status=candidate["implementation"]["automated_tests"]["status"],
                                     hardware_verification_status=candidate["implementation"]["hardware_result"])
            else:
                m["outputs"].update(build_status=candidate["build"]["status"],
                                     automated_test_status=derive_e2e_automated_test_status(candidate),
                                     hardware_verification_status=candidate["hardware"]["status"])
        except ValueError as exc:
            print(f"Result needs operator review; raw source snapshot preserved: {exc}")
    save(directory / "run-manifest.json", m)
    # Separate bare archive avoids touching any Orca-managed worktree.
    archive = Path(a.archive).resolve()
    if archive == checkout or archive.is_relative_to(checkout) or archive == ROOT:
        raise ValueError("archive must be outside checkout and source repository")
    if not archive.exists():
        archive.mkdir(parents=True)
        git("init", "--bare", cwd=archive)
    if git("rev-parse", "--is-bare-repository", cwd=archive) != "true":
        raise ValueError("expected dedicated bare archive repository")
    branch = m["execution"]["branch"]
    git("fetch", str(checkout), implementation, cwd=archive)
    # Preserve previous runs as parents while taking source from this run only.
    prior = subprocess.run(["git", "rev-parse", "--verify", f"refs/heads/{branch}"], cwd=archive, capture_output=True, text=True)
    parents = ["-p", implementation]
    if prior.returncode == 0:
        parents += ["-p", prior.stdout.strip()]
    tree = git("rev-parse", implementation + "^{tree}", cwd=archive)
    with tempfile.TemporaryDirectory(prefix="meter-index-") as temp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(temp) / "index"))
        def indexed(*args, data=None):
            return subprocess.check_output(["git", *args], cwd=archive, env=env, input=data)
        indexed("read-tree", tree)
        if prior.returncode == 0:
            entries = indexed("ls-tree", "-r", prior.stdout.strip(), "--", "results", "docs/agent-runs")
            # All old result directories are retained; run IDs are unique.
            if entries:
                indexed("update-index", "--index-info", data=entries)
        manifest_bytes = (json.dumps(m, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        blob = indexed("hash-object", "-w", "--stdin", data=manifest_bytes).decode().strip()
        indexed("update-index", "--add", "--cacheinfo", f"100644,{blob},results/{m['run_id']}/run-manifest.json")
        if normalized_result is not None:
            blob = indexed("hash-object", "-w", "--stdin", data=(json.dumps(normalized_result, ensure_ascii=False, indent=2) + "\n").encode()).decode().strip()
            indexed("update-index", "--add", "--cacheinfo", f"100644,{blob},{m['outputs']['structured_result']}")
        if evaluation_manifest is not None:
            blob = indexed("hash-object", "-w", "--stdin", data=(json.dumps(evaluation_manifest, ensure_ascii=False, indent=2) + "\n").encode()).decode().strip()
            indexed("update-index", "--add", "--cacheinfo", f"100644,{blob},{m['outputs']['evaluation_manifest']}")
        tree = indexed("write-tree").decode().strip()
    record = git("-c", "user.name=Benchmark", "-c", "user.email=benchmark@localhost", "commit-tree", tree,
                 *parents, "-m", f"Preserve {m['run_id']}; implementation {implementation}", cwd=archive)
    git("update-ref", f"refs/heads/{branch}", record, prior.stdout.strip() if prior.returncode == 0 else "0"*40, cwd=archive)
    save(directory / "run-manifest.json", m)
    print(f"Local archive branch: {branch}; record {record}; implementation {implementation}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="validate future-run inputs without reserving a run ID")
    check.add_argument("--baseline", required=True)
    check.add_argument("--profile", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--baseline", required=True)
    prep.add_argument("--profile", required=True)
    prep.add_argument("--root", required=True)
    prep.add_argument("--phase", choices=["pilot", "benchmark"], default="pilot")
    prep.add_argument("--seed", type=int, required=True)
    prep.add_argument("--port", default=None)
    prep.add_argument("--timeout", type=int, default=7200, choices=range(1, 7201), metavar="1..7200")
    run = sub.add_parser("run")
    run.add_argument("directory")
    run.add_argument("--receipt", required=True)
    archive = sub.add_parser("archive")
    archive.add_argument("directory")
    archive.add_argument("--archive", required=True)
    a = p.parse_args()
    try:
        if a.command == "check":
            return check_inputs(a)
        if a.command == "prepare":
            return prepare(a)
        if a.command == "archive":
            return archive_run(a)
        return execute(a)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
