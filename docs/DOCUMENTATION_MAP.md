# 문서 지도

문서를 후보 입력·운영/평가·과거 기록으로 구분한다. 모든 MD를 읽는 절차는 없다.
한 요구사항을 여러 문서에서 정의하지 않는다. 제품 동작의 원본은 제품 계약과 JSON schema,
새 비교 운영 규칙의 원본은 운영 계약이다. 문서/schema가 충돌하면 결함으로 기록한다.

## 디렉터리 역할

| 디렉터리 | 보관하는 내용 |
|---|---|
| `decisions/` | 채택 범위·근거가 있는 ADR |
| `hardware/` | 공통 보드 사실·제조사 source·bring-up 자료 |
| `experiments/` | 운영·평가 계약과 현재 준비 상태, `evidence/`의 원본 관측 |
| `plans/` | 앞으로 할 작업·의존 순서·완료 조건. 채택 규칙과 실행 승인은 별도 원본을 참조 |
| `design/` | 구현 인터페이스·상태·증거 연결 설계. 제품·운영 규칙의 원본을 참조 |
| `overview/` | 관측 시점이 표시된 HTML 탐색 자료 |
| `archive/` | 날짜·대상·원본 판정을 보존한 과거 문서 |

계획은 도구 이름과 독립된 `plans/`에 둔다. 새 문서의 저장 위치와 이동 시 참조 갱신은
[프로젝트 지침](../AGENTS.md)을 따른다. 계획을 읽는 것만으로 남은 작업 전체의 실행을 시작하지 않는다.

## 후보 입력: 필수 MD 3개

| 순서 | 문서 | 역할 |
|---|---|---|
| 1 | [실행 과제](../experiments/prompts/version-2-agent-task.md) | 목표·범위·실행·제출 |
| 2 | [제품 계약](PRODUCT_CONTRACT.md) | C/I/F·데이터·wire·화면·시험 |
| 3 | [보드 자료](hardware/version-2-capabilities.md) | 핀·극성·설정·제조사 source |

[파일 allowlist](../experiments/config/agent-inputs.json)는 schema/fixture/예제/필요 도구를
정확한 경로로 고정한다. runner가 만든 `.benchmark-inputs/`는 식별자·평가 manifest 사본·
목록/hash다. 운영 profile·receipt·계측은 후보 checkout 밖에서 관리한다.
main에 문서가 존재한다는 이유로 후보에게 읽도록 제공하지 않는다.

## 운영자·평가자

