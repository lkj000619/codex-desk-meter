# Experiment launch readiness record — 2026-09-21

## Decision boundary

This is the Luna-max preparation handoff for the pending first-cohort decision. It is
an offline readiness record, not an experiment run and not an authorization. No model
call, provider run, `benchmark.py run`, serial access, flash, commit, tag, or push is
performed by this record.

Current decision: `READINESS_EVIDENCE_COLLECTED / NOT_AUTHORIZED`.

The two proposed first-cohort entries are Codex CLI candidates:

| Candidate | Model field | Reasoning field | Candidate file | Decision |
|---|---|---|---|---|
| Luna | `gpt-5.6-luna` | `max` | `experiments/config/verified-profiles-candidate/codex-cli-luna-max.candidate.json` | pending Q1 |
| Sol | `gpt-5.6-sol` | `medium` | `experiments/config/verified-profiles-candidate/codex-cli-sol-medium.candidate.json` | pending Q1 |

The model IDs and reasoning levels above are resolved from the local non-secret model
metadata cache and remain proposed cohort candidates while Q1 is pending. The local
executable, version, and argument spelling are measured below. Model entitlement,
account access, actual model behavior, and enforcement of the `builtin-only-v1`
condition were not tested and must not be inferred from a version/help probe or a
metadata cache.

## Starting state and scope

- Repository: `C:\Users\이광진\orca\codex-desk-meter`
- Branch: `main`, ahead of `origin/main` by one commit at the start of this work.
- Starting HEAD: `47b720d7f29185dd63a0d72737897966a4ea335f`.
- Working tree: already dirty with the earlier documentation, schema, runner, test,
  and untracked review artifacts. Those changes are preserved. This task adds only
  the readiness record, evidence, and candidate profile files listed here.
- User decisions Q1 (two-Codex cohort versus the existing six planned entries) and
  Q2 (local baseline commit/tag) remain pending in
  [`launch-coordination-20260921.md`](launch-coordination-20260921.md). No baseline
  commit or tag is created here.
- Existing policy remains authoritative: R4/R5/R10 are not closed, and the existing
  conditional approval is not converted into execution approval.

The work is limited to read-only executable/configuration inspection, offline host
checks, reversible temporary build/preflight work if needed, and durable evidence.
The preflight performed incidental OS presence detection for COM3, but did not open
the serial port, test exclusivity or communication, operate the board, or flash it.
It does not include product implementation, provider/model calls, credentials, ESP32
operation, or flash.

## Required source records read

- [`DOCUMENTATION_REVIEW_CHECKLIST.md`](../DOCUMENTATION_REVIEW_CHECKLIST.md)
- [`benchmark-readiness.md`](benchmark-readiness.md)
- [`agent-run-commands.md`](agent-run-commands.md)
- [`r4-profile-resolution.md`](r4-profile-resolution.md)
- [`preflight-evidence-20260918.md`](preflight-evidence-20260918.md)
- [`agent-experiment-protocol.md`](agent-experiment-protocol.md)
- [`agent-usage-and-permissions.md`](agent-usage-and-permissions.md)
- [`isolation-policy.md`](isolation-policy.md)
- [`launch-coordination-20260921.md`](launch-coordination-20260921.md)
- `scripts/benchmark.py`, `experiments/schema/runner-profile.schema.json`, and the
  local preflight/activation scripts.

The local OpenAI documentation skill was applied for Codex settings. The official
Codex CLI and configuration references confirm that `-c` overrides a configuration
key, `--model` selects a model, `--sandbox` selects a sandbox mode,
`--ask-for-approval` selects the noninteractive approval policy, and
`--ignore-user-config`/`--ignore-rules` are real `exec` options. The local executable
help remains the authority for the installed version. Reference:
<https://developers.openai.com/codex/cli> and
<https://developers.openai.com/codex/config-reference>.

## Checklist and evidence ledger

Status values are deliberately limited to `observed`, `blocked`, and `not-run`.
`observed` means a command produced the stated local
evidence; it does not mean that a model or product run is approved.

