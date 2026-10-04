#include "bsp_button.h"
#include "bsp_board.h"
#include "esp_timer.h"
#include "esp_log.h"

static const char *TAG = "bsp_button";
static int s_last_level = 1;
static int64_t s_last_press_us = 0;

esp_err_t bsp_button_init(void)
{
    gpio_config_t conf = {
        .pin_bit_mask = (1ULL << PIN_BOOT_BUTTON),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    esp_err_t ret = gpio_config(&conf);
    if (ret == ESP_OK) {
        ESP_LOGI(TAG, "BOOT button initialized on GPIO 0");
    }
    s_last_level = gpio_get_level(PIN_BOOT_BUTTON);
    s_last_press_us = esp_timer_get_time();
    return ret;
}

bool bsp_button_poll_press(void)
{
    int level = gpio_get_level(PIN_BOOT_BUTTON);
    int64_t now_us = esp_timer_get_time();

    /* Active low: 0 is pressed */
    if (level == 0 && s_last_level == 1) {
        /* Transition from released to pressed */
        if (now_us - s_last_press_us > 300000LL) { /* 300ms debounce */
            s_last_press_us = now_us;
            s_last_level = level;
            return true;
        }
    }
    s_last_level = level;
    return false;
}
