# Planned runner profiles (operator-check only)

These files are non-executable planning inputs for the documented comparison
surfaces. They contain no credentials, account identifiers, provider telemetry, or
guessed model/version values. Every file intentionally uses
`operator-check-required` sentinels; `scripts/benchmark.py prepare` rejects those
sentinels until the operator records read-only version/help checks and fills a
profile for the exact approved tool.

The documented CLI order is Gemini CLI, Antigravity CLI, OpenCode CLI, then
GPT/Codex (the codex-cli profile). The Antigravity IDE surface is not representable by the current noninteractive
CLI runner and remains an operator design check; it is not silently converted to a
CLI profile.

| Order | Profile | Planned identity | Unresolved operator checks |
|---|---|---|---|
| 1 | `gemini-cli.example.json` | provider `google`, product `gemini-cli`, adapter `gemini` | executable, exact version, model ID/slug, stream format, token telemetry |
| 2 | `antigravity-cli.example.json` | provider `google`, product `antigravity-cli`, adapter `antigravity` | executable, exact version, model ID/slug, noninteractive mode, telemetry |
| 3 | `opencode-cli.example.json` | provider `opencode`, product `cli`, adapter `opencode` | executable, exact version, endpoint/model naming, noninteractive mode, telemetry |
| 4 | `codex-cli.example.json` | provider `openai`, product `codex-cli` (GPT/Codex), adapter `codex` | executable, exact version, model ID/slug, reasoning flag, JSON/usage event shape |

The planned historical cohort is fixture-only and not authorized. A future operator
must also confirm the proposed baseline, prompt/config/fixture hashes, sandbox
receipt, one-shot boundary, and explicit R10 approval before invoking any runner
command.
