# Current GUI review checkpoint — 2026-10-08

- Run: `run_c968c43361da`
- Task: `task_c0ecb13ae179`
- Active Dispatch: `ctx_35a7c601f1d6` (the previous `ctx_28254a047a7d` attempt was revoked as terminal-missing)
- Worker terminal: `term_079881f4-f92c-464b-a856-21274157b8c1`
- Orca browser page: `7f2799a1-9f3f-41b1-8dd6-3e25a97c6fa8`, currently on `http://127.0.0.1:8289/opendesign/mockups/gemini-a/index.html`
- Last completed action: full manifest scan rebuilt six A–F entries; six normal screenshots captured at exact 820×320; D WAITING showed unknown placeholders.
- Current phase: reviewing remaining states, BOOT cycle, clipping, offline resources and Sol window paging. No designer HTML or handoff was edited.
- Next action: resume live browser state checks on all six candidates, then create only assigned report/check/gallery artifacts and update the manifest/checkpoint as needed.
- Browser server verified bound to `127.0.0.1:8289`; viewer returns HTTP 200.

---
# Orca Luna checkpoint

## GUI review Dispatch start

- Task ID: `task_c0ecb13ae179`
- Dispatch ID: `ctx_28254a047a7d`
- Scope: own only `docs/agent-runs/orca-luna/gui-review.md`, this checkpoint, `tests/integration/design-check.py`, `opendesign/comparison.html`, `opendesign/manifest.json`, and `opendesign/screenshots/`.
- Completed at start: located all six candidate `index.html` files and the design brief; no candidate inspection, browser interaction, or shared-manifest rebuild has been performed in this Dispatch.
- Exact next step: read current `AGENTS.md`, selected user requirements/design brief, and the pinned `run-opendesign` skill; inspect the existing checkpoint and coordinator inbox before beginning the browser review.
- Evidence: six candidate paths (`gemini-a/b/c`, `sol61-a/b/c`) and `opendesign/manifest.json` exist. No files outside this Dispatch's owned scope have been changed.

---
# Orca Luna checkpoint

## Fresh Dispatch final review

- Task ID: `task_c4c03e6d2c02`
- Dispatch ID: `ctx_a4f395e58ecc`
- Scope: review-only; owned files are this checkpoint and `requirements-review.md`.
- Completed: resumed the existing review; reread the persisted interface decision in `docs/design/2026-10-08-orca-harness.md`; updated report Dispatch metadata and GUI status. The report retains the acceptance matrix, live token/quota mapping and conflicts, LCD/BOOT constraints, safe resume checks, pre-implementation corrections, and explicit `not_run` limits.
- Persisted mapping confirmed: fixed token channels under `session_telemetry`; cached input and reasoning output are subcounts; normalized total is input+output; exact quota duration stays in local typed metadata and wire ID/label; missing duration remains unknown; available account context uses `agent_id=codex-cli` and stable sanitized collector `host_id`; quota stays account-scoped; local inputs use `local_runtime`, fixtures use `fixture`.
- GUI status: all six `index.html` paths exist and coordinator reports Sol submission complete. Handoff completeness, independent visual QA, and user selection remain future review gates; no visual approval is claimed.
- Prior failed Dispatch preserved: `ctx_85d922e4b68d`; its incorrect worker check/ack with `--run` returned `consumer_fenced`, request ID `d24edef2-d5f2-4d8b-b6da-4ea567dffa0f`. It ended without `worker_done`; this fresh Dispatch is authoritative.
- Current coordinator delivery `delivery_3cd92f62438d` / message `msg_f801c20f6c69` was acknowledged. Ack result request ID: `82ddfee8-4edc-433f-bb48-3509389c230e`; no additional messages were returned.
- Evidence: design decision at lines 75–90; report includes acceptance matrix at line 66, LCD/BOOT constraints at line 99, safe resume checks at line 110, future GUI gate at line 123, and limitations at line 145. All six GUI paths returned `True`. Prior synthetic schema/semantic checks remain recorded in the report; no runtime/hardware test was run.
- Files modified: `docs/agent-runs/orca-luna/checkpoint.md`, `docs/agent-runs/orca-luna/requirements-review.md` only. No frozen inputs, coordinator docs, firmware, PC code, user logs/auth, other worktrees, or hardware were accessed in this resumed dispatch; no commit was made.
- Exact next step: perform the final mailbox check with only `orca orchestration check --terminal term_5a5f6147-6087-4bd6-af81-a1a434563ab8 --json`; if no redirect is present, send exactly one `worker_done` for this Task/Dispatch, listing both modified files and the report path.


## GUI review Task retry — 2026-10-08

- Run: `run_c968c43361da`
- Task: `task_c0ecb13ae179`
- Dispatch: `ctx_35a7c601f1d6`
- Worker terminal: `term_079881f4-f92c-464b-a856-21274157b8c1`
- Phase: reviewing candidates; prior coordinator attempt was terminal-missing and revoked, this Dispatch is authoritative.
- Scope: `docs/agent-runs/orca-luna/gui-review.md`, this checkpoint, `tests/integration/design-check.py`, `opendesign/comparison.html`, `opendesign/manifest.json`, and `opendesign/screenshots/` only.
- Inputs: six candidate HTML files and designer handoffs already exist; all six candidates will be reviewed against `experiments/orca-harness-20261008/design-brief.md`, the selected user requirements, and `docs/agent-runs/orca-luna/requirements-review.md`.
- Viewer: pinned project skill `tools/opendesign/skills/run-opendesign/SKILL.md`; verified `127.0.0.1:8289` is the listener and `/opendesign/index.html` returns HTTP 200. No server was started or changed.
- Mail: coordinator follow-up `msg_fb6c80183447` was processed and delivery acknowledged via `orca orchestration check --terminal term_079881f4-f92c-464b-a856-21274157b8c1 --ack delivery_e9366c281ad3 --json`.
- Completed: read documentation map, design brief, shared design/plan, requirements review, both handoffs/checkpoints, viewer and pinned run skill; confirmed candidate paths.
- Remaining: inspect each candidate's actual browser geometry and interactions at 820×320; save six normal screenshots; add a lightweight design-check, comparison page and full-scan manifest; record actionable issues and update this checkpoint; final inbox check and one native `worker_done`.
- Last verification: server listener `127.0.0.1:8289`; local viewer HTTP 200. Browser state checks not run yet.
- Next action: inspect the native embedded browser commands and review candidate controls/data/state selectors before capturing.
- Physical LCD, firmware, live account and device tests: not_run; no COM access performed.

