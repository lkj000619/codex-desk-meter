"""Pixel-check numeric fields from production C against the supplied old GUI."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[2]
ZIG = ROOT / "firmware/.host-tools/ziglang/zig.exe"
BASELINE = ROOT / "artifacts/orca-harness-runtime/numeric-baseline-gui.c"
CJSON = Path("C:/Espressif/v5.3.2/esp-idf/components/json/cJSON")
STAMP = "2026-10-07T17:10:00Z"
HEADER = b"P6\n820 320\n255\n"
PAPER, INK, BLUE = bytes((246, 246, 246)), bytes((24, 24, 24)), bytes((0, 133, 197))

# Independent bitmap expectations for numeric glyphs and the printed token unit.
GLYPHS = {
    "A": (14, 17, 17, 31, 17, 17, 17), "C": (14, 17, 16, 16, 16, 17, 14),
    "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31), "I": (31, 4, 4, 4, 4, 4, 31),
    "K": (17, 18, 20, 24, 20, 18, 17), "M": (17, 27, 21, 21, 17, 17, 17),
    "N": (17, 25, 21, 19, 17, 17, 17), "O": (14, 17, 17, 17, 17, 17, 14),
    "P": (30, 17, 17, 30, 16, 16, 16), "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (15, 16, 16, 14, 1, 1, 30), "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14), "Y": (17, 17, 10, 4, 4, 4, 4),
    "0": (14, 17, 19, 21, 25, 17, 14), "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 2, 4, 8, 31), "3": (30, 1, 1, 14, 1, 1, 30),
    "4": (2, 6, 10, 18, 31, 2, 2), "5": (31, 16, 30, 1, 1, 17, 14),
    "6": (6, 8, 16, 30, 17, 17, 14), "7": (31, 1, 2, 4, 8, 8, 8),
    "8": (14, 17, 17, 14, 17, 17, 14), "9": (14, 17, 17, 15, 1, 2, 12),
    ".": (0, 0, 0, 0, 0, 12, 12), "-": (0, 0, 0, 31, 0, 0, 0),
    "+": (0, 4, 4, 31, 4, 4, 0), "%": (17, 18, 2, 4, 8, 9, 17),
    "/": (1, 1, 2, 4, 8, 16, 16), " ": (0,) * 7,
}
CHANNELS = ("input", "output", "cached_input", "reasoning_output", "source_total", "normalized_total")


def session(values: dict[str, int | float | None]) -> dict:
    return {
        "schema_version": 1, "snapshot_id": "numeric-review", "provider_id": "codex",
        "agent_id": "codex-cli", "host_id": "synthetic-host", "model_id": None,
        "account_profile_id": None, "source_kind": "fixture", "metric_kind": "session_telemetry",
        "unit": "token", "status": "available", "observed_at": STAMP,
        "windows": [
            {"window_id": key, "label": key, "used_units": values.get(key),
             "remaining_units": None, "limit_units": None, "unit": "token",
             "percent_used": None, "percent_remaining": None, "resets_at": None,
             "reset_status": "unknown"}
            for key in CHANNELS
        ],
        "stale": False, "last_good_at": STAMP, "error_code": None, "error_reason": None,
    }


def quota(*, used=None, remaining=None, percent_used=None, percent_remaining=None, unit="token") -> dict:
    return {
        "schema_version": 1, "snapshot_id": "quota-review", "provider_id": "codex",
        "agent_id": "codex-cli", "host_id": "synthetic-host", "model_id": None,
        "account_profile_id": "synthetic-account", "source_kind": "fixture",
        "metric_kind": "quota_window", "unit": unit, "status": "available",
        "observed_at": STAMP,
        "windows": [{
            "window_id": "primary-18000s", "label": "300 min", "used_units": used,
            "remaining_units": remaining, "limit_units": None, "unit": unit,
            "percent_used": percent_used, "percent_remaining": percent_remaining,
            "resets_at": None, "reset_status": "unknown",
        }],
        "stale": False, "last_good_at": STAMP, "error_code": None, "error_reason": None,
    }


def wire_line(seq: int, usage: list[dict]) -> bytes:
    unsigned = {"protocol": "cdm/1", "sequence": seq, "sent_at": STAMP,
                "payload": {"usage": usage, "global_resets": []}}
    canonical = lambda obj: json.dumps(obj, sort_keys=True, separators=(",", ":"),
                                      ensure_ascii=False, allow_nan=False).encode("utf-8")
    envelope = {**unsigned, "integrity": {"algorithm": "crc32",
                                           "value": f"{zlib.crc32(canonical(unsigned)):08X}"}}
    return canonical(envelope) + b"\n"


def expected_field(text: str, width: int, height: int, scale: int, color: bytes = INK) -> bytes:
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


def ppm_region(path: Path, x: int, y: int, width: int, height: int) -> bytes:
    raw = path.read_bytes()
    if not raw.startswith(HEADER) or len(raw) != len(HEADER) + 820 * 320 * 3:
        raise AssertionError(f"invalid production framebuffer image: {path}")
    image = raw[len(HEADER):]
    return b"".join(image[(row * 820 + x) * 3:(row * 820 + x + width) * 3]
                    for row in range(y, y + height))


def assert_drawn_field(test: unittest.TestCase, image: Path, x: int, y: int,
                       width: int, height: int, text: str, scales: tuple[int, ...],
                       color: bytes = INK) -> None:
    actual = ppm_region(image, x, y, width, height)
    complete = [expected_field(text, width, height, scale, color) for scale in scales
                if len(text) * 6 * scale <= width and 7 * scale <= height]
    test.assertIn(actual, complete, f"incomplete glyphs or field overdraw: {text!r} at {x},{y}")


def compile_gui(zig: Path, gui_source: Path, executable: Path, cache: Path) -> None:
    env = os.environ.copy()
    env["ZIG_GLOBAL_CACHE_DIR"] = str(cache)
    env["ZIG_LOCAL_CACHE_DIR"] = str(cache)
    result = subprocess.run([
        str(zig), "cc", "-O0", "-std=c11", "-D_CRT_SECURE_NO_WARNINGS",
        f"-I{ROOT / 'firmware/main'}", f"-I{ROOT / 'tests/firmware/include'}",
        f"-I{CJSON}", str(ROOT / "tests/firmware/host_main.c"),
        str(ROOT / "firmware/main/cdm.c"), str(ROOT / "firmware/main/legacy.c"),
        str(gui_source), str(CJSON / "cJSON.c"), "-o", str(executable),
    ], cwd=ROOT, env=env, capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise AssertionError(f"host C compile failed for {gui_source}: {result.stdout}{result.stderr}")


def render(executable: Path, line: bytes, prefix: Path) -> Path:
    relative_prefix = Path(os.path.relpath(prefix, ROOT)).as_posix()
    event = {"line_hex": line.hex(), "mono_ms": 1000, "now_ms": 1000,
             "render": True, "ppm_prefix": relative_prefix}
    result = subprocess.run([str(executable), "--wire"], input=json.dumps({"events": [event]}),
                            text=True, capture_output=True, cwd=ROOT, timeout=15)
    if result.returncode:
        raise AssertionError(f"production C receiver/renderer failed: {result.stderr or result.stdout}")
    rows = json.loads(result.stdout)
    if len(rows) != 1 or not rows[0]["accepted"]:
        raise AssertionError(f"synthetic cdm/1 frame was not accepted: {result.stdout}")
    return ROOT / f"{relative_prefix}-usage-0.ppm"


class LcdNumericReadabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not ZIG.is_file() or not BASELINE.is_file() or not CJSON.joinpath("cJSON.c").is_file():
            raise RuntimeError("approved Zig host compiler, numeric baseline, or IDF cJSON source is missing")
        cls.temp = tempfile.TemporaryDirectory(prefix="numeric-readability-", dir=ROOT / "tests/integration")
        cls.work = Path(cls.temp.name)
        cache = cls.work / "zig-cache"
        cls.current = cls.work / "current.exe"
        cls.baseline = cls.work / "baseline.exe"
        compile_gui(ZIG, ROOT / "firmware/main/gui.c", cls.current, cache)
        compile_gui(ZIG, BASELINE, cls.baseline, cache)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_current_gui_renders_complete_counts_units_and_bounded_fields(self) -> None:
        cases = [
            ("large", {"input": 300000000, "output": 14238800, "cached_input": 299000000,
                       "reasoning_output": 14000000, "source_total": 9007199254740991,
                       "normalized_total": 314238800},
             quota(used=314238800, remaining=123456789)),
            ("integer-boundary", {"input": 9007199254740991, "output": 0, "cached_input": 0,
                                  "reasoning_output": 0, "source_total": 0,
                                  "normalized_total": 9007199254740991},
             quota(used=9007199254740991, remaining=0)),
            ("percent", {key: 0 for key in CHANNELS},
             quota(percent_used=42.125, percent_remaining=57.875, unit="percent")),
            ("exponent", {"input": 123456789.25, "output": 0, "cached_input": 0,
                          "reasoning_output": 0, "source_total": 123456789.25,
                          "normalized_total": 123456789.25},
             quota(used=123456789.25, remaining=123456789.25)),
            ("exponent-percent", {key: 0 for key in CHANNELS},
             quota(percent_used=0.0000000125, remaining=123456789.25, unit="percent")),
            ("unknown", {key: 0 for key in CHANNELS}, quota(unit="token")),
        ]
        expected = {
            "large": ("314238800", ("300000000", "14238800", "299000000", "14000000",
                                     "9007199254740991"), "314238800", "USED / REM 123456789"),
            "integer-boundary": ("9007199254740991", ("9007199254740991", "0", "0", "0", "0"),
                                 "9007199254740991", "USED / REM 0"),
            "percent": ("0", ("0",) * 5, "42.125%", "USED / REM 57.875%"),
            "exponent": ("1.234568E+08", ("1.234568E+08", "0", "0", "0", "1.234568E+08"),
                         "1.234568E+08", "USED / REM 1.234568E+08"),
            "exponent-percent": ("0", ("0",) * 5, "1.25E-08%", "USED / REM 1.234568E+08"),
            "unknown": ("0", ("0",) * 5, "--", "USED / REM --"),
        }
        for seq, (name, values, quota_record) in enumerate(cases, 1):
            with self.subTest(case=name):
                image = render(self.current, wire_line(seq, [session(values), quota_record]),
                               self.work / f"current-{name}")
                total, rows, used, remaining = expected[name]
                assert_drawn_field(self, image, 643, 86, 160, 21, total, (3, 2, 1))
                self.assertEqual(ppm_region(image, 584, 86, 59, 21), PAPER * 59 * 21)
                self.assertEqual(ppm_region(image, 803, 86, 17, 21), PAPER * 17 * 21)
                for y, value in zip((119, 144, 169, 194, 219), rows):
                    assert_drawn_field(self, image, 680, y, 125, 14, value, (2, 1),
                                       BLUE if y in (169, 194) else INK)
                    self.assertEqual(ppm_region(image, 596, y, 84, 14), PAPER * 84 * 14)
                    self.assertEqual(ppm_region(image, 805, y, 15, 14), PAPER * 15 * 14)
                    self.assertEqual(ppm_region(image, 680, y + 14, 125, 4), PAPER * 125 * 4)
                assert_drawn_field(self, image, 18, 109, 170, 21, used, (3, 2, 1))
                assert_drawn_field(self, image, 190, 114, 215, 14, remaining, (2, 1))
                self.assertEqual(ppm_region(image, 0, 109, 18, 21), PAPER * 18 * 21)
                self.assertEqual(ppm_region(image, 188, 109, 2, 21), PAPER * 2 * 21)
                self.assertEqual(ppm_region(image, 405, 114, 20, 14), PAPER * 20 * 14)
                self.assertEqual(ppm_region(image, 408, 93, 17, 14), PAPER * 17 * 14)
                assert_drawn_field(self, image, 18, 93, 390, 14,
                                   "ID primary-18000s  " + ("percent" if name in ("percent", "exponent-percent") else "token"),
                                   (1,), bytes((123, 125, 123)))

    def test_approved_pre_numeric_gui_reproduces_exponent_clipping(self) -> None:
        values = {"input": 300000000, "output": 14238800, "cached_input": 299000000,
                  "reasoning_output": 14000000, "source_total": 9007199254740991,
                  "normalized_total": 314238800}
        image = render(self.baseline, wire_line(1, [session(values), quota(used=314238800, remaining=123456789)]),
                       self.work / "baseline-large")
        clipped = ppm_region(image, 643, 86, 160, 21)
        self.assertEqual(clipped, expected_field("3.142388", 160, 21, 3),
                         "baseline should draw only the eight glyphs that fit from 3.142388e+08")
        self.assertNotEqual(clipped, expected_field("314238800", 160, 21, 1))


if __name__ == "__main__":
    unittest.main()
