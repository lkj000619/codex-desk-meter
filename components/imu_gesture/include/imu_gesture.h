#ifndef IMU_GESTURE_H
#define IMU_GESTURE_H

#include "imu_detector.h"
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Hardware BSP functions for ESP-IDF target */
esp_err_t imu_gesture_hardware_init(void);
imu_gesture_event_t imu_gesture_poll_hardware(void);
bool imu_gesture_is_hardware_ready(void);

#ifdef __cplusplus
}
#endif

#endif /* IMU_GESTURE_H */