- Artifact checkpoint: rebuilt `opendesign/manifest.json` from a full scan after all six candidate HTML files existed; scan found six mockups and zero design-system files. Manifest contains actual A–F labels and groups in the original candidate folders.
- Next action: reload the viewer, then run rendered browser checks and collect the six normal-state LCD captures.

- Artifact checkpoint: saved six static normal-state PNGs under `opendesign/screenshots/`, each cropped from an Orca browser viewport screenshot using the rendered LCD element bounds; all six measured exactly 820×320 CSS px at devicePixelRatio 1. Screenshot files are A Gemini Telemetry Matrix, B Swiss Studio Meter, C Industrial Field Gauge, D Signal Board, E Session Ledger and F Window Atlas.
- Browser checkpoint: viewer manifest renders six A–F rows. D normal shows 58%/82% remaining, 42%/18% used, 124800 input, 16400 output, 89600 cached, 2300 reasoning and 141200 source/normalized total; UTC source observation and separate source/receive ages are visible. D WAITING renders `--` for metrics, reset, observation and ages rather than zeros.
- Interaction note: Orca `select` changes candidate state selectors. Orca `click --element` reports success but did not advance the BOOT button on A or D; invoking the page's actual BOOT element `.click()` from Orca `eval` does advance D to GLOBAL RESET. Checking whether this is a browser tool click limitation and verifying all three screens in each candidate.
- Remaining: inspect all states and screens, verify list paging where supplied, run the requested static design check, write GUI findings/comparison, verify links/resources/screenshots and finalize checkpoint/mail.
- Last verification: screenshot crop dimensions 820×320 for all six; no hardware or firmware test.
- Next action: run state and BOOT checks in each live candidate page, recording any content or geometry failures.

- Browser QA checkpoint: all six candidates render exactly 820×320; visible leaf-text bounds stayed inside the LCD for all selected states checked, with zero measured text elements outside. Browser `performance` resource lists were empty after each standalone candidate load; no network/CDN/font dependencies were observed.
- State checks: A–C selectors expose Normal, source-stale, disconnected, unknown, error, waiting and recovery; D–F expose those plus last-known reset. Normal common values and separate token/quota labels were present. Unknown removes numeric values; WAITING uses `...` in A–C and `--` in D–F; stale/disconnect retain baseline data and show independent source/receive age; error retains the sample when entered from Normal; recovery replays the original sample.
- BOOT checks: A–C screen selector values traversed `1 → 2 → 0` with the real page button event; D–F `data-screen` traversed `GLOBAL RESET → STATUS → USAGE`. D/E navigation stress wraps 1–2/6 → 3–4/6 → 5–6/6 → 1–2/6 and previous wraps to 5–6/6. F wraps each single-window page through 6/6 to 1/6. D last-known global view shows the original reset, codex-resets.com, captured time and 7h10m elapsed.
- Findings to verify/document: Gemini A/B/C `applyState` handlers mutate displayed values and do not restore the baseline before all states; changing from Unknown/WAITING to Error/Disconnected/Stale can leave placeholder values under a last-good/stale label. Sol B/C browser document titles still say `D · Signal Board · LCD exploration`. Gemini handoff §6.4 says a 171KB dirty-rect transfer is “60fps possible” without a measured transfer/renderer result. No designer source/handoff edited.
- Next action: confirm Gemini state-selector path dependence with a clean normal→unknown→error and unknown→disconnected sequence; then add the requested standard-library `design-check.py`, comparison page and review report.

- State-path checkpoint: fresh browser sequence in Gemini A/B/C — Normal → Unknown → Error leaves `--` under the “ERROR / LAST-GOOD” banner; Unknown → Disconnected leaves `--` under “LAST-GOOD VALUES PRESERVED”. The state selector therefore depends on the prior selection instead of restoring/declaring its last-good sample. Coordinator should route this to the Gemini designer for an independent-scenario reset or explicitly document sequential cache semantics; no source files were changed.
- Mail check after state-path run: `orca orchestration check --terminal term_079881f4-f92c-464b-a856-21274157b8c1 --json` returned no messages.
- Next action: add the small static design-check, then build comparison/report artifacts from the confirmed browser evidence.

- Artifact checkpoint: created `tests/integration/design-check.py` using only Python standard library. It will validate the six-file inventory, 820×320 CSS, sample values, offline resource references, state options, BOOT controls, screenshot/manifest/comparison evidence; it reports naming, source-total-label and fixed-window gaps as findings instead of modifying candidates.
- Checkpoint state: the static checker has not been run yet because `comparison.html` is still pending.
- Next action: create the six-row `opendesign/comparison.html` with candidate links, names, screenshot links and the shared synthetic sample.

- Artifact checkpoint: created `opendesign/comparison.html` with actual A–F names, direct candidate links, clickable 820×320 PNG evidence and the common synthetic quota/session/global-reset sample. The page states that browser evidence does not prove hardware behavior.
- Next action: run the new static checker, then render and verify the comparison page and all links in the local browser before writing the concise review report.


## Selected-design review completion - 2026-10-08

