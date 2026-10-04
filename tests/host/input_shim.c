/* Host shim: compile the real bsp_input.c debounce helper without IDF.
 * bsp_input.c includes driver/gpio.h and esp_check.h; provide minimal stubs
 * so the translation unit under test is the production file. */
#include <stdint.h>

int gpio_get_level(int pin) {
    (void)pin;
    return 1;
}
typedef int esp_err_t;
#define ESP_OK 0
