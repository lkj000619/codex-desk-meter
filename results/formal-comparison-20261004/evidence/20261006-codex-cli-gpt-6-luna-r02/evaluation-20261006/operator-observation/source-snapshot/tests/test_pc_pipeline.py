from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pc.pipeline import (
    CollectionError, FixtureCollector, build_frame, canonical_json,
    crc32_hex, encode_frame, normalize_global_reset, normalize_legacy_usage,
    parse_time, validate_snapshot,
)
from pc.sender import SequenceStateError, SequenceStore, send_payload


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = datetime(2026, 9, 10, 0, 0, 0, tzinfo=timezone.utc)


class FixturePipelineTests(unittest.TestCase):
    def test_common_profile_matches_fixed_payload_and_exact_seq_zero_one_frames(self):
        reference = parse_time("2026-09-30T18:40:49Z", "reference_time")
        collected = FixtureCollector().collect_common(reference)
        self.assertEqual(len(collected.usage), 1)
        usage = collected.usage[0]
        self.assertEqual(usage["snapshot_id"], "fixture-personal-usage")
        self.assertIsNone(usage["model_id"])
        self.assertIsNone(usage["account_profile_id"])
        self.assertEqual(usage["error_reason"], "The source observation is at least 300 seconds old; its value is retained as stale.")
        self.assertEqual([window["percent_remaining"] for window in usage["windows"]], [58, 82])
        self.assertEqual([window["reset_status"] for window in usage["windows"]], ["unknown", "unknown"])
        self.assertEqual(len(collected.global_resets), 2)
        self.assertTrue(all(reset["stale"] and reset["error_code"] is None for reset in collected.global_resets))

        expected_lines = (ROOT / ".benchmark-inputs/feedback-evidence/008-sent-frames.jsonl").read_bytes().splitlines(keepends=True)
        self.assertEqual(len(expected_lines), 2)
        payload = collected.payload
        first = encode_frame(build_frame(payload, 0, "2026-09-30T18:40:49Z"))
        second = encode_frame(build_frame(payload, 1, "2026-09-30T18:40:54Z"))
        self.assertEqual(first, expected_lines[0])
        self.assertEqual(second, expected_lines[1])

    def test_available_snapshot_over_stale_threshold_is_rejected_without_coercion(self):
        body = json.loads((ROOT / "experiments/fixtures/providers/available-over-stale-threshold.json").read_text(encoding="utf-8"))
        reference = parse_time("2026-09-10T00:04:59Z", "reference_time")
        with self.assertRaises(CollectionError) as error:
            validate_snapshot(body, reference)
        self.assertEqual(error.exception.code, "STALE_THRESHOLD_EXCEEDED")

    def test_available_requires_agent_and_host_but_error_status_allows_null_identity(self):
        available = json.loads((ROOT / "experiments/fixtures/providers/codex-percent-window.json").read_text(encoding="utf-8"))
        available["agent_id"] = None
        with self.assertRaises(CollectionError) as error:
            validate_snapshot(available, REFERENCE)
        self.assertEqual(error.exception.code, "IDENTITY_REQUIRED")

        unsupported = json.loads((ROOT / "experiments/fixtures/providers/antigravity-cli-unsupported.json").read_text(encoding="utf-8"))
        unsupported["agent_id"] = None
        unsupported["host_id"] = None
        validate_snapshot(unsupported, REFERENCE)

    def test_all_provider_fixture_matrix_expectations(self):
        matrix = json.loads((ROOT / "experiments/fixtures/provider-fixture-matrix.json").read_text(encoding="utf-8"))
        reference = parse_time(matrix["reference_time"], "reference_time")
        for entry in matrix["fixtures"]:
            path = ROOT / "experiments/fixtures" / entry["path"]
            value = json.loads(path.read_text(encoding="utf-8"))
            items = value if isinstance(value, list) else [value]
            errors = []
            for item in items:
                try:
                    validate_snapshot(item, reference)
                except CollectionError as error:
                    errors.append(error)
            with self.subTest(fixture=entry["path"]):
                if entry["expected"] == "valid":
                    self.assertFalse(errors)
                else:
                    self.assertTrue(errors)

    def test_legacy_usage_maps_original_values_and_keeps_observation_time(self):
        body = json.loads((ROOT / "experiments/fixtures/personal-usage.json").read_text(encoding="utf-8"))
        captured = datetime.fromisoformat(body["captured_at"].replace("Z", "+00:00"))
        snapshot = normalize_legacy_usage(body, reference_time=captured + timedelta(seconds=299))
        self.assertEqual(snapshot["observed_at"], body["captured_at"])
        self.assertEqual(snapshot["windows"][0]["window_id"], body["windows"][0]["id"])
        self.assertEqual(snapshot["windows"][0]["percent_used"], 42)
        self.assertIsNone(snapshot["windows"][0]["used_units"])
        self.assertFalse(snapshot["stale"])

    def test_source_age_boundary_299_and_300_seconds(self):
        body = {
            "captured_at": "2026-09-10T00:00:00Z",
            "windows": [{"id": "daily", "label": "Daily", "percent_used": 25,
                         "percent_remaining": 75, "resets_at": None}],
        }
        fresh = normalize_legacy_usage(body, reference_time=REFERENCE + timedelta(seconds=299))
        stale = normalize_legacy_usage(body, reference_time=REFERENCE + timedelta(seconds=300))
        self.assertEqual(fresh["status"], "available")
        self.assertFalse(fresh["stale"])
        self.assertEqual(stale["status"], "stale")
        self.assertTrue(stale["stale"])
        self.assertEqual(stale["observed_at"], body["captured_at"])

    def test_global_reset_aliases_are_normalized_and_sources_stay_separate(self):
        history = json.loads((ROOT / "experiments/fixtures/codex-resets-history.json").read_text(encoding="utf-8"))
        forecast = json.loads((ROOT / "experiments/fixtures/codex-reset-forecast.json").read_text(encoding="utf-8"))
        reset_reference = REFERENCE + timedelta(days=1)
        normalized_history = normalize_global_reset(history, reset_reference)
        normalized_forecast = normalize_global_reset(forecast, reset_reference)
        self.assertEqual(normalized_history["source"], "codex-resets.com")
        self.assertEqual(normalized_history["latest_reset_at"], history["latest_reset_at"])
        self.assertEqual(normalized_forecast["source"], "codex-reset.com")
        self.assertEqual(normalized_forecast["latest_reset_at"], forecast["last_reset_at"])
        self.assertFalse(normalized_forecast["forecast_is_schedule"])
        self.assertNotEqual(normalized_history["source"], normalized_forecast["source"])

    def test_fixture_registry_collects_each_adapter_at_the_fixed_reference(self):
        result = FixtureCollector().collect(REFERENCE + timedelta(seconds=299))
        self.assertGreaterEqual(len(result.usage), 5)
        self.assertTrue(all(snapshot["observed_at"] is not None for snapshot in result.usage))
        self.assertFalse(any(snapshot["status"] == "stale" for snapshot in result.usage))
        self.assertEqual(len(result.failures), 2)

    def test_one_adapter_failure_keeps_last_good_and_does_not_stop_others(self):
        collector = FixtureCollector()
        initial = collector.collect(REFERENCE + timedelta(seconds=299))
        original = collector._load

        def failing_first(relative):
            if relative.endswith("codex-percent-window.json"):
                raise CollectionError("DNS_FAILURE", "synthetic adapter failure")
            return original(relative)

        with patch.object(collector, "_load", side_effect=failing_first):
            recovered_result = collector.collect(REFERENCE + timedelta(seconds=299))
        self.assertTrue(initial.usage)
        self.assertTrue(any(entry["adapter_id"] == "codex-percent-window" for entry in recovered_result.failures))
        first = next(snapshot for snapshot in recovered_result.usage if snapshot["provider_id"] == "openai")
        self.assertEqual(first["status"], "error")
        self.assertEqual(first["error_code"], "DNS_FAILURE")
        self.assertEqual(first["observed_at"], initial.usage[0]["observed_at"])
        self.assertTrue(any(snapshot["provider_id"] == "anthropic" for snapshot in recovered_result.usage))

    def test_frame_is_sorted_crc_signed_and_lf_terminated(self):
        frame = build_frame({"usage": [], "global_resets": []}, 9, "2026-09-10T00:00:00Z")
        unsigned = {key: value for key, value in frame.items() if key != "integrity"}
        self.assertEqual(frame["integrity"]["value"], crc32_hex(canonical_json(unsigned)))
        line = encode_frame(frame)
        self.assertTrue(line.endswith(b"\n"))
        self.assertFalse(line.endswith(b"\n\n"))
        self.assertEqual(line[:-1], canonical_json(frame))
        self.assertIn("한글".encode("utf-8"), canonical_json({"label": "한글"}))

    def test_global_capture_time_must_not_be_missing(self):
        with self.assertRaises(CollectionError) as error:
            normalize_global_reset({"source": "codex-resets.com", "captured_at": None}, REFERENCE)
        self.assertEqual(error.exception.code, "CAPTURE_TIME_MISSING")


