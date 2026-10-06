#ifndef BSP_SERIAL_H
#define BSP_SERIAL_H

#include "esp_err.h"
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef void (*bsp_serial_line_cb_t)(const char *line, size_t len);

/* Initialize USB serial UART at 115200 baud 8N1 */
esp_err_t bsp_serial_init(bsp_serial_line_cb_t callback);

/* Process incoming UART bytes; call periodically from receiver task */
void bsp_serial_poll(void);

#ifdef __cplusplus
}
#endif

#endif /* BSP_SERIAL_H */
