#include "board_input.h"
#include "user_config.h"
#include "driver/gpio.h"
#include "esp_timer.h"
#include "esp_log.h"

static const char *TAG = "board_input";

static bool s_last_level = 1;
static uint32_t s_press_start_time_ms = 0;
static bool s_long_reported = false;

esp_err_t board_input_init(void) {
    gpio_config_t conf = {
        .pin_bit_mask = (1ULL << BOARD_BOOT_BTN_PIN),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    esp_err_t err = gpio_config(&conf);
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "BOOT button initialized on GPIO%d", BOARD_BOOT_BTN_PIN);
    }
    return err;
}

board_input_event_t board_input_poll(void) {
    int level = gpio_get_level(BOARD_BOOT_BTN_PIN);
    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000LL);
    board_input_event_t result = INPUT_EVENT_NONE;

    if (level == 0 && s_last_level == 1) {
        /* Press Down */
        s_press_start_time_ms = now_ms;
        s_long_reported = false;
    } else if (level == 0 && s_last_level == 0) {
        /* Holding */
        if (!s_long_reported && (now_ms - s_press_start_time_ms >= 1200)) {
            s_long_reported = true;
            result = INPUT_EVENT_LONG_PRESS;
        }
    } else if (level == 1 && s_last_level == 0) {
        /* Released */
        uint32_t duration = now_ms - s_press_start_time_ms;
        if (duration >= 50 && duration < 1200 && !s_long_reported) {
            result = INPUT_EVENT_SHORT_CLICK;
        }
    }

    s_last_level = level;
    return result;
}
