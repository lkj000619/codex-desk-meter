# Benchmark results

Only completed results that pass the applicable schema and semantic validator are included. Runs requiring operator policy review must also have an eligible, verified review. Pilot runs are excluded; duplicate run identities are excluded as well.

## Valid runs

| Run | Comparison group | Success | Seconds | Normalized tokens | Build | Hardware | Result |
|---|---|---:|---:|---:|---|---|---|

## Comparison groups

Minimum repetitions per comparison group: **3**.

| Comparison group | Valid repetitions | Eligible | Success ratio | Seconds median | Seconds range | Tokens median | Tokens range |
|---|---:|---|---:|---:|---|---:|---|

## Exclusions

Pilot: 0; incomplete: 0; invalid or semantically unjoined: 0; duplicate path/run identity: 0.
Follow-ups excluded from independent repetitions: 1.
Required policy review missing, invalid, unverified or ineligible: 1.

## All attempts and costs

Measured costs include failed, aborted and timed-out attempts. Missing measurements remain unknown; coverage is measured attempts / all attempts. Product success requires a valid joined result.

| Comparison group | Attempts | Completed | Timeout | Aborted | Environment failed | Product success / attempts | Measured seconds | Time coverage | Measured normalized tokens | Token coverage | Running | Unvalidated products |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---|---:|---:|
| agent=opencode/opencode-cli/cli/opencode/muse-spark-1.3-contributor-free/provider-default@1.18.34 \| experiment=version-2-end-to-end-v1 \| baseline=comparison-baseline-20261004@comparison-baseline-20261004 \| commit=272875140d19 \| inputs=5dd98522aeb9 \| config=8cb468d6cea8 | 2 | 1 | 0 | 0 | 0 | 0.000 | 1024.64 | 1/2 | 306858 | 1/2 | 1 | 0 |

Attempt exclusions: pilot=0; prepared=0; invalid=0; duplicate=0.

### Operator policy review

Costs and observed product outcomes above remain recorded regardless of policy eligibility. Only eligible reviewed runs enter quality comparisons.

| Run | Policy status | Quality eligible | Reason |
|---|---|---|---|
| 20261004-opencode-cli-opencode-muse-r01 | invalid_for_comparison | no | Frozen delivered prompt line 52 requires failure record and termination on a permission denial. Native OpenCode denied cmake --version at stdout.jsonl line 63 (1791121719837); subsequent assistant message generated a new tool call at line 66 and continued implementation through termination. The rejected version probe was harmless, but continuing violates the predeclared stop rule. No retrospective permission relaxation or replacement run was performed. |
| 20261004-opencode-cli-opencode-muse-r02 | missing | no | Required operator policy review is missing. |

## First and follow-up comparison costs

Follow-ups remain part of their initial series and do not count as independent repetitions. Reference cost requires a hashed RM1–RM5 pass review, every preceding round with its required policy review eligible, and full measurement coverage. A dash means unknown or not reached.

| Series | Follow-up rounds | Initial seconds | Follow-up seconds | Total measured seconds | Time coverage | Initial tokens | Follow-up tokens | Total measured tokens | Token coverage | Reference round | Reference seconds | Reference tokens |
|---|---:|---:|---:|---:|---|---:|---:|---:|---|---:|---:|---:|
| 20261004-opencode-cli-opencode-muse-r01 | 1 | 1024.64 | — | 1024.64 | 1/2 | 306858 | — | 306858 | 1/2 | — | — | — |
