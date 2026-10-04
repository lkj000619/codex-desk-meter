#ifndef BSP_BUTTON_H
#define BSP_BUTTON_H

#include "esp_err.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Initialize BOOT button on GPIO 0 with internal pull-up */
esp_err_t bsp_button_init(void);

/* Check if BOOT button was pressed (with internal debounce).
 * Returns true if a transition from released to pressed occurred. */
bool bsp_button_poll_press(void);

#ifdef __cplusplus
}
#endif

#endif /* BSP_BUTTON_H */
