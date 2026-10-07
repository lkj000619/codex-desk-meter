# Sol 6.1 LCD candidates D / E / F

Design artifact handoff. User selection is pending; firmware/PC implementation, preview hosting and independent verification belong to the coordinator's other Orca Tasks.

| Provenance | Value |
|---|---|
| Run | `run_c968c43361da` |
| Task | `task_871ad3d94f9f` |
| Dispatch | `ctx_43a32c7bf49d` |
| Worker | `term_6be2e33f-de19-49ee-851d-54cc709c4938` |
| Requested model | `gpt-6.1-sol`; effective launch argv/model confirmation is coordinator-owned and not independently inspected here |
| Pinned design skills | `tools/opendesign/skills/opendesign/SKILL.md`, `tools/opendesign/skills/frontend-design/SKILL.md` |
| Upstream revision | `cecd9bb6b59408cb96a3974449b8e6ef9f5b17bb` |
| Intake | Desk LCD owner; fresh implementation; 820×320; no brand; diverse composition; three readable, hardware-feasible interactive HTML candidates |

The task overrides upstream intake questions, designer-spawned setup/preview/verifier agents and global manifest writes. No shared viewer or manifest was edited. These single files use local font names and native JavaScript only; no dependency, network, CDN, font download or product service is required.

## Choice and purpose

All three serve the same job: read account quota and independent session tokens at a glance, then use BOOT to inspect global reset and data trust.

| Candidate / file | Tone and memorable difference | Strength | Tradeoff |
|---|---|---|---|
| **D / Signal Board** — `opendesign/mockups/sol61-a/index.html` | Severe industrial instrument. Two quota percentages dominate the left; session total and a vertical ledger occupy the right. Dark neutral field with mint. | Both quota windows and every token component are visible together. Familiar reading order. | Session total is smaller than quota. Metadata is dense. |
| **E / Session Ledger** — `opendesign/mockups/sol61-b/index.html` | Warm editorial ledger. Exact session total leads; input/output and included subsets form two ledger rows. Quotas stack in a narrow right column. Light neutral field with green. | Clearest session emphasis; no abbreviation hides token counts. | Quota figures are smaller. Light display may need lower physical backlight in a dark room. |
| **F / Window Atlas** — `opendesign/mockups/sol61-c/index.html` | Focused instrument. One oversized quota window sits beside an indexed rail; a full-width session strip sits below. Dark neutral field with amber. | Largest remaining percentage and explicit selected-window context. | Seeing the second quota requires one held-BOOT action. Token metadata is compact. |

No logo, illustrations, texture assets, gradients, alpha layers, shadows or animation occur inside the LCD. Differences include composition, reading order, quota capacity per page, token placement and global-reset composition.

## Common synthetic data and meaning

The original reference is `2026-10-07T17:10:00Z` / 08 Oct 2026 02:10 KST. All three use the exact common sample:

| Scope | Values | Original source/time |
|---|---|---|
| Account quota / primary | duration 300 min = 5h; **42% used, 58% remaining**; personal reset `2026-10-07T18:20:00Z` / 08 Oct 03:20 KST | app-server `account/rateLimits/read`; observed `2026-10-07T17:10:00Z` |
| Account quota / secondary | duration 10080 min = 168h; **18% used, 82% remaining**; personal reset `2026-10-12T17:10:00Z` / 13 Oct 02:10 KST | Same response observation |
| Session telemetry | input **124800**, output **16400**, cached input **89600**, reasoning output **2300**, source total **141200** | Synthetic `token_count` metadata; event observed `2026-10-07T17:10:00Z` |
| Global reset | latest reset `2026-10-07T10:00:00Z` / 07 Oct 19:00 KST; elapsed **7h10m** at reference | **codex-resets.com**; captured `2026-10-07T17:10:00Z` |

Session headline is input + output = **141200 tokens**. Cached and reasoning are already included subsets, marked `*`; they are not added again. Source total is separately labeled and preserved. Session limit, absolute remaining and percentage are **unknown**. Account remaining percentage is only `100 - used_percent`; there is no fabricated absolute account token balance and no session/quota aggregation.

Window labels derive from duration, rather than assuming a fixed primary/secondary meaning. `168h window` is the common weekly duration; a different duration stays different. Personal reset times never appear as global reset data. The global view displays observed elapsed and explicitly says it is not a forecast.