| Item | Status | Evidence | Remaining action |
|---|---|---|---|
| Repository/ref inventory | observed | This record; starting `git status`, HEAD, and diff summary | Keep all prior changes; choose a clean approved baseline later |
| Codex executable identity | observed | [`codex-cli-preflight-20260921.txt`](evidence/codex-cli-preflight-20260921.txt) | Re-run immediately before any future prepare; exact output must still match |
| Codex noninteractive argv shape | observed | Same evidence; version/help exits are recorded | Use only the candidate argv; no unlisted switch may be added |
| Candidate model/reasoning IDs | observed | Local model metadata excerpt in [`codex-cli-preflight-20260921.txt`](evidence/codex-cli-preflight-20260921.txt) | User chooses cohort; a future run must separately establish access/entitlement |
| Settings isolation | blocked | Runtime config inventory in the evidence file; explicit argv in candidates | Prove the effective profile used by the exact runner; do not call policy strings proof |
| ESP-IDF activation/version | observed | Activation exit 0; `idf.py --version` exit 0; ESP-IDF v5.3.2 | Repeat in the final clean selected checkout |
| ESP-IDF compile smoke check | observed | ASCII hello-world build exit 0; three binary hashes in the evidence file | This proves toolchain/build readiness only; repository product firmware is still absent |
| Offline repository validators/tests | observed | 81 tests, E2E, matrix, historical, host dry-run, and diff check exits recorded below | Repeat against the final frozen baseline |
| Profile schema/check | observed | `benchmark.py check --baseline HEAD` exit 0 for both candidates after UTF-8 environment fix | Re-run against the user-approved final tag; check is not approval |
| Baseline freeze | blocked | Working tree is dirty; Q2 pending | User decides whether to commit/tag after review; no tag here |
| Profile-bound receipt | blocked | No final baseline/profile decision and no receipt | Create receipt only after Q1/Q2 and final hash; `pilot_pass` remains false |
| R10 execution authorization | blocked | Existing conditional approval and coordination record | Verify whether the 2026-09-18 conditional approval applies after Q1/Q2 and all original conditions; request new approval only if the selected target/scope falls outside it |
| Product/model/hardware execution | not-run | No model call; no serial open; no flash | Remains outside this preparation task |

### Exact local executable probes

The following probes are safe metadata reads. They do not authenticate, call a model,
or start an agent session:

```powershell
& 'C:\Users\이광진\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe' --version
& 'C:\Users\이광진\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe' --help
& 'C:\Users\이광진\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe' exec --help
```

Observed exits: `--version` 0, `--help` 0, and `exec --help` 0. The exact output
excerpt and the installed path are preserved in the evidence file. No `exec` invocation
without `--help` was attempted.

The candidate command uses only options confirmed by that help:

```text
  codex.exe --ask-for-approval never exec --json --ignore-user-config --ignore-rules
  --ephemeral --sandbox workspace-write
  -c model_reasoning_effort="<max-or-medium>" -m <gpt-5.6-luna-or-gpt-5.6-sol> -
```

`reasoning` is represented by the confirmed `-c model_reasoning_effort=...` override;
there is no invented `--reasoning` flag. `workspace-write` is required for an agent
implementation checkout. The repository's `prompt-and-log` policy and
`read_isolation: not_enforced` boundary remain separate from this CLI sandbox flag.

The installed CLI accepts the exact candidate argument ordering in help mode for both
profiles (exit 0), including the `max` value. Help mode exits before authentication or
model resolution, so it does not prove that the selected account can execute Luna at
`max`. The local CLI catalog confirms the full model IDs and cached effort metadata;
request-time entitlement and acceptance remain untested. A generic online configuration
enum is not used to substitute another effort or create a separate design gate.

The first direct `benchmark.py check` attempt exited 1 because the PowerShell process
used the Windows `charmap` stdout codec while printing the Korean workspace path. The
same read-only check exited 0 after setting `PYTHONUTF8=1` and
`PYTHONIOENCODING=utf-8`; this is now included in the handoff command block. No source
or global setting was changed.

### Offline command results (2026-09-21)

