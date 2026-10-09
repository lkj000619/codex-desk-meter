# ESP32-S3 firmware and B GUI implementation

Run `run_c968c43361da` · Task `task_b1214421a314` · Dispatch `ctx_ce28c7cbe236` · worker terminal `term_9a4ebce2-fd56-4795-b238-e480cc1dc1bb`.

## Delivered and verified

The firmware links the ST7701 BSP, `cdm/1` receiver/cache/time module, three-screen Swiss Studio Meter renderer, BOOT navigation, and the separately contained internal-temperature feature. The actual PC synthetic 3,279-byte frame is accepted by the linked C receiver; its four usage records and one global record stay distinct. The B browser/design gate passed independently in `docs/agent-runs/orca-luna/gui-b-review.md`; the firmware renderer is separate code with separate pixel tests.

`tests/firmware/build-host.ps1` compiled `firmware/main/cdm.c`, `legacy.c`, and `gui.c` into one host adapter. `python -B -X utf8 -m unittest discover -s tests/firmware -p 'test_*.py' -v` passed **10/10**. These tests include the frozen section-5 legacy evaluator's **29/29 cases**, actual PC frame interop, malformed/canonical/CRC/length/sequence/wrap rejection, independent provider failure and recovery, source age 0/299/300 against an anchored clock, and actual 820×320 B framebuffer pixels. The framebuffer checks cover six quota windows over three reachable pages, three-screen wrap, session changes leaving account quota pixels unchanged, Waiting, Unknown, error last-good, and global fallback. Generated host PPM files are in ignored `tests/firmware/.build/` for inspection; the coordinator may regenerate them with the host test command.

