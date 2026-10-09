# Independent PC remediation and selected-B firmware review

## Current retry Dispatch result — 2026-10-10

Run `run_c968c43361da` · Task `task_4d49e747c570` · Dispatch `ctx_6b00e6339d06` · worker `term_b6cd0335-ea67-4926-8229-b50602b3fb97`.

**Host review passes on the accepted source. This is not whole-product approval.** The current production PC → canonical `cdm/1` bytes → linked product C receiver path, CLI/serial seam, active-session replacement, selected-B C renderer, F9 module, and accepted build evidence passed. All test data was synthetic metadata; no real account/session/auth data, COM port, reset, flash, Git history, or other worktree was accessed.

| Verification command/evidence | Result |
|---|---|
| `python -B -X utf8 -m unittest discover -s tests/integration -p 'test_*.py' -v` | **PASS 27/27**; actual production collector/normalizer/frame into `tests/firmware/.build/cdm-host.exe`, receiver boundaries/cache/time, A→B selection pixels, CLI refresh/reconnect/sequence, and real F9 module. |
| `python -B -X utf8 -m unittest discover -s tests/pc -p 'test_*.py' -v` | **PASS 64/64**; production PC unit/remediation suite. |
| `python -B -X utf8 -m unittest discover -s tests/firmware -p 'test_*.py' -v` | **PASS 18/18**; actual C receiver/cache/time and B renderer host suite. Frozen `scripts/evaluate-product.py` legacy seam is **29/29**, separate from device acceptance. |
| `python docs/design/lcd/gemini/regression-check.py` | **PASS**; executes selected B JavaScript/DOM transitions, F1 cache, F2 totals, F3 windows/BOOT, and 299/300/301 boundaries. |
| `python tests/integration/design-check.py` | B geometry/sample/state/BOOT/offline checks pass; reported A/C/E/F comparison-only findings are outside selected B. |
| Accepted [Sol build report](../orca-sol/report.md) and [active-usage build log](../orca-sol/build-active-usage-output.txt) | **PASS, not rebuilt.** ESP-IDF v5.3.2 target/build success; active app SHA-256 `385130667AB15CA8DCC665E70FC06882B1E89535BDE8D84AF05FDC2B36C1EF72`, bootloader `F4C5160D0777EBDA11EDAC881853B211300323E5CF8F96EEEDA5314D731D02AB`, partition `7F00B6C042A89B15B0CAC534F82ED988CAF29278FF5700B0C511EB1B5BB7C820`, sdkconfig `46788F1C30A51868DA7C66C41DEF9045514FAAF393BC68EC0D6F05DF4DACA452`; independently recomputed hashes match. |

The integration suite covers native nested token events/session identity, absent and malformed/bool/negative/fractional/subcount token cases, original token timestamps despite unrelated events, explicit multi-session selection, source vs normalized totals, quota `rateLimitsByLimitId` duration/unknown windows, account/session scope, source ages 0/299/300 with fresh C receive age, future timestamps, per-source failure/last-good/recovery, global latest/source/captured/last-known/default, RPC initialize → initialized → read order and bounded cleanup, and production CLI reservation/wrap/corrupt-or-missing state/contention/no implicit initialization. CLI checks exercise independent manual/automatic refresh, actual queue drain success/failure, reconnect ≤1/s and availability/manual dispatch ≤5s. Manual tests prove both an event after quota acquisition triggers a fresh native acquisition and a second request during MANUAL write sends a second frame. Two distinct near-limit cases pass: the no-budget path models 0.5s bounded cleanup, skips another RPC, retains quota last-good with `QUOTA_TIMEOUT`, recollects token input 250 and drains sequences 0/1; the original two-RPC boundary uses .95/.95 AUTO and .9/.9 MANUAL responses plus .8s successful drains, and observes the real `CdmSender.transmit_payload` return to confirm a successful MANUAL `SendOutcome` within five seconds, fresh input 250, retained quota last-good and C acceptance of sequences 0/1.

