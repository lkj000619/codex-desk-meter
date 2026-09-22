# End-to-end contract examples

`end-to-end-result.example.json` is a schema-valid synthetic result for the
planned `version-2-end-to-end-v1` cohort. It records fixture collection and
normalization as passing while leaving transport, hardware, GUI capture, and
telemetry explicitly `not_run`.

`end-to-end-hardware-not-run.example.json` demonstrates the conservative result
shape when no device or integration seam was exercised. Neither example claims
`product_pass`; product pass requires every F1-F9 and I1-I4 result plus build,
host, transport, and hardware validation to pass.

The files under `invalid/` are executable negative examples:

| Example | Expected validator code |
|---|---|
| `pass-without-evidence.example.json` | `EVIDENCE_REQUIRED` |
| `missing-identity.example.json` | `IDENTITY_REQUIRED` |
| `fabricated-token.example.json` | `TOKEN_TELEMETRY_UNAVAILABLE` |
| `invalid-product-pass.example.json` | `PRODUCT_PASS_REQUIRES_CORE_RESULTS` |

All paths are repository-relative and evidence is synthetic. The examples do
not read credentials, query provider endpoints, select a transport, flash a
board, or establish hardware success.

Provider fixture expectations are recorded separately in
[`../fixtures/provider-fixture-matrix.json`](../fixtures/provider-fixture-matrix.json)
and can be checked with the same validator. The matrix is constrained by
[`../schema/provider-fixture-matrix.schema.json`](../schema/provider-fixture-matrix.schema.json);
fixture evidence is also joined to the provider identity and window IDs claimed by a
result, so a path to a different provider cannot substantiate a pass.

The host-device pre-experiment evidence example records reproducible fixture and
golden-frame SHA-256 values in
`host-device-pipeline-evidence.example.json`. Its loopback and reference-model
classification is host-only: it is not serial-device receipt, firmware, LCD, or
physical-hardware evidence.

`cdm-frame.example.json` is the canonical empty-payload golden vector;
`invalid/cdm-frame-crc.example.json`, `invalid/cdm-frame-schema.example.json`,
and `invalid/cdm-frame-unsupported-version.example.json` exercise protocol
rejection classes.

When agent token telemetry is available, the schema explicitly defines
`total = input + output`; `cached` and `reasoning` are annotations and are not
added again. The corresponding `token_total_definition` value is
`input_plus_output_excludes_cached_and_reasoning`.
This is the normalized E2E definition, not every provider's raw total. Every
E2E telemetry object must include nullable `provider_total` and the
`provider_total_definition` declaration; raw provider totals are preserved and
never added to the normalized total. Do not overwrite raw telemetry to make a
result validate.

Every E2E result requires top-level `core_results.C1` through `C8`, even when
the result is `not_run`. F9 is the only feature that may carry `details`.
When F9 is `pass` or `partial`, its details contain exactly three candidates
with user value, implementation cost, risk, verification method, selection
state, selection/rejection evidence, and the canonical score fields:
`hardware_understanding` (5), `user_value` (5), `selection_logic` (5),
`implementation_completeness` (10), and `separation_portability` (5). The
validator requires `total` to equal their sum.

The archive path runs the E2E schema validator, the semantic validator, and the
evaluation-manifest/evidence join before adding a normalized result. A failed
candidate is retained only as its raw source snapshot. The summary excludes
pilot, incomplete, invalid, semantically unjoined, and duplicate path/run
identity records. It groups repetitions by agent configuration plus the full
experiment, baseline id/ref/commit, and input-bundle identity, then reports
per-group valid repetition counts, success ratio, median, and range. Long hash
values are shortened only in the display label.

The run manifest's `execution.profile_sha256` is the semantic hash of the
operator profile. `benchmark.py check` and `prepare` include that profile hash
and the selected baseline reference/commit in the same `input_bundle_sha256`
calculation; the check uses a temporary baseline snapshot and does not mutate
the worktree.
The preflight receipt's `profile_sha256` must equal that execution hash.
`agent.configuration_sha256` remains a separate byte-level integrity check for
the saved profile JSON and is not the receipt binding.
