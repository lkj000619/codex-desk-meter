# Host-to-device pre-experiment infrastructure plan

## Status and purpose

**`IMPLEMENTATION_AUTHORIZED / EXPERIMENT_NOT_AUTHORIZED`**

This plan defines the maintainer-owned infrastructure that must exist before an AI agent
benchmark can start. It does not implement the benchmark product on behalf of a candidate
agent. The output is an offline, deterministic harness for exercising the seams from a PC
usage source to an ESP32 receiver without contacting a provider or flashing hardware.

The canonical checkout is the repository checkout on branch `main`. Preserve
all existing uncommitted work. The historical `main-2` checkout and its r01 snapshot are
read-only references.

## Decisions fixed for this phase

1. The benchmark transport baseline is USB serial with newline-delimited UTF-8 JSON.
2. Local Wi-Fi HTTP remains a later product-operation cohort and is not implemented here.
3. Inputs are synthetic fixtures conforming to `usage-snapshot.schema.json`.
4. Provider credentials, cookies, account tokens, and live endpoints are outside scope.
5. Host output is a versioned `cdm/1` envelope. Payloads retain provider, agent, host,
   model, account-profile, source, metric, unit, freshness, and error identity.
6. Integrity uses canonical JSON plus CRC32. The precise canonicalization and CRC coverage
   must be specified once and tested with golden vectors.
7. This phase performs PC-only tests. COM3 access, ESP32 flashing, firmware builds, and
   physical LCD evaluation require later operator authorization.

## Required implementation

### P1 — Freeze the wire contract

Create a JSON Schema for the `cdm/1` frame and document:

- protocol version, monotonically increasing sequence, and RFC3339 `sent_at`;
- the array of normalized provider snapshots and independently typed global-reset inputs;
- UTF-8, one-frame-per-line framing, maximum encoded frame size, and newline policy;
- canonical JSON rules, CRC32 input bytes, encoding, and hexadecimal representation;
- duplicate, out-of-order, wraparound, malformed, oversized, and unsupported-version rules;
- ACK policy. For this first baseline, a sender-side write receipt is not a device ACK;
  device ACK/retry remains explicitly unsupported unless fully specified and tested.

Completion: schema-valid golden frames and deliberately invalid frames exist, and every
rule above has an automated assertion.

### P2 — Implement the fixture collector registry

Implement a host-side registry whose adapters read only repository fixtures. At minimum it
must emit Codex, Claude Code, Gemini CLI, and Orca-host examples through the same interface.
One adapter failure must not suppress other snapshots. Unsupported, unavailable, error,
and stale are values, not exceptions that abort collection.

No live-provider adapter is required. Define a narrow extension interface so a later
owner-only adapter can be added without changing normalization or transport code.

Completion: deterministic tests cover healthy multi-provider input, partial failure,
unsupported capability, absent reset time, percent-only quota, and absolute token balance.

### P3 — Implement normalization and frame encoding

Validate adapter output with the existing usage snapshot schema before encoding. Preserve
null rather than inventing token counts, reset times, model IDs, or quota limits. Produce a
deterministic frame and expose decode/verify functions used by tests and the receiver model.

Completion: round-trip, golden-vector, CRC corruption, truncation, invalid UTF-8,
oversized-frame, invalid-schema, and unsupported-version tests pass.

### P4 — Implement a safe serial bridge boundary

Add a host CLI that can:

- render a frame to stdout or a file in dry-run mode;
- accept an explicit serial port only when the operator supplies a send flag;
- default to no device access;
- record structured command outcome without recording secrets;
- reject ambiguous or missing port selection for a real send.

Automated tests must use an in-memory or loopback fake. They must never open COM3.

Completion: help text documents the safety boundary, dry-run works without hardware, and
fake-serial success/failure tests are deterministic.

### P5 — Implement a PC reference receiver/state model

Implement a host-only receiver model for the behavioral contract expected from a future
ESP32 implementation. It must validate framing/schema/CRC, accept a new sequence, reject
duplicates and out-of-order frames, retain the last good state after bad input, enter stale
at 300 seconds, preserve provider-local failures, and recover on the next valid frame.

This is a conformance oracle, not firmware and not evidence that ESP32 behavior passed.

Completion: tests cover normal update, every rejection class, last-good retention, stale
transition at 299/300 seconds, multi-provider partial failure, and recovery.

### P6 — Connect the E2E result contract

Extend examples and validation only as needed to record this infrastructure truthfully:

- F1/F2 host fixture pipeline may pass when its production host implementation is tested;
- F3 may only claim `host_simulated` until real serial bytes and device receipt are tested;
- F4 is `reference_model_only`, not ESP32 receiver pass;
- I1/I2 may pass from host evidence; I3/I4 and product pass remain not-run/false;
- generated evidence paths and SHA-256 values must be reproducible and repository-relative.

Completion: valid examples pass, targeted invalid examples fail for stable error codes, and
the historical validators still pass.

## Verification commands

The implementer must discover the repository's actual command surface rather than assume
filenames. At minimum run and report exit codes for:

1. the new host pipeline unit/integration tests;
2. `python scripts/validate-end-to-end-result.py`;
3. `python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json`;
4. `python scripts/validate-experiment-result.py`;
5. JSON parsing and Draft 2020-12 schema checks for every changed JSON file;
6. a no-write Python syntax/import check when bytecode-cache writes are unavailable;
7. `git diff --check`.

## Evidence and completion report

Report every modified file, commands with exit codes, test counts, and unresolved risks.
Clearly distinguish schema validation, host simulation, serial loopback, firmware, and
physical hardware evidence. Do not relabel a simulation as transport or hardware pass.

The work is complete only when the offline fixture-to-frame-to-reference-receiver path is
deterministic, the original E2E/historical validators remain compatible, and no live or
hardware side effect occurred.

## Hard boundaries

- Do not run a benchmark, pilot, or candidate-agent product implementation.
- Do not access provider endpoints or local provider credentials.
- Do not open COM3, flash or reset an ESP32, or run a hardware monitor.
- Do not build or modify candidate firmware or LCD GUI code.
- Do not stage, commit, push, tag, merge, or rewrite existing history.
- Do not discard, overwrite, or reformat unrelated uncommitted user changes.
- Do not change readiness gate R10 to authorized or claim the project is experiment-ready.

Path hygiene: documentation and evidence must use repository-relative paths or
generic ASCII examples such as `C:\\src\\codex-desk-meter`; never record a maintainer's
absolute user-profile path in a committed planning artifact.
