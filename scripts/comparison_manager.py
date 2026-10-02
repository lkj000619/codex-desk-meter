"""Operator-owned first/follow-up lifecycle. Never edits the shared baseline."""
from contextlib import contextmanager
from datetime import datetime
import math
import re
from pathlib import Path
import shutil
import subprocess

from benchmark_support import KST, digest, read, save, validate_operator, validate_schema, verify_evidence

LIMITS = {"initial_seconds": 7200, "remediation_seconds": 7200, "remediation_rounds": 3}
REFERENCE_IDS = ["RM1", "RM2", "RM3", "RM4", "RM5"]
TERMINAL = {"completed", "timeout", "aborted", "environment_failed"}


@contextmanager
def locked(path):
    path = Path(path).resolve()
    marker = path.with_name(path.name + ".lock")
    try:
        handle = marker.open("x", encoding="ascii")
    except FileExistsError as error:
        raise ValueError("comparison is locked; inspect interrupted operation before recovery") from error
    try:
        handle.close()
        yield path
    finally:
        marker.unlink()


def _git(*args, cwd):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True, encoding="utf-8", stderr=subprocess.PIPE).strip()


def _load(path):
    state = read(path)
    if state.get("schema_version") != 1 or state.get("limits") != LIMITS:
        raise ValueError("invalid comparison limits/version")
    reference = Path(state["reference_inputs"])
    if digest(reference.read_bytes()) != state["reference_inputs_sha256"]:
        raise ValueError("frozen reference inputs changed")
    from reference_inputs import validate_reference
    validate_reference(reference)
    runs = state["runs"]
    if (not runs or len(runs) > 4 or [entry["round"] for entry in runs] != list(range(len(runs)))
            or len({entry["run_id"] for entry in runs}) != len(runs)):
        raise ValueError("invalid comparison round sequence")
    for entry in runs:
        if entry["elapsed_seconds"] is not None:
            value = entry["elapsed_seconds"]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError("invalid comparison cost")
        if entry["status"] not in TERMINAL | {"prepared", "running"}:
            raise ValueError("invalid comparison run status")
    return state


def _bound(directory):
    directory = Path(directory).resolve()
    manifest = read(directory / "run-manifest.json")
    validate_schema(manifest, "run-manifest.schema.json")
    validate_operator(manifest)
    connection = manifest["operator"]["comparison"]
    path = Path(connection["ledger"]).resolve()
    if path.is_relative_to(Path(manifest["execution"]["worktree"]).resolve()):
        raise ValueError("comparison ledger must stay outside candidate checkout")
    return directory, manifest, path


def _entry(state, manifest, directory):
    connection = manifest["operator"]["comparison"]
    entry = next((item for item in state["runs"] if item["run_id"] == manifest["run_id"]), None)
    if (entry is None or connection["comparison_id"] != state["comparison_id"]
            or connection["round"] != entry["round"] or Path(entry["directory"]).resolve() != directory
            or connection["starting_commit"] != entry["starting_commit"]
            or connection["reference_inputs_sha256"] != state["reference_inputs_sha256"]
            or connection["feedback_sha256"] != entry["feedback_sha256"]
            or manifest["execution"]["input_bundle_sha256"] != state["input_bundle_sha256"]
            or manifest["execution"]["base_commit"] != state["base_commit"]
            or manifest["execution"]["profile_sha256"] != state["profile_sha256"]):
        raise ValueError("comparison identity/input/profile mismatch")
    from benchmark import profile_digest
    profile_path = directory / "profile.json"
    if (profile_digest(read(profile_path)) != state["profile_sha256"]
            or digest(profile_path.read_bytes()) != manifest["agent"]["configuration_sha256"]):
        raise ValueError("comparison profile changed")
    return entry


def _connect(state, path, manifest, directory, round_number, starting_commit, feedback_hash=None):
    manifest["operator"]["comparison"] = {
        "ledger": str(path), "comparison_id": state["comparison_id"], "round": round_number,
        "starting_commit": starting_commit, "feedback_sha256": feedback_hash,
        "reference_status": "not_run", "reference_inputs_sha256": state["reference_inputs_sha256"],
    }
    entry = {"run_id": manifest["run_id"], "directory": str(directory), "round": round_number,
             "starting_commit": starting_commit, "status": "prepared", "reserved_seconds": 0,
             "elapsed_seconds": None, "reference_status": "not_run", "reviewed": False,
             "implementation_commit": None, "feedback_sha256": feedback_hash}
    state["runs"].append(entry)
    save(directory / "run-manifest.json", manifest)