| 용도 | 문서 |
|---|---|
| 다음 실험 준비·잔여 조건 | [준비 상태](experiments/next-comparison-readiness.md) |
| 다음 비교 모델·설정 | [2026-10-03 프로필](../experiments/config/next-profiles-20261003/README.md) · [GPT-6 갱신 계획](plans/2026-10-03-gpt6-comparison-profiles.md) |
| 2026-10-02 실행 준비의 원본 검증·동결 | [당시 준비 계획](plans/2026-10-02-experiment-launch-preparation.md) · [당시 준비 보고서](../results/experiment-preparation-20261002/report.md) |
| 새 운영 규칙 | [운영 계약](experiments/comparison-operating-contract.md) |
| Codex 기능 도달 판정 | [RM 목록](experiments/reference-match-matrix.md) |
| 수정 작업·의존 순서 | [계획](plans/2026-10-02-experiment-contract-remediation.md) |
| 문서 품질 검토 후속 보완 | [보완 계획](plans/2026-10-02-documentation-remediation.md) · [검토 원본](../results/documentation-assessment-20261002/review.md) |
| 평가 baseline·배점·일정 후속 정비 | [정비 계획](plans/2026-10-03-evaluation-baseline-remediation.md) · [재검토](../results/documentation-review-20261003/report.md) |
| 실험 실행 경계·hook·제한 검토 | [실행 경계 보고서](../results/experiment-execution-review-20261003/report.md) |
| 2026-10-04 정식 비교 시작 준비·완료 근거 | [선행 작업 계획](plans/2026-10-03-formal-comparison-launch-prerequisites.md) · [실행 준비 완료](../results/experiment-launch-preparation-20261004/report.md) |
| 정식 비교 실제 실행·재개 | [실행 계획](plans/2026-10-04-formal-comparison-execution.md) · [진행 기록](../results/formal-comparison-20261004/report.md) |
| 종료 후 artifact 보관 경로 보완 | [보완 계획](plans/2026-10-04-evidence-artifact-layout-remediation.md) · [독립 복원](../results/formal-comparison-20261004/operator-remediation-20261005/restore-audit.json) |
| timeout 재개·관측 전 보존·재업로드 | [복구 계획](plans/2026-10-05-timeout-evidence-recovery.md) · [복원 감사](../results/formal-comparison-20261004/timeout-preservation-20261005/restore-audit.json) |
| OpenCode 후속 최종 RM·예산 소진 | [최종 판정](../results/formal-comparison-20261004/review-finalization-20261005/reference-review.json) · [최종 복원](../results/formal-comparison-20261004/review-finalization-20261005/restore-audit.json) |
| AGY Flash 최초 평가 완료·후속 실행 | [평가 계획](plans/2026-10-05-agy-flash-initial-evaluation.md) · [최종 복원](../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r01/evaluation-final-20261005/restore-audit.json) |
| AGY Flash 후속 1회차 최종 평가·사용자 요청 대기 | [후속 평가 계획](plans/2026-10-05-agy-flash-followup-evaluation.md) · [최종 복원](../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-final-20261005/restore-audit.json) · [대기 지시](../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-final-20261005/operator-user-hold.json) |
| AGY Pro 최초·후속 3회 평가·회차 한도 종료 | [최초 계획](plans/2026-10-05-agy-pro-initial-launch.md) · [첫 후속 계획](plans/2026-10-05-agy-pro-followup-execution.md) · [남은 후속](plans/2026-10-05-agy-pro-remaining-followups.md) · [최종 복원](../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r04/evaluation-final-20261005/restore-audit.json) · [series 종료](../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r04/evaluation-final-20261005/operator-series-completion.json) |
| Codex Sol 최초 실행·재개 | [실행 계획](plans/2026-10-05-codex-sol-initial-launch.md) · [실제 시작](../results/formal-comparison-20261004/evidence/20261005-codex-cli-gpt-6-sol-r01/launch-20261005/native-start-observation.json) |
| Codex Sol 최초 평가·후속 선행 조건 | [평가 계획](plans/2026-10-06-codex-sol-initial-evaluation.md) · [최종 RM](../results/formal-comparison-20261004/evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/reference-review.json) · [독립 복원](../results/formal-comparison-20261004/evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/restore-audit.json) |
| Codex Sol 후속 1회차 평가·남은 후속 | [후속 계획](plans/2026-10-06-codex-sol-followup-execution.md) · [최종 복원](../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/restore-audit.json) · [남은 후속 계획](plans/2026-10-06-codex-sol-remaining-followups.md) |
| Codex Sol 후속 2회차 RM 완료·series 종료 | [완료 계획](plans/2026-10-06-codex-sol-remaining-followups.md) · [최종 RM](../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r02/evaluation-final-20261006/reference-review.json) · [최종 독립 복원](../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r02/evaluation-final-20261006/restore-audit.json) · [series 종료](../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r02/evaluation-final-20261006/operator-series-completion.json) |
| Codex Sol 최초 정책의 날짜 있는 정정 | [정정 원본](../results/formal-comparison-20261004/evidence/20261005-codex-cli-gpt-6-sol-r01/policy-correction-20261006/correction-note.json) · [후속1 비용 집계](../results/formal-comparison-20261004/comparison-checkpoint-09.md) · [관측 대기 당시 집계](../results/formal-comparison-20261004/comparison-checkpoint-10.md) · [Sol 종료 시점 비용](../results/formal-comparison-20261004/comparison-checkpoint-11.md) |
| Codex Luna 최초 검증·재업로드·검은 화면 평가·재개 | [시작 계획](plans/2026-10-06-codex-luna-initial-launch.md) · [실제 시작](../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r01/launch-20261006/native-start-observation.json) · [종료 확인](../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r01/terminal-status-20261006/terminal-status.json) · [평가·업로드 계획](plans/2026-10-06-codex-luna-initial-evaluation.md) · [최초 RM](../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r01/evaluation-20261006/reference-review.json) · [현재 비용 집계](../results/formal-comparison-20261004/comparison-checkpoint-12.md) |
| 비교 도구 명령·증거 형식 | [도구 안내](experiments/comparison-tooling.md) · [구현 계획](plans/2026-10-02-comparison-tooling.md) · [설계](design/2026-10-02-comparison-tooling.md) |
| 문제와 근거 | [세 에이전트 평가](experiments/architecture-review-20261002.md) |
| GUI/F 평가·host seam | [기능 평가](experiments/feature-comparison.md) · [평가 도구](experiments/evaluation-contract.md) |
| host oracle의 범위 | [pipeline 도구 안내](experiments/host-device-pipeline-contract.md) |
| 접근·보존·게시 | [접근 정책](experiments/isolation-policy.md) · [운영 관리](experiments/benchmark-management.md) |
| 환경·명령·profile | [개발 환경](DEVELOPMENT_ENVIRONMENT.md) · [실행 가이드](experiments/agent-run-commands.md) · [profile 안내](../experiments/config/runner-profiles/README.md) |
| 목표·결정 | [프로젝트 목적](PROJECT_PURPOSE.md) · [ADR](decisions/) |

