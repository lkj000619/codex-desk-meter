# Independent PC remediation and selected-B firmware review

Run `run_c968c43361da` · Task `task_4d49e747c570` · Dispatch `ctx_125c9c02c0ed` · worker `term_a4d53c0e-9eb2-4cae-b3ac-8a32bbb83956`.

## Verdict

**Failed independent review: PC manual dispatch/serial drain blockers remain.** Synthetic producer-to-C, C receiver/cache/GUI, selected-B, F9 and accepted build evidence pass within their host boundaries. No `product_pass=true` is claimed. All test inputs were metadata-only synthetic data; no account/session/auth files, COM device, reset, flash or other worktree/history was used.

## Commands and results

| Command/evidence | Result | What it establishes |
|---|---|---|
| `python -B -X utf8 -m unittest discover -s tests/integration -p 'test_*.py' -v` | **FAIL, 22 tests: 19 passed, 3 failed** | PC production gather/normalization/raw canonical bytes into the linked production C receiver, receiver boundary/cache/session-selection tests, and actual F9 module. Failures are the three PC blockers below. |
| `python -B -X utf8 -m unittest discover -s tests/firmware -p 'test_*.py' -v` | **PASS, 18/18** | Production C receiver/cache/time and B renderer host tests; includes the distinct frozen `scripts/evaluate-product.py` legacy seam result **29/29**, not device acceptance. |
| `python -B -X utf8 -m unittest discover -s tests/pc -p 'test_*.py' -v` | **PASS, 53/53** | PC unit/remediation tests; does not override the failing production CLI + actual C integration tests. |
| `python -B -X utf8 -m unittest tests.integration.test_pc_producer_to_c.PCProducerToCTests.test_manual_rpc_write_and_real_wrapper_drain_share_five_second_budget -v` | **FAIL** | Actual `run_watch_loop` → bounded native RPC → production `WindowsSerialSink` with fake pyserial `out_waiting`. Manual dispatch returns within 5s but reports host success while bytes remain queued; it neither completes drain nor reports a bounded failure/closed sink. |
| Accepted ESP-IDF build logs and hashes | **PASS, not rebuilt** | The corrected selected-B build in `firmware/.host-tools/active-usage-build/` matches the accepted report: app `385130667AB15CA8DCC665E70FC06882B1E89535BDE8D84AF05FDC2B36C1EF72`, bootloader `F4C5160D0777EBDA11EDAC881853B211300323E5CF8F96EEEDA5314D731D02AB`, partition `7F00B6C042A89B15B0CAC534F82ED988CAF29278FF5700B0C511EB1B5BB7C820`, sdkconfig `46788F1C30A51868DA7C66C41DEF9045514FAAF393BC68EC0D6F05DF4DACA452`. `idf.py set-target esp32s3` and `idf.py build` succeeded with IDF v5.3.2 in the recorded ASCII staging checkout; see [Sol build report](../orca-sol/report.md) and [build log](../orca-sol/build-active-usage-output.txt). |

The production integration suite adds these pass checks: native nested token event/session identity; malformed, missing, boolean, negative, fractional, and invalid subset counts; original token timestamp despite later unrelated events; explicit multi-session selection; normalized versus provider totals; quota `rateLimitsByLimitId` windows, exact durations and unknown duration; account quota vs session scope; source stale ages 0/299/300 with fresh C receive age; future timestamp rejection; provider failure/last-good/recovery; global latest/source/captured time/last-known/default; RPC initialize → initialized → read order and bounded timeout cleanup; CLI reservation before write, wrap, corrupt/missing state, contention and refusal to auto-initialize; automatic/manual independence and reconnect throttling; and actual PC float + Unicode canonical bytes accepted by C.

### Reproducible PC blockers

1. `test_production_windows_serial_flush_is_bounded_and_consumes_reserved_sequence`: fake serial holds queued bytes past `write_timeout`; `cmd_send` returns **0** while the production flush worker remains blocked. The reserved sequence is consumed, but the host reports success without completed drain. The wrapper also suppresses flush exceptions.
2. `test_watch_manual_event_during_write_collects_new_session_before_clearing`: a manual event arrives after the loop collected its snapshot and while it is writing. The loop clears that event after transmitting the pre-request snapshot; there is one frame and no post-request collection/sequence.
3. `test_manual_rpc_write_and_real_wrapper_drain_share_five_second_budget`: the realistic pyserial `out_waiting` probe confirms manual request-to-dispatch stays within 5s, but the wrapper reports host success while the queue remains pending. This is not completed drain evidence and is not an acceptable bounded failure. The earlier 5.296s run only timed an out-of-band fake sleep and is retained in the checkpoint as false-success evidence, not a valid deadline measurement.

These findings were sent to the coordinator in escalation `msg_653f77061153`; the coordinator accepted them and will route the PC fix after this failed review settles. No PC or firmware source was edited.

## C / I / F acceptance

