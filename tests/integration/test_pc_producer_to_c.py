"""Synthetic production PC -> canonical cdm/1 -> production C integration checks.

All session, quota, RPC, and serial inputs are synthetic. The C boundary is the
same host-linked cdm receiver used by tests/firmware.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from pc.frame import build_frame, encode_frame
from pc.normalizer import build_account_quota_snapshot
from pc.quota import fetch_native_rate_limits, parse_app_server_rate_limits
from pc.sender import CdmSender, StateStore
from pc.state import SharedCollectionState
from pc import cli


ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / "tests" / "firmware" / ".build" / "cdm-host.exe"
STAMP = "2026-10-09T12:00:00Z"
MISSING = object()


def c_receive(lines: list[bytes], mono_ms: list[int] | None = None) -> list[dict]:
    mono_ms = mono_ms or [(i + 1) * 1000 for i in range(len(lines))]
    request = {"events": [
        {"line_hex": line.hex(), "mono_ms": mono, "now_ms": mono}
        for line, mono in zip(lines, mono_ms, strict=True)
    ]}
    result = subprocess.run(
        [str(HOST), "--wire"], input=json.dumps(request), text=True,
        capture_output=True, cwd=ROOT, check=True,
    )
    return json.loads(result.stdout)


def token_line(session_id: str, observed_at: str, **counts: object) -> str:
    info = {"input_tokens": 120, "output_tokens": 30, "total_tokens": 999,
            "cached_input_tokens": 40, "reasoning_output_tokens": 8}
    info.update(counts)
    for key, value in tuple(info.items()):
        if value is MISSING:
            del info[key]
    return json.dumps({"type": "event_msg", "timestamp": "2026-10-09T12:01:00Z",
                       "payload": {"type": "token_count", "timestamp": observed_at,
                                   "info": {"total_token_usage": info}}})


def write_session(path: Path, session_id: str, observed_at: str, **counts: object) -> None:
    path.write_text("\n".join([
        json.dumps({"type": "session_meta", "payload": {"id": session_id}}),
        token_line(session_id, observed_at, **counts),
        json.dumps({"type": "event_msg", "timestamp": "2026-10-09T12:02:00Z",
                    "payload": {"type": "user_message", "message": "synthetic unrelated event"}}),
    ]) + "\n", encoding="utf-8")


def quota_snapshot(snapshot_id: str, provider: str, account: str, pct: float) -> dict:
    return {
        "schema_version": 1, "snapshot_id": snapshot_id, "provider_id": provider,
        "agent_id": "synthetic-cli", "host_id": "synthetic-host", "model_id": None,
        "account_profile_id": account, "source_kind": "fixture", "metric_kind": "quota_window",
        "unit": "percent", "status": "available", "observed_at": STAMP,
        "windows": [{"window_id": "primary-18000s", "label": "5h limit",
                     "used_units": None, "remaining_units": None, "limit_units": None,
                     "unit": "percent", "percent_used": pct,
                     "percent_remaining": 100.0 - pct, "resets_at": None,
                     "reset_status": "unknown"}],
        "stale": False, "last_good_at": STAMP, "error_code": None, "error_reason": None,
    }


def serial_module(serial_class) -> types.ModuleType:
    module = types.ModuleType("serial")
    module.EIGHTBITS = 8
    module.PARITY_NONE = "N"
    module.STOPBITS_ONE = 1
    module.SerialTimeoutException = TimeoutError
    module.Serial = serial_class
    return module


class _RecordingInput:
    def __init__(self):
        self.lines: list[bytes] = []
        self.closed = False

    def write(self, data: bytes) -> int:
        self.lines.append(data)
        return len(data)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        self.closed = True


class _FakeProcess:
    def __init__(self, stdout, stderr=None):
        self.stdin = _RecordingInput()
        self.stdout = stdout
        self.stderr = stderr or io.BytesIO()
        self.terminated = False
        self.killed = False
        self.waited = False

    def poll(self):
        return None

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        self.waited = True
        return 0


class _GateClock:
    def __init__(self, start: float = 100.0):
        self.value = start
        self.lock = threading.Lock()

    def now(self) -> float:
        with self.lock:
            return self.value

    def advance(self, seconds: float) -> None:
        with self.lock:
            self.value += seconds

    def sleep(self, seconds: float) -> None:
        time.sleep(0.005)


class PCProducerToCTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not HOST.is_file():
            raise RuntimeError("Run tests/firmware/build-host.ps1 first")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_native_nested_token_event_and_invalid_counts_reach_c_as_valid_error_frames(self):
        session_file = self.root / "native-session.jsonl"
        write_session(session_file, "synthetic-session-42", STAMP,
                      input_tokens=120, output_tokens=30, total_tokens=999,
                      cached_input_tokens=40, reasoning_output_tokens=8)
        state = SharedCollectionState()
        payload = state.collect_all(session_file=session_file, reference_time=STAMP)
        snap = payload["usage"][0]
        self.assertEqual(snap["snapshot_id"], "session-synthetic-session-42")
        self.assertEqual(snap["observed_at"], STAMP)
        values = {w["window_id"]: w["used_units"] for w in snap["windows"]}
        self.assertEqual(values, {"input": 120, "output": 30, "cached_input": 40,
                                  "reasoning_output": 8, "source_total": 999,
                                  "normalized_total": 150})
        raw = encode_frame(build_frame(payload, 1, STAMP, reference_time=STAMP), reference_time=STAMP)
        received = c_receive([raw])[0]
        self.assertTrue(received["accepted"], received.get("error"))
        current = received["usage"][0]["current"]
        self.assertEqual(current["observed_at"], STAMP)
        self.assertEqual({w["window_id"]: w["used_units"] for w in current["windows"]}, values)

        untokened_file = self.root / "untokened-session.jsonl"
        untokened_file.write_text(json.dumps({"type": "session_meta", "payload": {"id": "no-token"}})
                                  + "\n" + json.dumps({"type": "event_msg", "payload": {"type": "user_message"}})
                                  + "\n", encoding="utf-8")
        untokened = SharedCollectionState().collect_all(session_file=untokened_file,
                                                        reference_time=STAMP)["usage"][0]
        self.assertEqual(untokened["status"], "error")
        self.assertIsNone(untokened["observed_at"])
        untokened_raw = encode_frame(build_frame({"usage": [untokened], "global_resets": []}, 90,
                                                STAMP, reference_time=STAMP),
                                     reference_time=STAMP)
        self.assertTrue(c_receive([untokened_raw])[0]["accepted"])

        invalid_counts = [
            {"input_tokens": True}, {"input_tokens": -1}, {"input_tokens": 1.5},
            {"output_tokens": False}, {"cached_input_tokens": 121},
            {"reasoning_output_tokens": 31}, {"total_tokens": -1},
            {"input_tokens": None}, {"input_tokens": MISSING},
        ]
        for index, invalid in enumerate(invalid_counts, start=2):
            with self.subTest(invalid=invalid):
                bad_file = self.root / f"invalid-{index}.jsonl"
                write_session(bad_file, f"invalid-{index}", STAMP, **invalid)
                bad_payload = SharedCollectionState().collect_all(session_file=bad_file,
                                                                  reference_time=STAMP)
                bad = bad_payload["usage"][0]
                self.assertEqual(bad["status"], "error")
                self.assertIsNone(bad["observed_at"])
                bad_raw = encode_frame(build_frame(bad_payload, index, STAMP,
                                                   reference_time=STAMP),
                                       reference_time=STAMP)
                wire = c_receive([bad_raw])[0]
                self.assertTrue(wire["accepted"], wire.get("error"))
                self.assertEqual(wire["usage"][0]["current"]["status"], "error")

    def test_explicit_session_selection_source_timestamp_and_0_299_300_stale(self):
        directory = self.root / "sessions"
        directory.mkdir()
        stamp_dt = datetime.fromisoformat(STAMP.replace("Z", "+00:00"))
        a = directory / "a.jsonl"
        b = directory / "b.jsonl"
        write_session(a, "synthetic-A", STAMP)
        write_session(b, "synthetic-B", (stamp_dt - timedelta(seconds=10)).isoformat().replace("+00:00", "Z"))
        selected = SharedCollectionState().collect_all(session_dir=directory,
                                                       session_id="synthetic-B", reference_time=STAMP)
        self.assertEqual([s["snapshot_id"] for s in selected["usage"]], ["session-synthetic-B"])
        latest = SharedCollectionState().collect_all(session_dir=directory, use_latest=True,
                                                     reference_time=STAMP)
        self.assertEqual(latest["usage"][0]["snapshot_id"], "session-synthetic-A")

        lines = []
        for sequence, age in enumerate((0, 299, 300), start=10):
            observed = (stamp_dt - timedelta(seconds=age)).isoformat().replace("+00:00", "Z")
            write_session(b, f"stale-{age}", observed)
            payload = SharedCollectionState().collect_all(session_file=b, reference_time=STAMP)
            snap = payload["usage"][0]
            self.assertEqual(snap["observed_at"], observed)
            self.assertEqual(snap["stale"], age == 300)
            raw = encode_frame(build_frame(payload, sequence, STAMP, reference_time=STAMP),
                               reference_time=STAMP)
            lines.append(raw)
        output = c_receive(lines)
        self.assertTrue(all(row["accepted"] for row in output))
        self.assertEqual([row["usage"][0]["source_age_s"] for row in output], [0, 299, 300])
        self.assertEqual([row["receive_age_s"] for row in output], [0, 0, 0])
        self.assertEqual([row["usage"][0]["current"]["observed_at"] for row in output],
                         [STAMP, (stamp_dt - timedelta(seconds=299)).isoformat().replace("+00:00", "Z"),
                          (stamp_dt - timedelta(seconds=300)).isoformat().replace("+00:00", "Z")])
        self.assertEqual([row["usage"][0]["stale"] for row in output], [False, False, True])

    def test_account_quota_windows_scope_and_session_coexistence(self):
        response = {"result": {"accountId": "synthetic-account", "rateLimits": {
            "planType": "synthetic-plan",
            "primary": {"windowDurationMins": 300, "usedPercent": 40, "resetsAt": 1791547800},
            "secondary": {"windowDurationMins": 10080, "usedPercent": 70},
        }, "rateLimitsByLimitId": {
            "codex": {"primary": {"windowDurationMins": 300, "usedPercent": 41}},
            "review": {"primary": {"windowDurationMins": 20, "usedPercent": 12},
                       "secondary": {"usedPercent": 3}},
        }}}
        result = parse_app_server_rate_limits(response, STAMP, reference_time=STAMP)
        self.assertEqual(set(result.windows), {"primary", "secondary", "review_primary", "review_secondary"})
        self.assertIsNone(result.windows["review_secondary"].duration_seconds)
        quota = build_account_quota_snapshot(result)
        self.assertEqual(quota["account_profile_id"], "synthetic-account")
        self.assertEqual({w["window_id"] for w in quota["windows"]},
                         {"primary-18000s", "secondary-604800s", "review_primary-1200s",
                          "review_secondary-unknown"})

        session_file = self.root / "session.jsonl"
        write_session(session_file, "synthetic-session", STAMP)
        with patch("pc.state.fetch_native_rate_limits", return_value=result):
            payload = SharedCollectionState().collect_all(session_file=session_file, live_quota=True,
                                                          reference_time=STAMP)
        self.assertEqual({s["metric_kind"] for s in payload["usage"]},
                         {"session_telemetry", "quota_window"})
        session = next(s for s in payload["usage"] if s["metric_kind"] == "session_telemetry")
        account = next(s for s in payload["usage"] if s["metric_kind"] == "quota_window")
        self.assertIsNone(session["account_profile_id"])
        self.assertEqual(account["account_profile_id"], "synthetic-account")
        self.assertTrue(all(w["limit_units"] is None for w in session["windows"]))
        raw = encode_frame(build_frame(payload, 21, STAMP, reference_time=STAMP),
                           reference_time=STAMP)
        received = c_receive([raw])[0]
        self.assertTrue(received["accepted"], received.get("error"))
        self.assertEqual(len(received["usage"]), 2)

    def test_provider_recovery_and_global_reset_last_known_reach_c(self):
        fixture = self.root / "providers.json"
        entries = [quota_snapshot("openai-synthetic", "openai", "acct-openai", 20.0),
                   quota_snapshot("other-synthetic", "other-provider", "acct-other", 35.0)]
        fixture.write_text(json.dumps(entries), encoding="utf-8")
        manager = SharedCollectionState()
        good = manager.collect_all(provider_fixtures=[fixture], reference_time=STAMP)
        fixture.unlink()
        failed = manager.collect_all(provider_fixtures=[fixture], reference_time=STAMP)
        fixture.write_text(json.dumps([quota_snapshot("openai-recovered", "openai", "acct-openai", 25.0),
                                       quota_snapshot("other-recovered", "other-provider", "acct-other", 40.0)]),
                           encoding="utf-8")
        recovered = manager.collect_all(provider_fixtures=[fixture], reference_time=STAMP)
        self.assertEqual([s["status"] for s in failed["usage"]], ["error", "error"])
        self.assertEqual([s["windows"][0]["percent_used"] for s in failed["usage"]], [20.0, 35.0])
        self.assertEqual([s["status"] for s in recovered["usage"]], ["available", "available"])
        self.assertEqual([s["windows"][0]["percent_used"] for s in recovered["usage"]], [25.0, 40.0])

        reset = self.root / "reset.json"
        reset.write_text(json.dumps({"source": "synthetic-resets", "captured_at": STAMP,
                                     "latest_reset_at": "2026-10-09T11:00:00Z",
                                     "forecast_24h_percent": 22.0,
                                     "forecast_48h_percent": 47.0}), encoding="utf-8")
        reset_state = SharedCollectionState()
        global_good = reset_state.collect_all(global_reset_file=reset, reference_time=STAMP)
        reset.unlink()
        global_failed = reset_state.collect_all(global_reset_file=reset, reference_time=STAMP)
        self.assertEqual(global_failed["global_resets"][0]["source"], "synthetic-resets")
        self.assertEqual(global_failed["global_resets"][0]["captured_at"], STAMP)
        frames = []
        for sequence, payload in enumerate((good, failed, recovered), start=30):
            frames.append(encode_frame(build_frame(payload, sequence, STAMP, reference_time=STAMP),
                                       reference_time=STAMP))
        frames.extend(encode_frame(build_frame(payload, sequence, STAMP, reference_time=STAMP),
                                   reference_time=STAMP)
                      for sequence, payload in ((33, global_good), (34, global_failed)))
        output = c_receive(frames)
        self.assertTrue(all(row["accepted"] for row in output), [row.get("error") for row in output])
        self.assertEqual(len(output[1]["usage"]), 2)
        self.assertEqual([u["good"]["snapshot_id"] for u in output[1]["usage"]],
                         ["openai-synthetic", "other-synthetic"])
        self.assertEqual([u["current"]["snapshot_id"] for u in output[2]["usage"]],
                         ["openai-recovered", "other-recovered"])
        self.assertEqual(output[4]["global"][0]["good"]["captured_at"], STAMP)
        self.assertEqual(output[4]["global"][0]["good"]["source"], "synthetic-resets")
        self.assertEqual(output[4]["global"][0]["good"]["latest_reset_at"], "2026-10-09T11:00:00Z")

        no_reset = SharedCollectionState().collect_all(reference_time=STAMP)
        no_reset_raw = encode_frame(build_frame(no_reset, 35, STAMP, reference_time=STAMP),
                                    reference_time=STAMP)
        no_reset_result = c_receive([no_reset_raw])[0]
        self.assertTrue(no_reset_result["accepted"], no_reset_result.get("error"))
        self.assertEqual(no_reset_result["global"], [])

    def test_production_pc_float_unicode_canonical_frame_interoperates_with_c(self):
        snapshot = quota_snapshot("unicode-synthetic", "provider-synthetic", "account-synthetic", 37.25)
        snapshot["windows"][0]["label"] = "주간 quota • Café"
        snapshot["windows"][0]["percent_remaining"] = 62.75
        raw = encode_frame(build_frame({"usage": [snapshot], "global_resets": []}, 91, STAMP,
                                       reference_time=STAMP), reference_time=STAMP)
        result = c_receive([raw])[0]
        self.assertTrue(result["accepted"], result.get("error"))
        received = result["usage"][0]["current"]["windows"][0]
        self.assertEqual(received["percent_used"], 37.25)
        self.assertEqual(received["label"], "주간 quota • Café")

    def test_rpc_handshake_order_and_timeout_cleanup_with_fake_streams(self):
        responses = [
            {"jsonrpc": "2.0", "id": 1, "result": {"userAgent": "synthetic"}},
            {"jsonrpc": "2.0", "id": 2, "result": {"accountId": "synthetic-account",
             "rateLimits": {"primary": {"windowDurationMins": 5, "usedPercent": 10}}}},
        ]
        process = _FakeProcess(io.BytesIO("".join(json.dumps(r) + "\n" for r in responses).encode()))
        with patch("pc.quota.subprocess.Popen", return_value=process):
            result = fetch_native_rate_limits(command=["synthetic-app-server"], timeout_seconds=0.4,
                                              reference_time=STAMP)
        requests = [json.loads(line) for line in process.stdin.lines]
        self.assertEqual([r["method"] for r in requests],
                         ["initialize", "initialized", "account/rateLimits/read"])
        self.assertEqual([r.get("id") for r in requests], [1, None, 2])
        self.assertEqual(result.account_id, "synthetic-account")
        self.assertIn("primary", result.windows)
        self.assertTrue(process.terminated)
        self.assertTrue(process.waited)
        self.assertTrue(process.stdin.closed)

        class BlockingOutput:
            def __init__(self):
                self.release = threading.Event()
                self.closed = False

            def readline(self):
                self.release.wait(0.5)
                return b""

            def close(self):
                self.closed = True
                self.release.set()

        blocked_output = BlockingOutput()
        timeout_process = _FakeProcess(blocked_output)
        timeout_process.terminate = lambda: (setattr(timeout_process, "terminated", True),
                                             blocked_output.release.set())
        started = time.monotonic()
        with patch("pc.quota.subprocess.Popen", return_value=timeout_process):
            timed_out = fetch_native_rate_limits(command=["synthetic-app-server"], timeout_seconds=0.1,
                                                 reference_time=STAMP)
        elapsed = time.monotonic() - started
        self.assertEqual(timed_out.error_code, "INITIALIZE_FAILED")
        self.assertLess(elapsed, 1.0)
        self.assertTrue(timeout_process.terminated)
        self.assertTrue(timeout_process.waited)
        self.assertTrue(blocked_output.closed)

    def test_cli_fake_serial_reserves_before_write_wraps_and_fails_closed(self):
        state_path = self.root / "sender.json"
        lock_dir = self.root / "locks"
        store = StateStore(state_path)
        store.initialize_new("synthetic-meter", initial_sequence=0xFFFFFFFF)
        session_file = self.root / "session.jsonl"
        prior = "2026-10-09T11:59:59Z"
        write_session(session_file, "synthetic-send-session", prior)

        class InspectingSerial:
            def __init__(self, port, baudrate=115200):
                self.closed = False
                self.frames: list[bytes] = []

            def write(inner, raw: bytes) -> int:
                self.assertEqual(store.load("synthetic-meter").next_sequence, 0)
                inner.frames.append(bytes(raw))
                return len(raw)

            def flush(inner):
                pass

            def close(inner):
                inner.closed = True

        serial = InspectingSerial("FAKE")
        args = argparse.Namespace(
            port="FAKE", dry_run=False, device_alias="synthetic-meter", state_file=str(state_path),
            lock_dir=str(lock_dir), session_file=str(session_file), session_dir=None, session_id=None,
            latest=False, live_quota=False, provider_fixture=None, personal_usage=None, global_reset=None,
            host_alias="synthetic-host", agent_id="synthetic-cli", reference_time=STAMP, output=None,
        )
        with patch.object(cli, "WindowsSerialSink", return_value=serial):
            self.assertEqual(cli.cmd_send(args), 0)
        self.assertTrue(serial.closed)
        self.assertEqual(store.load("synthetic-meter").next_sequence, 0)
        output = c_receive(serial.frames)[0]
        self.assertTrue(output["accepted"], output.get("error"))
        self.assertEqual(output["sequence"], 0xFFFFFFFF)

        sender = CdmSender("synthetic-meter", store, lock_dir=lock_dir)
        class NoWrite:
            def __init__(self):
                self.count = 0

            def write(self, data):
                self.count += 1
                return len(data)

            def flush(self):
                pass

            def close(self):
                pass
        sink = NoWrite()
        state_path.write_text("{broken", encoding="utf-8")
        corrupt = sender.transmit_payload({"usage": [], "global_resets": []}, STAMP, sink=sink)
        self.assertEqual(corrupt.error_code, "STATE_FAILURE")
        self.assertEqual(sink.count, 0)
        state_path.unlink()
        missing = sender.transmit_payload({"usage": [], "global_resets": []}, STAMP, sink=sink)
        self.assertEqual(missing.error_code, "STATE_LOST")
        self.assertEqual(sink.count, 0)
        sender.close()

    def test_cli_refuses_implicit_state_initialization_and_sender_contention(self):
        state_path = self.root / "absent-state.json"
        lock_dir = self.root / "locks"
        args = argparse.Namespace(
            port="FAKE", dry_run=False, device_alias="synthetic-meter", state_file=str(state_path),
            lock_dir=str(lock_dir), session_file=None, session_dir=None, session_id=None, latest=False,
            live_quota=False, provider_fixture=None, personal_usage=None, global_reset=None,
            host_alias="synthetic-host", agent_id="synthetic-cli", reference_time=STAMP, output=None,
        )
        with patch.object(cli, "WindowsSerialSink", side_effect=AssertionError("must not open")):
            self.assertEqual(cli.cmd_send(args), 1)
        self.assertFalse(state_path.exists())

        store = StateStore(state_path)
        store.initialize_new("synthetic-meter", initial_sequence=0)
        holder = CdmSender("synthetic-meter", store, lock_dir=lock_dir)
        with patch.object(cli, "WindowsSerialSink", side_effect=AssertionError("must not open")):
            self.assertEqual(cli.cmd_send(args), 1)
        holder.close()

    def test_production_windows_serial_flush_is_bounded_and_consumes_reserved_sequence(self):
        state_path = self.root / "flush-state.json"
        StateStore(state_path).initialize_new("synthetic-flush", initial_sequence=17)
        session_file = self.root / "flush-session.jsonl"
        write_session(session_file, "synthetic-flush-session", "2026-10-09T11:59:59Z")
        instances = []

        class QueuedSerial:
            def __init__(self, **kwargs):
                self.options = kwargs
                self.write_timeout = kwargs["write_timeout"]
                self.queued_at = None
                self.closed = False
                instances.append(self)

            @property
            def out_waiting(self):
                if self.closed or self.queued_at is None:
                    return 0
                return 0 if time.monotonic() - self.queued_at >= 4.0 else 128

            def write(self, data):
                self.queued_at = time.monotonic()
                return len(data)

            def flush(self):
                raise AssertionError("production wrapper must drain using out_waiting")

            def close(self):
                self.closed = True

        fake_serial = serial_module(QueuedSerial)

        args = argparse.Namespace(
            port="FAKE", dry_run=False, device_alias="synthetic-flush", state_file=str(state_path),
            lock_dir=str(self.root / "flush-locks"), session_file=str(session_file),
            session_dir=None, session_id=None, latest=False, live_quota=False, provider_fixture=None,
            personal_usage=None, global_reset=None, host_alias="synthetic-host",
            agent_id="synthetic-cli", reference_time=STAMP, output=None,
        )
        started = time.monotonic()
        with patch.dict(sys.modules, {"serial": fake_serial}):
            rc = cli.cmd_send(args)
        elapsed = time.monotonic() - started
        failures = []
        if rc != 1:
            failures.append(f"cmd_send returned {rc} despite the queued-byte timeout")
        self.assertEqual(len(instances), 1)
        self.assertGreater(instances[0].options.get("write_timeout", 0), 0)
        if not instances[0].closed:
            failures.append("CLI did not close the serial wrapper")
        if elapsed >= 3.0:
            failures.append(f"flush exceeded its bound: {elapsed:.2f}s")
        if instances[0].out_waiting != 0:
            failures.append("closed serial sink retained queued bytes")
        if StateStore(state_path).load("synthetic-flush").next_sequence != 18:
            failures.append("reserved sequence was not consumed after failed host write")
        self.assertEqual(failures, [], "; ".join(failures))

    def test_production_windows_serial_success_waits_for_queue_drain(self):
        state_path = self.root / "drain-state.json"
        StateStore(state_path).initialize_new("synthetic-drain", initial_sequence=8)
        session_file = self.root / "drain-session.jsonl"
        write_session(session_file, "synthetic-drain-session", "2026-10-09T11:59:59Z")
        instances = []

        class DrainingSerial:
            def __init__(self, **kwargs):
                self.write_timeout = kwargs["write_timeout"]
                self.queued_at = None
                self.closed = False
                instances.append(self)

            @property
            def out_waiting(self):
                if self.closed or self.queued_at is None:
                    return 0
                return 0 if time.monotonic() - self.queued_at >= 0.08 else 64

            def write(self, raw):
                self.queued_at = time.monotonic()
                self.raw = bytes(raw)
                return len(raw)

            def close(self):
                self.closed = True

        args = argparse.Namespace(
            port="FAKE", dry_run=False, device_alias="synthetic-drain", state_file=str(state_path),
            lock_dir=str(self.root / "drain-locks"), session_file=str(session_file),
            session_dir=None, session_id=None, latest=False, live_quota=False, provider_fixture=None,
            personal_usage=None, global_reset=None, host_alias="synthetic-host",
            agent_id="synthetic-cli", reference_time=STAMP, output=None,
        )
        with patch.dict(sys.modules, {"serial": serial_module(DrainingSerial)}):
            self.assertEqual(cli.cmd_send(args), 0)
        self.assertEqual(len(instances), 1)
        self.assertTrue(instances[0].closed)
        self.assertEqual(StateStore(state_path).load("synthetic-drain").next_sequence, 9)
        self.assertTrue(c_receive([instances[0].raw])[0]["accepted"])

    def test_watch_manual_refresh_is_independent_of_automatic_deadline_and_bounded(self):
        state_path = self.root / "watch-state.json"
        lock_dir = self.root / "watch-locks"
        StateStore(state_path).initialize_new("synthetic-watch", initial_sequence=0)
        clock = _GateClock()
        manual = threading.Event()
        stop = threading.Event()

        class FakeSerial:
            def __init__(self):
                self.frames: list[bytes] = []
                self.writes = threading.Event()

            def write(inner, raw: bytes) -> int:
                inner.frames.append(bytes(raw))
                inner.writes.set()
                return len(raw)

            def flush(inner):
                pass

            def close(inner):
                pass

        serial = FakeSerial()
        args = argparse.Namespace(
            port="FAKE", dry_run=False, device_alias="synthetic-watch", interval=60,
            state_file=str(state_path), lock_dir=str(lock_dir), session_file=None,
            session_dir=None, session_id=None, latest=False, live_quota=False,
            provider_fixture=None, personal_usage=None, global_reset=None,
            host_alias="synthetic-host", agent_id="synthetic-cli", reference_time=STAMP, once=False,
        )
        thread = threading.Thread(target=cli.run_watch_loop, kwargs={
            "args": args, "state_manager": SharedCollectionState(), "manual_trigger_event": manual,
            "stop_event": stop, "time_provider": clock,
        }, daemon=True)
        with patch.object(cli, "WindowsSerialSink", return_value=serial):
            thread.start()
            self.assertTrue(serial.writes.wait(2), "initial automatic CLI write did not occur")
            first_count = len(serial.frames)
            request_started = time.monotonic()
            manual.set()
            deadline = time.monotonic() + 2
            while len(serial.frames) < first_count + 1 and time.monotonic() < deadline:
                time.sleep(0.005)
            self.assertEqual(len(serial.frames), first_count + 1, "manual CLI refresh did not write")
            self.assertLess(time.monotonic() - request_started, 5.0)

            clock.advance(59.9)
            time.sleep(0.05)
            self.assertEqual(len(serial.frames), first_count + 1,
                             "manual refresh incorrectly reset the automatic deadline")
            clock.advance(0.1)
            deadline = time.monotonic() + 2
            while len(serial.frames) < first_count + 2 and time.monotonic() < deadline:
                time.sleep(0.005)
            self.assertEqual(len(serial.frames), first_count + 2,
                             "automatic refresh missed the original 60-second deadline")
            stop.set()
            thread.join(timeout=2)
        self.assertFalse(thread.is_alive())

    def test_watch_manual_event_during_write_collects_new_session_before_clearing(self):
        state_path = self.root / "inflight-state.json"
        StateStore(state_path).initialize_new("synthetic-inflight", initial_sequence=0)
        session_file = self.root / "inflight-session.jsonl"
        write_session(session_file, "synthetic-inflight-session", "2026-10-09T11:59:59Z",
                      input_tokens=40, output_tokens=10, total_tokens=50)
        first_write_started = threading.Event()
        release_first_write = threading.Event()
        manual = threading.Event()
        stop = threading.Event()
        clock = _GateClock()
        serial_instances = []

        class BlockingSerial:
            def __init__(self, **kwargs):
                self.write_timeout = kwargs["write_timeout"]
                self.frames = []
                self.closed = False
                serial_instances.append(self)

            @property
            def out_waiting(self):
                return 0

            def write(self, raw):
                self.frames.append(bytes(raw))
                if len(self.frames) == 1:
                    first_write_started.set()
                    release_first_write.wait(3)
                return len(raw)

            def flush(self):
                pass

            def close(self):
                self.closed = True

        args = argparse.Namespace(
            port="FAKE", dry_run=False, device_alias="synthetic-inflight", interval=60,
            state_file=str(state_path), lock_dir=str(self.root / "inflight-locks"),
            session_file=str(session_file), session_dir=None, session_id=None, latest=False,
            live_quota=False, provider_fixture=None, personal_usage=None, global_reset=None,
            host_alias="synthetic-host", agent_id="synthetic-cli", reference_time=STAMP, once=False,
        )
        thread = threading.Thread(target=cli.run_watch_loop, kwargs={
            "args": args, "state_manager": SharedCollectionState(), "manual_trigger_event": manual,
            "stop_event": stop, "time_provider": clock,
        }, daemon=True)
        fake_serial = serial_module(BlockingSerial)
        with patch.dict(sys.modules, {"serial": fake_serial}):
            thread.start()
            try:
                self.assertTrue(first_write_started.wait(2), "automatic write did not start")
                write_session(session_file, "synthetic-inflight-session", "2026-10-09T11:59:58Z",
                              input_tokens=250, output_tokens=40, total_tokens=777)
                started = time.monotonic()
                manual.set()
                release_first_write.set()
                deadline = time.monotonic() + 5
                while len(serial_instances[0].frames) < 2 and time.monotonic() < deadline:
                    time.sleep(0.005)
                frames = serial_instances[0].frames
                self.assertGreaterEqual(len(frames), 2,
                                        "manual event during an already-collected write was cleared without recollection")
                self.assertLessEqual(time.monotonic() - started, 5.0)
                second = json.loads(frames[1])
                inputs = {w["window_id"]: w["used_units"]
                          for w in second["payload"]["usage"][0]["windows"]}
                self.assertEqual(inputs["input"], 250)
                self.assertTrue(c_receive([frames[1]])[0]["accepted"])
            finally:
                stop.set()
                release_first_write.set()
                thread.join(timeout=2)
        self.assertFalse(thread.is_alive())

    def test_watch_manual_event_during_native_rpc_uses_result_acquired_after_request(self):
        state_path = self.root / "rpc-watch-state.json"
        StateStore(state_path).initialize_new("synthetic-rpc-watch", initial_sequence=0)
        manual = threading.Event()
        stop = threading.Event()
        read_requested = threading.Event()
        release_result = threading.Event()
        write_event = threading.Event()
        frames = []
        init_line = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}).encode() + b"\n"
        quota_line = json.dumps({"jsonrpc": "2.0", "id": 2, "result": {
            "accountId": "synthetic-live-account",
            "rateLimits": {"primary": {"windowDurationMins": 5, "usedPercent": 37.5}},
        }}).encode() + b"\n"

        class GatedOutput:
            def __init__(self):
                self.index = 0

            def readline(self):
                self.index += 1
                if self.index == 1:
                    return init_line
                if self.index == 2:
                    release_result.wait(3)
                    return quota_line if release_result.is_set() else b""
                return b""

            def close(self):
                release_result.set()

        process = _FakeProcess(GatedOutput())
        class SignalingInput(_RecordingInput):
            def write(self, data):
                msg = json.loads(data)
                if msg.get("method") == "account/rateLimits/read":
                    read_requested.set()
                return super().write(data)
        process.stdin = SignalingInput()
        process.terminate = lambda: (setattr(process, "terminated", True), release_result.set())

        class FakeSerial:
            def __init__(self, **kwargs):
                self.write_timeout = kwargs["write_timeout"]
                self.closed = False

            def write(self, raw):
                frames.append(bytes(raw))
                write_event.set()
                return len(raw)

            @property
            def out_waiting(self):
                return 0

            def flush(self):
                pass

            def close(self):
                self.closed = True

        args = argparse.Namespace(
            port="FAKE", dry_run=False, device_alias="synthetic-rpc-watch", interval=60,
            state_file=str(state_path), lock_dir=str(self.root / "rpc-watch-locks"),
            session_file=None, session_dir=None, session_id=None, latest=False, live_quota=True,
            provider_fixture=None, personal_usage=None, global_reset=None,
            host_alias="synthetic-host", agent_id="synthetic-cli", reference_time=None, once=False,
        )
        clock = _GateClock()
        thread = threading.Thread(target=cli.run_watch_loop, kwargs={
            "args": args, "state_manager": SharedCollectionState(), "manual_trigger_event": manual,
            "stop_event": stop, "time_provider": clock,
        }, daemon=True)
        fake_serial = serial_module(FakeSerial)
        with patch("pc.quota.subprocess.Popen", return_value=process), patch.dict(sys.modules, {"serial": fake_serial}):
            thread.start()
            try:
                self.assertTrue(read_requested.wait(3), "automatic refresh did not reach real app-server read")
                request_utc = datetime.now(timezone.utc)
                request_started = time.monotonic()
                manual.set()
                release_result.set()
                self.assertTrue(write_event.wait(3), "frame was not written after RPC completion")
                self.assertLessEqual(time.monotonic() - request_started, 5.0)
                deadline = time.monotonic() + 1.0
                while manual.is_set() and time.monotonic() < deadline:
                    time.sleep(0.005)
                self.assertGreaterEqual(len(frames), 1)
                envelope = json.loads(frames[0])
                snap = envelope["payload"]["usage"][0]
                self.assertIsNotNone(snap["observed_at"], snap)
                acquired = datetime.fromisoformat(snap["observed_at"].replace("Z", "+00:00"))
                self.assertGreaterEqual(acquired, request_utc)
                self.assertEqual(snap["windows"][0]["percent_used"], 37.5)
            finally:
                stop.set()
                release_result.set()
                thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        self.assertTrue(c_receive([frames[0]])[0]["accepted"])

    def test_pure_quota_request_after_collection_requires_fresh_native_acquisition(self):
        state_path = self.root / "quota-after-acquisition-state.json"
        StateStore(state_path).initialize_new("synthetic-quota-after-acquisition", initial_sequence=0)
        manual = threading.Event()
        stop = threading.Event()
        collection_count = 0
        frames = []
        processes = []
        quota_values = iter((17.0, 29.0))
        init_line = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}).encode() + b"\n"

        def rpc_process():
            pct = next(quota_values)
            quota_line = json.dumps({"jsonrpc": "2.0", "id": 2, "result": {
                "accountId": "synthetic-pure-quota-account",
                "rateLimits": {"primary": {"windowDurationMins": 5, "usedPercent": pct}},
            }}).encode() + b"\n"

            class Output:
                def __init__(self):
                    self.lines = iter((init_line, quota_line, b""))

                def readline(self):
                    return next(self.lines, b"")

                def close(self):
                    pass

            proc = _FakeProcess(Output())
            processes.append(proc)
            return proc

        class ImmediateSerial:
            def __init__(self, **kwargs):
                self.write_timeout = kwargs["write_timeout"]
                self.closed = False

            @property
            def out_waiting(self):
                return 0

            def write(self, raw):
                frames.append(bytes(raw))
                return len(raw)

            def close(self):
                self.closed = True

        state_manager = SharedCollectionState()
        original_collect_all = state_manager.collect_all

        def collect_then_request(**kwargs):
            nonlocal collection_count
            payload = original_collect_all(**kwargs)
            collection_count += 1
            if collection_count == 1:
                # Model Enter after the real native response is acquired but before watch handles it.
                manual.set()
            return payload

        state_manager.collect_all = collect_then_request
        args = argparse.Namespace(
            port="FAKE", dry_run=False, device_alias="synthetic-quota-after-acquisition", interval=60,
            state_file=str(state_path), lock_dir=str(self.root / "quota-after-acquisition-locks"),
            session_file=None, session_dir=None, session_id=None, latest=False, live_quota=True,
            provider_fixture=None, personal_usage=None, global_reset=None,
            host_alias="synthetic-host", agent_id="synthetic-cli", reference_time=None, once=False,
        )
        thread = threading.Thread(target=cli.run_watch_loop, kwargs={
            "args": args, "state_manager": state_manager,
            "manual_trigger_event": manual, "stop_event": stop,
        }, daemon=True)
        with patch("pc.quota.subprocess.Popen", side_effect=[rpc_process(), rpc_process()]), \
                patch.dict(sys.modules, {"serial": serial_module(ImmediateSerial)}):
            thread.start()
            try:
                deadline = time.monotonic() + 3
                while collection_count < 2 and time.monotonic() < deadline:
                    time.sleep(0.005)
                self.assertGreaterEqual(
                    collection_count, 2,
                    "post-acquisition manual request was cleared using the already-acquired quota payload",
                )
                deadline = time.monotonic() + 2
                while len(frames) < 2 and time.monotonic() < deadline:
                    time.sleep(0.005)
                self.assertGreaterEqual(len(frames), 2, "fresh manual quota frame was not transmitted")
            finally:
                stop.set()
                thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        self.assertTrue(all(proc.terminated and proc.waited and proc.stdin.closed for proc in processes))
        rows = c_receive(frames)
        self.assertTrue(all(row["accepted"] for row in rows), [row.get("error") for row in rows])
        percentages = [row["usage"][0]["current"]["windows"][0]["percent_used"] for row in rows]
        self.assertEqual(percentages, [17.0, 29.0])

    def test_auto_rpc_then_post_request_manual_collection_write_and_drain_within_five_seconds(self):
        state_path = self.root / "combined-state.json"
        StateStore(state_path).initialize_new("synthetic-combined", initial_sequence=0)
        session_file = self.root / "combined-session.jsonl"
        write_session(session_file, "synthetic-combined-session", STAMP,
                      input_tokens=40, output_tokens=10, total_tokens=50)
        manual = threading.Event()
        stop = threading.Event()
        first_read = threading.Event()
        second_read = threading.Event()
        release_first = threading.Event()
        processes = []
        init_line = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}).encode() + b"\n"

        def rpc_process(account, pct, read_event, release_event=None, delay=0):
            quota_line = json.dumps({"jsonrpc": "2.0", "id": 2, "result": {
                "accountId": account,
                "rateLimits": {"primary": {"windowDurationMins": 5, "usedPercent": pct}},
            }}).encode() + b"\n"

            class Output:
                def __init__(self):
                    self.index = 0

                def readline(self):
                    self.index += 1
                    if self.index == 1:
                        return init_line
                    if self.index == 2:
                        read_event.set()
                        if release_event:
                            release_event.wait(1.0)
                        elif delay:
                            time.sleep(delay)
                        return quota_line
                    return b""

                def close(self):
                    if release_event:
                        release_event.set()

            proc = _FakeProcess(Output())
            if release_event:
                proc.terminate = lambda: (setattr(proc, "terminated", True), release_event.set())
            processes.append(proc)
            return proc

        first = rpc_process("synthetic-account", 10.0, first_read, release_first)
        second = rpc_process("synthetic-account", 20.0, second_read, delay=0.2)
        writes = []
        drained_second = threading.Event()

        class QueueSerial:
            def __init__(self, **kwargs):
                self.write_timeout = kwargs["write_timeout"]
                self.closed = False
                self.queued_at = None
                self.frames = []

            @property
            def out_waiting(self):
                if self.closed or self.queued_at is None:
                    return 0
                if time.monotonic() - self.queued_at >= 0.03:
                    if len(self.frames) >= 2:
                        drained_second.set()
                    return 0
                return 128

            def write(self, raw):
                self.queued_at = time.monotonic()
                self.frames.append(bytes(raw))
                writes.append(bytes(raw))
                return len(raw)

            def close(self):
                self.closed = True

        args = argparse.Namespace(
            port="FAKE", dry_run=False, device_alias="synthetic-combined", interval=60,
            state_file=str(state_path), lock_dir=str(self.root / "combined-locks"),
            session_file=str(session_file), session_dir=None, session_id=None, latest=False,
            live_quota=True, provider_fixture=None, personal_usage=None, global_reset=None,
            host_alias="synthetic-host", agent_id="synthetic-cli", reference_time=None, once=False,
        )
        thread = threading.Thread(target=cli.run_watch_loop, kwargs={
            "args": args, "state_manager": SharedCollectionState(),
            "manual_trigger_event": manual, "stop_event": stop,
        }, daemon=True)
        request_started = None
        fake_serial = serial_module(QueueSerial)
        with patch("pc.quota.subprocess.Popen", side_effect=[first, second]), \
                patch.dict(sys.modules, {"serial": fake_serial}):
            thread.start()
            try:
                self.assertTrue(first_read.wait(2), "automatic quota RPC did not start")
                request_started = time.monotonic()
                manual.set()
                write_session(session_file, "synthetic-combined-session",
                              datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                              input_tokens=250, output_tokens=40, total_tokens=777)
                time.sleep(0.7)
                release_first.set()
                self.assertTrue(second_read.wait(2), "manual follow-up did not perform a fresh native quota read")
                deadline = time.monotonic() + 3
                while len(writes) < 2 and time.monotonic() < deadline:
                    time.sleep(0.005)
                self.assertGreaterEqual(len(writes), 2, "manual follow-up frame missing")
                self.assertTrue(drained_second.wait(1), "manual follow-up bytes did not drain")
                elapsed = time.monotonic() - request_started
                self.assertLessEqual(elapsed, 5.0, f"AUTO remainder + MANUAL RPC/write/drain took {elapsed:.2f}s")
            finally:
                stop.set()
                release_first.set()
                thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        self.assertTrue(all(proc.terminated and proc.waited and proc.stdin.closed for proc in processes))
        rows = c_receive(writes)
        self.assertTrue(all(row["accepted"] for row in rows), [row.get("error") for row in rows])
        second_session = next(row["current"] for row in rows[1]["usage"]
                              if row["current"]["metric_kind"] == "session_telemetry")
        values = {w["window_id"]: w["used_units"] for w in second_session["windows"]}
        self.assertEqual(values["input"], 250)

    def test_second_manual_request_during_manual_write_is_not_lost(self):
        state_path = self.root / "second-manual-state.json"
        StateStore(state_path).initialize_new("synthetic-second-manual", initial_sequence=0)
        session_file = self.root / "second-manual-session.jsonl"
        write_session(session_file, "synthetic-second-manual-session", STAMP,
                      input_tokens=40, output_tokens=10, total_tokens=50)
        first_write = threading.Event()
        release_write = threading.Event()
        manual = threading.Event()
        stop = threading.Event()
        frames = []

        class BlockingSerial:
            def __init__(self, **kwargs):
                self.write_timeout = kwargs["write_timeout"]
                self.queued_at = None
                self.closed = False

            @property
            def out_waiting(self):
                return 0

            def write(self, raw):
                frames.append(bytes(raw))
                self.queued_at = time.monotonic()
                if len(frames) == 1:
                    first_write.set()
                    release_write.wait(2)
                return len(raw)

            def close(self):
                self.closed = True

        args = argparse.Namespace(
            port="FAKE", dry_run=False, device_alias="synthetic-second-manual", interval=60,
            state_file=str(state_path), lock_dir=str(self.root / "second-manual-locks"),
            session_file=str(session_file), session_dir=None, session_id=None, latest=False,
            live_quota=False, provider_fixture=None, personal_usage=None, global_reset=None,
            host_alias="synthetic-host", agent_id="synthetic-cli", reference_time=None, once=False,
        )
        manual.set()
        thread = threading.Thread(target=cli.run_watch_loop, kwargs={
            "args": args, "state_manager": SharedCollectionState(),
            "manual_trigger_event": manual, "stop_event": stop,
        }, daemon=True)
        with patch.dict(sys.modules, {"serial": serial_module(BlockingSerial)}):
            thread.start()
            try:
                self.assertTrue(first_write.wait(2), "first manual write did not start")
                write_session(session_file, "synthetic-second-manual-session",
                              datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                              input_tokens=250, output_tokens=40, total_tokens=777)
                request_started = time.monotonic()
                manual.set()
                release_write.set()
                deadline = time.monotonic() + 2
                while len(frames) < 2 and time.monotonic() < deadline:
                    time.sleep(0.005)
                self.assertGreaterEqual(len(frames), 2,
                                        "second manual request during an already-manual write was cleared")
                self.assertLessEqual(time.monotonic() - request_started, 5.0)
            finally:
                stop.set()
                release_write.set()
                thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        rows = c_receive(frames)
        self.assertTrue(all(row["accepted"] for row in rows), [row.get("error") for row in rows])
        current = next(row["current"] for row in rows[-1]["usage"]
                       if row["current"]["metric_kind"] == "session_telemetry")
        self.assertEqual(next(w["used_units"] for w in current["windows"] if w["window_id"] == "input"), 250)

    def test_auto_rpc_remainder_skips_manual_rpc_and_successful_drains_fit_five_seconds(self):
        state_path = self.root / "boundary-state.json"
        StateStore(state_path).initialize_new("synthetic-boundary", initial_sequence=0)
        session_file = self.root / "boundary-session.jsonl"
        write_session(session_file, "synthetic-boundary-session", STAMP,
                      input_tokens=40, output_tokens=10, total_tokens=50)
        manual = threading.Event()
        stop = threading.Event()
        auto_init_started = threading.Event()
        second_drain_finished = threading.Event()
        processes = []
        frames = []
        init_line = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}).encode() + b"\n"

        def rpc_process(pct, init_delay, read_delay, init_started):
            quota_line = json.dumps({"jsonrpc": "2.0", "id": 2, "result": {
                "accountId": "synthetic-boundary-account",
                "rateLimits": {"primary": {"windowDurationMins": 5, "usedPercent": pct}},
            }}).encode() + b"\n"

            class Output:
                def __init__(self):
                    self.index = 0

                def readline(self):
                    self.index += 1
                    if self.index == 1:
                        init_started.set()
                        time.sleep(init_delay)
                        return init_line
                    if self.index == 2:
                        time.sleep(read_delay)
                        return quota_line
                    return b""

                def close(self):
                    pass

            proc = _FakeProcess(Output())
            processes.append(proc)
            return proc

        auto_proc = rpc_process(10.0, 0.95, 0.95, auto_init_started)

        def bounded_terminate_wait(timeout=None):
            time.sleep(min(0.5, timeout if timeout is not None else 0.5))
            auto_proc.waited = True
            return 0

        auto_proc.wait = bounded_terminate_wait
        class DrainingSerial:
            def __init__(self, **kwargs):
                self.write_timeout = kwargs["write_timeout"]
                self.queued_at = None
                self.closed = False
                self.write_index = 0

            @property
            def out_waiting(self):
                if self.queued_at is None or time.monotonic() - self.queued_at < 0.8:
                    return 128
                if self.write_index >= 2:
                    second_drain_finished.set()
                return 0

            def write(self, raw):
                self.write_index += 1
                self.queued_at = time.monotonic()
                frames.append(bytes(raw))
                return len(raw)

            def close(self):
                self.closed = True

        args = argparse.Namespace(
            port="FAKE", dry_run=False, device_alias="synthetic-boundary", interval=60,
            state_file=str(state_path), lock_dir=str(self.root / "boundary-locks"),
            session_file=str(session_file), session_dir=None, session_id=None, latest=False,
            live_quota=True, provider_fixture=None, personal_usage=None, global_reset=None,
            host_alias="synthetic-host", agent_id="synthetic-cli", reference_time=None, once=False,
        )
        thread = threading.Thread(target=cli.run_watch_loop, kwargs={
            "args": args, "state_manager": SharedCollectionState(),
            "manual_trigger_event": manual, "stop_event": stop,
        }, daemon=True)
        request_started = None
        with patch("pc.quota.subprocess.Popen", side_effect=[auto_proc]), \
                patch.dict(sys.modules, {"serial": serial_module(DrainingSerial)}):
            thread.start()
            try:
                self.assertTrue(auto_init_started.wait(2), "AUTO initialize did not start")
                request_started = time.monotonic()
                manual.set()
                write_session(session_file, "synthetic-boundary-session",
                              datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                              input_tokens=250, output_tokens=40, total_tokens=777)
                self.assertTrue(second_drain_finished.wait(5), "MANUAL serial bytes did not drain")
                elapsed = time.monotonic() - request_started
                self.assertLessEqual(
                    elapsed, 5.0,
                    f"AUTO RPC remainder + MANUAL RPC + successful serial drains took {elapsed:.2f}s",
                )
            finally:
                stop.set()
                thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(processes), 1, "exhausted manual budget must not start another native RPC")
        self.assertTrue(all(proc.terminated and proc.waited and proc.stdin.closed for proc in processes))
        rows = c_receive(frames)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["accepted"] for row in rows), [row.get("error") for row in rows])
        quota = next(row["current"] for row in rows[1]["usage"]
                     if row["current"]["metric_kind"] == "quota_window")
        self.assertEqual(quota["status"], "error")
        self.assertEqual(quota["error_code"], "QUOTA_TIMEOUT")
        self.assertEqual(quota["windows"][0]["percent_used"], 10.0)
        current = next(row["current"] for row in rows[1]["usage"]
                       if row["current"]["metric_kind"] == "session_telemetry")
        self.assertEqual(next(w["used_units"] for w in current["windows"] if w["window_id"] == "input"), 250)

    def test_auto_and_manual_rpc_plus_successful_drains_finish_sender_within_five_seconds(self):
        state_path = self.root / "two-rpc-boundary-state.json"
        StateStore(state_path).initialize_new("synthetic-two-rpc-boundary", initial_sequence=0)
        session_file = self.root / "two-rpc-boundary-session.jsonl"
        write_session(session_file, "synthetic-two-rpc-boundary-session", STAMP,
                      input_tokens=40, output_tokens=10, total_tokens=50)
        manual = threading.Event()
        stop = threading.Event()
        auto_init_started = threading.Event()
        manual_init_started = threading.Event()
        second_drain_finished = threading.Event()
        processes = []
        frames = []
        sender_outcomes = []
        init_line = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}).encode() + b"\n"

        def rpc_process(pct, init_delay, read_delay, init_started):
            quota_line = json.dumps({"jsonrpc": "2.0", "id": 2, "result": {
                "accountId": "synthetic-two-rpc-account",
                "rateLimits": {"primary": {"windowDurationMins": 5, "usedPercent": pct}},
            }}).encode() + b"\n"

            class Output:
                def __init__(self):
                    self.index = 0

                def readline(self):
                    self.index += 1
                    if self.index == 1:
                        init_started.set()
                        time.sleep(init_delay)
                        return init_line
                    if self.index == 2:
                        time.sleep(read_delay)
                        return quota_line
                    return b""

                def close(self):
                    pass

            proc = _FakeProcess(Output())
            processes.append(proc)
            return proc

        auto_proc = rpc_process(10.0, 0.95, 0.95, auto_init_started)
        manual_proc = rpc_process(20.0, 0.9, 0.9, manual_init_started)

        class DrainingSerial:
            def __init__(self, **kwargs):
                self.write_timeout = kwargs["write_timeout"]
                self.queued_at = None
                self.closed = False
                self.write_index = 0

            @property
            def out_waiting(self):
                if self.queued_at is None or time.monotonic() - self.queued_at < 0.8:
                    return 128
                if self.write_index >= 2:
                    second_drain_finished.set()
                return 0

            def write(self, raw):
                self.write_index += 1
                self.queued_at = time.monotonic()
                frames.append(bytes(raw))
                return len(raw)

            def close(self):
                self.closed = True

        args = argparse.Namespace(
            port="FAKE", dry_run=False, device_alias="synthetic-two-rpc-boundary", interval=60,
            state_file=str(state_path), lock_dir=str(self.root / "two-rpc-boundary-locks"),
            session_file=str(session_file), session_dir=None, session_id=None, latest=False,
            live_quota=True, provider_fixture=None, personal_usage=None, global_reset=None,
            host_alias="synthetic-host", agent_id="synthetic-cli", reference_time=None, once=False,
        )
        thread = threading.Thread(target=cli.run_watch_loop, kwargs={
            "args": args, "state_manager": SharedCollectionState(),
            "manual_trigger_event": manual, "stop_event": stop,
        }, daemon=True)
        original_transmit = CdmSender.transmit_payload

        def observe_sender_terminal(sender, *args, **kwargs):
            outcome = original_transmit(sender, *args, **kwargs)
            sender_outcomes.append((time.monotonic(), outcome))
            return outcome

        with patch("pc.quota.subprocess.Popen", side_effect=[auto_proc, manual_proc]), \
                patch.object(CdmSender, "transmit_payload", observe_sender_terminal), \
                patch.dict(sys.modules, {"serial": serial_module(DrainingSerial)}):
            thread.start()
            try:
                self.assertTrue(auto_init_started.wait(2), "AUTO initialize did not start")
                request_started = time.monotonic()
                manual.set()
                write_session(session_file, "synthetic-two-rpc-boundary-session",
                              datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                              input_tokens=250, output_tokens=40, total_tokens=777)
                self.assertTrue(manual_init_started.wait(5), "bounded MANUAL RPC did not start")
                self.assertTrue(second_drain_finished.wait(5), "MANUAL queue did not drain")
                deadline = time.monotonic() + 0.5
                while len(sender_outcomes) < 2 and time.monotonic() < deadline:
                    time.sleep(0.001)
                self.assertEqual(len(sender_outcomes), 2, "production sender did not return both outcomes")
                self.assertLessEqual(sender_outcomes[-1][0] - request_started, 5.0,
                                     "manual request through production SendOutcome exceeded 5s")
                self.assertTrue(sender_outcomes[-1][1].success, sender_outcomes[-1][1])
            finally:
                stop.set()
                thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(processes), 2)
        self.assertTrue(all(proc.terminated and proc.waited and proc.stdin.closed for proc in processes))
        rows = c_receive(frames)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["accepted"] for row in rows), [row.get("error") for row in rows])
        quota = next(row["current"] for row in rows[1]["usage"]
                     if row["current"]["metric_kind"] == "quota_window")
        self.assertEqual(quota["status"], "error")
        self.assertEqual(quota["windows"][0]["percent_used"], 10.0)
        current = next(row["current"] for row in rows[1]["usage"]
                       if row["current"]["metric_kind"] == "session_telemetry")
        self.assertEqual(next(w["used_units"] for w in current["windows"] if w["window_id"] == "input"), 250)

    def test_watch_reconnect_is_rate_limited_and_writes_within_five_seconds_of_availability(self):
        state_path = self.root / "reconnect-state.json"
        lock_dir = self.root / "reconnect-locks"
        StateStore(state_path).initialize_new("synthetic-reconnect", initial_sequence=0)
        clock = _GateClock()
        stop = threading.Event()
        attempts: list[float] = []
        writes: list[float] = []
        attempt_events = [threading.Event(), threading.Event(), threading.Event()]
        write_event = threading.Event()

        class FakeSerial:
            def write(inner, raw: bytes) -> int:
                writes.append(clock.now())
                write_event.set()
                return len(raw)

            def flush(inner):
                pass

            def close(inner):
                pass

        serial = FakeSerial()

        def open_fake(port, baudrate=115200):
            attempts.append(clock.now())
            attempt_events[len(attempts) - 1].set()
            if len(attempts) < 3:
                raise OSError("synthetic port unavailable")
            return serial

        args = argparse.Namespace(
            port="FAKE", dry_run=False, device_alias="synthetic-reconnect", interval=60,
            state_file=str(state_path), lock_dir=str(lock_dir), session_file=None,
            session_dir=None, session_id=None, latest=False, live_quota=False,
            provider_fixture=None, personal_usage=None, global_reset=None,
            host_alias="synthetic-host", agent_id="synthetic-cli", reference_time=STAMP, once=False,
        )
        thread = threading.Thread(target=cli.run_watch_loop, kwargs={
            "args": args, "state_manager": SharedCollectionState(), "stop_event": stop,
            "time_provider": clock,
        }, daemon=True)
        with patch.object(cli, "WindowsSerialSink", side_effect=open_fake):
            thread.start()
            self.assertTrue(attempt_events[0].wait(2))
            clock.advance(0.9)
            time.sleep(0.05)
            self.assertEqual(len(attempts), 1, "port reopen attempted more than once per second")
            clock.advance(0.11)
            self.assertTrue(attempt_events[1].wait(2))
            clock.advance(1.0)
            self.assertTrue(attempt_events[2].wait(2))
            self.assertTrue(write_event.wait(2), "available fake port was not dispatched")
            stop.set()
            thread.join(timeout=2)

        self.assertFalse(thread.is_alive())
        self.assertGreaterEqual(attempts[1] - attempts[0], 1.0)
        self.assertGreaterEqual(attempts[2] - attempts[1], 1.0)
        self.assertLessEqual(writes[0] - attempts[2], 5.0)


if __name__ == "__main__":
    unittest.main()
