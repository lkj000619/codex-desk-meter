# Follow-up implementation and verification

## Changes

- Changed the ST7701 RGB startup to keep the separate 3-wire panel IO active through RGB initialization, matching the manufacturer factory source flow. The GPIO6 backlight now uses the manufacturer's RC-fast LEDC clock.
- Check and log boot-frame submission errors. The firmware logs the first USB Serial/JTAG data chunk before its existing accepted/rejected frame messages.
- Raised the idle backlight level from 22/255 to 120/255 after 60 seconds. The previous level could look like a black display; this is a suspected cause from source behavior, not a confirmed explanation of the previous screen report.
- Corrected the two Python test references to use the supplied, hash-listed `007-sent-frames.jsonl`. No `.benchmark-inputs/` file was changed.

## Reproduction commands

Run each command in the checkout root, separately:

```text
idf.py --version
idf.py set-target esp32s3
idf.py build
cmake -S tests/host -B build-host -G Ninja
cmake --build build-host
ctest --test-dir build-host --output-on-failure
python -m unittest discover -s tests -v
python tests/test_legacy_adapter.py
python tests/test_pc_pipeline.py
python tests/test_production_receiver.py
python -m py_compile pc/__init__.py pc/collector.py pc/gui.py pc/legacy_adapter.py pc/pipeline.py pc/sender.py pc/serial_sender.py tests/test_legacy_adapter.py tests/test_pc_pipeline.py tests/test_production_receiver.py
python scripts/validate-end-to-end-result.py --result results/20261006-codex-cli-gpt-6-luna-r03/end-to-end-result.json --manifest .benchmark-inputs/e2e-evaluation-manifest.json --evidence-root .
```

Observed here: ESP-IDF v5.3.2; firmware build passed; host CMake build passed; CTest passed 3/3; Python discovery passed 22/22; the individual Python files passed 2/2, 16/16, and 4/4; py_compile passed. The production C receiver test includes 29 wire/schema cases and accepts the exact supplied sequences 0 and 1. These are host results, not device acknowledgments or optical observations.

Built artifacts:

- `build/codex_desk_meter.bin`, SHA-256 `6298fbd63f86baf11b870bf7689852bae4bf85b5e05bd748c71939db339cf469` (316,848 bytes; 70% of the 1 MiB app partition remains free).
- `build/codex_desk_meter.elf`, SHA-256 `2174450821f9f9ab2bb09e85a556d11f09f3b173089e71320ad1c520799c2a69`.

## Error, stale, and recovery coverage

- Host Python tests check fixture-source preservation, the 299/300-second source-age boundary, provider errors, and recovery while retaining last-good values.
- Host-linked C tests call the production firmware parser/state module. They cover exact common seq0/seq1 frames, CRC and JSON/newline rejection, duplicate/out-of-order/wrap behavior, retained last-good payload, receive-stale at 300 seconds, and a newer-frame recovery.
- The idle-dim C test covers 59,999/60,000 ms, inactive-display behavior, and a monotonic-clock reversal.
- The frozen host write evidence is not a device receipt. The supplied prior capture has no accepted/rejected device marker, and the prior LCD report says black. No serial port, flash, reset, or `erase_flash` command was used for this run.

## Operator hardware procedure

The firmware build above is the artifact to test. Confirm COM3 is still the target board before using it; do not hold BOOT while resetting. These are operator commands only and were not run here:

```text
idf.py -p COM3 flash
idf.py -p COM3 monitor
```

After a normal boot, observe the LCD initialization result, the boot-screen submission, and `USB Serial/JTAG receiver ready`. Those log lines show software progress but do not prove the panel is readable. Keep the screen in view for at least 30 seconds and verify the landscape text is not clipped. Leave it idle past 60 seconds and verify it remains visibly lit; press BOOT and verify the higher brightness returns.

For a seq0/seq1 device test, use a new sender device alias and the operator-managed persistent sender state. Initialize that alias only after the board has booted and its volatile receiver is empty. Send each line as a separate command:

```text
python -m pc.serial_sender --port COM3 --device-alias r03-common-test --profile common --reference-time 2026-09-30T18:40:49Z --sent-at 2026-09-30T18:40:49Z --initialize-empty-receiver --capture-device-log-seconds 2
python -m pc.serial_sender --port COM3 --device-alias r03-common-test --profile common --reference-time 2026-09-30T18:40:49Z --sent-at 2026-09-30T18:40:54Z --capture-device-log-seconds 2
```

Use a different alias if `r03-common-test` already exists in the sender state. The first send should reserve sequence 0; the second should reserve sequence 1. In each command's `device_log_lines`, look for `USB Serial/JTAG receive path observed data` and `accepted cdm/1 frame sequence=0` or `sequence=1`. A `status=written` result alone is only a host write, not an ACK. Check the sender's raw frame log against `.benchmark-inputs/feedback-evidence/007-sent-frames.jsonl` if the bytes differ.

After sequence 1, observe the dashboard for `openai`, 5-hour remaining `58%`, weekly remaining `82%`, source kind `fixture`, preserved observation time, and `SOURCE-STALE`. Press BOOT once for the `codex-resets.com` global history and lookup time, again for diagnostics, then again to return to the dashboard. Verify the latest reset time and elapsed duration are shown without substituting the other global source.

For recovery, retain board power while disconnecting only the USB data link, if an already-confirmed safe independent supply is available. Check that last-good values remain and receive age advances; reconnect and send a newer frame, then confirm the accepted marker and refreshed dashboard. Do not assume battery or RTC backup power. Use RST only as a normal system reset, never while holding BOOT. A corrupted-frame test on the device and optical error/recovery observations remain unrun; their parser/state counterparts passed on the host.

## Remaining issues

- The changed firmware has not been flashed or observed on the board. Screen readability, accepted USB sequences, BOOT page changes, 30-second continuity, idle brightness visibility, and link recovery remain unverified.
- The black-screen source is still unconfirmed. The very low former idle value is now corrected, and the panel startup flow is closer to the fixed manufacturer source, but neither change has hardware evidence yet.
- `product_pass` is false. Operator visual, transport, and hardware results must be recorded against this exact artifact before any product-level pass is considered.
