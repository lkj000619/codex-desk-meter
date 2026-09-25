# AGY local inventory — 2026-09-25 KST

This is a read-only operator observation for the selected first-pilot surface. It
does not call a model, prove model entitlement, change settings, reserve a run,
or pass R4/R5.

| Check | Observation |
|---|---|
| `agy --version` | Exit 0; `1.2.11` after automatic update during the 2026-09-25 model-list check; current executable SHA-256 `6169FE5C865CB877FA0043507256A57945C2E23A6BB0E68060733F454A4554F6` |
| `agy --help` | Exit 0; [current-version raw help](agy-cli-20260925-v1211.txt) SHA-256 `95496B2718CF445A8BF9559BA54BA895ACD2DC49FD00BC66F9EDC25CFB323D07`; print mode supports `--input-format text`, `--output-format stream-json`, `--model`, `--print-timeout`; `--disable-slash-commands` disables all slash/skill expansion |
| `agy models --output-format json` | Exit 1; this installed CLI's `models` subcommand does not accept that flag |
| `agy models` | Exit 0 under 1.2.11 with auto-update disabled for the process; advertised list includes `gemini-3.8-flash-medium` (among 14 model IDs); [raw listing](agy-models-20260925-v1211.txt) SHA-256 `714DE458BFF1A50BEED3BCB04644578102F398F5396AE81F686C7D7EEF582DDA`; listing is not an inference-call or entitlement test |
| `agy agents` | Exit 0 under 1.2.11; no custom agent printed in the [raw inventory](agy-cli-20260925-v1211.txt) |
| `agy mcp list` | Exit 0 under 1.2.11; `No MCP servers configured.` |
| `agy plugin list` | Exit 0 under 1.2.11; `No imported plugins.` |
| Current repository `.agents/skills` | One local skill directory exists; `git ls-files .agents/skills` prints no tracked files |
| Preserved 2026-09-24 prepared checkout `.agents/skills` | Absent in that checkout; a future checkout must be inspected again |
| AGY global CLI skills/plugins/agents/rules directories | None exists under `~/.gemini/antigravity-cli/` at observation time |
| Legacy/shared skills directories | `~/.gemini/skills`, `~/.gemini/config/skills`, `~/.gemini/antigravity/skills` absent at observation time |
| AGY `settings.json` | Exists; SHA-256 `A9E7B57B56BB0225448A7068F18264CA3056C5A3C0EE49114F37BF4292EE0D48`; 114 allow rules (14 `command`, 100 `unsandboxed`); `toolPermission`, `artifactReviewPolicy`, and `enableTerminalSandbox` are not explicitly stored; `allowNonWorkspaceAccess` is `true` |
| Global `~/.gemini/GEMINI.md` | Exists; SHA-256 `12552A5E4B15F1B272FBD85C865E2457F7B045C69136ED9C7731D23314EDC512`; content was not included in this evidence |

The inventory shows configuration *presence*, not the effective policy of the
future AGY process. Sparse `settings.json` values can inherit defaults, and
the 114 allow rules were counted without evaluating their effective targets.
The global instruction file and possible CLI memory/cache/routing remain
unresolved for a fair `builtin-only-v1` comparison. A model-list entry also
does not prove that a headless run can use the selected model.

The [official headless documentation](https://www.antigravity.google/docs/cli/headless/)
states that headless tools needing approval can be soft-denied while the process
still exits 0. A profile-bound R5 receipt therefore needs observed effective
permissions for the exact invocation; process exit and this inventory alone
cannot establish that build commands will run. The settings and skills locations
come from the [official settings](https://www.antigravity.google/docs/settings?tab=cli)
and [skills](https://www.antigravity.google/docs/skills?tab=cli) documentation.

The installed binary updated from 1.2.9 to 1.2.11 at the first `agy models`
capture, so the initial listing was not safely attributable to one version.
The 1.2.11 captures above were repeated with `AGY_CLI_DISABLE_AUTO_UPDATE=true`
for those shell processes and matching binary hashes before/after. The
[official troubleshooting guide](https://antigravity.google/docs/cli/troubleshooting/)
documents this environment switch. A future run must pin its invocation
environment and recheck the executable immediately before delivery; another
AGY process could still update the shared binary.
