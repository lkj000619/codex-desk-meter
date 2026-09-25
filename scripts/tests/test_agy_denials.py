import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import benchmark


class DenialRegressionTests(unittest.TestCase):
    def test_error_step_and_terminal_denial_preserve_usage_and_counts(self):
        events = [
            {"event": "init", "init": {"permission_mode": "request-review"}},
            {"event": "step_update", "step_update": {
                "step_index": 2, "state": "ERROR", "step_type": "tool",
                "tool_name": "run_command", "tool_info": {"error": {
                    "type": "TOOL_ERROR", "message": "permission check failed for command dir"}}}},
            {"event": "result", "result": {"status": "SUCCESS", "num_turns": 1,
                "denied_actions": [{"action": "command"}],
                "usage": {"input_tokens": 21, "output_tokens": 8, "total_tokens": 29}}},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stdout.jsonl"
            path.write_text('\n'.join(json.dumps(e) for e in events), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, "permission"):
                benchmark.inspect_antigravity_stream(path)
            self.assertEqual(benchmark.command_metrics(path, 'antigravity'),
                             {'tool_calls': 1, 'failed_commands': 1})
            self.assertEqual(benchmark.telemetry(path, 'antigravity')['total'], 29)
            # Generic TOOL_ERROR message must also be caught without a terminal hint.
            events[-1]['result'].pop('denied_actions')
            path.write_text('\n'.join(json.dumps(e) for e in events), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, "permission"):
                benchmark.inspect_antigravity_stream(path)

    def test_stderr_only_headless_denial(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'stderr.txt'
            path.write_text('jetski: no output produced - headless mode cannot prompt for, so it was auto-denied.', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'permission'):
                benchmark.check_antigravity_stderr(path)
            path.write_text('ordinary diagnostic', encoding='utf-8')
            benchmark.check_antigravity_stderr(path)