`idf.py set-target esp32s3` and `idf.py build` both succeeded with ESP-IDF **v5.3.2**. Full command output: [set-target-output.txt](set-target-output.txt), [build-output.txt](build-output.txt). The SDK's Windows compiler fails when the project path contains Korean characters, so the owned `firmware/` source was staged byte-for-byte in `C:/Espressif/tmp/cdm-sol-task_b1214421a314`. All **15** source/config files were SHA-256 compared against the owned tree before the final build. The staging directory is build scratch, not another product implementation. The exact successful commands were:

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONUTF8='1'
$env:IDF_TOOLS_PATH='C:/Espressif/user-tools'
. 'C:/Espressif/v5.3.2/esp-idf/export.ps1'
$env:TEMP='C:/Espressif/tmp'
$env:TMP='C:/Espressif/tmp'
$env:IDF_CCACHE_ENABLE='0'
Set-Location 'C:/Espressif/tmp/cdm-sol-task_b1214421a314'
idf.py set-target esp32s3
idf.py build
```

The final generated `sdkconfig` has ESP32-S3, 16 MB flash, 8 MB Octal PSRAM at 80 MHz, PSRAM malloc, and USB Serial/JTAG console. The RGB DMA framebuffer is one `320×820×2 = 524,800` byte allocation in PSRAM; firmware checks that its pointer is external RAM before enabling the active-low GPIO6 backlight. The 820×320 logical renderer writes into this portrait framebuffer with the landscape coordinate transform. Font glyphs and colors are compiled constants; no web font, runtime allocation, or fabricated live value is required by the renderer.

| Artifact in ignored `firmware/.host-tools/final-build/` | Bytes | SHA-256 |
|---|---:|---|
| `codex_desk_meter.bin` | 307,440 | `1AE614E892F86E785025745B2E8F643718008060F3B99B4DB9CEFEB77A9D01C8` |
| `bootloader.bin` | 21,504 | `F4C5160D0777EBDA11EDAC881853B211300323E5CF8F96EEEDA5314D731D02AB` |
| `partition-table.bin` | 3,072 | `7F00B6C042A89B15B0CAC534F82ED988CAF29278FF5700B0C511EB1B5BB7C820` |
| `sdkconfig` | 70,020 | `46788F1C30A51868DA7C66C41DEF9045514FAAF393BC68EC0D6F05DF4DACA452` |

The application image occupies `0x4b0f0` bytes of a `0x100000` byte app partition; the build check reports 71% free. No flash, COM open, reset, account read, or physical observation was performed by this worker.

## Hardware and data decisions

The LCD pin map, 18 MHz portrait RGB timing, ST7701 commands, data bit order, and active-low backlight follow `docs/hardware/version-2-capabilities.md` and the specified raw manufacturer source. GPIO0 is held as LCD SPI CS through the ST7701 multiplex constructor; that constructor sends initialization commands and deletes command IO. The firmware then initializes RGB, obtains and fills the PSRAM framebuffer, drives CS high, changes GPIO0 to pulled-up input, and turns on GPIO6 backlight. Runtime BOOT samples are debounced at 10 ms task intervals; a short release cycles Usage → Global Reset → Status, while a 600 ms hold advances the window page. RST remains reset only. GPIO0 electrical behavior, panel orientation, clipping and font readability require coordinator hardware evidence.

`cdm.c` validates the whole LF-terminated canonical UTF-8 frame (including sorted keys, compact form, ≤65,536 bytes and CRC32) and schema/semantic constraints before atomically replacing its cache. Its uint32 sequence persists across USB disconnect and stale frames; accepted data anchors UTC to monotonic time. Source age and receive age are calculated independently, with age ≥300 s stale. Error records keep the last good values and original timestamps; unavailable/unknown records display placeholders without deleting the hidden cache. Session token channels show normalized input+output and original source total separately, while cached input and reasoning output are labeled included subsets. All quota provider/window records retain stable IDs and exact labels; page advancement reaches all records without assuming 5-hour or weekly duration. The global screen reads only `codex-resets.com` with latest → last-known → default state; elapsed time is unknown without an anchor.

## F9: three onboard candidates, one implementation

| Candidate | User value | Resources and cost | Risk | Reproduction test | Decision |
|---|---|---|---|---|---|
| Internal chip temperature on Status | Provides a local device-health reading while PC is absent | ESP32-S3 built-in temperature sensor, IDF `esp_driver_tsens`, no pins/credentials; one small `f9_temp.c` module and one Status row | Sensor can fail or measure die temperature rather than room temperature | Cross-build the module; on board compare plausible changing reading and verify `UNKNOWN` fallback | **Selected and implemented**; bounded read failure leaves LCD/transport running |
| PCF85063 RTC offline clock | Could keep time when PC is disconnected | Existing I2C GPIO7/15, RTC driver/init and backup-power validation | Unknown backup power or unset clock could fabricate elapsed values | Remove PC link with verified RTC anchor and power continuity | Not selected: would weaken strict unknown-clock semantics without hardware calibration |
| QMI8658 tilt rotation | Could reorient the display automatically | Existing I2C GPIO7/15, sampling/debounce and alternate layout | Unverified mounting/orientation could rotate the 820×320 UI incorrectly | Measured orientation/debounce/return on actual board | Not selected: greater layout and input risk for this desk display |

## C/I/F evidence map and operator actions

| IDs | Current evidence and remaining gate |
|---|---|
| C1 | **pass, build only**: ESP-IDF target/build logs and artifact hashes above. |
| C2, C8 | **not_run**: coordinator must upload, observe 820×320 landscape for ≥30 s, test BOOT short/held and RST, measure accepted frame → LCD ≤2 s. Host framebuffer tests establish pixels, not hardware timing/readability. |
| C3–C5 | **host pass, physical not_run**: renderer pages all quota windows, keeps session totals separate, and shows global latest/last-known/default. Compare actual LCD against parsed frame and capture timestamps. |
| C6–C7 | **host pass, physical not_run**: global source/captured timestamp, source/receive ages, error/cache/recovery are represented; run fault transitions on the device. |
| I1–I2, F1–F2, F6–F7 | **PC-owned evidence / coordinator gate**: firmware consumes the agreed PC frame and does not claim collector or live-account success. PC owner is remediating watch timestamp, cold-global capture and per-provider cache cases. |
| I3, F3 | **host wire pass, device not_run**: actual PC synthetic frame accepted by production C receiver; physical serial bytes/sequence/reconnect receipt and device observation remain coordinator-owned. Host write is not a device ACK. |
| I4, F4–F5 | **host pass, physical not_run**: production C receiver/cache and B framebuffer linked/tested. Verify panel rendering, GPIO0, fault persistence and recovery on board. |
| F8 | **build evidence present, physical not_run**: no `product_pass=true`; unmeasured latency, power, frame rate, physical C/I/F/G scores are `null`/`not_run`. |
| F9 | **implemented/build pass, physical not_run**: selected internal temperature feature and fallback; validate sensor reading on device. |

Coordinator-only upload/observation procedure:

1. Verify the three binary hashes above, identify the intended device and COM port, then from the staged build directory run `idf.py -p <COM_PORT> flash monitor` with the already exported IDF environment. The build log also provides the exact three flash offsets if a binary-only upload is preferred. Record port, firmware hash, boot log, and screen photo/video. Do not hold BOOT during reset; it can enter ROM download mode.
2. Before the first frame, record `WAITING / NO CACHE`. Send the synthetic PC frame via the PC owner's sender through the actual wire path and retain the raw sent bytes/sequence. Compare every quota provider/window and session total/subset/observation to the source frame. Confirm accepted frame to redraw latency ≤2 s with timestamps; a host write receipt alone does not prove device acceptance.
3. Cycle short BOOT presses through all three screens and hold BOOT ≥600 ms to reach every quota page. Compare global latest/captured/elapsed with `codex-resets.com` data and personal quota reset separately. Exercise error, null, source-age 299/300 s, disconnect/reconnect, stale last-good and recovery with synthetic frames; record original observation time, source age and receive age independently.
4. Observe the powered LCD for ≥30 s, inspect clipping/readability/rotation/backlight polarity and GPIO0 transitions, then press RST as a reset-only action. For USB disconnect, provide independent board power before removing the serial link; record continued display and valid recovery. Validate internal temperature or `UNKNOWN` fallback. Keep real-account collection under coordinator control.

The physical product verdict remains `not_run`; no whole-product pass is claimed.

## 2026-10-09 correction: current active usage and scoped identity

Run `run_c968c43361da` · Task `task_e44125e18973` · Dispatch `ctx_5f9f6d8e9d11` · worker terminal `term_9a4ebce2-fd56-4795-b238-e480cc1dc1bb`. This section amends the receiver result above; the accepted initial build commands and hashes remain as historical evidence.

The PC frame is the complete current active source collection. The receiver now stages an empty next usage/global list, builds it from the validated frame, and swaps it atomically only after all records pass. A selected session A followed by selected session B therefore displays only B; repeated changing observation IDs do not retain inactive history. A rejected frame leaves the active list, cached values, timestamps, and receiver sequence unchanged.

Usage identity is provider, agent, host, model, account profile, source kind, metric kind, and `snapshot_id` together. Distinct contexts may share a snapshot ID; an exact duplicate of this full scoped identity fails explicitly with `SNAPSHOT_DUPLICATE`. Exact scoped ID matching takes precedence for cache carry. A session never inherits another session's cache. For a non-session error/unknown with a changed observation ID, last-good carries only if exactly one prior and exactly one current record share its complete source context; ambiguous unmatched records remain cold/unknown. Original observation timestamps remain attached to the carried good value, and a later good record recovers independently.

Verification used the actual linked production C parser/cache and existing host adapter. `tests/firmware/build-host.ps1` succeeded; `python -B -X utf8 -m unittest discover -s tests/firmware -p 'test_*.py' -v` passed **18/18**, including the existing frozen section-5 evaluator's **29/29** cases and the new active-list/scoped-identity regressions. The read-only independent `python -B -X utf8 -m unittest discover -s tests/integration -p 'test_cdm_session_selection.py' -v` passed **1/1** after previously exposing the `[A,B]` defect. New cases cover A→B current selection, same ID across provider/metric contexts, true scoped duplicate atomic rejection, 20 changing observation IDs without list growth, single-source changed-ID error/unknown carry and recovery, ambiguous same-context non-inheritance, same-session last-good, and cross-context cache isolation.

The **incremental** ESP-IDF v5.3.2 `idf.py build` succeeded after replacing only staged `main/cdm.c`. All **15** owned firmware source/config files were SHA-256 identical to the ASCII SDK staging tree at build time. The exact build invocation, with output captured in [build-active-usage-output.txt](build-active-usage-output.txt), was:

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONUTF8='1'
$env:IDF_TOOLS_PATH='C:/Espressif/user-tools'
. 'C:/Espressif/v5.3.2/esp-idf/export.ps1' | Out-Null
$env:TEMP='C:/Espressif/tmp'
$env:TMP='C:/Espressif/tmp'
$env:IDF_CCACHE_ENABLE='0'
Set-Location 'C:/Espressif/tmp/cdm-sol-task_b1214421a314'
python 'C:/Espressif/v5.3.2/esp-idf/tools/idf.py' build *> 'C:/Users/이광진/orca/workspaces/codex-desk-meter/experiment-orca-harness-20261008/docs/agent-runs/orca-sol/build-active-usage-output.txt'
```

