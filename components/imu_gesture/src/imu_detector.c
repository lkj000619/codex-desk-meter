#include "imu_detector.h"
#include <math.h>
#include <string.h>

void imu_gesture_detector_init(imu_gesture_detector_t *det) {
    if (!det) return;
    memset(det, 0, sizeof(imu_gesture_detector_t));
    det->prev_raw_mag = 1.0f; /* nominal 1g gravity */
}

imu_gesture_event_t imu_gesture_process_sample(imu_gesture_detector_t *det, float ax, float ay, float az, uint32_t now_ms) {
    if (!det) return IMU_GESTURE_NONE;

    float mag = sqrtf(ax * ax + ay * ay + az * az);
    /* High-pass filter to remove 1g static gravity */
    float hp = 0.85f * (det->prev_filtered_mag + mag - det->prev_raw_mag);
    det->prev_filtered_mag = hp;
    det->prev_raw_mag = mag;

    float abs_hp = fabsf(hp);

    /* Shake detection: sustained oscillating peaks >= 0.45g within 600ms */
    if (abs_hp >= 0.45f) {
        if (now_ms - det->last_shake_time_ms < 600) {
            det->shake_count++;
            if (det->shake_count >= 3) {
                det->shake_count = 0;
                det->tap_count = 0;
                det->last_shake_time_ms = now_ms;
                return IMU_GESTURE_SHAKE;
            }
        } else {
            det->shake_count = 1;
        }
        det->last_shake_time_ms = now_ms;
    }

    /* Tap detection: sharp peak >= 0.50g */
    if (abs_hp >= 0.50f) {
        if (det->tap_count > 0) {
            uint32_t dt = now_ms - det->last_tap_time_ms;
            if (dt >= 80 && dt <= 550) {
                /* Second tap within 80..550ms window */
                det->tap_count = 0;
                det->last_tap_time_ms = 0;
                return IMU_GESTURE_DOUBLE_TAP;
            } else if (dt > 550) {
                det->tap_count = 1;
                det->last_tap_time_ms = now_ms;
            }
        } else {
            det->tap_count = 1;
            det->last_tap_time_ms = now_ms;
        }
    } else {
        if (det->tap_count > 0 && (now_ms - det->last_tap_time_ms > 550)) {
            det->tap_count = 0;
        }
    }

    return IMU_GESTURE_NONE;
}
