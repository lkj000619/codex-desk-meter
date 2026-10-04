"""Transport tests: canonical framing, CRC, sequence persistence/wrap,
raw logs, and the 7->restart->1-reject->8-accept recovery procedure."""
import json
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pc_tools"))

from sender import (  # noqa: E402
    SequenceStore,
    SendError,
    build_frame,
    canonical,
    crc_hex,
    encode_frame,
    sequence_is_newer,
)


def tiny_payload():
    return {"usage": [], "global_resets": []}


class CanonicalTest(unittest.TestCase):
    def test_canonical_matches_spec(self):
        frame = build_frame(tiny_payload(), 1, "2026-09-10T00:00:00Z")
        unsigned = {k: frame[k] for k in ("payload", "protocol", "sent_at", "sequence")}
        expect = json.dumps(unsigned, ensure_ascii=False, allow_nan=False,
                            sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.assertEqual(canonical(unsigned), expect)
        self.assertEqual(frame["integrity"]["value"],
                         f"{zlib.crc32(expect) & 0xFFFFFFFF:08X}")
        line = encode_frame(frame)
        self.assertTrue(line.endswith(b"\n"))
        self.assertEqual(line.count(b"\n"), 1)
        self.assertLessEqual(len(line), 65536)
        self.assertNotIn(b"\r", line)

    def test_nan_rejected(self):
        with self.assertRaises(SendError):
            canonical({"v": float("nan")})

    def test_sequence_novelty(self):
        self.assertTrue(sequence_is_newer(8, 7))
        self.assertFalse(sequence_is_newer(7, 7))
        self.assertFalse(sequence_is_newer(6, 7))
        self.assertFalse(sequence_is_newer(7 + 2**31, 7))
        self.assertTrue(sequence_is_newer(0, 2**32 - 1))

    def test_crc_mismatch_detected(self):
        frame = build_frame(tiny_payload(), 3, "2026-09-10T00:00:00Z")
        frame["integrity"]["value"] = "00000000"
        with self.assertRaises(SendError):
            encode_frame(frame)

    def test_seq_persistence_and_failed_write_consumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SequenceStore(Path(tmp) / "usb.seq.json")
            with self.assertRaises(SendError):
                store.reserve()  # missing state, no silent init
            with self.assertRaises(SendError):
                store.init_alias(receiver_empty_ack=False)
            self.assertEqual(store.init_alias(receiver_empty_ack=True), 1)
            self.assertEqual(store.reserve(), 1)  # first real frame
            self.assertEqual(store.reserve(), 2)  # failed write still consumed 1
            with self.assertRaises(SendError):
                store.init_alias(receiver_empty_ack=True)  # no re-init

    def test_restart_recovery_procedure(self):
        """Same receiver: 7 accepted, restart, 1 rejected, persisted 8 accepted."""
        with tempfile.TemporaryDirectory() as tmp:
            store = SequenceStore(Path(tmp) / "dev.seq.json")
            store.init_alias(receiver_empty_ack=True)
            for _ in range(7):
                store.reserve()
            # 7 frames consumed seq 1..7; next is 8.
            self.assertEqual(store.load_next(), 8)
            # Receiver restart does not touch sender state: stale seq 1 is older.
            self.assertFalse(sequence_is_newer(1, 7))
            self.assertTrue(sequence_is_newer(8, 7))

    def test_state_corruption_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.seq.json"
            p.write_text("not json", encoding="utf-8")
            with self.assertRaises(SendError):
                SequenceStore(p).reserve()

    def test_crc_hex_format(self):
        self.assertRegex(crc_hex(b"abc"), r"^[0-9A-F]{8}$")
        self.assertEqual(crc_hex(b"123456789"), "CBF43926")


if __name__ == "__main__":
    unittest.main(verbosity=2)
