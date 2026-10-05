import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest

from pc.desk_meter import FIXTURES, canonical, collect, frame, reserve_sequence, timestamp, usage_adapter


class ProductPcTests(unittest.TestCase):
    def test_fixture_matrix_contract(self):
        matrix = json.loads((FIXTURES / "provider-fixture-matrix.json").read_text())
        reference = timestamp(matrix["reference_time"])
        for entry in matrix["fixtures"]:
            raw = json.loads((FIXTURES / entry["path"]).read_text())
            snapshots = raw if isinstance(raw, list) else [raw]
            for snapshot in snapshots:
                if entry["expected"] == "invalid":
                    with self.assertRaisesRegex(ValueError, entry["error_code"]):
                        usage_adapter(snapshot, reference)
                else:
                    usage_adapter(snapshot, reference)

    def test_fixture_collection_and_errors(self):
        reference = timestamp("2026-09-10T00:04:59Z")
        matrix = json.loads((FIXTURES / "provider-fixture-matrix.json").read_text())
        payload, errors = collect(reference, fixture_paths=[entry["path"] for entry in matrix["fixtures"]])
        self.assertTrue(payload["usage"])
        self.assertTrue(payload["global_resets"])
        self.assertTrue(any(e["error"] == "ABSOLUTE_BALANCE_MISMATCH" for e in errors))
        self.assertEqual({g["source"] for g in payload["global_resets"]},
                         {"codex-reset.com", "codex-resets.com"})

    def test_legacy_personal_usage_reference(self):
        reference = timestamp("2026-09-30T18:40:49Z")
        payload, errors = collect(reference, fixture_paths=["personal-usage.json"])
        self.assertFalse(errors)
        self.assertEqual([w["percent_remaining"] for w in payload["usage"][0]["windows"]], [58, 82])
        self.assertEqual(payload["usage"][0]["status"], "stale")
        self.assertEqual(payload["usage"][0]["observed_at"], "2026-09-11T00:00:00Z")

    def test_stale_boundary(self):
        raw = json.loads((FIXTURES / "providers/codex-percent-window.json").read_text())
        usage_adapter(raw.copy(), timestamp("2026-09-10T00:04:59Z"))
        with self.assertRaisesRegex(ValueError, "STALE_THRESHOLD_EXCEEDED"):
            usage_adapter(raw.copy(), timestamp("2026-09-10T00:05:00Z"))

    def test_collector_last_good_error_and_recovery(self):
        reference = timestamp("2026-09-10T00:04:59Z")
        healthy = (FIXTURES / "providers/codex-percent-window.json").read_text(encoding="utf-8")
        global_reset = (FIXTURES / "codex-resets-history.json").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "provider-fixture-matrix.json").write_text('{"fixtures":[]}', encoding="utf-8")
            (root / "codex-resets-history.json").write_text(global_reset, encoding="utf-8")
            source = root / "current.json"
            source.write_text(healthy, encoding="utf-8")
            cache = {}
            first, errors = collect(reference, root, fixture_paths=["current.json"], cache=cache)
            self.assertFalse(errors)
            source.write_text("{broken", encoding="utf-8")
            failed, errors = collect(reference, root, fixture_paths=["current.json"], cache=cache)
            self.assertTrue(errors)
            self.assertEqual(failed["usage"][0]["status"], "error")
            self.assertEqual(failed["usage"][0]["observed_at"], first["usage"][0]["observed_at"])
            source.write_text(healthy, encoding="utf-8")
            recovered, errors = collect(reference, root, fixture_paths=["current.json"], cache=cache)
            self.assertFalse(errors)
            self.assertEqual(recovered["usage"][0]["status"], "available")

    def test_frame_and_persistent_reservation(self):
        data = frame(7, {"usage": [], "global_resets": []}, "2026-09-10T00:00:00Z")
        self.assertEqual(data[-1:], b"\n")
        self.assertEqual(data.count(b"\n"), 1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sender.json"
            with self.assertRaisesRegex(ValueError, "SENDER_STATE_MISSING"):
                reserve_sequence(path, "meter")
            self.assertEqual(reserve_sequence(path, "meter", True), 0)
            self.assertEqual(reserve_sequence(path, "meter"), 1)
            with self.assertRaisesRegex(ValueError, "CORRUPT"):
                reserve_sequence(path, "other")


if __name__ == "__main__":
    unittest.main()
