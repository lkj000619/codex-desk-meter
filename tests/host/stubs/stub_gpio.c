#include "driver/gpio.h"

int gpio_get_level(int pin) {
    (void)pin;
    return 1;
}

int gpio_config(const gpio_config_t *cfg) {
    (void)cfg;
    return 0;
}
