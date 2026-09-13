# Synthetic provider fixture matrix

Every JSON file in this directory is a credential-free `UsageSnapshot` candidate;
`multi-provider-healthy.json` is one JSON array input containing three such
snapshots.
Values are synthetic and use pseudonymous `acct-demo-*` aliases; they are not
personal account IDs, provider responses, or token telemetry.

The machine-readable expected outcome for this table is
[`../provider-fixture-matrix.json`](../provider-fixture-matrix.json). Its
`reference_time` makes future-time checks deterministic.
The matrix shape is constrained by
[`../../schema/provider-fixture-matrix.schema.json`](../../schema/provider-fixture-matrix.schema.json),
and result validation joins fixture evidence to the claimed provider identity and
window IDs.

| Fixture | Coverage | Expected result |
|---|---|---|
| `codex-percent-window.json` | Codex percent-only 5h window | valid |
| `claude-code-windows.json` | Claude Code 5h, weekly, and model sub-limit windows | valid |
| `gemini-cli-unsupported.json` | Gemini CLI capability unavailable | valid, `UNSUPPORTED_USAGE_SOURCE` |
| `orca-host-claude-code.json` | Claude provider on the Orca host | valid |
| `multi-provider-healthy.json` | One input containing healthy OpenAI Codex, Anthropic Claude Code, and Google Gemini snapshots | valid |
| `provider-stale.json` | One provider retains a last-good stale value | valid, `SOURCE_TIMEOUT` |
| `provider-error.json` | One provider returns an error without substituted quota | valid, `HTTP_500` |
| `reset-time-omitted.json` | Reset time is genuinely unavailable | valid |
| `mixed-percent-absolute.json` | Percent window and source-provided absolute token window | valid |
| `absolute-token-balance.json` | Source-provided absolute token balance | valid |
| `absolute-token-balance-inconsistent.json` | Absolute used + remaining does not equal limit | invalid, `ABSOLUTE_BALANCE_MISMATCH` |
| `unsupported-provider.json` | Unknown provider adapter | valid, `UNSUPPORTED_PROVIDER` |
| `duplicate-provider-window.json` | Duplicate provider window ID | invalid, `DUPLICATE_WINDOW` |
| `future-observed-reset.json` | Future observed/reset timestamp | invalid, `FUTURE_TIMESTAMP` |
| `available-over-stale-threshold.json` | Available snapshot older than the 300-second threshold | invalid, `STALE_THRESHOLD_EXCEEDED` |
| `out-of-range-percent.json` | Percent outside 0..100 | invalid, `SCHEMA_INVALID` |

Validate an individual fixture at a fixed reference time with:

```powershell
python scripts/validate-end-to-end-result.py `
  --fixture experiments/fixtures/providers/codex-percent-window.json `
  --reference-time 2026-09-10T00:04:59Z
```

The matrix intentionally contains invalid cases so that the semantic validator
has executable coverage for duplicate windows, future timestamps, and range
errors. It never performs network calls or credential reads.
