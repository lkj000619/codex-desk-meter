"""Shared operator validation; never infer product success from process success."""
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KST = timezone(timedelta(hours=9))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def validate_schema(value, name):
    from jsonschema import Draft202012Validator, FormatChecker
    schema = read(ROOT / "experiments/schema" / name)
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value))
    if errors:
        e = errors[0]
        raise ValueError(f"{name}:{'.'.join(map(str, e.absolute_path))}: {e.message}")


def utc(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("operator timestamps must be UTC RFC3339 ending in Z")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_operator(m):
    o, e = m["operator"], m["execution"]
    validate_schema(o, "operator.schema.json")
    suffix = f"-r{o['repetition']:02d}"
    if not m["run_id"].endswith(suffix):
        raise ValueError("run ID/repetition mismatch")
    datetime.strptime(m["run_id"][:8], "%Y%m%d")
    if not re.fullmatch(r"experiment/[a-z0-9-]+/[a-z0-9-]+/[a-z0-9-]+", e["branch"]):
        raise ValueError("expected experiment/provider/product/model branch")
    state = o["status"]
    start, end = e["started_at"], e["ended_at"]
    elapsed = m["measurement"]["wall_clock_seconds"]
    if state == "prepared" and any(x is not None for x in (start, end, elapsed, o["exit_code"])):
        raise ValueError("prepared run cannot have execution measurements")
    if start is not None:
        if utc(start).astimezone(KST).strftime("%Y%m%d") != m["run_id"][:8]:
            raise ValueError("run date must match actual start date in Asia/Seoul")
    if state == "running" and (start is None or end is not None):
        raise ValueError("running requires start and no end")
    if state in {"completed", "aborted", "timeout"} and any(x is None for x in (start, end, elapsed)):
        raise ValueError("terminal run requires start/end/elapsed")
    if state in {"aborted", "timeout", "environment_failed"} and not o["reason"]:
        raise ValueError("unsuccessful run requires reason")
    if state == "completed" and o["exit_code"] != 0:
        raise ValueError("completed requires zero exit code")
    if end is not None:
        if start is None or utc(end) < utc(start):
            raise ValueError("invalid start/end ordering")
        if elapsed is None or abs((utc(end) - utc(start)).total_seconds() - elapsed) > 5:
            raise ValueError("UTC/monotonic elapsed mismatch; investigate clock adjustment")
    for key, expected in (("selection_document", f"docs/agent-runs/{m['run_id']}/hardware-feature-selection.md"),
                          ("structured_result", f"results/{m['run_id']}/hardware-feature.json")):
        if m["outputs"][key] != expected:
            raise ValueError(f"{key} does not match run ID")


def validate_pair(m, r):
    for field, actual in (("build_status", r["implementation"]["build"]["status"]),
                          ("automated_test_status", r["implementation"]["automated_tests"]["status"]),
                          ("hardware_verification_status", r["implementation"]["hardware_result"]),
                          ("implementation_commit", r["implementation"]["commit"])):
        if m["outputs"][field] != actual:
            raise ValueError(f"manifest/result mismatch: {field}")


def verify_evidence(m, directory):
    root = Path(directory).resolve()
    for relative, expected in m["operator"]["evidence"].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"missing/unsafe evidence: {relative}")
        if digest(path.read_bytes()) != expected:
            raise ValueError(f"evidence hash mismatch: {relative}")
