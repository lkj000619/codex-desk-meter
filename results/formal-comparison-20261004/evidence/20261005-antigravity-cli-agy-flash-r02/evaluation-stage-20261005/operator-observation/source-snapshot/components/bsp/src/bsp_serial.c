#include "bsp_serial.h"
#include "driver/usb_serial_jtag.h"
#include "driver/usb_serial_jtag_vfs.h"
#include "driver/uart.h"
#include "esp_log.h"
#include <string.h>
#include <stdlib.h>

#define UART_PORT UART_NUM_0
#define RX_BUF_SIZE 4096
#define MAX_LINE_SIZE (64 * 1024)

static const char *TAG = "bsp_serial";
static bsp_serial_line_cb_t s_callback = NULL;
static char *s_line_buf = NULL;
static size_t s_line_len = 0;
static bool s_usj_installed = false;

esp_err_t bsp_serial_init(bsp_serial_line_cb_t callback)
{
    s_callback = callback;
    s_line_buf = (char *)malloc(MAX_LINE_SIZE);
    if (!s_line_buf) return ESP_ERR_NO_MEM;
    s_line_len = 0;

    /* 1. Install USB-Serial-JTAG driver for native USB Type-C port on ESP32-S3 */
    usb_serial_jtag_driver_config_t usj_config = {
        .tx_buffer_size = 4096,
        .rx_buffer_size = 32768,
    };
    esp_err_t usj_ret = usb_serial_jtag_driver_install(&usj_config);
    if (usj_ret == ESP_OK) {
        usb_serial_jtag_vfs_use_driver();
        s_usj_installed = true;
        ESP_LOGI(TAG, "USB-Serial-JTAG driver installed (RX: 32KB, TX: 4KB)");
    } else {
        ESP_LOGW(TAG, "USB-Serial-JTAG driver install returned: %s", esp_err_to_name(usj_ret));
    }

    /* 2. Configure secondary UART0 (GPIO43/44) */
    uart_config_t uart_config = {
        .baud_rate = 115200,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    esp_err_t ret = uart_param_config(UART_PORT, &uart_config);
    if (ret == ESP_OK) {
        uart_driver_install(UART_PORT, RX_BUF_SIZE * 2, 0, 0, NULL, 0);
        ESP_LOGI(TAG, "UART0 receiver initialized at 115200 8N1");
    }

    ESP_LOGI(TAG, "USB Serial Receiver ready");
    return ESP_OK;
}

void bsp_serial_poll(void)
{
    uint8_t chunk[256];
    int len = 0;

    /* Read native USB-Serial-JTAG endpoint first */
    if (s_usj_installed) {
        len = usb_serial_jtag_read_bytes(chunk, sizeof(chunk), pdMS_TO_TICKS(5));
    }

    /* Fallback to UART0 if no USB data */
    if (len <= 0) {
        len = uart_read_bytes(UART_PORT, chunk, sizeof(chunk), 0);
    }

    if (len <= 0) return;

    for (int i = 0; i < len; ++i) {
        char c = (char)chunk[i];
        if (s_line_len < MAX_LINE_SIZE - 1) {
            s_line_buf[s_line_len++] = c;
        } else {
            /* Overflow: reset line buffer */
            ESP_LOGW(TAG, "Line buffer overflow, resetting");
            s_line_len = 0;
            continue;
        }

        if (c == '\n') {
            s_line_buf[s_line_len] = '\0';
            if (s_callback) {
                s_callback(s_line_buf, s_line_len);
            }
            s_line_len = 0;
        }
    }
}