| New file | Bytes | SHA-256 |
|---|---:|---|
| `firmware/main/cdm.c` | 27,653 | `33899E302733A685B78F7171B87CC7827D4E2B34D8ADE0A82F0290C6D16B9C1C` |
| `tests/firmware/test_active_usage.py` | 6,735 | `13EB80DC31A30D1522E9D4FB0E0FED792CB746915451CAD2F2FA4455E7D20C33` |
| `build-active-usage-output.txt` | 4,638 | `91D7EFFDB9099AD01B943295ED31DFFA94675B533B0B71CA089CF059EA79514D` |
| `firmware/.host-tools/active-usage-build/codex_desk_meter.bin` | 307,680 | `385130667AB15CA8DCC665E70FC06882B1E89535BDE8D84AF05FDC2B36C1EF72` |
| `firmware/.host-tools/active-usage-build/bootloader.bin` | 21,504 | `F4C5160D0777EBDA11EDAC881853B211300323E5CF8F96EEEDA5314D731D02AB` |
| `firmware/.host-tools/active-usage-build/partition-table.bin` | 3,072 | `7F00B6C042A89B15B0CAC534F82ED988CAF29278FF5700B0C511EB1B5BB7C820` |
| `firmware/.host-tools/active-usage-build/sdkconfig` | 70,020 | `46788F1C30A51868DA7C66C41DEF9045514FAAF393BC68EC0D6F05DF4DACA452` |

