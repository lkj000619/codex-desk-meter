# AGY launch independent Sol review — 2026-09-25

## Verdict

`BLOCKED / NOT_AUTHORIZED` is the correct current verdict. The correction set removes the
earlier false preflight pass and now fails closed. No model/provider call, prompt delivery,
COM3 open, flash, new prepared run, commit, tag, or push was performed by this review.

The first pilot decision remains `antigravity-cli / gemini-3.8-flash-medium`, repetition 1,
with hardware option A selected. Q3 chooses the target and later hardware path; it does not
activate R10. The preserved conditional approval still requires an exact, evidence-backed
profile and receipt, a current successful preparation, completion of the pre-pilot gates,
and the remaining hardware safety checks.

## Independent identity and hash verification

| Item | Independently recomputed value | Result |
|---|---|---|
| Audit starting HEAD | `a36747ab2f7ac50676343b3b53517c8491d54b03` | Matches the starting point; edits were uncommitted at independent review time. |
| Baseline tag peeled commit | `9ef945efd9d6c2c4b4eedca75eccc9f280b3aced` | Matches the selected baseline. |
| Baseline tree | `f376f26c907613b457b4295931dd472254bf4716` | Matches the isolated checkout tree. |
| Isolated checkout local commit | `5475ee68f90674ce4ebea7e4707ec6dea5f9c6e1` | Expected local snapshot identity; checkout is clean. |
| Corrected profile semantic SHA-256 | `075f23c4ebb10c87b0d5bd54c86c9c03dd4ed1e21de44283b1cd65eb7c8caa84` | Matches receipt and review. |
| Corrected profile byte SHA-256 | `e659219fad1e1981c9ba39d978ed5eaf9f63f25ca4a489fe040a3af1f3bbf549` | Matches review. |
| Corrected input bundle SHA-256 | `ad574cbaacf93d876a0b4c2007e2065d6a2e164dff23f078abd213e377fd5389` | Recomputed from the selected baseline snapshot and external profile. |
| 2026-09-24 evidence SHA-256 | `3bd4294e5f56946c48f76b877457a6fe92c85b418eaeb61804f6c1f3d6874b00` | Matches receipt. |
| 2026-09-25 CLI evidence SHA-256 | `cc5a85106dda4bf90e4f5b7f1d5ac2c3b676c4a7cd353f552da8755d93b4a6ff` | Matches receipt. |
| Corrected receipt byte SHA-256 | `65b764715e0456fb76a7d9f6d9b4d7cbb35470260c6e8e3b019e7f81fdae03d9` | Matches Luna review. |
| Installed `agy.exe` SHA-256 | `6efbd9828df5d0f44d56cb5fd770d87387f40eb364360b06bfbeba7c76f89bec` | Matches 2026-09-25 evidence; version is `1.2.9`. |

The baseline and isolated checkout use different commit IDs because `prepare` creates a new
single-commit repository, but their tree IDs are identical. This is expected and is not a
baseline mismatch. The runner accepts a profile outside the clean baseline checkout and
binds its semantic hash into the input bundle, so a post-tag operator profile is mechanically
supported. It does not become part of the agent checkout or the baseline tag.

The independently recomputed component hashes are:

```text
prompt_sha256=f99d708ca9f3bdfc2134942c44e30b6c14bb7a098fe36f75ad5472c8210f4a77
config_sha256=f80d88b527c36f4ca591926be3842983fd61afa6ace517e6c31cf0ab197b337f
fixture_sha256=0a2964266df53a641dda4b4e9d460e2ffe990bfb38c6d40e32556610bbe42eec
schema_sha256=971a50e010d58a5c82f89dad5af9c99c6520130e63a96987ddc8e87e93a4bc79
evaluation_criteria_sha256=c3dd931a1e41ea3f74d2ae5f51701ff8545dcb2dbf4d2240849ae25dad8ce30e
profile_sha256=075f23c4ebb10c87b0d5bd54c86c9c03dd4ed1e21de44283b1cd65eb7c8caa84
input_bundle_sha256=ad574cbaacf93d876a0b4c2007e2065d6a2e164dff23f078abd213e377fd5389
```

## Profile and receipt findings

