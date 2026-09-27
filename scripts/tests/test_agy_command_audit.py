import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import benchmark


class CommandAuditTests(unittest.TestCase):
    def audit(self, tools):
        events = [{"event": "init", "init": {"permission_mode": "request-review"}}]
        events.extend({"event": "step_update", "step_update": t} for t in tools)
        events.append({"event": "result", "result": {"status": "SUCCESS", "num_turns": 1}})
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "stdout.jsonl"
            path.write_text("\n".join(json.dumps(e) for e in events))
            return benchmark.antigravity_command_audit(path), benchmark.command_metrics(path, "antigravity")

    def step(self, index, **info):
        return {"step_index": index, "state": "DONE", "step_type": "tool",
                "tool_name": "run_command", "tool_info": {"name": "run_command", **info}}

    def test_done_with_build_error_is_unknown_without_exit_status(self):
        audit, metrics = self.audit([self.step(1, output="ninja: build stopped: subcommand failed.")])
        self.assertIsNone(metrics["failed_commands"])
        self.assertEqual(audit["unknown_exit_commands"], 1)
        self.assertEqual(audit["failed_commands_lower_bound"], 0)

    def test_denials_retained_as_lower_bound_beside_unknown_done(self):
        audit, metrics = self.audit([self.step(1, output="OK"),
                                    self.step(2, error={"type": "PermissionDenied"})])
        self.assertIsNone(metrics["failed_commands"])
        self.assertEqual(audit["failed_commands_lower_bound"], 1)
        self.assertEqual(metrics["tool_calls"], 2)

    def test_explicit_exit_codes_count_and_duplicate_step_deduplicates(self):
        success = self.step(1, exit_code=0)
        audit, metrics = self.audit([success, success, self.step(2, exit_code=2)])
        self.assertEqual(metrics, {"tool_calls": 2, "failed_commands": 1})
        self.assertEqual(audit["unknown_exit_commands"], 0)

    def test_boolean_exit_and_output_claim_do_not_establish_success(self):
        audit, metrics = self.audit([self.step(1, exit_code=False, output="exit_code: 0")])
        self.assertIsNone(metrics["failed_commands"])
        self.assertEqual(audit["unknown_exit_commands"], 1)

    def test_file_denial_is_not_a_shell_command_failure(self):
        step = self.step(1, error={"type": "PermissionDenied"})
        step["tool_name"] = step["tool_info"]["name"] = "view_file"
        audit, metrics = self.audit([step])
        self.assertEqual(metrics, {"tool_calls": 1, "failed_commands": 0})
        self.assertEqual(audit["command_count"], 0)
