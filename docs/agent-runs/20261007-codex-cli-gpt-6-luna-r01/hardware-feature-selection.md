# On-board feature selection

Run: `20261007-codex-cli-gpt-6-luna-r01`  
Board: Waveshare ESP32-S3-LCD-3.16 / ESP32-S3R8

## Candidates

| Candidate | User value | Board resources | Cost | Risk | Test |
|---|---|---|---|---|---|
| Idle backlight dimming after 60 seconds | Reduces light and power while keeping the meter visible on a desk. | Existing active-low backlight on GPIO6; LEDC timer 3, channel 1, 8-bit duty. Uses the monotonic timer already used by the app. | Low: one small C policy module and one call in the main loop. No extra component or network access. | A low level could make values hard to read. The policy therefore changes from brightness 180 to 120 and never turns the display off while active. | Host C boundary checks at 59,999/60,000 ms, inactive display, and a monotonic-time reversal; then a board check of readability before and after idle. |
| QMI8658 orientation navigation | Lets a user turn the device and keep the information upright. | Shared I2C SCL=7/SDA=15, QMI8658 at 0x6B, CPU for sampling and orientation filtering. | Medium/high: sensor startup, filtering, debounce, coordinate remap, and return behavior. | Motion/noise can rotate or blank a display unexpectedly; it could obscure stale/error information. | Verify each supported orientation, debounce and return thresholds, USB traffic during rotation, and recovery after turning the device back. |
| PCF85063 time continuity | Could preserve a wall-clock reference across a board restart for age displays. | Shared I2C SCL=7/SDA=15, PCF85063 at 0x51, and its backup supply if fitted. | Medium: RTC validity checks, clock setting, and a defined fallback when backup power or the RTC is unavailable. | Backup power is not guaranteed by the supplied board facts. An invalid clock could make old values look current. | Verify clock validity and backup retention; remove or invalidate the RTC input and confirm the UI reports unknown time rather than substituting a value. |

## Selection

Selected: **idle backlight dimming**. It is isolated in `components/idle_dim_policy` and receives only monotonic time, last interaction time, and display-active state from the app. It does not change the parser, receiver, provider data, or page navigation. The host C test covers its boundaries. The board's visible PWM levels have not been measured in this run.

QMI8658 orientation is rejected because reliable rotation and return behavior would add more moving parts to the first hardware path, and the supplied feedback already identifies a screen orientation problem that must first be resolved in the fixed landscape layout. PCF85063 time continuity is rejected because backup power and RTC validity are unconfirmed; the contract requires unknown time rather than a guessed age when the reference is unavailable.

## Manufacturer source checks

The pin mapping, panel command sequence, button polarity, and backlight polarity were read from the declared `09_FactoryProgram` source root and compared with the hashes in `docs/hardware/vendor-source-index.json`. The checked hashes were `main/main.cpp` `f4d77ecb33568b0ad78b0b5eae86ad6c404cc5b500d54687928b8e8b0d746b32`, `main/user_config.h` `97a26c977fe5af98eab143bb7d1851ee6541dbd565829d62133fc80dcbd5e1b3`, `components/button_bsp/button_bsp.c` `374310396dddeda6cfd979e060737f73dda03ed4e7c31352005e73f1eb8cd8f3`, and `components/lcd_bl_pwm_bsp/lcd_bl_pwm_bsp.c` `1f6e4214730365fea9c56da92e820ee011287fd968485c646fbac246f5aca6`. The ST7701 RGB driver source used by the project matched `486572aabd1c05be15a9aa1bdcceeacfbfa55329aec65778cb530ef19e785a0f`.