- Current Dispatch: `task_c0ecb13ae179` / `ctx_35a7c601f1d6`; worker terminal `term_079881f4-f92c-464b-a856-21274157b8c1`; Orca page `7f2799a1-9f3f-41b1-8dd6-3e25a97c6fa8`.
- Coordinator selection update `msg_9a3ae89f12e2` / `delivery_85fd76a01c5f` was processed and acknowledged. User selected B - Swiss Studio Meter for follow-up; the current Task remains a six-candidate review and makes no product or hardware approval claim.
- Updated `gui-review.md` to identify B as selected and route B findings F1-F3 plus F5's unmeasured transfer estimate to the coordinator. A/C and E/F remain comparative evidence; no designer HTML or handoff was changed. Updated the comparison page with B selection, prototype-status, findings-route, and review-report text.
- Completed evidence: six actual 820x320 normal-state PNGs; state, stale/error/recovery, waiting, BOOT cycle, text-bound, source/timestamp, and paging checks across the six browser candidates; full-scan six-entry manifest. Physical LCD checks remain `not_run`.
- Final verification completed: `python tests/integration/design-check.py` exited 0; all six candidates, six screenshots, full-scan manifest, and comparison evidence passed. The checker reports documented design findings for fixed Gemini windows, B/C source-total labeling, and E/F copied browser titles.
- Updated comparison rendered in the Orca browser at `http://127.0.0.1:8289/opendesign/comparison.html`: B selection and report link are visible; six images are loaded at 820x320; 19 links are present; zero external image/script/style resources were found.
- Final remaining action: check the coordinator inbox once more, then send exactly one `worker_done` for this Dispatch.


## Selected-B follow-up review - 2026-10-08

- Current Task / Dispatch: `task_0d62e820abfa` / `ctx_c9524d9d2327` in `run_c968c43361da`; worker terminal `term_079881f4-f92c-464b-a856-21274157b8c1`.
- Orca browser page: `c96626c2-be26-4498-b9eb-375e79cd472f`; B was reviewed at `http://127.0.0.1:8289/opendesign/mockups/gemini-b/index.html`; viewer listener was `127.0.0.1:8289` only.
- Result: F1 FAIL. Live Normal->Unknown->Error/Disconnected and Normal->Waiting->Error lose the previously valid cache; direct Normal->Error and Normal->Disconnected retain it. The exact required correction and actual browser evidence are in `gui-b-review.md`, and escalation `msg_d8eee653314b` was sent to the coordinator.
- F2 PASS with an in-page synthetic mismatch (`normalized=141,200`, `source_total=999,999`), included subsets, unknown session quota, and account/session separation. F3 PASS: all six windows paged over three pages with wrap; the BOOT button event cycled Usage->Global Reset->Status->Usage. F5 PASS: handoff labels frame/transfer estimates `not_run` and not guaranteed.
- `python docs/design/lcd/gemini/regression-check.py` exited 0 but only asserts source strings and simulates a separate Python state machine; it does not execute B JavaScript. Latest `python tests/integration/design-check.py` exited 0: all six candidate checks and the full-scan manifest/gallery checks pass, with only comparative A/C/E/F findings.
- Browser geometry: 820x320 LCD; no text ranges outside bounds across normal, stale, disconnected, unknown, error, waiting, recovery, global reset, and status. The source-stale selector exercises 301s/0s; exact 300s is not configurable. Browser resource list was empty. Smallest measured text is 8.5 CSS px; physical readability remains `not_run`.
- Updated comparison was rendered: six initial images load at 820x320; 22 links; zero external resources; follow-up report and new selected-B screenshot both return HTTP 200. New screenshot `opendesign/screenshots/selected-b/B-swiss-studio-meter-normal.png` measures 820x320.
- Rebuilt `opendesign/manifest.json` from a full scan: six mockup HTML files in six A-F groups and zero design-system files. Baseline/final SHA-256 values match for initial `gui-review.md` and all six initial normal screenshots.
- Files changed: this checkpoint, `gui-b-review.md`, `opendesign/comparison.html`, `opendesign/manifest.json`, and the new selected-B screenshot. No designer B, handoff, designer regression-check, shared design-check, PC, firmware, frozen input, or initial screenshot/report file was changed.
- Exact next action: perform the required final `orca orchestration check --terminal term_079881f4-f92c-464b-a856-21274157b8c1 --json`; then send exactly one `worker_done` with outcome `failed` for this Dispatch because selected-B F1 remains blocked.


## Selected-B corrected retry — 2026-10-09

- Current Task / Dispatch: `task_0d62e820abfa` / `ctx_fbf6b4c142f4`; Run `run_c968c43361da`; worker terminal `term_079881f4-f92c-464b-a856-21274157b8c1`.
- Coordinator follow-up `msg_b568bb6d107b` was processed and acknowledged. It confirms this is the retry after the accepted first FAIL and requests preserving the original failed review, checking actual browser transitions/no-cache/stale boundaries/F2/F3/BOOT/geometry, and saving a separate corrected screenshot.
- Result: corrected selected B **passes F1–F3 and F5 review checks**. The prior 2026-10-08 F1 failure remains intact in `gui-b-review.md` and `comparison.html` as historical evidence.
- Browser: viewer listener `127.0.0.1:8289`; Orca page `c96626c2-be26-4498-b9eb-375e79cd472f`; B LCD rect `820×320` CSS px, DPR 1; default Usage. Normal→Unknown→Error, Normal→Waiting→Error, and Normal→Unknown→Disconnected retained original sample/time; Recovery restored it. Empty-cache injected in page memory made generic Error and Disconnected show `NO CACHE`, `--`, `OBS: UNKNOWN`.
- Browser: stale boundary views show 299s Available, 300/301s Stale, receive age 0s Fresh, and original corresponding observation times. Six quota windows page through all three pages and wrap; actual BOOT button click cycles Usage→Global Reset→Status while long-list mode remains selected. Global Reset source/time/scope labels and independent source/receive-age labels were checked.
- Geometry/offline: 33 state/screen checks across normal, unknown, waiting, error, disconnect, explicit cold states, 299/300/301 stale, and recovery show no text outside the 820×320 canvas; minimum text 8.5 CSS px. Browser external resource list was empty; physical readability is `not_run`.
- Last test: `python docs/design/lcd/gemini/regression-check.py` exited 0 (actual B inline JS executed by Node VM); `python tests/integration/design-check.py` exited 0 (six-candidate/static manifest and gallery checks; only A/C/E/F comparative findings). No shared-checker compatibility update was warranted.
- Artifacts: appended the dated retry section to `gui-b-review.md`; added dated status and new screenshot link to `comparison.html`; rebuilt `manifest.json` by full scan; saved `opendesign/screenshots/selected-b/B-swiss-studio-meter-normal-2026-10-09.png`. Initial `gui-review.md` and initial six PNGs are preserved.
- Files modified in this Dispatch: `docs/agent-runs/orca-luna/checkpoint.md`, `docs/agent-runs/orca-luna/gui-b-review.md`, `opendesign/comparison.html`, `opendesign/manifest.json`, and the new dated PNG under `opendesign/screenshots/selected-b/`.
- Exact next action: rebuild the manifest from the current full scan, rerun `python tests/integration/design-check.py`, confirm preservation hashes and local comparison/screenshot links, perform the final inbox check, then send exactly one `worker_done` with outcome `succeeded`.