The new application image occupies `0x4b1e0` bytes of the `0x100000` byte app partition, leaving 71% free. Coordinator-only next action: review the corrected source and new binary, then perform upload, serial/GUI observation, BOOT operation, synthetic device fault/recovery and live-account gates under the operator procedure above. For its upload step, verify and use the **new** three binary hashes in this correction table; the three binary hashes in the original section identify the superseded historical build. Physical, live, and COM evidence remain `not_run`; no `product_pass=true` is claimed.

## 2026-10-10 correction: RGB scan-visible partial clears

Run `run_c968c43361da` · Task `task_63d11f3c24cb` · Dispatch `ctx_2363ff345723` · worker terminal `term_e1bc5a22-2975-4c7e-a9c1-82097648f0e6`. This section supersedes the firmware app binary in the previous section only; prior verdicts and artifacts remain historical evidence. Coordinator deliveries `delivery_1d40dbac398e` and `delivery_899c2bcf9bbf` were read and acknowledged before this submission.

### Observation, cause, and boundary

The sanitized post-data observation records repeated flashes/white partial clears with populated Usage and Status frames. At least one live frame reached the device: Status physically showed `FRAME / CRC VALID`, `CONNECTED`, receive age 10 s and source age 44 s; the Usage view showed 31% and 68% used in its two quota windows. This does not establish uninterrupted display stability. The earlier 13-second black interval was the user's manual RST, not this recurring defect. Long scientific token strings also appear clipped; this is a separate display finding, not changed here. No original video/JPG or visible source identifier is included in this report.

The initial hypothesis was that the renderer exposes its intermediate full-screen PAPER clear to scanout. The production path established it: `main.c` calls `gui_render` on dirty state or every 1000 ms; `gui_render` starts with a full PAPER fill; original `bsp.c` used `num_fbs=1` and `bsp_fill`/`bsp_pixel` wrote directly to the RGB frame pointer. In the installed ESP-IDF v5.3.2 `components/esp_lcd/rgb/esp_lcd_panel_rgb.c`, `lcd_rgb_panel_fill_bounce_buffer` copies chunks from `fbs[bb_fb_index]` while the panel runs; the last chunk updates `bb_fb_index=cur_fb_index` and invokes `on_bounce_frame_finish`. `rgb_panel_draw_bitmap` selects `cur_fb_index` when passed one of its own framebuffer pointers. The manufacturer ST7701 wrapper keeps RGB's `draw_bitmap` method and the existing GPIO0 multiplex sequence. These facts explain how an in-progress clear can become visible without any receiver failure. They establish a firmware race and a host reproduction, not physical proof that every reported flash has this cause.