def init_comparison(path, directory, reference_inputs):
    path, directory = Path(path).resolve(), Path(directory).resolve()
    manifest = read(directory / "run-manifest.json")
    validate_schema(manifest, "run-manifest.schema.json")
    validate_operator(manifest)
    if (manifest["experiment_id"] != "version-2-end-to-end-v1"
            or manifest["operator"]["phase"] != "benchmark" or manifest["operator"]["status"] != "prepared"
            or "comparison" in manifest["operator"]):
        raise ValueError("comparison requires a prepared E2E benchmark initial run")
    if path.is_relative_to(Path(manifest["execution"]["worktree"]).resolve()):
        raise ValueError("ledger must stay outside candidate checkout")
    reference_inputs = Path(reference_inputs).resolve()
    from reference_inputs import validate_reference
    reference, reference_files = validate_reference(reference_inputs)
    expected_reference = manifest["operator"]["evidence"].get("reference/reference-inputs.json")
    if expected_reference is not None and digest(reference_inputs.read_bytes()) != expected_reference:
        raise ValueError("selected reference does not match prepared baseline reference")
    path.parent.mkdir(parents=True, exist_ok=True)
    with locked(path):
        if path.exists():
            raise ValueError("comparison already exists")
        reference_root = path.with_name(path.stem + "-reference")
        reference_root.mkdir(exist_ok=False)
        for name in reference_files:
            target = reference_root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(reference_inputs.parent / name, target)
        reference_copy = reference_root / reference_inputs.name
        state = {"schema_version": 1, "comparison_id": manifest["run_id"], "state": "active",
                 "base_commit": manifest["execution"]["base_commit"],
                 "input_bundle_sha256": manifest["execution"]["input_bundle_sha256"],
                 "profile_sha256": manifest["execution"]["profile_sha256"], "limits": dict(LIMITS),
                 "reference_inputs": str(reference_copy), "reference_inputs_sha256": digest(reference_copy.read_bytes()),
                 "runs": []}
        _connect(state, path, manifest, directory, 0, manifest["operator"]["local_base_commit"])
        save(path, state)
    return state


def start_run(directory):
    directory, manifest, path = _bound(directory)
    with locked(path):
        state = _load(path)
        entry = _entry(state, manifest, directory)
        if state["state"] != "active":
            raise ValueError("comparison reached or stopped")
        if entry["status"] != "prepared" or any(item["status"] == "running" for item in state["runs"]):
            raise ValueError("comparison already running or run consumed")
        if entry is not state["runs"][-1]:
            raise ValueError("only the latest prepared round can execute")
        if entry["round"]:
            previous = state["runs"][-2]
            if not previous["reviewed"] or previous["implementation_commit"] != entry["starting_commit"]:
                raise ValueError("followup requires reviewed frozen previous source")
            feedback = directory / "feedback.json"
            if digest(feedback.read_bytes()) != entry["feedback_sha256"]:
                raise ValueError("feedback changed")
            spent = sum(item["elapsed_seconds"] or 0 for item in state["runs"] if item["round"])
            remaining = LIMITS["remediation_seconds"] - spent
        else:
            remaining = LIMITS["initial_seconds"]
        timeout = min(manifest["execution"]["timeout_seconds"], math.floor(remaining))
        if timeout < 1:
            raise ValueError("comparison budget exhausted")
        entry.update(status="running", reserved_seconds=timeout)
        save(path, state)
        return timeout


def finish_run(directory):
    directory, manifest, path = _bound(directory)
    with locked(path):
        state = _load(path)
        entry = _entry(state, manifest, directory)
        if entry["status"] != "running" or manifest["operator"]["status"] not in TERMINAL:
            raise ValueError("finish requires one running ledger entry and a terminal manifest")
        elapsed = manifest["measurement"]["wall_clock_seconds"]
        if elapsed is None:
            raise ValueError("unknown cost must be reconciled before another round")
        entry.update(status=manifest["operator"]["status"], elapsed_seconds=elapsed,
                     tokens=manifest["measurement"]["tokens"], terminal_manifest_sha256=digest((directory / "run-manifest.json").read_bytes()))
        save(path, state)


