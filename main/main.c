#include "cdm_display.h"
#include "cdm_receiver.h"
#include "cdm_rtc.h"

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <time.h>

#include "driver/gpio.h"
#include "driver/usb_serial_jtag.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define MAX_LINE 65536
#define BOOT_PIN GPIO_NUM_0

static const char *TAG = "codex_meter";
static CdmReceiver receiver;
static CdmScreen screen = CDM_SCREEN_DASHBOARD;
static CdmButtonDebouncer boot_button;
static char *line_buffer;
static size_t line_length;
static bool dropping_line;
static bool rtc_ready;
static bool display_dirty = true;
static void trace_receiver(const char *event) {
    char trace[96];
    int length = snprintf(trace, sizeof(trace), "CDM_%s sequence=%lu result=%d\n",
                          event, (unsigned long)receiver.sequence, (int)receiver.last_error);
    if (length > 0 && length < (int)sizeof(trace))
        usb_serial_jtag_write_bytes(trace, (size_t)length, 0);
}
static int64_t current_epoch(void) {
    time_t now = time(NULL);
    return now >= 0 ? (int64_t)now : 0;
}

static void apply_line(void) {
    if (line_length == 0 || dropping_line) {
        line_length = 0;
        dropping_line = false;
        return;
    }
    line_buffer[line_length] = '\0';
    int64_t now = current_epoch();
    CdmResult result = cdm_receiver_apply(&receiver, line_buffer, line_length, now);
    display_dirty = true;
    trace_receiver("RX");
    if (result == CDM_ACCEPTED) {
        struct timeval tv = {.tv_sec = receiver.last_good_epoch, .tv_usec = 0};
        settimeofday(&tv, NULL);
        rtc_ready = cdm_rtc_sync(receiver.last_good_epoch);
    }
    line_length = 0;
}

static void receive_serial(void) {
    uint8_t bytes[1024];
    int count = usb_serial_jtag_read_bytes(bytes, sizeof(bytes), 0);
    for (int i = 0; i < count; ++i) {
        uint8_t byte = bytes[i];
        if (byte == '\n') {
            apply_line();
            continue;
        }
        if (byte == '\r') {
            dropping_line = true;
            continue;
        }
        if (!dropping_line) {
            if (line_length >= MAX_LINE) dropping_line = true;
            else line_buffer[line_length++] = (char)byte;
        }
    }
}

void app_main(void) {
    esp_log_level_set("*", ESP_LOG_WARN);
    cdm_receiver_init(&receiver);
    line_buffer = heap_caps_malloc(MAX_LINE + 1, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (line_buffer == NULL) line_buffer = malloc(MAX_LINE + 1);
    if (line_buffer == NULL) {
        ESP_LOGE(TAG, "unable to allocate serial receive buffer");
        return;
    }

    // The board's USB connector enumerates the ESP32-S3 native Serial/JTAG port.
    usb_serial_jtag_driver_config_t usb_config = {
        .rx_buffer_size = MAX_LINE + 1, .tx_buffer_size = 1024};
    ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&usb_config));

    rtc_ready = cdm_rtc_init(NULL);
    if (!cdm_display_init()) {
        ESP_LOGE(TAG, "LCD initialization failed");
        return;
    }
    // GPIO0 is shared with the ST7701 3-wire command chip-select on this board.
    // The panel only uses that command line during initialization; restore BOOT input afterward.
    gpio_config_t boot_config = {.pin_bit_mask = 1ULL << BOOT_PIN, .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE, .pull_down_en = GPIO_PULLDOWN_DISABLE, .intr_type = GPIO_INTR_DISABLE};
    if (gpio_config(&boot_config) != ESP_OK) ESP_LOGE(TAG, "BOOT input init failed");

    uint32_t last_render = 0;
    for (;;) {
        receive_serial();
        uint32_t now_ms = (uint32_t)(xTaskGetTickCount() * portTICK_PERIOD_MS);
        bool raw_pressed = gpio_get_level(BOOT_PIN) == 0;
        if (cdm_button_update(&boot_button, raw_pressed, now_ms, 50) && boot_button.stable_pressed) {
            screen = cdm_screen_next(screen);
            display_dirty = true;
        }
        int64_t now = current_epoch();
        cdm_receiver_update_stale(&receiver, now);
        if (display_dirty || (uint32_t)(now_ms - last_render) >= 1000) {
            cdm_display_render(&receiver, screen, now, rtc_ready);
            if (display_dirty) trace_receiver("DISPLAY");
            display_dirty = false;
            last_render = now_ms;
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}