## Recovery verification — 2026-10-09

- Current Task / Dispatch: `task_0d62e820abfa` / `ctx_9477f122f8d4`; Run `run_c968c43361da`; worker terminal `term_1a2fcc8b-6402-4851-ba15-d27061517be1`.
- Coordinator recovery note `msg_4ac54d9f247f` was processed and acknowledged. It fences prior Dispatch `ctx_fbf6b4c142f4` as `terminal_missing`, keeps this Task active, and asks to preserve the accepted corrected-B evidence without repeating six-candidate browser tests.
- Re-read the cohort design/interface, initial GUI F1–F5 findings, corrected Gemini handoff §7, and its Node VM regression check. The preserved B report records the original F1 FAIL and corrected F1–F3/F5 PASS with the requested transition, totals, stale-age, paging, BOOT, reset/source-label, and geometry evidence.
- Verified the dated corrected-B normal screenshot visually and measured it at 820×320 (34,682 bytes). The comparison page retains the initial findings and six original candidates, and links the dated B report and new screenshot; the full-scan manifest still lists all six candidates.
- `python docs/design/lcd/gemini/regression-check.py` exited 0, executing Candidate B inline JavaScript in the Node VM and passing cache/no-cache transitions, F2 totals, F3 paging/BOOT, and 299/300/301s boundaries. `python tests/integration/design-check.py` exited 0; B and the shared six-candidate artifact/link checks pass. Its only findings remain comparison-only A/C/E/F items, so no shared-checker compatibility edit was needed.
- The initial `gui-review.md` and six normal PNGs remain untouched. No designer, PC, firmware, frozen input, comparison, manifest, or test file changed in this recovery Dispatch; only this checkpoint is updated. Physical LCD readability and hardware behavior remain `not_run`.
- Last verification: `python docs/design/lcd/gemini/regression-check.py` exit 0; `python tests/integration/design-check.py` exit 0; corrected PNG dimensions 820×320.
- Exact next action: perform the final `orca orchestration check --terminal term_1a2fcc8b-6402-4851-ba15-d27061517be1 --json`; process and acknowledge any delivered messages, then send exactly one `worker_done` with outcome `succeeded` for this Task / Dispatch.

## Serial flush boundary follow-up — 2026-10-09

- Current Task / Dispatch: `task_4d49e747c570` / `ctx_da800c8d8bce`; Run `run_c968c43361da`; worker terminal `term_1a2fcc8b-6402-4851-ba15-d27061517be1`.
- Coordinator status `msg_d9f96b383c67` / delivery `delivery_8c5943fd2820` was processed and acknowledged. Coordinator reports the production Windows serial wrapper's `flush()` may outlast `write_timeout` while queued bytes drain or stall; it routed that finding to the active deadline-only PC owner. I did not inspect the out-of-scope `operator/pc-windows-flush-probe.json`.
- Updated `product-review.md`: after accepted readiness, test actual production serial wrapper with a fake serial transport for queued-byte delay/stall, bounded completion/timeout cleanup, sequence reservation, manual event during automatic RPC/write, and source last-good retention after native timeout. The current fake-sink checks remain non-acceptance evidence.
- Exact last test: none after the previous AST-only syntax check; no PC product code was imported or executed.
- Exact next action: wait for the latest accepted PC deadline submission; then inspect only that accepted snapshot, add fake `serial.Serial` transport cases that exercise production `WindowsSerialSink.write/flush`, and run the full synthetic producer/CLI->production-C matrix.

- Added a synthetic fake-serial regression through the real `cmd_send` and production `WindowsSerialSink` wrapper: the fake transport leaves bytes queued for four seconds even though the configured write timeout is shorter; expected behavior is bounded failure, serial close, and consumed reserved sequence. This test is intentionally unrun against active PC source until deadline remediation acceptance.
- Syntax AST check exited 0. Immediate inbox check `e7ff76ba-23e9-4e4d-87b9-9f97456240b5` returned no messages.
- Exact last validation: `python -B -c "import ast; from pathlib import Path; ast.parse(Path('tests/integration/test_pc_producer_to_c.py').read_text(encoding='utf-8')); print('syntax ok')"` = syntax ok.
- Exact next action: after the accepted deadline Task arrives, check whether its serial timeout seam matches this fake transport; adapt the case if needed, then add actual bounded RPC/write latency and last-good timeout cases and run all tests.

- Updated `product-review.md` to reflect that the production-wrapper queued-byte timeout test is authored but unrun.
- Immediate inbox check `2deb1054-1004-4589-8760-10c1125da9c4` returned no messages.
- Exact last validation remains AST syntax parse = `syntax ok`; exact next action remains inspect only the accepted deadline-only snapshot after coordinator readiness, then adapt and execute the RPC/serial/manual/cache integration cases.

## PC53 accepted review started — 2026-10-09

