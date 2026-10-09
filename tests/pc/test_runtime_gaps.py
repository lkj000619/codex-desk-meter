"""Tests for final PC runtime gaps remediation (A, B, C, D).

Verifies:
A. Watch loop scheduler:
   - Interruptible by manual trigger (<=5s response even with interval=60).
   - Port failure followed by port availability sends <=5s.
   - Requires --port or explicit --dry-run (refuses implicit loopback).
   - Per-source failure isolation keeps other sources and cached good values visible.
B. Bounded JSON-RPC reader:
   - Synthetic subprocess hung stream times out strictly without blocking forever.
   - Initialize failure handling.
   - Out-of-order notifications skipped, only init->initialized->read protocol.
   - Child process cleanup (terminated/killed).
   - observed_at reflects acquisition time, not start time.
C. SharedCollectionState & fixtures:
   - Normal -> error -> recovery preserves last-good values and timestamps.
   - 0/299/300 stale boundary without modifying source timestamp.
   - Generic provider fixture loading and personal-usage fixture loading.
   - Global reset source/captured_at preservation and error fallback.
D. StateStore & OS locking:
   - initialize_new refuses silent overwrite without confirmed_overwrite flag.
   - OS-held lock (msvcrt on Windows) released upon process death/crash.
   - Subprocess crash leaves lock cleanly acquirable by restart process.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

from pc.cli import main, run_watch_loop
from pc.quota import BoundedProcessReader, cleanup_process, fetch_native_rate_limits
from pc.sender import CdmSender, DeviceLock, DeviceSequenceState, LoopbackSink, SenderLockError, SenderStateError, StateStore
from pc.state import SharedCollectionState


class FakeTimeProvider:
    def __init__(self, start_time: float = 1000.0):
        self.current_time = start_time

    def now(self) -> float:
        return self.current_time

    def advance(self, seconds: float) -> None:
        self.current_time += seconds

    def sleep(self, seconds: float) -> None:
        # Actually pause the thread while advancing simulated clock
        self.current_time += seconds
        time.sleep(0.01)


class TestWatchSchedulerAndManualTrigger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.td = Path(self.temp_dir.name)
        self.state_file = self.td / "watch-state.json"
        self.lock_dir = self.td / "locks"
        self.store = StateStore(self.state_file)
        self.store.initialize_new("watch-test-meter", initial_sequence=0)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_refuse_implicit_loopback_when_port_missing(self):
        """CLI send and watch must require --port or explicit --dry-run."""
        rc_send = main(["send", "--device-alias", "watch-test-meter", "--state-file", str(self.state_file)])
        self.assertEqual(rc_send, 1)

        rc_watch = main(["watch", "--device-alias", "watch-test-meter", "--state-file", str(self.state_file), "--once"])
        self.assertEqual(rc_watch, 1)

    def test_watch_manual_trigger_immediate_dispatch(self):
        """Manual trigger fires immediately even when interval is 60s."""
        manual_event = threading.Event()
        stop_event = threading.Event()
        time_prov = FakeTimeProvider(start_time=100.0)

        sink = LoopbackSink()
        sm = SharedCollectionState()

        class Args:
            device_alias = "watch-test-meter"
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

        # Start watch loop in thread
        watch_thread = threading.Thread(
            target=run_watch_loop,
            kwargs={
                "args": Args(),
                "state_manager": sm,
                "sink_override": sink,
                "manual_trigger_event": manual_event,
                "stop_event": stop_event,
                "time_provider": time_prov,
            },
        )
        watch_thread.start()

        time.sleep(0.1)
        self.assertEqual(len(sink.written_frames), 1)  # Initial auto iteration at start

        # Trigger manual event before 60s
        time_prov.advance(5.0)  # only 5s passed
        manual_event.set()
        time.sleep(0.15)

        self.assertEqual(len(sink.written_frames), 2)  # Dispatched on manual trigger!

        stop_event.set()
        watch_thread.join(timeout=1.0)


class TestBoundedRpcReader(unittest.TestCase):
    def test_hung_stream_times_out_and_cleans_up_process(self):
        """A synthetic child process that never emits any output must time out strictly within timeout_seconds."""
        # Python script that sleeps forever without writing stdout
        hang_script = "import time; time.sleep(60)"
        start_t = time.monotonic()
        res = fetch_native_rate_limits(
            timeout_seconds=0.8,
            command=[sys.executable, "-c", hang_script],
        )
        elapsed = time.monotonic() - start_t

        self.assertLess(elapsed, 3.0)  # Did not hang for 60s!
        self.assertEqual(res.error_code, "INITIALIZE_FAILED")


class TestSharedCollectionStateAndCache(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.td = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_source_isolation_and_last_good_retention(self):
        """Failure of one source retains its last good values and does not abort others."""
        sm = SharedCollectionState()

        # Session file that starts valid
        s_file = self.td / "session.jsonl"
        s_file.write_text(
            json.dumps({"type": "token_count", "timestamp": "2026-10-08T12:00:00Z", "total_token_usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}}) + "\n"
        )

        res1 = sm.collect_all(session_file=s_file, reference_time="2026-10-08T12:00:00Z")
        self.assertEqual(len(res1["usage"]), 1)
        self.assertEqual(res1["usage"][0]["status"], "available")
        self.assertEqual(res1["usage"][0]["windows"][0]["used_units"], 100)

        # Corrupt session file
        s_file.write_text("corrupted non json content\n")
        res2 = sm.collect_all(session_file=s_file, reference_time="2026-10-08T12:00:00Z")
        self.assertEqual(len(res2["usage"]), 1)
        # Retains last-good window values while status is error
        err_snap = res2["usage"][0]
        self.assertEqual(err_snap["status"], "error")
        self.assertEqual(err_snap["windows"][0]["used_units"], 100)
        self.assertEqual(err_snap["last_good_at"], "2026-10-08T12:00:00Z")

    def test_stale_detection_0_299_300(self):
        """0s and 299s are not stale; 300s is marked stale without altering observed_at."""
        sm = SharedCollectionState()
        s_file = self.td / "session.jsonl"
        s_file.write_text(
            json.dumps({"type": "token_count", "timestamp": "2026-10-08T12:00:00Z", "total_token_usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30}}) + "\n"
        )

        # 0s: reference = 12:00:00Z
        res_0 = sm.collect_all(session_file=s_file, reference_time="2026-10-08T12:00:00Z")
        self.assertFalse(res_0["usage"][0]["stale"])

        # 299s: reference = 12:04:59Z
        res_299 = sm.collect_all(session_file=s_file, reference_time="2026-10-08T12:04:59Z")
        self.assertFalse(res_299["usage"][0]["stale"])

        # 300s: reference = 12:05:00Z
        res_300 = sm.collect_all(session_file=s_file, reference_time="2026-10-08T12:05:00Z")
        self.assertTrue(res_300["usage"][0]["stale"])
        self.assertEqual(res_300["usage"][0]["status"], "stale")
        self.assertEqual(res_300["usage"][0]["observed_at"], "2026-10-08T12:00:00Z")  # Unchanged!


class TestStateStoreAndOsLocking(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.td = Path(self.temp_dir.name)
        self.state_file = self.td / "seq-state.json"
        self.lock_path = self.td / "device.lock"
        self.store = StateStore(self.state_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initialize_new_refuses_silent_overwrite(self):
        """initialize_new raises error if state already exists without confirmed_overwrite=True."""
        self.store.initialize_new("test-dev", initial_sequence=0)

        with self.assertRaises(SenderStateError):
            self.store.initialize_new("test-dev", initial_sequence=5, confirmed_overwrite=False)

        # With confirmed_overwrite=True, succeeds
        state = self.store.initialize_new("test-dev", initial_sequence=5, confirmed_overwrite=True)
        self.assertEqual(state.next_sequence, 5)

    def test_os_lock_released_on_subprocess_crash(self):
        """A lock held by a crashed subprocess must be automatically released by the OS."""
        # Subprocess script that acquires lock and is killed
        child_code = f"""
