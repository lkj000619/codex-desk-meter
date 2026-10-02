"""Portable source/evidence package with an independent restoration check."""
import copy
from pathlib import Path
import shutil
import subprocess

from benchmark_support import digest, read, save, validate_operator, validate_schema, verify_evidence


def safe_path(root, name):
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name or name.startswith("/")
            or any(part in {"", ".", ".."} for part in name.split("/"))):
        raise ValueError("unsafe package path: " + str(name))
    root = Path(root).resolve()
    result = root / name
    if (not result.resolve().is_relative_to(root) or any(part.is_symlink() for part in (result, *result.parents) if part != root)
            or ".git" in name.split("/")):
        raise ValueError("unsafe package path: " + name)
    return result


def result_evidence_paths(result):
    paths = set()
    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"evidence", "snapshot_paths", "selection_document_evidence"} and isinstance(child, list):
                    paths.update(child)
                else:
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(result)
    return sorted(paths)


def _git(*args, cwd):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True, encoding="utf-8", stderr=subprocess.PIPE).strip()


def verify_report_dependencies(manifest, root):
    if "execution-preflight.json" in manifest["operator"]["evidence"]:
        receipt = read(Path(root) / "execution-preflight.json")
        verify_evidence({"operator": {"evidence": {"preflight-evidence/" + name: expected
                                                  for name, expected in receipt["evidence"].items()}}}, root)
    for name in ("reference-review.json", "feedback.json"):
        if name not in manifest["operator"]["evidence"]:
            continue
        report = read(Path(root) / name)
        entries = (report["evidence"] if name == "feedback.json" else
                   [value for item in report["items"].values() for value in item.get("evidence", [])])
        verify_evidence({"operator": {"evidence": {
            value.get("packaged_path", value["path"]): value["sha256"] for value in entries}}}, root)


