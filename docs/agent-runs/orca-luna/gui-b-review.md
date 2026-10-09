# Selected B follow-up review

- Date: 2026-10-08
- Task / Dispatch: `task_0d62e820abfa` / `ctx_c9524d9d2327`
- Run: `run_c968c43361da`
- Browser: Orca page `c96626c2-be26-4498-b9eb-375e79cd472f`, `http://127.0.0.1:8289/opendesign/mockups/gemini-b/index.html`
- Result: **FAIL - F1 cache retention remains incorrect.** F2, F3, and F5 pass the selected-B browser/document checks below. This is not product or physical LCD approval.

## Acceptance results

| Finding | Result | Evidence |
|---|---|---|
| F1 - last-good cache, null/error/disconnect/stale/recovery | **FAIL** | Normal -> Error and Normal -> Disconnected retain the normal sample and `OBS: 17:10:00Z`. However, `applyState("unknown")` at `opendesign/mockups/gemini-b/index.html:909-919` and `applyState("waiting")` at lines 951-960 set `lastGoodCache.hasCache = false`. In Orca, Normal -> Unknown -> Error then reports `NO PRIOR CACHE` and renders `--`; Normal -> Unknown -> Disconnected does the same. Normal -> Waiting -> Error also loses the prior valid sample. This is a transition-path failure, not an independent cold-start case. Recovery restores the synthetic sample. Source-stale renders observation `17:04:59Z`, source age 301s and receive age 0s; direct disconnect renders source/receive ages 301s/301s and keeps the original observation time. The UI only exposes 301s, so exact equality at 300s is not independently controllable. An empty cache object injected in page memory produced `NO PRIOR CACHE`, `OBS: UNKNOWN`, and blank values; the UI has no separate cold-start control. |
| F2 - normalized/source totals and subset/account isolation | **PASS** | In the live page, changed only the in-memory synthetic `sourceTotal` to `999,999`; `TOTAL TOKENS (IN+OUT)` stayed `141,200`, while `Source Total Reported` showed `999,999`. Cached input and reasoning are labeled as included subsets. Session limit, remaining and percent stay unknown, in a region separate from account quota. The normal screenshot retains the common equal-total sample. |
| F3 - variable provider quota windows and BOOT | **PASS** | The six-window list paged through `WIN 1-2 / 6`, `3-4 / 6`, and `5-6 / 6`; next/previous wrap in both directions. The last page shows the 20h and 30-day windows. The BOOT button event cycled Usage -> Global Reset -> Status -> Usage while long-list mode remained selected. |
| F5 - transfer/performance claims | **PASS** | The corrected Gemini handoff §6.4 labels the 171KB DMA transfer and 60fps as estimates, says hardware measurements are `not_run`, and makes no guaranteed frame-rate claim. No hardware measurement was performed. |

## Browser evidence

- Loaded B at the exact 820x320 CSS LCD size on a viewer server bound only to `127.0.0.1:8289`. Default screen is Usage; the normal view shows account quota separately from session telemetry and identifies the source, observation timestamp, units, included subsets, and unknown session quota fields.
- Global Reset via BOOT shows `CODEX-RESETS.COM`, last reset `2026-10-07 10:00:00Z`, capture `2026-10-07 17:10:00Z`, elapsed `7h 10m`, and worldwide scope independent of personal quota. Status is the third BOOT screen.
- Text-range geometry checks found no text outside the 820x320 LCD in normal, source-stale, disconnected, unknown, error, waiting, recovery, global-reset, or status views. The smallest measured Usage text is 8.5 CSS px (9px on global/status); the small footer is visible in the screenshot but physical readability remains `not_run`.
- The page's browser resource list was empty; the preview has no external runtime/font dependency. `opendesign/screenshots/selected-b/B-swiss-studio-meter-normal.png` is a new 820x320 crop of the corrected normal view. The original six screenshots remain separate.
- Orca's `click --element` reported a click on Next Win without changing the page; calling the actual page button's `.click()` through Orca `eval` dispatched its event and paged correctly. BOOT was likewise verified by firing the page button's real click event, not by claiming GPIO behavior.

## Regression checks

- `python docs/design/lcd/gemini/regression-check.py` exited 0. It is not a behavioral regression test: its HTML checks assert source strings, and `simulate_javascript_f1_state_machine()` constructs a separate Python dictionary rather than executing Candidate B JavaScript. The live browser failure above contradicts its F1 success message.
- `python tests/integration/design-check.py` exited 0. It passes B geometry/data/state/BOOT/offline checks and the shared gallery artifacts; its remaining findings are for comparison-only A/C fixed windows and C source-total labeling plus E/F copied titles. No compatibility change to this shared checker was justified.
- The OpenDesign manifest was rebuilt from a full scan: six mockup HTML files across the existing A-F groups and zero design-system files.

## Required follow-up

Keep the last-good cache for the same source context when rendering Unknown/Null or Waiting placeholders; do not turn a prior valid observation into a cold-start no-cache case. Keep a genuinely empty-cache case separate and verify both paths by exercising the actual B JavaScript: Normal -> Unknown -> Error/Disconnected must retain the prior values and observation time, while a cold Error/Disconnected with no prior sample must show `NO CACHE` and `--`. Add explicit 299/300/301-second source-age cases with independent receive age. The designer regression check must execute those JavaScript transitions instead of simulating them in Python.