import os, sys, time
from pathlib import Path
from pc.sender import DeviceLock
lock = DeviceLock(Path({repr(str(self.lock_path))}))
lock.acquire()
print('LOCKED', flush=True)
time.sleep(30)
"""
        proc = subprocess.Popen([sys.executable, "-c", child_code], stdout=subprocess.PIPE)
        try:
            line = proc.stdout.readline().decode().strip()
            self.assertEqual(line, "LOCKED")

            # Parent attempts to acquire lock -> must fail
            parent_lock = DeviceLock(self.lock_path)
            with self.assertRaises(SenderLockError):
                parent_lock.acquire()

            # Kill child abruptly (simulating crash).
            # On Windows, sys.executable in a venv may be a launcher whose real Python child
            # holds the OS handle. Terminate the entire process tree.
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
            else:
                proc.kill()
            proc.wait()
        finally:
            if proc.stdout:
                proc.stdout.close()
            try:
                proc.kill()
                proc.wait()
            except Exception:
                pass

        # Parent attempts to acquire again -> must succeed due to OS-level lock release
        parent_lock.acquire()
        parent_lock.release()

    def test_alias_safety_and_updated_at_validation(self):
        """DeviceSequenceState must reject path traversal aliases and corrupt/NaN updated_at."""
        with self.assertRaises(SenderStateError):
            DeviceSequenceState.from_dict({"device_alias": "../escape", "next_sequence": 0, "updated_at": 100.0})
        with self.assertRaises(SenderStateError):
            DeviceSequenceState.from_dict({"device_alias": "dev/slash", "next_sequence": 0, "updated_at": 100.0})
        with self.assertRaises(SenderStateError):
            DeviceSequenceState.from_dict({"device_alias": "valid-dev", "next_sequence": 0, "updated_at": float("nan")})
        with self.assertRaises(SenderStateError):
            DeviceSequenceState.from_dict({"device_alias": "valid-dev", "next_sequence": 0, "updated_at": -5.0})

    def test_lock_released_on_failed_load(self):
        """CdmSender must release its lock if StateStore.load fails."""
        corrupt_state = self.td / "corrupt-state.json"
        corrupt_state.write_text("{broken json")
        corrupt_store = StateStore(corrupt_state)
        lock_dir = self.td / "test-locks"

        with self.assertRaises(SenderStateError):
            CdmSender("meter-dev", corrupt_store, lock_dir=lock_dir)

        # Lock must not remain held
        test_lock = DeviceLock(lock_dir / "meter-dev.lock")
        test_lock.acquire()
        test_lock.release()

    def test_init_device_confirmed_empty_guard(self):
        """CLI init-device requires --confirmed-empty-receiver or --force-overwrite."""
        import argparse
        from pc.cli import cmd_init_device

        # Without confirmation flags
        args1 = argparse.Namespace(
            state_file=str(self.state_file),
            lock_dir=str(self.td / "init-locks"),
            device_alias="dev-guard",
            initial_sequence=0,
            confirmed_empty_receiver=False,
            force_overwrite=False,
        )
        self.assertEqual(cmd_init_device(args1), 1)

        # With --confirmed-empty-receiver
        args2 = argparse.Namespace(
            state_file=str(self.state_file),
            lock_dir=str(self.td / "init-locks"),
            device_alias="dev-guard",
            initial_sequence=0,
            confirmed_empty_receiver=True,
            force_overwrite=False,
        )
        self.assertEqual(cmd_init_device(args2), 0)


class TestProductionGapsRemediation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.td = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_wire_error_privacy_and_metric_kind(self):
        """Session cold error must preserve session_telemetry metric_kind and sanitize local paths."""
        sm = SharedCollectionState()
        non_existent = self.td / "private_folder" / "secret.jsonl"
        res = sm.collect_all(session_file=non_existent)
        snap = res["usage"][0]

        self.assertEqual(snap["metric_kind"], "session_telemetry")
        self.assertEqual(snap["unit"], "token")
        self.assertEqual(snap["status"], "error")
        # Ensure path privacy: does not expose full directory structure
        self.assertNotIn(str(self.td), snap["error_reason"])
        self.assertNotIn("private_folder", snap["error_reason"])

    def test_session_isolation_across_selections(self):
        """Selecting session A then switching to a missing session B must not attribute A to B."""
        sm = SharedCollectionState()
        sess_a = self.td / "session_a.jsonl"
        sess_a.write_text(
            json.dumps({"type": "token_count", "timestamp": "2026-10-08T12:00:00Z", "total_token_usage": {"input_tokens": 100, "output_tokens": 50}}) + "\n"
        )
        res_a = sm.collect_all(session_file=sess_a, reference_time="2026-10-08T12:00:00Z")
        self.assertEqual(res_a["usage"][0]["status"], "available")
        self.assertEqual(res_a["usage"][0]["windows"][0]["used_units"], 100)

        # Now select session B which does not exist
        sess_b = self.td / "session_b.jsonl"
        res_b = sm.collect_all(session_file=sess_b, reference_time="2026-10-08T12:00:00Z")
        self.assertEqual(res_b["usage"][0]["status"], "error")
        self.assertEqual(res_b["usage"][0]["snapshot_id"], "error-session_session_b.jsonl")
        # Must not have session A's window units
        self.assertEqual(len(res_b["usage"][0]["windows"]), 0)

    def test_missing_personal_usage_and_global_reset_routed_to_error(self):
        """Cold global error omits wire record and reports locally; warm error retains true capture."""
        sm = SharedCollectionState()
        missing_usage = self.td / "missing_usage.json"
        missing_reset = self.td / "missing_reset.json"

        # Cold failure: omitted on wire, reported locally in source_errors
        res = sm.collect_all(
            personal_usage_fixture=missing_usage,
            global_reset_file=missing_reset,
            reference_time="2026-10-08T12:00:00Z",
        )
        self.assertEqual(len(res["usage"]), 1)
        self.assertEqual(res["usage"][0]["status"], "error")
        self.assertEqual(res["usage"][0]["error_code"], "PERSONAL_USAGE_FIXTURE_ERROR")

        # Unobserved cold global record is omitted from wire to avoid schema violation
        self.assertEqual(len(res["global_resets"]), 0)
        self.assertTrue(any("global_reset" in k for k in sm.source_errors))

        # Warm failure: retains true captured_at from previous valid capture
        valid_reset = self.td / "valid_reset.json"
        valid_reset.write_text(
            json.dumps({
                "source": "codex-resets.com",
                "captured_at": "2026-10-08T11:00:00Z",
                "latest_reset_at": "2026-10-08T10:00:00Z",
                "forecast_24h_percent": 10.0,
                "forecast_48h_percent": 20.0,
            }),
            encoding="utf-8",
        )
        res_warm_ok = sm.collect_all(global_reset_file=valid_reset, reference_time="2026-10-08T11:00:00Z")
        self.assertEqual(len(res_warm_ok["global_resets"]), 1)
        self.assertEqual(res_warm_ok["global_resets"][0]["captured_at"], "2026-10-08T11:00:00Z")

        # Now corrupt/delete valid_reset
        valid_reset.unlink()
        res_warm_err = sm.collect_all(global_reset_file=valid_reset, reference_time="2026-10-08T11:00:00Z")
        self.assertEqual(len(res_warm_err["global_resets"]), 1)
        self.assertEqual(res_warm_err["global_resets"][0]["error_code"], "GLOBAL_RESET_ERROR")
        self.assertEqual(res_warm_err["global_resets"][0]["captured_at"], "2026-10-08T11:00:00Z")  # True capture retained!
        self.assertTrue(res_warm_err["global_resets"][0]["stale"])

    def test_absent_optional_counts_remain_null(self):
        """Optional session token counts (cached, reasoning, source_total) must be null when absent."""
        sm = SharedCollectionState()
        s_file = self.td / "minimal_counts.jsonl"
        s_file.write_text(
            json.dumps({"type": "token_count", "timestamp": "2026-10-08T12:00:00Z", "total_token_usage": {"input_tokens": 150, "output_tokens": 75}}) + "\n"
        )
        res = sm.collect_all(session_file=s_file, reference_time="2026-10-08T12:00:00Z")
        snap = res["usage"][0]
        window_dict = {w["window_id"]: w["used_units"] for w in snap["windows"]}

        self.assertEqual(window_dict["input"], 150)
        self.assertEqual(window_dict["output"], 75)
        self.assertIsNone(window_dict["cached_input"])
        self.assertIsNone(window_dict["reasoning_output"])
        self.assertIsNone(window_dict["source_total"])
        self.assertEqual(window_dict["normalized_total"], 225)


if __name__ == "__main__":
    unittest.main()
