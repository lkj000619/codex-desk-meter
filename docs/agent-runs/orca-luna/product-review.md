# Independent PC and selected-B firmware review

Run `run_c968c43361da` · Task `task_4d49e747c570` · Dispatch `ctx_da800c8d8bce` · worker terminal `term_1a2fcc8b-6402-4851-ba15-d27061517be1`.

## Status

**PC integration is pending the latest accepted PC submission. Firmware `853ddf7` is accepted and under independent verification; no product pass is claimed.** The coordinator said the PC remediation in `task_a6eebb977125` is still active. I have not inspected or tested that actively changing PC submission.

The initial accepted firmware baseline was `b6ec3d5`; its failing production-C integration evidence is preserved below. Corrected firmware `853ddf7` is accepted and stable for independent review. Each frame carries the complete current active usage list: a frame containing only B replaces an earlier A-only list, while distinct records in the same frame coexist. Therefore the original B-only selection assertion remains valid. Cache identity is the full scoped source identity plus `snapshot_id`; changed-ID last-good can carry only for one old and one current non-session record with identical complete source context; ambiguous matches stay cold/unknown; duplicate full scoped identities may be rejected.

## Commands and evidence

| Command / source | Result | Scope |
|---|---|---|
| `python -m unittest discover -s tests/integration -p 'test_cdm_session_selection.py' -v` | **Exit 1** against the existing host executable from accepted `b6ec3d5`. Synthetic canonical frames selecting A then B were both accepted; cache contained `['selected-session-A', 'selected-session-B']`; A→B Usage-page CRC `1525439880` differed from B-only CRC `2620002129`. | Actual linked C receiver/renderer through `tests/firmware/.build/cdm-host.exe`; no PC source or user data. The test predates the clarified complete-active-list rule and is not a final assertion of desired cache contents. |
| `python -B -X utf8 -m unittest discover -s tests/firmware -p 'test_*.py' -v` | **PASS, 18/18** (independent rerun). | Production C host receiver/cache/renderer suite; frozen legacy evaluator passes **29/29** through its separate adapter. Neither result is device proof. |
| `python -B -X utf8 -m unittest discover -s tests/integration -p 'test_cdm_session_selection.py' -v` | **PASS, 1/1** (independent rerun). | Actual linked production C receiver/renderer; the B-only assertion is valid because each frame is the full active set. |
| `python -B -X utf8 -m unittest discover -s tests/integration -p 'test_cdm_receiver_boundaries.py' -v` | **PASS, 3/3**. | Production C rejects bad protocol, extra properties, invalid schema/duplicate scoped identity, CRC, noncanonical JSON, truncated, CRLF, extra-LF, invalid UTF-8 and oversized frames atomically; accepts float percentages and Unicode labels; preserves sequence/cache over a stale frame and silent gap. |
| `python -B -X utf8 -m unittest discover -s tests/integration -p 'test_*.py' -v` | **PASS, 8/8** (latest complete integration discovery). | Includes C parser/cache/sequence and session-selection pixel checks plus actual F9 C module tests with a fake driver. PC producer/CLI integration remains pending. |
| `python -B -X utf8 -m unittest discover -s tests/integration -p 'test_f9_temp.py' -v` | **PASS, 4/4**. | Compiles actual `firmware/main/f9_temp.c` with an ephemeral fake IDF sensor API; install/enable/read errors yield unknown, enable failure uninstalls, null pointer is rejected, and a supplied value is returned without substitution. |
| Incremental `idf.py build` | Corrected build succeeded with ESP-IDF **v5.3.2**; I independently matched the app hash `385130667AB15CA8DCC665E70FC06882B1E89535BDE8D84AF05FDC2B36C1EF72` and related artifacts to the correction report. | Accepted corrected build; no rebuild is planned absent a new concern. Log: [build-active-usage-output.txt](../orca-sol/build-active-usage-output.txt). |

The focused test is `tests/integration/test_cdm_session_selection.py`; it builds only metadata-only canonical frames and feeds them to the actual C host adapter. It does not use a Python reimplementation of the C cache. The original baseline failure is retained separately from the corrected firmware result.

## Requirement status at this checkpoint

### C / I / F

