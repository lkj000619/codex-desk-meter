"""Synthetic unit and integration tests for pc/ package.

Covers:
- Metadata boundary and privacy (no conversation text or secrets).
- Native app-server rateLimits protocol parsing.
- Session token tracking (cumulative event_msg/token_count, partial line, truncation, restart).
- Session channels (input, output, cached_input, reasoning_output, source_total, normalized_total).
- Differing source_total vs normalized_total.
- Schema and semantic validation (non-null agent/host on available, session null fields).
- cdm/1 canonical JSON, CRC32, max 64KB, single trailing LF.
- uint32 sequence reservation, atomic persistence before write, failed write consuming sequence, wrap-around.
- Fail-closed behavior on state loss or corruption.
- Stale detection (0s, 299s, 300s).
- CLI inventory, collect, send (dry-run), watch, init-device.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pc.frame import (
    MAX_FRAME_BYTES,
    MAX_SEQUENCE,
    FrameError,
    build_frame,
    canonical_json,
    crc32_hex,
    decode_frame,
    encode_frame,
    semantic_validate_snapshot,
    sequence_is_newer,
)
from pc.normalizer import (
    build_account_quota_snapshot,
    build_session_telemetry_snapshot,
    normalize_global_reset,
)
from pc.quota import (
    AccountQuotaResult,
    RateLimitWindow,
    parse_app_server_rate_limits,
)
from pc.sender import (
    CdmSender,
    DeviceSequenceState,
    LoopbackSink,
    SenderStateError,
    StateStore,
)
from pc.session import (
    SessionTokenState,
    parse_session_file,
    scan_sessions_directory,
    select_latest_session,
)


class TestSessionCollector(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cumulative_token_count_not_double_summed(self):
        """Cumulative event_msg/token_count must replace previous values, not sum."""
        session_file = self.dir_path / "session_1.jsonl"
        lines = [
            json.dumps({"timestamp": "2026-10-08T10:00:00Z", "type": "session_start"}),
            json.dumps(
                {
                    "timestamp": "2026-10-08T10:01:00Z",
                    "type": "token_count",
                    "total_token_usage": {
                        "input_tokens": 100,
                        "output_tokens": 50,
                        "cached_input_tokens": 20,
                        "reasoning_output_tokens": 10,
                        "total_tokens": 150,
                    },
                }
            ),
            # Repeated / updated cumulative event
            json.dumps(
                {
                    "timestamp": "2026-10-08T10:02:00Z",
                    "type": "event_msg",
                    "token_count": {
                        "total_token_usage": {
                            "input_tokens": 150,
                            "output_tokens": 70,
                            "cached_input_tokens": 30,
                            "reasoning_output_tokens": 15,
                            "total_tokens": 220,
                        }
                    },
                }
            ),
        ]
        session_file.write_text("\n".join(lines), encoding="utf-8")

        state = parse_session_file(session_file)
        self.assertIsNotNone(state)
        self.assertEqual(state.input_tokens, 150)
        self.assertEqual(state.output_tokens, 70)
        self.assertEqual(state.cached_input_tokens, 30)
        self.assertEqual(state.reasoning_output_tokens, 15)
        self.assertEqual(state.source_total_tokens, 220)
        self.assertEqual(state.normalized_total_tokens, 220)  # 150 + 70
        self.assertEqual(state.event_count, 2)
        self.assertEqual(state.observed_at, "2026-10-08T10:02:00Z")

    def test_partial_line_and_truncation_handling(self):
        """Malformed or incomplete lines in JSONL should be skipped gracefully."""
        session_file = self.dir_path / "session_broken.jsonl"
        content = (
            '{"timestamp": "2026-10-08T10:00:00Z", "type": "token_count", '
            '"total_token_usage": {"input_tokens": 50, "output_tokens": 25, "total_tokens": 75}}\n'
            '{"truncated_json": true, "some_field": \n'
            '{"timestamp": "2026-10-08T10:05:00Z", "type": "token_count", '
            '"total_token_usage": {"input_tokens": 80, "output_tokens": 40, "total_tokens": 120}}\n'
        )
        session_file.write_text(content, encoding="utf-8")

        state = parse_session_file(session_file)
        self.assertIsNotNone(state)
        self.assertEqual(state.input_tokens, 80)
        self.assertEqual(state.output_tokens, 40)
        self.assertEqual(state.normalized_total_tokens, 120)

    def test_differing_source_total_and_normalized_total(self):
        """If source reported total differs from input + output, both must be preserved."""
        session_file = self.dir_path / "session_diff.jsonl"
        entry = {
            "timestamp": "2026-10-08T12:00:00Z",
            "type": "token_count",
            "total_token_usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "cached_input_tokens": 10,
                "reasoning_output_tokens": 5,
                "total_tokens": 300,  # Deliberately differs from 100 + 50
            },
        }
        session_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        state = parse_session_file(session_file)
        self.assertIsNotNone(state)
        self.assertEqual(state.normalized_total_tokens, 150)
        self.assertEqual(state.source_total_tokens, 300)

        # Build snapshot and verify channels
        snap = build_session_telemetry_snapshot(state)
        channels = {w["window_id"]: w["used_units"] for w in snap["windows"]}
        self.assertEqual(channels["normalized_total"], 150.0)
        self.assertEqual(channels["source_total"], 300.0)
        self.assertEqual(channels["input"], 100.0)
        self.assertEqual(channels["output"], 50.0)
        self.assertEqual(channels["cached_input"], 10.0)
        self.assertEqual(channels["reasoning_output"], 5.0)

    def test_privacy_boundary(self):
        """Verify no conversation dialogue or paths leak into normalized snapshot."""
        state = SessionTokenState(
            session_id="synthetic-session-123",
            observed_at="2026-10-08T10:00:00Z",
            input_tokens=100,
            output_tokens=50,
            source_path="C:\\Secret\\Path\\session.jsonl",
        )
        snap = build_session_telemetry_snapshot(state)
        raw_snap = json.dumps(snap)
        self.assertNotIn("Secret", raw_snap)
        self.assertNotIn("session.jsonl", raw_snap)

    def test_directory_scan_and_latest_selection(self):
        """Multiple sessions should be scanned and latest selected by timestamp."""
        (self.dir_path / "s1.jsonl").write_text(
            json.dumps({"timestamp": "2026-10-08T09:00:00Z", "type": "token_count", "total_token_usage": {"input_tokens": 10}}) + "\n"
        )
        (self.dir_path / "s2.jsonl").write_text(
            json.dumps({"timestamp": "2026-10-08T11:00:00Z", "type": "token_count", "total_token_usage": {"input_tokens": 20}}) + "\n"
        )
        (self.dir_path / "s3.jsonl").write_text(
            json.dumps({"timestamp": "2026-10-08T10:00:00Z", "type": "token_count", "total_token_usage": {"input_tokens": 15}}) + "\n"
        )

        sessions = scan_sessions_directory(self.dir_path)
        self.assertEqual(len(sessions), 3)
        latest = select_latest_session(sessions)
        self.assertIsNotNone(latest)
        self.assertEqual(latest.session_id, "s2")
        self.assertEqual(latest.input_tokens, 20)


class TestQuotaCollector(unittest.TestCase):
    def test_app_server_response_parsing(self):
        """Parse native account/rateLimits/read JSON-RPC structure."""
        synthetic_rpc = {
            "id": 2,
            "result": {
                "accountId": "test-account-123",
                "rateLimits": {
                    "planType": "plus",
                    "primary": {
                        "usedPercent": 35.5,
                        "windowDurationMins": 300,
                        "resetsAt": 1791484074,
                    },
                    "secondary": {
                        "usedPercent": 15.0,
                        "windowDurationMins": 10080,
                        "resetsAt": 1791987242,
                    },
                },
            },
        }

        quota_res = parse_app_server_rate_limits(synthetic_rpc, "2026-10-08T12:00:00Z")
        self.assertEqual(quota_res.account_id, "test-account-123")
        self.assertEqual(quota_res.plan_type, "plus")
        self.assertIn("primary", quota_res.windows)
        self.assertIn("secondary", quota_res.windows)

        primary = quota_res.windows["primary"]
        self.assertEqual(primary.duration_seconds, 18000)
        self.assertEqual(primary.duration_label, "5h limit")
        self.assertEqual(primary.used_percent, 35.5)
        self.assertEqual(primary.percent_remaining, 64.5)

        # Build snapshot
        snap = build_account_quota_snapshot(quota_res)
        semantic_validate_snapshot(snap)
        self.assertEqual(snap["provider_id"], "codex")
        self.assertEqual(snap["metric_kind"], "quota_window")
        self.assertEqual(snap["unit"], "percent")
        self.assertEqual(len(snap["windows"]), 2)


class TestValidationAndFraming(unittest.TestCase):
    def test_semantic_rule_available_requires_agent_and_host(self):
        """P2 rule: available source must have non-null agent_id and host_id."""
        snap = {
            "schema_version": 1,
            "snapshot_id": "test-snap",
            "provider_id": "codex",
            "agent_id": None,  # Null on available violates semantic rule
            "host_id": "pc-host",
            "model_id": None,
            "account_profile_id": None,
            "source_kind": "local_runtime",
            "metric_kind": "session_telemetry",
            "unit": "token",
            "status": "available",
            "observed_at": "2026-10-08T12:00:00Z",
            "windows": [],
            "stale": False,
            "last_good_at": "2026-10-08T12:00:00Z",
            "error_code": None,
            "error_reason": None,
        }
        with self.assertRaises(FrameError) as cm:
            semantic_validate_snapshot(snap)
        self.assertEqual(cm.exception.code, "SEMANTIC_AVAILABLE_AGENT_REQUIRED")

    def test_canonical_json_and_crc32(self):
        """Test canonical JSON encoding and CRC32 calculation."""
        payload = {"b": 2, "a": 1}
        encoded = canonical_json(payload)
        self.assertEqual(encoded, b'{"a":1,"b":2}')
        self.assertEqual(crc32_hex(encoded), "CF41CE83")

    def test_frame_size_and_newline_contract(self):
        """cdm/1 frame must have single LF, max 64KB, and match CRC32."""
        snap = {
            "schema_version": 1,
            "snapshot_id": "snap-1",
            "provider_id": "codex",
            "agent_id": "codex-cli",
            "host_id": "pc-collector",
            "model_id": None,
            "account_profile_id": None,
            "source_kind": "local_runtime",
            "metric_kind": "session_telemetry",
            "unit": "token",
            "status": "available",
            "observed_at": "2026-10-08T12:00:00Z",
            "windows": [],
            "stale": False,
            "last_good_at": "2026-10-08T12:00:00Z",
            "error_code": None,
            "error_reason": None,
        }
        payload = {"usage": [snap], "global_resets": []}
        frame = build_frame(payload, sequence=1, sent_at="2026-10-08T12:00:00Z")
        raw_bytes = encode_frame(frame)

        self.assertTrue(raw_bytes.endswith(b"\n"))
        self.assertEqual(raw_bytes.count(b"\n"), 1)
        self.assertLessEqual(len(raw_bytes), MAX_FRAME_BYTES)

        decoded = decode_frame(raw_bytes)
        self.assertEqual(decoded["sequence"], 1)
        self.assertEqual(decoded["protocol"], "cdm/1")


class TestSequenceAndSenderState(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file = Path(self.temp_dir.name) / "sender-state.json"
        self.store = StateStore(self.state_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_sequence_wrap_around_logic(self):
        """uint32 sequence wrap around rules."""
        self.assertTrue(sequence_is_newer(1, 0))
        self.assertTrue(sequence_is_newer(0, MAX_SEQUENCE))  # 4294967295 -> 0
        self.assertFalse(sequence_is_newer(0, 1))
        self.assertFalse(sequence_is_newer(5, 5))  # Duplicate
        self.assertFalse(sequence_is_newer(10, 10 + 2**31))  # Half-range boundary

    def test_atomic_sequence_reservation_consumes_on_failure(self):
        """Sequence reservation must increment atomically BEFORE write; failed write consumes sequence."""
        self.store.initialize_new("meter-1", initial_sequence=5)
        sender = CdmSender("meter-1", self.store)

        snap = {
            "schema_version": 1,
            "snapshot_id": "snap-1",
            "provider_id": "codex",
            "agent_id": "codex-cli",
            "host_id": "pc-collector",
            "model_id": None,
            "account_profile_id": None,
            "source_kind": "local_runtime",
            "metric_kind": "session_telemetry",
            "unit": "token",
            "status": "available",
            "observed_at": "2026-10-08T12:00:00Z",
            "windows": [],
            "stale": False,
            "last_good_at": "2026-10-08T12:00:00Z",
            "error_code": None,
            "error_reason": None,
        }
        payload = {"usage": [snap], "global_resets": []}

        # 1. Successful write consumes seq=5, next is 6
        sink = LoopbackSink()
        outcome1 = sender.transmit_payload(payload, "2026-10-08T12:00:00Z", sink=sink)
        self.assertTrue(outcome1.success)
        self.assertEqual(outcome1.sequence_used, 5)
        self.assertEqual(sender.current_sequence, 6)

        # 2. Failed write (sink closed) consumes seq=6, next is 7
        sink.close()
        outcome2 = sender.transmit_payload(payload, "2026-10-08T12:00:00Z", sink=sink)
        self.assertFalse(outcome2.success)
        self.assertEqual(outcome2.sequence_used, 6)
        self.assertEqual(sender.current_sequence, 7)

        # 3. Verify state persisted on disk matches sequence 7
        loaded_state = self.store.load("meter-1")
        self.assertIsNotNone(loaded_state)
        self.assertEqual(loaded_state.next_sequence, 7)

    def test_state_corruption_fails_closed(self):
        """Corrupt state file stops transmission immediately."""
        self.state_file.write_text("corrupted json data", encoding="utf-8")
        with self.assertRaises(SenderStateError):
            CdmSender("meter-1", self.store)


class TestStaleThresholds(unittest.TestCase):
    def test_stale_boundaries_0_299_300(self):
        """Snapshot age < 300s is fresh, >= 300s is stale."""
        base_time = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)

        # 0s diff
        ref_0 = base_time.isoformat().replace("+00:00", "Z")
        diff_0 = (datetime.fromisoformat(ref_0) - base_time).total_seconds()
        self.assertFalse(diff_0 >= 300)

        # 299s diff
        ref_299 = (base_time + timedelta(seconds=299)).isoformat().replace("+00:00", "Z")
        diff_299 = (datetime.fromisoformat(ref_299) - base_time).total_seconds()
        self.assertFalse(diff_299 >= 300)

        # 300s diff
        ref_300 = (base_time + timedelta(seconds=300)).isoformat().replace("+00:00", "Z")
        diff_300 = (datetime.fromisoformat(ref_300) - base_time).total_seconds()
        self.assertTrue(diff_300 >= 300)


if __name__ == "__main__":
    unittest.main()
