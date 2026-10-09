"""Exercise the production BSP against IDF 5.3.2 bounce handoff semantics."""
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

HARNESS = r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <windows.h>
#include "presentation_sdk.h"
#include "bsp.c"

static uint16_t fb[2][320 * 820];
static const uint16_t *scanned;
static const uint16_t *submitted;
static int current_fb, bounce_fb, backlight, backlight_dark_first, gpio0_mode;
static int callbacks_seen, takes, mode, draw_error, register_error;
static int delayed_ms = 20;
static esp_lcd_rgb_panel_event_callbacks_t registered;
static void *callback_ctx;
static presentation_test_semaphore boundary;

esp_err_t gpio_set_level(int pin, int level) {
    if (pin == GPIO_NUM_6) {
        if (level == 1 && backlight_dark_first == 0) backlight_dark_first = 1;
        if (level == 0) assert(backlight_dark_first == 1 && fb[0][0] == 0xF7BE && fb[1][0] == 0xF7BE);
        backlight = level;
    }
    return ESP_OK;
}
esp_err_t gpio_config(const gpio_config_t *c) { assert(c->mode == GPIO_MODE_OUTPUT); assert(backlight_dark_first == 1); return ESP_OK; }
esp_err_t gpio_set_direction(int pin, int dir) { if(pin == GPIO_NUM_0) { assert(backlight == 1); assert(dir == GPIO_MODE_INPUT); gpio0_mode=dir; } return ESP_OK; }
esp_err_t gpio_set_pull_mode(int pin, int mode) { if(pin == GPIO_NUM_0) { assert(gpio0_mode == GPIO_MODE_INPUT && mode == GPIO_PULLUP_ONLY); } return ESP_OK; }
int gpio_get_level(int pin) { return 1; }
esp_err_t esp_lcd_new_panel_io_3wire_spi(const esp_lcd_panel_io_3wire_spi_config_t *c, esp_lcd_panel_io_handle_t *io) { *io=fb; return ESP_OK; }
esp_err_t esp_lcd_new_panel_st7701(esp_lcd_panel_io_handle_t io, const esp_lcd_panel_dev_config_t *c, esp_lcd_panel_handle_t *p) {
    const esp_lcd_rgb_panel_config_t *r=c->vendor_config->rgb_config;
    assert(r->num_fbs==2 && r->bounce_buffer_size_px==3200 && r->timings.h_res==320 && r->timings.v_res==820 && r->flags.fb_in_psram);
    *p=fb; return ESP_OK;
}
esp_err_t esp_lcd_panel_init(esp_lcd_panel_handle_t p) { return ESP_OK; }
esp_err_t esp_lcd_rgb_panel_get_frame_buffer(esp_lcd_panel_handle_t p, uint32_t n, void **first, ...) {
    assert(n==2); *first=fb[0]; va_list a; va_start(a,first); void **second=va_arg(a,void **); *second=fb[1]; assert(va_arg(a,void **)==NULL); va_end(a); return ESP_OK;
}
esp_err_t esp_lcd_rgb_panel_register_event_callbacks(esp_lcd_panel_handle_t p, const esp_lcd_rgb_panel_event_callbacks_t *c, void *ctx) {
    if(register_error) return ESP_ERR_INVALID_STATE; registered=*c; callback_ctx=ctx; return ESP_OK;
}
esp_err_t esp_lcd_panel_draw_bitmap(esp_lcd_panel_handle_t p,int x0,int y0,int x1,int y1,const void *pixels) {
    assert(x0==0 && y0==0 && x1==320 && y1==820);
    if(draw_error) return ESP_ERR_INVALID_STATE;
    submitted=pixels; current_fb=(pixels==fb[0])?0:1; takes=0; callbacks_seen=0; return ESP_OK;
}
bool esp_ptr_external_ram(const void *p) { return p==fb[0] || p==fb[1]; }
SemaphoreHandle_t xSemaphoreCreateBinary(void) { return &boundary; }
BaseType_t xSemaphoreGiveFromISR(SemaphoreHandle_t s, BaseType_t *w) { s->signaled=1; if(w)*w=pdTRUE; return pdTRUE; }
BaseType_t xSemaphoreTake(SemaphoreHandle_t s,unsigned timeout) {
    if(s->signaled) { s->signaled=0; return pdTRUE; }
    if(!timeout) return pdFALSE;
    takes++;
    if(mode==2 && takes==2) { Sleep(timeout); return pdFALSE; }
    Sleep(delayed_ms);
    /* IDF copies a full old bounce frame before advancing bb_fb_index to cur_fb_index. */
    if(++callbacks_seen==1) { assert(bounce_fb != current_fb); bounce_fb=current_fb; }
    else { assert(callbacks_seen==2 && bounce_fb==current_fb); scanned=submitted; }
    assert(registered.on_bounce_frame_finish);
    registered.on_bounce_frame_finish(fb,NULL,callback_ctx);
    assert(s->signaled); s->signaled=0; return pdTRUE;
}

