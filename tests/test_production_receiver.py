from __future__ import annotations

import json
import os
import subprocess
import unittest
import copy
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIVER = ROOT / "build-host" / ("meter_receiver_cli.exe" if os.name == "nt" else "meter_receiver_cli")
COMMON_FRAMES = ROOT / ".benchmark-inputs" / "feedback-evidence" / "007-sent-frames.jsonl"


class ProductionCReceiverTests(unittest.TestCase):
    def _run_receiver(self, frames: bytes) -> list[dict]:
        if not RECEIVER.is_file():
            self.skipTest("build-host/meter_receiver_cli must be built with CMake first")
        completed = subprocess.run([str(RECEIVER)], input=frames, capture_output=True, check=True)
        return [json.loads(line) for line in completed.stdout.splitlines()]

    def test_exact_common_seq_zero_and_one_frames_reach_production_c_receiver(self):
        outputs = self._run_receiver(COMMON_FRAMES.read_bytes())
        self.assertEqual(len(outputs), 2)
        self.assertEqual([item["accepted"] for item in outputs], [True, True])
        self.assertEqual([item["sequence"] for item in outputs], [0, 1])
        self.assertTrue(all(item["has_good_frame"] and not item["receive_stale"] for item in outputs))
        self.assertEqual(outputs[-1]["last_error"], "")

    def test_rejected_duplicate_keeps_last_good_sequence_and_payload(self):
        first = COMMON_FRAMES.read_bytes().splitlines(keepends=True)[0]
        outputs = self._run_receiver(first + first)
        self.assertEqual([item["accepted"] for item in outputs], [True, False])
        self.assertEqual(outputs[1]["sequence"], 0)
        self.assertTrue(outputs[1]["has_good_frame"])
        self.assertEqual(outputs[1]["last_error"], "DUPLICATE_SEQUENCE")
        self.assertEqual(outputs[1]["last_good_length"], len(first))

    def test_bad_crc_retains_previous_good_frame(self):
        first = COMMON_FRAMES.read_bytes().splitlines(keepends=True)[0]
        corrupted = first.replace(b"203D8DF3", b"203D8DF4", 1)
        self.assertNotEqual(corrupted, first)
        outputs = self._run_receiver(first + corrupted)
        self.assertEqual([item["accepted"] for item in outputs], [True, False])
        self.assertEqual(outputs[1]["sequence"], 0)
        self.assertTrue(outputs[1]["has_good_frame"])
        self.assertEqual(outputs[1]["last_error"], "CRC_MISMATCH")

    @staticmethod
    def _canonical(value: dict) -> bytes:
        return json.dumps(value, ensure_ascii=False, allow_nan=False,
                          sort_keys=True, separators=(",", ":")).encode("utf-8")

    @classmethod
    def _signed_line(cls, frame: dict) -> bytes:
        unsigned = {key: value for key, value in frame.items() if key != "integrity"}
        signed = copy.deepcopy(frame)
        integrity = copy.deepcopy(frame.get("integrity", {}))
        integrity["value"] = f"{zlib.crc32(cls._canonical(unsigned)) & 0xFFFFFFFF:08X}"
        signed["integrity"] = integrity
        return cls._canonical(signed) + b"\n"

    def test_29_production_c_wire_and_schema_cases(self):
        common0, common1 = COMMON_FRAMES.read_bytes().splitlines(keepends=True)
        base = json.loads(common0)
        cases: list[tuple[str, bytes, bool]] = [
            ("common-sequence-0", common0, True),
            ("common-sequence-1", common1, True),
        ]

        def mutate(name: str, action) -> None:
            frame = copy.deepcopy(base)
            action(frame)
            cases.append((name, self._signed_line(frame), False))

        mutate("unsupported-protocol", lambda frame: frame.update(protocol="cdm/2"))
        mutate("sequence-overflow", lambda frame: frame.update(sequence=4294967296))
        mutate("fractional-sequence", lambda frame: frame.update(sequence=0.5))
        mutate("extra-top-level-key", lambda frame: frame.update(extra=True))
        mutate("missing-global-resets", lambda frame: frame["payload"].pop("global_resets"))
        mutate("missing-usage", lambda frame: frame["payload"].pop("usage"))
        mutate("invalid-provider-id", lambda frame: frame["payload"]["usage"][0].update(provider_id="OpenAI"))
        mutate("null-available-agent", lambda frame: frame["payload"]["usage"][0].update(
            agent_id=None, status="available", stale=False,
            observed_at=frame["sent_at"], last_good_at=frame["sent_at"],
            error_code=None, error_reason=None))
        mutate("out-of-range-percent", lambda frame: frame["payload"]["usage"][0]["windows"][0].update(percent_used=101, percent_remaining=0))
        mutate("inconsistent-percent-pair", lambda frame: frame["payload"]["usage"][0]["windows"][0].update(percent_remaining=59))
        mutate("partial-percent-pair", lambda frame: frame["payload"]["usage"][0]["windows"][0].update(percent_remaining=None))
        mutate("inconsistent-absolute-balance", lambda frame: frame["payload"]["usage"][0]["windows"][0].update(unit="token", used_units=2, remaining_units=3, limit_units=99))
        mutate("available-over-stale-threshold", lambda frame: frame["payload"]["usage"][0].update(status="available", stale=False, error_code=None, error_reason=None))
        mutate("stale-status-flag-mismatch", lambda frame: frame["payload"]["usage"][0].update(stale=False))
        mutate("stale-younger-than-threshold", lambda frame: frame["payload"]["usage"][0].update(observed_at=frame["sent_at"], last_good_at=frame["sent_at"]))
        mutate("future-last-good", lambda frame: frame["payload"]["usage"][0].update(last_good_at="2026-10-01T00:00:00Z"))
        mutate("future-observation", lambda frame: frame["payload"]["usage"][0].update(observed_at="2026-10-01T00:00:00Z", last_good_at="2026-10-01T00:00:00Z"))
        mutate("invalid-window-reset-time", lambda frame: frame["payload"]["usage"][0]["windows"][0].update(resets_at="not-a-time"))
        mutate("reset-status-mismatch", lambda frame: frame["payload"]["usage"][0]["windows"][0].update(reset_status="scheduled"))
        mutate("invalid-source-kind", lambda frame: frame["payload"]["usage"][0].update(source_kind="network"))
        mutate("invalid-metric-kind", lambda frame: frame["payload"]["usage"][0].update(metric_kind="other"))
        mutate("global-captured-in-future", lambda frame: frame["payload"]["global_resets"][0].update(captured_at="2026-10-01T00:00:00Z"))
        mutate("forecast-marked-schedule", lambda frame: frame["payload"]["global_resets"][0].update(forecast_is_schedule=True))
        mutate("forecast-over-100", lambda frame: frame["payload"]["global_resets"][0].update(forecast_24h_percent=101))
        mutate("wrong-integrity-algorithm", lambda frame: frame["integrity"].update(algorithm="sha256"))
        wrong_crc = common0.replace(base["integrity"]["value"].encode("ascii"), b"00000000", 1)
        cases.append(("bad-crc", wrong_crc, False))
        invalid_utf8 = common0.replace(b'"five-hour"', b'"\xffive-hour"', 1)
        cases.append(("invalid-utf8", invalid_utf8, False))

        self.assertEqual(len(cases), 29)
        for name, line, expected_acceptance in cases:
            with self.subTest(case=name):
                output = self._run_receiver(line)
                self.assertEqual(len(output), 1)
                self.assertIs(output[0]["accepted"], expected_acceptance)
                if expected_acceptance:
                    self.assertTrue(output[0]["has_good_frame"])
                else:
                    self.assertFalse(output[0]["has_good_frame"])
                    self.assertNotEqual(output[0]["last_error"], "")


if __name__ == "__main__":
    unittest.main()
