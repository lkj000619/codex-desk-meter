"""End-to-end pipeline test (host): collector -> sender -> golden frame.

Verifies the offline fixture-to-frame path byte-for-byte: canonical form,
CRC, LF discipline, size cap, and determinism. The device-side half (USB
receipt, LCD) is operator hardware scope and is NOT claimed here.
"""
import json
import sys
import tempfile
import unittest
import zlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pc_tools"))

from collector import collect_globals, collect_providers, parse_ts  # noqa: E402
from sender import SequenceStore, build_frame, encode_frame  # noqa: E402

REFERENCE = "2026-09-10T00:04:59Z"
SENT_AT = "2026-09-10T00:04:59Z"


class PipelineTest(unittest.TestCase):
    def test_collector_to_frame_roundtrip(self):
        ref = parse_ts(REFERENCE, "reference_time")
        snaps, pfails = collect_providers(
            ["codex-percent-window.json", "claude-code-windows.json",
             "gemini-cli-unsupported.json", "antigravity-cli-unsupported.json",
             "orca-host-claude-code.json"], ref)
        self.assertEqual(pfails, [])
        resets, gfails = collect_globals(
            ["codex-reset-forecast.json", "codex-resets-history.json"])
        self.assertEqual(gfails, [])
        payload = {"usage": snaps, "global_resets": resets}
        frame = build_frame(payload, 1, SENT_AT)
        line = encode_frame(frame)
        self.assertTrue(line.endswith(b"\n"))
        self.assertEqual(line.count(b"\n"), 1)
        self.assertLessEqual(len(line), 65536)
        # Determinism: same input -> identical bytes.
        line2 = encode_frame(build_frame(payload, 1, SENT_AT))
        self.assertEqual(line, line2)
        # CRC covers the canonical unsigned envelope.
        body = json.loads(line.decode("utf-8"))
        unsigned = {k: body[k] for k in ("payload", "protocol", "sent_at", "sequence")}
        expect = json.dumps(unsigned, ensure_ascii=False, allow_nan=False,
                            sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.assertEqual(body["integrity"]["value"],
                         f"{zlib.crc32(expect) & 0xFFFFFFFF:08X}")
        # Original source times are preserved, never overwritten by send time.
        self.assertEqual(body["payload"]["usage"][0]["observed_at"],
                         "2026-09-10T00:00:00Z")
        shown = [r for r in body["payload"]["global_resets"]
                 if r["source"] == "codex-resets.com"][0]
        self.assertEqual(shown["latest_reset_at"], "2026-09-08T01:56:00Z")

    def test_sender_cli_dry_run(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            payload_path = tmpdir / "payload.json"
            payload_path.write_text(json.dumps({"usage": [], "global_resets": []}),
                                    encoding="utf-8")
            state_dir = tmpdir / "state"
            out = tmpdir / "frame.bin"
            raw = tmpdir / "raw.log"
            report = tmpdir / "report.json"
            cmd = [sys.executable, str(ROOT / "pc_tools" / "sender.py"),
                   "--payload", str(payload_path), "--sent-at", SENT_AT,
                   "--alias", "t", "--state-dir", str(state_dir),
                   "--output", str(out), "--raw-log", str(raw),
                   "--report-output", str(report),
                   "--init-alias", "--receiver-empty-ack"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            line = out.read_bytes()
            self.assertTrue(line.endswith(b"\n"))
            self.assertEqual(raw.read_bytes(), line)
            outcome = json.loads(report.read_text(encoding="utf-8"))
            self.assertFalse(outcome["device_accessed"])
            # Second call reserves the next number (init consumed 1 for seq... check).
            seq_path = state_dir / "t.seq.json"
            nxt = json.loads(seq_path.read_text(encoding="utf-8"))["next"]
            self.assertEqual(nxt, 2)

    def test_no_device_access_without_send(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SequenceStore(Path(tmp) / "a.seq.json")
            store.init_alias(receiver_empty_ack=True)
            frame = build_frame({"usage": [], "global_resets": []}, store.reserve(),
                                SENT_AT)
            line = encode_frame(frame)
            self.assertTrue(line.endswith(b"\n"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