| Command | Exit | Result |
|---|---:|---|
| `.\\scripts\\check-experiment-preflight.ps1` | 1 | Required files, IDF, validators, 81 tests, matrix, and COM3 presence passed; one real failure: 53 dirty-tree changes |
| `. .\\scripts\\activate-idf.ps1` | 0 | ASCII IDF environment activated; Python requirements satisfied |
| `idf.py --version` | 0 | `ESP-IDF v5.3.2` |
| `idf.py -B build-readiness-20260921 build` in the ASCII hello-world smoke project | 0 | ESP32-S3 compile/link produced expected binaries |
| `python -m unittest discover -s scripts/tests -p 'test_*.py' -v` | 0 | 81 tests passed |
| `python scripts/validate-end-to-end-result.py` | 0 | Valid example |
| `python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json` | 0 | Provider fixture matrix valid |
| `python scripts/validate-experiment-result.py` | 0 | Historical examples valid |
| `python scripts/run-host-device-pipeline.py --dry-run` | 0 | 3961 bytes rendered; `device_accessed=false` |
| `git diff --check` | 0 | Whitespace check passed |

The smoke build and host dry-run are offline checks. Neither is a product, model,
provider, hardware, or flash pass.

### Candidate input hashes against current committed HEAD

Both checks below used the committed `HEAD` SHA shown above. They did not include the
dirty working-tree changes and did not reserve a run ID or touch a checkout. The
semantic profile and bundle hashes are therefore provisional until Q2's baseline
decision creates a clean approved ref.

| Candidate | Check exit | Profile SHA-256 | Input bundle SHA-256 |
|---|---:|---|---|
| `gpt-5.6-luna/max` | 0 | `63fa2d7422cd2f40a5082009606619b65340ac105d77329b56bf2d521ac9617b` | `3684b6de3957bf527a4580c58b31b699e65cf46929b6c52a09c807c317011ee5` |
| `gpt-5.6-sol/medium` | 0 | `3074d641549ada29c5dd9e42ad3ca96f7c417079ebe0a0e3d916705ffcaa6ea4` | `84302797e74e7c5ca7efc879e1dbcdce10d501b1354e811b5c0e961d0eaefac0` |

Shared current-HEAD component hashes from both checks:

```text
baseline_commit=47b720d7f29185dd63a0d72737897966a4ea335f
prompt_sha256=f99d708ca9f3bdfc2134942c44e30b6c14bb7a098fe36f75ad5472c8210f4a77
config_sha256=aad878a590937c2e2e34235462d05b8e8f314b22dc404f8506b2117292035959
fixture_sha256=0a2964266df53a641dda4b4e9d460e2ffe990bfb38c6d40e32556610bbe42eec
schema_sha256=72f399b5bb1e0766ca49aca7e33106ceebd66f4edb4918ac695e5877d223ac8c
evaluation_criteria_sha256=a25717f1d0b0f6856a22c164785ba80b61a054554305e00451e30d5f26553f24
```

`prepare` must recompute these values on the final clean checkout. A future receipt's
`base_commit` must equal that check's `baseline_commit`, and its `profile_sha256` must
equal the same candidate's semantic profile hash. The prepared manifest must then
repeat both values and the bundle hash; this transitive binding is the reason a receipt
cannot be created for the current dirty tree.

### Settings and environment evidence

The current process exposes `CODEX_HOME` as an Orca runtime home rather than the
default user path. Its config inventory contains a read-only sandbox default and a
runtime model/reasoning default, plus plugin and skills links. The inventory includes
auth/session/cache files, but their contents were not read or copied. The repository
has no `.codex` directory at this capture point.

This observation is intentionally not a builtin-only pass. The candidate argv excludes
the user config and user/project rules for the future `exec` process, but the available
help does not establish that all custom skills, plugins, or MCP integrations are
disabled by those flags. The candidate settings inventory therefore records the exact
flags and the unresolved enforcement boundary. A future operator must inspect the
effective invocation and preserve a profile-bound receipt before using `prepare`.

### Follow-up prompt-context inspection (2026-09-22)