## Interaction and variable lists

- External **BOOT · next screen** cycles **Usage → Global reset → Status → Usage**. It never refreshes, changes account usage or resets the device.
- External **BOOT hold · next windows** advances the usage window group; **Previous windows** is a preview convenience. F shows one window per group, D/E two. All wrap without dropping records. The selected group survives a three-screen cycle.
- The external list selector offers the common two windows and a **navigation stress** list of six synthetic IDs. Stress entries repeat the two supplied metrics, alternating durations, with no new measurement or sum. The same paging code renders either list; page counts are derived from list length.
- On hardware, propose one held BOOT event after 800ms for the next group, suppressing the release's short-press event. A debounced short press cycles screens. Exact GPIO/debounce behavior is firmware-owned; switching within the contract's 300ms after a recognized short press is `not_run` here.
- ArrowRight on the page body cycles screens; it is ignored while a select/button/input has focus. Controls have visible keyboard focus and 44px minimum height. There are no buttons, touch targets or clickable controls inside the 820×320 LCD.
- Final renderer must traverse the received provider/window list, retain selection by identity where possible and show page position. Provider/profile labels belong to the currently selected group; no account quota may be duplicated into each session and summed. The preview's single provider is the common Codex sample, not a product constraint.
- PC manual refresh is collector re-collection. It is not a BOOT action; no fake refresh button or device ACK is represented.

## State and provenance presentation

The external scenario selector controls eight isolated cases. Changing it resets the synthetic scenario's reference, not a real clock or capture; this is stated outside the LCD. A transition to Recovery is a replay of the original sample, not a claim that a later source fetch occurred.

| Scenario | Transformation | Display and retention |
|---|---|---|
| Normal | Original timestamps; now and receive time 17:10:00 UTC | AVAILABLE, source age 0s, receive age 0s |
| Source stale / receive fresh | Source observations/capture become 17:04:59 UTC; now and receive remain 17:10:00 UTC | SOURCE STALE, source age **301s**, receive age **0s**; values remain known; a fresh receive cannot clear source staleness |
| Receive stale / disconnected | Original captures and receive 17:10:00 UTC; scenario now 17:15:01 UTC | DISCONNECTED / STALE; both ages **301s**; last-good values and original times remain visible |
| Unknown / null | Quota used/reset, all session components, latest global reset become null; observation is still known | UNKNOWN; `--` in place of values, unknown bar drawn as an outline; no percent or token total inferred; global default says no reset record |
| Quota error / last-good | HTTP 500 on quota adapter; now 17:11:00 UTC; original observations and receive unchanged | QUOTA ERROR / LAST GOOD; 42/18% used and original 17:10 last-good retained; session/global remain available; both ages 60s |
| Initial WAITING | No validated frame; all values and observation/receive/last-good timestamps null | WAITING; no zeros, fake times or stale success values; global default remains usable |
| Recovery / same sample replay | Original sample at original reference; valid sample state restored | RECOVERED / REPLAY; error clears; no invented capture |
| Global no new record / last-known | latest=null; last-known=original latest reset | LAST-KNOWN RESET; elapsed still 7h10m; source and captured time stay visible |

The status screen labels each of **Account / Session / Global**, its source, **SRC AGE**, **RX AGE** and state. It shows original observed/captured, last-good and receive times, plus the failure/waiting/replay reason. Times are UTC in the status detail and KST in usage/global, with explicit zone labels. Display precision is one minute; exact RFC3339 seconds remain in the sample. Usage includes original observation plus both ages in its footer. Global includes source, capture and both ages. Colors reinforce explicit text; color alone never carries state.

Stale boundary is **age ≥300s** for source and receive independently. Tests exercise 299 and 300 seconds. UI age in this fixed preview does not continuously tick. Firmware must relate source UTC to its reference and then use monotonic elapsed for receive age; uncertain time bases remain unknown.

The common sample has identical account/session/global observation times. This does not authorize merging these time fields in firmware: source timestamps and per-adapter last-good/error states remain independent.

## Landscape coordinates and typography

All rectangles are `(x, y, width, height)` in LCD pixels, origin top-left, **820×320**. Shared header `(0,0,820,44)`, content `(20,44,780,230)`, footer `(20,280,780,32)`. The surrounding bezel, controls, title and synthetic notice are outside this region.

