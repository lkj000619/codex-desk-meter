#pragma once
#include <stdint.h>

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* BOOT button: GPIO0, active-low, pull-up (vendor button_bsp.c facts).
 * Shares LCD CS (GPIO0) so the pin is sampled only after LCD init and with
 * a 50 ms debounce. Single press cycles the 3 screens within 300 ms.
 * RST is the system reset and is never used as app input. */

#define BSP_INPUT_DEBOUNCE_MS 50
#define BSP_INPUT_SCREEN_MS 300

esp_err_t bsp_input_init(void);

/* Call from a 5 ms poll task. Returns 1 once per debounced press. */
int bsp_input_poll_press(uint64_t now_ms);

/* Pure helper for host tests: debounce a raw level trace. */
int bsp_input_debounce_step(int raw_level_active_low_pressed,
                            uint64_t now_ms, uint64_t *stable_since,
                            int *stable_pressed);

#ifdef __cplusplus
}
#endif
