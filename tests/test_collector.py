"""Collector/normalizer tests: fixture matrix expectations, error codes,
global wire mapping, and last-good preservation (no invented values)."""
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pc_tools"))

from collector import (  # noqa: E402
    check_snapshot,
    collect_globals,
    collect_legacy_personal_usage,
    collect_providers,
    normalize_global_reset,
    parse_ts,
)

REFERENCE = datetime(2026, 9, 10, 0, 4, 59, tzinfo=timezone.utc)


class CollectorTest(unittest.TestCase):
    def test_matrix_expectations(self):
        matrix = json.loads((ROOT / "experiments/fixtures/provider-fixture-matrix.json").read_text())
        ref = parse_ts(matrix["reference_time"], "reference_time")
        for entry in matrix["fixtures"]:
            path = ROOT / "experiments/fixtures" / entry["path"]
            value = json.loads(path.read_text(encoding="utf-8-sig"))
            entries = value if isinstance(value, list) else [value]
            codes = {check_snapshot(e, ref) for e in entries}
            if entry["expected"] == "valid":
                # valid fixtures: semantic check passes; carried error_code matches
                for e in entries:
                    code = check_snapshot(e, ref)
                    self.assertEqual(code, None if entry["error_code"] is None else code,
                                     msg=entry["path"])
                    if entry["error_code"] is None:
                        self.assertIsNone(code, msg=entry["path"])
                    else:
                        self.assertEqual(e.get("error_code"), entry["error_code"],
                                         msg=entry["path"])
            else:
                self.assertTrue(any(c == entry["error_code"] for c in codes),
                                msg=f'{entry["path"]}: got {codes}')

    def test_default_registry_collects_without_abort(self):
        snaps, fails = collect_providers(
            ["codex-percent-window.json", "provider-error.json",
             "gemini-cli-unsupported.json"], REFERENCE)
        self.assertEqual(len(snaps), 3)  # error entries preserved, not dropped
        self.assertEqual(fails, [])
        by_id = {s["provider_id"]: s for s in snaps}
        self.assertEqual(by_id["openai"]["status"], "available")
        self.assertEqual(by_id["google"]["status"] in ("error", "unsupported"), True)

    def test_windows_preserved_verbatim(self):
        snaps, _ = collect_providers(["codex-percent-window.json"], REFERENCE)
        self.assertEqual(snaps[0]["windows"][0]["percent_used"], 20)
        self.assertEqual(snaps[0]["observed_at"], "2026-09-10T00:00:00Z")

    def test_global_wire_mapping(self):
        resets, fails = collect_globals(
            ["codex-reset-forecast.json", "codex-resets-history.json"])
        self.assertEqual(fails, [])
        self.assertEqual(len(resets), 2)
        compat = next(r for r in resets if r["source"] == "codex-reset.com")
        shown = next(r for r in resets if r["source"] == "codex-resets.com")
        self.assertEqual(compat["forecast_24h_percent"], 22)
        self.assertFalse(compat["forecast_is_schedule"])
        self.assertEqual(shown["latest_reset_at"], "2026-09-08T01:56:00Z")
        # Screen shows only the second source.
        self.assertNotEqual(compat["source"], shown["source"])

    def test_global_null_captured_at_rejected(self):
        with self.assertRaises(Exception):
            normalize_global_reset({"source": "x", "captured_at": None})

    def test_no_credentials_in_fixtures(self):
        import re
        key_pattern = re.compile(r'"[^"]*(api[_-]?key|password|cookie|bearer|session[_-]?token)[^"]*"\s*:',
                                 re.IGNORECASE)
        for path in (ROOT / "experiments/fixtures").rglob("*.json"):
            text = path.read_text(encoding="utf-8-sig")
            self.assertIsNone(key_pattern.search(text), msg=str(path))

    def test_legacy_personal_usage_maps_to_valid_snapshot(self):
        ref = datetime(2026, 9, 11, 0, 4, 59, tzinfo=timezone.utc)
        snap = collect_legacy_personal_usage("personal-usage.json", ref)
        self.assertIsNone(check_snapshot(snap, ref))
        self.assertEqual(snap["observed_at"], "2026-09-11T00:00:00Z")
        by_id = {w["window_id"]: w for w in snap["windows"]}
        self.assertEqual(by_id["five-hour"]["percent_remaining"], 58)
        self.assertEqual(by_id["weekly"]["percent_remaining"], 82)
        self.assertEqual(by_id["five-hour"]["percent_used"], 42)
        self.assertEqual(by_id["weekly"]["percent_used"], 18)
        # Identity scaffolding is fixed; values are verbatim from the fixture.
        self.assertEqual(snap["provider_id"], "fixture")
        self.assertEqual(snap["status"], "available")


if __name__ == "__main__":
    unittest.main(verbosity=2)
