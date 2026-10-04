import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agy_pilot_environment import read_policy, restore, scoped_environment, sha, verify_scoped_environment


class AgyPilotEnvironmentTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows process-tree interruption regression')
    def test_wrapper_interrupt_stops_grandchild_before_restoring_globals(self):
        self.interrupt_wrapper()

    @unittest.skipUnless(os.name == 'nt', 'Windows process-tree interruption regression')
    def test_failed_tree_cleanup_keeps_scope_for_manual_recovery(self):
        self.interrupt_wrapper(cleanup_failure=True)

    def interrupt_wrapper(self, *, cleanup_failure=False):
        import ctypes
        import agy_pilot_environment as pilot

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            original = settings.read_bytes()
            ready = root / 'grandchild.pid'
            grandchild = "import time; time.sleep(60)"
            child_code = ("import subprocess,sys,time; from pathlib import Path; "
                          "p=subprocess.Popen([sys.executable, '-c', sys.argv[2]]); "
                          "Path(sys.argv[1]).write_text(str(p.pid)); time.sleep(60)")
            command = [sys.executable, '-c', child_code, str(ready), grandchild]
            wait, run = subprocess.Popen.wait, subprocess.run
            interrupted = False
            process_handle = None
            child_process = None
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.OpenProcess.restype = ctypes.c_void_p
            kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
            kernel.CloseHandle.argtypes = [ctypes.c_void_p]

            def interrupt_wait(process, *args, **kwargs):
                nonlocal interrupted, process_handle, child_process
                if process.args == command and not interrupted:
                    child_process = process
                    deadline = time.monotonic() + 10
                    while not ready.exists() and time.monotonic() < deadline:
                        time.sleep(.01)
                    self.assertTrue(ready.exists(), 'temporary grandchild did not start')
                    process_handle = kernel.OpenProcess(0x00100000, False, int(ready.read_text()))
                    self.assertTrue(process_handle)
                    interrupted = True
                    raise KeyboardInterrupt
                return wait(process, *args, **kwargs)

            def controlled_probe(args, *values, **kwargs):
                if args[0] == 'powershell':
                    return subprocess.CompletedProcess(args, 0, '0\n', '')
                if args[0] == 'taskkill' and cleanup_failure:
                    return subprocess.CompletedProcess(args, 1, '', 'injected cleanup failure')
                return run(args, *values, **kwargs)

            argv = ['agy_pilot_environment.py', '--gemini-root', str(gemini), '--policy', str(policy),
                    '--backup-dir', str(root / 'backup'), 'run', '--', *command]
            try:
                with patch.object(sys, 'argv', argv), patch.object(subprocess.Popen, 'wait', interrupt_wait), \
                        patch.object(subprocess, 'run', controlled_probe):
                    with self.assertRaises(BaseException) as raised:
                        pilot.main()
                self.assertIsInstance(raised.exception, RuntimeError if cleanup_failure else KeyboardInterrupt)
                if cleanup_failure:
                    self.assertNotEqual(settings.read_bytes(), original)
                    self.assertTrue((root / 'backup/active.json').exists())
                    with self.assertRaisesRegex(ValueError, 'active|restore'):
                        with scoped_environment(gemini, policy, root / 'retry'):
                            pass
                else:
                    self.assertEqual(kernel.WaitForSingleObject(process_handle, 1000), 0,
                                     'grandchild is still running after global settings were restored')
                    self.assertEqual(settings.read_bytes(), original)
            finally:
                if child_process is not None and child_process.poll() is None:
                    run(['taskkill', '/PID', str(child_process.pid), '/T', '/F'], capture_output=True)
                    wait(child_process, timeout=10)
                if process_handle:
                    if kernel.WaitForSingleObject(process_handle, 0) != 0:
                        run(['taskkill', '/PID', ready.read_text(), '/T', '/F'], capture_output=True)
                    kernel.CloseHandle(process_handle)
            if cleanup_failure:
                restore(root / 'backup')
                self.assertEqual(settings.read_bytes(), original)

    def start_scope_process(self, gemini, policy, backup, *, interrupt_setup=False):
        code = """
import os
import sys
from pathlib import Path
import agy_pilot_environment as pilot
if sys.argv[4] == 'interrupt-setup':
    original_write = pilot.write_atomic
    def interrupted_write(path, data):
        original_write(path, data)
        if path.name == 'settings.json':
            print('ready', flush=True)
            os._exit(7)
    pilot.write_atomic = interrupted_write
with pilot.scoped_environment(*map(Path, sys.argv[1:4])) as identity:
    print('ready ' + identity.get('lock_token', ''), flush=True)
    sys.stdin.readline()
"""
        child = subprocess.Popen(
            [sys.executable, '-c', code, str(gemini), str(policy), str(backup),
             'interrupt-setup' if interrupt_setup else 'normal'],
            cwd=Path(__file__).resolve().parents[1],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True,
        )
        self.addCleanup(self.stop_scope_process, child)
        ready = child.stdout.readline().strip().split()
        self.assertEqual(ready[0] if ready else '', 'ready')
        child.scope_token = ready[1] if len(ready) > 1 else ''
        return child

    @staticmethod
    def stop_scope_process(child):
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=10)

    def test_different_backup_cannot_overlap_or_release_winners_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            originals = {p: p.read_bytes() for p in (settings, instructions, hooks)}
            with scoped_environment(gemini, policy, root / 'winner'):
                active = settings.read_bytes()
                for backup in ('loser', 'another-loser'):
                    with self.assertRaisesRegex(ValueError, 'lock|active'):
                        with scoped_environment(gemini, policy, root / backup):
                            pass
                    self.assertEqual(settings.read_bytes(), active)
                    self.assertFalse((root / backup / 'active.json').exists())
                verify_scoped_environment(gemini, policy)
            for path, original in originals.items():
                self.assertEqual(path.read_bytes(), original)

    def test_live_owner_blocks_other_process_restore_even_with_force(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            child = self.start_scope_process(gemini, policy, root / 'backup')
            try:
                active = settings.read_bytes()
                with self.assertRaisesRegex(ValueError, 'lock|active'):
                    restore(root / 'backup', force=True)
                self.assertEqual(settings.read_bytes(), active)
                with self.assertRaisesRegex(ValueError, 'lock|owner'):
                    verify_scoped_environment(gemini, policy)
                with self.assertRaisesRegex(ValueError, 'lock|active'):
                    with scoped_environment(gemini, policy, root / 'other-backup'):
                        pass
            finally:
                child.communicate('\n', timeout=10)
            self.assertEqual(child.returncode, 0)

    def test_interrupted_owner_requires_matching_manual_restore(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            originals = {p: p.read_bytes() for p in (settings, instructions, hooks)}
            backup = root / 'backup'
            child = self.start_scope_process(gemini, policy, backup)
            self.stop_scope_process(child)
            with self.assertRaisesRegex(ValueError, 'restore|active'):
                with scoped_environment(gemini, policy, root / 'new-backup'):
                    pass
            shutil.copytree(backup, root / 'wrong-backup')
            with self.assertRaisesRegex(ValueError, 'owner|backup'):
                restore(root / 'wrong-backup', force=True)
            restore(backup)
            for path, original in originals.items():
                self.assertEqual(path.read_bytes(), original)
            with scoped_environment(gemini, policy, root / 'new-backup'):
                verify_scoped_environment(gemini, policy)

    def test_invalid_setup_releases_lock_for_next_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            original = settings.read_bytes()
            settings.write_bytes(b'invalid json')
            with self.assertRaises(ValueError):
                with scoped_environment(gemini, policy, root / 'backup'):
                    pass
            settings.write_bytes(original)
            with scoped_environment(gemini, policy, root / 'retry'):
                verify_scoped_environment(gemini, policy)

    def test_interruption_during_setup_can_restore_without_force(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            originals = {p: p.read_bytes() for p in (settings, instructions, hooks)}
            backup = root / 'backup'
            child = self.start_scope_process(gemini, policy, backup, interrupt_setup=True)
            child.communicate(timeout=10)
            self.assertEqual(child.returncode, 7)
            restore(backup)
            for path, original in originals.items():
                self.assertEqual(path.read_bytes(), original)

    def test_inherited_verification_token_requires_live_owner(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            child = self.start_scope_process(gemini, policy, root / 'backup')
            try:
                with patch.dict(os.environ, {'AGY_PILOT_LOCK_TOKEN': child.scope_token}):
                    verify_scoped_environment(gemini, policy)
                    self.stop_scope_process(child)
                    with self.assertRaisesRegex(ValueError, 'lock|owner'):
                        verify_scoped_environment(gemini, policy)
                restore(root / 'backup')
            finally:
                self.stop_scope_process(child)

    def test_corrupt_backup_does_not_partially_restore_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            backup = root / 'backup'
            child = self.start_scope_process(gemini, policy, backup)
            self.stop_scope_process(child)
            active = settings.read_bytes()
            (backup / 'hooks.original').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'backup hash'):
                restore(backup, force=True)
            self.assertEqual(settings.read_bytes(), active)
            self.assertFalse(instructions.exists())

    def test_failed_restore_keeps_owner_until_explicit_force_recovery(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            originals = {p: p.read_bytes() for p in (settings, instructions, hooks)}
            backup = root / 'backup'
            with self.assertRaisesRegex(ValueError, 'appeared'):
                with scoped_environment(gemini, policy, backup):
                    instructions.write_bytes(b'unexpected edit')
            with self.assertRaisesRegex(ValueError, 'restore|active'):
                with scoped_environment(gemini, policy, root / 'retry'):
                    pass
            restore(backup, force=True)
            for path, original in originals.items():
                self.assertEqual(path.read_bytes(), original)

    def test_setup_write_failure_restores_and_releases_lock(self):
        import agy_pilot_environment as pilot

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            originals = {p: p.read_bytes() for p in (settings, instructions, hooks)}
            write_atomic = pilot.write_atomic
            failed = False

            def fail_after_write(path, data):
                nonlocal failed
                write_atomic(path, data)
                if path == settings and not failed:
                    failed = True
                    raise OSError('injected write failure')

            with patch.object(pilot, 'write_atomic', fail_after_write):
                with self.assertRaisesRegex(OSError, 'injected'):
                    with scoped_environment(gemini, policy, root / 'backup'):
                        pass
            for path, original in originals.items():
                self.assertEqual(path.read_bytes(), original)
            with scoped_environment(gemini, policy, root / 'retry'):
                verify_scoped_environment(gemini, policy)

    def test_manual_restore_finishes_interrupted_journal_cleanup(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            originals = {p: p.read_bytes() for p in (settings, instructions, hooks)}
            backup = root / 'backup'
            unlink = Path.unlink

            def interrupt_manifest_cleanup(path, *args, **kwargs):
                if path == backup / 'active.json':
                    raise OSError('interrupted cleanup')
                return unlink(path, *args, **kwargs)

            with patch.object(Path, 'unlink', interrupt_manifest_cleanup):
                with self.assertRaisesRegex(OSError, 'interrupted cleanup'):
                    with scoped_environment(gemini, policy, backup):
                        pass
            restore(backup)
            self.assertFalse((backup / 'active.json').exists())
            for path, original in originals.items():
                self.assertEqual(path.read_bytes(), original)

    def test_owner_journal_write_failure_does_not_orphan_lock(self):
        import agy_pilot_environment as pilot

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            original = settings.read_bytes()
            write_atomic = pilot.write_atomic

            def fail_after_owner_publication(path, data):
                write_atomic(path, data)
                if path.name == '.agy-pilot-owner.json':
                    raise OSError('owner publication interrupted')

            with patch.object(pilot, 'write_atomic', fail_after_owner_publication):
                with self.assertRaisesRegex(OSError, 'publication interrupted'):
                    with scoped_environment(gemini, policy, root / 'backup'):
                        pass
            self.assertEqual(settings.read_bytes(), original)
            with scoped_environment(gemini, policy, root / 'retry'):
                verify_scoped_environment(gemini, policy)

    def test_legacy_backup_restores_only_when_global_root_is_unowned(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            originals = {p: p.read_bytes() for p in (settings, instructions, hooks)}
            backup = root / 'backup'
            child = self.start_scope_process(gemini, policy, backup)
            self.stop_scope_process(child)
            manifest_path = backup / 'active.json'
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            del manifest['lock']
            manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'owner'):
                restore(backup, force=True)
            (gemini / '.agy-pilot-owner.json').unlink()
            restore(backup)
            for path, original in originals.items():
                self.assertEqual(path.read_bytes(), original)

    def test_workspace_write_grant_is_exact_and_verified(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            gemini, settings, instructions, hooks, policy = self.fixture(root)
            workspace = root / 'checkout'
            workspace.mkdir()
            original = settings.read_bytes()
            with scoped_environment(gemini, policy, root / 'backup', workspace=workspace):
                active = json.loads(settings.read_text(encoding="utf-8"))
                self.assertIn('write_file(' + workspace.resolve().as_posix() + ')',
                              active['permissions']['allow'])
                verify_scoped_environment(gemini, policy, workspace=workspace)
                with self.assertRaisesRegex(ValueError, 'scope|allow list'):
                    verify_scoped_environment(gemini, policy, workspace=root / 'another-run')
                with self.assertRaisesRegex(ValueError, 'scope|allow list'):
                    verify_scoped_environment(gemini, policy)
            self.assertEqual(settings.read_bytes(), original)

    def test_only_declared_sdk_and_manufacturer_read_roots(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'policy.json'
            for rule, accepted in [
                ('read_file(C:/Espressif/v5.3.2/esp-idf)', True),
                ('read_file(C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16/source)', True),
                ('read_file(*)', False), ('write_file(C:/Espressif)', False),
                ('read_file(C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16/backup)', False),
            ]:
                path.write_text(json.dumps({'policy_version': 1, 'allow': [rule]}))
                with self.subTest(rule=rule):
                    if accepted:
                        self.assertEqual(read_policy(path), [rule])
                    else:
                        with self.assertRaises(ValueError):
                            read_policy(path)

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
