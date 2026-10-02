"""Recover reference stimuli from byte-preserving sender evidence and frozen Git."""
from datetime import datetime
import json
import math
from pathlib import Path
import re
import subprocess

from benchmark_support import digest, read, save
from evidence_package import safe_path
from host_device_pipeline import decode_frame_line


def validate_reference(path):
    """Validate every frozen byte and its recorded time/value joins."""
    path = Path(path).resolve()
    reference, root = read(path), path.parent
    if (reference.get("schema_version") != 1 or reference.get("required_ids") != ["RM1", "RM2", "RM3", "RM4", "RM5"]
            or not re.fullmatch(r"[0-9a-f]{40}", reference.get("reference_commit", ""))):
        raise ValueError("invalid frozen reference identity")
    inventory = dict(reference["fixture_files"])
    if not inventory:
        raise ValueError("reference fixtures are missing")
    inventory[reference["expected_frames"]] = reference["expected_frames_sha256"]
    for name, expected in inventory.items():
        if digest(safe_path(root, name).read_bytes()) != expected:
            raise ValueError("frozen reference hash mismatch: " + name)
    frames = [decode_frame_line(line) for line in safe_path(root, reference["expected_frames"]).read_bytes().splitlines(keepends=True)]
    offsets = reference["monotonic_offsets"]
    if (not frames or len(offsets) != len(frames) or any(isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0 for value in offsets) or offsets != sorted(offsets) or offsets[0] != 0):
        raise ValueError("invalid reference monotonic schedule")
    anchor = datetime.fromisoformat(reference["reference_time"].replace("Z", "+00:00"))
    if anchor.tzinfo is None:
        raise ValueError("reference time needs a timezone")
    recorded = [(datetime.fromisoformat(frame["sent_at"].replace("Z", "+00:00")) - anchor).total_seconds() for frame in frames]
    if recorded != offsets or read(root / "schedule.json") != {"monotonic_offsets": offsets}:
        raise ValueError("reference schedule disagrees with frames")
    usage = frames[0]["payload"]["usage"][0]
    values = {window["window_id"]: {"percent_used": window["percent_used"], "percent_remaining": window["percent_remaining"]}
              for window in usage["windows"]}
    if (reference["receiver_accepted_sequences"] != [frame["sequence"] for frame in frames]
            or reference["display_values"] != values or reference["source_status"] != usage["status"]):
        raise ValueError("reference values/sequence do not match recorded frames")
    return reference, [path.name, "schedule.json", *inventory]


def recover_reference(repository, evidence_directory, commit, output):
    repository, evidence_directory, output = map(lambda path: Path(path).resolve(), (repository, evidence_directory, output))
    full_commit = subprocess.check_output(["git", "rev-parse", commit + "^{commit}"], cwd=repository, text=True).strip()
    log = evidence_directory / "sent-frames.jsonl"
    records = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    device = read(evidence_directory / "device-check.json")
    if not records or len(records) != len(device["frames"]):
        raise ValueError("reference sender/device records do not align")
    files, wires, accepted = {}, [], []
    for record, observed in zip(records, device["frames"]):
        wire = (record["frame_json"] + "\n").encode("utf-8")
        frame = decode_frame_line(wire)
        if (digest(wire) != record["frame_sha256"] or len(wire) != record["bytes_written"]
                or frame["sequence"] != observed["sequence"] or digest(wire) != observed["frame_sha256"]
                or not re.search(rf"\bCDM_RX sequence={frame['sequence']} result=0\b", observed["device_response"])):
            raise ValueError("reference frame/hash/receiver evidence mismatch")
        for fixture in record["fixture_inputs"]:
            name = fixture["path"]
            safe_path(repository, name)
            raw = fixture["raw_utf8"].encode("utf-8")
            frozen = subprocess.check_output(["git", "show", full_commit + ":" + name], cwd=repository)
            if raw != frozen or digest(raw) != fixture["sha256"]:
                raise ValueError("reference fixture disagrees with source commit: " + name)
            if name in files and files[name] != raw:
                raise ValueError("reference fixture changed across recorded frames")
            files[name] = raw
        wires.append(wire)
        accepted.append(frame["sequence"])
    first = decode_frame_line(wires[0])
    stamp = lambda wire: datetime.fromisoformat(decode_frame_line(wire)["sent_at"].replace("Z", "+00:00"))
    offsets = [(stamp(wire) - stamp(wires[0])).total_seconds() for wire in wires]
    if offsets != sorted(offsets):
        raise ValueError("reference frame times are not ordered")
    collector = subprocess.check_output(["git", "show", full_commit + ":scripts/cdm_collector.py"], cwd=repository)
    harness = evidence_directory / "check-device.py"
    result = {"schema_version": 1, "reference_commit": full_commit,
              "required_ids": ["RM1", "RM2", "RM3", "RM4", "RM5"],
              "reference_time": first["sent_at"], "monotonic_offsets": offsets,
              "expected_frames": "expected-frames.jsonl", "expected_frames_sha256": digest(b"".join(wires)),
              "receiver_accepted_sequences": accepted,
              "source_status": first["payload"]["usage"][0]["status"],
              "display_values": {window["window_id"]: {"percent_used": window["percent_used"], "percent_remaining": window["percent_remaining"]}
                                 for window in first["payload"]["usage"][0]["windows"]},
              "fixture_files": {name: digest(raw) for name, raw in files.items()},
              "collector_source": {"git_path": "scripts/cdm_collector.py", "sha256": digest(collector)},
              "original_procedure": {"harness_sha256": digest(harness.read_bytes()),
                                     "fixture_args": {"all_provider_fixtures": False, "fixture": None, "omit_global_reset": False},
                                     "calls": ["collect_cli_fixtures(args)", "SenderSequence.reserve()", "make_frame(usage,resets,sequence)", "write_frame(owned_port,frame)"],
                                     "sender_timestamp": "runtime UTC; exact recorded sent_at is frozen above"},
              "provenance": {"sender_log_sha256": digest(log.read_bytes()),
                             "device_check_sha256": digest((evidence_directory / "device-check.json").read_bytes()),
                             "source_directory": str(evidence_directory)},
              "scope": "Recovered original stale synthetic values and accepted frames; optical/page evidence remains the original video review; no new hardware observation"}
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in files.items():
        target = safe_path(output, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (output / "expected-frames.jsonl").write_bytes(b"".join(wires))
    save(output / "schedule.json", {"monotonic_offsets": offsets})
    save(output / "reference-inputs.json", result)
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--commit", default="7923f96")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(recover_reference(args.repository, args.evidence, args.commit, args.output), indent=2))
        return 0
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "rejected", "reason": str(error)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
