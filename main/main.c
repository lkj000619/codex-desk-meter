#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_heap_caps.h"

#include "meter_types.h"
#include "meter_parser.h"
#include "meter_state.h"
#include "feature_imu.h"
#include "meter_gui.h"

#include "bsp_board.h"
#include "bsp_lcd.h"
#include "bsp_button.h"
#include "bsp_imu.h"
#include "bsp_serial.h"

static const char *TAG = "app_main";

static meter_state_t s_meter_state;
static meter_gui_t s_meter_gui;
static imu_feature_state_t s_imu_state;
static SemaphoreHandle_t s_state_mutex = NULL;

/* Reference clock tracking */
static int64_t s_base_epoch_sec = 0;
static int64_t s_base_uptime_us = 0;

static int64_t get_current_epoch_seconds(void)
{
    int64_t now_us = esp_timer_get_time();
    if (s_base_epoch_sec > 0) {
        int64_t elapsed_sec = (now_us - s_base_uptime_us) / 1000000LL;
        return s_base_epoch_sec + elapsed_sec;
    }
    /* Fallback monotonic time before first frame arrives */
    return now_us / 1000000LL;
}

static void on_frame_received(const char *line, size_t len)
{
    meter_frame_t frame;
    char err_code[32] = {0};

    int64_t now_sec = get_current_epoch_seconds();
    bool parse_ok = meter_parse_frame(line, len, &frame, err_code);

    if (xSemaphoreTake(s_state_mutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        if (!parse_ok) {
            ESP_LOGW(TAG, "Frame rejected: %s", err_code);
            meter_state_record_error(&s_meter_state, err_code, "parse or CRC failure");
        } else {
            /* Sync clock to valid sent_at */
            int64_t sent_sec = 0;
            if (meter_parse_rfc3339(frame.sent_at, &sent_sec)) {
                s_base_epoch_sec = sent_sec;
                s_base_uptime_us = esp_timer_get_time();
                now_sec = sent_sec;
            }

            char proc_err[32] = {0};
            if (!meter_state_process_frame(&s_meter_state, &frame, now_sec, proc_err)) {
                ESP_LOGW(TAG, "Frame state update rejected: %s", proc_err);
            } else {
                ESP_LOGI(TAG, "Frame accepted: seq=%" PRIu32 ", usage=%" PRIu32 ", resets=%" PRIu32,
                         frame.sequence, (uint32_t)frame.usage_count, (uint32_t)frame.global_reset_count);
            }
        }
        xSemaphoreGive(s_state_mutex);
    }
}

static void serial_rx_task(void *arg)
{
    ESP_LOGI(TAG, "Serial RX task started");
    while (1) {
        bsp_serial_poll();
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

static void input_sensor_task(void *arg)
{
    ESP_LOGI(TAG, "Input & sensor task started");
    while (1) {
        uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000LL);

        /* Poll BOOT button */
        if (bsp_button_poll_press()) {
            if (xSemaphoreTake(s_state_mutex, pdMS_TO_TICKS(50)) == pdTRUE) {
                if (meter_state_cycle_screen(&s_meter_state, now_ms)) {
                    ESP_LOGI(TAG, "Screen cycled to: %d", s_meter_state.screen_mode);
                }
                xSemaphoreGive(s_state_mutex);
            }
        }

        /* Poll QMI8658 IMU */
        float ax = 0, ay = 0, az = 0;
        if (bsp_imu_read_accel(&ax, &ay, &az) == ESP_OK) {
            if (feature_imu_update(&s_imu_state, ax, ay, az, now_ms)) {
                display_orientation_t new_orient = feature_imu_get_orientation(&s_imu_state);
                ESP_LOGI(TAG, "IMU orientation updated: %d", (int)new_orient);
                if (xSemaphoreTake(s_state_mutex, pdMS_TO_TICKS(50)) == pdTRUE) {
                    meter_state_set_orientation(&s_meter_state, new_orient);
                    xSemaphoreGive(s_state_mutex);
                }
            }

            if (feature_imu_consume_shake(&s_imu_state)) {
                ESP_LOGI(TAG, "IMU shake gesture detected!");
                if (xSemaphoreTake(s_state_mutex, pdMS_TO_TICKS(50)) == pdTRUE) {
                    meter_state_cycle_screen(&s_meter_state, now_ms);
                    xSemaphoreGive(s_state_mutex);
                }
            }
        }

        vTaskDelay(pdMS_TO_TICKS(30));
    }
}

static void gui_render_task(void *arg)
{
    ESP_LOGI(TAG, "GUI render task started");
    while (1) {
        int64_t now_sec = get_current_epoch_seconds();
        uint32_t uptime_ms = (uint32_t)(esp_timer_get_time() / 1000LL);

        display_orientation_t orient = ORIENTATION_LANDSCAPE_NORMAL;
        if (xSemaphoreTake(s_state_mutex, pdMS_TO_TICKS(50)) == pdTRUE) {
            meter_state_update_stale(&s_meter_state, now_sec);
            orient = s_meter_state.orientation;
            meter_gui_render(&s_meter_gui, &s_meter_state, now_sec, uptime_ms);
            xSemaphoreGive(s_state_mutex);
        }

        /* Flush canvas to hardware LCD */
        bsp_lcd_flush(s_meter_gui.canvas, orient);

        vTaskDelay(pdMS_TO_TICKS(50)); /* ~20 FPS refresh */
    }
}

void app_main(void)
{
    ESP_LOGI(TAG, "==================================================");
    ESP_LOGI(TAG, "Waveshare ESP32-S3-LCD-3.16 Meter Firmware v2");
    ESP_LOGI(TAG, "Run ID: 20261005-antigravity-cli-agy-flash-r01");
    ESP_LOGI(TAG, "==================================================");

    s_state_mutex = xSemaphoreCreateMutex();
    assert(s_state_mutex);

    meter_state_init(&s_meter_state);
    feature_imu_init(&s_imu_state);

    /* Allocate GUI landscape canvas in PSRAM (524,800 bytes) */
    uint16_t *canvas_buf = (uint16_t *)heap_caps_malloc(
        LCD_LANDSCAPE_WIDTH * LCD_LANDSCAPE_HEIGHT * sizeof(uint16_t),
        MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT
    );
    if (!canvas_buf) {
        ESP_LOGW(TAG, "PSRAM canvas alloc failed, falling back to default heap");
        canvas_buf = (uint16_t *)malloc(LCD_LANDSCAPE_WIDTH * LCD_LANDSCAPE_HEIGHT * sizeof(uint16_t));
    }
    assert(canvas_buf);
    meter_gui_init(&s_meter_gui, canvas_buf);

    /* Initialize LCD hardware */
    esp_err_t err = bsp_lcd_init();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "BSP LCD init failed: %s", esp_err_to_name(err));
    }

    /* Initial boot screen rendering (C2 requirement: LCD stays on >30s) */
    meter_gui_render(&s_meter_gui, &s_meter_state, 0, 0);
    bsp_lcd_flush(s_meter_gui.canvas, ORIENTATION_LANDSCAPE_NORMAL);

    /* Initialize BOOT button on GPIO 0 */
    bsp_button_init();

    /* Initialize QMI8658 6-axis IMU */
    bsp_imu_init();

    /* Initialize USB Serial Receiver */
    bsp_serial_init(on_frame_received);

    /* Create background worker tasks */
    xTaskCreatePinnedToCore(serial_rx_task, "serial_rx", 4096, NULL, 5, NULL, 0);
    xTaskCreatePinnedToCore(input_sensor_task, "input_sensor", 3072, NULL, 3, NULL, 0);
    xTaskCreatePinnedToCore(gui_render_task, "gui_render", 6144, NULL, 4, NULL, 1);

    ESP_LOGI(TAG, "All subsystems running");
}