int main(int argc,char **argv) {
    assert(argc==2); mode=atoi(argv[1]); scanned=fb[0]; bounce_fb=0;
    if(mode==4) register_error=1;
    esp_err_t init=bsp_init();
    if(mode==4) { assert(init==ESP_ERR_INVALID_STATE && backlight==1 && gpio0_mode==0); return 0; }
    assert(init==ESP_OK && backlight==0 && gpio0_mode==GPIO_MODE_INPUT);
    assert(scanned==fb[0] && fb[0][0]==0xF7BE);
    bsp_pixel(819,0,0x1234);
    assert(scanned==fb[0] && fb[0][0]==0xF7BE);
    if(mode==3) draw_error=1;
    double start=(double)GetTickCount64();
    esp_err_t result=bsp_present();
    double elapsed=(double)GetTickCount64()-start;
    if(mode==1) {
        assert(result==ESP_OK && scanned==fb[1] && elapsed>=2*delayed_ms-5);
        assert(fb[0][0]==0xF7BE && fb[1][0]==0x1234);
        bsp_fill(0,0,820,320,0x5678); assert(scanned[0]==0x1234);
        assert(bsp_present()==ESP_OK && scanned==fb[0] && fb[0][0]==0x5678);
        return 0;
    }
    if(mode==2) { assert(result==ESP_ERR_TIMEOUT && scanned==fb[0] && elapsed>=200 && elapsed<500 && backlight==1); }
    if(mode==3) { assert(result==ESP_ERR_INVALID_STATE && elapsed<100 && backlight==1 && scanned==fb[0]); }
    bsp_pixel(819,0,0x9999); bsp_fill(0,0,820,320,0x9999); assert(scanned==fb[0] && fb[0][0]==0xF7BE);
    return 0;
}
'''


class LcdPresentationTests(unittest.TestCase):
    def test_real_bsp_handoff_failures_and_boot_gpio_order(self):
        zig = ROOT / "firmware/.host-tools/ziglang/zig.exe"
        self.assertTrue(zig.is_file(), zig)
        with tempfile.TemporaryDirectory(prefix="cdm-lcd-review-") as temp:
            temp = Path(temp)
            headers = temp / "sdk"
            names = ("driver/gpio.h", "esp_lcd_panel_ops.h", "esp_lcd_panel_io_additions.h",
                     "esp_lcd_st7701.h", "esp_lcd_panel_rgb.h", "esp_heap_caps.h",
                     "esp_memory_utils.h", "esp_check.h")
            for name in names:
                path = headers / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("", encoding="utf-8")
            source = temp / "presentation_review.c"
            exe = temp / "presentation_review.exe"
            source.write_text(HARNESS, encoding="utf-8")
            build = subprocess.run([str(zig), "cc", "-O0", "-std=c11", "-DCDM_PRESENTATION_TEST",
                                    "-include", str(ROOT / "tests/firmware/presentation_sdk.h"),
                                    f"-I{headers}", f"-I{ROOT / 'tests/firmware'}",
                                    f"-I{ROOT / 'tests/firmware/include'}", f"-I{ROOT / 'firmware/main'}",
                                    str(source), "-o", str(exe)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            for mode in ("1", "2", "3", "4"):
                with self.subTest(mode=mode):
                    run = subprocess.run([str(exe), mode], cwd=ROOT, capture_output=True, text=True, timeout=3)
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
