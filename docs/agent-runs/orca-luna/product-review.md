# Independent PC remediation and selected-B firmware review

Run `run_c968c43361da` · Task `task_4d49e747c570` · Dispatch `ctx_08869eb488a4` · worker `term_a4d53c0e-9eb2-4cae-b3ac-8a32bbb83956`.

## Verdict

**Failed independent review: three PC manual-refresh/deadline blockers remain.** Synthetic producer-to-C, C receiver/cache/GUI, selected-B, F9 and accepted build evidence pass within their host boundaries, and bounded serial drain failure plus ordinary successful drain now behave correctly. No `product_pass=true` is claimed; all test inputs were metadata-only synthetic data, with no account/session/auth files, COM device, reset, flash or other worktree/history used.

## Commands and results

| Command/evidence | Result | What it establishes |
|---|---|---|
| `python -B -X utf8 -m unittest discover -s tests/integration -p 'test_*.py' -v` | **FAIL, 26 tests: 23 passed, 3 failed** | PC production gather/normalization/raw canonical bytes into the linked production C receiver, receiver boundary/cache/session-selection tests, actual F9 module, queue timeout/success, AUTO→MANUAL fast path. Failures are the three PC event/deadline blockers below. |
| `python -B -X utf8 -m unittest discover -s tests/firmware -p 'test_*.py' -v` | **PASS, 18/18** | Production C receiver/cache/time and B renderer host tests; includes the distinct frozen `scripts/evaluate-product.py` legacy seam result **29/29**, not device acceptance. |
| `python -B -X utf8 -m unittest discover -s tests/pc -p 'test_*.py' -v` | **PASS, 57/57** | Current PC unit/remediation suite; does not override the failing production CLI + actual C integration tests. |
| `python -B -X utf8 -m unittest tests.integration.test_pc_producer_to_c.PCProducerToCTests.test_auto_rpc_remainder_manual_rpc_and_successful_serial_drains_share_five_second_budget -v` | **FAIL, 5.56–5.58s > 5s** | Actual bounded native RPC, production watch loop and `WindowsSerialSink` with successful fake queue drains. Each stage remains under its own timeout; full sequential request budget is exceeded. |
| `python -B -X utf8 -m unittest tests.integration.test_pc_producer_to_c.PCProducerToCTests.test_auto_rpc_then_post_request_manual_collection_write_and_drain_within_five_seconds -v` | **PASS** | Separate fast path: AUTO RPC remainder .7s + MANUAL RPC .2s + queue drain .03s; not worst-case deadline evidence. |
| Accepted ESP-IDF build logs and hashes | **PASS, not rebuilt** | The corrected selected-B build in `firmware/.host-tools/active-usage-build/` matches the accepted report: app `385130667AB15CA8DCC665E70FC06882B1E89535BDE8D84AF05FDC2B36C1EF72`, bootloader `F4C5160D0777EBDA11EDAC881853B211300323E5CF8F96EEEDA5314D731D02AB`, partition `7F00B6C042A89B15B0CAC534F82ED988CAF29278FF5700B0C511EB1B5BB7C820`, sdkconfig `46788F1C30A51868DA7C66C41DEF9045514FAAF393BC68EC0D6F05DF4DACA452`. `idf.py set-target esp32s3` and `idf.py build` succeeded with IDF v5.3.2 in the recorded ASCII staging checkout; see [Sol build report](../orca-sol/report.md) and [build log](../orca-sol/build-active-usage-output.txt). |

The production integration suite adds these pass checks: native nested token event/session identity; malformed, missing, boolean, negative, fractional, and invalid subset counts; original token timestamp despite later unrelated events; explicit multi-session selection; normalized versus provider totals; quota `rateLimitsByLimitId` windows, exact durations and unknown duration; account quota vs session scope; source stale ages 0/299/300 with fresh C receive age; future timestamp rejection; provider failure/last-good/recovery; global latest/source/captured time/last-known/default; RPC initialize → initialized → read order and bounded timeout cleanup; CLI reservation before write, wrap, corrupt/missing state, contention and refusal to auto-initialize; automatic/manual independence and reconnect throttling; and actual PC float + Unicode canonical bytes accepted by C.

