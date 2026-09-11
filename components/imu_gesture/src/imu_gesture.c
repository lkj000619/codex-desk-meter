#include "imu_gesture.h"
#include <stdio.h>
#include "esp_log.h"
#include "driver/i2c.h"
#include "esp_timer.h"

static const char *TAG = "imu_gesture";

static imu_gesture_detector_t s_detector;
static bool s_hardware_ready = false;

#define I2C_MASTER_NUM           I2C_NUM_0
#define I2C_MASTER_SCL_IO        7
#define I2C_MASTER_SDA_IO        15
#define I2C_MASTER_FREQ_HZ       400000
#define QMI8658_ADDR             0x6B

#define QMI8658_WHO_AM_I         0x00
#define QMI8658_CTRL1            0x02
#define QMI8658_CTRL2            0x03
#define QMI8658_CTRL7            0x08
#define QMI8658_AX_L             0x35

static esp_err_t qmi8658_write_reg(uint8_t reg, uint8_t val) {
    uint8_t buf[2] = {reg, val};
    return i2c_master_write_to_device(I2C_MASTER_NUM, QMI8658_ADDR, buf, sizeof(buf), pdMS_TO_TICKS(100));
}

static esp_err_t qmi8658_read_regs(uint8_t reg, uint8_t *data, size_t len) {
    return i2c_master_write_read_device(I2C_MASTER_NUM, QMI8658_ADDR, &reg, 1, data, len, pdMS_TO_TICKS(100));
}

esp_err_t imu_gesture_hardware_init(void) {
    imu_gesture_detector_init(&s_detector);

    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = I2C_MASTER_FREQ_HZ,
    };
    esp_err_t err = i2c_param_config(I2C_MASTER_NUM, &conf);
    if (err != ESP_OK) return err;
    err = i2c_driver_install(I2C_MASTER_NUM, conf.mode, 0, 0, 0);
    if (err != ESP_OK && err != ESP_ERR_INVALID_STATE) return err;

    uint8_t who = 0;
    err = qmi8658_read_regs(QMI8658_WHO_AM_I, &who, 1);
    if (err == ESP_OK && who == 0x05) {
        ESP_LOGI(TAG, "QMI8658 identified successfully (0x%02X)", who);
        qmi8658_write_reg(QMI8658_CTRL1, 0x60); /* 50Hz INT1 */
        qmi8658_write_reg(QMI8658_CTRL2, 0x23); /* +/-4g, 100Hz ODR */
        qmi8658_write_reg(QMI8658_CTRL7, 0x03); /* Enable Accel & Gyro */
        s_hardware_ready = true;
    } else {
        ESP_LOGW(TAG, "QMI8658 not detected or different WHO_AM_I (0x%02X), err=%d", who, err);
        s_hardware_ready = false;
    }
    return ESP_OK;
}

imu_gesture_event_t imu_gesture_poll_hardware(void) {
    if (!s_hardware_ready) return IMU_GESTURE_NONE;

    uint8_t raw[6] = {0};
    if (qmi8658_read_regs(QMI8658_AX_L, raw, 6) != ESP_OK) {
        return IMU_GESTURE_NONE;
    }

    int16_t raw_x = (int16_t)(raw[0] | (raw[1] << 8));
    int16_t raw_y = (int16_t)(raw[2] | (raw[3] << 8));
    int16_t raw_z = (int16_t)(raw[4] | (raw[5] << 8));

    /* 4g range: 8192 LSB/g */
    float ax = (float)raw_x / 8192.0f;
    float ay = (float)raw_y / 8192.0f;
    float az = (float)raw_z / 8192.0f;

    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000LL);
    return imu_gesture_process_sample(&s_detector, ax, ay, az, now_ms);
}

bool imu_gesture_is_hardware_ready(void) {
    return s_hardware_ready;
}