Route minor cleanup with this follow-up: `opendesign/mockups/gemini-b/index.html:999` has trailing whitespace, and `docs/design/lcd/gemini/handoff.md` ends with two line breaks. No designer or handoff file was edited in this review.

No COM, real account session, auth file, account RPC, frozen input, other worktree, Git history, or device was accessed. Physical LCD readability, GPIO0 operation, transfer rate, frame rate, and power remain `not_run`.

The initial six-candidate review remains at [gui-review.md](gui-review.md). The original and follow-up screenshots are linked from [comparison.html](../../../opendesign/comparison.html).

## Corrected-B retry — 2026-10-09

- Task / Dispatch: `task_0d62e820abfa` / `ctx_fbf6b4c142f4` in `run_c968c43361da`.
- Dependency: the Gemini correction was submitted before this retry. The first 2026-10-08 F1 failure above remains as historical evidence; this section records the independent post-correction result.
- Result: **PASS for the selected B browser/design checks.** This is not product or physical LCD approval.

| Original finding | Retry result | Current evidence |
|---|---|---|
| F1 — last-good cache and state paths | **PASS** | On the actual B page, Normal → Unknown → Error and Normal → Waiting → Error retain the internal cache and restore input `124,800`, output `16,400`, totals `141,200`, and original `OBS: 17:10:00Z`. Normal → Unknown → Disconnected restores the same values and timestamp, with source age `301s` and receive age `301s (Timeout)`. Recovery restores the valid sample. The cold Error/Disconnected controls render `NO CACHE` and `--`; I also set an empty cache object in page memory and exercised the generic Error/Disconnected branches, which both displayed `NO CACHE`, `--`, and `OBS: UNKNOWN`. This memory-only setup was restored to Normal afterward. The designer check asserts the explicit cold-state displays after cached scenarios; the live empty-cache run supplies the separate conditional-path evidence. |
| F2 — normalized/source total, subsets, and quota separation | **PASS** | In the live page, an in-memory synthetic `sourceTotal` of `999,999` left `TOTAL TOKENS (IN+OUT)` at `141,200` and showed `999,999` under `Source Total Reported`. Cached input and reasoning are labeled included subsets; session limit, remaining, and percent are unknown, while account quota is separately labeled. No absolute session quota is shown. |
| F3 — variable windows and BOOT | **PASS** | Long-list pages exposed all six windows as `WIN 1-2 / 6`, `3-4 / 6`, and `5-6 / 6`, including `60m`, `24h`, `20h`, and `30 Days`; next and previous controls wrapped correctly. Clicking the actual preview BOOT button while long-list mode remained selected cycled screen indices `1 → 2 → 0`. |
| F5 — transfer/performance claims | **PASS, hardware not_run** | Handoff §6.4 calls the 171KB transfer and 60fps unmeasured estimates, marks hardware measurements `not_run`, and makes no guaranteed frame-rate claim. |

### Browser and regression evidence

- Orca loaded corrected B from `http://127.0.0.1:8289/opendesign/mockups/gemini-b/index.html`; the server listener was `127.0.0.1:8289`. The LCD element measured exactly `820×320` CSS px at devicePixelRatio 1, with default screen Usage. Normal labels separate `ACCOUNT QUOTA WINDOWS` from `SESSION TELEMETRY`, label the source total and observation time, and identify token units by row. Global Reset shows `SOURCE: CODEX-RESETS.COM`, reset `2026-10-07 10:00:00Z`, captured `2026-10-07 17:10:00Z`, elapsed `7h 10m`, and worldwide scope; Status shows separate Source Age and Receive Age labels.
- Source-age checks showed `299s (Available)` / `0s Fresh` / observation `17:05:01Z`, `300s (Stale)` / `0s Fresh` / `17:05:00Z`, and `301s (Stale)` / `0s Fresh` / `17:04:59Z`. Warning display was hidden at 299 and visible at 300/301. Receive-disconnect behavior was also checked at source/receive ages `301s` / `301s (Timeout)`.
- Text-range bounds were checked in all three screens for 11 states (33 state/screen combinations): normal, unknown, waiting, error, disconnected, both cold states, 299/300/301 stale boundaries, and recovery. No text range exceeded the `820×320` LCD; the smallest measured text was `8.5 CSS px`. This is geometry evidence, not physical-distance readability.
- The actual page resource list contained no external URLs. A separate `820×320` normal-state crop of the corrected page is [B-swiss-studio-meter-normal-2026-10-09.png](../../../opendesign/screenshots/selected-b/B-swiss-studio-meter-normal-2026-10-09.png); the earlier follow-up image and six initial PNGs were preserved.
- `python docs/design/lcd/gemini/regression-check.py` exited 0. It now extracts and executes B's inline JavaScript in a Node VM with a simulated DOM and asserts cache transitions, cold-state display, F2 common totals, F3 paging/BOOT, and 299/300/301 boundaries.
- `python tests/integration/design-check.py` exited 0. Its remaining findings concern comparison-only A/C fixed windows, C's missing source-total label, and E/F copied titles; no change to the shared checker was needed.
- The manifest was rebuilt by scanning the existing mockup and design-system directories: six mockup HTML files across A–F and zero design-system files. The original `gui-review.md` and six initial normal PNGs remain unchanged.

Physical LCD readability, GPIO0 behavior, transfer rate, frame rate, and power remain `not_run`; no COM, live account/session, auth, account RPC, PC/firmware, frozen-input, other-worktree, or Git operation was performed in this review.
