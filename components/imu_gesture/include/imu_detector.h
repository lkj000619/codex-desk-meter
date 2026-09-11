#ifndef IMU_DETECTOR_H
#define IMU_DETECTOR_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    IMU_GESTURE_NONE = 0,
    IMU_GESTURE_DOUBLE_TAP,   /* Double tap on desk or meter body -> Cycle Screen */
    IMU_GESTURE_SHAKE         /* Sustained shake gesture -> Manual Refresh Trigger */
} imu_gesture_event_t;

typedef struct {
    uint32_t last_tap_time_ms;
    uint32_t tap_count;
    float prev_filtered_mag;
    float prev_raw_mag;
    uint32_t shake_count;
    uint32_t last_shake_time_ms;
} imu_gesture_detector_t;

/* Reset / initialize standalone algorithm detector state */
void imu_gesture_detector_init(imu_gesture_detector_t *det);

/* Pure algorithmic update: feed raw acceleration in g and timestamp in ms.
 * Free of any ESP-IDF or FreeRTOS dependencies.
 */
imu_gesture_event_t imu_gesture_process_sample(imu_gesture_detector_t *det, float ax, float ay, float az, uint32_t now_ms);

#ifdef __cplusplus
}
#endif

#endif /* IMU_DETECTOR_H */
