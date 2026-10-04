/* Codex Desk Meter v2 firmware: USB CDM/1 receiver -> cache/stale -> LCD.
 *
 * Transport: USB-SERIAL-JTAG 115200 8N1 (baud is a host-side setting; the USB
 * function itself is rate-independent). No ACK/retry exists in cdm/1; the host
 * write receipt is not a device ACK. Console is routed to UART0 so the USB
 * port carries only canonical frames.
 */
#include <stdio.h>
#include <string.h>

#include "bsp_input.h"
#include "bsp_lcd.h"
#include "driver/usb_serial_jtag.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "feature_auto_dim.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "gui_format.h"
#include "meter_parser.h"
#include "meter_state.h"
#include "meter_validate.h"
#include "nvs_flash.h"

static const char *TAG = "cdm_meter";

static meter_receiver_t s_rx;
static uint8_t *s_line;       /* accumulation buffer (64K+1) */
static size_t s_line_len;
static uint8_t *s_last_good;  /* last accepted raw line */
static size_t s_last_good_len;
static int s_screen;
static uint64_t s_screen_deadline_ms;
static autodim_state_t s_dim;
static int s_link_ok = 1;

static uint64_t now_s(void) {
    return (uint64_t)(esp_timer_get_time() / 1000000LL);
}

static uint64_t now_ms(void) {
    return (uint64_t)(esp_timer_get_time() / 1000LL);
}

static void persist_seq(void) {
    nvs_handle_t h;
    if (nvs_open("cdm", NVS_READWRITE, &h) != ESP_OK) {
        return;
    }
    uint32_t seq = s_rx.seq;
    nvs_set_u32(h, "rx_seq", seq);
    nvs_set_u8(h, "rx_has", s_rx.has_seq ? 1 : 0);
    nvs_commit(h);
    nvs_close(h);
}

static void restore_seq(void) {
    nvs_handle_t h;
    if (nvs_open("cdm", NVS_READONLY, &h) != ESP_OK) {
        return;
    }
    uint32_t seq = 0;
    uint8_t has = 0;
    if (nvs_get_u8(h, "rx_has", &has) == ESP_OK && has &&
        nvs_get_u32(h, "rx_seq", &seq) == ESP_OK) {
        s_rx.has_seq = 1;
        s_rx.seq = seq;
        ESP_LOGI(TAG, "restored receiver seq %lu", (unsigned long)seq);
    }
    nvs_close(h);
}

/* Extract up to 5 windows (2 rows each) from the cached raw line. */
static int collect_dashboard(char rows[][65], int max_rows) {
    int n = 0;
    int windows = 0;
    const uint8_t *beg = s_last_good;
    const uint8_t *end = s_last_good + s_last_good_len;
    const uint8_t *p = beg;
    while (n + 1 < max_rows && windows < 5 && p < end) {
        const char *tok = "\"provider_id\"";
        size_t tl = strlen(tok);
        const uint8_t *found = NULL;
        for (const uint8_t *q = p; q + tl <= end; q++) {
            if (memcmp(q, tok, tl) == 0) {
                found = q;
                break;
            }
        }
        if (!found) {
            break;
        }
        char provider[32] = {0}, window[32] = {0};
        const uint8_t *scope_end = found + 2048 > end ? end : found + 2048;
        meter_json_find_string(found, scope_end, "provider_id", provider, sizeof provider);
        meter_json_find_string(found, scope_end, "window_id", window, sizeof window);
        double pct = 0;
        int is_null = 1;
        char pct_s[16] = {0};
        if (meter_json_find_number(found, scope_end, "percent_used", &pct, &is_null) && !is_null) {
            snprintf(pct_s, sizeof pct_s, "%g", pct);
        }
        char unit[16] = {0}, resets[32] = {0}, obs[32] = {0};
        meter_json_find_string(found, scope_end, "unit", unit, sizeof unit);
        meter_json_find_string(found, scope_end, "resets_at", resets, sizeof resets);
        meter_json_find_string(found, scope_end, "observed_at", obs, sizeof obs);
        gui_dashboard_line(provider[0] ? provider : NULL, window[0] ? window : NULL,
                           pct_s[0] ? pct_s : NULL, unit[0] ? unit : NULL,
                           rows[n], 65);
        gui_dashboard_time_line(resets[0] ? resets : NULL, obs[0] ? obs : NULL,
                                rows[n + 1], 65);
        n += 2;
        windows++;
        p = found + tl;
    }
    return n;
}