- Current Task / Dispatch: task_4d49e747c570 / ctx_da800c8d8bce; Run run_c968c43361da; worker terminal term_1a2fcc8b-6402-4851-ba15-d27061517be1.
- Coordinator msg_bf54f604138a and follow-up msg_a9b830d95286 were processed; the latter delivery delivery_16fdaaf91a58 was acknowledged. Stable PC commit 5ddef63 and firmware 853ddf7 are approved for independent tests. Coordinator directs immediate testing/reporting and explicit failed outcome if blockers remain; UI quota low.
- Reviewed only accepted 5ddef63 with git show. Confirmed WindowsSerialSink.flush starts a daemon worker, suppresses the worker exception, returns without raising after write_timeout; CdmSender.transmit_payload therefore may report success. run_watch_loop clears a manual event after transmission even when it arrived during the already-collected write.
- First complete run of the new integration harness was 10/10 but its queued-flush fake omitted write_timeout, so that result is invalid for flush behavior. Corrected the fake. Focused rerun now fails as expected: test_production_windows_serial_flush_is_bounded_and_consumes_reserved_sequence, exit 1, cmd_send returned 0 despite the queued-byte timeout; stdout says [HOST WRITE] for seq 17.
- Exact next action: finish the real fake-serial manual-during-write regression, rerun focused flush + new integration suite, then full integration and firmware suites; update report with exact passing counts and actionable failures, final inbox check, failed worker_done if any blockers persist.

## PC remediation and selected-B integration Dispatch — 2026-10-10

- Run: `run_c968c43361da`; Task: `task_4d49e747c570`; Dispatch: `ctx_125c9c02c0ed`; worker terminal: `term_a4d53c0e-9eb2-4cae-b3ac-8a32bbb83956`.
- Scope: own only `tests/integration/`, `docs/agent-runs/orca-luna/product-review.md`, and this checkpoint. The initial inbox check returned zero messages.
- Read the cohort design, PRODUCT_CONTRACT, prior findings, existing integration harness, and accepted PC/firmware reports. The report says the manual-dispatch deadline remediation is complete; selected firmware B is `853ddf7`; previous actual C/GUI findings and accepted build evidence are preserved.
- Exact next action: inspect current production PC collector/RPC/sender/watch and firmware parser/cache/time/F9 code plus build evidence, then execute the synthetic production producer-to-C and CLI integration suite to surface any reproducible blockers.
- No PC/firmware/designer/frozen inputs, other worktrees/history, live account/session/auth, COM/reset/flash, or unowned files have been accessed or changed.

### Current accepted PC/C integration checkpoint — 2026-10-10

- Confirmed accepted firmware report/build artifacts without rebuilding: `idf.py set-target esp32s3` and `idf.py build` succeeded in the recorded ESP-IDF v5.3.2 staged checkout; SHA-256 for app, bootloader, partition table, and sdkconfig matches `docs/agent-runs/orca-sol/report.md` exactly. This is accepted build evidence, not a new build.
- First producer-to-C run: `python -B -X utf8 -m unittest discover -s tests/integration -p 'test_pc_producer_to_c.py' -v` ran 12 cases, 9 passed, 3 failed. Reproducible blockers: `WindowsSerialSink.flush()` timeout is silently ignored so `cmd_send` returns 0 while a flush worker remains blocked; a manual event arriving during an already-collected write is cleared without a post-request collection/frame. The RPC-in-flight assertion observed the event before the watch loop's post-write clear, a test synchronization race; added bounded wait for the documented coalescing behavior before rechecking.
- Exact next action: rerun the RPC/manual-write/flush cases to validate the synchronization and preserve actionable reproductions, then run C parser/session/F9 and full firmware host suites plus the corrected complete integration discovery.
- Last test result: integration producer suite exit 1 (9/12); no product files modified. No physical hardware, live account, COM, reset, flash, other worktree/history, or user session/auth data used.

- Correction from current coordinator steering: the actual worker terminal is `term_a4d53c0e-9eb2-4cae-b3ac-8a32bbb83956`; `term_54a83fa0-c831-41b9-8295-ca84d361c828` is coordinator. The earlier escalation attempt from the coordinator handle was rejected (`caller is not the Dispatch pane`) and did not deliver. Worker delivery `delivery_c7da680ff2ce` (messages `msg_31c11629e00b`, `msg_75f00c07c67b`, `msg_b82cc6647639`) was read and acknowledged using the worker handle. Coordinator confirms stable PC 5ddef63 / firmware 853ddf7, requires in-flight assertions to permit either coalescing or an extra fresh request, and says reconcile actual acquisition timestamps with current UTC. Continue against current production sources, preserve exact fails, no owner-source edits.
- Exact next action: fix only the integration harness's RPC timing/assertion and subprocess-patch lifetime, then rerun the focused cases and full suites; update terminal provenance here to the actual worker handle.

### Harness correction and focused retry — 2026-10-10

- Corrected the checkpoint terminal identity to the dispatched worker handle `term_a4d53c0e-9eb2-4cae-b3ac-8a32bbb83956`; coordinator terminal is `term_54a83fa0-c831-41b9-8295-ca84d361c828`. Coordinator steering was read and worker delivery acknowledged; no coordinator inbox was read/acknowledged.
- In `tests/integration/test_pc_producer_to_c.py`, made the in-flight RPC case use production UTC (`reference_time=None`) because fixed 2026-10-09 made real RPC acquisition appear future on 2026-10-10. Moved C host subprocess execution outside the fake `subprocess.Popen` patch. Focused RPC test now passes with an actual post-request observed_at and accepted production-C frame. The contract permits either coalescing or an extra fresh dispatch, so the test no longer requires exactly one frame or a cleared event.
- Focused retry confirms manual-during-write still fails: event arrives after snapshot acquisition; only one old frame is sent and the manual request is cleared. Bounded serial flush test still fails with return code 0 and a blocked flush worker after timeout.
- Exact next action: run current producer integration, all integration tests, full firmware host suite, and PC suite with synthetic inputs; record exact counts and review any failures.


