#ifndef BOARD_INPUT_H
#define BOARD_INPUT_H

#include "esp_err.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    INPUT_EVENT_NONE = 0,
    INPUT_EVENT_SHORT_CLICK,   /* Cycle screen */
    INPUT_EVENT_LONG_PRESS     /* Manual refresh trigger */
} board_input_event_t;

esp_err_t board_input_init(void);
board_input_event_t board_input_poll(void);

#ifdef __cplusplus
}
#endif

#endif /* BOARD_INPUT_H */
