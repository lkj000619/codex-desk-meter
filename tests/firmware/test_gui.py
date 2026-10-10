"""Pixel checks of the production GUI linked to the production C receiver."""
import copy
import json
import subprocess
import unittest
from pathlib import Path

from test_cdm import EXE, ROOT, STAMP, frame, quota, session, global_reset

OUT = ROOT / "tests/firmware/.build"
HEADER = b"P6\n820 320\n255\n"
PAPER = bytes((246, 246, 246))
INK = bytes((24, 24, 24))
BLUE = bytes((0, 133, 197))
# Independent 5x7 glyph expectations for numeric fields and the quota prefix.
GLYPHS = {
    "0": (14, 17, 19, 21, 25, 17, 14), "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 2, 4, 8, 31), "3": (30, 1, 1, 14, 1, 1, 30),
    "4": (2, 6, 10, 18, 31, 2, 2), "5": (31, 16, 30, 1, 1, 17, 14),
    "6": (6, 8, 16, 30, 17, 17, 14), "7": (31, 1, 2, 4, 8, 8, 8),
    "8": (14, 17, 17, 14, 17, 17, 14), "9": (14, 17, 17, 15, 1, 2, 12),
    ".": (0, 0, 0, 0, 0, 12, 12), "-": (0, 0, 0, 31, 0, 0, 0),
    "+": (0, 4, 4, 31, 4, 4, 0), "%": (17, 18, 2, 4, 8, 9, 17),
    "/": (1, 1, 2, 4, 8, 16, 16), "E": (31, 16, 16, 30, 16, 16, 31),
    "U": (17, 17, 17, 17, 17, 17, 14), "S": (15, 16, 16, 14, 1, 1, 30),
    "D": (30, 17, 17, 17, 17, 17, 30), "R": (30, 17, 17, 30, 20, 18, 17),
    "M": (17, 27, 21, 21, 17, 17, 17), " ": (0,) * 7,
}


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


def expected_field(text, width, height, scale, color):
    pixels = bytearray(PAPER * width * height)
    for index, char in enumerate(text.upper()):
        for row, bits in enumerate(GLYPHS[char]):
            for col in range(5):
                if bits & (1 << (4 - col)):
                    for dy in range(scale):
                        for dx in range(scale):
                            at = ((row * scale + dy) * width + index * 6 * scale + col * scale + dx) * 3
                            pixels[at:at + 3] = color
    return bytes(pixels)


class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not EXE.exists():
            raise RuntimeError("Run tests/firmware/build-host.ps1 first")

    def assert_field(self, path, x, y, width, height, text, color=INK, scales=(3, 2, 1)):
        actual = region(path, x, y, width, height)
        self.assertTrue(any(len(text) * 6 * scale <= width and 7 * scale <= height and
                            actual == expected_field(text, width, height, scale, color)
                            for scale in scales), f"incomplete or overflowing rendered field: {text!r} at {x},{y}")

    def test_numeric_fields_keep_exact_counts_exponents_and_percent_suffixes(self):
        cases = []
        for values, quota_values in [
            (dict(input=300000000, output=14238800, cached_input=299000000,
                  reasoning_output=14000000, source_total=9007199254740991,
                  normalized_total=314238800),
             dict(used_units=314238800, remaining_units=123456789,
                  limit_units=437695589, percent_used=None, percent_remaining=None)),
            (dict(input=9007199254740991, output=0, cached_input=0,
                  reasoning_output=0, source_total=0, normalized_total=9007199254740991),
             dict(used_units=9007199254740991, remaining_units=0,
                  limit_units=9007199254740991, percent_used=None, percent_remaining=None)),
            (dict(input=0, output=0, cached_input=0, reasoning_output=0,
                  source_total=0, normalized_total=0),
             dict(used_units=None, remaining_units=None, limit_units=None,
                  percent_used=42.125, percent_remaining=57.875)),
            (dict(input=123456789.25, output=0, cached_input=0, reasoning_output=0,
                  source_total=123456789.25, normalized_total=123456789.25),
             dict(used_units=123456789.25, remaining_units=123456789.25,
                  limit_units=246913578.5, percent_used=None, percent_remaining=None)),
            (dict(input=0, output=0, cached_input=0, reasoning_output=0,
                  source_total=0, normalized_total=0),
             dict(used_units=None, remaining_units=None, limit_units=None,
                  percent_used=None, percent_remaining=None)),
            (dict(input=0, output=0, cached_input=0, reasoning_output=0,
                  source_total=0, normalized_total=0),
             dict(used_units=None, remaining_units=None, limit_units=None,
                  percent_used=0.0000000125, percent_remaining=None)),
        ]:
            s, q = session(), quota()
            for window in s["windows"]:
                window["used_units"] = values[window["window_id"]]
            q["windows"][0].update(quota_values)
            cases.append(frame(len(cases) + 1, [s, q], []))
        out = run_render(cases)
        self.assertEqual([row["accepted"] for row in out], [True] * len(cases), out)
        large, boundary, percent, fractional, unknown, tiny_percent = [
            OUT / f"gui-{i}-usage-0.ppm" for i in range(6)]
        for path, total, rows, used, remaining in [
            (large, "314238800", ("300000000", "14238800", "299000000", "14000000", "9007199254740991"),
             "314238800", "USED / REM 123456789"),
            (boundary, "9007199254740991", ("9007199254740991", "0", "0", "0", "0"),
             "9007199254740991", "USED / REM 0"),
            (percent, "0", ("0",) * 5, "42.125%", "USED / REM 57.875%"),
            (fractional, "1.234568E+08", ("1.234568E+08", "0", "0", "0", "1.234568E+08"),
             "1.234568E+08", "USED / REM 1.234568E+08"),
            (unknown, "0", ("0",) * 5, "--", "USED / REM --"),
            (tiny_percent, "0", ("0",) * 5, "1.25E-08%", "USED / REM --"),
        ]:
            self.assert_field(path, 643, 86, 160, 21, total)
            for y, value in zip((119, 144, 169, 194, 219), rows):
                self.assert_field(path, 680, y, 125, 14, value, BLUE if y in (169, 194) else INK, (2, 1))
                self.assertEqual(region(path, 805, y, 15, 14), PAPER * 15 * 14)
            self.assert_field(path, 18, 109, 170, 21, used)
            self.assert_field(path, 190, 114, 215, 14, remaining, INK, (2, 1))
            self.assertEqual(region(path, 805, 86, 15, 14), PAPER * 15 * 14)
            self.assertEqual(region(path, 405, 114, 20, 14), PAPER * 20 * 14)
        self.assertEqual(region(large, 440, 90, 203, 14), region(boundary, 440, 90, 203, 14))
        for y in (119, 144, 169, 194, 219):
            self.assertEqual(region(large, 440, y, 240, 14), region(boundary, 440, y, 240, 14))

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
