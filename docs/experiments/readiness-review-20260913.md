# Offline readiness review - 2026-09-13

## Scope and boundary

This is an independent review of the current uncommitted planning/tooling state
on main against PROJECT_PURPOSE, PRODUCT_CONTRACT, the benchmark-readiness gate,
evaluation/integration contracts, and the host-device implementation plan.

No candidate-agent prompt, pilot, benchmark, live provider/API/account access,
credential access, serial port, COM3, ESP32 operation, firmware, or LCD GUI
implementation was performed. The host-device command was exercised only in
dry-run mode with fake serial/reference-receiver logic; it is host_simulated /
reference_model_only, not I3, I4, production integration, or a hardware pass.

Current checkout: branch main, HEAD 34a1790ffeb31d47c1ae78c78a14d7cf4e318c6f,
tag benchmark-v2-baseline-20260911, origin/main at the same commit. No stage,
commit, push, tag, merge, rollback, or main-2 modification was performed.

## Findings and fixes

Findings are listed by severity as found during the standards/specification
review. All listed defects were fixed in the current working tree.

### High - fixture path escape could read arbitrary repository files

The custom host-pipeline fixture option and the direct file adapter did not
constrain a path to the provider-fixture directory. A caller could therefore
turn an offline fixture run into an arbitrary-file read. FixtureFileAdapter and
run-host-device-pipeline.py --fixture now require paths below
experiments/fixtures/providers; errors use repository-relative/sanitized paths.
Tests cover both direct adapter and CLI rejection of an unsafe path.

### High - fixture evidence could claim the wrong provider result

The E2E validator checked that evidence files existed but did not join fixture
contents to the provider identity, status, or window IDs in the result. Fixture
entries now require a matching snapshot identity, status, and exact window set;
nullable identity fields are treated as unknown only for unavailable sources.
The validator reports stable mismatch codes and tests cover identity mismatch,
nullable unsupported context, status/window joins, and duplicate identities.

### High - product_pass could omit GUI scoring evidence

The semantic validator required feature/integration/build/host/transport/
hardware pass states but did not require GUI scores and GUI evidence. A product
pass now requires every GUI rubric item to have a non-null score and evidence;
the regression test expects PRODUCT_PASS_REQUIRES_GUI when those are absent.

### Medium - non-canonical CDM frames were accepted

The decoder accepted alternate JSON whitespace/newline encodings when the CRC
matched canonical bytes. It now rejects any frame whose payload bytes are not
the exact canonical JSON bytes used for CRC, including pretty JSON and CRLF
forms. Golden-vector and rejection tests cover this boundary.

### Medium - duplicate JSON Schema definitions were silently overwritten

cdm-frame.schema.json contained duplicate $defs keys for nullable timestamp and
percent definitions. The duplicate definitions were consolidated, and a
duplicate-key parser now checks every JSON file in the repository.

### Medium - fixture bundle hashing omitted nested provider fixtures

benchmark.py prepare hashed only top-level fixture JSON files, allowing a nested
provider fixture to change without changing the recorded bundle hash. The hash
now includes all JSON files recursively below experiments/fixtures, with a
regression assertion in the benchmark tests.

### Medium - fixture matrix had no machine schema or duplicate-path guard

The provider matrix was validated only by ad hoc shape checks. A dedicated
Draft 2020-12 schema now covers the matrix, and the validator rejects duplicate
fixture paths and incomplete expected-invalid entries. The matrix is included
in README/preflight links and the offline preflight command.

### Medium - unresolved runner identity/version values could be mistaken for evidence

The prior profile examples and historical command notes contained concrete
tool/version-looking values without a current operator verification receipt.
Planning profiles now use the explicit operator-check-required sentinel, contain
no credentials or telemetry claims, and are non-executable. The runner rejects
angle-bracket placeholders and unresolved sentinels in model/version/reasoning/
argv fields. Historical version notes in agent-run-commands.md are explicitly
labeled non-evidence. The documented order is Gemini CLI, Antigravity CLI,
OpenCode CLI, then GPT/Codex (the codex-cli profile); Antigravity IDE remains an
operator design check rather than an invented CLI profile.

### Medium - clean-checkout dependency/bootstrap path was implicit

