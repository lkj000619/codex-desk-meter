# Independent LCD flicker correction review

Run `run_c968c43361da` · Task `task_4386f8dbef93` · Dispatch `ctx_1ab7525e89ae` · 2026-10-10.

## Verdict

**Host review: PASS for the accepted presentation correction and relevant regressions. Whole-product approval: not granted; `product_pass=false`.** The correction prevents production rendering from mutating the currently selected scan source, advances to the other render buffer only after two completed bounce-frame callbacks, and fails dark on a draw or bounded-wait error. The corrected firmware has not been flashed or physically observed in this review, so physical flicker removal remains `not_run`.

The pre-correction symptom is supported by fresh-cohort observations: after data arrived, populated Usage/Status views repeatedly showed white partial clears while the display reported CRC VALID and real quota values. This is consistent with a presentation race, not a C receiver/CRC failure. The separate initial-video black interval at about 13 s was a manually triggered RST. Long scientific token values also appeared exponent-clipped; that is a distinct renderer formatting/readability finding and is not fixed or covered by this presentation correction.

## Frozen build and source

- Accepted source commit recorded by coordinator: `9bbe333`.
- Current `firmware/main/bsp.c` SHA-256: `8A820F95AA58DB42D3C559901918419B8A11712E1D9F4A01F10CB085A890CEEE`.
- Accepted application binary SHA-256: `953782E5486ADBE9743E5B753E716892CFDFBEEF25D23B1702DC1D6050078F1F`.
- Independent comparison: **15/15** current source/config files equal `C:/Espressif/tmp/cdm-sol-task_b1214421a314`; **4/4** accepted binaries/config equal both staging outputs and `firmware/.host-tools/lcd-flicker-build/` copies.
- `docs/agent-runs/orca-sol/lcd-flicker-build-output.txt` SHA-256 is `5967CC3A615EF58DC6A6A86C0C914882D50FBD4AF5E1208A2A18CAE910A771A0`; verified `Project build complete` and 71% app partition free. The existing ESP-IDF v5.3.2 build was accepted and rechecked; no rebuild was justified.
- Verified artifact hashes: app `953782E5486ADBE9743E5B753E716892CFDFBEEF25D23B1702DC1D6050078F1F`, bootloader `F4C5160D0777EBDA11EDAC881853B211300323E5CF8F96EEEDA5314D731D02AB`, partition table `7F00B6C042A89B15B0CAC534F82ED988CAF29278FF5700B0C511EB1B5BB7C820`, sdkconfig `46788F1C30A51868DA7C66C41DEF9045514FAAF393BC68EC0D6F05DF4DACA452`.

## Presentation path and regression evidence

The production `bsp.c` sets the active-low GPIO6 backlight dark before configuring it as output, configures a two-frame 320×820 RGB panel with a 3200-pixel bounce buffer in PSRAM, and fills both buffers before lighting the display. It passes GPIO0 as ST7701 SPI CS, uses the multiplex constructor, drives CS high, then changes GPIO0 to pulled-up input for BOOT. The current implementation renders into the non-scan buffer, submits its full frame with `esp_lcd_panel_draw_bitmap`, drains any prior notification, and waits at most 200 ms for each of two frame-boundary notifications before swapping render ownership. A missing boundary/draw/callback-registration error keeps future pixel writes disabled and turns the backlight off; `main.c` propagates a present error through `ESP_ERROR_CHECK`, so the task aborts after fail-dark rather than retrying.

Installed ESP-IDF source was inspected at `C:/Espressif/v5.3.2/esp-idf/components/esp_lcd/rgb/esp_lcd_panel_rgb.c`:

- `rgb_panel_draw_bitmap`, lines 722–737, selects `cur_fb_index` when the submitted pointer is one of the driver's own framebuffers.
- `lcd_rgb_panel_fill_bounce_buffer`, lines 932–951, copies a full bounce chunk from `fbs[bb_fb_index]`; only when the frame wraps does it set `bb_fb_index=cur_fb_index` and call `on_bounce_frame_finish`. DMA EOF reaches this function at lines 962–970. This validates that two observed full-frame callbacks span adoption and subsequent full-frame presentation before the former front is reused.
- `esp_lcd_rgb_panel_get_frame_buffer`, lines 446–461, advances its vararg after each returned buffer, including the last; the production trailing `NULL` is therefore required by this implementation.
- Callback registration is at lines 396–418. ISR-IRAM and internal-context checks are conditional on `CONFIG_LCD_RGB_ISR_IRAM_SAFE`; the installed Kconfig defaults that option off (lines 13–21), and the accepted sdkconfig leaves it unset. The BSP callback is `IRAM_ATTR` and uses `xSemaphoreGiveFromISR`. The SDK header at `components/esp_lcd/rgb/include/esp_lcd_panel_rgb.h`, lines 114–120, says callbacks execute in ISR context and require IRAM placement when that option is enabled. Enabling it later requires validating the callback call chain and semaphore context against those constraints.