### Reproducible PC blockers

1. `test_second_manual_request_during_manual_write_is_not_lost`: a second Enter arrives while the first MANUAL write is blocked; the shared Event is cleared by the first iteration and only one frame is sent. The request is discarded.
2. `test_pure_quota_request_after_collection_requires_fresh_native_acquisition`: a thin wrapper sets manual Event only after production `SharedCollectionState.collect_all` completes its real synthetic native quota acquisition. The watch loop clears the request using that already-acquired payload; collection count stays one and no second quota value/sequence is produced.
3. `test_auto_rpc_remainder_manual_rpc_and_successful_serial_drains_share_five_second_budget`: actual watch/RPC/serial path takes **5.56–5.58s** from manual request during AUTO initialize through successful MANUAL queue drain. AUTO initialize/read delays are .95s each, MANUAL initialize/read .9s each, and each of two successful serial drains .8s; each remains below the corresponding per-stage limit. The distinct fast-path test passes and is reported separately. The earlier 5.296s callback measurement was invalid for the deadline and remains only in historical checkpoint text.

The corrected synchronous `WindowsSerialSink.flush()` tests now pass both bounded queue timeout (returns `WRITE_IO_ERROR`, closes queue, reserved sequence remains consumed) and normal successful queue drain; this is no longer a blocker. The existing MANUAL event during AUTO RPC test also passes when quota is actually acquired after the request; it does not cover the separate post-acquisition event boundary above.

These findings were sent to the coordinator in escalation `msg_978c602977cc`; coordinator confirms the follow-up PC-only Task will be routed after this failed review settles. No PC or firmware source was edited.

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
| C8 | **BLOCKED / not_run** | Host auto/manual/reconnect basics pass, but manual Event requests can be lost and the measured worst-case sequential manual deadline is 5.56–5.58s. Bounded serial drain itself passes. BOOT/RST electrical behavior and ≤2s device redraw not_run. |
| I1 | **PASS (synthetic)** | Source/time/unit/error and privacy checks use only synthetic metadata. |
| I2 | **PASS (synthetic)** | Session, account quota, provider fixtures and global records stay separately scoped. |
| I3 | **BLOCKED / not_run** | Canonical raw PC bytes, C parser, sequence checks and bounded drain behavior pass; manual event loss/deadline remain blocked. Physical serial/receiver evidence not_run. |
| I4 | **PASS (host) / not_run device** | Actual C receiver/cache/time and renderer host tests pass; no board observation. |
| F1 | **PASS (host)** | Nested token/session metadata, explicit selection and provider error recovery pass; manual-write dispatch has the separate F6 blocker. |
| F2 | **PASS (host)** | Source total differs safely from normalized input+output; cached/reasoning subcounts and quota windows/scope verified. |
| F3 | **BLOCKED / not_run** | C wire acceptance/rejection and fake serial queue drain pass; PC manual dispatch can be lost or exceed the 5s budget. No device transport/ACK (none is defined) was tested. |
| F4 | **PASS (host) / not_run device** | C receiver/cache/session replacement/last-good tests pass. |
| F5 | **PASS (host) / not_run device** | Selected-B framebuffer/paging/three screens pass host pixels; panel timing/readability not_run. |
| F6 | **FAIL** | Manual request during an already-MANUAL write is discarded; pure-quota Event after response acquisition is also cleared without fresh collection; worst-case combined real-monotonic path measures 5.56–5.58s. The separate fast combined path passes. Reconnect attempts are ≤1/s and fake-port dispatch is ≤5s in the passing isolated test. |
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

Coordinator-owned: route/fix the three PC manual-event/deadline failures and rerun this same integration Task; actual COM send/reconnect and receiver observation; flash/upload and hardware C2/C8, BOOT/RST/GPIO0 electrical behavior, 30-second display, ≤2s accepted-frame redraw, physical clipping/readability, sensor plausibility, live-account and 24-hour stability. Until then the physical/live gates remain **not_run** and the product is not approved.


