# Sol medium independent launch-readiness review — 2026-09-21

## Verdict

The Luna preparation record is internally consistent after correction of one smoke
artifact hash. Its offline evidence is suitable for the owner decision and final
baseline-freeze workflow.

The experiment is **not start-ready**. Current disposition:
`READINESS_EVIDENCE_VERIFIED / BLOCKED / NOT_AUTHORIZED`.

No model/provider request, benchmark run, run-ID reservation, serial open, flash,
commit, tag, or push was performed in this review. The review preserved the existing
dirty working tree.

## Independent checks

| Check | Result |
|---|---|
| Candidate JSON/profile validation | Both candidates passed `benchmark.py check --baseline HEAD` with the UTF-8 process environment documented in the handoff |
| Run side effects | Both checks reported `run_id_reserved=false` and `worktree_touched=false` |
| Installed argv parsing | Exact Luna and Sol candidate argv, with `--help` substituted for execution, each exited 0 |
| Model metadata | Installed `codex debug models`/local cache exposes `gpt-5.6-luna` with `max` and `gpt-5.6-sol` with `medium`; this is metadata, not entitlement or successful-request evidence |
| 2026-09-22 prompt-context probe | `codex debug prompt-input` rendered the current session context only; it rejects `--ignore-user-config` and `--ignore-rules`, so it cannot verify the candidate `exec` isolation behavior |
| Evidence-file integrity | `docs/experiments/evidence/codex-cli-preflight-20260921.txt` SHA-256 is `20F92F22398315667784B8853236C8FB51E85EF0123B217C2D56C5CD27DE3C88` |
| Profile hashes | Luna `63fa2d7422cd2f40a5082009606619b65340ac105d77329b56bf2d521ac9617b`; Sol `3074d641549ada29c5dd9e42ad3ca96f7c417079ebe0a0e3d916705ffcaa6ea4` |
| Provisional input-bundle hashes | Luna `3684b6de3957bf527a4580c58b31b699e65cf46929b6c52a09c807c317011ee5`; Sol `84302797e74e7c5ca7efc879e1dbcdce10d501b1354e811b5c0e961d0eaefac0` |
| Smoke artifacts | Recomputed SHA-256 values match the corrected evidence for `hello_world.bin`, `bootloader.bin`, and `partition-table.bin` |
| Repository hygiene | `git diff --check` exited 0; the worktree remains dirty, so `prepare` and baseline tagging remain blocked |

The initial evidence truncated/mistyped the `hello_world.bin` hash. The evidence now
records the independently recomputed value
`B4AC66871E1C998E4FB6F4282FE47BEE666563E6212FD9FC69EBA8B9E58A82F7`.

The current-HEAD input checks are intentionally provisional. `HEAD`
`47b720d7f29185dd63a0d72737897966a4ea335f` does not contain the dirty working-tree
changes. A final clean commit/tag will change at least the baseline identity and may
change component and bundle hashes.

The 2026-09-22 evidence-only follow-up did not change either candidate profile. The
independently reproduced profile and input-bundle hashes remain the values above.

### Feature-control delta review — 2026-09-22

The feature-control evidence file independently hashes to
`201C6578DEF4A16339802F332EDD85B49CADC6069FCF434CAE57154C3437DC90`.
Installed help and feature-state output establish that `exec` accepts the proposed
controls and that the measured state can report `plugins=false`,
`skill_search=false`, `enable_mcp_apps=false`, and
`skip_host_skill_discovery=true`.

In the current-session prompt renderer, disabling plugins reduced `SKILL.md`
references from 33 to 16. This is evidence that the plugin override changes visible
context. It is neither a builtin-only pass nor a failure: the remaining references
were counted without source provenance, and built-in skill references are expected.
The renderer also does not reproduce the exact future `exec` invocation or checkout.

The candidate JSON files remain unchanged (file SHA-256 Luna
`5C001B4CF428D8D71DB91A1F41636F3FDB063833AAE551C0B529FB4A05562D0B`,
Sol `34D2CCB4EE0C4F2D0A9EC165F98FD7BE239F4BBE8FEB690E5D4331A338B44B97`).
Their existing semantic profile and provisional bundle hashes therefore remain valid.
The feature flags are a reviewed proposal only until the selected profiles include
them and a runner-bound receipt records both effective feature state and sanitized
source provenance. If the installed CLI cannot expose that evidence for the exact
execution, the runner needs a verifiable environment or wrapper implementation.

## Coordination acceptance questions

