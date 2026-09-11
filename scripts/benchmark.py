"""Prepare isolated baseline snapshots and capture operator-owned execution records.

No shell interpolation. Logs stay outside the agent checkout. An external sandbox
must enforce read isolation; a separate folder alone is not a security boundary.
"""
import argparse
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
    validate_schema(profile, "runner-profile.schema.json")
    if any("<" in profile[k] or ">" in profile[k] for k in ("model", "agent_version", "reasoning")):
        raise ValueError("replace profile placeholders with verified values")
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
    archive = subprocess.check_output(["git", "archive", "--format=zip", base], cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for entry in z.infolist():
            if not (checkout / entry.filename).resolve().is_relative_to(checkout):
                raise ValueError("unsafe archive entry")
        z.extractall(checkout)
    git("init", cwd=checkout)
    git("add", ".", cwd=checkout)
    git("-c", "user.name=Benchmark", "-c", "user.email=benchmark@localhost", "commit", "-m", "Isolated baseline snapshot", cwd=checkout)
    local_base = git("rev-parse", "HEAD", cwd=checkout)
    template = (checkout / "experiments/prompts/version-2-agent-task.md").read_bytes()
    prompt = template.decode("utf-8").replace("<run-id>", run_id).encode("utf-8")
    (directory / "prompt.txt").write_bytes(prompt)
    save(directory / "profile.json", profile)
    m = read(checkout / "experiments/examples/run-manifest.example.json")
    m["run_id"] = run_id
    m["agent"].update({k: profile[k] for k in ("provider", "product", "interface", "agent_version", "model", "reasoning")})
    m["agent"]["configuration_sha256"] = digest((directory / "profile.json").read_bytes())
    fixture_lines = []
    for p in sorted((checkout / "experiments/fixtures").glob("*.json")):
        fixture_lines.append(f"{digest(p.read_bytes())}  {p.relative_to(checkout).as_posix()}")
    e = m["execution"]
    e.update(started_at=None, ended_at=None, base_commit=base,
             prompt_sha256=digest(template), config_sha256=digest((checkout / "experiments/config/version-2-baseline.yaml").read_bytes()),
             fixture_sha256=digest(("\n".join(fixture_lines) + "\n").encode()),
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
    m["outputs"].update(selection_document=f"docs/agent-runs/{run_id}/hardware-feature-selection.md",
                         structured_result=f"results/{run_id}/hardware-feature.json")
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


def capture(argv, cwd, prompt, directory, timeout):
    start = now()
    tick = time.monotonic()
    state, reason, code = "completed", None, None
    with (directory / "stdout.jsonl").open("xb") as out, (directory / "stderr.txt").open("xb") as err:
        p = None
        try:
            p = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=out, stderr=err,
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


def telemetry(path, adapter):
    tokens = dict(input=None, output=None, cached=None, reasoning=None, total=None,
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
            if tokens["input"] is not None and tokens["output"] is not None:
                tokens["total"] = tokens["input"] + tokens["output"]
            tokens["availability_note"] = "Codex turn.completed usage; cached is included in input; reasoning unavailable."
    return tokens


def command_metrics(path, adapter):
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
        if e.get("type") == "item.completed" and item.get("type") in {"command_execution", "mcp_tool_call", "web_search", "file_change"}:
            items[item["id"]] = item
    if not valid_stream:
        return dict(tool_calls=None, failed_commands=None)
    commands = [i for i in items.values() if i["type"] == "command_execution"]
    failed = sum(i.get("exit_code") not in (0, None) for i in commands)
    return dict(tool_calls=len(items), failed_commands=failed)


def execute(a):
    directory = Path(a.directory).resolve()
    m = read(directory / "run-manifest.json")
    profile = read(directory / "profile.json")
    validate_schema(m, "run-manifest.schema.json")
    validate_schema(profile, "runner-profile.schema.json")
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
    # A reviewed receipt is evidence, not a bypass flag. It is tied to this profile/baseline.
    for key, expected in (("base_commit", m["execution"]["base_commit"]), ("profile_sha256", m["agent"]["configuration_sha256"])):
        if receipt.get(key) != expected:
            raise ValueError(f"sandbox preflight receipt mismatch: {key}")
    for check in ("idf_build", "compiler", "ninja", "git", "temp_write", "network_policy", "read_isolation", "settings_inventory"):
        if receipt.get("checks", {}).get(check) != "pass":
            raise ValueError(f"sandbox preflight has not passed: {check}")
    if not receipt.get("evidence"):
        raise ValueError("sandbox receipt needs evidence file hashes")
    from benchmark_support import verify_evidence
    verify_evidence({"operator": {"evidence": receipt["evidence"]}}, Path(a.receipt).resolve().parent)
    argv = [s.replace("{checkout}", str(checkout)).replace("{model}", profile["model"]) for s in profile["argv"]]
    actual_version = subprocess.check_output(profile["version_argv"], encoding="utf-8", timeout=30).strip()
    if actual_version != profile["agent_version"]:
        raise ValueError(f"CLI version mismatch: {actual_version}")
    m["operator"]["status"] = "running"
    m["execution"]["started_at"] = now()
    save(directory / "run-manifest.json", m)
    r = capture(argv, checkout, prompt, directory, m["execution"]["timeout_seconds"])
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
    if result_path.is_file():
        candidate = read(result_path)
        try:
            validate_schema(candidate, "hardware-feature-result.schema.json")
            if candidate["run_id"] != m["run_id"] or candidate["experiment_id"] != m["experiment_id"]:
                raise ValueError("result ID mismatch")
            candidate["implementation"]["commit"] = implementation
            normalized_result = candidate
            m["outputs"].update(build_status=candidate["implementation"]["build"]["status"],
                                 automated_test_status=candidate["implementation"]["automated_tests"]["status"],
                                 hardware_verification_status=candidate["implementation"]["hardware_result"])
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
        tree = indexed("write-tree").decode().strip()
    record = git("-c", "user.name=Benchmark", "-c", "user.email=benchmark@localhost", "commit-tree", tree,
                 *parents, "-m", f"Preserve {m['run_id']}; implementation {implementation}", cwd=archive)
    git("update-ref", f"refs/heads/{branch}", record, prior.stdout.strip() if prior.returncode == 0 else "0"*40, cwd=archive)
    save(directory / "run-manifest.json", m)
    print(f"Local archive branch: {branch}; record {record}; implementation {implementation}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
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
