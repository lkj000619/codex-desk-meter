#include "feature_imu.h"
#include <math.h>

#define DEBOUNCE_SAMPLES 3
#define ORIENTATION_HYSTERESIS_G 0.40f /* ~24 degrees tilt */
#define SHAKE_THRESHOLD_G 2.2f         /* > 2.2g indicates active shake */
#define SHAKE_COOLDOWN_MS 800

void feature_imu_init(imu_feature_state_t *state)
{
    if (!state) return;
    state->current_orientation = ORIENTATION_LANDSCAPE_NORMAL;
    state->candidate_orientation = ORIENTATION_LANDSCAPE_NORMAL;
    state->consecutive_samples = 0;
    state->last_orientation_change_ms = 0;
    state->shake_detected = false;
    state->last_shake_ms = 0;
}

bool feature_imu_update(imu_feature_state_t *state, float ax, float ay, float az, uint32_t now_ms)
{
    if (!state) return false;

    /* Detect shake: total acceleration magnitude */
    float mag = sqrtf(ax * ax + ay * ay + az * az);
    if (mag > SHAKE_THRESHOLD_G) {
        if (now_ms - state->last_shake_ms > SHAKE_COOLDOWN_MS) {
            state->shake_detected = true;
            state->last_shake_ms = now_ms;
        }
    }

    /* Determine candidate orientation from Y axis gravity component */
    display_orientation_t candidate = state->current_orientation;
    if (state->current_orientation == ORIENTATION_LANDSCAPE_NORMAL) {
        /* To flip to inverted landscape, ay must strongly exceed positive threshold */
        if (ay > ORIENTATION_HYSTERESIS_G) {
            candidate = ORIENTATION_LANDSCAPE_INVERTED;
        }
    } else {
        /* To flip back to normal landscape, ay must drop below negative threshold */
        if (ay < -ORIENTATION_HYSTERESIS_G) {
            candidate = ORIENTATION_LANDSCAPE_NORMAL;
        }
    }

    /* Debounce consecutive samples */
    if (candidate != state->current_orientation) {
        if (candidate == state->candidate_orientation) {
            state->consecutive_samples++;
            if (state->consecutive_samples >= DEBOUNCE_SAMPLES) {
                state->current_orientation = candidate;
                state->consecutive_samples = 0;
                state->last_orientation_change_ms = now_ms;
                return true; /* Changed! */
            }
        } else {
            state->candidate_orientation = candidate;
            state->consecutive_samples = 1;
        }
    } else {
        state->consecutive_samples = 0;
        state->candidate_orientation = state->current_orientation;
    }

    return false;
}

bool feature_imu_consume_shake(imu_feature_state_t *state)
{
    if (!state) return false;
    if (state->shake_detected) {
        state->shake_detected = false;
        return true;
    }
    return false;
}

display_orientation_t feature_imu_get_orientation(const imu_feature_state_t *state)
{
    return state ? state->current_orientation : ORIENTATION_LANDSCAPE_NORMAL;
}
