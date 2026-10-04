#pragma once
#include <stddef.h>
#include <stdint.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Board facts (vendor 09_FactoryProgram main/user_config.h + main.cpp):
 * portrait panel 320x820, RGB565, control SPI CS=0 SCK=2 SDO=1,
 * RGB DE=40 PCLK=41 VSYNC=39 HSYNC=38 RESET=16,
 * data order B0..B4 G0..G5 R0..R4, backlight GPIO6 active-low.
 * This BSP re-implements init/draw locally; it does not copy vendor
 * component sources. Landscape 820x320 is a software transpose over the
 * proven portrait timings so the proven porch/pulse values are untouched. */

#define BSP_LCD_PHYS_W 320
#define BSP_LCD_PHYS_H 820
#define BSP_LCD_LOGIC_W 820
#define BSP_LCD_LOGIC_H 320

esp_err_t bsp_lcd_init(void);

/* Active-low backlight: duty = 255 - brightness (matches vendor PWM BSP). */
esp_err_t bsp_backlight_set_brightness(uint8_t brightness_0_255);

/* Fill the logical 820x320 canvas. */
void bsp_lcd_fill(uint16_t rgb565);

/* Print up to 12 lines of <=64 chars each on the logical canvas. */
void bsp_lcd_show_text(const char lines[][65], int n_lines, const char *header);

/* Push the logical canvas to the panel (transpose + full draw). */
esp_err_t bsp_lcd_flush(void);

uint16_t bsp_rgb565(uint8_t r, uint8_t g, uint8_t b);

#ifdef __cplusplus
}
#endif
