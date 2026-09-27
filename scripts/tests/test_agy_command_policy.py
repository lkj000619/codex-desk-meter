"""Check our declared raw-line allow patterns; real CLI matching needs a smoke run."""
import json
from pathlib import Path
import re
import unittest


class CommandPolicyTests(unittest.TestCase):
    def test_git_index_listing_is_checkout_scoped(self):
        for cmd in ['git ls-files', 'git ls-files docs/', 'git ls-files -- docs/README.md',
                    'git ls-files --others --exclude-standard main']:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.allowed(cmd))
        for cmd in ['git ls-files ../', 'git ls-files C:/Users',
                    'git ls-files docs/; whoami', 'git ls-files --recurse-submodules',
                    'git ls-files --with-tree=HEAD~1']:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.allowed(cmd))

    def allowed(self, command):
        policy = Path(__file__).resolve().parents[2] / 'experiments/config/agy-pilot-permissions.json'
        for rule in json.loads(policy.read_text())['allow']:
            if not rule.startswith('command('):
                continue
            target = rule[len('command('):-1]
            if target.startswith('regex:'):
                if re.fullmatch(target[6:], command):
                    return True
            elif target == command:
                return True
        return False

    def test_declared_build_and_read_commands(self):
        for cmd in ['Get-ChildItem -Force', 'Get-ChildItem . -Recurse -File',
                    'dir docs', 'ls -Force', 'Get-Content README.md -TotalCount 1',
                    'Get-Content -Raw docs/PRODUCT_CONTRACT.md',
                    'git status --short', 'git diff --stat', 'idf.py --version',
                    'idf.py set-target esp32s3', 'idf.py build',
                    'python --version', 'python -m unittest discover -s scripts/tests -v']:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.allowed(cmd))

    def test_local_setup_and_test_command_groups(self):
        for cmd in ['Test-Path docs/agent-runs', 'Test-Path -LiteralPath .\\main',
                    'Get-Item README.md', 'Resolve-Path .',
                    'New-Item -ItemType Directory -Force -Path main',
                    'New-Item -Path smoke.txt -ItemType File', 'mkdir build-host',
                    'Get-FileHash README.md -Algorithm SHA256',
                    'idf.py -B build set-target esp32s3', 'idf.py -B build build',
                    'cmake -S host -B build-host -G Ninja', 'cmake --build build-host',
                    'ctest --test-dir build-host --output-on-failure',
                    'python -m py_compile scripts/collector.py',
                    'python tests/test_parser.py', '.\\build-host\\parser-test.exe']:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.allowed(cmd))

    def test_out_of_scope_commands_do_not_match(self):
        for cmd in ['Get-ChildItem -Force; Remove-Item x', 'dir ..',
                    'Get-Content C:/Users/me/secret', 'Get-Content $HOME/key',
                    'Get-Content docs/../secret', 'git log', 'git show HEAD',
                    'git -c core.pager=evil diff', 'idf.py flash', 'idf.py erase-flash',
                    'python -c "print(1)"', 'python -m unittest; whoami',
                    'python -m unittest $(whoami)', 'Get-ChildItem | iex',
                    'New-Item -Path ../outside -ItemType File', 'Test-Path C:/Users',
                    'cmake -S .. -B build', 'cmake --install build',
                    'python -m pip install anything', 'python scripts/benchmark.py run x']:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.allowed(cmd))

    def test_read_path_arrays_and_bounded_depth(self):
        for cmd in ['Get-ChildItem -Recurse experiments, results, docs -Depth 2',
                    'gci -Path docs,experiments -Depth 0',
                    'Get-ChildItem -LiteralPath "docs", \'experiments\' -Depth 10']:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.allowed(cmd))
        for cmd in ['Get-ChildItem docs, ../outside -Depth 2',
                    'Get-ChildItem docs, C:/Users -Depth 2',
                    'Get-ChildItem docs -Depth 2; whoami',
                    'Get-ChildItem docs -Depth -1',
                    'Get-ChildItem docs, $(whoami)',
                    'Get-ChildItem docs,', 'Get-ChildItem -Depth']:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.allowed(cmd))