The pinned dependency file already existed, but the README did not provide a
single clean-checkout validation sequence. README and preflight documentation
now install scripts/requirements-benchmark.txt explicitly, then run the offline
unit/runner suite, E2E validator, fixture-matrix validator, historical
validator, and host dry-run. The pinned install completed successfully in this
review; no e2e-verify-deps artifact was used.

### Low - documentation contained a user-specific absolute path

The host-device plan and development-environment junction example exposed an
absolute user-profile path. Both now use repository-relative or generic path
examples. The proposed change scope has zero absolute user paths and zero
credential-like matches in the final scan.

### Medium - localized Windows TEMP broke an isolation regression test

The test for benchmark.prepare inherited the default Korean user-profile TEMP,
which correctly failed the production ASCII run-root policy before exercising
its ID reservation assertions. The test now requests the Windows system ASCII
TEMP directory (and /tmp on non-Windows) only for that synthetic isolation
fixture; benchmark.prepare's ASCII production check remains unchanged and a
no-write boundary probe still rejects a non-ASCII run root.

## Standards/spec review outcome

The standards axis checked repository conventions, pinned bootstrap, JSON
parsing/schema validity, stable validator codes, path safety, canonical framing,
portable documentation links, and no-write/offline test behavior. The
specification axis checked the stated product/E2E contracts, provider/host
identity separation, fixture evidence provenance, benchmark run gates, and the
host-device implementation plan. The defects above were the concrete gaps
found; no additional in-scope correctness or safety defect remains in the
offline preparation state.

## Prepared runner profiles and preflight inputs

The planned order and identity templates are present under
experiments/config/runner-profiles/:

1. gemini-cli.example.json - provider google, product gemini-cli, adapter gemini.
2. antigravity-cli.example.json - provider google, product antigravity-cli,
   adapter antigravity.
3. opencode-cli.example.json - provider opencode, product cli, adapter opencode.
4. codex-cli.example.json - provider openai, product codex-cli (GPT/Codex),
   adapter codex.

Every profile uses operator-check-required for model/version/reasoning/argv
values and is rejected by benchmark.py prepare until an operator performs
read-only executable/version/help checks for the exact approved surface. No
model ID, CLI version, token telemetry, credential, or availability fact was
invented. experiments/config/preflight-inputs.example.json records the planned
order, current HEAD/tag, proposed baseline, offline commands, transport status
not_run, and R10/candidate/hardware approval gates.

## Offline verification record

| Command | Exit | Result |
|---|---:|---|
| python -m pip install -r scripts/requirements-benchmark.txt | 0 | Installed/confirmed pinned validation dependencies. |
| python -m unittest scripts.tests.test_benchmark.IsolationTests.test_prepare_reserves_ids_and_excludes_parent_history -v (pre-fix repro) | 1 | Red under default localized TEMP with the ASCII run-root ValueError. |
| python -m unittest scripts.tests.test_benchmark.IsolationTests.test_prepare_reserves_ids_and_excludes_parent_history -v | 0 | Focused regression passed under the default localized TEMP. |
| python -m unittest discover -s scripts/tests -p test_*.py -v | 0 | 50 tests passed under the default localized TEMP. |
| python scripts/validate-end-to-end-result.py | 0 | Valid example accepted. |
| python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json | 0 | Matrix/schema/fixture checks passed. |
| python scripts/validate-experiment-result.py | 0 | Historical validator accepted its unchanged examples. |
| python scripts/run-host-device-pipeline.py --dry-run | 0 | device_accessed=false, collection_failures=[], 3437 bytes, frame SHA-256 878cfb1a4b34c6662bf447ec07932d4db0c55d8fa85ba23596eacf57f2ddb87f. |
| no-write ASCII enforcement boundary probe | 0 | Non-ASCII run root rejected before directory creation; production ASCII enforcement retained. |
| profile-order assertion | 0 | Gemini, Antigravity, OpenCode, then GPT/Codex profile paths match preflight order. |
| no-write AST/import check | 0 | 11 Python files parsed; benchmark, host pipeline, and E2E validator imported. |
| JSON duplicate/parser/schema check | 0 | 63 JSON files parsed; 9 Draft 2020-12 schemas checked; duplicate keys 0. |
| runner-profile schema/sentinel check | 0 | 4 profile JSON files and preflight JSON validated; all 4 profiles retain operator-check-required sentinels. |
| local Markdown link check | 0 | 86 locally checkable links resolved; no broken links. |
| sensitive/absolute-path scan | 0 | 0 absolute user paths; 0 credential-like matches. |
| proposed-scope trailing-whitespace scan | 0 | 76 tracked/untracked files checked; 0 trailing-whitespace findings. |
| git diff --check | 0 | No whitespace errors; Git emitted only its LF-to-CRLF advisory for the PowerShell file. |
| .\scripts\check-experiment-preflight.ps1 -SkipIdf | 1 | Required files, 50 tests, E2E, and matrix checks passed; expected failure is the uncommitted working-tree gate. |

