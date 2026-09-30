import importlib.util
import json
import pathlib
import tempfile
import unittest
import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cdm_collector", ROOT / "scripts" / "cdm_collector.py")
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class CollectorTests(unittest.TestCase):
    def test_fixture_registry_normalizes_supported_and_unsupported_providers(self):
        registry = collector.FixtureRegistry(ROOT / "experiments" / "fixtures" / "providers")
        snapshots = registry.collect_all()
        self.assertIn("openai", {item["provider_id"] for item in snapshots})
        self.assertIn("anthropic", {item["provider_id"] for item in snapshots})
        self.assertTrue(any(item["provider_id"] == "google" and item["status"] == "unsupported" for item in snapshots))
        self.assertTrue(any(item["provider_id"] == "openai" and item["windows"] and
                            item["windows"][0]["percent_remaining"] == 80 for item in snapshots))
        self.assertTrue(all(isinstance(item["source_kind"], str) and item["source_kind"] for item in snapshots))

    def test_collector_keeps_source_error_as_data(self):
        registry = collector.FixtureRegistry(ROOT / "experiments" / "fixtures" / "providers")
        snapshots = registry.collect_all()

        self.assertTrue(any(item["status"] == "error" for item in snapshots))
        self.assertTrue(any(item["status"] == "stale" for item in snapshots))

    def test_frame_matches_canonical_crc_example_and_has_one_newline(self):
        frame = collector.make_frame([], [], sequence=1, sent_at="2026-09-10T00:00:00Z")

        self.assertEqual(frame["integrity"]["value"], "BE8028D7")
        self.assertEqual(collector.encode_frame(frame), collector.canonical_json(frame).encode() + b"\n")
        self.assertEqual(collector.crc32_without_integrity(frame), "BE8028D7")

    def test_personal_fixture_frame_obeys_checked_in_wire_schema(self):
        raw = json.loads((ROOT / "experiments" / "fixtures" / "personal-usage.json").read_text(encoding="utf-8"))
        snapshot = collector.normalize_personal_usage(raw)
        reset = collector.normalize_global_reset(json.loads((ROOT / "experiments" / "fixtures" / "codex-resets-history.json").read_text(encoding="utf-8")))
        frame = collector.make_frame([snapshot], [reset], sequence=17, sent_at="2026-10-01T00:00:00Z")
        schema = json.loads((ROOT / "experiments" / "schema" / "cdm-frame.schema.json").read_text(encoding="utf-8"))
        jsonschema.validate(frame, schema)

    def test_default_collection_keeps_both_global_reset_sources_separate(self):
        args = type("Args", (), {"all_provider_fixtures": False, "fixture": None, "omit_global_reset": False})()
        _, resets = collector.collect_cli_fixtures(args)
        self.assertEqual({item["source"] for item in resets}, {"codex-reset.com", "codex-resets.com"})

    def test_provider_fixture_matrix_emits_schema_valid_snapshots_without_credentials(self):
        snapshots = collector.FixtureRegistry(ROOT / "experiments" / "fixtures" / "providers").collect_all()
        schema = json.loads((ROOT / "experiments" / "schema" / "usage-snapshot.schema.json").read_text(encoding="utf-8"))
        for snapshot in snapshots:
            jsonschema.validate(snapshot, schema)

    def test_sender_sequence_survives_restart_and_failed_write_consumes_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = pathlib.Path(tmp) / "desk.json"
            collector.initialize_sender_state(state, receiver_known_empty=True)
            first = collector.SenderSequence(state).reserve()
            self.assertEqual(first, 0)
            self.assertEqual(collector.SenderSequence(state).reserve(), 1)
            reopened = collector.SenderSequence(state)
            self.assertEqual(reopened.reserve(), 2)

    def test_sender_sequence_wraps_at_uint32_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = pathlib.Path(tmp) / "desk.json"
            state.write_text(json.dumps({"schema_version": 1, "last_reserved": 4294967295}), encoding="utf-8")
            self.assertEqual(collector.SenderSequence(state).reserve(), 0)

    def test_sender_sequence_restart_keeps_device_order_without_board_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = pathlib.Path(tmp) / "desk.json"
            state.write_text(json.dumps({"schema_version": 1, "last_reserved": 7}), encoding="utf-8")
            self.assertEqual(collector.SenderSequence(state).reserve(), 8)

    def test_personal_fixture_preserves_both_source_windows_and_is_marked_old(self):
        raw = json.loads((ROOT / "experiments" / "fixtures" / "personal-usage.json").read_text(encoding="utf-8"))
        snapshot = collector.normalize_personal_usage(raw)
        self.assertEqual([window["window_id"] for window in snapshot["windows"]], ["five-hour", "weekly"])
        self.assertTrue(snapshot["stale"])
        self.assertEqual(snapshot["windows"][0]["percent_remaining"], 58)

    def test_frame_writer_uses_one_complete_line(self):
        frame = collector.make_frame([], [], sequence=4, sent_at="2026-09-10T00:00:00Z")
        sink = collector.MemorySerial()
        self.assertEqual(collector.write_frame(sink, frame), len(collector.encode_frame(frame)))
        self.assertEqual(sink.data.count(b"\n"), 1)
        self.assertTrue(sink.data.endswith(b"\n"))

    def test_serial_audit_log_captures_fixture_hashes_and_raw_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "wire.jsonl"
            frame = collector.make_frame([], [], sequence=9, sent_at="2026-09-10T00:00:00Z")
            collector.append_serial_log(path, port="COM3", fixture_paths=[ROOT / "experiments/fixtures/personal-usage.json"], frame=frame, bytes_written=len(collector.encode_frame(frame)))
            record = json.loads(path.read_text(encoding="utf-8").strip())
            self.assertEqual(record["frame_json"], collector.canonical_json(frame))
            self.assertIn("sha256", record["fixture_inputs"][0])
            self.assertEqual(record["bytes_written"], len(collector.encode_frame(frame)))

    def test_existing_or_corrupt_sender_state_cannot_be_initialized_over(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = pathlib.Path(tmp) / "desk.json"
            state.write_text("broken", encoding="utf-8")
            with self.assertRaises(collector.SequenceStateError):
                collector.initialize_sender_state(state, receiver_known_empty=True)
            with self.assertRaises(collector.SequenceStateError):
                collector.SenderSequence(state).reserve()

    def test_absolute_quota_inconsistency_is_rejected_without_percent_inference(self):
        raw = {
            "provider_id": "openai", "agent_id": "codex-cli", "host_id": "cli",
            "model_id": None, "account_profile_id": None,
            "source_kind": "fixture", "metric_kind": "token_balance", "unit": "token",
            "status": "available", "observed_at": "2026-09-11T00:00:00Z",
            "last_good_at": "2026-09-11T00:00:00Z", "windows": [{
                "window_id": "quota", "label": "Quota", "used_units": 10,
                "remaining_units": 10, "limit_units": 25, "unit": "token",
                "percent_used": None, "percent_remaining": None, "resets_at": None,
            }],
        }
        with self.assertRaises(collector.CollectionError):
            collector.normalize_snapshot(raw, snapshot_id="test", observed_at=raw["observed_at"])


if __name__ == "__main__":
    unittest.main()
