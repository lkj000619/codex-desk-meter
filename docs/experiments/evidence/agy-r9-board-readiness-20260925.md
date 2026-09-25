# AGY R9 board readiness — 2026-09-25 KST

| Pilot-entry check | Observation | Status |
|---|---|---|
| COM3 device | Windows `Win32_SerialPort` showed USB serial COM3 `OK`; `esptool chip_id` opened it and returned ESP32-S3 rev v0.2 with 8MiB PSRAM | pass at observation time |
| Exclusive access | The full 16MiB `read_flash` held COM3 for 386.6 seconds and exited 0 | pass at observation time; repeat immediately before pilot/flash |
| Current-state backup | `C:\Espressif\vendor\waveshare-esp32-s3-lcd-3.16\backup\pilot-preflight-read-20260925.bin`, 16,777,216 bytes, SHA-256 `ba234a8044e5174ef0275f99b89573a78a6ce62d70b62196720b0ad83d8e532b` | pass; preserve outside Git |
| Historical factory backup | `factory-flash-20260911-005604.bin`, 16,777,216 bytes, SHA-256 `aa51ba15b975ec2e564506e609729f36d85da23d8892023396a700846955a1e6` | preserved; different from current flash |
| Board model | Prior bring-up documentation identifies Waveshare ESP32-S3-LCD-3.16; current `chip_id` proves the SoC. The user visually confirmed in this session that the connected COM3 device is that board. | pass for pilot entry |
| Flash/erase rule | No `write_flash`, `flash`, or `erase_flash` command was used here; agent prompt forbids direct serial/flash access | pass for preparation |
| Candidate firmware | Agent has not run, so no candidate firmware or flash hash exists | post-agent, pre-flash review |

The first pilot can start after time-sensitive COM3 exclusivity is rechecked at
the actual run time. Before any later hardware
flash, verify the candidate artifact and hash against the frozen agent result,
retain both recovery images, and follow the no-erase rule. A successful backup
read is not a product or display test.
