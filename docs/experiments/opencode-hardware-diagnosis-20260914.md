# OpenCode pilot hardware observation and diagnosis status — 2026-09-14

## Scope and provenance

Run: `20260914-opencode-cli-muse-spark-1-3-contributor-free-r02`.
This is an operator follow-up to the manual pilot, not a formal benchmark.
The user authorized uploading its existing firmware to COM3 and subsequently
requested recording the situation and diagnosing it. No implementation fix,
rebuild, additional flash, git stage/commit/tag/push or main merge was performed
as part of this diagnostic follow-up. Original candidate output is preserved.

## Recorded observations

- ESP32-S3 on COM3 was identified; existing firmware image SHA-256:
  `a54604d171a44a3de60953a12719c4d7bf39ac7f70102d59e15125d784051ce6`.
- Prior operator upload: esptool 4.12.0, 460800 baud, DIO/16MB/80MHz,
  bootloader at `0x0`, partition table at `0x8000`, application at `0x10000`.
  Exit 0; all three on-device hash verifications passed. Only the image
  sectors were erased, not a whole-chip erase. Upload reset the board.
- Boot log: `panel ready (320x820 RGB565, canvas in PSRAM)`.
- Boot self-test: `FAIL frame_crc_reject`; final total 1 failure.
  Compiling the firmware successfully did not establish device correctness.
- Synthetic serial test: a 1424-byte personal frame was sent, and the device
  reported `line overlong/unterminated (64 bytes); draining`, followed by
  `reject FRAME_TRUNCATED (overlong line drained)`. The configured maximum
  reported at boot was 65536 bytes. A preceding 3543-byte frame send occurred
  before the operator log-reader command failed with a quoting SyntaxError
  (exit 1); that command cannot establish an acceptance result.
- Corrected serial send/read command exited 0; subsequent reset/12-second
  boot-log capture exited 0. Both closed COM3. Command success is not frame
  acceptance or a hardware product pass.
- User-supplied photo visibly shows `CODEX DESK METER`, `GLOBAL RESETS`,
  `WAITING FOR FRAME`, `RX 0 ERR 0`, and `LIGHT:DIM`. The photograph is an
  actual LCD-output observation, not a simulator result. RX/ERR zero reflects
  the pictured state after reset and does not negate the earlier reject log.
- User reports: holding BOOT makes the screen visible; briefly pressing BOOT
  makes the screen black. This is a reported behavior, not yet a timed,
  instrumented reproduction. The photo alone does not prove which action
  changed the screen or whether black means backlight-off or black pixels.

Photo provenance: attachment supplied in this conversation. The temporary
attachment has not been copied into the repository; no absolute user path or
device MAC address is included here. The source conversation retains the photo.

## Diagnosis status and evidence limits

Confirmed failures: a device self-test fails and an actual serial input is
rejected. LCD text rendering is confirmed by the photo. The complete data-to-LCD
pipeline and BOOT behavior are **not verified**. None of these observations
establish I3/I4 pass or `product_pass=true`.

The `diagnosing-bugs` skill requires an already-executed red-capable reproduction
of the exact symptom before root-cause hypotheses. There is currently no
agent-runnable, deterministic reproduction of the reported short/long BOOT
screen-black behavior: a physical press and visual observation are required.
Accordingly the button root cause is **unresolved**, not guessed from code.
The earlier panel-ready log proves initialization returned successfully, not
continuous correct refresh, brightness or input operation. Earlier assistant
claims that the button/backlight was definitely faulty were stronger than the
available evidence; this record corrects that certainty.

Diagnosis performed so far: correlated user report/photo with the existing
boot/serial failure signals and separated display initialization, visible output,
frame acceptance and button behavior. No new hardware actions were taken during
this recording turn. Reading nearby source to invent a likely cause would not
satisfy the reproduction requirement, so deeper diagnosis is paused.

## Next diagnostic step / remaining gates

1. Capture a continuous video of the LCD and button: initial state, a short
   press, release, a long press (at least 1.5 seconds), release; include timing
   and whether the panel remains illuminated while black. Pair with a bounded
   COM3 log capture so screen-change and backlight messages can be correlated.
2. Build a reproducible pass/fail observation for that exact symptom before
   ranking and testing causes. If existing logs cannot distinguish it, obtain
   approval for temporary diagnostic instrumentation, keeping original output.
3. Diagnose the independent serial truncation and CRC self-test failure using
   their own minimal reproductions; neither is proven to cause the button symptom.
4. Any firmware fix/rebuild/reflash is a separate action requiring user direction.
   Formal frozen-input/manifest validation and formal benchmark authorization
   remain separate; this hardware follow-up does not grant those gates.

The original pilot result remains `product_pass=false`; its placeholder
`baseline.commit` still fails result schema validation (exit 1). No identity or
evidence field was silently replaced to make validation pass.