- Final coordinator steering received and acknowledged in `delivery_d5f14e5bb465` (`msg_fc7a45c5c3fc`): escalation `msg_653f77061153` accepted; do not expand scope or repeat GUI/IDF. Finish already-planned integration/C/F9 runs, update current requirement matrix and exact counts, preserve old findings, and report failed because the two blockers persist; coordinator will route those PC fixes after this report settles.
- Latest producer integration: 13 tests, 11 pass / 2 reproducible fails (serial drain timeout and manual-during-write). New actual PC float + Unicode canonical frame passes production C; no-token error and global reset latest/source/capture/empty-default path pass production C.
- Last full suite results before these added integration cases: firmware host 18/18 pass; PC tests 53/53 pass; full integration 20 tests with 18 pass / the same 2 fails. New PC producer tests were added afterward, so rerun final full integration discovery.
- Exact next action: rerun full integration discovery once, review F9/B/navigation and legacy adapter source evidence as needed, then produce current per-C/I/F and L1-L8 matrix with precise blockers and `not_run` live limits.

- Added a single production-watch combined deadline regression (`test_manual_rpc_write_and_real_wrapper_drain_share_five_second_budget`) using the actual RPC reader, `run_watch_loop`, and `WindowsSerialSink` over a fake serial queue. It measures from manual request through delayed quota RPC and queue drain. Exact next action: run this focused timing case, then final full integration discovery; the expected failure, if any, is a real deadline miss rather than selected timeout constants.

- Combined deadline probe result: **FAIL**, 1/1. It traversed actual `run_watch_loop` → native RPC handshake/reader → production `WindowsSerialSink` and a fake serial drain; measured **5.391s** from manual request to completed queue drain, exceeding the 5.0s contract despite the sender reporting host-write success at about 1.1s after RPC response. This directly confirms the end-to-end deadline defect. No source outside integration tests/docs changed.
- Exact next action: perform the final full `tests/integration` discovery and confirm only the expected serial/manual/combined budget failures remain, then update `product-review.md` with final evidence and requirement matrix.

### Final owned integration run — 2026-10-10

- `python -B -X utf8 -m unittest discover -s tests/integration -p 'test_*.py' -v`: **22 tests; 19 passed, 3 failed**. The only failures are the known production PC blockers: combined manual RPC/write/drain **5.296s > 5.0s**, serial flush timeout returns success while background drain remains pending, and manual arrival during the already-collected write is cleared without a new collection/frame. All C boundary, selected-session, F9, PC-to-C producer semantics, actual PC float/Unicode interop, and in-flight RPC cases pass.
- `python -B -X utf8 -m unittest discover -s tests/firmware -p 'test_*.py' -v`: **18/18 passed**, including the frozen legacy evaluator's distinct **29/29** result. `python -B -X utf8 -m unittest discover -s tests/pc -p 'test_*.py' -v`: **53/53 passed**. These prior runs remain valid; only integration-owned harness changed afterward.
- Exact next action: check selected B navigation/F9/legacy actual source evidence and accepted build hash linkage, finalize current product-review matrix and checkpoint, rerun only lightweight syntax if needed, then final worker mailbox check and one failed worker_done.

### Final report artifact — 2026-10-10

- Replaced this stale review with the current independent PC/selected-B result in `product-review.md`. It contains exact runnable commands/counts, current C/I/F and L1–L8 statuses, the three reproduced PC blockers, synthetic-data boundary, old B/firmware findings and their resolution, and physical/live `not_run` gates. Current report explicitly claims no product pass.
- Build evidence correction: an earlier hash command inspected `firmware/.host-tools/final-build/`, the superseded baseline. The accepted corrected artifact directory is `firmware/.host-tools/active-usage-build/`; its app/bootloader/partition/sdkconfig SHA-256 values match the corrected report exactly. No rebuild was run.
- Exact next action: final worker-mail check, then send exactly one failed `worker_done` for Task `task_4d49e747c570` / Dispatch `ctx_125c9c02c0ed`, with only owned modified paths and this report path.

- Coordinator steering received and acknowledged: `delivery_90c70b22961b` / `msg_2f0f01b04a43`. It clarifies the combined test must not treat an out-of-band delayed callback as evidence the sender exceeded its synchronous budget: production may correctly return a bounded write failure, close, and consume sequence before physical drain. Revise the combined fake to expose realistic `out_waiting`; assert the actual production path either drains or reports failure/closes within ≤5s, with no background worker. Preserve the prior 5.296s fake callback observation only as a false-success/leaked-drain reproduction, not as the contract timing verdict.
- Exact next action: adjust only the owned combined integration test and report phrasing to reflect this distinction, run that focused case against current source, then finalize the failed report. No PC/firmware changes.

- Combined probe refinement per coordinator feedback: the prior 5.296s result timed an out-of-band fake flush sleep after the production wrapper had already returned success; it is retained only as evidence of success-before-drain, not as a valid synchronous deadline measurement. Replaced the combined test to model pyserial `out_waiting`, measure manual request through actual watch dispatch, and accept only completed drain or a bounded failure that closes/clears the queue, leaves no worker, and consumes the reserved sequence. Exact next action: run the revised focused probe, then final full integration suite.

- Revised combined probe result: **FAIL**. Manual request-to-dispatch returns within the 5s bound, but the production wrapper reports `[HOST WRITE]` while fake pyserial `out_waiting` remains nonzero; it does not complete drain or return a bounded failure and close the sink. The earlier 5.296s test timed an out-of-band callback after return and is explicitly retained only as false-success evidence, not a deadline measurement.
- Exact next action: rerun final full integration discovery against this revised combined probe, then finalize report/checkpoint and perform the last worker inbox check.

## Final evidence checkpoint — 2026-10-10

