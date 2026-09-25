import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agy_pilot_environment import read_policy, scoped_environment, sha, verify_scoped_environment


class AgyPilotEnvironmentTests(unittest.TestCase):
    def fixture(self, root):
        gemini = root / ".gemini"
        settings = gemini / "antigravity-cli" / "settings.json"
        instructions = gemini / "GEMINI.md"
        hooks = gemini / "config" / "hooks.json"
        for path in (settings, instructions, hooks):
            path.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(json.dumps({"permissions": {"allow": ["command(*)"]},
                                        "allowNonWorkspaceAccess": True}), encoding="utf-8")
        instructions.write_text("private instruction\n", encoding="utf-8")
        hooks.write_text('{"Stop": []}\n', encoding="utf-8")
        policy = root / "policy.json"
        policy.write_text(json.dumps({"policy_version": 1,
                                      "allow": ["command(git status)", "command(idf.py build)"]}),
                          encoding="utf-8")
        return gemini, settings, instructions, hooks, policy

    def test_scope_narrows_and_restores_original_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            originals = {p: p.read_bytes() for p in (settings, instructions, hooks)}
            backup = root / "backup"
            with scoped_environment(gemini, policy, backup) as identity:
                active = json.loads(settings.read_text(encoding="utf-8"))
                self.assertEqual(active["permissions"]["allow"],
                                 ["command(git status)", "command(idf.py build)"])
                self.assertFalse(active["allowNonWorkspaceAccess"])
                self.assertEqual(active["toolPermission"], "request-review")
                self.assertFalse(instructions.exists())
                self.assertFalse(hooks.exists())
                self.assertEqual(identity["settings_sha256"], sha(settings.read_bytes()))
                self.assertTrue((backup / "active.json").exists())
                self.assertEqual(verify_scoped_environment(gemini, policy), identity["settings_sha256"])
            for path, original in originals.items():
                self.assertEqual(path.read_bytes(), original)
            self.assertFalse((backup / "active.json").exists())
            with self.assertRaises(ValueError):
                verify_scoped_environment(gemini, policy)

    def test_exception_restores_originals(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            originals = {p: p.read_bytes() for p in (settings, instructions, hooks)}
            with self.assertRaisesRegex(RuntimeError, "injected"):
                with scoped_environment(gemini, policy, root / "backup"):
                    raise RuntimeError("injected")
            for path, original in originals.items():
                self.assertEqual(path.read_bytes(), original)

    def test_cli_sparse_persistence_of_defaults_still_restores(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            original = settings.read_bytes()
            with scoped_environment(gemini, policy, root / "backup"):
                active = json.loads(settings.read_text(encoding="utf-8"))
                del active["allowNonWorkspaceAccess"]
                del active["toolPermission"]
                settings.write_text(json.dumps(active), encoding="utf-8")
                verify_scoped_environment(gemini, policy)
            self.assertEqual(settings.read_bytes(), original)

    def test_rejects_unscoped_command_and_custom_skill(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            policy.write_text(json.dumps({"policy_version": 1, "allow": ["command(*)"]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                read_policy(policy)
            policy.write_text(json.dumps({"policy_version": 1, "allow": ["command(git status)"]}),
                              encoding="utf-8")
            skill = gemini / "antigravity-cli" / "skills" / "custom"
            skill.mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "custom AGY skills"):
                with scoped_environment(gemini, policy, root / "backup"):
                    pass
            self.assertTrue(settings.exists())
            self.assertTrue(instructions.exists())
            self.assertTrue(hooks.exists())


if __name__ == "__main__":
    unittest.main()