static void render(void) {
    char header[65];
    snprintf(header, sizeof header, "CDM METER %s", gui_screen_name(s_screen));
    if (s_screen == 0) {
        char rows[10][65];
        memset(rows, 0, sizeof rows);
        int n = 0;
        if (s_rx.has_payload) {
            n = collect_dashboard(rows, 10);
        }
        if (n == 0) {
            snprintf(rows[0], sizeof rows[0], "BOOT: default (awaiting PC frame)");
            snprintf(rows[1], sizeof rows[1], "send cdm/1 via USB 115200 8N1");
            n = 2;
        }
        bsp_lcd_show_text(rows, n, header);
    } else if (s_screen == 1) {
        gui_screen_text_t t;
        if (s_rx.has_payload) {
            const uint8_t *beg = s_last_good;
            const uint8_t *end = s_last_good + s_last_good_len;
            char latest[32] = {0}, cap[32] = {0};
            int has = 0;
            /* Prefer codex-resets.com; fall back to any latest_reset_at. */
            const char *want = "\"codex-resets.com\"";
            const uint8_t *f = NULL;
            for (const uint8_t *q = beg; q + strlen(want) <= end; q++) {
                if (memcmp(q, want, strlen(want)) == 0) {
                    f = q;
                    break;
                }
            }
            const uint8_t *scope = f ? f : beg;
            const uint8_t *scope_end = scope + 1024 > end ? end : scope + 1024;
            if (meter_json_find_string(scope, scope_end, "latest_reset_at", latest, sizeof latest) && latest[0]) {
                has = 1;
            }
            meter_json_find_string(scope, scope_end, "captured_at", cap, sizeof cap);
            char age[32];
            snprintf(age, sizeof age, "%llus (rx-age)",
                     (unsigned long long)(now_s() - s_rx.received_monotonic_s));
            gui_global_text("codex-resets.com", latest[0] ? latest : NULL,
                            cap[0] ? cap : NULL, age, has, &t);
        } else {
            gui_global_text("codex-resets.com", NULL, NULL, NULL, 0, &t);
        }
        bsp_lcd_show_text(t.lines, t.count, header);
    } else {
        gui_screen_text_t t;
        char good[32] = {0};
        if (s_rx.has_payload) {
            snprintf(good, sizeof good, "%s", s_rx.sent_at);
        }
        gui_status_text(s_link_ok, s_rx.last_error[0] ? s_rx.last_error : NULL,
                        s_rx.stale, good[0] ? good : NULL,
                        s_link_ok ? "host-polls-5s" : "reopen<=1Hz", &t);
        bsp_lcd_show_text(t.lines, t.count, header);
    }
    bsp_lcd_flush();
    /* Backlight follows the separated feature module (never the core path). */
    bsp_backlight_set_brightness(255 - autodim_duty(&s_dim, now_s()));
}

