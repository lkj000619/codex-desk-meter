from __future__ import annotations

import json
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "pc" / "legacy_adapter.py"


class LegacyAdapterTests(unittest.TestCase):
    def _invoke(self, source: str, events: list[dict]) -> list[dict]:
        completed = subprocess.run(
            [sys.executable, str(ADAPTER)],
            cwd=ROOT,
            input=json.dumps({"source": source, "events": events}, ensure_ascii=False),
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=True,
        )
        return json.loads(completed.stdout)

    def test_fixture_stale_boundary_and_error_recovery_retain_source_values(self):
        body = json.loads((ROOT / "experiments/fixtures/personal-usage.json").read_text(encoding="utf-8"))
        captured = datetime.fromisoformat(body["captured_at"].replace("Z", "+00:00"))
        stamp = lambda seconds: (captured + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")
        bad = dict(body)
        bad["captured_at"] = "not-a-timestamp"
        outputs = self._invoke("fixture", [
            {"now": stamp(0), "body": body, "error": None},
            {"now": stamp(299), "body": body, "error": None},
            {"now": stamp(300), "body": body, "error": None},
            {"now": stamp(301), "body": bad, "error": None},
            {"now": stamp(302), "body": None, "error": "dns"},
            {"now": stamp(303), "body": body, "error": None},
        ])
        self.assertEqual([entry["stale"] for entry in outputs], [False, False, True, True, True, True])
        self.assertEqual(outputs[0]["windows"], body["windows"])
        self.assertEqual(outputs[3]["windows"], body["windows"])
        self.assertEqual(outputs[3]["observed_at"], body["captured_at"])
        self.assertEqual(outputs[3]["error_code"], "TIMESTAMP_INVALID")
        self.assertEqual(outputs[4]["error_code"], "DNS_FAILURE")
        self.assertIsNone(outputs[5]["error_code"])

    def test_global_source_and_prediction_remain_separate(self):
        body = json.loads((ROOT / "experiments/fixtures/codex-resets-history.json").read_text(encoding="utf-8"))
        captured = datetime.fromisoformat(body["captured_at"].replace("Z", "+00:00"))
        now = captured.isoformat().replace("+00:00", "Z")
        output = self._invoke(body["source"], [{"now": now, "body": body, "error": None}])[0]
        self.assertEqual(output["provider"], "codex-resets.com")
        self.assertEqual(output["fetched_at"], body["captured_at"])
        self.assertEqual(output["latest_reset_at"], body["latest_reset_at"])
        self.assertFalse(output["forecast_is_schedule"])


if __name__ == "__main__":
    unittest.main()
