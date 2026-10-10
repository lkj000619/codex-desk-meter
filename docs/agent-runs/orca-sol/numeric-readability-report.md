# LCD numeric readability correction

Run `run_c968c43361da`; Task `task_2ae3cb0fe949`; Dispatch `ctx_6fb4838726ea`; worker terminal `term_c11b9d1c-4c32-4a5c-ac0d-1c4814fd426d`.

## Cause and change

Production `number()` formatted every value with `%.7g`, and the bitmap `draw_text()` silently stopped after `width/(6*scale)` glyphs. At Usage TOTAL's 160-pixel width and scale 3, only eight glyphs fit; `314238800` became `3.142388e+08`, then was drawn as `3.142388`. Quota remaining also counted `USED / REM ` inside its 215-pixel field, leaving only six scale-2 glyphs for a value. This changed the apparent magnitude without changing the wire value.

`firmware/main/gui.c` now formats finite integral counts as complete decimal digits whenever they fit at bitmap scale 1, falling back to complete scientific notation for nonintegral or oversized values. The common formatter includes any prefix and `%` in the width check, chooses scale 3/2/1 per field, and substitutes `--` if a complete value cannot fit. Session rows, Usage TOTAL, and quota used/remaining all use that formatter. The B layout, colors, labels, raw/wire values, input+output total, and cached/reasoning subset rules are unchanged. No library or font dependency was added.

## Production pixel regression and host verification

The new `tests/firmware/test_gui.py` case sends six synthetic `cdm/1` frames through the existing production C receiver and renderer, then compares the exact 5×7 bitmap pixels in each numeric field at the allowed scales. It checks the current `314238800` total, large individual input/cache/source rows, the exact `9007199254740991` boundary, zero, null `--`, quota absolute fallback with its prefix, normal percentages, nonintegral scientific notation, a scientific percent with its `%`, unchanged neighboring labels, and blank right margins. It does not merely inspect a formatter string.

Before editing `gui.c`, the exact commands below built the old GUI and exited 1 on the new regression: `incomplete or overflowing rendered field: '314238800' at 643,86`. The other two GUI tests passed. After the fix and final test assertions, the same host build exited 0 and full firmware discovery exited 0 with **20/20 tests passed**:

```powershell
& 'tests/firmware/build-host.ps1'
& 'C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe' -B -X utf8 -m unittest discover -s tests/firmware -p 'test_*.py' -v
```

The final `git diff --check` for owned files exited 0. Generated PPMs and host binaries are ignored build output.

## Genuine ESP-IDF 5.3.2 build

The installed `idf.py --version` exited 0 and printed `ESP-IDF v5.3.2`. The checkout's Korean path cannot be compiled by the Windows GCC wrapper, so the approved ASCII scratch tree `C:/Espressif/tmp/cdm-sol-task_b1214421a314` was reused. All 15 firmware source/config files below were copied from **this worktree** to the same relative paths in staging, then SHA-256 compared both before and after the build. The stage is SDK scratch, not another product checkout. The build command exited 0; its full output is [numeric-readability-build-output.txt](numeric-readability-build-output.txt), SHA-256 `5BD87A30E3BC33BEC929457B5B8F02DF27EC90B2EB55FB40AE9FFBA16D759A3D`.

```powershell
$env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'
$env:IDF_TOOLS_PATH='C:/Espressif/user-tools'
. 'C:/Espressif/v5.3.2/esp-idf/export.ps1' | Out-Null
$env:TEMP='C:/Espressif/tmp'; $env:TMP='C:/Espressif/tmp'; $env:IDF_CCACHE_ENABLE='0'
Set-Location 'C:/Espressif/tmp/cdm-sol-task_b1214421a314'
& 'C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe' -B -X utf8 'C:/Espressif/v5.3.2/esp-idf/tools/idf.py' build *> 'C:/Users/이광진/orca/workspaces/codex-desk-meter/experiment-orca-harness-20261008/docs/agent-runs/orca-sol/numeric-readability-build-output.txt'
```