- Revised combined `out_waiting` production-watch test failed against the stable PC source because request-to-dispatch was within 5s but host success was returned while bytes remained queued; the test also verifies a bounded closed failure with consumed sequence is acceptable. The focused prior 5.296s sleep callback is retained only as false-success/worker-leak evidence, not as deadline timing.
- Final full integration discovery after all harness changes: `python -B -X utf8 -m unittest discover -s tests/integration -p 'test_*.py' -v` → **22 tests, 19 passed, 3 failed** (serial timeout/success, manual during collected write, realistic combined queue pending). Firmware host suite → **18/18**; PC unit suite → **53/53**. Legacy frozen evaluator → **29/29**, distinct from device pass.
- Corrected firmware artifact hashes are from `active-usage-build`, not the superseded `final-build`; the active app/bootloader/partition/sdkconfig hashes match the accepted selected-B report. No rebuild.
- Final files changed in this Dispatch: `tests/integration/test_pc_producer_to_c.py`, `docs/agent-runs/orca-luna/product-review.md`, and this checkpoint only. No PC/firmware/designer/frozen inputs or Git state changed. Escalation `msg_653f77061153` was accepted; coordinator will route the PC fix after this failed submission settles.
- Exact next action: final worker-mail check on `term_a4d53c0e-9eb2-4cae-b3ac-8a32bbb83956`; process any delivery, then send exactly one failed `worker_done` with these three modified paths and `docs/agent-runs/orca-luna/product-review.md` as report path.

## Same-task retry Dispatch — 2026-10-10

- Run: `run_c968c43361da`; Task: `task_4d49e747c570`; current Dispatch: `ctx_08869eb488a4`; worker terminal: `term_a4d53c0e-9eb2-4cae-b3ac-8a32bbb83956`.
- Coordinator retry message `msg_b6ec41ecf6af` was read and delivery `delivery_c44e48dbdc58` acknowledged. Prior failed Dispatch `ctx_125c9c02c0ed` remains historical evidence. Stable PC remediation is now `1c8181e`; firmware `853ddf7` unchanged. Scope remains only `tests/integration/`, this checkpoint and `product-review.md`.
- Required current checks: read current PC/CLI/serial source before verdict; retest producer-to-C; add focused regression for second manual event during an already-manual write, pure quota response acquisition, and real-time combined auto-RPC + post-request manual collection/RPC cleanup + wrapper write/drain ≤5s. Retain valid bounded failure semantics, test ordinary successful drain, then report exact final status. Do not repeat GUI or IDF work absent a concern.
- Exact next action: inspect current accepted PC commit `1c8181e` production source and existing integration test doubles; then adapt/add only owned integration tests and run the required suites. Physical/live gates remain not_run.

### Current PC remediation source review — 2026-10-10

- Inspected current `pc/sender.py`, `pc/cli.py`, `pc/quota.py`: `WindowsSerialSink.flush()` now synchronously polls `out_waiting` against the write-start deadline and raises on timeout; `run_watch_loop` leaves a manual event pending when a session source was collected before that request, but clears it after an already-manual write. Current source therefore needs two targeted tests: AUTO/session → manual fresh re-collect, and a second manual request during an already-manual write.
- Several prior `serial_module` doubles lack `out_waiting` or `write_timeout`; they no longer model pyserial and must be corrected to realistic immediate-drain or intentional-stall queues. The former out-of-band 5.296s result is not a deadline measurement.
- Exact next action: update owned fake serial behavior, add the second-manual and combined AUTO→MANUAL production watch tests, add normal successful-drain and bounded timeout assertions, then run producer/full integration suites.

### Current-implementation test update — 2026-10-10

- Adapted stalled serial test to the new synchronous `out_waiting` wrapper: expect bounded `cmd_send` failure, closed queue, consumed sequence, and no background flush worker. Added a successful ordinary-drain test which passes raw bytes to the production C receiver. Updated non-stall pyserial fakes to expose `write_timeout` and `out_waiting`.
- Added production regressions for the already-manual second request race and the full AUTO native quota request → post-request MANUAL session + quota recollection/second RPC cleanup → actual wrapper write/drain within 5s. Existing pure-quota in-flight test asserts tokenless quota acquisition is after the request and accepted by C.
- Exact next action: run focused stalled/success drain, AUTO→MANUAL, second-manual, existing manual-during-AUTO-write and pure-quota tests; adjust only test-double issues or document concrete current-source failures.

- Focused test invocation initially failed before collection with `SyntaxError` in the edited flush test: removal of its obsolete worker cleanup left `try:` without a handler. Removed the orphaned `try`; this was a harness syntax issue only, not product evidence.
- Exact next action: rerun focused serial/manual/RPC tests against accepted PC source `1c8181e`.

### Focused PC1c8181e remediation retry — 2026-10-10

- Focused command: `python -B -X utf8 -m unittest tests.integration.test_pc_producer_to_c.PCProducerToCTests.test_production_windows_serial_flush_is_bounded_and_consumes_reserved_sequence tests.integration.test_pc_producer_to_c.PCProducerToCTests.test_production_windows_serial_success_waits_for_queue_drain tests.integration.test_pc_producer_to_c.PCProducerToCTests.test_watch_manual_event_during_write_collects_new_session_before_clearing tests.integration.test_pc_producer_to_c.PCProducerToCTests.test_second_manual_request_during_manual_write_is_not_lost tests.integration.test_pc_producer_to_c.PCProducerToCTests.test_watch_manual_event_during_native_rpc_uses_result_acquired_after_request tests.integration.test_pc_producer_to_c.PCProducerToCTests.test_auto_rpc_then_post_request_manual_collection_write_and_drain_within_five_seconds -v`
- Result: **5/6 pass**. Stalled queue now yields bounded WRITE_IO_ERROR, closes/clears queue and consumes the sequence; ordinary queued bytes drain and the C receiver accepts the resulting frame; AUTO write → manual event with session source → fresh manual session/quota collection, second native RPC cleanup and real wrapper drain completes ≤5s; pure quota result acquired after request passes. Remaining failure: a second manual request during an already-manual write shares the same set Event and gets erased by the first iteration's clear; only one frame is emitted.
- Exact next action: report this concrete remaining race to coordinator, then run current `tests/pc` and full integration discovery against stable `1c8181e`.

