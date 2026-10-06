# On-board feature selection

The display and BOOT navigation required by the product contract stay in the core. These are three optional board features evaluated for F9.

| Candidate | User value | Board resources | Implementation cost | Main risk | Verification |
|---|---|---|---|---|---|
| Idle backlight dimming (selected) | Reduce glare and backlight power while the meter is unattended. | Existing GPIO6 active-low LEDC backlight; no additional peripheral or hardware. | Low. An isolated policy module selects 180 brightness before 60 seconds of inactivity and 120 afterward; BOOT interaction restores 180. | A low idle value could make the required UI appear black. The floor is 120/255, and hardware visibility still needs optical confirmation. | Host C boundary tests cover 59,999/60,000 ms and inactive/out-of-order time. On the board, observe the display before and after 60 seconds, then press BOOT and confirm brightness returns without losing the current page. |
| IMU tilt navigation | Rotate or change pages without pressing BOOT. | QMI8658 on I2C GPIO7/15, address 0x6B; sampling and filtering use CPU and the existing I2C bus. | Medium. Add sensor startup, orientation thresholds, debounce, and recovery if I2C initialization fails. | Movement can cause accidental page changes and compete with the explicit BOOT behavior. | On hardware, hold known orientations, apply controlled tilts, and verify threshold/debounce behavior and recovery to BOOT navigation. This was not implemented or measured. |
| RTC time context | Show a local clock alongside source and observation times. | PCF85063 on I2C GPIO7/15, address 0x51; requires RTC initialization and a trusted clock source. | Medium. Add RTC access, time validity handling, and a fallback for unset or lost time. | Backup power is not confirmed; an unset or stale RTC could make source age look current. | On hardware, compare a set RTC with a trusted reference, test unset/lost-backup states, and ensure the UI reports unknown instead of inventing time. This was not implemented or measured. |

## Choice

Idle dimming is selected because it uses an existing output and stays outside the parser, receiver state, and screen data model. It has the smallest implementation and recovery cost. The initial idle setting of 22/255 could be mistaken for a failed LCD, so the implementation now keeps an idle floor of 120/255. BOOT activity restores the 180/255 level. Host C tests verify the policy boundary; the optical level, continuous display, and actual power reduction remain for the operator's hardware check.

Tilt navigation was rejected because the contract already defines BOOT as the reliable way to reach usage, global-reset, and diagnostics pages. It would add sensor failure and false-trigger paths to essential navigation.

RTC time context was rejected because frames already carry source observation timestamps, and the supplied board facts do not confirm RTC backup power or a valid RTC clock. Showing unverified wall time could misrepresent source freshness.

## Implementation boundary

The selected policy is implemented in `components/idle_dim_policy/idle_dim_policy.c`, exposed by its component header, and called by `main/app_main.c`. The BSP applies the returned level through the existing GPIO6 LEDC control in `main/board_lcd.c`. No IMU, RTC, network, or account data is needed for this feature.
