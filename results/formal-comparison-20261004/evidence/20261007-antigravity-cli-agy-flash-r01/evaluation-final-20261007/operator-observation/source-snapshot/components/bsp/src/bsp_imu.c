#include "bsp_imu.h"
#include "bsp_board.h"
#include "driver/i2c_master.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "bsp_imu";
static i2c_master_bus_handle_t s_i2c_bus = NULL;
static i2c_master_dev_handle_t s_imu_dev = NULL;
static bool s_imu_available = false;

static esp_err_t write_reg(uint8_t reg, uint8_t val)
{
    if (!s_imu_dev) return ESP_ERR_INVALID_STATE;
    uint8_t buf[2] = {reg, val};
    return i2c_master_transmit(s_imu_dev, buf, 2, 100);
}

static esp_err_t read_reg(uint8_t reg, uint8_t *val)
{
    if (!s_imu_dev) return ESP_ERR_INVALID_STATE;
    return i2c_master_transmit_receive(s_imu_dev, &reg, 1, val, 1, 100);
}

static esp_err_t read_bytes(uint8_t reg, uint8_t *buf, size_t len)
{
    if (!s_imu_dev) return ESP_ERR_INVALID_STATE;
    return i2c_master_transmit_receive(s_imu_dev, &reg, 1, buf, len, 100);
}

esp_err_t bsp_imu_init(void)
{
    i2c_master_bus_config_t bus_cfg = {
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .i2c_port = I2C_NUM_0,
        .scl_io_num = PIN_I2C_SCL,
        .sda_io_num = PIN_I2C_SDA,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    esp_err_t ret = i2c_new_master_bus(&bus_cfg, &s_i2c_bus);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "I2C bus init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    i2c_device_config_t dev_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = I2C_ADDR_QMI8658,
        .scl_speed_hz = 300000,
    };
    ret = i2c_master_bus_add_device(s_i2c_bus, &dev_cfg, &s_imu_dev);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Failed to add QMI8658 to I2C bus: %s", esp_err_to_name(ret));
        return ret;
    }

    /* Check WHO_AM_I */
    uint8_t who_am_i = 0;
    ret = read_reg(0x00, &who_am_i);
    if (ret != ESP_OK || who_am_i != 0x05) {
        ESP_LOGW(TAG, "QMI8658 WHO_AM_I mismatch: 0x%02x (expected 0x05)", who_am_i);
        s_imu_available = false;
        return ESP_ERR_NOT_FOUND;
    }

    /* Configure QMI8658 */
    write_reg(0x02, 0x60); /* CTRL1: auto-increment */
    write_reg(0x03, 0x23); /* CTRL2: Accel +-8g, 100Hz ODR */
    write_reg(0x08, 0x01); /* CTRL7: Enable accelerometer */

    s_imu_available = true;
    ESP_LOGI(TAG, "QMI8658 6-axis IMU initialized (addr=0x6B, ID=0x05)");
    return ESP_OK;
}

esp_err_t bsp_imu_read_accel(float *ax, float *ay, float *az)
{
    if (!s_imu_available || !s_imu_dev) return ESP_ERR_INVALID_STATE;

    uint8_t raw[6] = {0};
    esp_err_t ret = read_bytes(0x35, raw, 6);
    if (ret != ESP_OK) return ret;

    int16_t raw_x = (int16_t)((raw[1] << 8) | raw[0]);
    int16_t raw_y = (int16_t)((raw[3] << 8) | raw[2]);
    int16_t raw_z = (int16_t)((raw[5] << 8) | raw[4]);

    /* For +-8g range, sensitivity is 4096 LSB/g */
    if (ax) *ax = (float)raw_x / 4096.0f;
    if (ay) *ay = (float)raw_y / 4096.0f;
    if (az) *az = (float)raw_z / 4096.0f;

    return ESP_OK;
}
