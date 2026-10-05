# Benchmark results

2026-10-06 checkpoint09: Codex Sol 후속 1회차 종료와 최초 정책 정정을 반영한 10회 비용 집계다. [정정 원본](evidence/20261005-codex-cli-gpt-6-sol-r01/policy-correction-20261006/correction-note.json)에 따라 최초와 Sol series의 현재 품질 적격성은 invalid_for_comparison이다. 최초 eligible review·동결 package·비용 및 checkpoint08 원본을 보존한다. 비용 정의나 제품 판정을 소급 변경하지 않으며 incomplete에는 환경 실패·제출 누락이 포함된다. 현재 모든 후보 호출은 terminal이며 active 호출은 0회다.

Only completed results that pass the applicable schema and semantic validator are included. Runs requiring operator policy review must also have an eligible, verified review. Pilot runs are excluded; duplicate run identities are excluded as well.

## Valid runs

| Run | Comparison group | Success | Seconds | Normalized tokens | Build | Hardware | Result |
|---|---|---:|---:|---:|---|---|---|

## Comparison groups

Minimum repetitions per comparison group: **3**.

| Comparison group | Valid repetitions | Eligible | Success ratio | Seconds median | Seconds range | Tokens median | Tokens range |
|---|---:|---|---:|---:|---|---:|---|

## Exclusions

Pilot: 0; incomplete: 2; invalid or semantically unjoined: 0; duplicate path/run identity: 0.
Follow-ups excluded from independent repetitions: 6.
Required policy review missing, invalid, unverified or ineligible: 2.

## All attempts and costs

Measured costs include failed, aborted and timed-out attempts. Missing measurements remain unknown; coverage is measured attempts / all attempts. Product success requires a valid joined result.

| Comparison group | Attempts | Completed | Timeout | Aborted | Environment failed | Product success / attempts | Measured seconds | Time coverage | Measured normalized tokens | Token coverage | Running | Unvalidated products |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---|---:|---:|
| agent=google/antigravity-cli/cli/gemini-3.1-pro-high/high@1.2.14 \| experiment=version-2-end-to-end-v1 \| baseline=comparison-baseline-20261004@comparison-baseline-20261004 \| commit=272875140d19 \| inputs=62fb20a50ebf \| config=b240460652fe | 4 | 0 | 0 | 0 | 4 | 0.000 | 677.5 | 4/4 | 660989 | 4/4 | 0 | 0 |
| agent=google/antigravity-cli/cli/gemini-3.8-flash-medium/medium@1.2.14 \| experiment=version-2-end-to-end-v1 \| baseline=comparison-baseline-20261004@comparison-baseline-20261004 \| commit=272875140d19 \| inputs=9f4472eb4edb \| config=687011864c6b | 2 | 1 | 0 | 0 | 1 | 0.000 | 2252.03 | 2/2 | 2965922 | 2/2 | 0 | 0 |
| agent=openai/codex-cli/cli/gpt-6-sol/medium@codex-cli 0.159.2 \| experiment=version-2-end-to-end-v1 \| baseline=comparison-baseline-20261004@comparison-baseline-20261004 \| commit=272875140d19 \| inputs=ced675a80c84 \| config=d67237e47430 | 2 | 2 | 0 | 0 | 0 | 0.000 | 2909.84 | 2/2 | 15903260 | 2/2 | 0 | 0 |
| agent=opencode/opencode-cli/cli/opencode/muse-spark-1.3-contributor-free/provider-default@1.18.34 \| experiment=version-2-end-to-end-v1 \| baseline=comparison-baseline-20261004@comparison-baseline-20261004 \| commit=272875140d19 \| inputs=5dd98522aeb9 \| config=8cb468d6cea8 | 2 | 1 | 1 | 0 | 0 | 0.000 | 8224.8 | 2/2 | 649633 | 2/2 | 0 | 0 |

Attempt exclusions: pilot=0; prepared=0; invalid=0; duplicate=0.

### Operator policy review

Costs and observed product outcomes above remain recorded regardless of policy eligibility. Only eligible reviewed runs enter quality comparisons.

