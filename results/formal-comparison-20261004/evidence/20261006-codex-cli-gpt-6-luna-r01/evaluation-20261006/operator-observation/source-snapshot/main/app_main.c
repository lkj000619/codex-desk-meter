#include "board_lcd.h"
#include "idle_dim_policy.h"
#include "meter_core.h"

#include "driver/usb_serial_jtag.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include <stdbool.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdlib.h>

static const char *TAG = "meter_app";
static meter_receiver_t receiver;

static bool finish_line(uint8_t *line, size_t *line_length, bool *overflow,
                        uint64_t monotonic_ms)
{
    size_t frame_length = *overflow ? METER_MAX_FRAME_BYTES + 1u : *line_length;
    bool accepted = meter_receiver_receive(&receiver, line, frame_length, monotonic_ms);
    if (accepted) ESP_LOGI(TAG, "accepted cdm/1 frame sequence=%" PRIu32, receiver.sequence);
    else ESP_LOGW(TAG, "rejected frame: %s; last-good sequence=%" PRIu32,
                  receiver.last_error, receiver.sequence);
    *line_length = 0;
    *overflow = false;
    return accepted;
}

static bool consume_usb_bytes(uint8_t *incoming, int count, uint8_t *line,
                              size_t *line_length, bool *overflow,
                              bool *pending_lf, uint64_t *pending_lf_ms,
                              uint64_t monotonic_ms)
{
    bool accepted_any = false;
    for (int i = 0; i < count; i++) {
        uint8_t byte = incoming[i];
        if (*pending_lf) {
            if (byte == '\n') {
                if (*line_length < METER_MAX_FRAME_BYTES + 1u) line[(*line_length)++] = byte;
                else *overflow = true;
                accepted_any |= finish_line(line, line_length, overflow, monotonic_ms);
                *pending_lf = false;
                continue;
            }
            accepted_any |= finish_line(line, line_length, overflow, monotonic_ms);
            *pending_lf = false;
        }
        if (*line_length < METER_MAX_FRAME_BYTES + 1u) {
            line[(*line_length)++] = byte;
        } else {
            *overflow = true;
        }
        if (byte == '\n') {
            *pending_lf = true;
            *pending_lf_ms = monotonic_ms;
        }
    }
    return accepted_any;
}

void app_main(void)
{
    meter_receiver_init(&receiver);
    ESP_ERROR_CHECK(board_lcd_init());
    usb_serial_jtag_driver_config_t usb_config = {
        .tx_buffer_size = 256,
        .rx_buffer_size = 2048,
    };
    ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&usb_config));

    uint8_t *line = (uint8_t *)heap_caps_malloc(METER_MAX_FRAME_BYTES + 1u,
                                                MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (!line) line = (uint8_t *)malloc(METER_MAX_FRAME_BYTES + 1u);
    if (!line) {
        ESP_LOGE(TAG, "cannot allocate maximum cdm/1 line buffer");
        return;
    }
    ESP_LOGI(TAG, "USB Serial/JTAG receiver ready: 115200 8N1 host settings, no ACK/retry protocol");

    uint8_t incoming[128];
    size_t line_length = 0;
    bool overflow = false;
    bool pending_lf = false;
    uint64_t pending_lf_ms = 0;
    int raw_button = board_boot_level();
    int stable_button = raw_button;
    uint64_t button_changed_ms = (uint64_t)esp_timer_get_time() / 1000u;
    uint64_t last_interaction_ms = button_changed_ms;
    uint64_t last_draw_ms = 0;
    uint64_t dashboard_scroll_ms = 0;
    uint64_t scroll_offset = 0;
    meter_page_t page = METER_PAGE_DASHBOARD;
    bool needs_draw = true;

    for (;;) {
        int bytes = usb_serial_jtag_read_bytes(incoming, sizeof(incoming), pdMS_TO_TICKS(10));
        uint64_t now_ms = (uint64_t)esp_timer_get_time() / 1000u;
        if (bytes > 0) needs_draw |= consume_usb_bytes(incoming, bytes, line, &line_length,
            &overflow, &pending_lf, &pending_lf_ms, now_ms);
        if (pending_lf && now_ms - pending_lf_ms >= 50u) {
            needs_draw |= finish_line(line, &line_length, &overflow, now_ms);
            pending_lf = false;
        }

        int current_button = board_boot_level();
        if (current_button != raw_button) {
            raw_button = current_button;
            button_changed_ms = now_ms;
        }
        if (raw_button != stable_button && now_ms - button_changed_ms >= 30u) {
            stable_button = raw_button;
            if (stable_button == 0) {
                page = (meter_page_t)(((unsigned)page + 1u) % 3u);
                last_interaction_ms = now_ms;
                needs_draw = true;
                ESP_LOGI(TAG, "BOOT debounced; page=%u", (unsigned)page);
            }
        }

        meter_receiver_poll(&receiver, now_ms);
        if (page == METER_PAGE_DASHBOARD && now_ms - dashboard_scroll_ms >= 4000u) {
            dashboard_scroll_ms = now_ms;
            scroll_offset++;
            needs_draw = true;
        }
        if (now_ms - last_draw_ms >= 1000u) needs_draw = true;
        if (needs_draw) {
            esp_err_t draw_error = board_lcd_present(receiver.last_good_line, receiver.sequence,
                receiver.has_good_frame, receiver.receive_stale, receiver.last_error, page,
                now_ms, receiver.accepted_at_ms, scroll_offset, false);
            if (draw_error != ESP_OK) ESP_LOGE(TAG, "LCD update failed: %s", esp_err_to_name(draw_error));
            last_draw_ms = now_ms;
            needs_draw = false;
        }
        static uint8_t applied_brightness = 180;
        uint8_t brightness = idle_dim_brightness(now_ms, last_interaction_ms, true);
        if (brightness != applied_brightness) {
            (void)board_backlight_set(brightness);
            applied_brightness = brightness;
        }
        vTaskDelay(pdMS_TO_TICKS(5));
    }
}
