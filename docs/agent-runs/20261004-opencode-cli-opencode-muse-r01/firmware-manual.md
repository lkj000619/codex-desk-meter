# Build, Test, and Observation Manual — 20261004-opencode-cli-opencode-muse-r01

## 1. Reproduce the build

Environment is operator-provisioned (ESP-IDF v5.3.2, host toolchain pinned in
`experiments/config/host-toolchain.json`). No installs, no network: the
firmware has no component-manager dependencies.

- `idf.py --version` -> `ESP-IDF v5.3.2` (observed).
- `idf.py set-target esp32s3` (workdir `firmware/`) -> configures, all five
  candidate components registered (`meter_core`, `bsp_lcd`, `bsp_input`,
  `gui`, `feature_auto_dim`).
- `idf.py build` (workdir `firmware/`) -> success. Artifacts:
  `firmware/build/cdm_meter.bin` (0x515b0 B, 68% of the 1 MB app partition
  free), `firmware/build/bootloader/bootloader.bin`.
- `idf.py size` -> image 333128 B; DIRAM 73643/341760 (21.5%); IRAM
  16383/16384 (99.99%, 1 B remains — builds cleanly, see §6); flash code
  187286 B, flash data 59528 B.
- Memory budget: 320x820x2 = 524800 B portrait staging + 820x320x2 logical
  canvas + 2x 64 KB line caches all live in 8 MB octal PSRAM
  (`sdkconfig.defaults`: `SPIRAM=y`, `MODE_OCT`, `80M`, 240 MHz CPU).

## 2. Reproduce the tests

- `python -m unittest discover -s tests -v` -> 25 tests OK (collector matrix,
  sender framing/persistence, legacy seam freshness/recovery, e2e dry-run,
  GUI budget). Python-side proof only; not claimed as firmware proof.
- `cmake -S tests -B build-host -G Ninja` -> configures with the pinned
  host compiler.
- `cmake --build build-host` -> builds the production C modules
  (`meter_crc32/parser/state/validate`, `gui_format`, `feature_auto_dim`,
  `bsp_input` with host-only IDF-header stubs) plus six harnesses.
- `ctest --test-dir build-host --output-on-failure` -> 6/6 pass:
  parser (canonical/CRC/version/newline/UTF-8/size/sequence incl. wrap),
  state (accept/dup/reverse/half-range, last-good preserved, 0/299/300 s
  receive-age stale, no seq reset on stale/disconnect, wrap 2^32-1->0),
  validate (percent/absolute/reset-class/source-age), GUI regression
  (verbatim provenance, default screens, 64-char landscape budget), feature
  autodim, input debounce (50 ms).
- Legacy seam: `tests/test_legacy_adapter.py` drives
  `pc_tools/legacy_adapter.py` through the `evaluate-product.py` event shapes
  (personal-usage / codex-reset-forecast / codex-resets-history x
  freshness/invalid/dns/tls/http_500). The operator runs
  `scripts/evaluate-product.py` with its own adapter-config for the verdict;
  this run does not pre-claim it.

## 3. Error / stale / recovery coverage (host-proven, operator-observed)

| Case | Host proof | Operator panel check |
|---|---|---|
| Bad CRC / schema / version / CRLF / pretty / truncated / oversized / bad UTF-8 | `test_meter_parser` rejections | send corrupt line -> STATUS shows code, last-good kept |
| Duplicate / reverse / half-range seq | `test_meter_state` | resend seq -> rejected, screen unchanged |
| Wrap 4294967295 -> 0 | `test_meter_state` | procedure doc only (needs NVS cycling) |
| Sender restart 7 -> 1 rejected -> persisted 8 accepted | `test_sender` | §4 procedure |
| Receive-age 0/299/300 s stale | `test_meter_state` | wait 5 min after last frame -> STALE:YES, dim |
| Source-age 0/299/300 s | `test_meter_validate` | PC-side; panel shows receive-age + verbatim stamps |
| USB disconnect | logic (`s_link_ok`, dim) | unplug 5 s -> LINK:USB-LOST + dim; replug+resend -> OK |
| Empty/old input, DNS/TLS/HTTP/JSON | legacy adapter tests | PC collector logs failure, panel keeps last-good |
| BOOT cycles 3 screens <= 300 ms | `test_input_debounce` + firmware poll | press BOOT -> DASHBOARD/GLOBAL/STATUS rotate |
| RST is system reset only | no app code path | press RST -> reboot to BOOT default screen |

## 4. Physical upload / observation procedure (operator runs; candidate did not)

1. Freeze: `firmware/build/cdm_meter.bin`, `bootloader.bin`,
   `partition-table.bin` as built above (no `erase_flash` by candidate).
2. Console is on UART0; USB-SERIAL-JTAG carries only `cdm/1` frames. Connect
   both USB (frames) and UART0 (logs) or observe the LCD only.
3. `idf.py -p <UART-COM> flash` (operator port), reset, expect BOOT default
   screen ("awaiting PC frame"), backlight on, 30+ min soak for C2.
4. PC: `pc_tools/collector.py` (default registry, `--reference-time` fixed)
   writes payload; `pc_tools/sender.py --init-alias --receiver-empty-ack`
   once, then `--send --port <USB-COM>` (115200 8N1). Reopen attempts <= 1 Hz;
   new snapshot <= 5 s after port available; LCD reflects accepted frame
   <= 2 s (1 Hz GUI poll).
5. Manual refresh = rerun the PC collector+sender commands (BOUND: BOOT never
   triggers a PC fetch). Auto cadence <= 60 s is a PC scheduler concern.
6. Evidence to capture: raw `.bin` frame bytes, sender report JSON, UART log,
   LCD photos/video of the three screens, disconnect/replug sequence, 30 s
   lit-soak clip.

## 5. Time-base mapping used for the verdict

Fixture `reference_time` (UTC) <-> firmware monotonic anchor: the receiver
stores `sent_at` verbatim and stamps `received_monotonic_s` at accept.
Stale-on-panel is receive-age only (`now_mono - received_mono >= 300`).
Source-age (`observed_at` vs wall clock) is shown as verbatim stamps with age
`unknown`, because the firmware has no wall clock (no Wi-Fi/NTP; RTC cell
unconfirmed). PC-side validators apply the UTC reference checks.

## 6. Remaining issues (honest, not blocking host verdicts)

1. IRAM 16383/16384 B (1 B slack) — build succeeds, but any IDF growth needs
   `CONFIG_BT_ENABLED=n` or similar trimming; flagged for the next iteration.
2. Landscape is a software transpose over proven portrait timings; MADCTL
   stays at the vendor value. Orientation must be confirmed on the panel
   photo (operator C2/G1).
3. `usb_serial_jtag` baud is host-side (USB function is rate-independent);
   documented, not device-configurable.
4. Reboot loses the last-good payload (NVS keeps only the sequence);
   documented behavior, not last-good loss within a boot.
5. `product_pass=false` in this run: operator hardware evidence (C2, G1-G6,
   physical disconnect/replug) is `blocked`/`not_run` until the procedure in
   §4 is executed against these frozen artifacts.