### C / I / F acceptance

| IDs | Result | Remaining boundary |
|---|---|---|
| C1 | **PASS (accepted build)** | Build/log/hash verified; no rebuild needed. |
| C2 | **not_run** | No physical 30-second panel/readability/clipping observation. |
| C3–C7 | **PASS (host)** | Production PC data through C and B renderer cover dynamic quota/global/null/error/stale/last-good; physical LCD display remains not_run. |
| C8 | **PASS (host)** | Manual/auto/BOOT navigation and bounded PC refresh tested; physical BOOT/RST, GPIO0, redraw timing remain not_run. |
| I1–I2 | **PASS (synthetic host)** | Source/time/unit/error and privacy/scoping use metadata-only fake inputs. |
| I3 | **PASS (host wire)** | Canonical bytes, C acceptance/rejection and serial mock behavior pass; actual COM/receiver observation not_run. |
| I4 | **PASS (host)** | Product C receiver/cache/time and B renderer linked in tests; physical device remains not_run. |
| F1–F7 | **PASS (host)** | Collection, normalization, transport, receiver, renderer, refresh and global-reset source semantics covered by suites above. |
| F8 | **PASS (accepted build/host)** | On-device timing, power and 30-second observation not_run. |
| F9 | **PASS (host)** | Sol report records exactly three candidates and one selected implementation: internal chip temperature, isolated in `f9_temp.c`; tests cover install/enable/read failures and return a sensor value without constant substitution. Physical plausibility not_run. |

### Live L1–L8

| ID | Result | Evidence/boundary |
|---|---|---|
| L1 | **PASS (host)** | Explicit selection and A→B replacement; C renderer pixels match B-only state. |
| L2 | **PASS (host)** | Native cumulative token count replaces earlier count; unrelated later events do not change the token observation time. |
| L3 | **PASS (host)** | Input/output/cache/reasoning/source/normalized channels retain units and subset meanings. |
| L4 | **PASS (host)** | Account quota remains separate from session telemetry. |
| L5 | **PASS (host)** | All provider quota windows, exact duration and unknown-duration windows stay distinct and pageable. |
| L6 | **PASS (host)** | Different source total and input+output normalized total both survive. |
| L7 | **PASS (host)** | Original event timestamps, future rejection, source stale 0/299/300 and independent receive age pass. |
| L8 | **PASS for synthetic review** | Only synthetic metadata used; no credentials, conversations or real session files accessed. |

### Prior actual findings

- Earlier selected-B execution lost last-good cache after Normal → Unknown/Waiting → Error/Disconnected. The corrected B JavaScript now passes those transitions, empty-cache behavior, recovery, 299/300/301 source-age checks, all quota pages, and BOOT navigation in the actual Node VM/DOM regression. Physical readability remains not_run.
- An earlier production C A→B frame retained both sessions and rendered A+B. The accepted active-usage correction now atomically replaces the current list; the linked C test verifies B-only records/pixels, full-scope identities, rejected-frame atomicity and bounded history.
- Earlier PC findings around token observation stamping, cold global omission, provider isolation/last-good and sequence/write bounds are covered by current PC and producer-to-C tests. The prior independent Dispatch reproduced three manual refresh defects; on accepted PC source `39e52bd`, all three regression paths now pass: post-acquisition quota requests make a fresh acquisition, a second request during MANUAL write sends another frame, and near-limit cleanup/drain remains within five seconds.

No `product_pass=true` is claimed. Coordinator/device gates still required: actual COM upload/send/reconnect and receiver observation; physical selected-B screen/BOOT/RST, 30-second operation, ≤2s accepted-frame redraw, clipping/readability, BOOT/RST/GPIO0 electrical behavior, sensor plausibility, live-account observation and endurance. The changes owned here are limited to `tests/integration/test_pc_producer_to_c.py` and this report/checkpoint; no PC, firmware, design or frozen input source was changed.