def review_run(directory, report):
    directory, manifest, path = _bound(directory)
    with locked(path):
        state = _load(path)
        entry = _entry(state, manifest, directory)
        if entry["status"] not in TERMINAL or entry["reviewed"]:
            raise ValueError("review requires an unreviewed terminal run")
        if digest((directory / "run-manifest.json").read_bytes()) != entry["terminal_manifest_sha256"]:
            raise ValueError("terminal manifest changed before reference review")
        if (report.get("run_id") != manifest["run_id"]
                or report.get("reference_inputs_sha256") != state["reference_inputs_sha256"]
                or set(report.get("items", {})) != set(REFERENCE_IDS)):
            raise ValueError("reference review identity/items mismatch")
        for key, item in report["items"].items():
            if item.get("status") not in {"pass", "partial", "fail", "not_run"}:
                raise ValueError("invalid reference status: " + key)
            evidence = item.get("evidence", [])
            if item["status"] != "not_run" and not evidence:
                raise ValueError("assessed reference item requires evidence: " + key)
            verify_evidence({"operator": {"evidence": {value["path"]: value["sha256"] for value in evidence}}}, directory)
            for value in evidence:
                manifest["operator"]["evidence"][value["path"]] = value["sha256"]
        from benchmark import verify_agent_inputs
        verify_agent_inputs(directory, manifest)
        checkout = Path(manifest["execution"]["worktree"])
        _git("add", "--all", cwd=checkout)
        if _git("diff", "--cached", "--name-only", cwd=checkout):
            _git("-c", "user.name=Benchmark", "-c", "user.email=benchmark@localhost", "commit",
                 "-m", "Freeze " + manifest["run_id"], cwd=checkout)
        implementation = _git("rev-parse", "HEAD", cwd=checkout)
        source_bundle = directory / "comparison-source.bundle"
        _git("bundle", "create", str(source_bundle), "HEAD", cwd=checkout)
        status = "pass" if all(item["status"] == "pass" for item in report["items"].values()) else "fail"
        review_path = directory / "reference-review.json"
        save(review_path, report)
        entry.update(reviewed=True, reference_status=status, implementation_commit=implementation,
                     source_bundle_sha256=digest(source_bundle.read_bytes()), reference_review_sha256=digest(review_path.read_bytes()))
        manifest["operator"]["comparison"]["reference_status"] = status
        manifest["operator"]["evidence"][review_path.name] = entry["reference_review_sha256"]
        manifest["operator"]["evidence"][source_bundle.name] = entry["source_bundle_sha256"]
        manifest["outputs"]["implementation_commit"] = implementation
        save(directory / "run-manifest.json", manifest)
        if status == "pass":
            state["state"] = "reached"
        save(path, state)


