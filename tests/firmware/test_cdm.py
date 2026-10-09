"""Synthetic interop and persistent receiver tests against production C modules."""
from __future__ import annotations

import copy
import json
import subprocess
import unittest
from pathlib import Path

from pc.frame import build_frame, encode_frame

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "tests/firmware/.build/cdm-host.exe"
STAMP = "2026-10-07T17:10:00Z"


def channel(name: str, count: int) -> dict:
    return dict(window_id=name, label=name, used_units=count, remaining_units=None,
                limit_units=None, unit="token", percent_used=None, percent_remaining=None,
                resets_at=None, reset_status="unknown")


def session(sid="session-a", status="available", observed=STAMP) -> dict:
    values = dict(input=124800, output=16400, cached_input=89600,
                  reasoning_output=2300, source_total=999999, normalized_total=141200)
    return dict(schema_version=1, snapshot_id=sid, provider_id="codex", agent_id="codex-cli",
                host_id="test-host", model_id=None, account_profile_id=None,
                source_kind="fixture", metric_kind="session_telemetry", unit="token",
                status=status, observed_at=observed,
                windows=[channel(k, v) for k, v in values.items()] if status == "available" else [],
                stale=False, last_good_at=observed,
                error_code=None if status == "available" else "HTTP_500",
                error_reason=None if status == "available" else "synthetic adapter failure")


def quota(sid="quota-a", status="available") -> dict:
    return dict(schema_version=1, snapshot_id=sid, provider_id="codex", agent_id="codex-cli",
                host_id="test-host", model_id=None, account_profile_id="acct-test",
                source_kind="fixture", metric_kind="quota_window", unit="percent",
                status=status, observed_at=STAMP,
                windows=[dict(window_id="primary-18000s", label="300 min", used_units=None,
                              remaining_units=None, limit_units=None, unit="percent",
                              percent_used=42, percent_remaining=58, resets_at=None,
                              reset_status="unknown")] if status == "available" else [],
                stale=False, last_good_at=STAMP,
                error_code=None if status == "available" else "DNS",
                error_reason=None if status == "available" else "synthetic adapter failure")


def global_reset(latest="2026-10-07T10:00:00Z", error=None) -> dict:
    return dict(schema_version=1, source="codex-resets.com", captured_at=STAMP,
                latest_reset_at=latest, forecast_24h_percent=None,
                forecast_48h_percent=None, forecast_is_schedule=False,
                stale=False, error_code=error)


def frame(seq: int, usage=None, global_resets=None, stamp=STAMP) -> bytes:
    value = build_frame(dict(usage=[session(), quota()] if usage is None else usage,
                             global_resets=[global_reset()] if global_resets is None else global_resets),
                        seq, stamp, reference_time=stamp)
    return encode_frame(value, reference_time=stamp)


def run_wire(*events: tuple[bytes, int, int | None]) -> list[dict]:
    request = {"events": [dict(line_hex=line.hex(), mono_ms=mono,
                                now_ms=mono if now is None else now) for line, mono, now in events]}
    result = subprocess.run([str(EXE), "--wire"], input=json.dumps(request), text=True,
                            capture_output=True, check=True, cwd=ROOT)
    return json.loads(result.stdout)


class ReceiverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not EXE.exists():
            raise RuntimeError("Run tests/firmware/build-host.ps1 first")

    def test_last_good_independent_adapter_failure_and_recovery(self):
        first = frame(7)
        error = frame(8, [session(status="error"), quota()], [global_reset(None, "HTTP_500")])
        recovery = frame(9)
        out = run_wire((first, 1000, None), (error, 2000, None), (recovery, 3000, None))
        self.assertEqual([row["accepted"] for row in out], [True] * 3)
        errored_session = next(v for v in out[1]["usage"] if v["key"] == "session-a")
        healthy_quota = next(v for v in out[1]["usage"] if v["key"] == "quota-a")
        self.assertEqual(errored_session["current"]["status"], "error")
        self.assertEqual(errored_session["good"]["windows"][4]["used_units"], 999999)
        self.assertEqual(healthy_quota["good"]["windows"][0]["percent_remaining"], 58)
        self.assertEqual(out[1]["global"][0]["good"]["latest_reset_at"], "2026-10-07T10:00:00Z")
        self.assertEqual(out[2]["usage"][0]["current"]["status"], "available")

    def test_source_age_is_separate_from_receive_age_and_anchor(self):
        old = frame(3, [session(observed="2026-10-07T17:05:00Z")], [])
        at_299 = frame(2, [session(observed="2026-10-07T17:05:01Z")], [])
        at_0 = frame(1, [session()], [])
        out = run_wire((at_0, 1000, None), (at_299, 2000, None), (old, 3000, None))
        self.assertEqual([v["usage"][0]["source_age_s"] for v in out], [0, 299, 300])
        self.assertEqual([v["usage"][0]["stale"] for v in out], [False, False, True])
        self.assertEqual([v["receive_age_s"] for v in out], [0, 0, 0])
        later = run_wire((at_0, 1000, 301000))[0]
        self.assertEqual(later["usage"][0]["source_age_s"], 300)
        self.assertEqual(later["receive_age_s"], 300)
        self.assertTrue(later["anchor"])

    def test_corruption_does_not_change_cache_or_sequence(self):
        good = frame(7)
        corrupt = good.replace(b'"protocol":"cdm/1"', b'"protocol":"cdm/2"')
        lines = [good, corrupt, good[:-1], good[:-1] + b"\r\n", good+b"\n",
                 good[:-1] + b" ", good[:-1] + b"\xff\n", b"x" * 65536 + b"\n",
                 frame(8)]
        out = run_wire(*[(line, i * 1000, None) for i, line in enumerate(lines)])
        self.assertEqual([v["accepted"] for v in out], [True]+[False]*7+[True])
        self.assertEqual([v["sequence"] for v in out[:-1]], [7]*8)
        self.assertEqual(out[-1]["sequence"], 8)
        self.assertEqual(out[7]["usage"][0]["good"]["observed_at"], STAMP)

    def test_sequence_wrap_duplicate_backwards_half_range_persistence(self):
        events = [frame(4294967295), frame(0), frame(0), frame(4294967295),
                  frame(2147483648), frame(1)]
        out = run_wire(*[(value, i * 1000, None) for i, value in enumerate(events)])
        self.assertEqual([v["accepted"] for v in out], [True, True, False, False, False, True])
        self.assertEqual(out[-1]["sequence"], 1)

    def test_semantic_invalidity_preserves_good(self):
        valid = frame(3)
        altered = copy.deepcopy(session())
        altered["windows"][2]["used_units"] = 124801
        # Bypass the PC semantic validator to exercise the C receiver's own boundary.
        envelope = json.loads(valid)
        envelope["sequence"] = 4
        envelope["payload"]["usage"][0] = altered
        import zlib
        canonical = lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        unsigned = {k: v for k, v in envelope.items() if k != "integrity"}
        envelope["integrity"]["value"] = f"{zlib.crc32(canonical(unsigned)):08X}"
        bad = canonical(envelope) + b"\n"
        out = run_wire((valid, 1000, None), (bad, 2000, None))
        self.assertEqual([v["accepted"] for v in out], [True, False])
        self.assertEqual(out[1]["usage"][0]["good"]["windows"][2]["used_units"], 89600)

    def test_actual_pc_synthetic_wire_sample(self):
        path = ROOT / "experiments/orca-harness-20261008/operator/pc-fixture-frame-0.ndjson"
        raw = path.read_bytes()
        self.assertEqual(len(raw), 3279)
        self.assertEqual(__import__("hashlib").sha256(raw).hexdigest(),
                         "a077100ec2382f9f077644b998db57928fe94e50f7622e2f456b5cf3ed77ed24")
        result = run_wire((raw, 1000, None))[0]
        self.assertTrue(result["accepted"], result["error"])
        self.assertEqual(result["sequence"], 0)
        self.assertEqual(len(result["usage"]), 4)
        self.assertEqual(len(result["global"]), 1)


if __name__ == "__main__":
    unittest.main()
