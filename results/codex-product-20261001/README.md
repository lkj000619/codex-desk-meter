# Codex Desk Meter reference build record

This is the independent Codex reference product build. It is not a benchmark
comparison result. No board was flashed or opened during this run.

## Commits and build

- First product implementation: `6ccdeb1739c70aeaf2d2e0e65f7b56200e87d00d`.
- Firmware receive/BOOT behavior and host integration tests: `04dd1a0c1de742bfbfbaffaaef7984371abeb5c4`.
- Build record and isolated output path: `d48bf6cc7574bc129b1f119ace0e7fcfd0d093c1`.
- Source commit recorded by the clean build: `d48bf6cc7574bc129b1f119ace0e7fcfd0d093c1` (`source_tracked_dirty=False`).
- ESP-IDF: 5.3.2; target: ESP32-S3; Xtensa GCC: pinned 13.2.0; serial Ninja build.
- ASCII source stage: `C:\Espressif\projects\codex-desk-meter-reference-20261001-024909`.
- Build directory: `C:\Espressif\builds\codex-desk-meter-reference-20261001-024909`.
- Full transcript: `results/codex-product-20261001/build.log`.
- The first full attempt exposed an Xtensa GCC ICE in the IDF RGB driver and a bounded-format warning in the display code. The display formatting was bounded, the build script gained one serial retry, and this clean full build completed successfully.

## Artifacts

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| `artifacts/codex_desk_meter.bin` | 0x54DF0 bytes | `824cd21be557b2330d92d1bf32bf428de004e6d683fc08b9915f13dfc89eb67b` |
| `artifacts/bootloader.bin` | 0x5490 bytes | `38258a697adeb0ab7570a04c3ed3662b26c7fa92962e53245eabbc22b2d894cb` |
| `artifacts/partition-table.bin` | see build output | `7f00b6c042a89b15b0cac534f82ed988caf29278ff5700b0c511eb1b5bb7c820` |

The application fits the 1 MiB app partition with 0xAB210 bytes free. Build
artifacts are in this directory's `artifacts/` subdirectory.

## Automatic tests

- `python -m unittest discover -s tests -v`: 14 passed. Covers fixture
  normalization, schema/CRC/line encoding, stale values and reset-source
  separation, sender sequence persistence/wrap/failure behavior, and audit log.
- `cmake --build build-host` followed by
  `ctest --test-dir build-host --output-on-failure`: 3 passed. Includes the
  firmware receiver module and a simulated firmware main loop exercising
  native USB packet-to-display and BOOT stable-to-render/hold behavior.
- `python scripts/cdm_collector.py` emits a valid synthetic fixture frame to
  stdout and reports `offline_fixture_only`. No COM port was opened.

These host tests do not establish physical LCD color/orientation, USB device
enumeration, BOOT electrical behavior, RTC battery holdover, or actual receiver
acceptance. Board validation is pending.

## PC fixture sender

Run from the repository root. The default dry run prints one synthetic `cdm/1`
frame without opening hardware:

```powershell
python scripts/cdm_collector.py
```

After the operator confirms the receiver has no saved sequence, transmit once
through the board's native USB Serial/JTAG COM port (replace `COM3` with the
enumerated port):

```powershell
python scripts/cdm_collector.py --send --port COM3 --device-alias desk316 --initialize-empty-receiver
```

The persistent sender sequence is `.cdm-state/desk316.json`. Subsequent manual
refreshes omit `--initialize-empty-receiver`. For periodic refresh:

```powershell
python scripts/cdm_collector.py --send --port COM3 --device-alias desk316 --watch --interval-seconds 60
```

The default audit output is `logs/cdm-serial.jsonl`; a host write is not a
device acknowledgement. Use `--all-provider-fixtures` to cycle the checked-in
valid synthetic provider cases. Values in these fixtures are not actual account
remaining quota.

## Operator hardware check

1. Inspect the build artifacts and confirm the board's USB port and backup
   procedure. Upload with the printed ASCII stage/build paths, for example:

   ```powershell
   idf.py -C C:\Espressif\projects\codex-desk-meter-reference-20261001-024909 -B C:\Espressif\builds\codex-desk-meter-reference-20261001-024909 -p COM3 flash monitor
   ```

2. Confirm the LCD lights, landscape orientation, all three BOOT views, one
   accepted fixture frame, stale/error presentation, and recovery after a later
   good frame. Confirm the RTC keeps time through a power cycle.
3. Close the monitor before running the PC sender; the serial port is exclusive.
4. Record photographs or observations and the actual enumerated COM port. Do
   not mark the reference product fully accepted until these checks pass.

Live account integration status is `offline_fixture_only`: no Codex, Claude,
Antigravity, or IDE account/runtime source is collected; no credentials or
undocumented source were accessed. No session token counter was available from
the provided execution instrumentation, so no token usage is claimed.
