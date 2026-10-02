import importlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_support import read
from host_device_pipeline import build_frame, encode_frame


class ProductObservationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("product_observation"), "production observation tools missing")
        self.tools = importlib.import_module("product_observation")
        self.snapshot = read(ROOT / "experiments/fixtures/providers/codex-percent-window.json")

    def wire(self, sequence=1, sent_at="2026-09-10T00:00:01Z"):
        return encode_frame(build_frame({"usage": [self.snapshot], "global_resets": []}, sequence, sent_at))

    def test_new_frame_cannot_make_old_or_future_source_fresh(self):
        receiver = self.tools.ProductReceiver("2026-09-10T00:10:00Z", 100)
        old = receiver.receive(self.wire(sent_at="2026-09-10T00:10:00Z"), 100)
        self.assertFalse(old["accepted"])
        self.assertEqual(old["error_code"], "STALE_THRESHOLD_EXCEEDED")
        self.snapshot.update(observed_at="2026-09-10T00:11:00Z", last_good_at="2026-09-10T00:11:00Z")
        future = receiver.receive(self.wire(sent_at="2026-09-10T00:10:00Z"), 100)
        self.assertEqual(future["error_code"], "FUTURE_TIMESTAMP")

    def test_source_and_receive_clocks_have_independent_300_second_boundaries(self):
        receiver = self.tools.ProductReceiver("2026-09-10T00:00:01Z", 100)
        self.assertTrue(receiver.receive(self.wire(), 100)["accepted"])
        self.assertFalse(receiver.advance(398)["source_stale"])
        self.assertTrue(receiver.advance(399)["source_stale"])
        self.assertFalse(receiver.advance(399)["receive_stale"])
        self.assertTrue(receiver.advance(400)["receive_stale"])
        self.assertEqual(receiver.advance(400)["payload"]["usage"][0]["observed_at"], "2026-09-10T00:00:00Z")

    def test_bad_wire_keeps_last_good_and_clock_reset_requires_a_new_anchor(self):
        receiver = self.tools.ProductReceiver("2026-09-10T00:00:01Z", 100)
        self.assertTrue(receiver.receive(self.wire(), 100)["accepted"])
        result = receiver.receive(self.wire(2)[:-2], 101)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["payload"]["usage"][0]["windows"][0]["percent_remaining"], 80)
        with self.assertRaises(ValueError):
            receiver.advance(99)
        receiver.reset(None, 0)
        result = receiver.receive(self.wire(1), 0)
        self.assertEqual(result["clock_status"], "unknown")
        self.assertIsNone(result["source_stale"])

    def test_capture_owns_one_backend_and_write_does_not_mean_acceptance_or_optical_pass(self):
        class Serial:
            def __init__(self):
                self.writes, self.closed = [], False
            def write(self, wire):
                self.writes.append(wire)
                return len(wire)
            def read(self, count):
                return b"CDM_DISPLAY sequence=1 result=0\n"
            def close(self):
                self.closed = True
        serial = Serial()
        opens = []
        def factory(port):
            opens.append(port)
            return serial
        with tempfile.TemporaryDirectory() as folder:
            report = self.tools.capture_frames([self.wire()], "TEST", factory, Path(folder), wait_seconds=0.01)
            self.assertEqual(opens, ["TEST"])
            self.assertTrue(serial.closed)
            self.assertEqual(len(serial.writes), 1)
            self.assertIsNone(report["frames"][0]["accepted_at_seconds"])
            self.assertEqual(report["optical_status"], "not_run")
            self.assertFalse(report["product_pass"])

    def test_receiver_marker_is_distinct_from_display_marker_and_short_write_is_preserved(self):
        class Serial:
            def write(self, wire):
                return len(wire) - 1
            def read(self, count):
                return b"CDM_RX sequence=1 result=0\n"
            def close(self):
                pass
        with tempfile.TemporaryDirectory() as folder:
            report = self.tools.capture_frames([self.wire()], "TEST", lambda _: Serial(), Path(folder), wait_seconds=0.01)
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["error_code"], "SERIAL_WRITE_INCOMPLETE")
            self.assertIsNone(report["frames"][0]["accepted_at_seconds"])
            self.assertTrue((Path(folder) / "capture.json").is_file())

    def test_recovered_reference_schedule_does_not_reject_second_frame_as_future(self):
        reference = read(ROOT / "experiments/reference/codex-7923f96/reference-inputs.json")
        wires = (ROOT / "experiments/reference/codex-7923f96/expected-frames.jsonl").read_bytes().splitlines(keepends=True)
        result = self.tools.replay_frames(wires, reference["reference_time"], monotonic_offsets=reference["monotonic_offsets"])
        self.assertEqual([frame["accepted"] for frame in result["frames"]], [True, True])
        self.assertTrue(all(frame["source_stale"] for frame in result["frames"]))

    def test_queued_receiver_marker_cannot_be_attributed_to_a_new_write(self):
        class Serial:
            pending = b"CDM_RX sequence=1 result=0\n"
            @property
            def in_waiting(self):
                return len(self.pending)
            def write(self, wire):
                return len(wire)
            def read(self, count):
                data, self.pending = self.pending, b""
                return data
            def close(self):
                pass
        with tempfile.TemporaryDirectory() as folder:
            report = self.tools.capture_frames([self.wire()], "TEST", lambda _: Serial(), folder, wait_seconds=0.01)
            self.assertIsNone(report["frames"][0]["accepted_at_seconds"])
            self.assertIn(b"CDM_RX", (Path(folder) / "device-serial.bin").read_bytes())
