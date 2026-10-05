# Hardware feature selection

Run: `20261006-codex-cli-gpt-6-sol-r01`. The core USB receiver, BOOT navigation, and LCD UI do not depend on this feature.

| Candidate | User value | Resources and implementation cost | Risk | Verification |
|---|---|---|---|---|
| Idle backlight dimming (selected) | Reduces glare and power after one minute without accepted data while leaving values visible. | GPIO6 PWM, one timestamp comparison and a separate `feature.c` module; no added hardware. | PWM polarity or an unreadably low idle level. | Host state test at 59/60 seconds and recovery; operator observes brightness and readability on the board. |
| IMU orientation gesture | Automatically reorients the display. | QMI8658 on GPIO7/15 I2C, driver, filtering, framebuffer rotation; moderate code and CPU cost. | Accidental rotation and additional display instability. | Physical tilt and return with debounce, plus portrait/landscape readability. Rejected because the display path needs to stay simple and stable. |
| RTC backed reset age | Keeps reset age across a board restart. | PCF85063 on GPIO7/15 I2C, battery/backup power and clock setting; moderate integration cost. | Unsynchronised or unpowered RTC could present false age. | Set RTC, remove USB power, restore, compare with known UTC and test no backup battery. Rejected because backup power is unconfirmed and the contract already supports unknown age. |

The selected dimming feature uses the active low backlight on GPIO6. `feature_idle_dimming` is isolated from the receiver and GUI; it never edits quota data, sequence state or source age. Physical brightness and power savings are unmeasured until operator observation.
