#pragma once
/* Host-only stub for ESP_RETURN_ON_ERROR used by production bsp_input.c. */
#define ESP_RETURN_ON_ERROR(x, tag, msg) \
    do {                                 \
        if ((x) != 0) {                  \
            return (x);                  \
        }                                \
    } while (0)
typedef int esp_err_t;
#ifndef ESP_OK
#define ESP_OK 0
#endif
