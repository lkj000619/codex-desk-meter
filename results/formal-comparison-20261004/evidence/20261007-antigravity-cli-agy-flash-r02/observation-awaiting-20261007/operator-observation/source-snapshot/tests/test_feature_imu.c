#include "feature_imu.h"
#include <stdio.h>
#include <assert.h>

static void test_imu_orientation_and_debounce(void)
{
    imu_feature_state_t imu;
    feature_imu_init(&imu);
    assert(feature_imu_get_orientation(&imu) == ORIENTATION_LANDSCAPE_NORMAL);

    uint32_t now = 1000;

    /* Jitter near zero (normal flat or small tilt) -> no change */
    assert(!feature_imu_update(&imu, 0.05f, 0.10f, 9.8f, now));
    assert(feature_imu_get_orientation(&imu) == ORIENTATION_LANDSCAPE_NORMAL);

    /* Hysteresis zone: ay = 0.30g (< 0.40g threshold) -> no change */
    assert(!feature_imu_update(&imu, 0.0f, 0.30f, 9.0f, now += 50));
    assert(feature_imu_get_orientation(&imu) == ORIENTATION_LANDSCAPE_NORMAL);

    /* Above threshold: ay = 0.60g (> 0.40g) */
    /* Sample 1: detected candidate, not yet confirmed */
    assert(!feature_imu_update(&imu, 0.0f, 0.60f, 8.0f, now += 50));
    assert(feature_imu_get_orientation(&imu) == ORIENTATION_LANDSCAPE_NORMAL);

    /* Sample 2: still candidate */
    assert(!feature_imu_update(&imu, 0.0f, 0.65f, 7.8f, now += 50));
    assert(feature_imu_get_orientation(&imu) == ORIENTATION_LANDSCAPE_NORMAL);

    /* Sample 3: debounce threshold reached -> orientation flips to INVERTED */
    assert(feature_imu_update(&imu, 0.0f, 0.70f, 7.5f, now += 50));
    assert(feature_imu_get_orientation(&imu) == ORIENTATION_LANDSCAPE_INVERTED);

    /* While in INVERTED, slight return to ay = 0.10g (> -0.40g) stays INVERTED due to hysteresis */
    assert(!feature_imu_update(&imu, 0.0f, 0.10f, 9.0f, now += 50));
    assert(feature_imu_get_orientation(&imu) == ORIENTATION_LANDSCAPE_INVERTED);

    /* Strongly negative tilt: ay = -0.60g (< -0.40g) */
    assert(!feature_imu_update(&imu, 0.0f, -0.60f, 8.0f, now += 50)); /* Sample 1 */
    assert(!feature_imu_update(&imu, 0.0f, -0.62f, 7.9f, now += 50)); /* Sample 2 */
    assert(feature_imu_update(&imu, 0.0f, -0.65f, 7.7f, now += 50));  /* Sample 3 -> FLIPS back to NORMAL */
    assert(feature_imu_get_orientation(&imu) == ORIENTATION_LANDSCAPE_NORMAL);

    printf("test_imu_orientation_and_debounce passed\n");
}

static void test_imu_shake_detection(void)
{
    imu_feature_state_t imu;
    feature_imu_init(&imu);

    uint32_t now = 1000;
    /* Normal gravity: ~1.0g -> no shake */
    assert(!feature_imu_update(&imu, 0.1f, 0.1f, 1.0f, now));
    assert(!feature_imu_consume_shake(&imu));

    /* Sudden high acceleration: 2.5g -> shake detected */
    feature_imu_update(&imu, 1.8f, 1.5f, 0.8f, now += 100);
    assert(feature_imu_consume_shake(&imu));

    /* Flag is consumed */
    assert(!feature_imu_consume_shake(&imu));

    printf("test_imu_shake_detection passed\n");
}

int main(void)
{
    test_imu_orientation_and_debounce();
    test_imu_shake_detection();
    printf("ALL FEATURE_IMU TESTS PASSED!\n");
    return 0;
}
