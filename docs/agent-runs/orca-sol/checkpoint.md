# Firmware checkpoint

- Run: `run_c968c43361da`; Task: `task_b1214421a314`; Dispatch: `ctx_d5c857a3d228`; terminal: `term_e949afe5-d263-4f89-950b-3cca8cc9520f`.
- Phase: core C receiver/host seam verified; BSP source assembled; B final GUI gate pending.
- Modified owned files: `firmware/` CMake/config/main/BSP/CDM/F9 modules and command table, `tests/firmware/` host adapter/build/tests, this checkpoint. No COM or Git operation.
- Last verification: `tests/firmware/build-host.ps1` success; `python -B -X utf8 -m unittest discover -s tests/firmware -p 'test_*.py' -v` passed 7/7; frozen `scripts/evaluate-product.py` direct matrix passed 29/29.
- Actual PC synthetic wire interop: `experiments/orca-harness-20261008/operator/pc-fixture-frame-0.ndjson`, 3279 bytes, SHA256 `A077100EC2382F9F077644B998DB57928FE94E50F7622E2F456B5CF3ED77ED24`; production C receiver accepted sequence 0, four usage and one global. Coordinator status `msg_081d9df35a6c`.
- Next action: complete B GUI after independent PASS, then `idf.py set-target esp32s3` / `idf.py build`, review binary/hash and report. Physical/live/COM remain not_run.
- B first review FAIL retained; corrected design review still pending. Interface decision `msg_1a0585d74a22`/`msg_5d56c1876c49` adopted.