`codex debug prompt-input --help` exited 0 and describes a JSON renderer. The actual
`codex debug prompt-input` invocation exited 0 without a model/provider request. Its
sanitized shape was four messages, seven content blocks, and 29,474 text characters;
the output was held in memory and no prompt text was written or displayed. The current
session context contained 33 `SKILL.md` references and three `AGENTS.md` references,
which describes this Codex session and is not evidence about a future runner checkout.

The debug renderer has no `--ignore-user-config` or `--ignore-rules` option. Passing
either flag exited 2 with an unexpected-argument error, and the top-level form also
exited 2. Therefore this surface cannot emulate the candidate `exec` flags.

The current `CODEX_HOME` inventory, read by name/type only, has `skills` and `plugins`
Junctions, one `.rules` file under `rules`, and `config.toml`; the repository has no
project `.codex` directory. The candidate `exec` help explicitly documents that
`--ignore-user-config` skips `CODEX_HOME/config.toml` and `--ignore-rules` skips user or
project `.rules`. It exposes no `--ignore-*` equivalent for skills, plugins, or MCP;
the separately documented feature switches and their bounded probe are recorded below.
The factual disposition is therefore: user config/rule exclusion is configured in the
candidate argv, while builtin-only enforcement for skills/plugins/MCP remains blocked.
The concrete next fix is to bind a dedicated per-run execution environment or wrapper
that can be represented and verified by the runner profile/receipt; the current profile
schema has no environment field, so this task does not pretend that the host links are
disabled or add unsupported environment plumbing.

### Feature-flag follow-up (2026-09-22)

The exact commands and sanitized feature-state inventory are preserved in
[`codex-feature-controls-20260922.txt`](evidence/codex-feature-controls-20260922.txt).

The installed top-level and `exec` help both exited 0 and document `--enable <FEATURE>`
and `--disable <FEATURE>`, with the explicit equivalence
`-c features.<name>=true|false`. `codex features list` also exited 0 with these
overrides. The effective-state probe reported `plugins=false`, `skill_search=false`,
and `enable_mcp_apps=false` when those three features were disabled; enabling
`skip_host_skill_discovery` reported `true`.

The no-model `debug prompt-input` renderer provided a bounded behavior probe using
sanitized counts only. The baseline exited 0 with 32,644 serialized JSON characters,
33 `SKILL.md` references, and three `AGENTS.md` references. `--disable plugins`
exited 0 and reduced that to 25,201 characters, 16 `SKILL.md` references, and two
`AGENTS.md` references. `--disable skill_search`, `--disable enable_mcp_apps`, and
`--enable skip_host_skill_discovery` each exited 0 but produced no comparable
reduction. The combined three-disable probe exited 0 with 25,203 characters, 16
`SKILL.md` references, and two `AGENTS.md` references. No prompt text was displayed
or saved.

This supports a concrete candidate-argv proposal, still pending review and profile
update:

```text
codex.exe --ask-for-approval never exec --json --disable plugins
  --disable skill_search --disable enable_mcp_apps --ignore-user-config
  --ignore-rules --ephemeral --sandbox workspace-write
  -c model_reasoning_effort="<max-or-medium>" -m <approved-model-id> -
```

The observed reduction is evidence that the `plugins` feature override affects the
model-visible context; it is not a builtin-only pass. Residual skill context remains,
the skill/MCP-specific flags had no additional observable effect here, and the debug
renderer cannot emulate the candidate `exec` isolation flags. The runner still needs
an effective-context receipt that proves the selected flags and source inventory for
the future checkout. Candidate JSON files were not changed during this probe.

### Questions requiring an owner decision or operator evidence

