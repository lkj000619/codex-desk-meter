#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdarg.h>
#include <stdlib.h>
#include "esp_err.h"

#define ESP_OK 0
#define ESP_ERR_NO_MEM 0x101
#define ESP_ERR_TIMEOUT 0x107
#define ESP_ERR_INVALID_STATE 0x103
#define ESP_RETURN_ON_ERROR(call, tag, message) do { esp_err_t err = (call); if (err != ESP_OK) return err; } while (0)
#define ESP_ERROR_CHECK(call) do { if ((call) != ESP_OK) abort(); } while (0)
#define IRAM_ATTR
#define GPIO_NUM_0 0
#define GPIO_NUM_1 1
#define GPIO_NUM_2 2
#define GPIO_NUM_6 6
#define GPIO_NUM_16 16
#define GPIO_MODE_OUTPUT 1
#define GPIO_MODE_INPUT 2
#define GPIO_PULLUP_ONLY 1
#define IO_TYPE_GPIO 1
#define LCD_CLK_SRC_DEFAULT 0
#define LCD_RGB_ELEMENT_ORDER_RGB 0
#define pdTRUE 1
#define pdFALSE 0
#define pdMS_TO_TICKS(ms) (ms)

typedef int BaseType_t;
typedef struct { uint64_t pin_bit_mask; int mode; } gpio_config_t;
typedef struct { int cs_io_type, cs_gpio_num, scl_io_type, scl_gpio_num, sda_io_type, sda_gpio_num; void *io_expander; } spi_line_config_t;
typedef struct { int unused; } esp_lcd_panel_io_3wire_spi_config_t;
#define ST7701_PANEL_IO_3WIRE_SPI_CONFIG(lines, mode) ((esp_lcd_panel_io_3wire_spi_config_t){0})
typedef void *esp_lcd_panel_handle_t;
typedef void *esp_lcd_panel_io_handle_t;
typedef struct { unsigned char cmd; const uint8_t *data; size_t data_bytes; unsigned delay_ms; } st7701_lcd_init_cmd_t;
typedef struct {
    int clk_src, psram_trans_align, bounce_buffer_size_px, num_fbs, data_width, bits_per_pixel;
    int de_gpio_num, pclk_gpio_num, vsync_gpio_num, hsync_gpio_num, disp_gpio_num;
    int data_gpio_nums[16];
    struct { int pclk_hz, h_res, v_res, hsync_back_porch, hsync_front_porch, hsync_pulse_width,
                 vsync_back_porch, vsync_front_porch, vsync_pulse_width; } timings;
    struct { bool fb_in_psram; } flags;
} esp_lcd_rgb_panel_config_t;
typedef struct { const st7701_lcd_init_cmd_t *init_cmds; size_t init_cmds_size;
                 esp_lcd_rgb_panel_config_t *rgb_config; struct { int enable_io_multiplex; } flags; } st7701_vendor_config_t;
typedef struct { int reset_gpio_num, rgb_ele_order, bits_per_pixel; st7701_vendor_config_t *vendor_config; } esp_lcd_panel_dev_config_t;
typedef struct { int unused; } esp_lcd_rgb_panel_event_data_t;
typedef bool (*esp_lcd_rgb_panel_bounce_buf_finish_cb_t)(esp_lcd_panel_handle_t, const esp_lcd_rgb_panel_event_data_t *, void *);
typedef struct { void *on_vsync, *on_bounce_empty; esp_lcd_rgb_panel_bounce_buf_finish_cb_t on_bounce_frame_finish; } esp_lcd_rgb_panel_event_callbacks_t;
typedef struct { int signaled; } presentation_test_semaphore;
typedef presentation_test_semaphore *SemaphoreHandle_t;

esp_err_t gpio_set_level(int pin, int level);
esp_err_t gpio_config(const gpio_config_t *config);
esp_err_t gpio_set_direction(int pin, int mode);
esp_err_t gpio_set_pull_mode(int pin, int mode);
int gpio_get_level(int pin);
esp_err_t esp_lcd_new_panel_io_3wire_spi(const esp_lcd_panel_io_3wire_spi_config_t *config, esp_lcd_panel_io_handle_t *io);
esp_err_t esp_lcd_new_panel_st7701(esp_lcd_panel_io_handle_t io, const esp_lcd_panel_dev_config_t *config, esp_lcd_panel_handle_t *panel);
esp_err_t esp_lcd_panel_init(esp_lcd_panel_handle_t panel);
esp_err_t esp_lcd_rgb_panel_get_frame_buffer(esp_lcd_panel_handle_t panel, uint32_t count, void **first, ...);
esp_err_t esp_lcd_rgb_panel_register_event_callbacks(esp_lcd_panel_handle_t panel, const esp_lcd_rgb_panel_event_callbacks_t *callbacks, void *context);
esp_err_t esp_lcd_panel_draw_bitmap(esp_lcd_panel_handle_t panel, int x0, int y0, int x1, int y1, const void *pixels);
bool esp_ptr_external_ram(const void *pointer);
SemaphoreHandle_t xSemaphoreCreateBinary(void);
BaseType_t xSemaphoreTake(SemaphoreHandle_t semaphore, unsigned timeout_ticks);
BaseType_t xSemaphoreGiveFromISR(SemaphoreHandle_t semaphore, BaseType_t *woken);
