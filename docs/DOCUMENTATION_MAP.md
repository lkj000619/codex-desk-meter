# 문서 지도

문서를 후보 입력·운영/평가·과거 기록으로 구분한다. 모든 MD를 읽는 절차는 없다.
한 요구사항을 여러 문서에서 정의하지 않는다. 제품 동작의 원본은 제품 계약과 JSON schema,
새 비교 운영 규칙의 원본은 운영 계약이다. 문서/schema가 충돌하면 결함으로 기록한다.

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
| 새 운영 규칙 | [운영 계약](experiments/comparison-operating-contract.md) |
| Codex 기능 도달 판정 | [RM 목록](experiments/reference-match-matrix.md) |
| 수정 작업·의존 순서 | [계획](superpowers/plans/2026-10-02-experiment-contract-remediation.md) |
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
- [기존 단회 프로토콜](experiments/agent-experiment-protocol.md)·
  [기존 gate](experiments/benchmark-readiness.md)는 해당 historical cohort에만 적용한다.
- [원본 evidence](experiments/evidence/)는 파일/hash 보존을 위해 경로·내용을 유지한다.
  evidence가 참조하는 [AGY launch 검토](experiments/agy-launch-review-20260925.md)·
  [초기 preflight](experiments/preflight-evidence-20260918.md)도 기존 경로에 남겼다.
- [보드 bring-up](hardware/version-2-bring-up.md)·[제조사 재현](hardware/waveshare-manufacturer-example.md),
  [HTML overview](overview/index.html), [결과 인덱스](../results/README.md)는 관측 시점·대상을 확인한다.

archive를 포함한 과거 기록의 `현재`·`승인`·`남은 작업`은 해당 시점의 표현이다.
이전 commit/tag의 동결 파일은 Git 이력에서 복구하며 새 입력 조건을 과거 실행에 소급하지 않는다.