The fix keeps the 320×820 physical / 820×320 logical mapping and 10×320 bounce buffers. RGB now allocates two 524,800-byte PSRAM frames. The GUI draws into the frame the bounce copier does not use; `bsp_present()` selects that completed frame through `esp_lcd_panel_draw_bitmap(0,0,320,820,...)` and waits for two `on_bounce_frame_finish` notifications after draining an old notification. Two wraps cover a completion already in progress across the submit call before reusing the former front buffer. Each wait is bounded at 200 ms; draw submission or wait failure disables active-low backlight, prevents further pixel writes, returns an error, and `app_main` aborts. The framebuffer getter receives a trailing `NULL` because this installed SDK implementation advances its variadic argument after returning the last pointer. The periodic redraw, stale/receive age, temperature, BOOT navigation, quota/token contents, receiver/cache, and ST7701/CS handoff remain on their prior paths. This adds one frame (524,800 bytes) of PSRAM and no package or graphics framework.

### Red/green regression and host checks

The coordinator supplied the exact original accepted BSP as the sole approved extra read, `artifacts/orca-harness-runtime/flicker-baseline-bsp.c`, SHA-256 `2D3D21445DCF31EB51EE20544B512DF19C0399B64BA734F0E25F4B946940B3BE`. The host test compiles the actual BSP body with fake SDK declarations; the baseline-only `bsp_present` shim is unreachable because the scan-integrity assertion runs first. The fake RGB driver leaves the scanned frame visible during clear/redraw, can delay adoption until a second boundary, and can stop boundaries for the timeout case. Exact baseline command and observed red result:

```powershell
$env:CDM_PRESENTATION_BASELINE_BSP='artifacts/orca-harness-runtime/flicker-baseline-bsp.c'
& 'C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe' -B -X utf8 -m unittest discover -s tests/firmware -p 'test_presentation.py' -v
Remove-Item Env:CDM_PRESENTATION_BASELINE_BSP
```

The BSP compiled; the test failed with harness exit **3** at `presentation assertion line 74: scanned[0] == scanned_before`. The original `bsp_pixel` had changed the pixel being scanned before a frame was complete. With the environment variable absent, the same assertion and subsequent old-front ordering, two-boundary handoff, and fail-dark timeout checks passed. The final fixed `bsp.c` hash is `8A820F95AA58DB42D3C559901918419B8A11712E1D9F4A01F10CB085A890CEEE`. The test does not emulate LCD timing, DMA underrun, electrical conditions, or the camera; physical flicker remains unverified.

Final host commands and results:

```powershell
& 'tests/firmware/build-host.ps1'  # exit 0
& 'C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe' -B -X utf8 -m unittest discover -s tests/firmware -p 'test_*.py' -v  # 19/19
& 'C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe' -B -X utf8 -m unittest discover -s tests/integration -p 'test_cdm_session_selection.py' -v  # 1/1
```

The 19 owned tests include all prior 18 and their frozen 29/29 matrix. The selected-session integration test exercised the actual producer-to-C receiver/GUI path; this display change did not alter it. `git diff --check` passed for the tracked owned changes. The new test hashes are `presentation_sdk.h` `48F1AEC737A806F85464E5FD05394167791904B3BCBC26DE1201FBD5B899BF72`, `presentation_host.c` `B968967C023163B4DD8F014096CDCEFE86419C9BA225177BCDD3E63893790ACA`, and `test_presentation.py` `5D6EC9DA3302558A9EDD6B66F371A21D200038DA6033C024614A8F6D7FFDDEC4`.

### Genuine ESP-IDF build and reproducibility

The checkout has a non-ASCII path, so the real ESP-IDF build ran in `C:/Espressif/tmp/cdm-sol-task_b1214421a314` using installed ESP-IDF `C:/Espressif/v5.3.2/esp-idf` and its Python `C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe`. Only `main/bsp.c`, `main/bsp.h`, and `main/main.c` were recopied into this existing staging tree; all **15/15** source/config files below matched the checkout SHA-256 immediately before and after the build. `sdkconfig` is the generated staged config and its copy is listed separately below.

