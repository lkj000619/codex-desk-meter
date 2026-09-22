"""Summarize valid benchmark repetitions without authorizing or executing runs."""

import argparse
import importlib.util
import json
import statistics
from pathlib import Path

from benchmark_support import read, validate_operator, validate_schema


ROOT = Path(__file__).resolve().parents[1]


def _load_module(filename, name):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"cannot load {filename}")
    spec.loader.exec_module(module)
    return module


def _archive_root(path):
    path = path.resolve()
    if path.parent.parent.name == "results" and path.parent.name:
        return path.parent.parent.parent
    return None


def _existing_candidates(paths):
    seen = set()
    for path in paths:
        if path is None:
            continue
        path = Path(path)
        key = str(path.resolve())
        if key not in seen:
            seen.add(key)
            if path.is_file():
                yield path


def _result_path_candidates(manifest_path, manifest):
    output = Path(manifest["outputs"]["structured_result"])
    archive_root = _archive_root(manifest_path)
    worktree = Path(manifest["execution"]["worktree"])
    return _existing_candidates((
        manifest_path.parent / output.name,
        None if archive_root is None else archive_root / output,
        worktree / output,
    ))


def _evaluation_path_candidates(manifest_path, manifest):
    output = manifest["outputs"].get("evaluation_manifest")
    if not output:
        return iter(())
    output = Path(output)
    archive_root = _archive_root(manifest_path)
    worktree = Path(manifest["execution"]["worktree"])
    return _existing_candidates((
        manifest_path.parent / output.name,
        manifest_path.parent / "e2e-evaluation-manifest.json",
        None if archive_root is None else archive_root / output,
        worktree / output,
        worktree.parent / "e2e-evaluation-manifest.json",
    ))


def _load_valid_result(manifest_path, manifest):
    result_candidates = list(_result_path_candidates(manifest_path, manifest))
    if not result_candidates:
        return None
    result_path = result_candidates[0]
    result = json.loads(result_path.read_text(encoding="utf-8-sig"))
    if manifest["experiment_id"] == "version-2-end-to-end-v1":
        evaluation_paths = list(_evaluation_path_candidates(manifest_path, manifest))
        if not evaluation_paths:
            return None
        evaluation_path = evaluation_paths[0]
        evaluation_manifest = json.loads(evaluation_path.read_text(encoding="utf-8-sig"))
        # Validate both JSON objects before reading join fields. A malformed
        # copied artifact must be excluded instead of aborting the summary.
        validate_schema(result, "end-to-end-result.schema.json")
        validate_schema(evaluation_manifest, "end-to-end-manifest.schema.json")
        _check_e2e_identity(manifest, evaluation_manifest, result)
        validator = _load_module("validate-end-to-end-result.py", "summary_e2e_validator")
        archive_root = _archive_root(manifest_path)
        evidence_roots = [root for root in (archive_root, Path(manifest["execution"]["worktree"]), manifest_path.parent) if root is not None]
        for evidence_root in evidence_roots:
            try:
                validator.validate_result(
                    result,
                    manifest=evaluation_manifest,
                    evidence_root=evidence_root,
                    manifest_root=evidence_root,
                )
                return result
            except (validator.ValidationError, OSError, ValueError):
                continue
        return None
    historical = _load_module("validate-experiment-result.py", "summary_historical_validator")
    validate_schema(result, "hardware-feature-result.schema.json")
    try:
        historical.validate_result(result, manifest)
    except (historical.ValidationError, OSError, ValueError):
        return None
    return result


