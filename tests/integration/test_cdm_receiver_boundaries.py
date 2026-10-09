"""Exercise strict cdm/1 rejection through the production C receiver."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import unittest
import zlib

from test_cdm_session_selection import HOST, STAMP, frame, session


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def signed(unsigned: dict) -> bytes:
    integrity = {"algorithm": "crc32", "value": f"{zlib.crc32(canonical(unsigned)):08X}"}
    return canonical({**unsigned, "integrity": integrity}) + b"\n"


def unsigned_frame(sequence: int, usage: list[dict]) -> dict:
    return {
        "protocol": "cdm/1",
        "sequence": sequence,
        "sent_at": STAMP,
        "payload": {"usage": usage, "global_resets": []},
    }


def host_events(lines: list[bytes], mono_times: list[int] | None = None) -> list[dict]:
    mono_times = mono_times or [(index + 1) * 1000 for index in range(len(lines))]
    events = [
        {"line_hex": line.hex(), "mono_ms": mono, "now_ms": mono}
        for line, mono in zip(lines, mono_times, strict=True)
    ]
    result = subprocess.run(
        [str(HOST), "--wire"], input=json.dumps({"events": events}), text=True,
        capture_output=True, cwd=Path(__file__).resolve().parents[2],
    )
    if result.returncode:
        raise AssertionError(f"production C host harness failed: {result.stderr or result.stdout}")
    return json.loads(result.stdout)


class ReceiverBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not HOST.is_file():
            raise RuntimeError("Run tests/firmware/build-host.ps1 first")

    def test_rejects_bad_frames_atomically_and_accepts_next_sequence(self) -> None:
        baseline = session("baseline-A", 10, 1)
        seed = signed(unsigned_frame(7, [baseline]))

        bad_protocol = unsigned_frame(8, [session("candidate", 20, 2)])
        bad_protocol["protocol"] = "cdm/2"

        extra_top_level = unsigned_frame(8, [session("candidate", 20, 2)])
        extra_top_level["unexpected"] = True

        extra_snapshot = session("candidate", 20, 2)
        extra_snapshot["private_extra"] = "synthetic"

        duplicate = session("candidate", 20, 2)
        schema_invalid = session("candidate", 20, 2)
        schema_invalid["windows"][0]["private_extra"] = "synthetic"

        valid_candidate = signed(unsigned_frame(8, [session("candidate", 20, 2)]))
        crc_bad = bytearray(valid_candidate)
        value_at = crc_bad.index(b'"value":"') + len(b'"value":"')
        crc_bad[value_at] = ord("0") if crc_bad[value_at] != ord("0") else ord("1")

        pretty = valid_candidate.replace(b'"sequence":8', b'"sequence": 8')

        lines = [
            seed,
            signed(bad_protocol),
            signed(extra_top_level),
            signed(unsigned_frame(8, [extra_snapshot])),
            signed(unsigned_frame(8, [schema_invalid])),
            signed(unsigned_frame(8, [duplicate, copy.deepcopy(duplicate)])),
            bytes(crc_bad),
            pretty,
            valid_candidate[:-1],
            valid_candidate[:-1] + b"\r\n",
            valid_candidate + b"\n",
            valid_candidate[:-1] + b"\xff\n",
            b"x" * 65536 + b"\n",
            valid_candidate,
        ]
        output = host_events(lines)

        self.assertTrue(output[0]["accepted"])
        self.assertEqual([event["accepted"] for event in output[1:-1]], [False] * 12)
        self.assertEqual([event["sequence"] for event in output[:-1]], [7] * 13)
        self.assertEqual([event["error"] for event in output[1:-1]], [
            "FRAME_SHAPE", "FRAME_SHAPE", "SNAPSHOT_INVALID", "SNAPSHOT_INVALID",
            "SNAPSHOT_DUPLICATE", "CRC_MISMATCH", "FRAME_CANONICAL",
            "FRAME_BYTES", "FRAME_BYTES", "FRAME_BYTES", "FRAME_BYTES", "FRAME_BYTES",
        ])
        for event in output[1:-1]:
            self.assertEqual([entry["key"] for entry in event["usage"]], ["baseline-A"])
            self.assertEqual(event["usage"][0]["good"]["snapshot_id"], "baseline-A")
        self.assertTrue(output[-1]["accepted"])
        self.assertEqual(output[-1]["sequence"], 8)
        self.assertEqual([entry["key"] for entry in output[-1]["usage"]], ["candidate"])

    def test_sequence_survives_stale_frame_and_silent_disconnect_gap(self) -> None:
        fresh = session("source-A", 10, 1)
        stale = session("source-A", 10, 1)
        stale["observed_at"] = "2026-10-07T17:05:00Z"
        stale["last_good_at"] = stale["observed_at"]
        lines = [
            frame(7, [fresh]),
            frame(8, [stale]),
            frame(7, [fresh]),
            frame(9, [fresh]),
        ]
        output = host_events(lines, [1000, 301000, 302000, 303000])

        self.assertEqual([event["accepted"] for event in output], [True, True, False, True])
        self.assertEqual([event["sequence"] for event in output], [7, 8, 8, 9])
        self.assertEqual(output[1]["usage"][0]["source_age_s"], 300)
        self.assertEqual(output[1]["receive_age_s"], 0)
        self.assertTrue(output[1]["usage"][0]["stale"])
        self.assertEqual(output[2]["usage"][0]["good"]["snapshot_id"], "source-A")

    def test_accepts_fractional_quota_and_unicode_canonical_label(self) -> None:
        quota = session("quota-float", 0, 0)
        quota["metric_kind"] = "quota_window"
        quota["unit"] = "percent"
        quota["account_profile_id"] = "synthetic-account"
        quota["windows"] = [{
            "window_id": "primary-18000s",
            "label": "300 min · 사용량",
            "used_units": None,
            "remaining_units": None,
            "limit_units": None,
            "unit": "percent",
            "percent_used": 42.5,
            "percent_remaining": 57.5,
            "resets_at": None,
            "reset_status": "unknown",
        }]
        result = host_events([frame(1, [quota])])[0]

        self.assertTrue(result["accepted"], result["error"])
        window = result["usage"][0]["current"]["windows"][0]
        self.assertEqual(window["percent_used"], 42.5)
        self.assertEqual(window["percent_remaining"], 57.5)
        self.assertEqual(window["label"], "300 min · 사용량")


if __name__ == "__main__":
    unittest.main()