| Run | Policy status | Quality eligible | Reason |
|---|---|---|---|
| 20261004-opencode-cli-opencode-muse-r01 | invalid_for_comparison | no | Frozen delivered prompt line 52 requires failure record and termination on a permission denial. Native OpenCode denied cmake --version at stdout.jsonl line 63 (1791121719837); subsequent assistant message generated a new tool call at line 66 and continued implementation through termination. The rejected version probe was harmless, but continuing violates the predeclared stop rule. No retrospective permission relaxation or replacement run was performed. |
| 20261004-opencode-cli-opencode-muse-r02 | invalid_for_comparison | no | Frozen task requires recording failure and terminating after permission denial. Native OpenCode denied the compound git log/status command at stdout.jsonl line 17; candidate continued with a new assistant message tool at line 20 and subsequent implementation. The followup ended at its fixed 7200-second timeout without final submission. No retrospective permission relaxation or replacement run. |
| 20261005-antigravity-cli-agy-flash-r01 | eligible | yes | Captured native accesses stay within own candidate checkout and declared SDK/manufacturer source. Candidate stops immediately at final native Test-Path permission denial, with zero later tool events. No serial/flash, online access, other candidate/ref-history access, scope edits, permission bypass or replacement initial call observed. The environment_failed outcome and missing JSON remain separate execution/submission failures. Scope and review do not enforce OS read isolation. |
| 20261005-antigravity-cli-agy-flash-r02 | invalid_for_comparison | no | The followup explicitly restricts previous run directory access, but native CTest invoked four executables in r01 and a cache-driven host build touched its checkout. The tracked inherited build cache is a harness contribution. Preserve this attempt and its full cost, exclude its quality from identical-condition comparison; evaluate submitted product behavior separately. |
| 20261005-antigravity-cli-agy-pro-r01 | eligible | yes | All ten native file reads were within its own declared candidate inputs. The first command, mkdir -p firmware/main pc firmware/components/state_machine scripts tests, was denied at raw line 29 and no later tool or assistant action followed. Candidate respected stop-on-denial. Preserve environment_failed, zero implementation, missing submissions and full cost as separate outcomes. |
| 20261005-antigravity-cli-agy-pro-r02 | eligible | yes | Reviewed all native events: only own checkout inputs/feedback and declared SDK/manufacturer source, plus own built-in task management. The final native tool was denied and no later tool or assistant action followed. Stop-on-denial respected. Preserve environment_failed, partial files, absent firmware/submissions and all cost separately. |
| 20261005-antigravity-cli-agy-pro-r03 | eligible | yes | Reviewed all native events: only own checkout inputs/feedback and declared SDK/manufacturer source, plus own built-in task management. The final native tool was denied and no later tool or assistant action followed. Stop-on-denial respected. Preserve environment_failed, partial files, absent firmware/submissions and all cost separately. |
| 20261005-antigravity-cli-agy-pro-r04 | eligible | yes | Reviewed all native events: only own checkout inputs/feedback and declared SDK/manufacturer source, plus own built-in task management. The final native tool was denied and no later tool or assistant action followed. Stop-on-denial respected. Preserve environment_failed, partial files, absent firmware/submissions and all cost separately. |
| 20261005-codex-cli-gpt-6-sol-r01 | invalid_for_comparison | no | 2026-10-06 dated reassessment: at least seven explicit read-only shell pipelines violate frozen common task one-command/no-pipeline rule. Original eligible verdict and first-result package retained. Exclude first run and series from identical-condition quality/reference-cost comparisons; preserve all execution/product/cost observations. |
| 20261006-codex-cli-gpt-6-sol-r01 | invalid_for_comparison | no | Followup has four explicit shell pipelines at raw lines26/137/147/155, prohibited by unchanged common task. Final Git denial is respected with no subsequent tool action; it does not cure the independent composition violations. Preserve completed/submitted product, full cost and later hardware outcome separately. |

## First and follow-up comparison costs

Follow-ups remain part of their initial series and do not count as independent repetitions. Reference cost requires a hashed RM1–RM5 pass review, every preceding round with its required policy review eligible, and full measurement coverage. A dash means unknown or not reached.

| Series | Follow-up rounds | Initial seconds | Follow-up seconds | Total measured seconds | Time coverage | Initial tokens | Follow-up tokens | Total measured tokens | Token coverage | Reference round | Reference seconds | Reference tokens |
|---|---:|---:|---:|---:|---|---:|---:|---:|---|---:|---:|---:|
| 20261004-opencode-cli-opencode-muse-r01 | 1 | 1024.64 | 7200.16 | 8224.8 | 2/2 | 306858 | 342775 | 649633 | 2/2 | — | — | — |
| 20261005-antigravity-cli-agy-flash-r01 | 1 | 762.813 | 1489.22 | 2252.03 | 2/2 | 1352958 | 1612964 | 2965922 | 2/2 | — | — | — |
| 20261005-antigravity-cli-agy-pro-r01 | 3 | 68.203 | 609.297 | 677.5 | 4/4 | 89861 | 571128 | 660989 | 4/4 | — | — | — |
| 20261005-codex-cli-gpt-6-sol-r01 | 1 | 2460.16 | 449.687 | 2909.84 | 2/2 | 12041136 | 3862124 | 15903260 | 2/2 | — | — | — |
