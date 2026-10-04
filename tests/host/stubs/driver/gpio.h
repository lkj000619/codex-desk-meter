#pragma once
/* Host-only stub so the production bsp_input.c compiles under test.
 * The debounce helper under test never touches GPIO. */
#include <stdint.h>
typedef int gpio_num_t;
typedef struct {
    unsigned long long pin_bit_mask;
    int mode;
    int pull_up_en;
    int pull_down_en;
    int intr_type;
} gpio_config_t;
#define GPIO_MODE_INPUT 1
#define GPIO_PULLUP_ENABLE 1
#define GPIO_PULLDOWN_DISABLE 0
#define GPIO_INTR_DISABLE 0
int gpio_get_level(int pin);
int gpio_config(const gpio_config_t *cfg);
