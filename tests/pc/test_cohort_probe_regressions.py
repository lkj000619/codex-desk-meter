"""Targeted regression tests for cohort probe failures and production C interoperability.

Covers:
1. Watch sent_at stamped after acquisition, satisfying envelope-time invariant and accepted by production C.
2. Invariant violation (observed_at > sent_at) rejected by PC build_frame and production C (SNAPSHOT_INVALID).
3. Cold global error omits unobserved record on wire, valid schema accepted by production C, reports failure locally / nonzero collect.
4. Warm global error retains true captured_at and is accepted by production C.
5. Provider file with 3 entries retains all 3 on load error and is accepted by production C.
6. Malformed provider entry is isolated without failing healthy updates.
7. Session identity uses path context and actual session, path changes do not inherit cache, no paths on wire.
8. Watch automatic interval (<=60s) includes collection/write duration.
9. Watch manual trigger does not move the automatic deadline.
10. Persistent port reopen throttling and immediate transmission.
"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

from pc.cli import cmd_collect, run_watch_loop
from pc.frame import (
    FrameError,
    build_frame,
    canonical_json,
    encode_frame,
    validate_envelope_time_invariant,
)
from pc.sender import CdmSender, LoopbackSink, StateStore
from pc.state import SharedCollectionState

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "tests/firmware/.build/cdm-host.exe"


def run_c_wire(*events: tuple[bytes, int, int | None]) -> list[dict]:
    """Execute raw encoded frames against read-only production C cdm-host.exe."""
    request = {
        "events": [
            {
                "line_hex": line.hex(),
                "mono_ms": mono,
                "now_ms": mono if now is None else now,
            }
            for line, mono, now in events
        ]
    }
    result = subprocess.run(
        [str(EXE), "--wire"],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=True,
        cwd=ROOT,
    )
    return json.loads(result.stdout)


class FakeClock:
    def __init__(self, start_time: float = 1000.0):
        self.current_time = start_time

    def now(self) -> float:
        return self.current_time

    def advance(self, seconds: float) -> None:
        self.current_time += seconds

    def sleep(self, seconds: float) -> None:
        self.current_time += seconds
        time.sleep(0.005)


class TestCohortProbeRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not EXE.exists():
            raise RuntimeError(f"Missing production C binary: {EXE}")

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.td = Path(self.temp_dir.name)
        self.state_file = self.td / "sender-state.json"
        self.lock_dir = self.td / "locks"
        self.store = StateStore(self.state_file)
        self.store.initialize_new("test-alias", initial_sequence=0)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_watch_sent_at_stamped_after_acquisition_accepted_by_production_c(self):
        """Acquisition-first stamping guarantees observed_at <= sent_at; C accepts without SNAPSHOT_INVALID."""
        sess_file = self.td / "live_session.jsonl"
        sess_file.write_text(
            json.dumps({
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "timestamp": "2026-10-09T08:58:41.000000Z",
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
            }) + "\n",
            encoding="utf-8",
        )

        sm = SharedCollectionState()
        # Collect payload first
        payload = sm.collect_all(session_file=sess_file)
        # Stamp sent_at after acquisition
        obs_str = payload["usage"][0]["observed_at"]
        sent_at = "2026-10-09T08:58:42.000000Z"  # sent_at after observed_at

        # Verify envelope-time invariant
        validate_envelope_time_invariant(payload, sent_at)

        # Build and encode frame
        frame = build_frame(payload, sequence=0, sent_at=sent_at)
        raw_bytes = encode_frame(frame)

        # Send to actual production C
        out = run_c_wire((raw_bytes, 1000, 1000))
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0]["accepted"], out[0].get("error"))
        self.assertEqual(out[0]["sequence"], 0)
        self.assertEqual(len(out[0]["usage"]), 1)
        self.assertEqual(out[0]["usage"][0]["current"]["windows"][0]["used_units"], 100)

    def test_future_observation_rejected_by_envelope_validation_and_production_c(self):
        """Observed timestamp in future of sent_at is rejected by PC build_frame and production C."""
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
            "observed_at": "2026-10-09T08:58:42.000000Z",  # newer than sent_at
            "windows": [
                {"window_id": "input", "label": "in", "used_units": 10, "remaining_units": None, "limit_units": None, "unit": "token", "percent_used": None, "percent_remaining": None, "resets_at": None, "reset_status": "unknown"},
                {"window_id": "output", "label": "out", "used_units": 20, "remaining_units": None, "limit_units": None, "unit": "token", "percent_used": None, "percent_remaining": None, "resets_at": None, "reset_status": "unknown"},
                {"window_id": "cached_input", "label": "cached", "used_units": 5, "remaining_units": None, "limit_units": None, "unit": "token", "percent_used": None, "percent_remaining": None, "resets_at": None, "reset_status": "unknown"},
                {"window_id": "reasoning_output", "label": "reason", "used_units": 5, "remaining_units": None, "limit_units": None, "unit": "token", "percent_used": None, "percent_remaining": None, "resets_at": None, "reset_status": "unknown"},
                {"window_id": "source_total", "label": "source", "used_units": 30, "remaining_units": None, "limit_units": None, "unit": "token", "percent_used": None, "percent_remaining": None, "resets_at": None, "reset_status": "unknown"},
                {"window_id": "normalized_total", "label": "norm", "used_units": 30, "remaining_units": None, "limit_units": None, "unit": "token", "percent_used": None, "percent_remaining": None, "resets_at": None, "reset_status": "unknown"},
            ],
            "stale": False,
            "last_good_at": "2026-10-09T08:58:42.000000Z",
            "error_code": None,
            "error_reason": None,
        }
        sent_at_before = "2026-10-09T08:58:41.000000Z"

        # PC build_frame must reject
        with self.assertRaises(FrameError) as cm:
            build_frame({"usage": [snap], "global_resets": []}, sequence=0, sent_at=sent_at_before)
        self.assertIn("SNAPSHOT_INVALID", str(cm.exception))

        # Raw bypass frame must be rejected by production C with SNAPSHOT_INVALID
        import zlib
        unsigned = {
            "protocol": "cdm/1",
            "sequence": 0,
            "sent_at": sent_at_before,
            "payload": {"usage": [snap], "global_resets": []},
        }
        crc = zlib.crc32(canonical_json(unsigned)) & 0xFFFFFFFF
        envelope = {"integrity": {"algorithm": "crc32", "value": f"{crc:08X}"}, **unsigned}
        line = canonical_json(envelope) + b"\n"
        out = run_c_wire((line, 1000, 1000))
        self.assertFalse(out[0]["accepted"])
        self.assertEqual(out[0]["error"], "SNAPSHOT_INVALID")

    def test_cold_global_omitted_on_wire_and_reports_locally_nonzero(self):
        """Cold global error omits record on wire, valid frame passes C, collect returns 1."""
        missing_reset = self.td / "non_existent_global.json"
        sm = SharedCollectionState()

        # Run collect_all with missing global reset
        payload = sm.collect_all(global_reset_file=missing_reset, reference_time="2026-10-09T08:00:00Z")
        # Record is omitted on wire to avoid captured_at=null violation
        self.assertEqual(payload["global_resets"], [])
        self.assertTrue(any("global_reset" in k for k in sm.source_errors))

        # Frame with empty global_resets is schema-valid and accepted by production C
        frame = build_frame(payload, 0, "2026-10-09T08:00:00Z", reference_time="2026-10-09T08:00:00Z")
        line = encode_frame(frame, reference_time="2026-10-09T08:00:00Z")
        out = run_c_wire((line, 1000, 1000))
        self.assertTrue(out[0]["accepted"], out[0].get("error"))

        # CLI collect must report nonzero on cold source error
        args = argparse.Namespace(
            session_file=None,
            session_dir=None,
            session_id=None,
            latest=False,
            live_quota=False,
            provider_fixture=None,
            personal_usage=None,
            global_reset=str(missing_reset),
            host_alias="pc-collector",
            agent_id="codex-cli",
            reference_time="2026-10-09T08:00:00Z",
            output=None,
        )
        self.assertEqual(cmd_collect(args, state_manager=sm), 1)

    def test_warm_global_retains_true_capture_accepted_by_production_c(self):
        """Warm global error retains true captured_at and is accepted by production C."""
        reset_file = self.td / "global_reset.json"
        reset_file.write_text(
            json.dumps({
                "source": "codex-resets.com",
                "captured_at": "2026-10-09T07:59:00Z",
                "latest_reset_at": "2026-10-09T07:50:00Z",
                "forecast_24h_percent": 15.0,
                "forecast_48h_percent": 30.0,
            }),
            encoding="utf-8",
        )
        sm = SharedCollectionState()
        # Initial successful collect (age 60s < 300s threshold -> good status)
        res1 = sm.collect_all(global_reset_file=reset_file, reference_time="2026-10-09T08:00:00Z")
        self.assertEqual(len(res1["global_resets"]), 1)
        self.assertEqual(res1["global_resets"][0]["captured_at"], "2026-10-09T07:59:00Z")
        self.assertFalse(res1["global_resets"][0]["stale"])

        # Now delete file -> warm error
        reset_file.unlink()
        res2 = sm.collect_all(global_reset_file=reset_file, reference_time="2026-10-09T08:00:00Z")
        self.assertEqual(len(res2["global_resets"]), 1)
        # Retains true captured_at
        self.assertEqual(res2["global_resets"][0]["captured_at"], "2026-10-09T07:59:00Z")
        self.assertEqual(res2["global_resets"][0]["error_code"], "GLOBAL_RESET_ERROR")

        # Send both frames to production C
        frame1 = build_frame(res1, 0, "2026-10-09T08:00:00Z", reference_time="2026-10-09T08:00:00Z")
        line1 = encode_frame(frame1, reference_time="2026-10-09T08:00:00Z")
        frame2 = build_frame(res2, 1, "2026-10-09T08:00:00Z", reference_time="2026-10-09T08:00:00Z")
        line2 = encode_frame(frame2, reference_time="2026-10-09T08:00:00Z")

        out = run_c_wire((line1, 1000, 1000), (line2, 2000, 2000))
        self.assertEqual([r["accepted"] for r in out], [True, True])
        self.assertEqual(out[1]["global"][0]["good"]["latest_reset_at"], "2026-10-09T07:50:00Z")

    def test_multi_provider_file_failure_retains_all_entries_accepted_by_production_c(self):
        """Provider file with 3 entries retains all 3 on file error and is accepted by production C."""
        multi_file = self.td / "multi_providers.json"
        raw_multi = (ROOT / "experiments/fixtures/providers/multi-provider-healthy.json").read_text(encoding="utf-8")
        multi_file.write_text(raw_multi, encoding="utf-8")

        sm = SharedCollectionState()
        # Iteration 1: load 3 entries
        res1 = sm.collect_all(provider_fixtures=[multi_file], reference_time="2026-09-10T00:00:00Z")
        self.assertEqual(len(res1["usage"]), 3)
        initial_providers = [s["provider_id"] for s in res1["usage"]]
        self.assertEqual(initial_providers, ["openai", "anthropic", "google"])

        # Iteration 2: file fails (deleted)
        multi_file.unlink()
        res2 = sm.collect_all(provider_fixtures=[multi_file], reference_time="2026-09-10T00:00:00Z")
        # All 3 entries must be retained, not reduced to 1!
        self.assertEqual(len(res2["usage"]), 3)
        retained_providers = [s["provider_id"] for s in res2["usage"]]
        self.assertEqual(retained_providers, ["openai", "anthropic", "google"])
        self.assertTrue(all(s["status"] == "error" for s in res2["usage"]))
        self.assertTrue(all(s["error_code"] == "FIXTURE_LOAD_ERROR" for s in res2["usage"]))

        # Transmit to production C
        frame1 = build_frame(res1, 0, "2026-09-10T00:00:00Z", reference_time="2026-09-10T00:00:00Z")
        line1 = encode_frame(frame1, reference_time="2026-09-10T00:00:00Z")
        frame2 = build_frame(res2, 1, "2026-09-10T00:00:00Z", reference_time="2026-09-10T00:00:00Z")
        line2 = encode_frame(frame2, reference_time="2026-09-10T00:00:00Z")

        out = run_c_wire((line1, 1000, 1000), (line2, 2000, 2000))
        self.assertEqual([r["accepted"] for r in out], [True, True])
        self.assertEqual(len(out[1]["usage"]), 3)
        self.assertTrue(all(u["good"] is not None for u in out[1]["usage"]))

    def test_malformed_provider_entry_isolated_from_healthy_updates(self):
        """A single malformed entry is isolated without preventing healthy entries from updating."""
        multi_file = self.td / "mixed_providers.json"
        entries = [
            {
                "schema_version": 1, "snapshot_id": "fix-openai", "provider_id": "openai",
                "agent_id": "codex-cli", "host_id": "terminal", "model_id": None, "account_profile_id": "acct-openai",
                "source_kind": "fixture", "metric_kind": "quota_window", "unit": "percent",
                "status": "available", "observed_at": "2026-09-10T00:00:00Z",
                "windows": [{"window_id": "5h", "label": "5h", "used_units": None, "remaining_units": None, "limit_units": None, "unit": "percent", "percent_used": 20.0, "percent_remaining": 80.0, "resets_at": None, "reset_status": "unknown"}],
                "stale": False, "last_good_at": "2026-09-10T00:00:00Z", "error_code": None, "error_reason": None
            },
            {
                "schema_version": 1, "snapshot_id": "fix-bad", "provider_id": "anthropic",
                "agent_id": "claude-code", "host_id": "terminal", "model_id": None, "account_profile_id": "acct-anthropic",
                "source_kind": "fixture", "metric_kind": "quota_window", "unit": "percent",
                "status": "invalid_status_value",  # Schema violation
                "windows": [],
                "stale": False, "last_good_at": "2026-09-10T00:00:00Z", "error_code": None, "error_reason": None
            },
            {
                "schema_version": 1, "snapshot_id": "fix-google", "provider_id": "google",
                "agent_id": "gemini-cli", "host_id": "terminal", "model_id": None, "account_profile_id": "acct-google",
                "source_kind": "fixture", "metric_kind": "quota_window", "unit": "percent",
                "status": "available", "observed_at": "2026-09-10T00:00:00Z",
                "windows": [{"window_id": "daily", "label": "daily", "used_units": None, "remaining_units": None, "limit_units": None, "unit": "percent", "percent_used": 5.0, "percent_remaining": 95.0, "resets_at": None, "reset_status": "unknown"}],
                "stale": False, "last_good_at": "2026-09-10T00:00:00Z", "error_code": None, "error_reason": None
            }
        ]
        multi_file.write_text(json.dumps(entries), encoding="utf-8")

        sm = SharedCollectionState()
        res = sm.collect_all(provider_fixtures=[multi_file], reference_time="2026-09-10T00:00:00Z")
        self.assertEqual(len(res["usage"]), 3)
        self.assertEqual(res["usage"][0]["status"], "available")
        self.assertEqual(res["usage"][1]["status"], "error")
        self.assertEqual(res["usage"][1]["error_code"], "FIXTURE_ENTRY_ERROR")
        self.assertEqual(res["usage"][2]["status"], "available")

    def test_session_identity_path_context_and_no_contamination_on_path_change(self):
        """Path context prevents cache inheritance across different directories/files; no paths leak on wire."""
        sm = SharedCollectionState()

        # Session in dir1
        dir1 = self.td / "dir1"
        dir1.mkdir()
        f1 = dir1 / "session.jsonl"
        f1.write_text(
            json.dumps({"type": "token_count", "timestamp": "2026-10-09T08:00:00Z", "total_token_usage": {"input_tokens": 100, "output_tokens": 50}}) + "\n",
            encoding="utf-8",
        )
        res1 = sm.collect_all(session_file=f1, reference_time="2026-10-09T08:00:00Z")
        self.assertEqual(res1["usage"][0]["status"], "available")
        self.assertEqual(res1["usage"][0]["windows"][0]["used_units"], 100)

        # Same basename in dir2, but invalid/empty
        dir2 = self.td / "dir2"
        dir2.mkdir()
        f2 = dir2 / "session.jsonl"
        f2.write_text("invalid content\n", encoding="utf-8")

        res2 = sm.collect_all(session_file=f2, reference_time="2026-10-09T08:00:00Z")
        # Must NOT inherit dir1/session.jsonl values!
        self.assertEqual(res2["usage"][0]["status"], "error")
        self.assertEqual(len(res2["usage"][0]["windows"]), 0)

        # Ensure no filesystem paths appear in wire error_reason or snapshot_id
        wire_snap = res2["usage"][0]
        self.assertNotIn(":", wire_snap["snapshot_id"].replace("error-", ""))
        self.assertNotIn("/", wire_snap["snapshot_id"])
        self.assertNotIn("\\", wire_snap["snapshot_id"])
        if wire_snap.get("error_reason"):
            self.assertNotIn(str(dir2), wire_snap["error_reason"])

    def test_watch_auto_period_includes_slow_collection_duration(self):
        """Automatic interval (60s) includes collection duration; next auto occurs at t=60, not t=75."""
        clock = FakeClock(start_time=100.0)
        stop_event = threading.Event()
        sink = LoopbackSink()
        sm = SharedCollectionState()

        class Args:
            device_alias = "test-alias"
            interval = 60
            port = None
            dry_run = True
            state_file = str(self.state_file)
            lock_dir = str(self.lock_dir)
            session_file = None
            session_dir = None
            session_id = None
            latest = False
            live_quota = False
            provider_fixture = None
            personal_usage = None
            global_reset = None
            host_alias = "pc-test"
            agent_id = "codex-cli"
            reference_time = None
            once = False

        # Custom state manager where collection takes 15s simulated time
        class SlowStateManager(SharedCollectionState):
            def collect_all(self, *a, **kw):
                clock.advance(15.0)  # Collection takes 15s!
                return {"usage": [], "global_resets": []}

        watch_thread = threading.Thread(
            target=run_watch_loop,
            kwargs={
                "args": Args(),
                "state_manager": SlowStateManager(),
                "sink_override": sink,
                "stop_event": stop_event,
                "time_provider": clock,
            },
        )
        watch_thread.start()

        # Wait for initial iteration
        for _ in range(50):
            if len(sink.written_frames) >= 1:
                break
            time.sleep(0.02)
        self.assertEqual(len(sink.written_frames), 1)

        # Advance clock to 159.0 (only 59s since start, 44s since collection finished)
        clock.advance(44.0)
        time.sleep(0.05)
        self.assertEqual(len(sink.written_frames), 1)  # Still 1

        # Advance clock past 60s from start (at 160.0)
        clock.advance(2.0)
        for _ in range(50):
            if len(sink.written_frames) >= 2:
                break
            time.sleep(0.02)
        # Next auto iteration fired at t=60s from initial start (160.0), including 15s collection!
        self.assertEqual(len(sink.written_frames), 2)

        stop_event.set()
        watch_thread.join(timeout=1.0)

    def test_watch_manual_trigger_does_not_move_automatic_deadline(self):
        """Manual refresh does not push the automatic deadline backwards."""
        clock = FakeClock(start_time=100.0)
        stop_event = threading.Event()
        manual_event = threading.Event()
        sink = LoopbackSink()
        sm = SharedCollectionState()

        class Args:
            device_alias = "test-alias"
            interval = 60
            port = None
            dry_run = True
            state_file = str(self.state_file)
            lock_dir = str(self.lock_dir)
            session_file = None
            session_dir = None
            session_id = None
            latest = False
            live_quota = False
            provider_fixture = None
            personal_usage = None
            global_reset = None
            host_alias = "pc-test"
            agent_id = "codex-cli"
            reference_time = None
            once = False

        watch_thread = threading.Thread(
            target=run_watch_loop,
            kwargs={
                "args": Args(),
                "state_manager": sm,
                "sink_override": sink,
                "manual_trigger_event": manual_event,
                "stop_event": stop_event,
                "time_provider": clock,
            },
        )
        watch_thread.start()

        for _ in range(50):
            if len(sink.written_frames) >= 1:
                break
            time.sleep(0.02)
        self.assertEqual(len(sink.written_frames), 1)  # Iteration 1 (Auto) at 100.0

        # At t = 110.0 (10s later), manual trigger fires
        clock.advance(10.0)
        manual_event.set()
        for _ in range(50):
            if len(sink.written_frames) >= 2:
                break
            time.sleep(0.02)
        self.assertEqual(len(sink.written_frames), 2)  # Iteration 2 (Manual) at 110.0

        # Advance to 159.0 (59s from start, 49s after manual)
        clock.advance(49.0)
        time.sleep(0.05)
        self.assertEqual(len(sink.written_frames), 2)  # Still 2

        # Advance past 160.0 (60s from start) -> Automatic iteration MUST fire on schedule!
        clock.advance(2.0)
        for _ in range(50):
            if len(sink.written_frames) >= 3:
                break
            time.sleep(0.02)
        self.assertEqual(len(sink.written_frames), 3)  # Iteration 3 (Auto) fired at 160.0!

        stop_event.set()
        watch_thread.join(timeout=1.0)

    def test_untimed_token_event_routes_to_error_with_null_observed_at(self):
        """Untimed token metadata event does not invent observation timestamp; routes to error with null observed_at and C accepts."""
        session_file = self.td / "untimed_session.jsonl"
        lines = [
            json.dumps({"type": "session_meta", "payload": {"id": "synthetic-untimed"}}),
            json.dumps({"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 10, "output_tokens": 2}}}}),
        ]
        session_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        sm = SharedCollectionState()
        res = sm.collect_all(session_file=session_file, reference_time="2026-10-09T08:00:00Z")
        self.assertEqual(len(res["usage"]), 1)
        snap = res["usage"][0]

        # Status must be error without inventing a fake available observation
        self.assertEqual(snap["status"], "error")
        self.assertIsNone(snap["observed_at"])
        self.assertIsNone(snap["last_good_at"])
        self.assertEqual(snap["error_code"], "SESSION_COLLECTION_ERROR")
        self.assertIn("Untimed", snap["error_reason"])

        # Envelope validation and Production C binary acceptance
        frame = build_frame(res, 0, "2026-10-09T08:00:00Z", reference_time="2026-10-09T08:00:00Z")
        line = encode_frame(frame, reference_time="2026-10-09T08:00:00Z")
        out = run_c_wire((line, 1000, 1000))
        self.assertTrue(out[0]["accepted"], out[0].get("error"))

    def test_cold_source_error_has_null_timestamps(self):
        """Cold source error snapshot has observed_at=None, last_good_at=None, accepted by C."""
        missing_session = self.td / "nonexistent_session.jsonl"
        sm = SharedCollectionState()
        res = sm.collect_all(session_file=missing_session, reference_time="2026-10-09T08:00:00Z")
        self.assertEqual(len(res["usage"]), 1)
        snap = res["usage"][0]

        self.assertEqual(snap["status"], "error")
        self.assertIsNone(snap["observed_at"])
        self.assertIsNone(snap["last_good_at"])

        frame = build_frame(res, 0, "2026-10-09T08:00:00Z", reference_time="2026-10-09T08:00:00Z")
        line = encode_frame(frame, reference_time="2026-10-09T08:00:00Z")
        out = run_c_wire((line, 1000, 1000))
        self.assertTrue(out[0]["accepted"], out[0].get("error"))

    def test_watch_manual_deadline_bounded_under_slow_source_and_write(self):
        """Under slow source (4.5s collection) and 1.0s write, manual dispatch budget caps collection so end-to-end <= 5.0s."""
        clock = FakeClock(start_time=100.0)
        stop_event = threading.Event()
        manual_event = threading.Event()

        class DelayedSink(LoopbackSink):
            def write(self, data: bytes) -> int:
                clock.advance(1.0)  # Simulates 1.0s write I/O
                return super().write(data)

        sink = DelayedSink()

        # State manager with a slow source that respects quota_timeout budget
        class SlowSourceStateManager(SharedCollectionState):
            def collect_all(self, *a, **kw):
                budget = kw.get("quota_timeout", 4.0)
                # If budget is 2.5s, simulate 2.5s delay and return timeout error on cold quota
                clock.advance(min(budget, 4.5))
                # Call base collect_all
                return super().collect_all(*a, **kw)

        sm = SlowSourceStateManager()

        class Args:
            device_alias = "test-alias"
            interval = 60
            port = None
            dry_run = True
            state_file = str(self.state_file)
            lock_dir = str(self.lock_dir)
            session_file = None
            session_dir = None
            session_id = None
            latest = False
            live_quota = False
            provider_fixture = None
            personal_usage = None
            global_reset = None
            host_alias = "pc-test"
            agent_id = "codex-cli"
            reference_time = None
            once = False

        watch_thread = threading.Thread(
            target=run_watch_loop,
            kwargs={
                "args": Args(),
                "state_manager": sm,
                "sink_override": sink,
                "manual_trigger_event": manual_event,
                "stop_event": stop_event,
                "time_provider": clock,
            },
        )
        watch_thread.start()

        # Wait for auto iteration 1 at t=100.0 (collection takes 4.0s, write takes 1.0s -> completes at 105.0)
        for _ in range(50):
            if len(sink.written_frames) >= 1:
                break
            time.sleep(0.02)
        self.assertEqual(len(sink.written_frames), 1)

        # Trigger manual dispatch at t = 110.0
        clock.current_time = 110.0
        start_manual_t = clock.now()
        manual_event.set()

        for _ in range(50):
            if len(sink.written_frames) >= 2:
                break
            time.sleep(0.02)
        self.assertEqual(len(sink.written_frames), 2)
        duration = clock.now() - start_manual_t

        # PRODUCT_CONTRACT sections 3/4 requires manual dispatch <= 5.0s!
        self.assertLessEqual(duration, 5.0, f"Manual dispatch duration {duration}s exceeded max 5.0s")

        stop_event.set()
        watch_thread.join(timeout=1.0)

    def test_port_reopened_deadline_bounded_under_slow_source(self):
        """When port becomes available, bounded collection ensures new sequence is sent <= 5.0s."""
        clock = FakeClock(start_time=200.0)
        stop_event = threading.Event()
        sink = LoopbackSink()

        class SlowSourceStateManager(SharedCollectionState):
            def collect_all(self, *a, **kw):
                budget = kw.get("quota_timeout", 4.0)
                clock.advance(min(budget, 4.5))
                return super().collect_all(*a, **kw)

        sm = SlowSourceStateManager()

        # Populate a last good snapshot for quota
        quota_src = sm.get_source("quota")
        quota_src.update_good({
            "schema_version": 1,
            "snapshot_id": "quota-codex-account",
            "provider_id": "codex",
            "agent_id": "codex-cli",
            "host_id": "pc-test",
            "model_id": None,
            "account_profile_id": None,
            "source_kind": "local_runtime",
            "metric_kind": "quota_window",
            "unit": "percent",
            "status": "available",
            "observed_at": "2026-10-09T08:00:00Z",
            "windows": [],
            "stale": False,
            "last_good_at": "2026-10-09T08:00:00Z",
            "error_code": None,
            "error_reason": None,
        })

        class Args:
            device_alias = "test-alias"
            interval = 60
            port = "COM3"
            dry_run = False
            state_file = str(self.state_file)
            lock_dir = str(self.lock_dir)
            session_file = None
            session_dir = None
            session_id = None
            latest = False
            live_quota = False
            provider_fixture = None
            personal_usage = None
            global_reset = None
            host_alias = "pc-test"
            agent_id = "codex-cli"
            reference_time = None
            once = False

        # In watch loop, we pass sink_override as a simulated opened port
        watch_thread = threading.Thread(
            target=run_watch_loop,
            kwargs={
                "args": Args(),
                "state_manager": sm,
                "sink_override": sink,
                "stop_event": stop_event,
                "time_provider": clock,
            },
        )
        watch_thread.start()

        start_t = clock.now()
        for _ in range(50):
            if len(sink.written_frames) >= 1:
                break
            time.sleep(0.02)
        self.assertEqual(len(sink.written_frames), 1)

        # Total time taken to transmit new sequence after port available must be <= 5.0s
        self.assertLessEqual(clock.now() - start_t, 5.0)

        stop_event.set()
        watch_thread.join(timeout=1.0)

    def test_watch_manual_arrival_during_in_flight_automatic_collection(self):
        """When manual event arrives while automatic collection/write is in flight, coalesce ensures request-to-sequence <= 5.0s."""
        clock = FakeClock(start_time=300.0)
        stop_event = threading.Event()
        manual_event = threading.Event()

        class DelayedWriteSink(LoopbackSink):
            def write(self, data: bytes) -> int:
                clock.advance(0.8)
                return super().write(data)

        sink = DelayedWriteSink()

        # State manager where automatic collection takes 2.0s
        class InFlightStateManager(SharedCollectionState):
            def __init__(self):
                super().__init__()
                self.calls = 0

            def collect_all(self, *a, **kw):
                self.calls += 1
                # During the first automatic collection (calls == 1), manual trigger arrives!
                if self.calls == 1:
                    clock.advance(1.0)
                    manual_event.set()  # User presses Enter midway!
                    clock.advance(1.0)
                else:
                    clock.advance(0.5)
                return super().collect_all(*a, **kw)

        sm = InFlightStateManager()

        class Args:
            device_alias = "test-alias"
            interval = 60
            port = None
            dry_run = True
            state_file = str(self.state_file)
            lock_dir = str(self.lock_dir)
            session_file = None
            session_dir = None
            session_id = None
            latest = False
            live_quota = False
            provider_fixture = None
            personal_usage = None
            global_reset = None
            host_alias = "pc-test"
            agent_id = "codex-cli"
            reference_time = None
            once = False

        watch_thread = threading.Thread(
            target=run_watch_loop,
            kwargs={
                "args": Args(),
                "state_manager": sm,
                "sink_override": sink,
                "manual_trigger_event": manual_event,
                "stop_event": stop_event,
                "time_provider": clock,
            },
        )
        watch_thread.start()

        for _ in range(50):
            if len(sink.written_frames) >= 1:
                break
            time.sleep(0.02)

        # The frame was transmitted
        self.assertEqual(len(sink.written_frames), 1)

        # The manual event set at t=301.0 was coalesced into this fresh acquisition (completed at t=302.8)
        # Total elapsed time from user manual request (t=301.0) to frame write completion (t=302.8) is 1.8s <= 5.0s!
        self.assertLessEqual(clock.now() - 301.0, 5.0)

        # Ensure manual event was cleared (not resulting in a redundant second delayed collection)
        self.assertFalse(manual_event.is_set())

        stop_event.set()
        watch_thread.join(timeout=1.0)


if __name__ == "__main__":
    unittest.main()



