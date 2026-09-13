# E2E contract readiness proposal

This proposal records the documentation links and gate update suggested by the
E2E contract implementation plan. It does not authorize a benchmark run, pick
a transport, access a provider, flash hardware, or change the existing baseline.

## Proposed links

- [UsageSnapshot schema](../../experiments/schema/usage-snapshot.schema.json)
- [End-to-end result schema](../../experiments/schema/end-to-end-result.schema.json)
- [Provider fixture matrix](../../experiments/fixtures/providers/README.md)
- [Machine-readable fixture expectations](../../experiments/fixtures/provider-fixture-matrix.json)
- [Fixture matrix schema](../../experiments/schema/provider-fixture-matrix.schema.json)
- [Result examples](../../experiments/examples/README.md)
- [Semantic validator](../../scripts/validate-end-to-end-result.py)
- [Host-device pipeline contract](host-device-pipeline-contract.md)
- [Host-device pipeline evidence](../../experiments/examples/host-device-pipeline-evidence.example.json)
- [Integration contract](integration-contract.md)
- [Benchmark readiness gate](benchmark-readiness.md)

## Proposed readiness update

| Gate | Current meaning | Proposed status after maintainer review |
|---|---|---|
| R1 inputs | schema, fixture, baseline, and transport inputs | `in_review`: schemas and fixtures are present; transport remains unset |
| R2 rubric | F1-F9, I1-I4, and G1-G6 recording contract | `in_review`: result schema and examples record every required ID |
| R3 result tooling | E2E schema, validator, valid/invalid examples | `in_review`: local schema and semantic checks are available |
| R8 host integration | collector, normalizer, transport, receiver tests | `not_ready`: no transport or hardware execution was performed |
| R9 hardware operations | board artifact, COM3 policy, and operator evidence | `not_ready`: explicitly out of scope for this change |
| R10 authorization | owner approval for baseline/profile/pilot | `not_authorized`: unchanged |

The maintainer may update the corresponding rows in
`benchmark-readiness.md` after reviewing the local checks. Until then, the
repository remains `PLANNING / NOT_AUTHORIZED`; a valid synthetic result is not
evidence of live quota access or a product pass.

The host-device pipeline adds only `host_simulated` framing/loopback and a
`reference_model_only` receiver oracle. It does not change R8 to a production
integration pass or authorize R10.

## Current review addendum (2026-09-13)

The detailed readiness review is recorded in
[`readiness-review-20260913.md`](readiness-review-20260913.md). It supersedes
the proposed statuses above for this review only: offline tooling checks are
complete, while profile verification, sandbox receipt, one-shot boundary,
production transport/receiver evidence, hardware evidence, and R10 approval
remain open. Host simulation remains `host_simulated` /
`reference_model_only`, never I3/I4 or a hardware pass.
