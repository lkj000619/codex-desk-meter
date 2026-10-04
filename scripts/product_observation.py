"""Offline source/receive oracle and operator-owned serial observation boundary."""
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import math
from pathlib import Path
import re
import time

from benchmark_support import digest, save
from host_device_pipeline import PipelineError, decode_frame_line, sequence_is_newer


def _validator():
    spec = importlib.util.spec_from_file_location("observation_validator", Path(__file__).with_name("validate-end-to-end-result.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _utc(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("UTC anchor needs an explicit timezone")
    return parsed.astimezone(timezone.utc)


class ProductReceiver:
    """Evaluation oracle, never evidence that a firmware implementation ran."""
    def __init__(self, reference_time=None, monotonic_anchor=0):
        self.validator = _validator()
        self.reset(reference_time, monotonic_anchor)

    def reset(self, reference_time=None, monotonic_anchor=0):
        if isinstance(monotonic_anchor, bool) or not math.isfinite(monotonic_anchor) or monotonic_anchor < 0:
            raise ValueError("invalid monotonic anchor")
        self.anchor = None if reference_time is None else _utc(reference_time)
        self.anchor_tick = self.last_tick = monotonic_anchor
        self.received_tick = None
        self.sequence, self.payload, self.last_error = None, None, None

    def advance(self, monotonic_now):
        if (isinstance(monotonic_now, bool) or not math.isfinite(monotonic_now)
                or monotonic_now < self.last_tick):
            raise ValueError("monotonic clock moved backwards or is invalid; reset needs a new anchor")
        self.last_tick = monotonic_now
        current = None if self.anchor is None else self.anchor + timedelta(seconds=monotonic_now - self.anchor_tick)
        ages = []
        if current is not None and self.payload is not None:
            for snapshot in self.payload["usage"]:
                observed = snapshot.get("observed_at") or snapshot.get("last_good_at")
                if observed:
                    ages.append(snapshot["stale"] or (current - _utc(observed)).total_seconds() >= 300)
            for reset in self.payload["global_resets"]:
                if reset.get("captured_at"):
                    ages.append(reset["stale"] or (current - _utc(reset["captured_at"])).total_seconds() >= 300)
        return {"clock_status": "unknown" if current is None else "anchored",
                "reference_time": None if current is None else current.isoformat().replace("+00:00", "Z"),
                "source_stale": None if current is None or self.payload is None else any(ages),
                "receive_stale": self.received_tick is not None and monotonic_now - self.received_tick >= 300,
                "sequence": self.sequence, "payload": copy.deepcopy(self.payload), "error_code": self.last_error}

    def receive(self, line, monotonic_now):
        view = self.advance(monotonic_now)
        try:
            frame = decode_frame_line(line)
            if self.sequence is not None and not sequence_is_newer(frame["sequence"], self.sequence):
                raise PipelineError("DUPLICATE_OR_OLD_SEQUENCE", "sequence is not newer")
            if view["reference_time"] is not None:
                reference = _utc(view["reference_time"])
                if _utc(frame["sent_at"]) > reference:
                    raise PipelineError("FUTURE_TIMESTAMP", "frame sent_at is after the UTC anchor")
                for snapshot in frame["payload"]["usage"]:
                    self.validator.validate_snapshot(snapshot, reference_time=reference)
                for reset in frame["payload"]["global_resets"]:
                    if reset["captured_at"] is None and reset["error_code"] is None:
                        raise PipelineError("INVALID_TIMESTAMP", "normal reset source needs captured_at")
                    if reset["captured_at"] is not None:
                        age = (reference - _utc(reset["captured_at"])).total_seconds()
                        if age < 0:
                            raise PipelineError("FUTURE_TIMESTAMP", "reset source is in the future")
                        if age >= 300 and reset["stale"] is not True:
                            raise PipelineError("STALE_THRESHOLD_EXCEEDED", "old reset source is not stale")
            self.payload, self.sequence = copy.deepcopy(frame["payload"]), frame["sequence"]
            self.received_tick, self.last_error = monotonic_now, None
            accepted = True
        except (PipelineError, self.validator.ValidationError) as error:
            self.last_error, accepted = error.code, False
        return dict(self.advance(monotonic_now), accepted=accepted)


def open_observer_serial(port):
    import serial
    connection = serial.Serial(port=None, baudrate=115200, timeout=0.05, write_timeout=3,
                               bytesize=8, parity="N", stopbits=1, xonxoff=False, rtscts=False, dsrdtr=False)
    connection.dtr = connection.rts = False
    connection.port = port
    connection.open()
    return connection


def capture_frames(wires, port, serial_factory, output, wait_seconds=5, writer=None, receiver_log=None):
    if not 0 < wait_seconds <= 60 or not port:
        raise ValueError("capture requires an explicit port and 0 < wait <= 60")
    review_bytes = None
    if receiver_log is not None:
        template = receiver_log.get("acceptance_template")
        reviewer = receiver_log.get("reviewer")
        if (not isinstance(template, str) or template.count("{sequence}") != 1
                or any(c in template for c in "\r\n")
                or not isinstance(reviewer, str) or not reviewer.strip()):
            raise ValueError("receiver log needs one {sequence}, a single-line template and reviewer")
        review_bytes = Path(receiver_log["evidence_path"]).read_bytes()
        if not review_bytes or digest(review_bytes) != receiver_log["evidence_sha256"]:
            raise ValueError("receiver log review evidence hash mismatch or empty evidence")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    evidence_names = ["events.jsonl", "device-serial.bin", "sent-frames.jsonl"]
    if receiver_log is not None:
        evidence_names += ["receiver-log.json", "receiver-log-review.bin"]
    if any((output / name).exists() for name in ["capture.json", *evidence_names]):
        raise ValueError("capture output already exists")
    if receiver_log is not None:
        save(output / "receiver-log.json", receiver_log)
        (output / "receiver-log-review.bin").write_bytes(review_bytes)
    report = {"schema_version": 1, "status": "captured", "port": port,
              "sender_kind": "operator_replay" if writer is None else "candidate_writer_adapter",
              "started_at": datetime.now(timezone.utc).isoformat(), "frames": [], "error_code": None,
              "optical_status": "not_run", "product_pass": False, "device_accessed": False,
              "clock": "host monotonic relative to session start; firmware uptime is separate"}
    started, connection = time.monotonic(), None
    with (output / "events.jsonl").open("x", encoding="utf-8") as events, (output / "device-serial.bin").open("xb") as raw, (output / "sent-frames.jsonl").open("xb") as transmitted:
        def event(kind, **fields):
            item = dict(kind=kind, seconds=time.monotonic() - started,
                        utc=datetime.now(timezone.utc).isoformat(), **fields)
            events.write(json.dumps(item, ensure_ascii=False) + "\n")
            events.flush()
            return item["seconds"]
        try:
            connection = serial_factory(port)
            report["device_accessed"] = True
            event("port_open", baud=115200, dtr=False, rts=False, note="backend must set DTR/RTS before open; actual reset/re-enumeration requires observation")
            line_incomplete = False
            for wire in wires:
                incomplete_prelude = line_incomplete
                pending = getattr(connection, "in_waiting", 0)
                if pending:
                    if pending > 65536:
                        raise PipelineError("SERIAL_PRELUDE_TOO_LARGE", "inspect noisy device before sending")
                    prelude = connection.read(pending)
                    if prelude:
                        incomplete_prelude = not prelude.endswith(b"\n")
                    raw.write(prelude)
                    raw.flush()
                    event("pre_write_read", bytes_received=len(prelude), sha256=digest(prelude))
                frame = json.loads(wire)
                record = {"sequence": frame["sequence"], "frame_sha256": digest(wire), "bytes_requested": len(wire),
                          "bytes_written": None, "accepted_at_seconds": None, "display_marker_at_seconds": None,
                          "write_at_seconds": None}
                report["frames"].append(record)
                wire_start = event("write_start", sequence=frame["sequence"], frame_sha256=digest(wire))
                emitted = bytearray()
                actual_counts = []
                class RecordingWriter:
                    def write(self, data):
                        emitted.extend(data)
                        transmitted.write(data)
                        transmitted.flush()
                        actual = connection.write(data)
                        actual_counts.append((len(data), actual))
                        return actual
                    def __getattr__(self, name):
                        return getattr(connection, name)
                owned = RecordingWriter()
                count = owned.write(wire) if writer is None else writer(owned, frame)
                record["bytes_written"] = count
                if emitted != wire:
                    raise PipelineError("WRITER_FRAME_MISMATCH", "writer emitted different bytes than the frozen stimulus")
                if count != len(wire) or any(requested != actual for requested, actual in actual_counts):
                    raise PipelineError("SERIAL_WRITE_INCOMPLETE", "short write")
                record["write_at_seconds"] = event("write_complete", sequence=frame["sequence"], bytes_written=count)
                response = bytearray()
                deadline = time.monotonic() + wait_seconds
                while time.monotonic() < deadline:
                    data = connection.read(4096)
                    if data:
                        response.extend(data)
                        raw.write(data)
                        raw.flush()
                        observed = event("read", bytes_received=len(data), sha256=digest(data))
                        text = response.decode("utf-8", errors="replace")
                        for prefix, key in (("CDM_RX", "accepted_at_seconds"), ("CDM_DISPLAY", "display_marker_at_seconds")):
                            if prefix == "CDM_RX" and receiver_log is not None:
                                expected = template.replace("{sequence}", str(frame["sequence"]))
                                complete_lines = response.split(b"\n")[:-1]
                                if incomplete_prelude:
                                    complete_lines = complete_lines[1:]
                                if record[key] is None and any(
                                        line.removesuffix(b"\r") == expected.encode("utf-8") for line in complete_lines):
                                    record[key] = observed
                                continue
                            if record[key] is None and re.search(rf"\b{prefix} sequence={frame['sequence']} result=0\b", text):
                                record[key] = observed
                        time.sleep(0.001)
                line_incomplete = not response.endswith(b"\n") if response else incomplete_prelude
                record["response_sha256"] = digest(response)
                record["write_duration_seconds"] = record["write_at_seconds"] - wire_start
        except (OSError, ValueError) as error:
            report["status"] = "failed"
            report["error_code"] = getattr(error, "code", "CAPTURE_ERROR")
            report["error"] = str(error)
            event("capture_error", error=report["error"])
        finally:
            if connection is not None:
                try:
                    connection.close()
                    event("port_close")
                except OSError as error:
                    report["status"], report["error_code"] = "failed", "PORT_CLOSE_FAILED"
                    event("port_close_failed", error=str(error))
    report["evidence"] = {name: digest((output / name).read_bytes()) for name in evidence_names}
    save(output / "capture.json", report)
    return report


def replay_frames(wires, reference_time=None, monotonic_anchor=0, monotonic_offsets=None):
    wires = list(wires)
    offsets = list(range(len(wires))) if monotonic_offsets is None else monotonic_offsets
    if len(offsets) != len(wires):
        raise ValueError("schedule length must match frames")
    receiver = ProductReceiver(reference_time, monotonic_anchor)
    return {"mode": "offline_oracle", "device_accessed": False, "product_pass": False,
            "frames": [receiver.receive(wire, monotonic_anchor + offset) for offset, wire in zip(offsets, wires)]}
