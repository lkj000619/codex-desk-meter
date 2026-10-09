#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "presentation_sdk.h"

#undef assert
#define assert(condition) do { if (!(condition)) { fprintf(stderr,"presentation assertion line %d: %s\n",__LINE__,#condition); exit(3); } } while (0)

// Compile the production BSP with a deterministic RGB scan/bounce boundary.
#ifndef PRESENTATION_BSP_SOURCE
#define PRESENTATION_BSP_SOURCE "../../firmware/main/bsp.c"
#endif
#include PRESENTATION_BSP_SOURCE
#ifdef PRESENTATION_BASELINE
esp_err_t bsp_present(void) { return ESP_OK; } // Unreachable: the scan-integrity assertion fails first.
#endif

static uint16_t frame[2][320 * 820];
static const uint16_t *scanned = frame[0];
static const uint16_t *submitted;
static esp_lcd_rgb_panel_event_callbacks_t callbacks;
static void *callback_context;
static presentation_test_semaphore boundary;
static int configured_buffers, backlight, stop_boundaries, wraps;

esp_err_t gpio_set_level(int pin, int level) { if (pin == GPIO_NUM_6) backlight = level; return ESP_OK; }
esp_err_t gpio_config(const gpio_config_t *config) { return ESP_OK; }
esp_err_t gpio_set_direction(int pin, int mode) { return ESP_OK; }
esp_err_t gpio_set_pull_mode(int pin, int mode) { return ESP_OK; }
int gpio_get_level(int pin) { return 1; }
esp_err_t esp_lcd_new_panel_io_3wire_spi(const esp_lcd_panel_io_3wire_spi_config_t *config, esp_lcd_panel_io_handle_t *io) { *io = frame; return ESP_OK; }
esp_err_t esp_lcd_new_panel_st7701(esp_lcd_panel_io_handle_t io, const esp_lcd_panel_dev_config_t *config, esp_lcd_panel_handle_t *handle)
{ configured_buffers = config->vendor_config->rgb_config->num_fbs; *handle = frame; return ESP_OK; }
esp_err_t esp_lcd_panel_init(esp_lcd_panel_handle_t handle) { return ESP_OK; }
esp_err_t esp_lcd_rgb_panel_get_frame_buffer(esp_lcd_panel_handle_t handle, uint32_t count, void **first, ...)
{
    *first = frame[0];
    if (count == 2) {
        va_list args; va_start(args, first);
        void **second = va_arg(args, void **); *second = frame[1];
        assert(va_arg(args, void **) == NULL);
        va_end(args);
    }
    return ESP_OK;
}
esp_err_t esp_lcd_rgb_panel_register_event_callbacks(esp_lcd_panel_handle_t handle, const esp_lcd_rgb_panel_event_callbacks_t *events, void *context)
{ callbacks = *events; callback_context = context; return ESP_OK; }
esp_err_t esp_lcd_panel_draw_bitmap(esp_lcd_panel_handle_t handle, int x0, int y0, int x1, int y1, const void *color)
{ assert(x0 == 0 && y0 == 0 && x1 == 320 && y1 == 820); submitted = color; wraps = 0; return ESP_OK; }
bool esp_ptr_external_ram(const void *pointer) { return pointer == frame[0] || pointer == frame[1]; }
SemaphoreHandle_t xSemaphoreCreateBinary(void) { return &boundary; }
BaseType_t xSemaphoreGiveFromISR(SemaphoreHandle_t semaphore, BaseType_t *woken)
{ semaphore->signaled = 1; if (woken) *woken = pdTRUE; return pdTRUE; }
BaseType_t xSemaphoreTake(SemaphoreHandle_t semaphore, unsigned timeout_ticks)
{
    if (semaphore->signaled) { semaphore->signaled = 0; return pdTRUE; }
    if (!timeout_ticks || stop_boundaries) return pdFALSE;
    assert(submitted != scanned); // The scan still sees the old completed frame.
    if (++wraps == 2) scanned = submitted; // First completion may have started before submit.
    assert(callbacks.on_bounce_frame_finish);
    callbacks.on_bounce_frame_finish(frame, NULL, callback_context);
    assert(semaphore->signaled);
    semaphore->signaled = 0;
    return pdTRUE;
}

int main(void)
{
    assert(bsp_init() == ESP_OK);
    assert(scanned == frame[0] && frame[0][0] == 0xF7BE);
    const uint16_t scanned_before = scanned[0];
    bsp_fill(0, 0, 820, 320, 0xF7BE);
    bsp_pixel(819, 0, 0x18C3);
    assert(scanned[0] == scanned_before); // Original BSP fails here: it writes into the scanned frame.
    assert(configured_buffers == 2 && backlight == 0);
    assert(frame[0][0] == 0xF7BE && frame[1][0] == 0x18C3);
    assert(bsp_present() == ESP_OK);
    assert(scanned == frame[1] && frame[1][0] == 0x18C3);
    bsp_fill(0, 0, 820, 320, 0xF7BE);
    assert(scanned[0] == 0x18C3); // A new clear must remain invisible.
    bsp_pixel(819, 0, 0x0438);
    assert(scanned[0] == 0x18C3);
    assert(bsp_present() == ESP_OK);
    assert(scanned == frame[0] && scanned[0] == 0x0438);
    stop_boundaries = 1;
    bsp_pixel(819, 0, 0xB1A6);
    assert(bsp_present() == ESP_ERR_TIMEOUT);
    assert(backlight == 1); // A stalled scan handoff fails dark.
    return 0;
}
