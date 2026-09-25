# AGY pilot-entry environment evidence — 2026-09-25 KST

This record covers local preparation. No model prompt, pilot, flash write, or
`erase_flash` was executed. The selected target remains
`antigravity-cli / gemini-3.8-flash-medium`.

## Scoped AGY configuration

- Installed AGY CLI: `1.2.11`; `agy models` listed the selected model while the
  scoped settings were active. Model listing is not inference entitlement.
- Original global `settings.json` SHA-256:
  `a9e7b57b56bb0225448a7068f18264ca3056c5a3c0ee49114f37bf4292ee0d48`.
  It contained 114 allow rules and `allowNonWorkspaceAccess=true`.
- Original global `GEMINI.md` SHA-256:
  `12552a5e4b15f1b272fbd85c865e2457f7b045c69136ed9c7731d23314edc512`.
  Original global `hooks.json` SHA-256:
  `90d1b998102ca61fac85e85ece8597a264791339135820b20ccb6e5bddfc0c2e`.
  Both are temporarily absent in the pilot scope, then restored byte for byte.
- `mcp_config.json` had zero servers; no custom global skill directories were
  present. Earlier `agy mcp list`, `agy plugin list`, and `agy agents` inventories
  were empty. The wrapper rechecks skills and MCP before every invocation.
- The selected [allow policy](../../../experiments/config/agy-pilot-permissions.json)
  SHA-256 is `a046cfa637e99ca27a6b7f2f6da22e60d9192af3105441f73a7d6b6af4db9384`.
  Active settings immediately before `agy models` had SHA-256
  `a00210cd5ee167f72417b52a04e507b51daa9d9ae6cf1358c17177bae6b5e981`.
  The wrapper replaces the 114-rule list, sets workspace-only file access and
  `request-review`, and disables auto-update for the child. The runner refuses
  AGY launch unless the scoped state is active.
- First `agy models` scope run surfaced AGY sparse settings persistence: AGY
  omitted `allowNonWorkspaceAccess=false` and `toolPermission=request-review`
  from the file. The wrapper stopped automatic restore, the remaining keys and
  allow list were reviewed, and the original files were manually restored.
  The wrapper now accepts only omission of these documented defaults; the
  second scoped `agy models` run exited 0 and restored the originals. After
  that run all three original hashes above matched and no active lock remained.

The scope has been tested with metadata commands, not with model tool calls.
Actual Windows command matching, `init.permission_mode`, soft-denial, model
entitlement, and usage remain first-pilot observations. Raw stdout and stderr
must be reviewed before `pilot_pass=true`.

## Host preflight

- `check-experiment-preflight.ps1 -RequireHardware -Port COM3` ran on a clean
  `804a3001069c47eb744e091ea60a6b352beb3b96` checkout: 0 failures, 0
  warnings, ESP-IDF v5.3.2, 88 offline tests, valid example and matrix, COM3
  USB serial status OK. This was before the new wrapper files were added.
- The same full preflight ran again on clean final baseline
  `eef278013428a79c29d6b9456018049af149ca61`: 0 failures, 0 warnings,
  92 offline tests, valid example and matrix, ESP-IDF v5.3.2, COM3 status OK.
  The [R8 ledger](r8-baseline-20260925/ledger.json) records the separate frozen
  offline harness commands, UTC times, output hashes, and maintainer review.
- Git 2.55.0.windows.3, Ninja 1.12.1 in the activated IDF environment, and
  xtensa-esp32s3-elf-gcc 13.2.0 were observed. TEMP write/read passed.
- Manufacturer `09_FactoryProgram` ESP-IDF project `build` exited 0 on the
  activated v5.3.2 toolchain. Full stdout is preserved as
  [`agy-idf-build-20260925.stdout.gz`](agy-idf-build-20260925.stdout.gz), whose
  decompressed SHA-256 is
  `58ff7180190b511ea9aeea86d2c27f7d37e2543247d2daca0d57407f08b0660c`.
  Stderr was empty. This is a toolchain preflight, not a build of the future
  agent product.
- Product inputs use offline fixtures. The AGY model list was fetched under
  the scoped configuration; this does not prove inference connectivity. The
  first pilot must verify the actual provider response.

## Board and recovery image

- COM3 was opened exclusively for non-writing `esptool chip_id` and a full
  16MiB `read_flash`; both exited 0. It identified ESP32-S3 rev v0.2 with 8MiB
  PSRAM. The raw chip ID output and current flash image stay outside Git.
- Historic factory backup at
  `C:\Espressif\vendor\waveshare-esp32-s3-lcd-3.16\backup\factory-flash-20260911-005604.bin`
  is 16,777,216 bytes with SHA-256
  `aa51ba15b975ec2e564506e609729f36d85da23d8892023396a700846955a1e6`.
- The freshly read current-board recovery image at
  `C:\Espressif\vendor\waveshare-esp32-s3-lcd-3.16\backup\pilot-preflight-read-20260925.bin`
  is 16,777,216 bytes with SHA-256
  `ba234a8044e5174ef0275f99b89573a78a6ce62d70b62196720b0ad83d8e532b`.
  The hashes differ; the historic factory backup is not the current flash
  state. Preserve both. The current image is the rollback candidate before
  any later authorized flash operation.
- COM3 exclusivity is time-sensitive and must be rechecked immediately before
  pilot preparation and hardware use. The candidate firmware artifact and its
  flash hash can only be reviewed after the agent produces them.

Reviewed by: Codex maintainer, 2026-09-25 KST. The evidence supports local
pilot preparation while retaining the first-pilot observation boundaries.