- Current stable PC test suite independently verified: `python -B -X utf8 -m unittest discover -s tests/pc -p 'test_*.py' -v` → **57/57 pass**. This includes the new owner remediation test for AUTO in-flight write followed by fresh manual collection; my independent second-request-during-MANUAL-write test remains a separate failure.
- Focused integration command on `1c8181e`: **5/6 pass**, only `test_second_manual_request_during_manual_write_is_not_lost` fails. Bounded stalled drain (error/close/sequence), successful normal drain + C acceptance, existing AUTO-write→manual fresh session path, pure quota post-request collection, and combined AUTO remainder + second manual native RPC cleanup + actual queue drain ≤5s pass.
- Exact next action: rerun full `tests/integration` after current source/fake updates; report exact count and the second-manual-only blocker, then finalize current acceptance matrix and worker result.

- Coordinator steering `msg_4ba9059e3485` was read and delivery `delivery_6054774a0806` acknowledged. Existing AUTO→MANUAL integration test only covers a fast path; it does not test the sequential budget boundary. Add a second real-monotonic case with AUTO init/read ~0.95s each, MANUAL init/read ~0.9s each, and actual serial queue drains ~0.8s for each write; each phase remains below its own production timeout while combined work can exceed 5s. The coordinator confirms no source changes are allowed and the second-manual race was escalated.
- Exact next action: implement the permitted-stage-boundary synthetic case using two actual bounded RPC process fakes and realistic successful serial queue drain; run it separately from the fast-path case, then final full integration discovery.

### Worst-case phase-boundary probe — 2026-10-10

- Coordinator steering `msg_4ba9059e3485` was received and acknowledged earlier; current worker inbox was checked and is empty. Existing combined case remains separate fast-path evidence (AUTO remainder .7s + MANUAL RPC .2s + queue .03s).
- Exact next action: add one synthetic test through actual `run_watch_loop`, `fetch_native_rate_limits`/bounded reader and `WindowsSerialSink`, with AUTO initialize/read delays .95s each, MANUAL initialize/read .9s each, and successful per-frame serial drains .8s. Start timing when the manual event arrives during AUTO initialize; assert ≤5s and verify subprocess cleanup plus actual C frame acceptance. Then run this case and final integration discovery.

- Test milestone: the new stage-boundary case used production RPC response parsing, real `time.monotonic()`, `run_watch_loop`, the bounded reader, `WindowsSerialSink` and synthetic pyserial queue drains. It failed the 5s contract at **5.578s** while each individual configured delay stayed below its stage/write timeout; the existing fast-path combined test passed. The second-manual-during-MANUAL-write race reproduced as one frame instead of two. Both generated frames in the new boundary case were subsequently checked by the linked production C receiver after timing assertion cleanup.
- Inbox delivery `delivery_b293ffb65592` containing coordinator status `msg_6cfb90a129d2` was processed and acknowledged; it confirms no PC edits and the follow-up fix is planned after this review settles.
- Exact next action: run full integration discovery on the current tree, update `product-review.md` with current Dispatch and separate fast-path/boundary outcomes (correct stale F6 5.296s wording), then perform final inbox check and one failed `worker_done`.

- Full integration milestone: `python -B -X utf8 -m unittest discover -s tests/integration -p 'test_*.py' -v` → **25 tests, 23 pass / 2 fail**. The only failures are the phase-boundary RPC+successful-drain deadline (**5.579s > 5s**) and the second manual request during MANUAL write (only one frame); fast path and remaining C/PC/F9 cases pass.
- Coordinator follow-up `msg_7c0f4cbe03d0` was read: it identifies the distinct pure-quota event-after-acquisition/before-watch-return race and specifies a minimal wrapper around real `SharedCollectionState.collect_all` to set the Event after actual collection, then require a fresh native acquisition/second sequence. Exact next action: add that test inside owned integration file and reproduce it with two real synthetic RPC responses; then rerun full integration and update report.

### Pure-quota post-acquisition event boundary — 2026-10-10

- Added `test_pure_quota_request_after_collection_requires_fresh_native_acquisition`: production `SharedCollectionState.collect_all` performs the actual native JSON-RPC collection; a thin test wrapper sets the manual Event only after that real call returns; two synthetic server responses carry distinct quota values; actual CLI watch and fake serial are used.
- Focused result: **FAIL**, production collection count remains 1 and one MANUAL-labeled frame is sent; the already-acquired 17% quota is reused and the pending request cleared instead of a second 29% quota acquisition/sequence. Other existing AUTO-in-flight post-request test remains separate and passing.
- Exact next action: final full integration discovery after this test; then update current-dispatch report to three actual PC blockers (second request during MANUAL write, pure-quota event after acquisition, worst-case combined 5s), correct F6 timing text, and final inbox check/failed worker_done.

### Current Dispatch final report evidence — 2026-10-10

- Current full integration command `python -B -X utf8 -m unittest discover -s tests/integration -p 'test_*.py' -v` → **26 tests, 23 passed / 3 failed**. Failures: worst-case combined real RPC/write/drain **5.563s**, pure-quota Event after actual acquisition yields only one collection, and second MANUAL request during blocked MANUAL write yields only one frame. Fast AUTO→MANUAL path, synchronous bounded drain failure/close/sequence behavior, successful serial drain, C producer/parser/cache/session tests and F9 module tests pass.
- Current `tests/pc` already ran against stable PC `1c8181e`: **57/57 pass**. Accepted selected-B artifact hashes/logs and firmware host suite **18/18** (legacy frozen evaluator **29/29**, separate) were verified in the prior checkpoint; no rebuild. GUI/F9/B navigation checks remain tied to those accepted host artifacts. No physical/live claims.
- Updated `product-review.md` header to Dispatch `ctx_08869eb488a4`, current test counts and precise three blockers; removed invalid 5.296s inference and marked bounded serial timeout/success behavior passing. Escalation `msg_dcf123b5555a` sends concrete current findings to the coordinator.
- Exact next action: check worker inbox on `term_a4d53c0e-9eb2-4cae-b3ac-8a32bbb83956`, process/ack any delivery, then send exactly one failed `worker_done` for Task `task_4d49e747c570` / Dispatch `ctx_08869eb488a4` with the three owned paths and `docs/agent-runs/orca-luna/product-review.md` report path.