| IDs | Status | Evidence and remaining boundary |
|---|---|---|
| C1 | **PASS on accepted corrected build** | ESP-IDF v5.3.2 incremental build succeeded. I independently matched the app, bootloader, partition table, sdkconfig, `cdm.c`, active-usage test, and build-log SHA-256 values to the dated Sol report. |
| C2 | **not_run** | No physical LCD observation, 30-second run, or readability/clipping evidence from a board. |
| C3 | **host-only partial; current end-to-end pending** | Baseline host report covers quota/session rendering and paging. Current accepted PC frames have not been tested through corrected C and GUI. |
| C4 | **corrected host renderer pass; PC global producer pending; physical not_run** | Host checks cover latest reset and elapsed-time rendering; current PC global-reset producer has not yet been joined to C. |
| C5 | **corrected host renderer pass; physical not_run** | Host checks cover last-known reset and default fallback when reset data is absent; no board observation. |
| C6 | **corrected host renderer pass; PC global producer pending; physical not_run** | Host checks preserve source and captured-time labels; current PC global-reset source integration remains pending. |
| C7 | **corrected host receiver/renderer pass; producer integration pending** | Independent corrected suite passes per-source failure/recovery and source/receive-age coverage. Corrected PC producer is not yet available. |
| C8 | **host navigation pass; refresh/timing partly pending; physical not_run** | Host tests cover screen/page navigation. Coordinator's synthetic prior-PC scheduler probe measured 4.5s collection + 2s write = 6.5s after a manual request, returned rc 0, and exceeded the 5s limit; this is routed to the active PC owner. Actual BOOT electrical behavior and ≤2s LCD response remain unmeasured. |
| I1 | **pending latest accepted PC submission** | Fixture collector source/time/unit/error provenance and privacy behavior await independent synthetic producer-to-C integration. |
| I2 | **pending latest accepted PC submission** | Provider normalization and separation of distinct global sources await independent synthetic producer-to-C integration. |
| I3 | **host wire checks pass; device not_run** | Production C parser/sequence checks pass; PC sender and device ACK integration remain pending. |
| I4 | **corrected host tests pass; physical not_run** | Independent receiver/cache suite and A→B selection pixel test pass against linked production C; device behavior remains `not_run`. |
| F1 | **pending latest accepted PC submission** | Collector behavior, native token events, explicit session selection, and per-source cache/error recovery await current PC-to-C evidence. |
| F2 | **pending latest accepted PC submission** | Normalized/source totals, included subsets, window normalization and account/session scope await producer-to-C verification. |
| F3 | **host wire checks pass; device not_run** | Production C rejection/sequence checks pass; PC sender and device ACK integration remain pending. |
| F4 | **corrected host tests pass; physical not_run** | Production C cache replacement/last-good behavior and selected-session pixel regression pass; no board observation. |
| F5 | **host-renderer pass; physical not_run** | Corrected host pixel checks pass; physical panel readability and timing remain `not_run`. |
| F6 | **pending latest accepted PC submission** | Input/refresh behavior, including automatic/manual dispatch, reconnect, and the five-second bound, awaits the accepted deadline remediation and real fake-process/transport integration. |
| F7 | **host-renderer pass; PC global producer pending** | Host behavior for latest/last-known/default reset data passes; global source/captured-time producer integration remains pending. |
| F8 | **baseline build evidence; physical not_run** | Artifact hashes were checked. No latency/power/board evidence; no `product_pass=true`. |
| F9 | **host fake-driver tests pass; physical not_run** | Design/report lists exactly three candidates and one isolated internal-temperature implementation. New host tests execute the actual F9 C module for install/enable/read failure and success; device sensor plausibility and `UNKNOWN` on real hardware remain not_run. |

### Live requirements L1–L8

