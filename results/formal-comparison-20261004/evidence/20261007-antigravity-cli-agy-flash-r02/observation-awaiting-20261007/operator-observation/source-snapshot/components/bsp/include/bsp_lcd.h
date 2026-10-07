#ifndef BSP_LCD_H
#define BSP_LCD_H

#include "bsp_board.h"
#include "meter_types.h"
#include "esp_err.h"
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Initialize ST7701 controller, RGB panel, PSRAM framebuffer, and backlight PWM */
esp_err_t bsp_lcd_init(void);

/* Set backlight brightness 0 (off) to 255 (maximum) */
void bsp_lcd_set_backlight(uint8_t brightness);

/* Flush 820x320 landscape canvas to the display */
void bsp_lcd_flush(const uint16_t *canvas_820x320, display_orientation_t orientation);

#ifdef __cplusplus
}
#endif

#endif /* BSP_LCD_H */
