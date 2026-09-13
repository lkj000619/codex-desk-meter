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
| `invalid-product-pass.example.json` | `PRODUCT_PASS_REQUIRES_INTEGRATION` |

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