reference 도달과 `product_pass`는 별도 판정이다. 후보 실패도 첫 결과로 보존한다.
운영자 자료를 후보에게 전부 읽히거나, 이전 구현·실험 결과를 공통 입력에 넣지 않는다.
후속 피드백은 자신의 직전 결과에 대한 고정 요구·관측·근거·남은 예산만 제공한다.

## 과거 기록

- [2026-09-29 비교 방향 전환](experiments/reference-comparison-20260929.md).
- [archive](archive/): 날짜별 검토·launch·진단·과거 제안 17개를 이동했다.
  [문서 검토](archive/reviews/DOCUMENTATION_REVIEW.md)와
  [당시 작업 체크리스트](archive/reviews/DOCUMENTATION_REVIEW_CHECKLIST.md)는 현재 준비 상태가 아니다.
- 2026-10-02에는 과거 구현 계획 2개를 `archive/plans/`로 보관했다:
  [2026-09-13 E2E 계약 계획](archive/plans/2026-09-13-e2e-contract-implementation-plan.md) ·
  [2026-09-13 host pipeline 계획](archive/plans/2026-09-13-host-device-pipeline-implementation-plan.md).
  원문과 당시 검증 기록을 보존하며 현재 작업은 `plans/`와 새 비교 준비 상태를 따른다.
- [기존 단회 프로토콜](experiments/agent-experiment-protocol.md)·
  [기존 gate](experiments/benchmark-readiness.md)는 해당 historical cohort에만 적용한다.
- [원본 evidence](experiments/evidence/)는 파일/hash 보존을 위해 경로·내용을 유지한다.
  evidence가 참조하는 [AGY launch 검토](experiments/agy-launch-review-20260925.md)·
  [초기 preflight](experiments/preflight-evidence-20260918.md)도 기존 경로에 남겼다.
- [보드 bring-up](hardware/version-2-bring-up.md)·[제조사 재현](hardware/waveshare-manufacturer-example.md),
  [HTML overview](overview/index.html), [결과 인덱스](../results/README.md)는 관측 시점·대상을 확인한다.

archive를 포함한 과거 기록의 `현재`·`승인`·`남은 작업`은 해당 시점의 표현이다.
이전 commit/tag의 동결 파일은 Git 이력에서 복구하며 새 입력 조건을 과거 실행에 소급하지 않는다.