def prepare_followup(path, root, feedback):
    from benchmark import prepare_agent_inputs, git
    path, root = Path(path).resolve(), Path(root).resolve()
    with locked(path):
        state = _load(path)
        previous = state["runs"][-1]
        if state["state"] != "active":
            raise ValueError("comparison reached or stopped")
        if not previous["reviewed"] or previous["status"] not in TERMINAL:
            raise ValueError("followup requires previous review")
        if previous["round"] >= LIMITS["remediation_rounds"]:
            raise ValueError("remediation round limit exhausted")
        remaining = LIMITS["remediation_seconds"] - sum(item["elapsed_seconds"] or 0 for item in state["runs"] if item["round"])
        if remaining < 1:
            raise ValueError("remediation budget exhausted")
        if (feedback.get("previous_run_id") != previous["run_id"]
                or feedback.get("previous_commit") != previous["implementation_commit"]
                or not feedback.get("target_ids") or not feedback.get("observed") or not feedback.get("expected")
                or not feedback.get("evidence")):
            raise ValueError("feedback needs previous identity, targets, observation, expectation and evidence")
        if any(not re.fullmatch(r"(RM[1-5]|C[1-8]|F[1-9]|I[1-4])", key) for key in feedback["target_ids"]):
            raise ValueError("invalid feedback target")
        previous_directory = Path(previous["directory"])
        previous_checkout = Path(read(previous_directory / "run-manifest.json")["execution"]["worktree"]).resolve()
        if not str(root).isascii() or root.is_relative_to(previous_directory) or root.is_relative_to(previous_checkout):
            raise ValueError("followup root must be a separate ASCII directory outside the previous checkout")
        for value in feedback["evidence"]:
            evidence = Path(value["path"]).resolve()
            if not evidence.is_relative_to(previous_directory) or digest(evidence.read_bytes()) != value["sha256"]:
                raise ValueError("feedback evidence must match previous run")
        source_bundle = previous_directory / "comparison-source.bundle"
        if digest(source_bundle.read_bytes()) != previous["source_bundle_sha256"]:
            raise ValueError("frozen source bundle changed")
        manifest = read(previous_directory / "run-manifest.json")
        _entry(state, manifest, previous_directory)
        # Verify sidecars against the prior frozen hashes before reusing them.
        verify_evidence(manifest, previous_directory)
        root.mkdir(parents=True, exist_ok=True)
        date = datetime.now(KST).strftime("%Y%m%d")
        suffix = "-" + manifest["run_id"][9:].rsplit("-r", 1)[0]
        for repetition in range(1, 100):
            directory = root / f"{date}{suffix}-r{repetition:02d}"
            if (directory == previous_directory or any(directory == Path(item["directory"]) for item in state["runs"])
                    or directory.name in {item["run_id"] for item in state["runs"]}):
                continue
            try:
                directory.mkdir()
                break
            except FileExistsError:
                continue
        else:
            raise ValueError("daily repetition slots exhausted")
        checkout = directory / "checkout"
        _git("clone", "--quiet", "--no-hardlinks", str(source_bundle), str(checkout), cwd=directory)
        _git("checkout", "--quiet", "--detach", previous["implementation_commit"], cwd=checkout)
        _git("remote", "remove", "origin", cwd=checkout)
        for candidate in (checkout / ".benchmark-inputs", checkout / "results" / manifest["run_id"],
                          checkout / "docs/agent-runs" / manifest["run_id"]):
            if candidate.exists() and candidate.resolve().is_relative_to(checkout):
                shutil.rmtree(candidate)
        shutil.copyfile(previous_directory / "profile.json", directory / "profile.json")
        inventory = previous_directory / "candidate-inputs.json"
        if inventory.is_file():
            shutil.copyfile(inventory, directory / inventory.name)
        feedback = dict(feedback, remaining_rounds=LIMITS["remediation_rounds"] - previous["round"],
                        remaining_seconds=remaining)
        feedback_evidence = {}
        for index, value in enumerate(feedback["evidence"]):
            name = f"feedback-evidence/{index:03d}-{Path(value['path']).name}"
            target = directory / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(value["path"], target)
            feedback_evidence[name] = value["sha256"]
        feedback["evidence"] = [dict(value, packaged_path=name) for value, name in zip(feedback["evidence"], feedback_evidence)]
        save(directory / "feedback.json", feedback)
        prompt = ("Continue your own frozen implementation. Preserve the baseline inputs and submit results for <run-id>.\n"
                  "Operator feedback (observations and expected behavior):\n" + (directory / "feedback.json").read_text(encoding="utf-8"))
        manifest["run_id"] = directory.name
        prompt = prompt.replace("<run-id>", directory.name).encode("utf-8")
        (directory / "prompt.txt").write_bytes(prompt)
        manifest["operator"].update(status="prepared", reason=None, exit_code=None, repetition=repetition,
                                    local_base_commit=None, delivered_prompt_sha256=digest(prompt), evidence={})
        manifest["execution"].update(worktree=str(checkout), started_at=None, ended_at=None, timeout_seconds=min(7200, math.floor(remaining)))
        manifest["measurement"].update(wall_clock_seconds=None, tool_calls=None, failed_commands=None, user_interventions=None)
        manifest["measurement"]["tokens"] = {key: None if key not in {"availability_note", "provider_total_definition"} else value
                                              for key, value in manifest["measurement"]["tokens"].items()}
        run_id = manifest["run_id"]
        manifest["outputs"].update(implementation_commit=None, build_status="not_run", automated_test_status="not_run",
                                   hardware_verification_status="not_run", selection_document=f"docs/agent-runs/{run_id}/hardware-feature-selection.md",
                                   structured_result=f"results/{run_id}/end-to-end-result.json", evaluation_manifest=f"results/{run_id}/e2e-evaluation-manifest.json")
        evaluation_path = previous_directory / "e2e-evaluation-manifest.json"
        if evaluation_path.is_file():
            evaluation = read(evaluation_path)
        else:
            evaluation = {"schema_version": 1, "baseline_id": manifest["baseline_id"], "baseline_ref": manifest["baseline_ref"],
                          "experiment_id": manifest["experiment_id"], "execution": {"base_commit": manifest["execution"]["base_commit"]}}
        evaluation.pop("result_id", None)
        evaluation.update(manifest_id=run_id, run_id=run_id, result_reference=run_id)
        save(directory / "e2e-evaluation-manifest.json", evaluation)
        _connect(state, path, manifest, directory, previous["round"] + 1, previous["implementation_commit"],
                 digest((directory / "feedback.json").read_bytes()))
        manifest["operator"]["evidence"].update(feedback_evidence)
        manifest["operator"]["evidence"]["feedback.json"] = digest((directory / "feedback.json").read_bytes())
        prepare_agent_inputs(directory, manifest)
        git("add", "--all", cwd=checkout)
        git("-c", "user.name=Benchmark", "-c", "user.email=benchmark@localhost", "commit", "-m", "Followup immutable run inputs", cwd=checkout)
        manifest["operator"]["local_base_commit"] = git("rev-parse", "HEAD", cwd=checkout)
        validate_schema(manifest, "run-manifest.schema.json")
        validate_operator(manifest)
        save(directory / "run-manifest.json", manifest)
        save(path, state)
        return directory
