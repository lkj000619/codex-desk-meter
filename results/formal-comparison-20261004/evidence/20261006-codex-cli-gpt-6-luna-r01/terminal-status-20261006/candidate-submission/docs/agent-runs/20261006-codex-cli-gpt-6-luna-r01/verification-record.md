# Verification and handoff — 20261006-codex-cli-gpt-6-luna-r01

## Scope and identity

- Run: `20261006-codex-cli-gpt-6-luna-r01`
- Experiment: `version-2-end-to-end-v1`
- Baseline ref / ID: `comparison-baseline-20261004`
- Baseline commit: `272875140d1998d458e26fdb2f6deab5e5d8f7b5`
- Fixed evaluation-manifest reference: `.benchmark-inputs/e2e-evaluation-manifest.json`
- Result: `results/20261006-codex-cli-gpt-6-luna-r01/end-to-end-result.json`

Only the fixture pipeline is used. No provider account, credential, network service, COM port, board flash, reset, or flash erase was used. The host tests compile and call the production C receiver/parser module; their success does not show that USB reached the board or that the LCD worked.

Execution note: one read-only PowerShell source-inspection call combined two `Get-Content` commands with `;`, contrary to the requested one-command-per-call rule. It made no file changes. Build, test, and validation commands were invoked separately.

## Reproduction commands and outcomes

Run each command separately from the checkout root with the prepared ESP-IDF v5.3.2 environment.

| Command | Outcome |
|---|---|
| `idf.py --version` | `ESP-IDF v5.3.2` |
| `idf.py -B build-idf set-target esp32s3` | Passed; target configured in `build-idf`. The no-`-B` invocation initially encountered an incomplete pre-existing build directory, so the isolated build directory is used for repeatability. |
| `idf.py -B build-idf build` | Passed; generated `build-idf/codex_desk_meter.bin` (0x4d370 bytes, SHA-256 `3AF7FD933B743EA7B16BA02627617E3ADB3BE0D5273EB9DEB184F1BE9C9D51D6`). The smallest app partition is 0x100000 bytes, with 70% reported free. |
| `python -m unittest discover -s tests -v` | Passed, 11 tests. |
| `python tests/test_pc_pipeline.py` | Passed, 11 tests. The test module adds the checkout root to `sys.path` so the requested direct invocation works. |
| `python -m py_compile pc/pipeline.py pc/collector.py pc/sender.py pc/serial_sender.py pc/gui.py tests/test_pc_pipeline.py` | Passed. |
| `cmake -S tests/host -B build-host -G Ninja` | Passed. |
| `cmake --build build-host` | Passed; linked host programs from the actual `components/meter_core/meter_core.c` plus the isolated idle policy component. |
| `ctest --test-dir build-host --output-on-failure` | Passed, 3/3: `meter_parser`, `meter_state`, `idle_dim`. |

The project disables the ESP-IDF component manager and compiles the hash-checked manufacturer ST7701, three-wire panel-I/O, and I/O-expander sources through local wrapper components. The SDK emitted Git “dubious ownership” metadata warnings while configuring; compilation, linking, image generation, and partition-size checks still completed successfully. No global Git trust setting was changed.

## Error, stale, and recovery coverage

- The C parser test accepts a valid `cdm/1` frame, rejects a changed payload with `CRC_MISMATCH`, rejects CRLF, and preserves the last-good sequence and exact frame after rejection. It also exercises wrap from `UINT32_MAX` to zero, duplicate, reverse, and half-range sequence comparisons, and source-age boundary behavior.
- The C state test observes receive age as fresh at 299,999 ms and stale at 300,000 ms. It rejects sequence 1 after sequence 7 while retaining sequence 7 and stale state, then accepts sequence 8 and clears the error/stale state. This calls the firmware receiver module linked into the host executable; it is not a physical USB test.
- Python tests cover source staleness at 299/300 seconds, isolated per-adapter failure with last-good preservation, normalization of global-reset aliases without merging sources, corrupt sender state, explicit empty-receiver initialization, durable sequence advancement, and sequence consumption after a failed write. Host write receipts explicitly report that they are not device ACKs.
- An old source remains source-stale when a newer frame arrives. Receiver freshness and source freshness are shown separately on the LCD; a transport reconnect must not make old source data appear fresh.

## Operator board upload and observation procedure

These are handoff commands only; they were not run in this session. Replace `COMx` with the operator-selected port. Close any other serial monitor before opening the port.

1. Connect the board and use normal boot (do not hold BOOT while testing app behavior). Upload the frozen image:

   `idf.py -B build-idf -p COMx flash`

   If the board does not enter download mode automatically, use the documented BOOT + RST bootloader-entry sequence for flashing, release BOOT, and repeat the flash command. Then start a separate monitor:

   `idf.py -B build-idf -p COMx monitor`

2. In another terminal, install the product's optional serial dependency if it is not already present:

   `python -m pip install -r requirements-product.txt`

   Start the PC fixture GUI:

   `python -m pc.gui`

3. Select the data COM port and alias `waveshare-meter-1`. Keep automatic send disabled for the first run. The GUI only reads the local fixture registry and does not contact accounts or providers. Check “Initialize only after confirming receiver is empty” only for a new/known-empty receiver; the first send consumes sequence 1. Press “Refresh and send.” Later sends reserve durable, increasing sequences. A host “written” receipt is not a board ACK.

4. Within 5 seconds the monitor should show `USB Serial/JTAG receiver ready` and an accepted frame sequence. Within 2 seconds of acceptance the LCD should show provider/window rows, values with their source units, original observation/reset times, and the separate `codex-resets.com` global reset page. With no reset history, it should show the default/no-history state. Leave it powered for at least 30 seconds and check the full landscape layout. Press BOOT briefly to cycle Dashboard → Global reset → Status; verify it is an app input and not a reset/download action.

5. To observe receiver staleness, send a frame and leave the board powered without sending for at least 300 seconds. Status should mark receive age stale while retaining the last-good frame. Send the next frame using the same sender state and alias; the receiver should accept the next sequence and clear receive-stale. Any old fixture source must remain source-stale. For a full source-freshness recovery observation, use an operator-created synthetic test capture with truthful capture timestamps in a separate fixture file; do not edit supplied fixtures or relabel an old observation time.

6. For error recovery, retain the monitor and LCD status view. A malformed frame should be logged as rejected and leave the displayed last-good sequence/data intact. A subsequent valid frame with the next reserved sequence should be accepted and clear the transport error. Preserve the frozen binary, monitor log, raw sender log, and LCD photos/video as operator evidence. Do not infer device acceptance from the PC serial write receipt.

## Remaining issues and unmeasured items

- USB receive, normal boot, the LCD panel, BOOT multiplexing, the 30-second display hold, PWM brightness, and physical recovery were not observed. C2 and hardware/transport results remain `not_run`; LCD-dependent results are partial. `product_pass` is false.
- The ST7701 init sequence and RGB pins/timing follow the supplied manufacturer sources. The landscape memory-access command (`0x36 = 0x20`) is a candidate setting and still needs physical orientation/color-order validation.
- Text drawing uses a small ASCII glyph set; non-ASCII provider or window labels are rendered as fallback glyphs, and long labels may be truncated. These limitations need visual review at the actual 820×320 size.
- The optional dim level and LEDC polarity are based on the documented active-low board output but need a physical readability/flicker/power check.
- GUI rubric scores, run wall time, agent token counts, and independent operator evaluation were not supplied by the runtime and remain null/unscored.
