import os
from pathlib import Path
import subprocess
import unittest


@unittest.skipUnless(os.name == 'nt' and Path('C:/Espressif/user-tools').exists(),
                     'requires the pinned Windows IDF installation')
class IdfChildShellTests(unittest.TestCase):
    def test_activation_reaches_fresh_child_powershell(self):
        root = Path(__file__).resolve().parents[2]
        result = subprocess.run([
            'powershell', '-NoProfile', '-Command',
            ". ./scripts/activate-idf.ps1; powershell -NoProfile -Command 'idf.py --version'"
        ], cwd=root, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip().splitlines()[-1], 'ESP-IDF v5.3.2')
