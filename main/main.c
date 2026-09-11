#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "nvs_flash.h"

#include "user_config.h"
#include "meter_model.h"
#include "meter_parser.h"
#include "display_ui.h"
#include "board_input.h"
#include "fixture_data.h"
#include "imu_gesture.h"

static const char *TAG = "main";

static meter_state_t s_meter_state;

static void load_meter_fixtures(const char *now_str) {
    ESP_LOGI(TAG, "Loading synthetic fixtures at now=%s", now_str);

    /* 1. Parse Personal Usage */
    meter_parse_usage_json(g_fixture_personal_usage_json, now_str, NULL, &s_meter_state.usage);

    /* 2. Parse codex-reset.com forecast */
    meter_parse_global_reset_json(g_fixture_codex_reset_forecast_json, "codex-reset.com", now_str, NULL, &s_meter_state.reset_forecast);

    /* 3. Parse codex-resets.com history */
    meter_parse_global_reset_json(g_fixture_codex_resets_history_json, "codex-resets.com", now_str, NULL, &s_meter_state.reset_history);

    s_meter_state.last_success_update_sec = (uint32_t)(esp_timer_get_time() / 1000000LL);
}

void app_main(void) {
    ESP_LOGI(TAG, "=== Codex Desk Meter Version 2 Starting ===");
    ESP_LOGI(TAG, "Target Board: Waveshare ESP32-S3-LCD-3.16");
    ESP_LOGI(TAG, "Framework: ESP-IDF v5.3.2");

    /* Initialize NVS */
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    /* Initialize Display & Backlight */
    display_ui_init();

    /* Initialize BOOT Input */
    board_input_init();

    /* Initialize Autonomous Hardware Feature: IMU QMI8658 Gesture Sensor */
    imu_gesture_hardware_init();

    /* Initialize State & Load Fixtures */
    memset(&s_meter_state, 0, sizeof(s_meter_state));
    s_meter_state.current_screen = 0;
    load_meter_fixtures("2026-09-11T00:00:00Z");

    /* Initial Render */
    display_ui_render(&s_meter_state);

    ESP_LOGI(TAG, "Initial display rendered. Entering main operational loop.");

    uint32_t last_auto_refresh_ms = (uint32_t)(esp_timer_get_time() / 1000LL);

    while (1) {
        uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000LL);
        bool need_render = false;

        /* 1. Poll BOOT Button */
        board_input_event_t btn_evt = board_input_poll();
        if (btn_evt == INPUT_EVENT_SHORT_CLICK) {
            display_ui_cycle_screen();
            s_meter_state.current_screen = display_ui_get_screen();
            ESP_LOGI(TAG, "BOOT clicked -> switched to screen %lu", (unsigned long)s_meter_state.current_screen);
            need_render = true;
        } else if (btn_evt == INPUT_EVENT_LONG_PRESS) {
            ESP_LOGI(TAG, "BOOT long press -> triggering manual refresh");
            load_meter_fixtures("2026-09-11T00:00:00Z");
            last_auto_refresh_ms = now_ms;
            need_render = true;
        }

        /* 2. Poll IMU Gesture (Candidate 1 Feature) */
        imu_gesture_event_t imu_evt = imu_gesture_poll_hardware();
        if (imu_evt == IMU_GESTURE_DOUBLE_TAP) {
            display_ui_cycle_screen();
            s_meter_state.current_screen = display_ui_get_screen();
            ESP_LOGI(TAG, "IMU Double-Tap detected -> switched to screen %lu", (unsigned long)s_meter_state.current_screen);
            need_render = true;
        } else if (imu_evt == IMU_GESTURE_SHAKE) {
            ESP_LOGI(TAG, "IMU Shake detected -> triggering manual refresh");
            load_meter_fixtures("2026-09-11T00:00:00Z");
            last_auto_refresh_ms = now_ms;
            need_render = true;
        }

        /* 3. Check Auto Refresh Timer (60 seconds) */
        if (now_ms - last_auto_refresh_ms >= (METER_AUTO_REFRESH_INTERVAL_SEC * 1000)) {
            ESP_LOGI(TAG, "Auto refresh interval reached (60s). Refreshing fixtures.");
            load_meter_fixtures("2026-09-11T00:00:00Z");
            last_auto_refresh_ms = now_ms;
            need_render = true;
        }

        if (need_render) {
            display_ui_render(&s_meter_state);
        }

        vTaskDelay(pdMS_TO_TICKS(50));
    }
}
