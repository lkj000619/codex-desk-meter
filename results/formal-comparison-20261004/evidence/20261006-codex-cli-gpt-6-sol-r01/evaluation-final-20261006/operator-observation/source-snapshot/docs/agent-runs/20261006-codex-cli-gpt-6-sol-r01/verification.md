# Candidate verification

Run ID: `20261006-codex-cli-gpt-6-sol-r01`. Local source and test evidence only; no board was opened, reset, flashed, or monitored in this followup.

## Commands and observed results

Run each command separately from the checkout root:

```text
idf.py --version                         ESP-IDF v5.3.2
idf.py set-target esp32s3                completed
idf.py build                             completed; build/codex_desk_meter.bin 0x4bab0 bytes
python -m unittest discover -s tests -v 6 passed
python -m py_compile pc/desk_meter.py    completed
cmake -S host -B build-host -G Ninja     completed
cmake --build build-host                 completed
ctest --test-dir build-host --output-on-failure  3 passed
```

The linked C host receiver accepted the exact two seq 0/1 lines in `.benchmark-inputs/feedback-evidence/002-sent-frames.jsonl`, and a newly collected legacy fixture with five-hour 58% and weekly 82% remaining. The test also checks old sequence rejection, corrupt frame rejection, and recovery. This is production `main/receiver.c` linked with IDF cJSON, not a Python receiver. The PC unit tests cover fixture validation, stale threshold, last-good error and recovery, and sequence reservation. The local tests do not prove USB acceptance or LCD readability on the board.

## Operator physical procedure

Use the frozen `build/bootloader/bootloader.bin`, `build/partition_table/partition-table.bin`, and `build/codex_desk_meter.bin` as a single artifact set. Record their SHA-256 values before upload. On the operator's selected COM port, run the IDF flash procedure for these binaries with offsets `0x0`, `0x8000`, `0x10000`; do not erase the whole flash. Keep the sender state for that device alias across PC restarts. Only initialise it with `--receiver-empty` after confirming the receiver has no sequence. The sender command is `python pc/desk_meter.py --port COMx --alias meter --state sender-state.json --receiver-empty --fixture personal-usage.json --log sender-log.jsonl`; subsequent runs omit `--receiver-empty`. The sender takes the current UTC time, so use the reference UTC in a controlled test harness for exact fixture comparison.

Observe readable `USAGE DASHBOARD` with five-hour left 58% and weekly left 82%, source age marked stale, original observed time, and no fabricated token balance. Observe `GLOBAL RESET` showing `codex-resets.com`, its captured time, latest reset and elapsed time. Press BOOT briefly three times after normal boot and observe usage → global reset → status → usage, with response within 300 ms after debounce. Observe error and last-good preservation with malformed CRC, malformed schema, disconnected USB and recovery; capture raw bytes, device log, and screen for each. Check continuous display for at least 30 seconds, page clipping, dimming after 60 seconds of accepted-frame inactivity, restoration after a new accepted frame, and acceptance-to-screen latency under 2 seconds. These physical observations remain outstanding.

Known risk: direct RGB framebuffer drawing with bounce-buffer scanout is build-verified but has not been optically verified. The previous frozen artifact showed color bands; this followup changes the scanout path but does not claim that the issue is resolved on hardware. A prior 12.9-second video cannot establish 30-second continuity or BOOT response for this new binary.
