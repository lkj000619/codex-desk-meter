# Planned runner profiles (operator-check only)

Default access policy: `sandbox_policy: prompt-and-log`.
Docker/VM is optional; OS read isolation is recorded as `not_enforced`.
See [access policy](../../../docs/experiments/isolation-policy.md).
Inventory includes plugins, permissions, and model-call network conditions;
operator-check values are unresolved, not evidence of disabled features.

These files are non-executable planning inputs for the documented comparison
surfaces. They contain no credentials, account identifiers, provider telemetry, or
guessed model/version values. Every file intentionally uses
`operator-check-required` sentinels; `scripts/benchmark.py prepare` rejects those
sentinels until the operator records read-only version/help checks and fills a
profile for the exact approved tool.

The documented CLI order is Antigravity CLI, OpenCode CLI, then GPT/Codex
(the codex-cli profile). The `gemini-cli.example.json` is retained for
Enterprise/API-key conditional use only and is not part of the default cohort.
The Antigravity IDE surface is not representable by the current noninteractive
CLI runner and remains an operator design check; it is not silently converted to a
CLI profile.

| Order | Profile | Planned identity | Unresolved operator checks |
|---|---|---|---|
| 1 | `antigravity-cli.example.json` | provider `google`, product `antigravity-cli`, adapter `antigravity` | executable, exact version, model ID/slug, noninteractive mode, telemetry |
| 2 | `opencode-cli.example.json` | provider `opencode`, product `cli`, adapter `opencode` | executable, exact version, endpoint/model naming, noninteractive mode, telemetry |
| 3 | `codex-cli.example.json` | provider `openai`, product `codex-cli` (GPT/Codex), adapter `codex` | executable, exact version, model ID/slug, reasoning flag, JSON/usage event shape |
| Conditional | `gemini-cli.example.json` | provider `google`, product `gemini-cli`, adapter `gemini` | eligibility, executable, exact version, model ID/slug, stream format, token telemetry |

This is a profile inventory order, not the randomized benchmark execution order.
`../preflight-inputs.example.json` preserves the older Gemini-first inventory and
historical baseline identifiers; it is not the current run schedule or HEAD.
Replace those values when preparing reviewed inputs, without treating the example
as an authorization receipt.

The planned E2E cohort uses synthetic fixtures and is not authorized. A future operator
must also confirm the proposed baseline, prompt/config/fixture hashes, access-policy preflight
receipt, one-shot boundary, and explicit R10 approval before invoking any runner
prepare/run command. Offline tooling checks can be performed while preparing gates.

## Adopted extension condition

The first comparison uses `builtin-only-v1`: disable custom/user-installed skills,
external plugins and MCP servers; retain and inventory built-in agent features.
Record configuration before execution and observed usage after execution.
Policy strings in templates are planned requirements, not proof of enforcement.
Unknown version/hash/call counts remain null with reasons in operator evidence.
Ponytail or other extensions belong to a separate later comparison condition.
See [extension policy](../../../docs/experiments/isolation-policy.md).