The read-only command scripts/check-experiment-preflight.ps1 -SkipIdf exited 1
as intended because the working tree is not yet committed. Its internal
required-file, historical validator, 50-test, E2E, and matrix checks passed.
It only queried device presence through the existing preflight check; no serial
port was opened.

## Current readiness R0-R10

| Gate | Current status | Evidence/remaining boundary |
|---|---|---|
| R0 scope/cohort | in_review | Contracts and historical-vs-E2E scope reviewed; baseline not frozen. |
| R1 inputs | in_review | Schemas, fixtures, profiles, and preflight inputs prepared; final hashes wait for an approved commit. |
| R2 rubric | in_review | F1-F9, I1-I4, and GUI rubric structures are represented; no live run. |
| R3 result tooling | in_review | Schema/semantic validators, valid/invalid examples, matrix checks, and tests pass offline. |
| R4 profile | not_ready | Profiles are operator-check sentinels; executable/model/version checks remain open. |
| R5 sandbox receipt | not_ready | No profile-bound sandbox receipt exists. |
| R6 runner telemetry | partial | Deterministic runner tests cover missing telemetry/null classification; no candidate raw log or live telemetry exists. |
| R7 one-shot | not_ready | No candidate prompt execution occurred. |
| R8 host integration | partial | Fixture collector, normalization, framing, fake serial, and reference receiver are tested; no production parser/transport/device pass. |
| R9 hardware | not_ready | No firmware build/flash/reset/monitor or COM3 open occurred. |
| R10 authorization | not_authorized | User has not approved a baseline commit, candidate run, or hardware operation. |

The host simulation must not be relabeled I3/I4 or hardware pass. R10 remains
explicitly not_authorized.

## Pre-commit inventory and baseline-freeze proposal

The proposed candidate set is exactly the 16 tracked-modified and 60
untracked files listed below. Nothing was staged. Files outside this list are
excluded, including unchanged tracked files, main-2, external temporary test
roots, generated run outputs, credentials, serial logs, firmware artifacts, and
any candidate-agent output.

### Tracked modified (16)

~~~text
README.md
docs/DEVELOPMENT_ENVIRONMENT.md
docs/PRODUCT_CONTRACT.md
docs/PROJECT_PURPOSE.md
docs/experiments/agent-experiment-protocol.md
docs/experiments/agent-run-commands.md
docs/experiments/benchmark-management.md
docs/experiments/evaluation-contract.md
docs/experiments/hardware-feature-discovery.md
experiments/config/runner-profile.example.json
experiments/config/version-2-baseline.yaml
experiments/prompts/version-2-agent-task.md
results/README.md
scripts/benchmark.py
scripts/check-experiment-preflight.ps1
scripts/tests/test_benchmark.py
~~~

### Untracked proposed additions (60)