| Region | D / Signal Board | E / Session Ledger | F / Window Atlas |
|---|---|---|---|
| Quota | Two columns `(20,52,226,222)` and `(266,52,226,222)` | Right column `(520,52,280,222)`, inset 20px; two stacked 103px rows and 8px gap | Rail `(20,44,188,156)`; selected window `(228,52,572,148)` |
| Session | `(512,44,288,230)`, 20px left inset | `(20,44,480,230)` | Bottom strip `(20,206,780,68)` |
| Quota percent | 64px; top y96 | 44px; first top y71, second y182 | 96px; top y76 |
| Session total | 34px | 64px | 28px |
| Global elapsed | Left 420px column, 80px type | Right 460px column, 68px type; observed reset leads at left | Left 480px column, 88px type |
| Global observed reset | Right 340px column, 28px | Left 300px column, 36px | Right 280px column, 24px |
| Metadata and labels | 14/16/20px; 12px column headings | 12/14/16/18px and 20px state summary | 12/14/16/18/20/22px |

Usage percentages use rectangular 10px tracks; unknown uses an empty dashed outline and `--%`, never a 0% fill. Error/disconnected last-good percentages keep their numeric value. Lists page explicitly, rather than clipping a list off-screen.

### LCD font handoff

Browser D/F uses installed **Courier New**; E uses installed **Trebuchet MS** for prose and Courier New for numbers. These are offline preview surrogates, not firmware assets. Exact browser-to-LCD glyph parity is **not verified**. All LCD copy is ASCII, including `--`, `>=300s` and numerals; outside-LCD prose may use Unicode.

Target the actual LCD with **LVGL raster glyph masks**, using a Montserrat ASCII subset at body sizes 12/14/16/18/20/22/24/28/36 as needed for the selected candidate, and numeric-only masks at its exact large sizes. Manufacturer indexed raw `09_FactoryProgram/components/ui_bsp/generated/setup_scr_screen.c` references `lv_font_montserratMedium_30`, `lv_font_montserratMedium_31` and `lv_font_Alatsi_Regular_21`; this confirms the raw demo's glyph-font approach, not availability of every requested size in the new firmware. Existing 30/31px assets may serve a revised 30/31px scale only after fitting the coordinates; they are not silently stretched to 96px.

For faithful sizing, selected large sets are D **34/64/80**, E **44/64/68**, F **28/88/96**. Restrict large glyphs to `0123456789,%hm -` plus any required elapsed separator. Body font maximum glyph widths, line heights and date/source widths must be measured in the actual font build. Fit without ellipsis; if a long provider/window label does not fit, use explicit identity/detail paging rather than silently cutting it. No full Korean/CJK atlas is needed for these English LCD candidates.

Use 4bpp glyph coverage blended directly into RGB565, or 1bpp masks if the selected design accepts harder edges. Atlas generation and link-map size are firmware work **after user selection**; no font asset/build is claimed here. A conservative **384KiB Flash cap** for the selected candidate's subset fonts is a design budget, not a measured build size. Glyphs stay in Flash; do not cache three screens as bitmaps or rasterize browser fonts on the ESP32.

## Actual RGB565 palettes

LCD CSS tokens are rounded to nearest RGB565 channel levels, then expanded to sRGB, so these hex values and 16-bit codes describe the same quantized palette. Conversion: nearest `r×31/255`, `g×63/255`, `b×31/255`, then `(r5<<11)|(g6<<5)|b5`. Status accents replace the normal accent on stale/disconnected/error. Rule colors are separators, not text.

| Token | D: expanded hex / RGB565 | E: expanded hex / RGB565 | F: expanded hex / RGB565 |
|---|---|---|---|
| Background | `#101010 / 0x1082` | `#efefe6 / 0xEF7C` | `#191819 / 0x18C3` |
| Foreground | `#efefef / 0xEF7D` | `#212021 / 0x2104` | `#efefe6 / 0xEF7C` |
| Metadata | `#adaead / 0xAD75` | `#525152 / 0x528A` | `#bdbeb5 / 0xBDF6` |
| Normal accent | `#94d7c5 / 0x96B8` | `#296952 / 0x2B4A` | `#e6c67b / 0xE62F` |
| Rule | `#5a595a / 0x5ACB` | `#94928c / 0x9491` | `#6b6963 / 0x6B4C` |
| Stale/disconnected | `#f7c66b / 0xF62D` | `#8c5100 / 0x8A80` | `#f7ce84 / 0xF670` |
| Error | `#f78a84 / 0xF450` | `#ad3929 / 0xA9C5` | `#f79a94 / 0xF4D2` |