| Staged relative source/config | SHA-256 |
|---|---|
| `CMakeLists.txt` | `9E9534402359BAB131F26DCF0D246C9E23DDCD8699AA0E5E9DAB634E195020D7` |
| `sdkconfig.defaults` | `A232B9341461C95DDC0C18084A77459013B4C236DDCD6BEEE3108FF175B2FFB8` |
| `main/CMakeLists.txt` | `AF58E3AE2C42CC4E17CA4016464F48B31A90DBE7D21974C7A4740B3A78E14256` |
| `main/bsp.c` | `8A820F95AA58DB42D3C559901918419B8A11712E1D9F4A01F10CB085A890CEEE` |
| `main/bsp.h` | `B80339EF1F22CAC176D67F3073BD5D1D96E9275F9E1242FE1DF05C694786FAB2` |
| `main/cdm.c` | `33899E302733A685B78F7171B87CC7827D4E2B34D8ADE0A82F0290C6D16B9C1C` |
| `main/cdm.h` | `7C900F68AF9B75D85E8CD4E8E2D9E22F2E582BAB5DE2BF3A6B75F1F9D9ADA8C6` |
| `main/f9_temp.c` | `43F760751E10633A132249AB87AD86E63A11DAC97FE2D661B3ED1E31DD6E7812` |
| `main/f9_temp.h` | `645EDDA639A3876506FE9D00B1CD5DE82435BA14DE2B22C4C8C4D8255AAB3B92` |
| `main/gui.c` | `3D0E2B6DB2F425D419DFB6346FBA909C477E24B944ECF3C56AC3568BF172E975` |
| `main/gui.h` | `0781E73DDC3BADA616E334D0308EAB0477C76B33E7797E8D0688CA52A8494780` |
| `main/legacy.c` | `D652633AEDDA1F755DC7190A2104DB361B97EAFB144FC68922D6682D7B89479C` |
| `main/legacy.h` | `EFB69CA3856A50BCF423792805B19999D53C4D919B91DC93FC6DAF610E0ED441` |
| `main/main.c` | `4E1612983701B8951C06BA43A8A8132C725A30A5BAFDAAE1CEE00040CEE812E1` |
| `main/st7701_commands.inc` | `AF9C061384023D46BA85D9530A96630AE8680776D747ED73E2844DCCCF513B1C` |

Exact successful build invocation (exit 0), with complete output in [lcd-flicker-build-output.txt](lcd-flicker-build-output.txt), SHA-256 `5967CC3A615EF58DC6A6A86C0C914882D50FBD4AF5E1208A2A18CAE910A771A0`:

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONUTF8='1'
$env:IDF_TOOLS_PATH='C:/Espressif/user-tools'
. 'C:/Espressif/v5.3.2/esp-idf/export.ps1' | Out-Null
$env:TEMP='C:/Espressif/tmp'
$env:TMP='C:/Espressif/tmp'
$env:IDF_CCACHE_ENABLE='0'
Set-Location 'C:/Espressif/tmp/cdm-sol-task_b1214421a314'
& 'C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe' -B -X utf8 'C:/Espressif/v5.3.2/esp-idf/tools/idf.py' build *> 'C:/Users/이광진/orca/workspaces/codex-desk-meter/experiment-orca-harness-20261008/docs/agent-runs/orca-sol/lcd-flicker-build-output.txt'
```

| Copy in ignored `firmware/.host-tools/lcd-flicker-build/` | Flash address | Bytes | SHA-256 |
|---|---:|---:|---|
| `codex_desk_meter.bin` | `0x10000` | 308,672 | `953782E5486ADBE9743E5B753E716892CFDFBEEF25D23B1702DC1D6050078F1F` |
| `bootloader.bin` | `0x0` | 21,504 | `F4C5160D0777EBDA11EDAC881853B211300323E5CF8F96EEEDA5314D731D02AB` |
| `partition-table.bin` | `0x8000` | 3,072 | `7F00B6C042A89B15B0CAC534F82ED988CAF29278FF5700B0C511EB1B5BB7C820` |
| `sdkconfig` | — | 70,020 | `46788F1C30A51868DA7C66C41DEF9045514FAAF393BC68EC0D6F05DF4DACA452` |

All four copies match the staged build files. The app size is `0x4b5c0` in a `0x100000` app partition, with `0xb4a40` (71%) free. The generated config still selects ESP32-S3, 16 MB flash, Octal 8 MB PSRAM at 80 MHz, PSRAM malloc, and USB Serial/JTAG console; `CONFIG_LCD_RGB_ISR_IRAM_SAFE` is unset. No prior `active-usage-build` artifact was modified. The coordinator and Luna should inspect the new source/build before any coordinator-owned COM flash and real 30-second video/BOOT/stale check. COM, upload, and corrected-board flicker observation are `not_run`; `product_pass` remains false.
