import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_pipeline():
    spec = importlib.util.spec_from_file_location(
        "host_device_pipeline", SCRIPTS / "host_device_pipeline.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


pipeline = load_pipeline()


def read_json(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def sample_payload():
    return {
        "usage": [read_json("experiments/fixtures/providers/codex-percent-window.json")],
        "global_resets": [],
    }


class StaticAdapter:
    def __init__(self, adapter_id, snapshots):
        self.adapter_id = adapter_id
        self.provider_id = snapshots[0]["provider_id"] if snapshots else "fixture"
        self.agent_id = snapshots[0]["agent_id"] if snapshots else "fixture"
        self.host_id = snapshots[0]["host_id"] if snapshots else "terminal"
        self._snapshots = snapshots

    def collect(self):
        return copy.deepcopy(self._snapshots)


class BrokenAdapter:
    adapter_id = "broken"
    provider_id = "broken-provider"
    agent_id = "broken-agent"
    host_id = "terminal"

    def collect(self):
        raise RuntimeError("synthetic adapter failure")


class ShortSerial:
    def write(self, data):
        return len(data) - 1


class HostDevicePipelineTests(unittest.TestCase):
    def test_default_fixture_registry_collects_all_required_provider_and_host_examples(self):
        registry = pipeline.FixtureRegistry.with_defaults(
            ROOT, reference_time="2026-09-10T00:04:59Z"
        )
        collected = registry.collect()
        self.assertEqual(collected.failures, [])
        self.assertGreaterEqual(len(collected.snapshots), 4)
        self.assertEqual(
            {snapshot["provider_id"] for snapshot in collected.snapshots},
            {"openai", "anthropic", "google"},
        )
        self.assertIn("orca", {snapshot["host_id"] for snapshot in collected.snapshots})
        antigravity = next(s for s in collected.snapshots if s["agent_id"] == "antigravity-cli")
        self.assertEqual(antigravity["status"], "unsupported")
        self.assertEqual(antigravity["windows"], [])
        self.assertEqual(
            {reset["source"] for reset in collected.global_resets},
            {"codex-reset.com", "codex-resets.com"},
        )

    def test_one_adapter_failure_is_a_value_and_does_not_suppress_other_snapshots(self):
        healthy = read_json("experiments/fixtures/providers/codex-percent-window.json")
        registry = pipeline.FixtureRegistry(
            [BrokenAdapter(), StaticAdapter("healthy", [healthy])], reference_time="2026-09-10T00:04:59Z"
        )
        collected = registry.collect()
        self.assertEqual(len(collected.failures), 1)
        self.assertEqual(collected.failures[0]["adapter_id"], "broken")
        self.assertIn("openai", {snapshot["provider_id"] for snapshot in collected.snapshots})
        error_snapshots = [snapshot for snapshot in collected.snapshots if snapshot["provider_id"] == "broken-provider"]
        self.assertEqual(len(error_snapshots), 1)
        self.assertEqual(error_snapshots[0]["status"], "error")

    def test_global_reset_normalization_is_independently_typed(self):
        registry = pipeline.FixtureRegistry.with_defaults(
            ROOT, reference_time="2026-09-10T00:04:59Z"
        )
        collected = registry.collect()
        forecast = next(item for item in collected.global_resets if item["source"] == "codex-reset.com")
        history = next(item for item in collected.global_resets if item["source"] == "codex-resets.com")
        self.assertEqual(forecast["forecast_24h_percent"], 22)
        self.assertEqual(forecast["latest_reset_at"], "2026-09-08T04:05:53Z")
        self.assertIsNone(history["forecast_24h_percent"])
        self.assertNotIn("source_url", forecast)

    def test_registry_preserves_percent_only_absolute_and_missing_reset_fixture_values(self):
        provider_root = ROOT / "experiments" / "fixtures" / "providers"
        registry = pipeline.FixtureRegistry(
            [
                pipeline.FixtureFileAdapter("mixed", provider_root / "mixed-percent-absolute.json"),
                pipeline.FixtureFileAdapter("absolute", provider_root / "absolute-token-balance.json"),
                pipeline.FixtureFileAdapter("reset-omitted", provider_root / "reset-time-omitted.json"),
            ],
            reference_time="2026-09-10T00:04:59Z",
        )
        collected = registry.collect()
        self.assertEqual(collected.failures, [])
        self.assertTrue(any(item["unit"] == "token" for item in collected.snapshots))
        self.assertTrue(any(window["resets_at"] is None for item in collected.snapshots for window in item["windows"]))

    def test_logical_and_wire_global_reset_mapping_preserves_nulls_and_rejects_conflicts(self):
        raw = read_json("experiments/fixtures/codex-resets-history.json")
        wire = pipeline._normalize_global_reset(raw)
        logical = pipeline.global_reset_to_logical(wire)
        self.assertEqual(logical["provider"], raw["source"])
        self.assertEqual(logical["fetched_at"], raw["captured_at"])
        self.assertIsNone(logical["forecast_24h_percent"])
        self.assertEqual(pipeline._normalize_global_reset(logical), wire)
        conflicting = dict(logical, source="codex-reset.com")
        with self.assertRaises(pipeline.PipelineError) as caught:
            pipeline._normalize_global_reset(conflicting)
        self.assertEqual(caught.exception.code, "GLOBAL_RESET_ALIAS_CONFLICT")

    def test_pc_restart_requires_successor_without_resetting_live_receiver(self):
        receiver = pipeline.ReferenceReceiver()
        def send(sequence, seconds):
            stamp = f"2026-09-10T00:00:{seconds:02d}Z"
            frame = pipeline.build_frame(sample_payload(), sequence=sequence, sent_at=stamp)
            return receiver.receive(pipeline.encode_frame(frame), stamp)
        self.assertTrue(send(7, 0).accepted)
        # A restarted sender's newer timestamp does not authorize sequence reset.
        self.assertEqual(send(1, 1).code, "OUT_OF_ORDER_SEQUENCE")
        self.assertEqual(receiver.state.sequence, 7)
        self.assertTrue(send(8, 2).accepted)
        self.assertEqual(receiver.state.sequence, 8)
        self.assertFalse(send(7, 3).accepted)

    def test_unavailable_is_a_nonfatal_snapshot_status(self):
        unavailable = read_json("experiments/fixtures/providers/gemini-cli-unsupported.json")
        unavailable["status"] = "unavailable"
        unavailable["error_code"] = "SOURCE_UNAVAILABLE"
        unavailable["error_reason"] = "Synthetic source is unavailable."
        registry = pipeline.FixtureRegistry(
            [StaticAdapter("unavailable", [unavailable])], reference_time="2026-09-10T00:04:59Z"
        )
        collected = registry.collect()
        self.assertEqual(collected.failures, [])
        self.assertEqual(collected.snapshots[0]["status"], "unavailable")

    def test_frame_round_trip_and_canonical_golden_vector(self):
        frame = pipeline.build_frame(
            {"usage": [], "global_resets": []},
            sequence=1,
            sent_at="2026-09-10T00:00:00Z",
        )
        line = pipeline.encode_frame(frame)
        self.assertEqual(
            line,
            b'{"integrity":{"algorithm":"crc32","value":"BE8028D7"},"payload":{"global_resets":[],"usage":[]},"protocol":"cdm/1","sent_at":"2026-09-10T00:00:00Z","sequence":1}\n',
        )
        decoded = pipeline.decode_frame_line(line)
        self.assertEqual(decoded, frame)

        golden = read_json("experiments/examples/cdm-frame.example.json")
        self.assertEqual(pipeline.decode_frame_line(pipeline.canonical_json(golden) + b"\n"), golden)
        invalid_crc = read_json("experiments/examples/invalid/cdm-frame-crc.example.json")
        with self.assertRaises(pipeline.PipelineError) as context:
            pipeline.decode_frame_line(pipeline.canonical_json(invalid_crc) + b"\n")
        self.assertEqual(context.exception.code, "CRC_MISMATCH")

    def test_frame_rejects_crc_corruption_truncation_invalid_utf8_oversize_schema_and_version(self):
        frame = pipeline.build_frame(sample_payload(), sequence=1, sent_at="2026-09-10T00:00:00Z")
        line = pipeline.encode_frame(frame)

        corrupted = bytearray(line)
        corrupted[-3] = ord("0") if corrupted[-3] != ord("0") else ord("1")
        with self.assertRaises(pipeline.PipelineError) as context:
            pipeline.decode_frame_line(bytes(corrupted))
        self.assertEqual(context.exception.code, "CRC_MISMATCH")

        with self.assertRaises(pipeline.PipelineError) as context:
            pipeline.decode_frame_line(line[:-1])
        self.assertEqual(context.exception.code, "FRAME_TRUNCATED")

        with self.assertRaises(pipeline.PipelineError) as context:
            pipeline.decode_frame_line(b"\xff\n")
        self.assertEqual(context.exception.code, "INVALID_UTF8")

        with self.assertRaises(pipeline.PipelineError) as context:
            pipeline.decode_frame_line(line + b"\n")
        self.assertEqual(context.exception.code, "FRAME_NEWLINE_INVALID")

        with self.assertRaises(pipeline.PipelineError) as context:
            pipeline.decode_frame_line(b"not-json\n")
        self.assertEqual(context.exception.code, "MALFORMED_JSON")

        with self.assertRaises(pipeline.PipelineError) as context:
            pipeline.decode_frame_line(b"x" * pipeline.MAX_FRAME_BYTES + b"\n")
        self.assertEqual(context.exception.code, "FRAME_OVERSIZED")

        invalid = {
            "protocol": "cdm/1",
            "sequence": 1,
            "sent_at": "2026-09-10T00:00:00Z",
            "payload": {"usage": [], "global_resets": []},
            "integrity": {"algorithm": "crc32", "value": "00000000"},
        }
        invalid["payload"].pop("usage")
        with self.assertRaises(pipeline.PipelineError) as context:
            pipeline.decode_frame_line(pipeline.canonical_json(invalid) + b"\n")
        self.assertEqual(context.exception.code, "FRAME_SCHEMA_INVALID")

        unsupported = copy.deepcopy(frame)
        unsupported["protocol"] = "cdm/2"
        with self.assertRaises(pipeline.PipelineError) as context:
            pipeline.decode_frame_line(pipeline.canonical_json(unsupported) + b"\n")
        self.assertEqual(context.exception.code, "UNSUPPORTED_VERSION")

        static_unsupported = read_json("experiments/examples/invalid/cdm-frame-unsupported-version.example.json")
        with self.assertRaises(pipeline.PipelineError) as context:
            pipeline.decode_frame_line(pipeline.canonical_json(static_unsupported) + b"\n")
        self.assertEqual(context.exception.code, "UNSUPPORTED_VERSION")
        static_schema = read_json("experiments/examples/invalid/cdm-frame-schema.example.json")
        with self.assertRaises(pipeline.PipelineError) as context:
            pipeline.decode_frame_line(pipeline.canonical_json(static_schema) + b"\n")
        self.assertEqual(context.exception.code, "FRAME_SCHEMA_INVALID")

        noncanonical = b'{"protocol":"cdm/1","sequence":1,"sent_at":"2026-09-10T00:00:00Z","payload":{"usage":[],"global_resets":[]},"integrity":{"algorithm":"crc32","value":"BE8028D7"}}\n'
        with self.assertRaises(pipeline.PipelineError) as context:
            pipeline.decode_frame_line(noncanonical)
        self.assertEqual(context.exception.code, "NON_CANONICAL_FRAME")

    def test_fixture_adapter_cannot_read_outside_repository_provider_fixtures(self):
        adapter = pipeline.FixtureFileAdapter("escape", ROOT / "README.md")
        with self.assertRaises(pipeline.PipelineError) as context:
            adapter.collect()
        self.assertEqual(context.exception.code, "FIXTURE_PATH_UNSAFE")

        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "run-host-device-pipeline.py"),
                "--fixture",
                "..\\README.md",
                "--dry-run",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("FIXTURE_PATH_UNSAFE", completed.stderr)

    def test_receiver_sequence_rules_wraparound_and_last_good_retention(self):
        receiver = pipeline.ReferenceReceiver()
        first = pipeline.build_frame(sample_payload(), sequence=7, sent_at="2026-09-10T00:00:00Z")
        accepted = receiver.receive(pipeline.encode_frame(first), reference_time="2026-09-10T00:00:01Z")
        self.assertTrue(accepted.accepted)

        duplicate = receiver.receive(pipeline.encode_frame(first), reference_time="2026-09-10T00:00:02Z")
        self.assertFalse(duplicate.accepted)
        self.assertEqual(duplicate.code, "DUPLICATE_SEQUENCE")

        older = pipeline.build_frame(sample_payload(), sequence=6, sent_at="2026-09-10T00:00:02Z")
        rejected = receiver.receive(pipeline.encode_frame(older), reference_time="2026-09-10T00:00:03Z")
        self.assertFalse(rejected.accepted)
        self.assertEqual(rejected.code, "OUT_OF_ORDER_SEQUENCE")
        self.assertEqual(receiver.state.payload, first["payload"])

        wrap_receiver = pipeline.ReferenceReceiver()
        max_frame = pipeline.build_frame(sample_payload(), sequence=pipeline.MAX_SEQUENCE, sent_at="2026-09-10T00:00:00Z")
        zero_frame = pipeline.build_frame(sample_payload(), sequence=0, sent_at="2026-09-10T00:00:01Z")
        self.assertTrue(wrap_receiver.receive(pipeline.encode_frame(max_frame), "2026-09-10T00:00:00Z").accepted)
        self.assertTrue(wrap_receiver.receive(pipeline.encode_frame(zero_frame), "2026-09-10T00:00:01Z").accepted)

        bad = bytearray(pipeline.encode_frame(first))
        bad[-3] = ord("0") if bad[-3] != ord("0") else ord("1")
        failed = receiver.receive(bytes(bad), reference_time="2026-09-10T00:00:04Z")
        self.assertFalse(failed.accepted)
        self.assertEqual(failed.code, "CRC_MISMATCH")
        self.assertEqual(receiver.state.payload, first["payload"])

    def test_receiver_stale_boundary_provider_error_and_recovery(self):
        receiver = pipeline.ReferenceReceiver()
        first = pipeline.build_frame(sample_payload(), sequence=1, sent_at="2026-09-10T00:00:00Z")
        self.assertTrue(receiver.receive(pipeline.encode_frame(first), "2026-09-10T00:00:01Z").accepted)
        self.assertFalse(receiver.advance("2026-09-10T00:04:59Z").stale)
        self.assertTrue(receiver.advance("2026-09-10T00:05:00Z").stale)

        provider_error = read_json("experiments/fixtures/providers/provider-error.json")
        error_frame = pipeline.build_frame(
            {"usage": [provider_error], "global_resets": []}, sequence=2, sent_at="2026-09-10T00:05:00Z"
        )
        accepted = receiver.receive(pipeline.encode_frame(error_frame), "2026-09-10T00:05:01Z")
        self.assertTrue(accepted.accepted)
        self.assertFalse(accepted.stale)
        self.assertEqual(receiver.state.payload["usage"][0]["status"], "error")

    def test_serial_boundary_is_dry_run_by_default_and_loopback_only_in_tests(self):
        frame = pipeline.build_frame({"usage": [], "global_resets": []}, sequence=1, sent_at="2026-09-10T00:00:00Z")
        bridge = pipeline.SerialBridge()
        outcome = bridge.render(frame)
        self.assertEqual(outcome.mode, "dry_run")
        self.assertEqual(outcome.status, "rendered")
        with self.assertRaises(pipeline.PipelineError) as context:
            bridge.send(frame, port=None)
        self.assertEqual(context.exception.code, "PORT_REQUIRED")

        loopback = pipeline.LoopbackSerial()
        sent = bridge.send_loopback(frame, loopback)
        self.assertEqual(sent.status, "sent")
        self.assertEqual(loopback.writes, [pipeline.encode_frame(frame)])

        serial_outcome = bridge.send(frame, port="FAKE", serial_factory=lambda _port: loopback)
        self.assertEqual(serial_outcome.mode, "serial")
        self.assertTrue(serial_outcome.device_accessed)
        with self.assertRaises(pipeline.PipelineError) as context:
            bridge.send(frame, port="FAKE", serial_factory=lambda _port: ShortSerial())
        self.assertEqual(context.exception.code, "SERIAL_WRITE_INCOMPLETE")

    def test_cli_dry_run_emits_frame_and_structured_outcome_without_device_access(self):
        command = [
            sys.executable,
            str(SCRIPTS / "run-host-device-pipeline.py"),
            "--reference-time",
            "2026-09-10T00:04:59Z",
            "--sent-at",
            "2026-09-10T00:00:00Z",
            "--sequence",
            "1",
            "--dry-run",
        ]
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=False)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode())
        decoded = pipeline.decode_frame_line(completed.stdout)
        self.assertEqual(decoded["protocol"], "cdm/1")
        report = json.loads(completed.stderr.decode("utf-8"))
        self.assertEqual(report["mode"], "dry_run")
        self.assertFalse(report["device_accessed"])
        self.assertEqual(report["frame_sha256"], pipeline.sha256(completed.stdout))

        rejected = subprocess.run(
            [sys.executable, str(SCRIPTS / "run-host-device-pipeline.py"), "--port", "FAKE_PORT"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(rejected.returncode, 1)
        self.assertIn("PORT_REQUIRES_SEND", rejected.stderr)

    def test_cli_writes_machine_readable_preflight_report_file(self):
        with tempfile.TemporaryDirectory() as folder:
            frame_path = Path(folder) / "frame.jsonl"
            report_path = Path(folder) / "report.json"
            completed = subprocess.run(
                [sys.executable, str(SCRIPTS / "run-host-device-pipeline.py"),
                 "--dry-run", "--output", str(frame_path), "--report-output", str(report_path)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout, "")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "rendered")
            self.assertFalse(report["device_accessed"])
            self.assertEqual(report["frame_sha256"], pipeline.sha256(frame_path.read_bytes()))

    def test_evidence_hashes_and_classification_are_reproducible(self):
        evidence = read_json("experiments/examples/host-device-pipeline-evidence.example.json")
        self.assertEqual(evidence["classification"]["F3"], "host_simulated")
        self.assertEqual(evidence["classification"]["F4"], "reference_model_only")
        self.assertFalse(evidence["loopback"]["device_accessed"])
        golden_path = ROOT / evidence["golden_frame"]["path"]
        golden = read_json(evidence["golden_frame"]["path"])
        self.assertEqual(
            pipeline.sha256(pipeline.canonical_json(golden) + b"\n"),
            evidence["golden_frame"]["frame_line_sha256"],
        )
        self.assertEqual(hashlib.sha256(golden_path.read_bytes()).hexdigest(), evidence["golden_frame"]["file_sha256"])
        for relative_path, expected in evidence["fixture_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest(), expected)


if __name__ == "__main__":
    unittest.main()
