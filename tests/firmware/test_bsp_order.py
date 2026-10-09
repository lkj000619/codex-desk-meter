"""Guard the GPIO0 handoff against the real vendor ST7701 reset behavior."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENDOR = Path("C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16/source/ESP32-S3-LCD-3.16-Demo/ESP-IDF/09_FactoryProgram/managed_components/espressif__esp_lcd_st7701/esp_lcd_st7701_rgb.c")


class BspOrderTests(unittest.TestCase):
    def test_constructor_initializes_and_releases_command_io_before_rgb_init(self):
        driver = VENDOR.read_text(encoding="utf-8")
        constructor = driver.split("if (st7701->flags.enable_io_multiplex) {", 1)[1].split("// Create RGB panel", 1)[0]
        self.assertLess(constructor.index("panel_st7701_send_init_cmds(st7701)"),
                        constructor.index("esp_lcd_panel_io_del(io)"))
        reset = driver.split("static esp_err_t panel_st7701_reset(esp_lcd_panel_t *panel)\n{", 1)[1].split("static esp_err_t panel_st7701_mirror", 1)[0]
        self.assertIn("gpio_set_level(st7701->reset_gpio_num, st7701->flags.reset_level)", reset)
        bsp = (ROOT / "firmware/main/bsp.c").read_text(encoding="utf-8")
        self.assertIn(".flags.enable_io_multiplex=1", bsp)
        self.assertLess(bsp.index("esp_lcd_new_panel_st7701"), bsp.index("esp_lcd_panel_init"))
        self.assertNotIn("esp_lcd_panel_reset(panel)", bsp)
        self.assertLess(bsp.index("esp_lcd_panel_init"), bsp.index("gpio_set_direction(GPIO_NUM_0,GPIO_MODE_INPUT)"))