The corrected argv is consistent with the captured AGY help and repository rules:

```text
agy --print --input-format text --output-format stream-json --print-timeout 120m \
  --model gemini-3.8-flash-medium
```

The model ID already embeds the medium effort variant, so a separate `--effort medium` is
correctly omitted. `--disable-slash-commands` is also omitted because it disables all skill
expansion and is not equivalent to `builtin-only-v1`, which retains built-in features while
disabling custom extensions. The copied Codex-only `--ask-for-approval never` claim is gone.

The profile truthfully records unverified approval, skills, memory, user instructions, cache,
routing, permissions, model network, and extension enforcement. It is schema-valid but
`validate_resolved_profile` rejects the `unverified` markers. `benchmark.py check` therefore
also exits blocked without reserving a run.

The receipt now records host and policy checks as `not_observed`, settings inventory as
`blocked`, read isolation as `not_enforced`, and `pilot_pass: false`. Its evidence hashes are
valid. `validate_preflight_receipt` rejects it at `idf_build`, which is the intended fail-closed
behavior. A receipt hash match proves evidence-file integrity, not that the evidence supports
the previous settings claims.

## Runner and gate review

The offline suite now includes an AGY-shaped mock-stream test. It proves that `capture()`
delivers the exact UTF-8 prompt bytes once through stdin, preserves one raw JSONL event,
checks the prompt SHA-256, and keeps unsupported AGY token/tool metrics null. The full suite
passes 82 tests. This is meaningful pre-pilot evidence for R6/R7, but those gates remain
`not_ready`: the real AGY stream format, user-intervention measurement, and evaluator
read-only enforcement have not been demonstrated.

R8 also remains `not_ready`. Existing tests prove fixture collection and normalization,
canonical `cdm/1` framing, CRC and sequence handling, stale and last-good behavior in a host
reference receiver, loopback, and a dry run that does not access a device. Repository evidence
correctly classifies F3 as `host_simulated`, F4 as `reference_model_only`, and I3/I4 as
`not_run`.

The R8 boundary must be resolved before launch. Candidate production evidence can only exist
after the pilot creates an artifact, so it cannot be a prerequisite for that same pilot.
Pre-pilot R8 needs explicit evaluator-harness acceptance criteria and a maintainer decision;
candidate production and hardware results remain post-run evaluation. Until that distinction
is recorded and the pre-pilot criteria pass, R8 continues to block R10.

## Hardware and stale-run verification

COM3 is currently enumerated as `USB\VID_303A&PID_1001`, status `OK`. The port was not opened,
so presence is not proof of exclusive ownership. The historical 16 MiB backup exists and
recomputes to:

```text
AA51BA15B975EC2E564506E609729F36D85DA23D8892023396A700846955A1E6
```

R9 remains `not_ready` because current board/artifact linkage, COM3 exclusivity, and a completed
operator checklist are absent. The old prepared manifest also records `port: null`,
`hardware_slot: none`, and `baseline_image_sha256: null`.

The preserved `20260924-antigravity-cli-agy-flash-medium-r01` directory is not executable on
2026-09-25. The runner rejects a run whose ID date differs from the current KST date. It also
contains the superseded semantic profile hash `e9b4...` and copied invalid approval claim.
The directory should remain preserved as a consumed preparation ID and must not be reused.

## Validation performed

- `git diff --check`: no whitespace errors; only the existing CRLF normalization warning.
- Runner/profile schema validation: pass.
- Resolved-profile validation: expected block on `unverified`.
- `benchmark.py check`: expected block; no run ID reserved.
- Receipt evidence verification: hashes pass; receipt validation expected block on
  `idf_build=not_observed`.
- Unit suite: 82 tests passed.
- Historical manifest/result validator: passed.
- E2E example validator: passed.
- Provider fixture matrix validator: passed.

The next launch review must close R4/R5, decide and satisfy the pre-pilot R8 harness boundary,
complete R9, recompute the profile and bundle hashes, issue a passing profile-bound receipt,
and create a new date-valid preparation with `-Port COM3`. Only then can the preserved
conditional approval be evaluated for exact R10 activation. No prompt or model process may
start before that activation.
