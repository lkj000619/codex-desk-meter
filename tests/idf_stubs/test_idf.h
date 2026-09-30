#ifndef TEST_IDF_H
#define TEST_IDF_H
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
typedef int esp_err_t;
#define ESP_OK 0
#define ESP_LOG_WARN 2
#define ESP_ERROR_CHECK(call) do { if ((call) != ESP_OK) abort(); } while (0)
#define ESP_LOGE(tag, ...) ((void)(tag))
#define ESP_LOGI(tag, ...) ((void)(tag))
#define MALLOC_CAP_SPIRAM 1
#define MALLOC_CAP_8BIT 2
#define GPIO_NUM_0 0
#define GPIO_MODE_INPUT 1
#define GPIO_PULLUP_ENABLE 1
#define GPIO_PULLDOWN_DISABLE 0
#define GPIO_INTR_DISABLE 0
#define UART_NUM_0 0
#define UART_DATA_8_BITS 8
#define UART_PARITY_DISABLE 0
#define UART_STOP_BITS_1 1
#define UART_HW_FLOWCTRL_DISABLE 0
#define UART_SCLK_DEFAULT 0
#define UART_PIN_NO_CHANGE -1
#define portTICK_PERIOD_MS 1
#define pdMS_TO_TICKS(ms) (ms)
typedef struct { uint64_t pin_bit_mask; int mode, pull_up_en, pull_down_en, intr_type; } gpio_config_t;
typedef struct { int baud_rate, data_bits, parity, stop_bits, flow_ctrl, source_clk; } uart_config_t;
typedef struct { size_t rx_buffer_size, tx_buffer_size; } usb_serial_jtag_driver_config_t;
void esp_log_level_set(const char *, int);
void *heap_caps_malloc(size_t, int);
int gpio_get_level(int);
esp_err_t gpio_config(const gpio_config_t *);
uint32_t xTaskGetTickCount(void);
void vTaskDelay(uint32_t);
int uart_read_bytes(int, void *, size_t, uint32_t);
esp_err_t uart_driver_install(int, int, int, int, void *, int);
esp_err_t uart_param_config(int, const uart_config_t *);
esp_err_t uart_set_pin(int, int, int, int, int);
esp_err_t usb_serial_jtag_driver_install(const usb_serial_jtag_driver_config_t *);
int usb_serial_jtag_read_bytes(void *, size_t, uint32_t);
int usb_serial_jtag_write_bytes(const void *, size_t, uint32_t);
#endif