Commands and results:

| Command | Result |
|---|---|
| `python -B -X utf8 -m unittest tests.integration.test_lcd_presentation -v` | **PASS 1/1**, 1.329 s initially and 1.101 s after rebuilding the host adapter. Compiled the real production `bsp.c`; exercised two consecutive delayed handoffs, immutable scanned frame, missing second boundary with a 200 ms timeout, draw error, registration error, geometry/two-frame PSRAM setup, fail-dark writes, and GPIO0/backlight init ordering. |
| Pre-fix command: `$env:CDM_PRESENTATION_BASELINE_BSP='artifacts/orca-harness-runtime/flicker-baseline-bsp.c'; & 'C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe' -B -X utf8 -m unittest discover -s tests/firmware -p 'test_presentation.py' -v` | **Expected red reproduced.** The approved same-cohort baseline hash was `2D3D21445DCF31EB51EE20544B512DF19C0399B64BA734F0E25F4B946940B3BE`; build succeeded and test failed from harness exit 3 at `presentation assertion line 74: scanned[0] == scanned_before`, not at setup/compiler. Environment override was removed. |
| `& 'tests/firmware/build-host.ps1'` | **PASS**, exit 0. |
| `python -B -X utf8 -m unittest discover -s tests/firmware -p 'test_*.py' -v` | **PASS 19/19**, 4.137 s, including the distinct frozen legacy evaluator **29/29**, receiver/cache/time, selected-B renderer/navigation, and production presentation owner test. |
| `python -B -X utf8 -m unittest tests.integration.test_cdm_session_selection tests.integration.test_pc_producer_to_c -v` | **PASS 21/21** (one selected-session + 20 producer-to-C), 15.648 s. The selected-session case uses production C; producer frames exercise actual PC normalization/canonical bytes through the C receiver. |

The independent integration seam models only the SDK ownership order established above; it does not model LCD electrical timing, DMA underrun, panel scanout, or a camera. It is host evidence for the code's handoff/failure logic, not proof of no physical flicker.

## C/I/F and live L1–L8 status

| Gates | Result | Remaining evidence |
|---|---|---|
| C1 | **PASS (accepted build)** | Frozen IDF build log/source/artifact hashes match; no new build run. |
| C2, C8 | **not_run** | Corrected board has no 30-second observation, physical BOOT/RST/GPIO0 validation, or measured accepted-frame-to-LCD latency. |
| C3–C7 | **PASS (host); physical not_run** | Existing B/C host coverage plus these integrations remains intact; actual screen values/readability and physical error/recovery still need device evidence. |
| I1–I2 | **PASS (synthetic host)** | This review introduced no account/session data and made no PC changes. |
| I3–I4 | **PASS (host); device not_run** | Production producer-to-C/receiver path passes; no COM/device observation was performed. |
| F1–F9 | **PASS (host/build evidence); physical not_run** | Relevant firmware suite and accepted build pass; physical refresh, BOOT, clipping, temperature plausibility and endurance remain unmeasured. |
| L1 | **Prior host PASS; live not_run** | Explicit session selection/A→B replacement is unchanged; selected-session integration passes. |
| L2 | **Prior host PASS; live not_run** | Cumulative token event and observation-time handling is unchanged; producer-to-C suite passes. |
| L3 | **Prior host PASS; live not_run** | Session channel identities and source/normalized totals are unchanged; producer-to-C suite passes. |
| L4 | **Prior synthetic host PASS; live not_run** | Account quota remains distinct from session telemetry; no live account was read. |
| L5 | **Prior host PASS; live not_run** | Provider windows/durations/unknown windows are unchanged; current producer-to-C suite passes. |
| L6 | **Prior host PASS; live not_run** | Token subset/total and account/session separation are unchanged; current C interop passes. |
| L7 | **Prior host PASS; live not_run** | Original timestamps, source age and receive age/cache semantics are unchanged; current C interop passes. |
| L8 | **PASS for this synthetic review; live not_run** | Only synthetic test fixtures and the two approved observation metadata records were read; no credentials, conversations or real session files were accessed. |

Required remaining coordinator/device gates include corrected firmware upload and physical display observation, ≥30 s stability, clipping/readability (including the separate scientific-value issue), short/held BOOT and RST behavior, GPIO0 electrical behavior, accepted-frame latency, sensor plausibility, fault/recovery and endurance. No physical result is inferred from a host pass, and no `product_pass=true` is claimed.

## Scope

Only these review-owned files were changed: `tests/integration/test_lcd_presentation.py`, this report, and the current Task section appended to `docs/agent-runs/orca-luna/checkpoint.md`. Read only the two Task-approved observation JSON records and the same-cohort baseline BSP exception; no COM, flash, reset, Git mutation, real account/session/auth data, or other worktree/history was used.