class SenderStateTests(unittest.TestCase):
    def test_explicit_empty_receiver_initialization_then_durable_increment(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            store = SequenceStore(Path(temporary) / "sender-state.json")
            with self.assertRaises(SequenceStateError):
                store.reserve("board-1")
            self.assertEqual(store.reserve("board-1", initialize_empty_receiver=True), 0)
            self.assertEqual(store.reserve("board-1"), 1)

    def test_corrupt_state_stops_sender_even_with_initialization_flag(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            path = Path(temporary) / "sender-state.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(SequenceStateError):
                SequenceStore(path).reserve("board-1", initialize_empty_receiver=True)

    def test_wrap_and_failed_write_consume_sequence(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            state = Path(temporary) / "sender-state.json"
            state.write_text(json.dumps({"schema_version": 1, "devices": {"wrap": 0xFFFFFFFF}}), encoding="utf-8")
            self.assertEqual(SequenceStore(state).reserve("wrap"), 0)
            failed_state = Path(temporary) / "failed-state.json"
            raw_log = Path(temporary) / "raw.log"

            class FailedSerial:
                def write(self, data):
                    raise OSError("synthetic USB disconnect")

                def close(self):
                    pass

            with self.assertRaises(OSError):
                send_payload({"usage": [], "global_resets": []}, "COM9", "board-2", failed_state, raw_log,
                             initialize_empty_receiver=True,
                             serial_factory=lambda *args, **kwargs: FailedSerial())
            self.assertEqual(SequenceStore(failed_state).reserve("board-2"), 1)
            self.assertTrue(raw_log.read_bytes().endswith(b"\n"))

    def test_successful_host_write_is_not_reported_as_device_ack(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            raw_log = Path(temporary) / "raw.log"

            class FakeSerial:
                def __init__(self):
                    self.writes = []

                def write(self, data):
                    self.writes.append(data)
                    return len(data)

                def close(self):
                    pass

            serial = FakeSerial()
            receipt = send_payload({"usage": [], "global_resets": []}, "COM9", "board-1",
                                   Path(temporary) / "state.json", raw_log, True,
                                   serial_factory=lambda *args, **kwargs: serial)
            self.assertEqual(receipt["status"], "written")
            self.assertFalse(receipt["device_ack"])
            self.assertEqual(raw_log.read_bytes(), serial.writes[0])

    def test_optional_device_logs_are_diagnostic_and_never_an_ack(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            log_path = Path(temporary) / "device.log"

            class LoggedSerial:
                def __init__(self):
                    self.lines = [b"I meter_app: accepted cdm/1 frame sequence=0\r\n", b""]

                def write(self, data):
                    return len(data)

                def readline(self):
                    return self.lines.pop(0) if self.lines else b""

                def close(self):
                    pass

            receipt = send_payload(
                {"usage": [], "global_resets": []}, "COM9", "board-logs",
                Path(temporary) / "state.json", Path(temporary) / "raw.log", True,
                serial_factory=lambda *args, **kwargs: LoggedSerial(),
                capture_device_logs_seconds=0.01, device_log_path=log_path,
            )
            self.assertEqual(receipt["device_log_lines"], ["I meter_app: accepted cdm/1 frame sequence=0"])
            self.assertFalse(receipt["device_ack"])
            self.assertEqual(log_path.read_text(encoding="utf-8"), "I meter_app: accepted cdm/1 frame sequence=0\n")


if __name__ == "__main__":
    unittest.main()