| ID | Question | Owner | Answer/evidence required | State |
|---|---|---|---|---|
| Q1 | Is the first cohort exactly Codex Luna max and Codex Sol medium, or should the existing six planned entries be retained? | User | Explicit cohort list and one pilot per chosen entry | pending |
| Q2 | Should the reviewed dirty changes be committed and tagged as the new local baseline? | User/maintainer | Baseline commit/tag name and SHA after review | pending |
| Q3 | Does the exact candidate invocation enforce the intended `builtin-only-v1` condition? | Operator | Effective config/settings inventory and receipt; no policy-string-only claim | open |
| Q4 | Are `gpt-5.6-luna` and `gpt-5.6-sol` accepted model IDs for the selected Codex account? | Operator/user | A separately authorized lightweight access check or provider evidence; no benchmark call in this task | open |
| Q5 | Is the selected profile's `model_reasoning_effort` accepted for each model? | Operator/user | Explicit CLI/config acceptance evidence; record rejection without retrying as a different cohort | open |
| Q6 | Is the profile-bound preflight receipt tied to the final baseline/profile hashes? | Maintainer | `base_commit`, `profile_sha256`, evidence SHA-256, and `pilot_pass: false` | blocked |
| Q7 | Are COM3, board backup hash, and operator hardware checklist ready for the later pilot? | Hardware operator | Separate hardware evidence; no COM3 use here | blocked |
| Q8 | After all conditions, which phase/repetition is explicitly authorized? | User | Verify whether the 2026-09-18 conditional approval applies after Q1/Q2 and all original conditions; request new approval only if target/scope falls outside it | blocked |

## Offline preflight plan and handoff commands

Run these in a fresh PowerShell session from a clean selected baseline checkout after
the user resolves Q1/Q2. Until then, the commands are verification templates only.
They do not include `benchmark.py run`.

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
Set-Location 'C:\src\codex-desk-meter'
git status --short --branch
git rev-parse HEAD
. .\scripts\activate-idf.ps1
idf.py --version
git --version
python --version
ninja --version
cmake --version
python -m unittest discover -s scripts/tests -p 'test_*.py' -v
python scripts/validate-end-to-end-result.py
python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json
python scripts/validate-experiment-result.py
python scripts/run-host-device-pipeline.py --dry-run
git diff --check
python scripts/benchmark.py check --baseline <approved-baseline-tag> `
  --profile <approved-codex-candidate.json>
```

The existing `check-experiment-preflight.ps1` is also valid for the offline gate:

```powershell
.\scripts\check-experiment-preflight.ps1
```

It should be expected to return exit 1 while the working tree is dirty; that is a
real blocker, not a test failure to suppress. `-RequireHardware -Port COM3` is
outside this task and must not be added during this preparation.

After final review only, the documented sequence is:

```powershell
python scripts/benchmark.py check --baseline <approved-baseline-tag> --profile <approved-profile.json>
# obtain and review the profile-bound receipt
python scripts/benchmark.py prepare --baseline <approved-baseline-tag> `
  --profile <approved-profile.json> --root C:\Espressif\benchmark-runs `
  --seed 20260921 --phase pilot
# verify the conditional approval and explicitly activate R10
python scripts/benchmark.py run C:\Espressif\benchmark-runs\<run-id> `
  --receipt <preflight-receipt.json>
```

The final two commands are handoff instructions only. They are not executed by this
task. `prepare` itself is model-free but requires a clean checkout and is not R10.

## Next-step record

1. Sol medium's independent review is recorded in
   [`launch-review-sol-20260921.md`](launch-review-sol-20260921.md); its findings are
   reflected here, including the corrected smoke-build hash and the prompt-context
   isolation result.
2. After Q1/Q2, recompute the candidate profile and input bundle hashes against the
   clean selected baseline; the current-HEAD checks are explicitly provisional and
   non-authorizing.
3. Wait for Q1 and Q2. Do not replace the candidate files with a selected profile or
   make a commit/tag on assumption.
4. If Q1 selects the two-Codex cohort, operator verification must still establish
   model access, reasoning acceptance, builtin-only enforcement, and the profile-bound
   receipt before any prepare.
5. Before any prepare, compare the final check and prepare component/bundle hashes,
   and verify that the receipt `base_commit` and `profile_sha256` match the selected
   baseline and profile; reject the handoff on any mismatch.

## Evidence appendices

The companion evidence file contains the sanitized native help/version output and the
configuration inventory summary. It intentionally omits auth, cookie, token, session,
and cache contents. Subsequent command results must be appended as exact command,
exit code, and a secret-free output summary; do not copy raw credential-bearing logs.
