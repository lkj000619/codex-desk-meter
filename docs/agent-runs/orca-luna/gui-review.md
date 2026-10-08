# Independent LCD GUI review

- Run: `run_c968c43361da`
- Task / Dispatch: `task_c0ecb13ae179` / `ctx_35a7c601f1d6`
- Review status: browser review complete; the user selected B (Swiss Studio Meter) for follow-up. This is not product approval; physical LCD behavior is `not_run`.
- Coordinator route: B findings F1-F3 and the unmeasured transfer estimate F5 are being sent to the Gemini designer. This review preserves the submitted screenshots and records comparative A/C and E/F observations without changing designer files.
- Inputs: `experiments/orca-harness-20261008/design-brief.md`, the selected cohort requirements in `docs/design/2026-10-08-orca-harness.md`, `docs/agent-runs/orca-luna/requirements-review.md`, and both designer handoffs.

## Method and evidence

Used the pinned `tools/opendesign/skills/run-opendesign/SKILL.md` viewer at `http://127.0.0.1:8289/opendesign/`. The server listener was verified at `127.0.0.1:8289`. Each standalone candidate was opened in the Orca embedded browser; its LCD element measured exactly 820×320 CSS px at device scale 1. The six normal-state screenshots were cropped to those element bounds from browser screenshots:

- A: `opendesign/screenshots/A-gemini-telemetry-matrix.png`
- B: `opendesign/screenshots/B-gemini-swiss-studio-meter.png`
- C: `opendesign/screenshots/C-gemini-industrial-field-gauge.png`
- D: `opendesign/screenshots/D-sol-signal-board.png`
- E: `opendesign/screenshots/E-sol-session-ledger.png`
- F: `opendesign/screenshots/F-sol-window-atlas.png`

Changed each candidate's state selector and checked normal, stale, disconnected, unknown, error, waiting and recovery; D–F also expose last-known global reset. The rendered text-element bounds stayed inside the LCD in the checked states. Every candidate's browser resource list was empty after load. State selectors were operated through Orca; the embedded browser's `click --element` command returned success but did not dispatch the BOOT event, so BOOT was checked by calling the actual page button's `.click()` and verifying the rendered screen sequence.

The common sample appears in all six normal views: 42%/58% primary quota, 18%/82% weekly quota, input 124,800, output 16,400, cached input 89,600, reasoning output 2,300, and 141,200 input-plus-output tokens. The candidates keep account quota and session telemetry in separate regions. D–F explicitly show the source total beside the input-plus-output total. B and C show a single session total without a separate source-total label (see F2).

## Findings for coordinator routing

| ID | Candidate / evidence | Issue and recommended route |
|---|---|---|
| F1 | B: `opendesign/mockups/gemini-b/index.html`; reproduced in the external state selector with `Normal → Unknown → Error` and `Unknown → Disconnected`. A/C show the same comparative behavior. | B's error/disconnect messages say last-good is retained, but the LCD continues to show `--` values after Unknown. The coordinator is routing this selected-design finding to the Gemini designer for a clean scenario reset or explicit, tested cache-transition semantics. Recovery restores the sample. A/C are comparison evidence only in this Task. |
| F2 | B: `gemini-b/index.html` shows `TOTAL TOKENS`; C: `gemini-c/index.html` shows `SESSION METADATA` and one total. | B does not separately label `source_total`; the common source total happens to equal `input + output`, so the screen cannot show a future mismatch. The coordinator is routing the selected B presentation decision to the Gemini designer. A/C remain comparative evidence; A labels its headline as source total but does not show a distinct normalized total. |
| F3 | A–C: static two-window quota layouts and no list selector or paging controls; their Gemini handoff dirty rectangles also describe the fixed two-window layout. | The brief says a fixed one- or two-window renderer must not become the final contract. The coordinator is routing B follow-up to preserve variable provider/window iteration and explicit paging in the selected firmware design; this preview does not demonstrate it. A/C are comparison evidence only in this Task. |
| F4 | E and F: actual browser `document.title` remains `D · Signal Board · LCD exploration`; visible candidates are Session Ledger and Window Atlas. | Comparative metadata issue recorded for coordinator awareness; no E/F changes are in scope for this selected-B review. |
| F5 | `docs/design/lcd/gemini/handoff.md` §6.4: 85,920 pixels / about 171KB for a dirty rectangle is followed by “60fps possible.” | Treat this as an unmeasured estimate. The handoff has no measured transfer rate or renderer profile; the coordinator is routing the claim for correction or validation on selected firmware. |

## Browser interaction results

- A–C and D–F cycled Usage → Global reset → Status → Usage when the page BOOT event was fired. Global views identify `codex-resets.com`, show the reset and capture times, and distinguish global elapsed time from personal quota resets.
- D–F show `Source age 301s / receive age 0s` in source-stale, and `301s / 301s` in receive-stale/disconnected. Error retains the common sample with its original observation time; recovery replays the original sample. Unknown removes numeric values; WAITING uses `--` (D–F) or `...` (A–C).
- D/E list stress mode paged 1–2/6 → 3–4/6 → 5–6/6 → 1–2/6; Previous wrapped back to 5–6/6. F paged one window at a time and wrapped 6/6 → 1/6. The D selected group survived a full BOOT cycle.
- `python tests/integration/design-check.py` exited 0. It checks dimensions, common sample, state controls, BOOT controls, offline resource references, screenshots, manifest and comparison links; its `FINDING` lines correspond to F2–F4 and A–C's fixed-window limitation.

The shared comparison is [opendesign/comparison.html](../../../opendesign/comparison.html). Browser rendering does not establish physical font readability, LCD clipping under firmware fonts, panel contrast, GPIO0 behavior, memory cost, transfer rate, or device success.
