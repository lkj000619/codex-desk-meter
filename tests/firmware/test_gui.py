"""Pixel checks of the production GUI linked to the production C receiver."""
import copy
import json
import subprocess
import unittest
from pathlib import Path

from test_cdm import EXE, ROOT, STAMP, frame, quota, session, global_reset

OUT = ROOT / "tests/firmware/.build"
HEADER = b"P6\n820 320\n255\n"


def region(path: Path, x: int, y: int, width: int, height: int) -> bytes:
    raw = path.read_bytes()
    assert raw.startswith(HEADER) and len(raw) == len(HEADER) + 820 * 320 * 3
    image = raw[len(HEADER):]
    return b"".join(image[(row * 820 + x) * 3:(row * 820 + x + width) * 3]
                    for row in range(y, y + height))


def run_render(events):
    request = {"events": [dict(line_hex=raw.hex(), mono_ms=1000 + n * 1000,
                               render=True, ppm_prefix=f"tests/firmware/.build/gui-{n}")
                          for n, raw in enumerate(events)]}
    result = subprocess.run([str(EXE), "--wire"], input=json.dumps(request), text=True,
                            cwd=ROOT, capture_output=True, check=True)
    return json.loads(result.stdout)


class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not EXE.exists():
            raise RuntimeError("Run tests/firmware/build-host.ps1 first")

    def test_pages_screen_wrap_and_source_separation(self):
        q = quota()
        base = q["windows"][0]
        q["windows"] = [dict(base, window_id=f"window-{i}-3600s", label=f"{i + 1} hour",
                             percent_used=10 * (i + 1), percent_remaining=90 - 10 * i)
                        for i in range(6)]
        first = frame(1, [session(), q], [global_reset()])
        changed = session()
        changed["windows"][0]["used_units"] = 124801
        changed["windows"][5]["used_units"] = 141201
        second = frame(2, [changed, q], [global_reset()])
        out = run_render([first, second])
        self.assertEqual([row["accepted"] for row in out], [True, True])
        self.assertEqual(out[0]["render"]["quota_count"], 6)
        self.assertEqual(len(out[0]["render"]["usage_pages"]), 3)
        self.assertEqual(len(set(out[0]["render"]["usage_pages"])), 3)
        self.assertTrue(out[0]["render"]["screen_wrap"])
        self.assertNotEqual(out[0]["render"]["global"], out[0]["render"]["status"])
        first_image = OUT / "gui-0-usage-0.ppm"
        second_image = OUT / "gui-1-usage-0.ppm"
        self.assertEqual(region(first_image, 0, 52, 425, 240),
                         region(second_image, 0, 52, 425, 240))
        self.assertNotEqual(region(first_image, 440, 86, 363, 160),
                            region(second_image, 440, 86, 363, 160))

    def test_waiting_unknown_error_last_good_and_global_fallback(self):
        unavailable = session(status="unavailable")
        out = run_render([b"invalid\n", frame(1), frame(2, [unavailable], [global_reset(None, "HTTP_500")]),
                          frame(3, [session(status="error")], [global_reset(None, "HTTP_500")])])
        self.assertFalse(out[0]["accepted"])
        self.assertEqual(out[0]["render"]["quota_count"], 0)
        self.assertTrue(out[0]["render"]["screen_wrap"])
        self.assertEqual([row["accepted"] for row in out[1:]], [True] * 3)
        normal = region(OUT / "gui-1-usage-0.ppm", 440, 86, 363, 160)
        unknown = region(OUT / "gui-2-usage-0.ppm", 440, 86, 363, 160)
        recovered_cache = region(OUT / "gui-3-usage-0.ppm", 440, 86, 363, 160)
        self.assertNotEqual(normal, unknown)
        self.assertEqual(normal, recovered_cache)
        self.assertEqual(region(OUT / "gui-1-global-0.ppm", 22, 124, 776, 27),
                         region(OUT / "gui-3-global-0.ppm", 22, 124, 776, 27))


if __name__ == "__main__":
    unittest.main()
