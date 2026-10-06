# Reproduction and hardware check

## Build and host verification

Run one command at a time from the project root, using ESP-IDF v5.3.2:

```text
idf.py --version
idf.py set-target esp32s3
idf.py build
cmake -S tests/host -B build-host -G Ninja
cmake --build build-host
ctest --test-dir build-host --output-on-failure
python -m unittest discover -s tests -v
python tests/test_production_receiver.py
python -m py_compile pc/collector.py pc/pipeline.py pc/sender.py pc/serial_sender.py pc/gui.py pc/legacy_adapter.py
python scripts/validate-end-to-end-result.py --result results/20261007-codex-cli-gpt-6-luna-r01/end-to-end-result.json --manifest .benchmark-inputs/e2e-evaluation-manifest.json --evidence-root .
```

Observed in this run:

- `idf.py --version` reported ESP-IDF v5.3.2. `idf.py set-target esp32s3` configured the target. The SDK printed a Git safe-directory ownership warning, but CMake completed successfully; no global setting was changed.
- `idf.py build` passed and generated `build/codex_desk_meter.bin` (0x4d720 bytes); the 1 MiB app partition had 70% free.
- The LCD requests two RGB framebuffers in PSRAM and allocates one 524,800-byte PSRAM canvas. The configured framebuffer/canvas budget is 3 × 524,800 = 1,574,400 bytes (about 1.50 MiB) before driver overhead. Firmware logs free PSRAM/internal heap after allocation; that runtime measurement was not available here.
- Host CMake configured with the prepared Clang 22.1.8 compiler. The build linked the production `meter_core.c` into `meter_receiver_cli.exe`, parser/state tests, and the idle-dimming test. CTest passed 3/3.
- After the host binary existed, `python -m unittest discover -s tests -v` passed 22 tests with no skips. A direct `python tests/test_production_receiver.py` passed 4 tests. This includes the fixed common sequence 0 and 1 frames entering the production C receiver, the 29 wire/schema rejection cases, duplicate rejection, and last-good retention after bad CRC. The first unittest invocation was before the CMake build and skipped the C cases; it is not counted as a successful receiver run.
- Python compilation of the listed PC collector, normalization, sender, GUI, and adapter modules passed.
- The offline pipeline test compared its exact encoded sequence 0 and sequence 1 frames to the supplied common stimulus and checked the remaining values 58% and 82%. This proves host encoder agreement and production C host-receiver acceptance only. No USB write or LCD result was observed in this run.

The Python tests cover fixture adapter isolation, source-age 299/300 second boundaries, error recovery with last-good values, sender-state corruption, explicit empty-receiver initialization, and sequence consumption after a failed write. C host tests exercise the same parser/state module linked into firmware. These are host tests; they do not establish physical USB disconnect recovery or display readability.

## PC fixture and sender use

The collector is offline and reads only `pc/fixture-set.json`. A reproducible smoke collection is:

```text
python -m pc.collector --profile common --reference-time 2026-09-30T18:40:49Z --output results/20261007-codex-cli-gpt-6-luna-r01/common-payload.json
```

For a physical run, first let the operator select the COM port and stable device alias. Confirm the receiver has no accepted sequence before initializing sender state. On the first transmission only, add `--initialize-empty-receiver`; preserve that state file and omit the flag for later transmissions, including after PC restart or COM re-enumeration. A host `written` receipt is not a device ACK. Keep the raw frame log and optional ESP log, and distinguish an `accepted cdm/1 frame sequence=N` device log from the host write receipt.

```text
python -m pc.serial_sender --port COM3 --device-alias lcd316 --profile common --reference-time 2026-09-30T18:40:49Z --state results/20261007-codex-cli-gpt-6-luna-r01/device-state.json --raw-log results/20261007-codex-cli-gpt-6-luna-r01/raw-cdm-frames.jsonl --device-log results/20261007-codex-cli-gpt-6-luna-r01/device.log --capture-device-log-seconds 2 --initialize-empty-receiver
```

Wait five seconds and invoke the same command again with the same alias, state, and raw-log paths, omitting `--initialize-empty-receiver`. Do not reset the board to recover the sender. In this run the command was documented but not executed because serial access is prohibited.

## Physical procedure for the operator

Use the frozen build artifact. Do not hold BOOT while resetting. Use the operator-selected USB port and a setup that keeps board power present when testing only a USB data disconnect.

1. Boot normally. Record the boot and PSRAM log lines, verify the 820×320 landscape startup screen, and leave it untouched for at least 30 seconds.
2. Send common fixture frames with the persistent sender state above. Keep the raw bytes and device log. Look for accepted sequence 0 and 1 markers; a host write receipt alone does not establish receipt.
3. Within two seconds of each accepted marker, check that the two dashboard cards show the source labels, five-hour remaining 58%, weekly remaining 82%, lookup time, reset state, and visible `SOURCE STALE` where the source timestamp is old.
4. Tap BOOT once after normal boot to move Dashboard → Global Reset → Status, and tap again through the remaining pages back to Dashboard. Record each page and verify that short presses do not reset the board. Test RST separately without BOOT held.
5. On Global Reset, verify `codex-resets.com`, lookup time, most recent reset and elapsed time, or the explicit default when history is absent. Do not substitute `codex-reset.com` forecast data.
6. On Status, verify sequence, receive age, transport/parser error, source status, and last-good time. Leave the last accepted frame untouched until receive-age stale appears. Restore USB data without resetting the board, send the next durable sequence, and record accepted/rejected logs and recovery timing.
7. Check backlight readability before and after 60 seconds idle. This optional feature's PWM output still needs physical confirmation.

No serial port open, flash, reset, erase, or physical board observation was performed in this run. The orientation correction and redesigned dashboard are build-tested only. Physical 30-second persistence, acceptance markers, all three visible pages, BOOT return behavior, stale/recovery timing, and brightness remain unmeasured. Do not treat the earlier fragmented-screen observation as evidence for this modified binary.
