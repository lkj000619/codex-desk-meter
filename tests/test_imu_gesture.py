"""Algorithm Simulation Reference Test for IMU Gesture Recognition.
NOTE: This script is a Python-based algorithm simulation reference test.
It does NOT link or execute the production C firmware (components/imu_gesture/src/imu_gesture.c).
Actual C firmware execution on target hardware requires physical testing (currently not_run).
1. Static standstill gravity (1g z-axis) -> no false positive.
2. Typing micro-vibration noise (amplitude <= 0.25g) -> filtered out.
3. Single tap timeout -> no false double-tap.
4. Double-tap detection (two taps spaced 80..550ms) -> IMU_GESTURE_DOUBLE_TAP.
5. Vigorous shake detection (>= 3 peaks within 600ms) -> IMU_GESTURE_SHAKE.
"""
import math

class ImuGestureDetector:
    def __init__(self):
        self.last_tap_time_ms = 0
        self.tap_count = 0
        self.prev_filtered_mag = 0.0
        self.prev_raw_mag = 1.0  # 1g static gravity
        self.shake_count = 0
        self.last_shake_time_ms = 0

    def process_sample(self, ax, ay, az, now_ms):
        mag = math.sqrt(ax * ax + ay * ay + az * az)
        hp = 0.85 * (self.prev_filtered_mag + mag - self.prev_raw_mag)
        self.prev_filtered_mag = hp
        self.prev_raw_mag = mag
        abs_hp = abs(hp)

        # Shake detection
        if abs_hp >= 0.45:
            if now_ms - self.last_shake_time_ms < 600:
                self.shake_count += 1
                if self.shake_count >= 3:
                    self.shake_count = 0
                    self.tap_count = 0
                    self.last_shake_time_ms = now_ms
                    return "SHAKE"
            else:
                self.shake_count = 1
            self.last_shake_time_ms = now_ms

        # Tap detection
        if abs_hp >= 0.50:
            if self.tap_count > 0:
                dt = now_ms - self.last_tap_time_ms
                if 80 <= dt <= 550:
                    self.tap_count = 0
                    self.last_tap_time_ms = 0
                    return "DOUBLE_TAP"
                elif dt > 550:
                    self.tap_count = 1
                    self.last_tap_time_ms = now_ms
            else:
                self.tap_count = 1
                self.last_tap_time_ms = now_ms
        else:
            if self.tap_count > 0 and (now_ms - self.last_tap_time_ms > 550):
                self.tap_count = 0

        return "NONE"

def test_all():
    print("=================================================================")
    print("  Running IMU Gesture Algorithm Simulation (Python Reference)")
    print("  Notice: Production C firmware execution is not tested here")
    print("=================================================================")

    # Test 1: Static Standstill
    det = ImuGestureDetector()
    for t in range(0, 1000, 10):
        evt = det.process_sample(0.0, 0.0, 1.0, t)
        assert evt == "NONE", f"False trigger in standstill at t={t}"
    print("[PASS] Test 1: Static standstill (1.0g gravity rejection)")

    # Test 2: Typing Noise Rejection
    det = ImuGestureDetector()
    for t in range(0, 3000, 10):
        noise = ((t % 5) - 2.0) * 0.08  # -0.16g .. +0.16g
        evt = det.process_sample(noise, noise, 1.0 + noise, t)
        assert evt == "NONE", f"False trigger on typing noise at t={t}"
    print("[PASS] Test 2: Desk typing vibration noise rejection")

    # Test 3: Single Tap Timeout
    det = ImuGestureDetector()
    for t in range(0, 500, 10):
        det.process_sample(0.0, 0.0, 1.0, t)
    evt = det.process_sample(0.0, 0.0, 2.2, 500)
    assert evt == "NONE", "First tap must not trigger double-tap"
    for t in range(510, 1500, 10):
        evt = det.process_sample(0.0, 0.0, 1.0, t)
        assert evt == "NONE"
    assert det.tap_count == 0, "Tap count must expire after timeout"
    print("[PASS] Test 3: Single tap timeout (no phantom double tap)")

    # Test 4: Double Tap Detection
    det = ImuGestureDetector()
    for t in range(0, 500, 10):
        det.process_sample(0.0, 0.0, 1.0, t)
    # Tap 1 at t=500
    evt1 = det.process_sample(0.0, 0.0, 2.2, 500)
    assert evt1 == "NONE"
    # Settle
    for t in range(510, 700, 10):
        det.process_sample(0.0, 0.0, 1.0, t)
    # Tap 2 at t=700 (200ms interval)
    evt2 = det.process_sample(0.0, 0.0, 2.2, 700)
    assert evt2 == "DOUBLE_TAP", "Must detect double-tap at 200ms delta"
    print("[PASS] Test 4: Double-tap detection (screen cycle trigger)")

    # Test 5: Shake Detection
    det = ImuGestureDetector()
    det.process_sample(0.0, 0.0, 1.0, 100)
    det.process_sample(2.0, 0.0, 2.0, 150)
    det.process_sample(-1.8, 0.0, 0.2, 220)
    evt = det.process_sample(2.2, 0.0, 1.8, 290)
    assert evt == "SHAKE", "Must detect shake gesture within 600ms"
    print("[PASS] Test 5: Vigorous shake detection (manual refresh trigger)")

    print("=================================================================")
    print("  ALL 5 IMU GESTURE SIMULATION TESTS PASSED (Algorithm Reference)")
    print("  Hardware C firmware verification status: not_run")
    print("=================================================================")

if __name__ == "__main__":
    test_all()