static void rx_task(void *arg) {
    (void)arg;
    uint8_t chunk[1024];
    int empty_polls = 0;
    for (;;) {
        int n = usb_serial_jtag_read_bytes(chunk, sizeof chunk, pdMS_TO_TICKS(50));
        if (n <= 0) {
            if (++empty_polls > 100) {
                /* ~5 s without bytes: host reopen budget. Mark link lost but
                 * never reset the receiver sequence (contract). */
                s_link_ok = usb_serial_jtag_is_connected() ? 1 : 0;
                empty_polls = 0;
            }
            continue;
        }
        empty_polls = 0;
        s_link_ok = 1;
        s_dim.link_ok = 1;
        for (int i = 0; i < n; i++) {
            if (s_line_len >= METER_MAX_LINE + 1) {
                /* Oversized: reject, keep last-good, resync at next LF. */
                meter_receiver_update_stale(&s_rx, now_s());
                snprintf(s_rx.last_error, sizeof s_rx.last_error, "FRAME_OVERSIZED");
                if (chunk[i] == '\n') {
                    s_line_len = 0;
                }
                continue;
            }
            s_line[s_line_len++] = chunk[i];
            if (chunk[i] == '\n') {
                int rc = meter_receiver_accept(&s_rx, s_line, s_line_len, now_s(), NULL);
                if (rc == METER_FRAME_OK) {
                    memcpy(s_last_good, s_line, s_line_len);
                    s_last_good_len = s_line_len;
                    s_dim.last_activity_s = now_s();
                    persist_seq();
                    ESP_LOGI(TAG, "accepted seq %lu crc %s", (unsigned long)s_rx.seq,
                             s_rx.last_good_crc);
                } else {
                    ESP_LOGW(TAG, "rejected %s (kept seq %s%lu)", s_rx.last_error,
                             s_rx.has_seq ? "" : "none ",
                             (unsigned long)(s_rx.has_seq ? s_rx.seq : 0));
                }
                s_line_len = 0;
            }
        }
    }
}

static void ui_task(void *arg) {
    (void)arg;
    uint64_t last_flush_s = 0;
    render();
    for (;;) {
        vTaskDelay(pdMS_TO_TICKS(50));
        if (bsp_input_poll_press(now_ms())) {
            s_screen = (s_screen + 1) % 3;
            s_screen_deadline_ms = now_ms() + BSP_INPUT_SCREEN_MS;
            s_dim.last_activity_s = now_s();
            ESP_LOGI(TAG, "BOOT -> %s", gui_screen_name(s_screen));
            render();
            (void)s_screen_deadline_ms;
        }
        meter_receiver_update_stale(&s_rx, now_s());
        if (now_s() != last_flush_s) {
            last_flush_s = now_s();
            render(); /* 1 Hz refresh for ages/stale; LCD stays lit. */
        }
    }
}

void app_main(void) {
    ESP_ERROR_CHECK(nvs_flash_init());
    meter_receiver_init(&s_rx);
    restore_seq();
    /* Last-good payload lives in PSRAM so a 64K frame never touches DRAM. */
    s_line = heap_caps_malloc(METER_MAX_LINE + 2, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    s_last_good = heap_caps_malloc(METER_MAX_LINE + 2, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (!s_line || !s_last_good) {
        ESP_LOGE(TAG, "PSRAM line buffers unavailable");
        return;
    }
    ESP_ERROR_CHECK(bsp_lcd_init());
    ESP_ERROR_CHECK(bsp_input_init());
    autodim_init(&s_dim, now_s());

    usb_serial_jtag_driver_config_t cfg = USB_SERIAL_JTAG_DRIVER_CONFIG_DEFAULT();
    cfg.rx_buffer_size = 8192;
    cfg.tx_buffer_size = 1024;
    esp_err_t rc = usb_serial_jtag_driver_install(&cfg);
    if (rc != ESP_OK) {
        ESP_LOGW(TAG, "usb_serial_jtag install rc=%d; receiver still polls", rc);
    }
    ESP_LOGI(TAG, "CDM meter boot: USB cdm/1 115200 8N1, LCD 820x320, BOOT cycles screens");

    xTaskCreatePinnedToCore(rx_task, "cdm_rx", 6144, NULL, 6, NULL, 0);
    xTaskCreatePinnedToCore(ui_task, "cdm_ui", 8192, NULL, 5, NULL, 1);
}