def _check_e2e_identity(run_manifest, evaluation_manifest, result):
    """Require one operator/evaluation/result/baseline identity chain."""
    if evaluation_manifest["run_id"] != run_manifest["run_id"]:
        raise ValueError("E2E evaluation run_id does not match operator manifest")
    if evaluation_manifest["manifest_id"] != run_manifest["run_id"]:
        raise ValueError("E2E evaluation manifest_id does not match operator run_id")
    if evaluation_manifest["experiment_id"] != run_manifest["experiment_id"]:
        raise ValueError("E2E evaluation experiment_id does not match operator manifest")
    if evaluation_manifest["baseline_id"] != run_manifest["baseline_id"]:
        raise ValueError("E2E evaluation baseline_id does not match operator manifest")
    if evaluation_manifest["baseline_ref"] != run_manifest["baseline_ref"]:
        raise ValueError("E2E evaluation baseline_ref does not match operator manifest")
    if evaluation_manifest["execution"]["base_commit"] != run_manifest["execution"]["base_commit"]:
        raise ValueError("E2E evaluation base_commit does not match operator manifest")

    result_reference = evaluation_manifest.get("result_id", evaluation_manifest.get("result_reference"))
    if result_reference != result["result_id"]:
        raise ValueError("E2E evaluation result reference does not match result")
    if result["run_id"] != run_manifest["run_id"]:
        raise ValueError("E2E result run_id does not match operator manifest")
    if result["experiment_id"] != run_manifest["experiment_id"]:
        raise ValueError("E2E result experiment_id does not match operator manifest")
    if result["manifest_id"] != evaluation_manifest["manifest_id"]:
        raise ValueError("E2E result manifest_id does not match evaluation manifest")
    if result["manifest"]["id"] != evaluation_manifest["manifest_id"]:
        raise ValueError("E2E result manifest.id does not match evaluation manifest")
    if result["baseline_id"] != run_manifest["baseline_id"]:
        raise ValueError("E2E result baseline_id does not match operator manifest")
    if result["baseline"]["id"] != run_manifest["baseline_id"]:
        raise ValueError("E2E result baseline.id does not match operator manifest")
    if result["baseline"]["ref"] != run_manifest["baseline_ref"]:
        raise ValueError("E2E result baseline.ref does not match operator manifest")
    if result["baseline"]["commit"] != run_manifest["execution"]["base_commit"]:
        raise ValueError("E2E result baseline.commit does not match operator manifest")


def _comparison_group(manifest):
    """Return a compact label for a full comparison identity."""
    agent = manifest["agent"]
    execution = manifest["execution"]
    agent_label = "/".join(str(agent[key]) for key in ("provider", "product", "interface", "model", "reasoning"))
    agent_version = str(agent["agent_version"])
    config = agent.get("configuration_sha256")
    config_label = "none" if config is None else str(config)[:12]
    return " | ".join((
        f"agent={agent_label}@{agent_version}",
        f"experiment={manifest['experiment_id']}",
        f"baseline={manifest['baseline_id']}@{manifest['baseline_ref']}",
        f"commit={str(execution['base_commit'])[:12]}",
        f"inputs={str(execution['input_bundle_sha256'])[:12]}",
        f"config={config_label}",
    ))


def _comparison_key(manifest):
    """Use complete values for grouping; display labels are intentionally short."""
    agent = manifest["agent"]
    execution = manifest["execution"]
    return (
        manifest["experiment_id"],
        manifest["baseline_id"],
        manifest["baseline_ref"],
        execution["base_commit"],
        execution["input_bundle_sha256"],
        tuple(agent.get(key) for key in (
            "provider", "product", "interface", "agent_version", "model", "reasoning", "configuration_sha256",
        )),
    )


def _success(manifest, result):
    if manifest["experiment_id"] == "version-2-end-to-end-v1":
        return result.get("product_pass") is True
    core = result.get("core_requirements", {})
    return bool(core) and all(entry.get("status") == "pass" for entry in core.values())


def collect_records(manifest_paths):
    """Return valid, non-pilot completed records and excluded-input counts."""
    records = []
    excluded = {"pilot": 0, "incomplete": 0, "invalid": 0, "duplicate": 0}
    seen_paths = set()
    seen_run_ids = set()
    for path in manifest_paths:
        path = Path(path)
        path_key = str(path.resolve())
        if path_key in seen_paths:
            excluded["duplicate"] += 1
            continue
        seen_paths.add(path_key)
        try:
            manifest = read(path)
            # Run-manifest schema validation must precede every nested field
            # access so {} and malformed documents are ordinary invalid input.
            validate_schema(manifest, "run-manifest.schema.json")
            if manifest["operator"]["phase"] == "pilot":
                excluded["pilot"] += 1
                continue
            if manifest["operator"]["status"] != "completed":
                excluded["incomplete"] += 1
                continue
            validate_operator(manifest)
            result = _load_valid_result(path, manifest)
        except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
            result = None
        if result is None:
            excluded["invalid"] += 1
            continue
        run_id = manifest["run_id"]
        if run_id in seen_run_ids:
            excluded["duplicate"] += 1
            continue
        seen_run_ids.add(run_id)
        tokens = manifest["measurement"]["tokens"]
        group_key = _comparison_key(manifest)
        records.append({
            "manifest": manifest,
            "result": result,
            "path": path,
            "group": _comparison_group(manifest),
            "group_key": group_key,
            "success": _success(manifest, result),
            "seconds": manifest["measurement"]["wall_clock_seconds"],
            "tokens": tokens["total"],
        })
    return records, excluded


