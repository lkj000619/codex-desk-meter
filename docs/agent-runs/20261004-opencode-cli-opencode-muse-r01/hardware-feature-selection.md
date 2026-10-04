# Hardware Feature Selection — 20261004-opencode-cli-opencode-muse-r01

Board: Waveshare ESP32-S3-LCD-3.16 (ESP32-S3R8, 16 MB flash, 8 MB octal PSRAM,
320x820 ST7701 portrait panel driven as logical 820x320 landscape).
Board facts: `docs/hardware/version-2-capabilities.md`. Vendor source ground:
`docs/hardware/vendor-source-index.json` (09_FactoryProgram `main/user_config.h`
pins, `main/main.cpp` timings, `lcd_bl_pwm_bsp` active-low polarity,
`button_bsp.c` GPIO0 input). No extra parts, no credentials, core path
(PC fixture -> USB `cdm/1` -> receiver/cache/stale -> LCD) never depends on
the selected feature.

## Candidate F-A — Link/idle-aware backlight auto-dim (SELECTED)

- User value: desk meter stays readable but does not glare at night; when the
  USB link drops, the panel visibly dims instead of freezing on a bright
  stale screen, so a dead link is noticeable from across the room.
- Resources: backlight GPIO6 LEDC PWM already owned by the core BSP
  (8-bit, active-low: duty = 255 - brightness). No new pins, no I2C, no RAM
  beyond two small structs.
- Cost: ~40 lines of pure logic (`feature_auto_dim.c`) + one call in the GUI
  refresh path. No new tasks, no new drivers.
- Risk: low. Failure mode is wrong brightness only; the core meter path does
  not branch on it. PWM polarity follows the vendor BSP fact (active-low).
- Test: `tests/host/test_feature_autodim.c` (host, compiled from the
  production file): fresh+linked -> normal (duty 55); idle >= 30 s -> dimmed
  (duty 195); link loss -> dimmed immediately; activity restores normal.
  Operator visual check: unplug USB, panel dims within the 1 Hz refresh.
- Separation: `firmware/components/feature_auto_dim/` (own component,
  `REQUIRES` nothing from the meter path). GUI calls `autodim_duty()` only.

## Candidate F-B — IMU tilt page-turn (REJECTED)

- User value: tilt the board left/right to flip dashboard/global/status
  without touching BOOT; useful when the meter sits behind a monitor.
- Resources: QMI8658 at I2C 0x6B (SCL=7, SDA=15), shared I2C bus bring-up,
  per-poll accel reads, tilt state machine with debounce and a return-to-idle
  condition so the screen does not spin on a wobbly desk.
- Cost: new I2C BSP + sensor driver port + gesture tuning (~300 lines),
  plus power/UX validation on real hardware.
- Risk: medium-high. I2C brings a new failure surface into the boot path
  (a hung bus must never block the core receiver); accidental page flips
  from desk vibration directly harm the core reading task. Needs physical
  tuning time this run cannot afford.
- Test (planned, not built): host tilt-classifier unit test + operator
  tilt-left/right/idle procedure with debounce log.
- Rejection reason: highest integration risk of the three and the only one
  that can disturb the core display task; deferred until the core USB->LCD
  path is observed passing on hardware.

## Candidate F-C — RTC-backed last-good clock (REJECTED)

- User value: show wall-clock "last-good HH:MM:SS" and true source-age
  (observed_at vs now) on the status screen instead of receive-age only.
- Resources: PCF85063 at I2C 0x51, RTC init + set/valid flags, backup-power
  detection (operator must confirm whether a backup cell is fitted).
- Cost: I2C BSP shared with F-B plus time-base arbitration (RTC vs monotonic
  anchor vs unknown) and a "clock invalid" UI state (~200 lines).
- Risk: medium. Without a confirmed backup cell the clock resets every boot
  and the display would show confidently wrong times — worse than the honest
  `unknown` the contract requires when the time base is undetermined. Also
  adds the same I2C boot-path surface as F-B.
- Test (planned, not built): RTC present/absent host matrix + operator
  power-cycle retention check.
- Rejection reason: depends on an unconfirmed hardware fact (backup power);
  a wrong clock violates the contract's unknown-until-determined rule, while
  the selected dimmer needs no time base at all.

## Decision

Selected: **F-A auto-dim**. It is the only candidate that (a) uses an already
proven actuator (GPIO6 backlight), (b) cannot corrupt core meter state, and
(c) is fully verifiable on the host plus one glance at the panel. F-B and F-C
stay documented above with rejection reasons; neither is a vendor-demo repeat
(demo shows LVGL widgets/music; none of the three repeats it).
