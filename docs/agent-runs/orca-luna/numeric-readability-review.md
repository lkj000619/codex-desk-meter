# LCD numeric readability independent review

Run `run_c968c43361da`; Task `task_5b1435a8c3c1`; Dispatch `ctx_93b9c8f7189f`.

## Verdict

**Scoped host review: PASS. `product_pass=false`.** The accepted numeric GUI renders the complete tested counts, scientific notation, percentage suffixes, token/percent unit labels, null markers, and quota absolute fallback within their production pixel fields. The approved pre-numeric GUI reproduces the original defect: its 160-pixel TOTAL field contains only the first eight scale-3 glyphs, `3.142388`, from `3.142388e+08`.

The independent regression in `tests/integration/test_lcd_numeric_readability.py` compiles the production `cdm.c`, `legacy.c`, `gui.c`, and SDK cJSON with the pinned Zig host compiler into a private temporary directory. It feeds synthetic `cdm/1` frames to the real C receiver/renderer and compares complete PPM pixel regions against an independent 5×7 glyph oracle. It checks field gaps, right margins, row baselines, and quota/unit labels in addition to the number pixels; it does not infer success from formatted strings or nonempty regions.

Fixtures cover `314238800` from input `300000000` plus output `14238800`, exact `9007199254740991` integers, zero, unknown quota values (`--`), `42.125%` and `57.875%`, fractional `1.234568E+08`, scientific `1.25E-08%`, quota absolute fallback including its `USED / REM ` prefix, and the visible `token`/`percent` unit labels. Cached input `299000000` and reasoning output `14000000` remain visible as separate included-subset rows; source total `9007199254740991` remains distinct from normalized total `314238800`. Producer/selection integration below exercises the actual producer-to-C21 semantics and keeps account quota records separate from session telemetry.

## Host verification

All inputs were synthetic. These commands passed:

| Command | Result | Elapsed |
|---|---:|---:|
| `& 'C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe' -B -X utf8 -m unittest discover -s tests/integration -p 'test_lcd_numeric_readability.py' -v` | 2/2 | 18.150 s |
| `& 'C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe' -B -X utf8 -m unittest discover -s tests/firmware -p 'test_*.py' -v` | 20/20 | 5.003 s |
| `& 'C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe' -B -X utf8 -m unittest tests.integration.test_lcd_presentation -v` | 1/1 | 1.249 s |
| `& 'C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe' -B -X utf8 -m unittest tests.integration.test_cdm_session_selection tests.integration.test_pc_producer_to_c -v` | 20/20 | 16.032 s |

The firmware suite covers the existing GUI pixels, unknown/error/last-good behavior, source/receive age, usage selection, screen wrapping, and BSP ordering. The presentation integration exercises the accepted BSP handoff/error behavior. The selected-session and producer integration covers explicit selection and synthetic PC normalization/framing through the production C receiver. No product source was edited; the accepted BSP source remains byte-identical to its manifest entry.

The null display assertion uses quota `used_units`/`remaining_units`, which the C receiver accepts as null. A synthetic `available` session record with null channel counts is rejected by the current C21 validation as `SNAPSHOT_INVALID`, so that is not a valid renderable fixture; session rows are checked at zero and at large integer/fractional values.

## Accepted ESP-IDF build and hash audit

No genuine IDF rebuild was needed. The accepted receipt records ESP-IDF **5.3.2**, `buildExitCode: 0`, and the existing successful build log. I independently compared the receipt against the current checkout, its approved ASCII staging tree, and the exported build directory:

- **15/15** firmware source/config files match the receipt hash in both checkout and staging. `firmware/main/gui.c` is `9F299CE8BE4B5E92272FE0CEF51BD404F7E4E2F9543C00BA306423A8B21FEFCF`; BSP `main/bsp.c` is `8A820F95AA58DB42D3C559901918419B8A11712E1D9F4A01F10CB085A890CEEE`.
- **4/4** exported artifacts match both staging and receipt hashes: bootloader (21,504 bytes), partition table (3,072 bytes), app `codex_desk_meter.bin` (308,992 bytes; `953152B03EAC7E56CD696CCD37C9F1F182E5DC8C378854DE2296BB10121CD0E2`), and `sdkconfig` (70,020 bytes).
- `numeric-readability-build-output.txt` matches receipt SHA-256 `5BD87A30E3BC33BEC929457B5B8F02DF27EC90B2EB55FB40AE9FFBA16D759A3D` and contains `Project build complete`.

This verifies the accepted GUI source and genuine build lineage. It does not prove how the new binary reads on the physical panel.

## Remaining gates

The numeric candidate has not been flashed or observed on hardware in this task. Coordinator-owned COM3 upload/reset, physical numeric/unit/boundary inspection, BOOT and stale/error behavior observation, and a post-update flicker observation remain `not_run`. The prior user observation that flicker disappeared applies to the previously tested firmware and does not certify this unflashed numeric candidate. Live-account collection was not run.

Changed files: `tests/integration/test_lcd_numeric_readability.py`, this report, and the appended Luna checkpoint. No firmware, PC, frozen input, artifact, or Sol-owned file was changed.
