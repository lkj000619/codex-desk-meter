# Hardware feature selection — Codex reference product

This selection is part of the reference product build, not a benchmark run.

| Candidate | User value | Resource and cost | Risk | Verification |
|---|---|---|---|---|
| PCF85063 time holdover | Keep reset elapsed time and stale timing meaningful after the PC is disconnected or the board reboots. | Existing RTC, I2C pins 7/15; moderate implementation cost for BCD/calendar validation and host-time synchronization. | RTC backup cell may be absent or depleted; RTC drift and unset date must not look valid. | Host C tests cover UTC/BCD conversion and date validation; operator checks retained time and battery-backed behavior after upload. |
| QMI8658 viewing-orientation control | Rotate the dashboard after the display is physically repositioned. | Existing IMU on I2C; moderate cost plus layout/orientation testing. | Motion noise can cause unwanted rotations and complicate LCD geometry. | Injected orientation vectors plus physical tilt and debounce check. |
| Battery voltage status | Warn that the board is running from a low battery. | Existing battery ADC input; moderate cost for calibration and charge-state wording. | ADC calibration and voltage thresholds can misreport charge or encourage over-trust. | Calibrated voltage sweep and operator comparison to a meter. |

**Selected and implemented: PCF85063 time holdover.** A plausible RTC clock is
restored at startup. A valid host frame synchronizes system time and writes the
RTC. If the RTC cannot be read or written, product data reception still works;
the display reports that holdover is unavailable. RTC use is isolated in
`main/cdm_rtc.c` and does not replace the provider-supplied observation times.

The QMI8658 and battery ADC candidates were not implemented: both require
additional sensor calibration and board-side evidence; RTC holdover directly
improves elapsed-time and stale indications without changing the required
screens. No external hardware was added. Host evidence does not establish RTC
battery retention or physical sensor behavior.
