"""Exercise the production BSP against a deterministic RGB bounce-frame boundary."""
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class PresentationTests(unittest.TestCase):
    def test_only_a_completed_frame_becomes_scanned(self):
        zig = ROOT / "firmware/.host-tools/ziglang/zig.exe"
        exe = ROOT / "tests/firmware/.build/presentation-host.exe"
        exe.parent.mkdir(exist_ok=True)
        sdk_headers = exe.parent / "presentation-sdk-headers"
        for name in ("driver/gpio.h", "esp_lcd_panel_ops.h", "esp_lcd_panel_io_additions.h",
                     "esp_lcd_st7701.h", "esp_lcd_panel_rgb.h", "esp_heap_caps.h",
                     "esp_memory_utils.h", "esp_check.h"):
            path = sdk_headers / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        baseline = os.environ.get("CDM_PRESENTATION_BASELINE_BSP")
        defines = ([f'-DPRESENTATION_BSP_SOURCE="{Path(baseline).resolve().as_posix()}"',
                    "-DPRESENTATION_BASELINE"] if baseline else ["-DCDM_PRESENTATION_TEST"])
        build = subprocess.run([str(zig), "cc", "-O0", "-std=c11", *defines,
                                "-include", str(ROOT / "tests/firmware/presentation_sdk.h"),
                                f"-I{sdk_headers}", f"-I{ROOT / 'tests/firmware'}",
                                f"-I{ROOT / 'tests/firmware/include'}", f"-I{ROOT / 'firmware/main'}",
                                str(ROOT / "tests/firmware/presentation_host.c"), "-o", str(exe)],
                               cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
        run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
