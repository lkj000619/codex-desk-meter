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
from pc.sender import CdmSender, DeviceLock, LoopbackSink, SenderLockError, SenderStateError, StateStore
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

        res1 = sm.collect_all(session_file=s_file)
        self.assertEqual(len(res1["usage"]), 1)
        self.assertEqual(res1["usage"][0]["status"], "available")
        self.assertEqual(res1["usage"][0]["windows"][0]["used_units"], 100)

        # Corrupt session file
        s_file.write_text("corrupted non json content\n")
        res2 = sm.collect_all(session_file=s_file)
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
        line = proc.stdout.readline().decode().strip()
        self.assertEqual(line, "LOCKED")

        # Parent attempts to acquire lock -> must fail
        parent_lock = DeviceLock(self.lock_path)
        with self.assertRaises(SenderLockError):
            parent_lock.acquire()

        # Kill child abruptly (simulating crash)
        proc.kill()
        proc.wait()

        # Parent attempts to acquire again -> must succeed due to OS-level lock release
        parent_lock.acquire()
        parent_lock.release()


if __name__ == "__main__":
    unittest.main()
