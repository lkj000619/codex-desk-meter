# AGY first-pilot prepared-run verification — 2026-09-26 KST

## Result

The first AGY pilot is prepared. The run is
`C:\Espressif\benchmark-runs\20260925-antigravity-cli-agy-flash-medium-r01`.
Its manifest status is `prepared`; `started_at` and `ended_at` are null.
No AGY model prompt, firmware flash, or erase was performed by this verification.

| Check | Observed result |
|---|---|
| Frozen baseline | `benchmark-v2-baseline-20260925` resolves to `eef278013428a79c29d6b9456018049af149ca61`; separate checkout `C:\Espressif\benchmark-baseline-20260925` was clean. |
| Input check | `benchmark.py check` exited 0 with `inputs_valid`, profile SHA-256 `843a2cce0310b710e166de60cd3a4b5b651d88e06550f88f2f4552c6f6474f5e`, bundle SHA-256 `f7cfc546acac458c7691c10ccb776c20f5078ca141d353f1086fb808fe810948`. |
| Prepare | `new-experiment-run.ps1 -Baseline benchmark-v2-baseline-20260925 -Profile experiments/config/verified-profiles-candidate/agy-gemini-3.8-flash.candidate.json -RunRoot C:\Espressif\benchmark-runs -Seed 20260925 -Phase pilot -Port COM3` exited 0 and created the run above. |
| Manifest/receipt | `validate_preflight_receipt` passed against the actual run manifest, saved profile, and six evidence hashes. Manifest base commit/profile/bundle hashes matched the checked values. |
| Host and hardware preflight | On the frozen checkout, `check-experiment-preflight.ps1 -RequireHardware -Port COM3` exited 0: 92 tests passed; 0 failures, 0 warnings; checkout clean. |
| COM3 access | With ESP-IDF 5.3.2 activated, `python -m esptool --chip esp32s3 --port COM3 chip_id` exited 0 on 2026-09-26, opened COM3 exclusively, and identified ESP32-S3 rev v0.2 with 8 MiB PSRAM. The user separately confirmed the board is Waveshare ESP32-S3-LCD-3.16. Repeat port check immediately before actual run or flash. |
| Recovery images | Current-state 16 MiB backup SHA-256 `ba234a8044e5174ef0275f99b89573a78a6ce62d70b62196720b0ad83d8e532b`; historical factory 16 MiB backup SHA-256 `aa51ba15b975ec2e564506e609729f36d85da23d8892023396a700846955a1e6`. Both still exist outside Git and hashes were rechecked. |
| AGY global files | Original settings SHA-256 `a9e7b57b56bb0225448a7068f18264ca3056c5a3c0ee49114f37bf4292ee0d48`, global instruction SHA-256 `12552a5e4b15f1b272fbd85c865e2457f7b045c69136ed9c7731d23314edc512`, hooks SHA-256 `90d1b998102ca61fac85e85ece8597a264791339135820b20ccb6e5bddfc0c2e` matched originals; no active wrapper lock or AGY process remained. |

The first `python -m esptool` retry used the benchmark Python interpreter without
ESP-IDF activation and failed with `No module named esptool`. Activating the
pinned environment and repeating the same non-writing command resolved that
environment selection error; the successful output above is the hardware check.

The 2026-09-18 conditional approval covers one pilot per selected model entry,
and the later Q3 decision selects `antigravity-cli / gemini-3.8-flash-medium`
with COM3 hardware option A. The baseline, profile, receipt, preparation, and
hardware prerequisites for this AGY slot now have evidence. The actual launch
must repeat time-sensitive COM3 exclusivity and record R10 activation against
this run before handing off the one-shot prompt. Model entitlement, Windows
tool-rule matching, stream/usage, soft denials, candidate firmware, and product
behavior are first-pilot observations, not pre-pilot success claims.
