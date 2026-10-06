# Candidate validation record

Run: `20261006-codex-cli-gpt-6-luna-r02`  
Build environment: ESP-IDF v5.3.2, ESP32-S3 target.

- `idf.py set-target esp32s3`: pass.
- `idf.py build`: pass; application image generated at `build/codex_desk_meter.bin` (0x4d510 bytes), 70% app partition free.
- Candidate app image SHA-256: `8861E741F3ACDB3C511B399F2E92B96F70904F7000FAF01B43266016ECEA9FD5`.
- `cmake -S tests/host -B build-host -G Ninja`: pass.
- `cmake --build build-host`: pass; host executable links the production `components/meter_core/meter_core.c` receiver.
- `ctest --test-dir build-host --output-on-failure`: 3/3 pass (`meter_parser`, `meter_state`, `idle_dim`).
- `python -m unittest discover -s tests -v`: 22/22 pass.
- `python tests/test_pc_pipeline.py`: 16 pass.
- `python tests/test_legacy_adapter.py`: 2 pass.
- `python tests/test_production_receiver.py`: 4 test methods pass; includes exact common frame seq0/seq1 and the 29-case C wire/schema sweep.
- A sender host test confirms optional firmware log capture records diagnostics without reporting a protocol ACK.
- `python -m py_compile` on all six PC modules and three test modules: pass.

The production C host seam accepted the two supplied common frames and rejected malformed protocol/schema/integrity inputs. This record does not include a physical serial session, device acceptance observation, LCD photo/video, BOOT test, or 30-second optical check. No serial port, flash, reset, or erase command was run.