| ID | Status | Evidence / blocker |
|---|---|---|
| L1 explicit session selection | **firmware PASS; PC selection pending** | Independent A-only→B-only production-C regression passes. Accepted C tests cover same-frame coexisting scoped records, replacement, duplicate rejection, unique last-good inheritance, ambiguity/no-inheritance and same-session recovery. Current PC explicit selection remains pending. |
| L2 cumulative token events | **pending current PC evidence** | No accepted PC submission available for synthetic nested native token events, session identity, partial/restart/replace handling. |
| L3 token channels | **pending producer-to-C integration** | Existing renderer report distinguishes normalized and source totals; independent PC output verification of channel IDs, subset inclusion and nullable quota fields remains. |
| L4 account quota scope | **pending synthetic PC integration** | No live account/auth calls were made. Need current synthetic evidence for account-scoped quota and independent session scope. |
| L5 variable windows | **pending producer-to-C integration** | Baseline renderer report says all windows page; current PC rateLimitsByLimitId durations/unknown windows and exact IDs/labels are not yet verified end to end. |
| L6 total/subset semantics | **host-renderer partial** | Baseline render has separate normalized/source totals and included cache/reasoning labels. Current production PC output and C pixels are not joined. |
| L7 timestamps/ages | **C receive-age/source-age boundaries PASS; producer path pending** | Independent C suite checks source/receive age separation, anchoring and 0/299/300 stale boundaries. Original token event timestamps, future PC timestamps, fresh receive with stale source, and original timestamp retention need current PC→C evidence. |
| L8 privacy | **PASS for this review** | Test inputs are synthetic metadata. No real account/session/auth files, session bodies, COM, reset, flash, or other worktree/history were used. |

## Remaining PC integration after acceptance

The accepted C host suite and new integration tests cover parser/cache/pixel/F9 behavior. After the coordinator confirms the accepted PC submission, test that version's production gather and normalization output and feed its canonical raw `cdm/1` bytes into the same accepted C receiver. Include actual native nested token event shapes and invalid numeric forms; explicit multi-session selection; original token timestamps and unrelated events; future times; source vs receive ages and 0/299/300 stale; normalized/source totals and included subsets; all rateLimitsByLimitId windows/durations/unknowns, account/session scope; and per-provider failure, last-good, recovery and exact current-frame contents. Use only synthetic fixtures and process/transport doubles.

Also verify the real CLI serial path with only fake transport/processes: initialize/initialized/read RPC order and bounded timeout cleanup; independent manual/automatic refresh; full manual-request-to-write deadline including collection/RPC cleanup; reconnect rate/availability/manual dispatch; reserve-before-write persistent sequence including wrap/corrupt/missing state; single-sender contention; and no auto-init bypass. The coordinator's prior-PC synthetic manual probe was 6.5s (4.5s collection + 2s write), exceeding the 5s limit despite rc 0; this is routed to the active PC owner and needs retesting after acceptance. Actual COM, account/auth, reset/flash, physical C2/C8, electrical BOOT/GPIO0, panel timing and sensor readings remain coordinator-owned or `not_run`.

Current blocker: the coordinator has not yet sent readiness for the latest accepted PC submission. The known manual-dispatch deadline failure is in the active PC remediation. No test result here establishes complete product approval.

## PC integration harness prepared — 2026-10-09

Added [test_pc_producer_to_c.py](../../../tests/integration/test_pc_producer_to_c.py) under the owned integration scope. It uses only synthetic session JSONL, quota dictionaries, provider/reset fixtures, fake app-server streams, a fake serial sink, temporary sequence files, and the linked production C receiver. Cases cover native nested token events and identity; invalid count types/ranges and subset rules; normalized/source totals; explicit/latest selection; original timestamps and 0/299/300-second source staleness against fresh C receive age; all account quota window IDs/durations including unknown duration; account/session scope; provider error/last-good/recovery; global reset source/captured time and last-known; RPC initialize/initialized/read order and bounded timeout cleanup; CLI fake-serial sequence reservation/wrap and fail-closed missing/corrupt state; no implicit initialization and sender contention.

This harness has **not been run**: the coordinator authorized read-only review of accepted PC commit `0e39f0d` and test preparation, but final producer and CLI execution waits for the deadline remediation to be accepted. Its current basic watch cases do not satisfy the deadline test: the coordinator directed that a manual event arrive during a slow automatic initialize/read and write, that timing begin at the event, and that tests use the production bounded RPC and serial transport paths. The coordinator also reported that Windows `Serial.flush()` can wait for queued bytes beyond the configured `write_timeout`; this is routed to the active PC owner and is not independently verified here. A fake-transport test now exercises the real `cmd_send` and `WindowsSerialSink` wrapper with bytes held in the queue for four seconds; after acceptance it must demonstrate bounded failure, cleanup, and consumed sequence. Also cover manual arrival during automatic RPC/write, last-good cache after native timeout, independent scheduling, reconnect throttling and availability dispatch. The harness is still unrun, so none of these checks is acceptance evidence. No PC or firmware source was edited, and no actual provider call, session/account data, COM device, reset, or flash was used.
