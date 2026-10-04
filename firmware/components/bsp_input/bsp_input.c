#include "bsp_input.h"

#include "driver/gpio.h"
#include "esp_check.h"

#define PIN_BOOT 0

static uint64_t s_stable_since = 0;
static int s_stable_pressed = 0;
static int s_last_reported = 0;
static int s_inited = 0;

int bsp_input_debounce_step(int pressed, uint64_t now_ms, uint64_t *stable_since,
                            int *stable_pressed) {
    if (pressed != *stable_pressed) {
        if (*stable_since == 0) {
            *stable_since = now_ms;
        }
        if (now_ms - *stable_since >= BSP_INPUT_DEBOUNCE_MS) {
            *stable_pressed = pressed;
            *stable_since = 0;
            return 1;
        }
        return 0;
    }
    *stable_since = 0;
    return 0;
}

esp_err_t bsp_input_init(void) {
    gpio_config_t gc = {
        .pin_bit_mask = (1ULL << PIN_BOOT),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_RETURN_ON_ERROR(gpio_config(&gc), "bsp_input", "gpio0");
    s_stable_since = 0;
    s_stable_pressed = 0;
    s_last_reported = 0;
    s_inited = 1;
    return ESP_OK;
}

int bsp_input_poll_press(uint64_t now_ms) {
    if (!s_inited) {
        return 0;
    }
    int level = gpio_get_level(PIN_BOOT);
    int pressed = (level == 0);
    bsp_input_debounce_step(pressed, now_ms, &s_stable_since, &s_stable_pressed);
    int is_pressed = s_stable_pressed;
    int edge = is_pressed && !s_last_reported;
    s_last_reported = is_pressed;
    return edge;
}
