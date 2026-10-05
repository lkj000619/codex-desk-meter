# 자체 검증 기록

Run ID: `20261005-codex-cli-gpt-6-sol-r01`. 포트 open·flash·reset은 수행하지 않았다.

| 명령 | 결과 |
|---|---|
| `idf.py --version` | ESP-IDF v5.3.2 |
| `idf.py set-target esp32s3` | exit 0 |
| `idf.py build` | 최종 exit 0, app binary 0x4bab0 bytes, 1MiB app partition의 70% 여유 |
| `python -m py_compile pc/desk_meter.py` | exit 0 |
| `python -m unittest discover -s tests -v` | 5 tests, OK; fixture matrix, stale boundary, collector error/last-good/recovery, sender state |
| `cmake -S host -B build-host -G Ninja` | exit 0 |
| `cmake --build build-host` | exit 0; `main/receiver.c`, SDK cJSON 직접 compile/link |
| `ctest --test-dir build-host --output-on-failure` | 3/3 passed: receiver_state_and_crc, python_frame_to_firmware_receiver, idle_backlight_feature |

최초 firmware build의 `%X`/`uint32_t` format 오류는 `main/receiver.c`에서 수정했고 최종 재빌드가 성공했다. SDK Git dubious ownership 경고가 configuration 중 출력되었으나 build 종료 상태는 0이었다. host Python→C pipeline은 정상 fixture 프레임 7 수락, 재시작 후 1 거부, 손상 frame 거부, 8 복구를 확인했다. 이 기록은 후보 자체 시험이며 독립 운영자 판정은 아니다.

동결 후보 artifact SHA-256:

- `build/codex_desk_meter.bin`: `CEFA0A2BE742F4260FFCC8F3B83E2D35314E4CAF8FB2A915A10A9A552FDE6D78`
- `build/bootloader/bootloader.bin`: `E5AA9A3DEFC72C2AB8753CD463CAB09FF5AC3CEFA9E71F55E5722655492A9A09`
- `build/partition_table/partition-table.bin`: `7F00B6C042A89B15B0CAC534F82ED988CAF29278FF5700B0C511EB1B5BB7C820`