Analytical sRGB contrast against background: D foreground **16.55:1**, metadata **8.55:1**; E **14.04:1 / 6.83:1**; F **15.31:1 / 9.44:1**. Every foreground/metadata/normal/stale/error text token exceeds **4.5:1** after quantization. This calculation does not measure panel gamma, viewing angle or physical desk readability.

## Board and drawing costs

Hardware source: `docs/hardware/version-2-capabilities.md` and its indexed manufacturer source. ESP32-S3R8, 16MB Flash, 8MB Octal PSRAM, ST7701 RGB565; portrait physical panel 320×820 and landscape product coordinates 820×320. The raw SDK is ESP-IDF v5.3.2. Renderer rotation/stride and PSRAM allocation need firmware validation; orientation is not proven by this HTML.

| Budget / work | Amount or rule |
|---|---|
| Single RGB565 framebuffer | **820×320×2 = 524800 bytes** (~512.5KiB), PSRAM |
| Optional two buffers | **1049600 bytes** (~1025KiB); allocate only if measured tearing/driver requirements justify it |
| Extra packed scanline, if required | **1640 bytes**; no second whole-screen staging surface required by the design |
| Selected subset fonts | Flash budget **≤384KiB**, actual font data/link size **not_run** |
| Preview byte size | Each standalone HTML approximately 17–20KiB; not an embedded executable/memory measurement |
| Screen/page transition | Repaint the existing whole framebuffer; no transition animation or old-screen bitmap |
| Numeric/source update | Clear and redraw changed region: quota, session, global or status rectangle above |
| Age tick | Text-only dirty rectangle; do not repaint the whole screen solely for a clock tick |
| Render CPU/FPS | **unknown / not_run**; full pixel scan and glyph compositing must be profiled on the selected firmware |

Rectangle fill, thin lines and glyph masks cover the LCD. CSS Grid is authoring notation, not a firmware requirement. No blur, compositing tree, network request, video, image assets or continuously running animation is needed.

Backlight is **GPIO6 active-low**; retain a brightness tuning control because physical comfort and contrast are unmeasured. **BOOT is GPIO0 active-low with pull-up and shares LCD CS**: firmware must finish/release LCD initialization control before runtime button input; no pin configuration or timing assumption was tested here. RST is system reset. Holding BOOT across reset can enter ROM download mode and is outside the normal navigation design. This worker opened no COM port, uploaded nothing and performed no reset.

## Verification and next owner

Runnable check: `node docs/design/lcd/sol61/check.mjs`. It executes each real inline script in Node's VM using minimal mocked controls and asserts the common sample, all eight cases across all three screens, forward/backward/wrapped paging, source-vs-receive age, 299/300s boundaries, null rendering, last-good time retention, global fallback, keyboard focus behavior and lack of network dependencies. It does not emulate CSS or a browser rendering engine.

Latest behavior run: **three PASS lines, exit 0**. Final exact file hashes and run are recorded in `checkpoint.md`. RGB565 contrast calculation also passed for every text palette token.

- Coordinator / independent verifier: start the preview server, integrate the shared viewer/manifest, create thumbnails, examine every state and list page for clipping and readable hierarchy at actual 820×320; render/font/visual results remain **not_run** here. No designer self-screenshot/visual audit was performed, following pinned OpenDesign's separate-verifier workflow.
- User: select one of the six total candidates (three other-model candidates are outside this task).
- Firmware owner, after selection: generate/finalize glyph assets, map rectangles to the LCD renderer, validate GPIO0 BOOT handling and timing, rotation, memory, error retention and real panel readability.
- Coordinator: perform owner-only account and COM/hardware tests. Browser behavior alone is not product completion.

No unresolved material question was discovered; no Orca ask ID exists. Nothing outside the three candidate directories and this role's documentation directory was modified.
