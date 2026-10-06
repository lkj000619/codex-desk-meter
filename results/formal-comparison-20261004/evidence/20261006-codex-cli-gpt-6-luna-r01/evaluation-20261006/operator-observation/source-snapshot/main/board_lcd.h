#ifndef BOARD_LCD_H
#define BOARD_LCD_H

#include "esp_err.h"
#include <stdbool.h>
#include <stdint.h>

typedef enum {
    METER_PAGE_DASHBOARD = 0,
    METER_PAGE_GLOBAL_RESET = 1,
    METER_PAGE_STATUS = 2,
} meter_page_t;

esp_err_t board_lcd_init(void);
esp_err_t board_lcd_present(const char *frame,
                            uint32_t sequence,
                            bool has_frame,
                            bool receive_stale,
                            const char *last_error,
                            meter_page_t page,
                            uint64_t monotonic_ms,
                            uint64_t frame_accepted_ms,
                            uint64_t scroll_offset,
                            bool show_fixture_splash);
esp_err_t board_backlight_set(uint8_t brightness);
int board_boot_level(void);

#endif
