#ifndef BSP_IMU_H
#define BSP_IMU_H

#include "esp_err.h"
#include "feature_imu.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Initialize I2C and QMI8658 6-axis IMU */
esp_err_t bsp_imu_init(void);

/* Read latest accelerometer values in g-force. Returns ESP_OK if read successful. */
esp_err_t bsp_imu_read_accel(float *ax, float *ay, float *az);

#ifdef __cplusplus
}
#endif

#endif /* BSP_IMU_H */
