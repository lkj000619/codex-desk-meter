# Board feature selection — run 20261006-codex-cli-gpt-6-luna-r01

Board facts below come from [version-2-capabilities.md](../../hardware/version-2-capabilities.md) and the hash-checked files listed by [vendor-source-index.json](../../hardware/vendor-source-index.json). The base product stays a landscape 820×320 meter. The optional feature is independent of the wire parser and receiver.

## Candidates

| Candidate | User value | Board resources and implementation cost | Risk | Verification |
|---|---|---|---|---|
| Idle backlight dimming (**selected**) | Reduces display power and glare when the meter is unattended; a BOOT press returns it to full brightness. | Uses the existing active-low PWM backlight on GPIO6 and one LEDC channel. No extra part, framebuffer, network, or sensor task. The policy is a small standalone `idle_dim_policy` component. | PWM polarity or the 22/255 idle level may be uncomfortable or too dim; brightness and power have not been checked on the physical panel. | Host C test at 59,999/60,000 ms, no-display and monotonic-time reversal; on the board check the 60-second transition, readability, flicker, and BOOT wake. |
| IMU orientation indicator / page rotation | Could orient a compact status view to how the device is placed. | QMI8658 at I²C address 0x6B on SCL=7/SDA=15. Requires I²C setup, sensor reads, orientation thresholds, and a debounce/filter task. | Rotation can make the required wide dashboard harder to read and can switch pages while the meter is stationary or vibrating. Sensor availability and calibration need board checks. | Test four orientations, stationary drift, movement, repeated transitions, and return to the fixed landscape dashboard. |
| RTC-backed local time confidence | Could show local time alongside source timestamps when host time is unavailable. | PCF85063 at I²C address 0x51 on the shared I²C bus. Requires RTC initialization, time-setting policy, validity reporting, and checking backup power. | The board facts do not guarantee that a backup cell is fitted or that the RTC is set. A wrong clock could make source age or reset history look trustworthy. Firmware currently uses monotonic receive age and preserves source timestamps. | Verify cold-start time validity with and without backup power, drift, unset-state display, and that RTC values never replace source timestamps. |

## Selection

Idle backlight dimming is selected because it has direct value on a continuously visible meter, uses a documented existing output, and stays isolated from C1–C8 behavior. It is implemented in `components/idle_dim_policy`; `main/app_main.c` applies its output through the board backlight API. At 60 seconds without BOOT interaction the policy requests brightness 22, otherwise 180; the board API applies the manufacturer-documented active-low inversion. Host tests cover the threshold and invalid monotonic ordering.

IMU rotation is rejected because the display contract is a fixed landscape dashboard and the sensor would introduce a new interaction mode with more state and filtering. RTC time is rejected because backup power is not guaranteed and the product must preserve source times; adding a seemingly authoritative local clock risks hiding unknown time. Neither rejected idea is implemented.

The selected behavior has compile and host-policy evidence only. Physical brightness, power, and BOOT wake behavior remain unverified for this run.
