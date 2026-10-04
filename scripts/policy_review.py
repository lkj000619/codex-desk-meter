"""Operator-owned, evidence-bound policy judgments; never infer them from logs.

The sidecar digest detects modification, not reviewer impersonation. Its trust
boundary is the operator directory outside the candidate checkout, like the
operator manifest itself. Copy the sidecar and its evidence when archiving.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from benchmark_support import digest, read, utc, validate_operator, validate_schema, verify_evidence

REVIEW_NAME = "policy-review.json"
RAW_EVIDENCE = ("stdout.jsonl", "stderr.txt", "prompt.txt", "profile.json")
STATUSES = {"eligible", "invalid_for_comparison", "unverified"}


def _canonical_digest(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _operator_root(manifest, manifest_path):
    root = Path(manifest_path).resolve().parent
    if root.is_relative_to(Path(manifest["execution"]["worktree"]).resolve()):
        raise ValueError("policy review must be stored outside the candidate checkout")
    return root


def _binding(manifest, root):
    operator, execution = manifest["operator"], manifest["execution"]
    if operator["status"] not in {"completed", "aborted", "timeout", "environment_failed"}:
        raise ValueError("policy review requires a terminal attempt")
    evidence = {name: operator["evidence"][name] for name in RAW_EVIDENCE}
    verify_evidence({"operator": {"evidence": evidence}}, root)
    if (evidence["profile.json"] != manifest["agent"]["configuration_sha256"]
            or _canonical_digest(read(root / "profile.json")) != execution["profile_sha256"]):
        raise ValueError("policy review profile identity mismatch")
    return {
        "run_id": manifest["run_id"], "experiment_id": manifest["experiment_id"],
        "baseline_id": manifest["baseline_id"], "baseline_ref": manifest["baseline_ref"],
        "agent": manifest["agent"],
        "execution": {key: value for key, value in execution.items() if key != "worktree"},
        "status": operator["status"], "exit_code": operator["exit_code"],
        "delivered_prompt_sha256": operator["delivered_prompt_sha256"],
        "local_base_commit": operator["local_base_commit"],
        "user_interventions": manifest["measurement"]["user_interventions"],
        "raw_evidence": evidence, "raw_evidence_sha256": _canonical_digest(evidence),
    }


def _validate_decision(decision, manifest, root):
    if not isinstance(decision, dict) or decision.get("status") not in STATUSES:
        raise ValueError("policy status must be eligible, invalid_for_comparison or unverified")
    for field in ("reviewer", "reason", "intervention_review"):
        if not isinstance(decision.get(field), str) or not decision[field].strip():
            raise ValueError(f"policy review requires {field}")
    count = decision.get("user_interventions")
    measured_count = manifest["measurement"]["user_interventions"]
    if "user_interventions" not in decision or (measured_count is not None and count != measured_count):
        raise ValueError("policy review user_interventions does not match measurement")
    if count is not None and (type(count) is not int or count < 0):
        raise ValueError("policy review intervention count must be nonnegative or unknown")
    if decision["status"] == "eligible" and count is None:
        raise ValueError("eligible policy review requires known user_interventions")
    evidence = decision.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("policy review requires reviewer evidence")
    paths = set()
    for item in evidence:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"} or not isinstance(item["path"], str):
            raise ValueError("policy review evidence requires path and sha256")
        path = Path(item["path"])
        if path.is_absolute() or path.name == REVIEW_NAME or item["path"] in paths:
            raise ValueError("policy review evidence must be unique, relative and not self-referential")
        paths.add(item["path"])
        verify_evidence({"operator": {"evidence": {item["path"]: item["sha256"]}}}, root)


def create_review(manifest_path, decision):
    """Record an explicit operator judgment without changing the terminal manifest."""
    manifest_path = Path(manifest_path)
    manifest = read(manifest_path)
    validate_schema(manifest, "run-manifest.schema.json")
    validate_operator(manifest)
    root = _operator_root(manifest, manifest_path)
    _validate_decision(decision, manifest, root)
    review = {"schema_version": 1, "binding": _binding(manifest, root),
              "reviewed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
              "decision": decision}
    review["review_sha256"] = _canonical_digest(review)
    with (root / REVIEW_NAME).open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(review, ensure_ascii=False, indent=2) + "\n")
    return root / REVIEW_NAME


def validate_review(manifest, manifest_path):
    """Verify review integrity and evidence without requiring an eligible verdict."""
    root = _operator_root(manifest, manifest_path)
    review = read(root / REVIEW_NAME)
    if (not isinstance(review, dict) or set(review) != {"schema_version", "binding", "reviewed_at", "decision", "review_sha256"}
            or review["schema_version"] != 1):
        raise ValueError("invalid policy review format")
    body = {key: value for key, value in review.items() if key != "review_sha256"}
    if _canonical_digest(body) != review["review_sha256"]:
        raise ValueError("policy review digest mismatch")
    utc(review["reviewed_at"])
    if review["binding"] != _binding(manifest, root):
        raise ValueError("policy review run/profile/input/log/intervention identity mismatch")
    _validate_decision(review["decision"], manifest, root)
    return review


def review_eligibility(manifest, manifest_path):
    """Return (eligible, status, reason); legacy manifests retain prior behavior."""
    if not manifest["operator"].get("policy_review_required", False):
        return True, "legacy_not_required", "Review gate not applied retroactively."
    try:
        root = _operator_root(manifest, manifest_path)
        if not (root / REVIEW_NAME).is_file():
            return False, "missing", "Required operator policy review is missing."
        review = validate_review(manifest, manifest_path)
        decision = review["decision"]
        return decision["status"] == "eligible", decision["status"], decision["reason"]
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return False, "invalid_review", str(exc)
