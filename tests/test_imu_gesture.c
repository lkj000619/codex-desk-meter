#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <math.h>
#include "imu_gesture.h"

static void test_static_standstill(void) {
    printf("[IMU Test] Running static standstill test...\n");
    imu_gesture_detector_t det;
    imu_gesture_detector_init(&det);

    /* 100 samples of resting 1.0g on desk */
    for (uint32_t t = 0; t < 1000; t += 10) {
        imu_gesture_event_t evt = imu_gesture_process_sample(&det, 0.0f, 0.0f, 1.0f, t);
        assert(evt == IMU_GESTURE_NONE);
    }
    printf("[IMU Test] Static standstill: PASS\n");
}

static void test_typing_noise_rejection(void) {
    printf("[IMU Test] Running typing vibration noise rejection test...\n");
    imu_gesture_detector_t det;
    imu_gesture_detector_init(&det);

    /* Typing generates small micro-vibrations <= 0.25g */
    for (uint32_t t = 0; t < 3000; t += 10) {
        float noise = ((float)(t % 5) - 2.0f) * 0.08f;
        imu_gesture_event_t evt = imu_gesture_process_sample(&det, noise, noise, 1.0f + noise, t);
        assert(evt == IMU_GESTURE_NONE);
    }
    printf("[IMU Test] Typing noise rejection: PASS\n");
}

static void test_single_tap_timeout(void) {
    printf("[IMU Test] Running single tap timeout test...\n");
    imu_gesture_detector_t det;
    imu_gesture_detector_init(&det);

    /* Resting at 1g */
    for (uint32_t t = 0; t < 500; t += 10) {
        imu_gesture_process_sample(&det, 0.0f, 0.0f, 1.0f, t);
    }

    /* Single tap peak of 1.8g at t=500 */
    imu_gesture_event_t evt = imu_gesture_process_sample(&det, 0.0f, 0.0f, 2.2f, 500);
    assert(evt == IMU_GESTURE_NONE); /* First tap should NOT trigger double-tap */

    /* Wait 1000ms (exceeds 550ms double-tap window) */
    for (uint32_t t = 510; t <= 1500; t += 10) {
        evt = imu_gesture_process_sample(&det, 0.0f, 0.0f, 1.0f, t);
        assert(evt == IMU_GESTURE_NONE);
    }
    assert(det.tap_count == 0);
    printf("[IMU Test] Single tap timeout: PASS\n");
}

static void test_double_tap_detection(void) {
    printf("[IMU Test] Running double-tap detection test...\n");
    imu_gesture_detector_t det;
    imu_gesture_detector_init(&det);

    /* Resting */
    for (uint32_t t = 0; t < 500; t += 10) {
        imu_gesture_process_sample(&det, 0.0f, 0.0f, 1.0f, t);
    }

    /* Tap 1 at t=500 */
    imu_gesture_event_t evt1 = imu_gesture_process_sample(&det, 0.0f, 0.0f, 2.2f, 500);
    assert(evt1 == IMU_GESTURE_NONE);

    /* Settle between taps for 200ms */
    for (uint32_t t = 510; t < 700; t += 10) {
        imu_gesture_event_t ev = imu_gesture_process_sample(&det, 0.0f, 0.0f, 1.0f, t);
        assert(ev == IMU_GESTURE_NONE);
    }

    /* Tap 2 at t=700 (200ms delta, well within 80..550ms window) */
    imu_gesture_event_t evt2 = imu_gesture_process_sample(&det, 0.0f, 0.0f, 2.2f, 700);
    assert(evt2 == IMU_GESTURE_DOUBLE_TAP);
    printf("[IMU Test] Double-tap detection: PASS\n");
}

static void test_shake_detection(void) {
    printf("[IMU Test] Running shake gesture detection test...\n");
    imu_gesture_detector_t det;
    imu_gesture_detector_init(&det);

    /* Vigorous shaking: 3 oscillating peaks of 2.5g within 300ms */
    imu_gesture_process_sample(&det, 0.0f, 0.0f, 1.0f, 100);
    imu_gesture_process_sample(&det, 2.0f, 0.0f, 2.0f, 150); /* Peak 1 */
    imu_gesture_process_sample(&det, -1.8f, 0.0f, 0.2f, 220); /* Peak 2 */
    imu_gesture_event_t evt = imu_gesture_process_sample(&det, 2.2f, 0.0f, 1.8f, 290); /* Peak 3 */

    assert(evt == IMU_GESTURE_SHAKE);
    printf("[IMU Test] Shake detection: PASS\n");
}

int main(void) {
    printf("===========================================\n");
    printf("  Autonomous IMU Gesture Unit Tests Starting\n");
    printf("===========================================\n");

    test_static_standstill();
    test_typing_noise_rejection();
    test_single_tap_timeout();
    test_double_tap_detection();
    test_shake_detection();

    printf("===========================================\n");
    printf("  ALL IMU GESTURE TESTS PASSED SUCCESSFULLY!\n");
    printf("===========================================\n");
    return 0;
}
