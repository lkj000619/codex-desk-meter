"""Legacy seam test: pc_tools/legacy_adapter.py must satisfy the
scripts/evaluate-product.py contract (freshness 0/299/300, invalid recovery,
dns/tls/http_500 recovery, value preservation)."""
import json
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = [sys.executable, str(ROOT / "pc_tools" / "legacy_adapter.py")]


def at(stamp: str, seconds: int) -> str:
    dt = datetime.fromisoformat(stamp.replace("Z", "+00:00")) + timedelta(seconds=seconds)
    return dt.isoformat().replace("+00:00", "Z")


def run_adapter(source: str, events) -> list:
    payload = json.dumps({"source": source, "events": events})
    proc = subprocess.run(ADAPTER, input=payload, capture_output=True, text=True,
                          timeout=30)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


class LegacyAdapterTest(unittest.TestCase):
    def test_fixture_freshness(self):
        body = json.loads((ROOT / "experiments/fixtures/personal-usage.json").read_text())
        events = [{"now": at(body["captured_at"], n), "body": body, "error": None}
                  for n in (0, 299, 300)]
        out = run_adapter("fixture", events)
        self.assertEqual([o["stale"] for o in out], [False, False, True])
        self.assertEqual(out[0]["windows"], body["windows"])
        self.assertEqual(out[0]["observed_at"], body["captured_at"])

    def test_global_freshness_and_mapping(self):
        body = json.loads((ROOT / "experiments/fixtures/codex-resets-history.json").read_text())
        events = [{"now": at(body["captured_at"], n), "body": body, "error": None}
                  for n in (0, 299, 300)]
        out = run_adapter("codex-resets.com", events)
        # source passes through; mapping uses provider/fetched_at/latest_reset_at
        self.assertEqual([o["stale"] for o in out], [False, False, True])
        self.assertEqual(out[0]["provider"], "codex-resets.com")
        self.assertEqual(out[0]["fetched_at"], body["captured_at"])
        self.assertEqual(out[0]["latest_reset_at"], body["latest_reset_at"])
        self.assertFalse(out[0]["forecast_is_schedule"])

    def test_forecast_mapping(self):
        body = json.loads((ROOT / "experiments/fixtures/codex-reset-forecast.json").read_text())
        events = [{"now": at(body["captured_at"], n), "body": body, "error": None}
                  for n in (0, 299, 300)]
        out = run_adapter("codex-reset.com", events)
        self.assertEqual(out[0]["forecast_24h_percent"], 22)
        self.assertEqual(out[0]["forecast_48h_percent"], 39)
        self.assertFalse(out[0]["forecast_is_schedule"])

    def test_error_recovery(self):
        for filename, source in (("personal-usage.json", "fixture"),
                                 ("codex-reset-forecast.json", "codex-reset.com"),
                                 ("codex-resets-history.json", "codex-resets.com")):
            body = json.loads((ROOT / "experiments/fixtures" / filename).read_text())
            stamp = body["captured_at"]
            for error in ("dns", "tls", "http_500"):
                events = [{"now": at(stamp, 0), "body": body, "error": None},
                          {"now": at(stamp, 1), "body": None, "error": error},
                          {"now": at(stamp, 2), "body": body, "error": None}]
                out = run_adapter(source, events)
                self.assertTrue(out[1]["error_code"], msg=(filename, error))
                self.assertIsNone(out[0]["error_code"], msg=(filename, error))
                self.assertIsNone(out[2]["error_code"], msg=(filename, error))
                if source == "fixture":
                    self.assertEqual(out[1]["windows"], body["windows"])
                else:
                    self.assertEqual(out[1]["fetched_at"], body["captured_at"])

    def test_invalid_recovery(self):
        import copy
        body = json.loads((ROOT / "experiments/fixtures/personal-usage.json").read_text())
        bad = copy.deepcopy(body)
        bad["captured_at"] = "invalid-date"
        events = [{"now": at(body["captured_at"], 0), "body": body, "error": None},
                  {"now": at(body["captured_at"], 1), "body": bad, "error": None},
                  {"now": at(body["captured_at"], 2), "body": body, "error": None}]
        out = run_adapter("fixture", events)
        self.assertTrue(out[1]["error_code"])
        self.assertEqual(out[1]["windows"], body["windows"])
        self.assertIsNone(out[2]["error_code"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
