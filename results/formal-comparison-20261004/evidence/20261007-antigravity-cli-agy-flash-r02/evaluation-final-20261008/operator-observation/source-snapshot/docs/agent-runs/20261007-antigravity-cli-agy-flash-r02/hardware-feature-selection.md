# Hardware Feature Selection: Waveshare ESP32-S3-LCD-3.16

- **Run ID**: `20261007-antigravity-cli-agy-flash-r02`
- **MCU / Board**: Waveshare ESP32-S3-LCD-3.16 (ESP32-S3R8, 16MB Flash, 8MB Octal PSRAM)
- **Display**: ST7701 RGB565 (820x320 landscape orientation)
- **Scope**: Section 4 & F9 Autonomous Hardware Feature Selection Requirement

---

## 1. Candidate Features (Exactly 3 Candidates)

### Candidate 1 (SELECTED): QMI8658 6-Axis IMU Orientation Auto-Flip & Shake Navigation
- **Hardware Resources**: Onboard QMI8658 6-axis IMU connected via I2C (SCL=GPIO7, SDA=GPIO15, I2C address 0x6B).
- **User Value**:
  - The 3.16-inch ultra-wide bar display (820x320) is designed for flexible desktop placement. Depending on cable routing (USB-C port on left or right), users frequently place the device in normal (0°) or inverted (180°) landscape orientations.
  - Automatic 180° rotation allows the screen and text to remain right-side up regardless of physical orientation.
  - A gentle shake gesture provides hands-free screen navigation without touching the shared BOOT button.
- **Resource & Performance Cost**:
  - Negligible CPU footprint: I2C polling occurs every 30ms in a low-priority background task.
  - Minimal RAM footprint (<128 bytes state).
  - Tiled 32x32 cache-blocked pixel rotation takes ~3ms and maintains 20 FPS refresh without tearing.
- **Risk Assessment**:
  - Sensor noise, false triggers, and sensor failure.
  - Mitigated by 300ms debounce threshold, low-pass gravity filtering, hysteresis thresholds (0.5g for flip, 1.8g for shake), and graceful fallback to normal landscape if the IMU is disconnected or fails initialization.
- **Verification Method**:
  - Host C unit test: `tests/test_feature_imu.c` verifies gravity vector classification, hysteresis transitions, and shake debounce.
  - Firmware runtime: logs `[TRIGGER_IMU_ROTATE]` and `[TRIGGER_IMU_SHAKE]` on orientation changes.

---

### Candidate 2 (REJECTED): PCF85063 Real-Time Clock (RTC) Battery Backup Timekeeping
- **Hardware Resources**: Onboard PCF85063 RTC connected via I2C (address 0x51).
- **User Value**:
  - Maintains wall-clock time across device restarts when the host PC is temporarily disconnected.
- **Resource & Performance Cost**:
  - Low CPU and RAM overhead.
- **Risk Assessment & Reason for Rejection**:
  - **Rejection Rationale**: Per `docs/hardware/version-2-capabilities.md`, external coin cell battery backup is not mounted on the standard evaluation fixture. Without battery power, the PCF85063 loses time upon USB power cycling, requiring external time synchronization.
  - The protocol already transmits authoritative UTC timestamps (`sent_at`, `observed_at`, `captured_at`) in each `cdm/1` frame, making the RTC redundant and introducing failure risk due to unpowered RTC state.

---

### Candidate 3 (REJECTED): TF / MicroSD Card Offline Snapshot Logging
- **Hardware Resources**: Onboard MicroSD card slot connected via SPI/SDIO.
- **User Value**:
  - Persists historical snapshot logs locally for offline inspection.
- **Resource & Performance Cost**:
  - Significant memory footprint: FATFS driver and buffer allocation consume substantial SRAM/PSRAM.
- **Risk Assessment & Reason for Rejection**:
  - **Rejection Rationale**: Per `docs/hardware/version-2-capabilities.md`, no MicroSD card is installed in the test fixture slot. Initializing or relying on an unmounted SD card risks filesystem mount timeouts, task blocking, and spurious device errors.
  - The core product requirement specifies low-latency USB streaming without external storage dependencies.

---

## 2. Architecture & Modular Isolation

The selected QMI8658 IMU feature is strictly isolated from core meter functionality:
1. **Separation of Concerns**:
   - `components/bsp/src/bsp_imu.c` & `bsp_imu.h`: Low-level I2C register configuration and sensor polling.
   - `components/meter_core/src/feature_imu.c` & `feature_imu.h`: Pure algorithmic state machine for orientation detection, gravity filtering, and shake detection.
   - `components/meter_core/src/meter_state.c`: Receives clean orientation events (`ORIENTATION_LANDSCAPE_NORMAL` or `ORIENTATION_LANDSCAPE_INVERTED`).
2. **Graceful Degradation**:
   - If the IMU fails to initialize or communication drops, the firmware logs a warning and defaults to `ORIENTATION_LANDSCAPE_NORMAL`. The meter receiver, parser, and display continue normal operation without interruption.
3. **Host Testability**:
   - `tests/test_feature_imu.c` is fully compiled and tested natively in the host test suite (`ctest`), verifying correct behavior without requiring physical hardware.
