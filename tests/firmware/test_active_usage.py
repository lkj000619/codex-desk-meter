"""Current usage collection and scoped last-good behavior in production C."""
import json
import unittest
import zlib

from test_cdm import STAMP, frame, quota, run_wire, session


def raw_frame(sequence, records):
    """Valid canonical wire envelope without the PC sender's semantic preflight."""
    unsigned = {"protocol": "cdm/1", "sequence": sequence, "sent_at": STAMP,
                "payload": {"usage": records, "global_resets": []}}
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"),
                                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    wire = {**unsigned, "integrity": {"algorithm": "crc32",
                                    "value": f"{zlib.crc32(canonical(unsigned)):08X}"}}
    return canonical(wire) + b"\n"


class ActiveUsageTests(unittest.TestCase):
    def test_selected_session_replaces_previous_active_session(self):
        out = run_wire((frame(1, [session("selected-A")], []), 1000, None),
                       (frame(2, [session("selected-B")], []), 2000, None))
        self.assertEqual([row["accepted"] for row in out], [True, True])
        self.assertEqual([entry["key"] for entry in out[1]["usage"]], ["selected-B"])
        self.assertEqual(out[1]["usage"][0]["good"]["snapshot_id"], "selected-B")

    def test_same_snapshot_id_in_distinct_scopes_coexists(self):
        first = session("shared")
        second = quota("shared")
        third = quota("shared")
        third["provider_id"] = "other-provider"
        third["account_profile_id"] = "acct-other"
        result = run_wire((raw_frame(1, [first, second, third]), 1000, None))[0]
        self.assertTrue(result["accepted"], result["error"])
        self.assertEqual(len(result["usage"]), 3)
        self.assertEqual({entry["current"]["provider_id"] for entry in result["usage"]},
                         {"codex", "other-provider"})
        self.assertEqual({entry["current"]["metric_kind"] for entry in result["usage"]},
                         {"session_telemetry", "quota_window"})

    def test_full_scope_duplicate_rejects_without_changing_current_state(self):
        good = raw_frame(1, [session("selected-A")])
        bad = raw_frame(2, [session("selected-B"), session("selected-B")])
        out = run_wire((good, 1000, None), (bad, 2000, None))
        self.assertEqual([row["accepted"] for row in out], [True, False])
        self.assertEqual(out[1]["error"], "SNAPSHOT_DUPLICATE")
        self.assertEqual(out[1]["sequence"], 1)
        self.assertEqual([entry["key"] for entry in out[1]["usage"]], ["selected-A"])

    def test_changing_observation_ids_does_not_accumulate_history(self):
        events = [(raw_frame(i, [quota(f"observation-{i}")]), i * 1000, None)
                  for i in range(1, 21)]
        out = run_wire(*events)
        self.assertTrue(all(row["accepted"] for row in out))
        self.assertTrue(all(len(row["usage"]) == 1 for row in out))
        self.assertEqual(out[-1]["usage"][0]["key"], "observation-20")

    def test_single_non_session_source_keeps_good_across_observation_id_change(self):
        old = quota("observed-1")
        failed = quota("observed-2", status="error")
        unknown = quota("observed-3", status="unavailable")
        recovered = quota("observed-4")
        out = run_wire((raw_frame(1, [old]), 1000, None),
                       (raw_frame(2, [failed]), 2000, None),
                       (raw_frame(3, [unknown]), 3000, None),
                       (raw_frame(4, [recovered]), 4000, None))
        self.assertTrue(all(row["accepted"] for row in out))
        self.assertTrue(all(len(row["usage"]) == 1 for row in out))
        self.assertEqual(out[1]["usage"][0]["key"], "observed-2")
        self.assertEqual(out[1]["usage"][0]["good"]["snapshot_id"], "observed-1")
        self.assertEqual(out[2]["usage"][0]["good"]["snapshot_id"], "observed-1")
        self.assertEqual(out[3]["usage"][0]["good"]["snapshot_id"], "observed-4")

    def test_ambiguous_non_session_context_never_guesses_good(self):
        prior = [quota("observed-A"), quota("observed-B")]
        current = [quota("observed-A", status="error"),
                   quota("observed-C", status="error")]
        out = run_wire((raw_frame(1, prior), 1000, None),
                       (raw_frame(2, current), 2000, None))
        self.assertEqual([row["accepted"] for row in out], [True, True])
        self.assertEqual([row["key"] for row in out[1]["usage"]],
                         ["observed-A", "observed-C"])
        self.assertEqual(out[1]["usage"][0]["good"]["snapshot_id"], "observed-A")
        self.assertIsNone(out[1]["usage"][1]["good"])

        # One prior record is still ambiguous when two current records share its context.
        out = run_wire((raw_frame(1, [quota("observed-A")]), 1000, None),
                       (raw_frame(2, [quota("observed-B", status="error"),
                                      quota("observed-C", status="error")]), 2000, None))
        self.assertTrue(out[1]["accepted"], out[1]["error"])
        self.assertTrue(all(row["good"] is None for row in out[1]["usage"]))

    def test_same_session_cache_survives_unknown_error_then_recovers(self):
        old = session("selected-A", observed="2026-10-07T17:05:00Z")
        unknown = session("selected-A", status="unavailable")
        error = session("selected-A", status="error")
        new = session("selected-A")
        out = run_wire((frame(1, [old], []), 1000, None),
                       (frame(2, [unknown], []), 2000, None),
                       (frame(3, [error], []), 3000, None),
                       (frame(4, [new], []), 4000, None))
        self.assertTrue(all(row["accepted"] for row in out))
        self.assertTrue(all(len(row["usage"]) == 1 for row in out))
        self.assertEqual(out[1]["usage"][0]["current"]["status"], "unavailable")
        self.assertEqual(out[2]["usage"][0]["current"]["status"], "error")
        self.assertEqual(out[2]["usage"][0]["good"]["observed_at"], old["observed_at"])
        self.assertEqual(out[3]["usage"][0]["good"]["observed_at"], STAMP)

    def test_equal_id_new_context_does_not_inherit_another_sources_cache(self):
        old = session("shared")
        different = quota("shared", status="error")
        result = run_wire((raw_frame(1, [old]), 1000, None),
                          (raw_frame(2, [different]), 2000, None))[-1]
        self.assertTrue(result["accepted"], result["error"])
        self.assertEqual(len(result["usage"]), 1)
        self.assertEqual(result["usage"][0]["current"]["metric_kind"], "quota_window")
        self.assertIsNone(result["usage"][0]["good"])


if __name__ == "__main__":
    unittest.main()
