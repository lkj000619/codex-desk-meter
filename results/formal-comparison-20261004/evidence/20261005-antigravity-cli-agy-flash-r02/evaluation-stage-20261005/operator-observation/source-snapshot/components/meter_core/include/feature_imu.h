#ifndef FEATURE_IMU_H
#define FEATURE_IMU_H

#include "meter_types.h"
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    float ax, ay, az; /* m/s^2 or g-force */
    float gx, gy, gz; /* deg/s */
} imu_raw_data_t;

typedef struct {
    display_orientation_t current_orientation;
    int consecutive_samples;
    display_orientation_t candidate_orientation;
    uint32_t last_orientation_change_ms;
    bool shake_detected;
    uint32_t last_shake_ms;
} imu_feature_state_t;

/* Initialize IMU feature state machine */
void feature_imu_init(imu_feature_state_t *state);

/* Process accelerometer measurement (in m/s^2 or normalized g)
 * Returns true if orientation changed, false otherwise. */
bool feature_imu_update(imu_feature_state_t *state, float ax, float ay, float az, uint32_t now_ms);

/* Check and clear shake gesture flag */
bool feature_imu_consume_shake(imu_feature_state_t *state);

/* Get current orientation */
display_orientation_t feature_imu_get_orientation(const imu_feature_state_t *state);

#ifdef __cplusplus
}
#endif

#endif /* FEATURE_IMU_H */