def create_package(directory, destination):
    from benchmark import _check_e2e_manifest_join, _load_e2e_validator
    directory, destination = Path(directory).resolve(), Path(destination).resolve()
    manifest = read(directory / "run-manifest.json")
    validate_schema(manifest, "run-manifest.schema.json")
    validate_operator(manifest)
    if manifest["operator"]["status"] not in {"completed", "timeout", "aborted", "environment_failed"}:
        raise ValueError("package needs a terminal run")
    checkout = Path(manifest["execution"]["worktree"]).resolve()
    if destination.is_relative_to(directory) or directory.is_relative_to(destination):
        raise ValueError("package destination must be separate from the original run")
    implementation = manifest["outputs"]["implementation_commit"]
    if not implementation or _git("rev-parse", "HEAD", cwd=checkout) != implementation or _git("status", "--porcelain", cwd=checkout):
        raise ValueError("freeze source before creating an evidence package")
    verify_evidence(manifest, directory)
    verify_report_dependencies(manifest, directory)
    sources = {}
    for name in manifest["operator"]["evidence"]:
        sources["operator/" + name] = safe_path(directory, name)
    comparison = manifest["operator"].get("comparison")
    if comparison:
        from comparison_manager import _load
        from reference_inputs import validate_reference
        ledger_path = Path(comparison["ledger"])
        ledger = _load(ledger_path)
        if ledger["reference_inputs_sha256"] != comparison["reference_inputs_sha256"]:
            raise ValueError("package reference identity mismatch")
        reference_path = Path(ledger["reference_inputs"])
        _, reference_files = validate_reference(reference_path)
        for name in reference_files:
            sources["operator/reference/" + name] = safe_path(reference_path.parent, name)
        sources["operator/comparison-ledger.json"] = ledger_path
    result_path = safe_path(checkout, manifest["outputs"]["structured_result"])
    result, evaluation = None, None
    if result_path.is_file():
        if manifest["experiment_id"] != "version-2-end-to-end-v1":
            raise ValueError("portable result packaging currently requires the E2E contract")
        result = read(result_path)
        evaluation_path = directory / "e2e-evaluation-manifest.json"
        evaluation = read(evaluation_path)
        _check_e2e_manifest_join(evaluation, manifest, result)
        for name in result_evidence_paths(result):
            source = safe_path(checkout, name)
            if not source.is_file():
                raise ValueError("missing evidence: " + name)
            sources["checkout/" + name] = source
        _load_e2e_validator().validate_result(result, manifest=evaluation, evidence_root=checkout,
                                            manifest_root=checkout if (checkout / result["manifest"]["path"]).exists() else directory)
        sources["operator/raw-result.json"] = result_path
    build = checkout / "build"
    artifact_names = []
    if build.is_dir():
        for source in build.rglob("*"):
            if source.is_file() and source.suffix in {".bin", ".elf", ".map"}:
                name = source.relative_to(checkout).as_posix()
                safe_path(checkout, name)
                sources["checkout/" + name] = source
                artifact_names.append(name)
    if result is not None and result["build"]["status"] == "pass":
        required = (any(name.endswith(".elf") for name in artifact_names),
                    any(name.endswith(".map") for name in artifact_names),
                    any(name.endswith("bootloader.bin") for name in artifact_names),
                    any(name.endswith("partition-table.bin") for name in artifact_names),
                    any(name.endswith(".bin") and "/bootloader/" not in name and "/partition_table/" not in name for name in artifact_names))
        if not all(required):
            raise ValueError("passing firmware build requires app/ELF/map/bootloader/partition artifacts")
    if (checkout / "sdkconfig").is_file():
        sources["checkout/sdkconfig"] = checkout / "sdkconfig"
    for name, source in sources.items():
        safe_path(destination, name)
        if source.is_symlink() or not source.is_file():
            raise ValueError("missing or unsafe evidence: " + name)
    destination.mkdir(parents=True, exist_ok=False)
    source_bundle = destination / "source/implementation.bundle"
    source_bundle.parent.mkdir()
    _git("bundle", "create", str(source_bundle), "HEAD", cwd=checkout)
    for name, source in sources.items():
        target = safe_path(destination, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    save(destination / "operator/run-manifest.json", manifest)
    if result is not None:
        normalized = copy.deepcopy(result)
        normalized["manifest"]["path"] = manifest["outputs"]["evaluation_manifest"]
        target = safe_path(destination, "checkout/" + manifest["outputs"]["structured_result"])
        target.parent.mkdir(parents=True, exist_ok=True)
        save(target, normalized)
        target = safe_path(destination, "checkout/" + normalized["manifest"]["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        save(target, evaluation)
    files = {path.relative_to(destination).as_posix(): {"sha256": digest(path.read_bytes()), "bytes": path.stat().st_size}
             for path in destination.rglob("*") if path.is_file()}
    package = {"schema_version": 1, "run_id": manifest["run_id"], "implementation_commit": implementation,
               "source_bundle": "source/implementation.bundle", "files": files,
               "result": None if result is None else manifest["outputs"]["structured_result"],
               "evaluation_manifest": None if result is None else manifest["outputs"]["evaluation_manifest"],
               "artifact_paths": artifact_names, "original_worktree": str(checkout)}
    save(destination / "package-manifest.json", package)
    return {"package": str(destination), "files": len(files),
            "package_manifest_sha256": digest((destination / "package-manifest.json").read_bytes())}


def restore_package(package_root, destination, expected_sha256=None):
    from benchmark import _check_e2e_manifest_join, _load_e2e_validator
    package_root, destination = Path(package_root).resolve(), Path(destination).resolve()
    manifest_path = package_root / "package-manifest.json"
    if expected_sha256 is not None and digest(manifest_path.read_bytes()) != expected_sha256:
        raise ValueError("package manifest hash mismatch")
    package = read(manifest_path)
    if package.get("schema_version") != 1 or not isinstance(package.get("files"), dict):
        raise ValueError("invalid package manifest")
    if destination.exists() or destination.is_relative_to(package_root) or package_root.is_relative_to(destination):
        raise ValueError("restore requires a new independent destination")
    for name, metadata in package["files"].items():
        source = safe_path(package_root, name)
        safe_path(destination, name)
        if not source.is_file() or source.stat().st_size != metadata["bytes"] or digest(source.read_bytes()) != metadata["sha256"]:
            raise ValueError("package file hash mismatch: " + name)
    actual = {path.relative_to(package_root).as_posix() for path in package_root.rglob("*") if path.is_file()}
    if actual != set(package["files"]) | {"package-manifest.json"}:
        raise ValueError("package has unlisted or missing files")
    bundle = safe_path(package_root, package["source_bundle"])
    if package["source_bundle"] not in package["files"]:
        raise ValueError("source bundle is not in package inventory")
    destination.mkdir(parents=True)
    checkout = destination / "checkout"
    _git("clone", "--quiet", str(bundle), str(checkout), cwd=destination)
    _git("checkout", "--quiet", "--detach", package["implementation_commit"], cwd=checkout)
    _git("remote", "remove", "origin", cwd=checkout)
    if _git("rev-parse", "HEAD", cwd=checkout) != package["implementation_commit"]:
        raise ValueError("restored source commit mismatch")
    for name in package["files"]:
        if name.startswith("checkout/") or name.startswith("operator/"):
            target = safe_path(destination, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(safe_path(package_root, name), target)
    valid = False
    operator = read(destination / "operator/run-manifest.json")
    validate_schema(operator, "run-manifest.schema.json")
    validate_operator(operator)
    verify_evidence(operator, destination / "operator")
    verify_report_dependencies(operator, destination / "operator")
    if operator["run_id"] != package["run_id"] or operator["outputs"]["implementation_commit"] != package["implementation_commit"]:
        raise ValueError("restored package/operator identity mismatch")
    if operator["operator"].get("comparison"):
        from reference_inputs import validate_reference
        reference_path = destination / "operator/reference/reference-inputs.json"
        if digest(reference_path.read_bytes()) != operator["operator"]["comparison"]["reference_inputs_sha256"]:
            raise ValueError("restored reference identity mismatch")
        validate_reference(reference_path)
    if package["result"] is not None:
        result_path = safe_path(checkout, package["result"])
        evaluation_path = safe_path(checkout, package["evaluation_manifest"])
        _check_e2e_manifest_join(read(evaluation_path), operator, read(result_path))
        _load_e2e_validator().validate_result(read(result_path), manifest=read(evaluation_path),
                                            evidence_root=checkout, manifest_root=checkout)
        valid = True
    # Keep provenance bytes; expose a usable manifest for later summaries.
    shutil.copyfile(destination / "operator/run-manifest.json", destination / "operator/raw-run-manifest.json")
    operator["execution"]["worktree"] = str(checkout)
    save(destination / "operator/run-manifest.json", operator)
    report = {"run_id": package["run_id"], "implementation_commit": package["implementation_commit"],
              "restored_root": str(destination), "result_valid": valid,
              "manifest_identity_verified": expected_sha256 is not None,
              "package_manifest_sha256": digest(manifest_path.read_bytes()),
              "original_checkout_used": False, "files_verified": len(package["files"])}
    save(destination / "restore-report.json", report)
    return report
