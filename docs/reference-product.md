# Codex Desk Meter reference product

This workspace contains an independently implemented ESP-IDF v5.3.2 product for
the Waveshare ESP32-S3-LCD-3.16 and a fixture-only PC collector. This is the
reference product build; it is not a candidate comparison run or a product
acceptance claim.

## Product data path

```text
repository fixture files
    -> Python provider/global-reset normalizers
    -> canonical UTF-8 cdm/1 JSON + CRC32 + persistent uint32 sequence
    -> USB serial, 115200 baud, 8N1, no flow control
    -> firmware canonical/schema/CRC/sequence validation
    -> last-good state and stale marking
    -> ST7701 820 x 320 landscape display
```

The current collector reads only `experiments/fixtures/`. Provider API, Codex
account, Claude Code, Antigravity, and IDE telemetry collection is not
implemented. It does not read credentials or contact those sources. Its status
is `offline_fixture_only`; the percentages and reset records are synthetic
fixture values, never an account's actual remaining quota. It normalizes the
Codex and Claude/Google fixture providers through one registry and preserves
unsupported, error, unavailable, and stale statuses. The `codex-reset.com`
forecast fixture remains a separate normalized source; the LCD shows only
`codex-resets.com` history.

## PC commands

Run commands from the repository root with Python 3.11.15. The no-argument
command prints one valid fixture frame to stdout and summary information to
stderr, without opening a serial port:

```powershell
python scripts/cdm_collector.py
```

For first use, connect the board and confirm its receiver has no sequence state.
Initialize the sender file and transmit one frame:

```powershell
python scripts/cdm_collector.py --send --port COM3 --device-alias desk316 --initialize-empty-receiver
```

Subsequent one-shot sends are the manual refresh command. The sequence state is
persisted at `.cdm-state/desk316.json`; a reserved number is saved before the
serial write, so a failed write consumes it. Restarting the collector keeps
using the saved successor without rebooting the board. A missing or corrupt
state file stops transmission. The tool holds an exclusive alias lock while it
sends. The default raw fixture/frame audit log is `logs/cdm-serial.jsonl` and
records fixture contents and hashes, exact canonical output bytes, sequence,
port and byte count. `cdm/1` has no device acknowledgement: a successful host
write is not proof that the ESP32 accepted or displayed the frame.

To recollect and send periodically, run:

```powershell
python scripts/cdm_collector.py --send --port COM3 --device-alias desk316 --watch --interval-seconds 60
```

The supported automatic interval is 5 to 60 seconds. Manual refresh is the
one-shot command above. If a provider fixture's `observed_at` is at least 300
seconds old, its source value is retained and explicitly marked stale; sending
it again does not make it fresh. `--all-provider-fixtures` sends the valid cases
in the fixed synthetic provider fixture matrix for inspection and testing.

Do not pass `--initialize-empty-receiver` again while the board retains an
ordering state. If sequence state is lost, archive it and reset the powered
board before explicitly initializing a replacement. The collector rejects
arbitrary source paths; only checked-in fixtures are accepted.

## Device behavior

- The landscape dashboard displays source-provided quota windows, provider and
  agent identity, percent used/remaining, source observation time, reset time
  or reset status. It rotates through all windows in pages of eight every eight
  seconds.
- The global view displays the latest `codex-resets.com` reset and elapsed time.
  With no record or an unusable clock it shows a default/unknown state; it does
  not show a fabricated zero or future reset schedule.
- The status view retains the last good snapshot and exposes receiver and
  provider stale/error status. A malformed, corrupt, unsupported-version,
  oversized or out-of-order frame does not replace last-good data.
- BOOT cycles dashboard, global reset and status. It is debounced for 50 ms and
  polled every 10 ms. RST remains the board's system-reset control.
- PC automatic refresh runs independently of BOOT. Disconnecting the host does
  not clear receiver ordering state; a later accepted sequence clears receiver
  transport error state.
- The PCF85063 RTC restores its clock on boot when the RTC contains a plausible
  date. An accepted host frame synchronizes system time and writes the RTC for
  holdover. RTC battery presence, retained time, board display orientation and
  BOOT timing still require physical confirmation.

GPIO0 is both the board BOOT button and the ST7701 3-wire command chip-select
listed in the fixed manufacturer pinout. Firmware initializes the LCD first,
then restores GPIO0 as the pulled-up BOOT input. The display uses the board's
fixed RGB pins, reset pin and backlight pin, with a software landscape-to-panel
framebuffer mapping.

## Build and operator handoff

Use the pinned ESP-IDF and host toolchain. The build script copies only the
current product source and its resolved component dependencies to a physical
ASCII staging directory because Windows resolves both `subst` and junction
current directories back to this Korean workspace before Xtensa compilation.
The script builds serially after an observed parallel Xtensa compiler ICE, then
runs `idf.py build` to record the final IDF command result. It does not flash or
erase the board.

```powershell
& .\scripts\build-reference-firmware.ps1
```

The script writes the full transcript under
`results/codex-product-20261001/build.log`, copies the application,
bootloader and partition binaries into that result's `artifacts/`, and prints
their SHA-256 hashes. The matching ASCII staging source/build paths are printed
in the log.

After reviewing the artifact and backing up the board as required by the
operator's hardware procedure, upload only the application build:

```powershell
idf.py -C C:\Espressif\projects\<printed-stage-name> -B C:\Espressif\builds\<printed-build-name> -p COM3 flash monitor
```

Close the monitor before starting the PC collector because COM3 is exclusive.
Confirm the LCD lights in landscape orientation, then run the one-shot sender.
Use BOOT to verify all three views, send a newer frame, reject an intentionally
bad test frame only in the host test harness, and confirm the next good frame
recovers. No firmware has been uploaded in this reference implementation run.

## Automated evidence and limits

`python -m unittest discover -s tests -v` checks fixture normalization against
the checked-in schemas, both reset-source identities, stale/absolute-value
rules, canonical CRC and line encoding, persistent sequence and wraparound,
and the raw audit writer. `cmake --build build-host` plus CTest compiles and
calls the same C receiver used by firmware against ESP-IDF's cJSON; it covers
canonical frame acceptance, payload fields, source identity, CRC rejection,
sequence ordering, debounce, page selection, RTC conversion and stale boundary.

These are host tests. No COM port was opened, and the firmware has not been
observed on the actual LCD. The application does not yet collect real account
usage. Host write completion, loopback, and host C receiver tests are not
physical ESP32 receiver evidence. Operator validation remains necessary before
freezing this reference product.
