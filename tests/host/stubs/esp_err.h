#pragma once
/* Host-only stub for the IDF esp_err.h used by production bsp headers. */
typedef int esp_err_t;
#ifndef ESP_OK
#define ESP_OK 0
#endif
#ifndef ESP_FAIL
#define ESP_FAIL 1
#endif
