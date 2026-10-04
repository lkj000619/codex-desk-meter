"""Regression for the next comparison's declared native permission mapping.

These are configuration tests; actual CLI capability evidence is separate.
"""
import ast
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def permission_config():
    profile = json.loads((ROOT / 'experiments/config/next-profiles-20261003/opencode-muse.json').read_text(encoding='utf-8'))
    tree = ast.parse(profile['argv'][2])
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'update':
            env = ast.literal_eval(node.args[0])
            return json.loads(env['OPENCODE_CONFIG_CONTENT'])['permission']
    raise AssertionError('embedded environment not found')


def matched(rules, value):
    if isinstance(rules, str):
        return rules
    action = 'deny'
    for pattern, current in rules.items():
        pattern = re.escape(pattern).replace(r'\*', '.*').replace(r'\?', '.')
        if re.fullmatch(pattern, value, re.DOTALL):
            action = current
    return action


class NextPermissionsTests(unittest.TestCase):
    def test_documented_compile_and_working_diff_are_allowed(self):
        rules = permission_config()['bash']
        for command in ('python -m py_compile scripts/check.py', 'git diff', 'git diff --stat',
                        'git diff -- components/foo.c', 'git diff --check'):
            with self.subTest(command=command):
                self.assertEqual(matched(rules, command), 'allow')

    def test_reference_reads_and_external_compile_are_denied(self):
        rules = permission_config()['bash']
        for command in ('git diff HEAD~1', 'git diff --stat HEAD', 'git log -n 1',
                        'git show HEAD', 'python -m py_compile ../outside.py',
                        'python -m py_compile C:/Espressif/vendor/file.py',
                        'python -m py_compile scripts/check.py /outside.py',
                        'python -m py_compile scripts/check.py\t/outside.py',
                        'python -m py_compile scripts/check.py \\outside.py'):
            with self.subTest(command=command):
                self.assertEqual(matched(rules, command), 'deny')

    def test_sdk_vendor_are_readable_but_not_editable(self):
        rules = permission_config()
        for path in ('C:/Espressif/v5.3.2/esp-idf/tools/idf.py',
                     'C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16/source/file.c'):
            with self.subTest(path=path):
                self.assertEqual(matched(rules['external_directory'], path), 'allow')
                self.assertEqual(matched(rules['edit'], path), 'deny')
        self.assertEqual(matched(rules['edit'], 'main/main.c'), 'allow')


if __name__ == '__main__':
    unittest.main()
