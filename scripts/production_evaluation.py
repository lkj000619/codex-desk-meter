"""Compare a reviewed production adapter with an oracle and join optical evidence."""
import math
from pathlib import Path
import subprocess

from benchmark_support import digest, read, save, verify_evidence
from evidence_package import safe_path
from product_observation import ProductReceiver
from host_device_pipeline import decode_frame_line


def display_values(payload):
    if payload is None:
        return {}
    return {"/".join((snapshot["provider_id"], snapshot["agent_id"], snapshot["account_profile_id"], window["window_id"])):
            {key: window.get(key) for key in ("unit", "percent_remaining", "remaining_units", "used_units", "limit_units", "resets_at")}
            for snapshot in payload["usage"] for window in snapshot["windows"]}


def expected_trace(request):
    receiver = ProductReceiver(request.get("reference_time"), request.get("monotonic_anchor", 0))
    views = []
    for event in request["events"]:
        if event.get("reset"):
            receiver.reset(event.get("reference_time"), event["seconds"])
        view = (receiver.receive(event["wire"].encode("utf-8"), event["seconds"]) if "wire" in event
                else receiver.advance(event["seconds"]))
        view["display_values"] = display_values(view["payload"])
        views.append(view)
    if not views:
        raise ValueError("production trace needs events")
    return views


def evaluate_trace(request, actual):
    expected = expected_trace(request)
    views = actual.get("views", [])
    differences = []
    if len(views) != len(expected):
        differences.append({"field": "views.length", "expected": len(expected), "actual": len(views)})
    for index, (reference, observed) in enumerate(zip(expected, views)):
        if not isinstance(observed, dict):
            differences.append({"event": index, "field": "view", "actual": observed})
            continue
        for key, value in reference.items():
            if key not in observed or observed[key] != value:
                differences.append({"event": index, "field": key, "expected": value, "actual": observed.get(key)})
    return {"schema_version": 1, "conformance_pass": not differences, "product_pass": False,
            "scope": "Only supplied events; production linkage requires operator review; LCD/hardware gates remain separate",
            "events": len(expected), "differences": differences}


