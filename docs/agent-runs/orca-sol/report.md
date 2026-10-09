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