| Source/config relative to `firmware/` and staging | SHA-256 in both locations |
|---|---|
| `CMakeLists.txt` | `9E9534402359BAB131F26DCF0D246C9E23DDCD8699AA0E5E9DAB634E195020D7` |
| `sdkconfig.defaults` | `A232B9341461C95DDC0C18084A77459013B4C236DDCD6BEEE3108FF175B2FFB8` |
| `main/CMakeLists.txt` | `AF58E3AE2C42CC4E17CA4016464F48B31A90DBE7D21974C7A4740B3A78E14256` |
| `main/bsp.c` | `8A820F95AA58DB42D3C559901918419B8A11712E1D9F4A01F10CB085A890CEEE` |
| `main/bsp.h` | `B80339EF1F22CAC176D67F3073BD5D1D96E9275F9E1242FE1DF05C694786FAB2` |
| `main/cdm.c` | `33899E302733A685B78F7171B87CC7827D4E2B34D8ADE0A82F0290C6D16B9C1C` |
| `main/cdm.h` | `7C900F68AF9B75D85E8CD4E8E2D9E22F2E582BAB5DE2BF3A6B75F1F9D9ADA8C6` |
| `main/f9_temp.c` | `43F760751E10633A132249AB87AD86E63A11DAC97FE2D661B3ED1E31DD6E7812` |
| `main/f9_temp.h` | `645EDDA639A3876506FE9D00B1CD5DE82435BA14DE2B22C4C8C4D8255AAB3B92` |
| `main/gui.c` | `9F299CE8BE4B5E92272FE0CEF51BD404F7E4E2F9543C00BA306423A8B21FEFCF` |
| `main/gui.h` | `0781E73DDC3BADA616E334D0308EAB0477C76B33E7797E8D0688CA52A8494780` |
| `main/legacy.c` | `D652633AEDDA1F755DC7190A2104DB361B97EAFB144FC68922D6682D7B89479C` |
| `main/legacy.h` | `EFB69CA3856A50BCF423792805B19999D53C4D919B91DC93FC6DAF610E0ED441` |
| `main/main.c` | `4E1612983701B8951C06BA43A8A8132C725A30A5BAFDAAE1CEE00040CEE812E1` |
| `main/st7701_commands.inc` | `AF9C061384023D46BA85D9530A96630AE8680776D747ED73E2844DCCCF513B1C` |

All four new copies below are in ignored `firmware/.host-tools/numeric-readability-build/` and hash-match the staged build. The previous `lcd-flicker-build` and `active-usage-build` copies were preserved.

| Artifact | Flash offset | Bytes | SHA-256 |
|---|---:|---:|---|
| `bootloader.bin` | `0x0` | 21,504 | `F4C5160D0777EBDA11EDAC881853B211300323E5CF8F96EEEDA5314D731D02AB` |
| `partition-table.bin` | `0x8000` | 3,072 | `7F00B6C042A89B15B0CAC534F82ED988CAF29278FF5700B0C511EB1B5BB7C820` |
| `codex_desk_meter.bin` | `0x10000` | 308,992 | `953152B03EAC7E56CD696CCD37C9F1F182E5DC8C378854DE2296BB10121CD0E2` |
| `sdkconfig` | — | 70,020 | `46788F1C30A51868DA7C66C41DEF9045514FAAF393BC68EC0D6F05DF4DACA452` |

The app uses `0x4b700` bytes of a `0x100000` app partition, leaving `0xb4900` bytes (71%). `sdkconfig` selects ESP32-S3, 16 MB flash, Octal PSRAM at 80 MHz with malloc, and USB Serial/JTAG console; `CONFIG_LCD_RGB_ISR_IRAM_SAFE` remains unset. The structured source/artifact mapping and status are also in [numeric-readability-build-receipt.json](numeric-readability-build-receipt.json).

The coordinator alone owns COM/upload/reset, physical LCD observation, and real-account testing. These gates, including PC64 rerun and product PASS, remain `not_run`; the host pixel test and cross-build do not prove physical readability or flicker behavior.
