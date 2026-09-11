/* Host C unit test for production IMU detector logic.
 * Directly includes / links components/imu_gesture/src/imu_detector.c.
 * Verifies standstill gravity rejection, noise filtering, single tap timeout,
 * double tap detection, and vigorous shake detection without hardware.
 */
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "../components/imu_gesture/include/imu_detector.h"

int main(void) {
    printf("=================================================================\n");
    printf("  Running Production C IMU Detector Host Unit Tests\n");
    printf("=================================================================\n");

    imu_gesture_detector_t det;

    /* Test 1: Standstill Gravity Rejection */
    imu_gesture_detector_init(&det);
    for (uint32_t t = 0; t < 1000; t += 10) {
        imu_gesture_event_t evt = imu_gesture_process_sample(&det, 0.0f, 0.0f, 1.0f, t);
        assert(evt == IMU_GESTURE_NONE);
    }
    printf("[PASS] Test 1: Static standstill (1.0g gravity rejection)\n");

    /* Test 2: Typing Noise Rejection */
    imu_gesture_detector_init(&det);
    for (uint32_t t = 0; t < 3000; t += 10) {
        float noise = ((float)(t % 5) - 2.0f) * 0.08f;
        imu_gesture_event_t evt = imu_gesture_process_sample(&det, noise, noise, 1.0f + noise, t);
        assert(evt == IMU_GESTURE_NONE);
    }
    printf("[PASS] Test 2: Desk typing vibration noise rejection\n");

    /* Test 3: Single Tap Timeout */
    imu_gesture_detector_init(&det);
    for (uint32_t t = 0; t < 500; t += 10) {
        imu_gesture_process_sample(&det, 0.0f, 0.0f, 1.0f, t);
    }
    imu_gesture_event_t evt1 = imu_gesture_process_sample(&det, 0.0f, 0.0f, 2.2f, 500);
    assert(evt1 == IMU_GESTURE_NONE);
    for (uint32_t t = 510; t < 1500; t += 10) {
        imu_gesture_event_t evt = imu_gesture_process_sample(&det, 0.0f, 0.0f, 1.0f, t);
        assert(evt == IMU_GESTURE_NONE);
    }
    assert(det.tap_count == 0);
    printf("[PASS] Test 3: Single tap timeout (no phantom double tap)\n");

    /* Test 4: Double Tap Detection */
    imu_gesture_detector_init(&det);
    for (uint32_t t = 0; t < 500; t += 10) {
        imu_gesture_process_sample(&det, 0.0f, 0.0f, 1.0f, t);
    }
    imu_gesture_process_sample(&det, 0.0f, 0.0f, 2.2f, 500);
    for (uint32_t t = 510; t < 700; t += 10) {
        imu_gesture_process_sample(&det, 0.0f, 0.0f, 1.0f, t);
    }
    imu_gesture_event_t evt2 = imu_gesture_process_sample(&det, 0.0f, 0.0f, 2.2f, 700);
    assert(evt2 == IMU_GESTURE_DOUBLE_TAP);
    printf("[PASS] Test 4: Double-tap detection (screen cycle trigger)\n");

    /* Test 5: Shake Detection */
    imu_gesture_detector_init(&det);
    imu_gesture_process_sample(&det, 0.0f, 0.0f, 1.0f, 100);
    imu_gesture_process_sample(&det, 2.0f, 0.0f, 2.0f, 150);
    imu_gesture_process_sample(&det, -1.8f, 0.0f, 0.2f, 220);
    imu_gesture_event_t evt_shake = imu_gesture_process_sample(&det, 2.2f, 0.0f, 1.8f, 290);
    assert(evt_shake == IMU_GESTURE_SHAKE);
    printf("[PASS] Test 5: Vigorous shake detection (manual refresh trigger)\n");

    printf("=================================================================\n");
    printf("  ALL 5 PRODUCTION C IMU DETECTOR TESTS PASSED (100%%)\n");
    printf("=================================================================\n");
    return 0;
}