def _number(value):
    return "—" if value is None else f"{value:g}" if isinstance(value, float) else str(value)


def _range(values):
    if not values:
        return "—"
    return f"{_number(min(values))}–{_number(max(values))}"


def render_summary(records, excluded, min_repetitions):
    rows = [
        "# Benchmark results",
        "",
        "Only completed results that pass the applicable schema and semantic validator are included. Pilot runs are excluded; duplicate run identities are excluded as well.",
        "",
        "## Valid runs",
        "",
        "| Run | Comparison group | Success | Seconds | Normalized tokens | Build | Hardware | Result |",
        "|---|---|---:|---:|---:|---|---|---|",
    ]

    def cell(value):
        return "—" if value is None else str(value).replace("|", "\\|").replace("\n", " ")

    for record in records:
        manifest = record["manifest"]
        result = record["result"]
        if manifest["experiment_id"] == "version-2-end-to-end-v1":
            build = result["build"]["status"]
            hardware = result["hardware"]["status"]
        else:
            build = result["implementation"]["build"]["status"]
            hardware = result["implementation"]["hardware_result"]
        values = (
            manifest["run_id"], record["group"], "yes" if record["success"] else "no",
            record["seconds"], record["tokens"], build, hardware,
            manifest["outputs"]["structured_result"],
        )
        rows.append("| " + " | ".join(cell(value) for value in values) + " |")

    groups = {}
    for record in records:
        key = record["group_key"] if "group_key" in record else record["group"]
        bucket = groups.setdefault(key, {"label": record["group"], "records": []})
        bucket["records"].append(record)
    rows.extend([
        "",
        "## Comparison groups",
        "",
        f"Minimum repetitions per comparison group: **{min_repetitions}**.",
        "",
        "| Comparison group | Valid repetitions | Eligible | Success ratio | Seconds median | Seconds range | Tokens median | Tokens range |",
        "|---|---:|---|---:|---:|---|---:|---|",
    ])
    for bucket in sorted(groups.values(), key=lambda value: value["label"]):
        group = bucket["label"]
        values = bucket["records"]
        seconds = [record["seconds"] for record in values if isinstance(record["seconds"], (int, float))]
        tokens = [record["tokens"] for record in values if isinstance(record["tokens"], int) and not isinstance(record["tokens"], bool)]
        eligible = len(values) >= min_repetitions
        rows.append(
            "| " + " | ".join((
                cell(group), str(len(values)), "yes" if eligible else "no",
                f"{sum(record['success'] for record in values) / len(values):.3f}",
                _number(statistics.median(seconds)) if seconds else "—", _range(seconds),
                _number(statistics.median(tokens)) if tokens else "—", _range(tokens),
            )) + " |"
        )
    rows.extend([
        "",
        "## Exclusions",
        "",
        f"Pilot: {excluded.get('pilot', 0)}; incomplete: {excluded.get('incomplete', 0)}; invalid or semantically unjoined: {excluded.get('invalid', 0)}; duplicate path/run identity: {excluded.get('duplicate', 0)}.",
        "",
    ])
    return "\n".join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifests", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--min-repetitions", type=int, default=3, choices=range(1, 101), metavar="1..100")
    args = parser.parse_args()
    records, excluded = collect_records(args.manifests)
    # Exclusive creation prevents accidentally replacing a reviewed result index.
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(render_summary(records, excluded, args.min_repetitions) + "\n")


if __name__ == "__main__":
    main()
