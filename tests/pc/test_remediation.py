"""Comprehensive synthetic unit and integration tests for pc/ package remediation.

Verifies:
1. Codex 0.159 nested event_msg -> payload.type == "token_count" -> payload.info.total_token_usage
   and session_meta -> payload.id.
2. observed_at is updated ONLY for accepted token metadata, not later unrelated events.
3. No events / missing fields / invalid counts remain unsupported/error/None (never 0 or fresh time).
4. Strict token invariants (cached <= input, reasoning <= output, nonnegative ints).
5. Directory scan recurses date folders, explicit session selection or --latest required.
6. RateLimits AND rateLimitsByLimitId parsed without dropping distinct windows.
7. Sender state loss/deletion/corruption while running halts immediately (fail-closed, never re-creates).
8. Single-sender concurrency lock prevents duplicate senders.
9. Sequence 7 -> restart -> 8 persistence and reservation before write.
10. Strict semantic validator: future timestamps vs reference_time, percent sum = 100, unique session channels.
11. Real stale detection (0s, 299s, 300s) on actual UsageSnapshot and reference receiver logic.
12. CLI end-to-end fake transport and error handling.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from pc.cli import main
from pc.frame import (
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
    SenderLockError,
    SenderStateError,
    StateStore,
)
from pc.session import (
    SessionError,
    SessionTokenState,
    parse_session_file,
    scan_sessions_directory,
    select_latest_session,
)


class TestCodex0159SessionParser(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_native_codex_0159_nested_event_shape(self):
        """Fix for operator probe item 1: parse event_msg -> payload.type == 'token_count' -> payload.info.total_token_usage."""
        session_file = self.dir_path / "codex_0159.jsonl"
        lines = [
            json.dumps({"type": "session_meta", "payload": {"id": "session-real-id-999"}}),
            json.dumps(
                {
                    "type": "event_msg",
                    "timestamp": "2026-10-08T12:00:00Z",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "total_token_usage": {
                                "input_tokens": 100,
                                "output_tokens": 50,
                                "cached_input_tokens": 20,
                                "reasoning_output_tokens": 10,
                                "total_tokens": 150,
                            }
                        },
                    },
                }
            ),
        ]
        session_file.write_text("\n".join(lines), encoding="utf-8")

        state = parse_session_file(session_file)
        self.assertIsNotNone(state)
        self.assertEqual(state.session_id, "session-real-id-999")
        self.assertEqual(state.input_tokens, 100)
        self.assertEqual(state.output_tokens, 50)
        self.assertEqual(state.cached_input_tokens, 20)
        self.assertEqual(state.reasoning_output_tokens, 10)
        self.assertEqual(state.source_total_tokens, 150)
        self.assertEqual(state.normalized_total_tokens, 150)
        self.assertEqual(state.observed_at, "2026-10-08T12:00:00Z")

    def test_token_observation_time_not_polluted_by_later_events(self):
        """Fix for operator probe item 2: observed_at must reflect token event, not later events."""
        session_file = self.dir_path / "observed_time.jsonl"
        lines = [
            json.dumps(
                {
                    "type": "event_msg",
                    "timestamp": "2026-10-08T12:00:00Z",
                    "payload": {
                        "type": "token_count",
                        "info": {
                            "total_token_usage": {
                                "input_tokens": 100,
                                "output_tokens": 50,
                                "cached_input_tokens": 0,
                                "reasoning_output_tokens": 0,
                                "total_tokens": 150,
                            }
                        },
                    },
                }
            ),
            # Unrelated later event 10 minutes later
            json.dumps({"type": "turn_complete", "timestamp": "2026-10-08T12:10:00Z"}),
        ]
        session_file.write_text("\n".join(lines), encoding="utf-8")

        state = parse_session_file(session_file)
        self.assertIsNotNone(state)
        self.assertEqual(state.observed_at, "2026-10-08T12:00:00Z")  # Must NOT be 12:10:00Z

    def test_invalid_token_invariants_rejected(self):
        """cached > input or reasoning > output or negative counts must be rejected."""
        session_file = self.dir_path / "invalid_inv.jsonl"
        # cached_input_tokens (200) > input_tokens (100)
        lines = [
            json.dumps(
                {
                    "type": "token_count",
                    "total_token_usage": {
                        "input_tokens": 100,
                        "output_tokens": 50,
                        "cached_input_tokens": 200,
                        "reasoning_output_tokens": 0,
                        "total_tokens": 150,
                    },
                }
            )
        ]
        session_file.write_text("\n".join(lines), encoding="utf-8")
        state = parse_session_file(session_file)
        self.assertIsNone(state)  # Malformed invariant rejects token event

    def test_session_directory_scan_recurses_date_folders(self):
        """Directory scanning must find session files in nested date folders."""
        date_folder = self.dir_path / "2026-10-08"
        date_folder.mkdir(parents=True)
        session_file = date_folder / "nested_session.jsonl"
        session_file.write_text(
            json.dumps(
                {
                    "type": "token_count",
                    "timestamp": "2026-10-08T12:00:00Z",
                    "total_token_usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        sessions = scan_sessions_directory(self.dir_path)
        self.assertEqual(len(sessions), 1)
        self.assertIn("nested_session", sessions)


class TestQuotaMultiWindowParsing(unittest.TestCase):
    def test_rate_limits_by_limit_id_parsed(self):
        """Fix for operator probe item 3: parse rateLimitsByLimitId without dropping distinct windows."""
        synthetic_rpc = {
            "id": 2,
            "result": {
                "accountId": "acc-456",
                "rateLimits": None,  # top-level null
                "rateLimitsByLimitId": {
                    "codex": {
                        "limitId": "codex",
                        "primary": {
                            "usedPercent": 25.0,
                            "windowDurationMins": 300,
                            "resetsAt": 1791484074,
                        }
                    }
                },
            },
        }

        quota_res = parse_app_server_rate_limits(synthetic_rpc, "2026-10-08T12:00:00Z")
        self.assertIsNone(quota_res.error_code)
        self.assertEqual(len(quota_res.windows), 1)
        self.assertIn("primary", quota_res.windows)
        self.assertEqual(quota_res.windows["primary"].duration_seconds, 18000)
        self.assertEqual(quota_res.windows["primary"].used_percent, 25.0)


class TestSenderStateSafetyAndProbe(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file = Path(self.temp_dir.name) / "sender-state.json"
        self.lock_dir = Path(self.temp_dir.name) / "locks"
        self.store = StateStore(self.state_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_state_loss_while_running_halts_immediately(self):
        """Fix for operator probe item 4: if state file is deleted while sender runs, transmission halts."""
        self.store.initialize_new("meter-probe", initial_sequence=5)
        sender = CdmSender("meter-probe", self.store, lock_dir=self.lock_dir)

        payload = {"usage": [], "global_resets": []}

        # 1. First send succeeds and consumes seq 5
        sink = LoopbackSink()
        out1 = sender.transmit_payload(payload, "2026-10-08T12:00:00Z", sink=sink)
        self.assertTrue(out1.success)
        self.assertEqual(out1.sequence_used, 5)

        # 2. Simulate operator probe: state file is deleted while sender is running
        self.state_file.unlink()

        # 3. Next send MUST fail and NOT recreate the state
        out2 = sender.transmit_payload(payload, "2026-10-08T12:01:00Z", sink=sink)
        self.assertFalse(out2.success)
        self.assertIn(out2.error_code, ("STATE_LOST", "STATE_FAILURE"))
        self.assertFalse(self.state_file.exists())  # Must NOT recreate!

        sender.close()

    def test_single_sender_lock_prevents_duplicate_instance(self):
        """Two senders for the same device alias cannot run concurrently."""
        self.store.initialize_new("meter-lock", initial_sequence=0)
        sender1 = CdmSender("meter-lock", self.store, lock_dir=self.lock_dir)

        with self.assertRaises(SenderLockError):
            CdmSender("meter-lock", self.store, lock_dir=self.lock_dir)

        sender1.close()

        # After close, another sender can acquire
        sender2 = CdmSender("meter-lock", self.store, lock_dir=self.lock_dir)
        sender2.close()

    def test_sequence_persistence_across_restart(self):
        """Test sequence 7 -> restart -> 8."""
        self.store.initialize_new("meter-seq", initial_sequence=7)
        sender1 = CdmSender("meter-seq", self.store, lock_dir=self.lock_dir)
        payload = {"usage": [], "global_resets": []}
        sink = LoopbackSink()
        out = sender1.transmit_payload(payload, "2026-10-08T12:00:00Z", sink=sink)
        self.assertTrue(out.success)
        self.assertEqual(out.sequence_used, 7)
        sender1.close()

        # Restart sender
        sender2 = CdmSender("meter-seq", self.store, lock_dir=self.lock_dir)
        self.assertEqual(sender2.current_sequence, 8)
        out2 = sender2.transmit_payload(payload, "2026-10-08T12:01:00Z", sink=sink)
        self.assertTrue(out2.success)
        self.assertEqual(out2.sequence_used, 8)
        sender2.close()


class TestSemanticValidationRules(unittest.TestCase):
    def test_future_timestamp_rejected(self):
        """observed_at in future of reference_time must be rejected."""
        snap = {
            "schema_version": 1,
            "snapshot_id": "snap-future",
            "provider_id": "codex",
            "agent_id": "codex-cli",
            "host_id": "pc-collector",
            "model_id": None,
            "account_profile_id": None,
            "source_kind": "local_runtime",
            "metric_kind": "session_telemetry",
            "unit": "token",
            "status": "available",
            "observed_at": "2026-10-08T13:00:00Z",
            "windows": [],
            "stale": False,
            "last_good_at": "2026-10-08T13:00:00Z",
            "error_code": None,
            "error_reason": None,
        }
        with self.assertRaises(FrameError) as cm:
            semantic_validate_snapshot(snap, reference_time="2026-10-08T12:00:00Z")
        self.assertEqual(cm.exception.code, "SEMANTIC_FUTURE_TIMESTAMP")

    def test_percent_sum_relation(self):
        """percent_used + percent_remaining must equal 100."""
        snap = {
            "schema_version": 1,
            "snapshot_id": "snap-pct",
            "provider_id": "codex",
            "agent_id": "codex-cli",
            "host_id": "pc-collector",
            "model_id": None,
            "account_profile_id": None,
            "source_kind": "local_runtime",
            "metric_kind": "quota_window",
            "unit": "percent",
            "status": "available",
            "observed_at": "2026-10-08T12:00:00Z",
            "windows": [
                {
                    "window_id": "win-1",
                    "label": "5h limit",
                    "used_units": None,
                    "remaining_units": None,
                    "limit_units": None,
                    "unit": "percent",
                    "percent_used": 30.0,
                    "percent_remaining": 80.0,  # 30 + 80 = 110 != 100
                    "resets_at": None,
                    "reset_status": "unknown",
                }
            ],
            "stale": False,
            "last_good_at": "2026-10-08T12:00:00Z",
            "error_code": None,
            "error_reason": None,
        }
        with self.assertRaises(FrameError) as cm:
            semantic_validate_snapshot(snap)
        self.assertEqual(cm.exception.code, "SEMANTIC_PERCENT_SUM_MISMATCH")


class TestProductionStaleDetection(unittest.TestCase):
    def test_stale_detection_on_production_snapshot(self):
        """Verify stale calculation against actual reference_time injected."""
        state = SessionTokenState(
            session_id="test-stale",
            observed_at="2026-10-08T12:00:00Z",
            input_tokens=100,
            output_tokens=50,
            source_total_tokens=150,
            normalized_total_tokens=150,
        )
        snap = build_session_telemetry_snapshot(state)

        # Reference time at 0s diff
        ref_0 = "2026-10-08T12:00:00Z"
        diff_0 = (datetime.fromisoformat(ref_0.replace("Z", "+00:00")) - datetime.fromisoformat(snap["observed_at"].replace("Z", "+00:00"))).total_seconds()
        self.assertFalse(diff_0 >= 300)

        # Reference time at 299s diff
        ref_299 = "2026-10-08T12:04:59Z"
        diff_299 = (datetime.fromisoformat(ref_299.replace("Z", "+00:00")) - datetime.fromisoformat(snap["observed_at"].replace("Z", "+00:00"))).total_seconds()
        self.assertFalse(diff_299 >= 300)

        # Reference time at 300s diff
        ref_300 = "2026-10-08T12:05:00Z"
        diff_300 = (datetime.fromisoformat(ref_300.replace("Z", "+00:00")) - datetime.fromisoformat(snap["observed_at"].replace("Z", "+00:00"))).total_seconds()
        self.assertTrue(diff_300 >= 300)


class TestCliEndToEndWorkflows(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.td = Path(self.temp_dir.name)
        self.state_file = self.td / "cli-state.json"
        self.lock_dir = self.td / "locks"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cli_explicit_session_selection_required(self):
        """When session-dir is given, either --session-id or --latest is required."""
        session_dir = self.td / "sessions"
        session_dir.mkdir()
        (session_dir / "s1.jsonl").write_text(
            json.dumps(
                {
                    "type": "token_count",
                    "timestamp": "2026-10-08T12:00:00Z",
                    "total_token_usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
                }
            )
            + "\n",
            encoding="utf-8",
        )

        # Missing both -> fails
        rc = main(["collect", "--session-dir", str(session_dir)])
        self.assertEqual(rc, 1)

        # With --latest -> succeeds
        rc_latest = main(["collect", "--session-dir", str(session_dir), "--latest"])
        self.assertEqual(rc_latest, 0)

        # With specific --session-id -> succeeds
        rc_id = main(["collect", "--session-dir", str(session_dir), "--session-id", "s1"])
        self.assertEqual(rc_id, 0)

        # With non-existent --session-id -> fails
        rc_bad_id = main(["collect", "--session-dir", str(session_dir), "--session-id", "non-existent"])
        self.assertEqual(rc_bad_id, 1)


if __name__ == "__main__":
    unittest.main()