| # | Review question | Disposition | Evidence and remaining condition |
|---:|---|---|---|
| 1 | Do model, reasoning, argv, installed version, and evidence agree? | **Conditional pass** | Full model IDs, reasoning labels, `codex-cli 0.153.2`, argv ordering, installed help, and local model metadata agree. Account entitlement and successful runtime acceptance were not tested. |
| 2 | Is `builtin-only-v1` enforced rather than merely labeled? | **Blocked** | `--ignore-user-config`, `--ignore-rules`, and `--ephemeral` are present, but the runtime home still exposes linked skills/plugins. `debug prompt-input` cannot accept the candidate isolation flags and therefore cannot prove their effective context. Candidate prose and operator signoff are not enforcement evidence. |
| 3 | Do profile, baseline, check hashes, and receipt identify the same input? | **Blocked pending final ref/receipt** | The two provisional check outputs reproduce exactly. The runner deterministically derives the bundle from baseline commit/ref, semantic profile, and component hashes. No final baseline or receipt exists yet. |
| 4 | Are failures and unknowns represented honestly? | **Pass** | Dirty-tree preflight exit 1, initial Windows stdout encoding failure, COM3 presence-only observation, missing entitlement, and unresolved settings enforcement are recorded without promotion to pass. |
| 5 | Are the latest changes included in the selected baseline? | **Blocked** | The working tree is dirty and Q2 is unanswered. Current `HEAD` checks explicitly exclude those changes. |
| 6 | Are preparation, actual execution, and conditional authorization separated? | **Pass, manually enforced** | The handoff distinguishes `check`, baseline freeze, receipt, `prepare`, R10 activation, and `run`. The runner validates the receipt but does not machine-verify an R10 approval record; operators must preserve the documented gate. |
| 7 | Do operating commands match the actual files and CLI? | **Pass for handoff** | Profile paths, top-level `--ask-for-approval never` ordering, full model IDs, UTF-8 environment, and runner subcommands match the current files. Commands must be repeated from the final clean baseline. |
| 8 | Are tests/dry-runs kept distinct from product/model/hardware success? | **Pass** | The 81 offline tests, validators, host dry-run, help probes, and IDF smoke build are correctly scoped. COM3 was detected through OS inventory but was not opened or tested. |
| 9 | Is evidence preserved without secrets or overwriting unrelated work? | **Pass for reviewed artifacts** | Evidence contains sanitized metadata and hashes, while auth/session/cache contents are excluded. Existing tracked and untracked changes remain present. |
| 10 | Is the launch decision grounded in concrete baseline/profile/receipt state? | **Pass** | The handoff concludes `NOT_AUTHORIZED` and lists the missing decisions and evidence. It does not claim readiness from provisional hashes or offline checks. |

## Required decisions and remaining gates

Only Q1 and Q2 require an immediate user choice:

1. Choose the two Codex entries or retain the previously planned six-entry cohort.
2. Decide whether the reviewed change set should become a local baseline commit and
   new tag.

After those decisions, the maintainer can complete the following work offline:

1. Create the chosen clean baseline, rerun the offline suite and `benchmark.py check`,
   and record the final component, semantic-profile, and input-bundle hashes.
2. Resolve `builtin-only-v1` enforcement in the execution design. Either implement a
   runner-bound environment or wrapper that is represented in the profile schema,
   hashed, and verified by the receipt, or identify documented CLI disable controls
   for skills, plugins, and MCP that apply to the exact `exec` invocation. The current
   profile schema has no environment field, and `debug prompt-input` cannot emulate
   the candidate flags, so neither is an already-supported verification path.
3. After that implementation, collect offline effective-settings evidence using the
   exact runner-bound mechanism. An operator assertion alone cannot close this gate.
4. Create and review the profile-bound receipt with `pilot_pass: false`. The receipt
   must bind the final baseline commit and semantic profile hash and preserve the
   settings/network/build evidence hashes.

The client-side model spelling and effort metadata need no further offline discovery:
the installed catalog confirms `gpt-5.6-luna/max` and `gpt-5.6-sol/medium`, and the
candidate argument shapes parse in help mode. Account entitlement and successful
request-time acceptance cannot be established offline. They require provider evidence
or the authorized pilot; a rejection must remain a recorded result rather than being
silently substituted.

Hardware readiness is also an operator action rather than a user design decision:
record the board backup hash, COM3 exclusive ownership, and the hardware checklist.
OS device presence alone is insufficient.

Finally, apply the 2026-09-18 conditional approval only if Q1/Q2 and the selected
target remain within its scope and every original condition is satisfied. Otherwise
obtain a new target-specific approval. `benchmark.py prepare` may be used only after
the clean baseline, selected profile, receipt, and applicable approval record exist;
it remains non-authorizing. Do not deliver the prompt with `benchmark.py run` until
the remaining conditional requirements are met and R10 activation is recorded.

## Reviewed artifacts

- [`launch-readiness-20260921.md`](launch-readiness-20260921.md)
- [`codex-cli-preflight-20260921.txt`](evidence/codex-cli-preflight-20260921.txt)
- `experiments/config/verified-profiles-candidate/codex-cli-luna-max.candidate.json`
- `experiments/config/verified-profiles-candidate/codex-cli-sol-medium.candidate.json`
- [`launch-coordination-20260921.md`](launch-coordination-20260921.md)
- [`benchmark-readiness.md`](benchmark-readiness.md)
- [`agent-run-commands.md`](agent-run-commands.md)
- `scripts/benchmark.py`
