"""Test the real F9 module against a deterministic fake IDF sensor API."""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
ZIG = ROOT / "firmware/.host-tools/ziglang/zig.exe"
HEADER = r"""
#pragma once
#include <stddef.h>
typedef int esp_err_t;
#define ESP_OK 0
typedef void *temperature_sensor_handle_t;
typedef struct { int min_celsius; int max_celsius; } temperature_sensor_config_t;
#define TEMPERATURE_SENSOR_CONFIG_DEFAULT(low, high) \
    ((temperature_sensor_config_t){(low), (high)})
esp_err_t temperature_sensor_install(const temperature_sensor_config_t *, temperature_sensor_handle_t *);
esp_err_t temperature_sensor_enable(temperature_sensor_handle_t);
esp_err_t temperature_sensor_uninstall(temperature_sensor_handle_t);
esp_err_t temperature_sensor_get_celsius(temperature_sensor_handle_t, float *);
"""
HARNESS = r"""
#include <string.h>
#include "driver/temperature_sensor.h"
#include "f9_temp.h"

static int install_result, enable_result, read_result;
static int installs, enables, uninstalls, reads;
static float sensor_value = 42.25f;

esp_err_t temperature_sensor_install(const temperature_sensor_config_t *config,
                                     temperature_sensor_handle_t *handle)
{
    installs++;
    if (config->min_celsius != 10 || config->max_celsius != 80) return -9;
    if (install_result == ESP_OK) *handle = (void *)1;
    return install_result;
}
esp_err_t temperature_sensor_enable(temperature_sensor_handle_t handle)
{ enables++; return handle ? enable_result : -9; }
esp_err_t temperature_sensor_uninstall(temperature_sensor_handle_t handle)
{ uninstalls++; return handle ? ESP_OK : -9; }
esp_err_t temperature_sensor_get_celsius(temperature_sensor_handle_t handle, float *value)
{ reads++; if (!handle || read_result != ESP_OK) return -9; *value = sensor_value; return ESP_OK; }

int main(int argc, char **argv)
{
    if (argc != 2) return 20;
    if (!strcmp(argv[1], "install-fail")) install_result = -1;
    if (!strcmp(argv[1], "enable-fail")) enable_result = -1;
    if (!strcmp(argv[1], "read-fail")) read_result = -1;
    f9_temp_init();
    float output = -99.0f;
    bool known = f9_temp_read(&output);

    if (!strcmp(argv[1], "install-fail"))
        return installs == 1 && enables == 0 && uninstalls == 0 && reads == 0 && !known ? 0 : 1;
    if (!strcmp(argv[1], "enable-fail"))
        return installs == 1 && enables == 1 && uninstalls == 1 && reads == 0 && !known ? 0 : 2;
    if (!strcmp(argv[1], "read-fail"))
        return installs == 1 && enables == 1 && uninstalls == 0 && reads == 1 && !known && output == -99.0f ? 0 : 3;
    if (!strcmp(argv[1], "read-ok")) {
        if (!known || output != sensor_value || installs != 1 || enables != 1 || reads != 1) return 4;
        if (f9_temp_read(0) || reads != 1) return 5;
        return 0;
    }
    return 21;
}
"""


class F9TemperatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not ZIG.is_file():
            raise RuntimeError("The accepted firmware host Zig compiler is unavailable")
        cls.temp = tempfile.TemporaryDirectory(prefix="f9-temp-test-", dir=Path(__file__).parent)
        root = Path(cls.temp.name)
        include = root / "include/driver"
        include.mkdir(parents=True)
        (include / "temperature_sensor.h").write_text(HEADER, encoding="utf-8")
        harness = root / "harness.c"
        harness.write_text(HARNESS, encoding="utf-8")
        cls.exe = root / "f9-temp-test.exe"
        result = subprocess.run(
            [str(ZIG), "cc", "-O0", "-std=c11", f"-I{root / 'include'}",
             f"-I{ROOT / 'firmware/main'}", str(ROOT / "firmware/main/f9_temp.c"),
             str(harness), "-o", str(cls.exe)], capture_output=True, text=True,
        )
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def run_case(self, name: str) -> None:
        result = subprocess.run([str(self.exe), name], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout or name)

    def test_install_failure_reports_unavailable_without_enable(self) -> None:
        self.run_case("install-fail")

    def test_enable_failure_uninstalls_and_reports_unavailable(self) -> None:
        self.run_case("enable-fail")

    def test_read_failure_preserves_output_and_reports_unknown(self) -> None:
        self.run_case("read-fail")

    def test_success_returns_sensor_value_without_constant_substitution(self) -> None:
        self.run_case("read-ok")


if __name__ == "__main__":
    unittest.main()