~~~text
docs/experiments/benchmark-readiness.md
docs/experiments/e2e-contract-implementation-plan.md
docs/experiments/e2e-contract-readiness-proposal.md
docs/experiments/feature-comparison.md
docs/experiments/host-device-pipeline-contract.md
docs/experiments/host-device-pipeline-implementation-plan.md
docs/experiments/integration-contract.md
docs/experiments/readiness-review-20260913.md
experiments/config/preflight-inputs.example.json
experiments/config/runner-profiles/README.md
experiments/config/runner-profiles/antigravity-cli.example.json
experiments/config/runner-profiles/codex-cli.example.json
experiments/config/runner-profiles/gemini-cli.example.json
experiments/config/runner-profiles/opencode-cli.example.json
experiments/examples/README.md
experiments/examples/cdm-frame.example.json
experiments/examples/end-to-end-hardware-not-run-manifest.example.json
experiments/examples/end-to-end-hardware-not-run.example.json
experiments/examples/end-to-end-manifest.example.json
experiments/examples/end-to-end-result.example.json
experiments/examples/host-device-pipeline-evidence.example.json
experiments/examples/invalid-fabricated-token-manifest.example.json
experiments/examples/invalid-missing-identity-manifest.example.json
experiments/examples/invalid-pass-without-evidence-manifest.example.json
experiments/examples/invalid-product-pass-manifest.example.json
experiments/examples/invalid/cdm-frame-crc.example.json
experiments/examples/invalid/cdm-frame-schema.example.json
experiments/examples/invalid/cdm-frame-unsupported-version.example.json
experiments/examples/invalid/fabricated-token.example.json
experiments/examples/invalid/invalid-product-pass.example.json
experiments/examples/invalid/missing-identity.example.json
experiments/examples/invalid/pass-without-evidence.example.json
experiments/fixtures/provider-fixture-matrix.json
experiments/fixtures/providers/README.md
experiments/fixtures/providers/absolute-token-balance-inconsistent.json
experiments/fixtures/providers/absolute-token-balance.json
experiments/fixtures/providers/available-over-stale-threshold.json
experiments/fixtures/providers/claude-code-windows.json
experiments/fixtures/providers/codex-percent-window.json
experiments/fixtures/providers/duplicate-provider-window.json
experiments/fixtures/providers/future-observed-reset.json
experiments/fixtures/providers/gemini-cli-unsupported.json
experiments/fixtures/providers/mixed-percent-absolute.json
experiments/fixtures/providers/multi-provider-healthy.json
experiments/fixtures/providers/orca-host-claude-code.json
experiments/fixtures/providers/out-of-range-percent.json
experiments/fixtures/providers/provider-error.json
experiments/fixtures/providers/provider-stale.json
experiments/fixtures/providers/reset-time-omitted.json
experiments/fixtures/providers/unsupported-provider.json
experiments/schema/cdm-frame.schema.json
experiments/schema/end-to-end-manifest.schema.json
experiments/schema/end-to-end-result.schema.json
experiments/schema/provider-fixture-matrix.schema.json
experiments/schema/usage-snapshot.schema.json
scripts/host_device_pipeline.py
scripts/run-host-device-pipeline.py
scripts/tests/test_host_device_pipeline.py
scripts/tests/test_validate_end_to_end_result.py
scripts/validate-end-to-end-result.py
~~~

No generated/local artifact is proposed for inclusion. The test suite used
temporary directories outside the repository and PYTHONDONTWRITEBYTECODE=1;
there are no repository __pycache__, run, serial, credential, or hardware
artifacts in the inventory.

Proposed baseline identifiers (not finalized):

- Commit message: chore: freeze offline E2E readiness tooling
- Baseline ID/tag: benchmark-v2-baseline-20260913
- Commit SHA, prompt SHA-256, config SHA-256, and recursive fixture-bundle
  SHA-256: finalize_after_user_approved_commit

## Exact approval gates and next actions

The first action requiring approval is staging/committing the proposed set.
After reviewing this report and the diff, the user must explicitly authorize
the following sequence; none of it was run here:

~~~powershell
git diff --check
git status --short
git add -- <the exact 76 paths listed in this report>
git diff --cached --check
git commit -m "chore: freeze offline E2E readiness tooling"
git rev-parse HEAD
~~~

Creating the proposed annotated tag benchmark-v2-baseline-20260913 is a
separate approval gate; do not create it automatically. After the approved
commit, calculate and record the prompt, config, and recursive fixture-bundle
hashes and update the preflight inputs only under a separately approved
metadata change.

Before any candidate run, an operator must read-only verify the selected CLI's
executable, --version, --help, model naming, reasoning mode, and telemetry
surface, then replace the profile sentinel and obtain a sandbox receipt.
benchmark.py prepare must succeed only after those checks; no live provider
access is implied by the profile templates.

R10 requires explicit user approval of the frozen baseline, exact profile,
one-shot prompt boundary, and pilot/benchmark scope. Hardware remains a
separate operator approval: only then may a future owner run hardware-specific
preflight/firmware/COM3 actions. This review stops before all such actions.