def run_adapter(checkout, adapter_path, stimulus_path, output):
    """Execute only explicitly supplied operator argv; never substitute a simulator."""
    checkout, adapter_path, stimulus_path, output = map(lambda path: Path(path).resolve(), (checkout, adapter_path, stimulus_path, output))
    adapter, request = read(adapter_path), read(stimulus_path)
    expected_trace(request)  # Reject malformed input before invoking candidate code.
    production = adapter.get("production_files", {})
    linkage = adapter.get("linkage_evidence", {})
    if not production or not linkage or adapter.get("linkage_reviewed") is not True:
        raise ValueError("adapter needs reviewed production files and linkage evidence")
    for paths in (production, linkage):
        verify_evidence({"operator": {"evidence": paths}}, checkout)
    argv = adapter["argv"]
    if (not isinstance(argv, list) or not argv or not all(isinstance(value, str) for value in argv)
            or not any("{stimulus}" in value for value in argv) or not any("{output}" in value for value in argv)):
        raise ValueError("adapter argv needs stimulus and output placeholders")
    timeout = adapter.get("timeout_seconds", 60)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 60:
        raise ValueError("adapter timeout must be 1..60 seconds")
    output.mkdir(parents=True, exist_ok=False)
    input_path, actual_path = output / "stimulus.json", output / "actual.json"
    input_path.write_bytes(stimulus_path.read_bytes())
    stimulus_hash = digest(input_path.read_bytes())
    command = [value.replace("{stimulus}", str(input_path)).replace("{output}", str(actual_path)) for value in argv]
    report = {"schema_version": 1, "conformance_pass": False, "product_pass": False, "status": "failed",
              "adapter_sha256": digest(adapter_path.read_bytes()), "stimulus_sha256": stimulus_hash,
              "production_files": production, "linkage_evidence": linkage, "argv": command}
    with (output / "stdout.log").open("wb") as stdout, (output / "stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(command, cwd=checkout, stdout=stdout, stderr=stderr, timeout=timeout, check=False)
            report["exit_code"] = completed.returncode
            if completed.returncode != 0:
                raise ValueError("production adapter failed")
            if digest(input_path.read_bytes()) != stimulus_hash:
                raise ValueError("adapter changed its stimulus")
            for paths in (production, linkage):
                verify_evidence({"operator": {"evidence": paths}}, checkout)
            report.update(evaluate_trace(request, read(actual_path)), status="evaluated")
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            report["error"] = str(error)
    report["evidence"] = {path.name: digest(path.read_bytes()) for path in output.iterdir() if path.is_file()}
    save(output / "production-report.json", report)
    return report


def join_optical(capture_path, annotations):
    capture_path = Path(capture_path).resolve()
    root, capture = capture_path.parent, read(capture_path)
    if digest(capture_path.read_bytes()) != annotations.get("capture_sha256") or capture["status"] != "captured":
        raise ValueError("optical evidence needs the unchanged successful capture")
    verify_evidence({"operator": {"evidence": capture["evidence"]}}, root)
    if "sent-frames.jsonl" not in capture["evidence"]:
        raise ValueError("optical expected values need hashed sent stimulus")
    sent = {}
    for wire in (root / "sent-frames.jsonl").read_bytes().splitlines(keepends=True):
        frame = decode_frame_line(wire)
        sent[(frame["sequence"], digest(wire))] = frame["payload"]
    def matches_subset(expected, stimulus):
        if isinstance(expected, dict):
            return bool(expected) and isinstance(stimulus, dict) and all(
                key in stimulus and matches_subset(value, stimulus[key]) for key, value in expected.items())
        return expected == stimulus
    alignment = annotations.get("clock_alignment", {})
    if alignment.get("status") != "verified":
        raise ValueError("optical/media clock alignment needs operator verification")
    def verify(item):
        path = safe_path(root, item["path"])
        if digest(path.read_bytes()) != item["sha256"]:
            raise ValueError("optical evidence hash mismatch")
    verify(alignment["evidence"])
    observations = []
    for item in annotations.get("observations", []):
        tick = item["seconds"]
        if isinstance(tick, bool) or not isinstance(tick, (int, float)) or not math.isfinite(tick):
            raise ValueError("optical timestamp must use the capture monotonic clock")
        candidates = [frame for frame in capture["frames"] if frame["accepted_at_seconds"] is not None and frame["accepted_at_seconds"] <= tick]
        if not candidates:
            raise ValueError("optical observation has no accepted frame")
        frame = max(candidates, key=lambda value: value["accepted_at_seconds"])
        if frame["sequence"] != item["sequence"] or frame["frame_sha256"] != item["frame_sha256"]:
            raise ValueError("optical observation does not match the current accepted frame")
        verify(item["evidence"])
        if not item.get("expected_values") or not item.get("observed_values"):
            raise ValueError("optical observation requires expected and observed values")
        payload = sent.get((frame["sequence"], frame["frame_sha256"]))
        if payload is None:
            raise ValueError("accepted frame does not match sent stimulus")
        stimulus_values = dict(display_values(payload), global_resets=payload["global_resets"])
        if not matches_subset(item["expected_values"], stimulus_values):
            raise ValueError("optical expected values disagree with sent stimulus")
        observations.append(dict(item, values_match=item["expected_values"] == item["observed_values"],
                                 accept_to_visible_seconds=tick-frame["accepted_at_seconds"],
                                 write_to_visible_seconds=tick-frame["write_at_seconds"]))
    return {"schema_version": 1, "capture_sha256": annotations["capture_sha256"],
            "optical_status": "not_run" if not observations else "pass" if all(item["values_match"] for item in observations) else "fail",
            "scope": "Operator annotated media and timing for these observations only; full product gates remain separate",
            "product_pass": False, "clock_alignment": alignment, "observations": observations}
