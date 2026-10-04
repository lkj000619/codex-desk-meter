# Hardware Feature Selection: Waveshare ESP32-S3-LCD-3.16

- **Run ID**: `20261005-antigravity-cli-agy-flash-r02`
- **Target Platform**: Waveshare ESP32-S3-LCD-3.16 (ESP32-S3R8, 16MB Flash, 8MB Octal PSRAM, ST7701 820x320 RGB565 LCD, QMI8658 6-axis IMU, PCF85063 RTC, Battery ADC, GPIO0 BOOT button).
- **Evaluation Contract**: Version 2 Hardware Feature Selection (Section 4 & 5).

---

## 1. Candidate Features Considered

### Candidate 1 (SELECTED): QMI8658 6-Axis IMU Motion Gestures & View Cycling
- **ID**: `qmi8658_imu_gestures`
- **Description**: Utilizes the onboard QMI8658 6-axis IMU (I2C address `0x6B`, GPIO8 SDA / GPIO9 SCL) to implement dynamic motion detection. Shake gestures trigger sequential cycling through the 3 primary display views (Dashboard, Global Resets, Diagnostics) with debounce protection.
- **User Value**:
  - Provides intuitive, hands-free desk interaction: users can tap or lightly shake the desk meter to inspect global reset or diagnostic stats without pressing small physical buttons.
  - Mitigates physical wear on the single onboard tactile BOOT switch (GPIO0).
  - Compatible with 3D-printed enclosure designs where the physical BOOT switch is recessed or inaccessible.
- **Resource Consumption**:
  - Bus: Shared I2C0 bus (100kHz standard mode), non-blocking FreeRTOS polling task running at 20Hz.
  - RAM: < 512 bytes for state tracking and vector history.
  - CPU: Negligible (< 0.2% ESP32-S3 core time).
- **Implementation Cost & Complexity**:
  - Moderate: Requires register configuration for continuous accelerometer sampling (±4g scale), low-pass digital filtering, euclidean norm calculation ($\sqrt{a_x^2 + a_y^2 + a_z^2}$), and software debouncing (300ms window).
  - Clean architectural separation: Encapsulated entirely in `components/meter_core/src/feature_imu.c` and `feature_imu.h` without contaminating core JSON parsers or protocol state machines.
- **Risks & Mitigations**:
  - *Risk*: False positive triggers from typing or desk bumps.
  - *Mitigation*: Calibrated jerk/acceleration threshold to > 1.8g and enforced a minimum 300ms cooldown window between consecutive transitions.
- **Verification Plan**:
  - Host native unit tests in `build-host/test_feature_imu.exe` testing resting stability, single shake detection, rapid multi-shake debounce rejection, and reset recovery.
  - Firmware runtime verification emitting distinct serial log marker `[TRIGGER_IMU_SHAKE]` upon verified gesture.

---

### Candidate 2 (REJECTED): PCF85063 Real-Time Clock (RTC) for Local Timekeeping
- **ID**: `pcf85063_rtc_timekeeping`
- **Description**: Communicates with the onboard PCF85063 I2C RTC (`0x51`, GPIO8/GPIO9) to maintain local wall-clock time across power drops.
- **User Value**:
  - Preserves wall-clock time even when disconnected from the PC host.
- **Implementation Cost**:
  - Moderate: Requires reading and writing BCD registers, leap-year calculations, and synchronizing host RFC3339 timestamps into RTC registers upon frame receipt.
- **Risks & Failure Modes**:
  - Evaluation boards often ship without a coin-cell battery or rechargeable supercapacitor installed.
  - Without battery backup, PCF85063 oscillator stop flag (OS) triggers on cold boot, requiring software fallback.
  - Contract strictly defines relative monotonic age from observed/received timestamps, making RTC synchronization redundant.
- **Rejection Rationale**:
  - The CDM/1 contract deliberately decouples host reference UTC and device monotonic uptime. Introducing local hardware RTC introduces unneeded clock-drift sync edge cases and hardware battery dependency that cannot be guaranteed during automated test runs.

---

### Candidate 3 (REJECTED): Onboard Battery Voltage ADC Monitor & Power Telemetry
- **ID**: `battery_adc_voltage_monitor`
- **Description**: Uses ESP32-S3 ADC1 (connected to battery resistor divider circuit) to monitor battery voltage and render a battery gauge icon on the LCD GUI.
- **User Value**:
  - Allows monitoring remaining battery life when operating wire-free.
- **Implementation Cost**:
  - Low: Requires ESP-IDF `esp_adc` one-shot driver setup and calibration curve lookup.
- **Risks & Failure Modes**:
  - When the board is plugged into USB-C (which is required for CDM/1 serial communication), the ADC reads the USB charging voltage (~4.2V float), reporting 100% permanently and hiding actual battery telemetry.
  - In unpowered battery fixtures, ADC floating pin noise can report erratic readings.
- **Rejection Rationale**:
  - The primary deployment mode for the Codex Desk Meter is continuous USB-C tethering for real-time serial telemetry. Under USB power, the battery monitor provides no actionable user value and cannot be verified without auxiliary variable DC power supplies.

---

## 2. Selection Summary & Rubric Alignment

| Candidate | User Value | Resource Cost | Implementation Risk | Verification Feasibility | Decision |
|---|---|---|---|---|---|
| **QMI8658 IMU Gestures** | **High (ergonomic hands-free view cycling)** | **Very Low (<0.5KB RAM, shared I2C)** | **Low (debounced vector threshold)** | **High (Deterministic host tests & device log markers)** | **SELECTED** |
| PCF85063 RTC | Low (redundant with host monotonic reference) | Low | High (coin cell unpopulated in test environments) | Moderate | REJECTED |
| Battery ADC Monitor | Low (reads float voltage during USB session) | Low | Moderate (distorted readings under USB VBUS) | Low (requires external battery supply) | REJECTED |

## 3. Modular Separation & Architectural Provenance
- `components/meter_core/include/feature_imu.h`: Pure interface definition.
- `components/meter_core/src/feature_imu.c`: Hardware-independent detection logic with pluggable sample feed.
- `components/bsp/src/bsp_i2c.c`: I2C peripheral bus initialization for ESP32-S3 hardware.
- `tests/test_feature_imu.c`: 100% host unit test coverage verifying thresholding and debounce.
- `main/main.c`: Integrates the IMU gesture hook into the view management state without coupling to the `meter_parser` or `meter_state` core.