| ID | Status | Evidence / remaining boundary |
|---|---|---|
| C1 | **PASS (accepted build)** | Corrected 853ddf7 report/log and active-usage artifact hashes independently matched. No repeat build. |
| C2 | **not_run** | No physical panel 30-second run, readability/clipping or orientation check. |
| C3 | **PASS (host)** | Synthetic PC quota/session production output reaches C; B host renderer covers dynamic windows and pages. Physical display remains not_run. |
| C4 | **PASS (host)** | PC global reset source/latest/captured record reaches C; host renderer exercises elapsed time. Actual source/live display remains not_run. |
| C5 | **PASS (host)** | Last-known and empty/default reset paths covered in C/renderer tests. Physical fallback not_run. |
| C6 | **PASS (host)** | Source and captured time survive PC normalization and C cache. Physical label/readability not_run. |
| C7 | **PASS (host)** | C malformed/stale/error handling preserves last-good and recovers; PC per-source failure/recovery passes. Network/device endurance not_run. |
| C8 | **BLOCKED / not_run** | Host auto/manual/reconnect basics pass, but manual-during-write fails and the realistic fake `out_waiting` path reports success while bytes remain queued; bounded complete-or-fail behavior is therefore blocked. BOOT/RST electrical behavior and ≤2s device redraw not_run. |
| I1 | **PASS (synthetic)** | Source/time/unit/error and privacy checks use only synthetic metadata. |
| I2 | **PASS (synthetic)** | Session, account quota, provider fixtures and global records stay separately scoped. |
| I3 | **BLOCKED / not_run** | Canonical raw PC bytes, C parser and sequence checks pass; production flush falsely reports success. Physical serial/receiver evidence not_run. |
| I4 | **PASS (host) / not_run device** | Actual C receiver/cache/time and renderer host tests pass; no board observation. |
| F1 | **PASS (host)** | Nested token/session metadata, explicit selection and provider error recovery pass; manual-write dispatch has the separate F6 blocker. |
| F2 | **PASS (host)** | Source total differs safely from normalized input+output; cached/reasoning subcounts and quota windows/scope verified. |
| F3 | **BLOCKED / not_run** | C wire acceptance and rejection pass; PC serial drain fails. No device transport/ACK (none is defined) was tested. |
| F4 | **PASS (host) / not_run device** | C receiver/cache/session replacement/last-good tests pass. |
| F5 | **PASS (host) / not_run device** | Selected-B framebuffer/paging/three screens pass host pixels; panel timing/readability not_run. |
| F6 | **FAIL** | Manual arriving during an already-collected write is discarded; exact RPC-to-drain measurement is 5.296s. Reconnect attempts are ≤1/s and fake-port dispatch is ≤5s in the passing isolated test. |
| F7 | **PASS (host)** | Global latest, last-known/captured source and empty/default paths are covered. Live source accuracy not_run. |
| F8 | **PASS (build/host) / not_run device** | Accepted IDF build/hash and host suite pass; no on-device timing, power, or 30-second evidence. |
| F9 | **PASS (host) / not_run device** | Exactly three candidates are documented; only internal chip temperature is selected and isolated in `f9_temp.c`. Four tests compile/execute the real module with a fake IDF sensor API for install/enable/read failures and success without a substituted constant. Real sensor plausibility remains not_run. |

## Live L1–L8

| ID | Status | Evidence / remaining boundary |
|---|---|---|
| L1 session selection | **PASS (host)** | Explicit PC selection plus A→B replacement and B-only framebuffer against production C. |
| L2 cumulative token events | **PASS (host)** | Native nested event replaces cumulative counts; no double-sum; unrelated later events do not replace the token timestamp. |
| L3 token channels | **PASS (host)** | Input/output/cache/reasoning/source/normalized channels preserve units and subset meaning through C. |
| L4 account quota scope | **PASS (host)** | Account profile quota remains separate from session telemetry. |
| L5 variable windows | **PASS (host)** | `rateLimitsByLimitId`, exact duration IDs/labels and unknown duration stay distinct; renderer pages all windows. |
| L6 total/subset semantics | **PASS (host)** | Original total and input+output differ in the fixture; cache/reasoning remain included subsets. |
| L7 timestamp and age | **PASS (host)** | Original event time, future rejection, source ages 0/299/300 and independent fresh receive age are covered. |
| L8 privacy | **PASS for this review** | All local test data is synthetic metadata; no real account/session/auth data was read or emitted. |

## Prior actual findings retained and resolution

- The first selected-B firmware baseline had an actual production-C A→B defect: active usage retained A and B and its framebuffer differed from B-only. Accepted correction 853ddf7 builds the complete active list atomically; `test_cdm_session_selection.py` passes against linked production C and compares actual rendered pixels.
- The first browser B review found cache loss after Normal→Unknown/Waiting→Error or Disconnected. The dated corrected-B rerun records those paths, empty-cache behavior, 299/300/301 stale boundaries, paging, BOOT event and 820×320 geometry as passing. See [B review](gui-b-review.md); physical readability remains not_run.
- PC remediation previously fixed token stamping, cold global omission, multi-entry provider retention, session-path cache isolation, and bounded RPC/scheduler cases; current producer-to-C integration reproduces their synthetic semantics. The two serial/manual races and the combined deadline miss are new independent blockers and supersede no historical evidence.

## Remaining gates

Coordinator-owned: route/fix the three PC deadline failures and rerun this same integration Task; actual COM send/reconnect and receiver observation; flash/upload and hardware C2/C8, BOOT/RST/GPIO0 electrical behavior, 30-second display, ≤2s accepted-frame redraw, physical clipping/readability, sensor plausibility, live-account and 24-hour stability. Until then the physical/live gates remain **not_run** and the product is not approved.


