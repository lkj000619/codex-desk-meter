# 문서 역할과 기준 안내

## 읽는 순서와 상태 해석

1. [프로젝트 목적](PROJECT_PURPOSE.md): 제품과 실험을 만드는 이유, 현재·후속 범위.
2. [제품 계약](PRODUCT_CONTRACT.md): 구현할 동작과 합격 조건.
3. [기능·GUI 비교](experiments/feature-comparison.md),
   [평가 interface](experiments/evaluation-contract.md),
   [통합 계약](experiments/integration-contract.md): 평가와 계층별 상세 계약.
4. [실험 프로토콜](experiments/agent-experiment-protocol.md),
   [운영 관리](experiments/benchmark-management.md),
   [접근 정책](experiments/isolation-policy.md): 동일 조건·역할·증거 보존.
5. [readiness gate](experiments/benchmark-readiness.md): 현재 실행 가능 여부와 잔여 조건.
6. 승인된 실행의 [공통 prompt](../experiments/prompts/version-2-agent-task.md)와
   [실행 가이드](experiments/agent-run-commands.md).

주제별 기준 문서가 요구사항을 소유하고 다른 문서는 이를 참조한다. 충돌 시
날짜가 최신이라는 이유만으로 우선하지 않는다. 적용 cohort·승인 상태·대체 관계를
확인하고, 문서와 schema/code가 다르면 결함으로 기록한다. 구현이 있다는 이유로
요구사항을 낮추거나 문서만으로 구현 완료를 선언하지 않는다.

- **승인 ADR:** 승인된 결정과 그 적용 범위를 기록한다. ADR-0002는 대체된 기록이다.
- **검토 중 계약:** 현재 main의 E2E 작업 기준. USB·가로·단일 출처 선택값이 반영되어
  있지만 ADR-0005/0006은 제안 상태이며 R1 승인·baseline 동결 대기다.
- **계획·제안:** 작업 순서나 변경안을 설명한다. 현재 구현·gate 상태를 보장하지 않는다.
- **시점별 증거:** 명시된 날짜·commit·대상에서 관측한 결과다. 당시 `현재`·`미커밋`·
  `남은 작업`을 오늘의 상태로 읽지 않는다. 과거 실물 사진·로그는 새 artifact의 증거가 아니다.
- **예제:** schema·오류 검사 입력이다. preflight 예제의 HEAD·순서·태그는 실측 receipt가 아니다.

현재 실행 상태는 readiness gate의 본문 표에서 확인한다. 조건부 승인 기록과 승인
전제조건 충족은 구분한다. 문서 정비·host 검사 완료는 R10 발효가 아니다.

## 문서 목록

2026-09-20 검토 시작 HEAD의 추적 MD 42개를 모두 검토했다. 아래는 해당 목록이다.
추가된 문서 지도·검토 보고서·진행 체크리스트는 마지막 절에 별도로 연결한다.

| 문서 | 역할·상태 |
|---|---|
| [README](../README.md) | 진입점·요약; 상세 요구사항은 아래 기준 문서 참조 |
| [PROJECT_PURPOSE](PROJECT_PURPOSE.md) | 목적·현재 범위·후속 목표 |
| [PRODUCT_CONTRACT](PRODUCT_CONTRACT.md) | 검토 중 E2E 제품 계약, C/I 합격 조건 |
| [DEVELOPMENT_ENVIRONMENT](DEVELOPMENT_ENVIRONMENT.md) | 개발 절차와 날짜별 환경 관측 |
| [ADR-0001](decisions/0001-use-esp-idf.md) | 승인: ESP-IDF 사용 |
| [ADR-0002](decisions/0002-version-1-first.md) | 대체됨: Version 1 우선 개발 당시 기록 |
| [ADR-0003](decisions/0003-version-2-first.md) | 승인: Version 2 우선; 화면 변경 제안은 ADR-0006 참조 |
| [ADR-0004](decisions/0004-pin-esp-idf-5.3.2.md) | 승인: Version 2 ESP-IDF v5.3.2 |
| [ADR-0005](decisions/0005-transport-usb-serial-baseline.md) | 제안: USB serial 선택; R1 승인·동결 대기 |
| [ADR-0006](decisions/0006-resets-single-landscape-default.md) | 제안: 단일 출처·가로 기본; R1 승인·동결 대기 |
| [하드웨어 기능 카탈로그](hardware/version-2-capabilities.md) | 고정 입력 후보, 제조사·과거 관측 근거 |
| [bring-up 기록](hardware/version-2-bring-up.md) | 2026-09-11 보드 관측; 현재 제품 합격 아님 |
| [제조사 예제](hardware/waveshare-manufacturer-example.md) | 재현 절차와 2026-09-11 증거 |
| [실험 프로토콜](experiments/agent-experiment-protocol.md) | 실험 단위·공정성·역할·평가 절차 |
| [실행 가이드](experiments/agent-run-commands.md) | 준비·실행·평가 명령과 도구의 현재 한계 |
| [사용법·계측·권한](experiments/agent-usage-and-permissions.md) | 날짜별 CLI 관측과 계측·권한 설정 안내 |
| [운영 관리](experiments/benchmark-management.md) | baseline·run ID·반복·보존·게시 기준 |
| [readiness](experiments/benchmark-readiness.md) | 현재 R0~R10 상태의 기준 |
| [접근 정책](experiments/isolation-policy.md) | prompt-and-log·builtin-only-v1, 관측 한계 |
| [기능·GUI 비교](experiments/feature-comparison.md) | F1~F9·G1~G6 기준 |
| [평가 interface](experiments/evaluation-contract.md) | legacy host 회귀·실물 C 판정; E2E와의 경계 |
| [자율 기능 실험](experiments/hardware-feature-discovery.md) | 후보 3개·선택 1개·별도 30점 |
| [통합 계약](experiments/integration-contract.md) | 초안: I1~I4·논리/wire 매핑 |
| [host-device 계약](experiments/host-device-pipeline-contract.md) | cdm/1 bytes·순번·복구, host oracle 한계 |
| [E2E 구현 계획](experiments/e2e-contract-implementation-plan.md) | 도구 구현 계획; 실제 완료는 코드·검증 증거 참조 |
| [E2E readiness 제안](experiments/e2e-contract-readiness-proposal.md) | 과거 제안·후속 주석; 현행 gate 표 아님 |
| [host-device 구현 계획](experiments/host-device-pipeline-implementation-plan.md) | offline 인프라 계획; 제품 구현 승인 아님 |
| [설계 검토 후속 기록](experiments/design-remediation-20260918.md) | 2026-09-18 변경·63개 시험·잔여 조건 기록 |
| [preflight 증거](experiments/preflight-evidence-20260918.md) | 2026-09-18 초기 측정과 조건부 승인 기록 |
| [R4 profile 검토](experiments/r4-profile-resolution.md) | 2026-09-18 실측·후속 관측, draft 모델·설정 미확정 |
| [offline readiness 검토](experiments/readiness-review-20260913.md) | 2026-09-13/14 당시 검증·변경 목록 |
| [tooling 검증](experiments/tooling-readiness-20260911.md) | 2026-09-11 도구 관측과 후속 정책 주석 |
| [2차 검증](experiments/verification-report-2nd.md) | 2026-09-17 특정 branch/commit 평가; 최신 계약 증거 아님 |
| [OpenCode 준비 점검](experiments/opencode-preflight-check.md) | 당시 probe·archive 미완료 기록 |
| [OpenCode stdin probe](experiments/opencode-stdin-probe-20260914.md) | 2026-09-14 단순 응답 probe; 제품 실험 아님 |
| [OpenCode 실물 진단](experiments/opencode-hardware-diagnosis-20260914.md) | manual pilot 관측·미해결 원인; 정식 합격 아님 |
| [profile 안내](../experiments/config/runner-profiles/README.md) | 실행 불가 템플릿·현재 후보와 conditional 구분 |
| [결과 예제 안내](../experiments/examples/README.md) | synthetic valid/invalid 입력·검증 의미 |
| [legacy fixture 안내](../experiments/fixtures/README.md) | parser 입력·표시 범위·live 경계 |
| [provider fixture 안내](../experiments/fixtures/providers/README.md) | 합성 정상·오류 matrix; 실제 provider 능력 증명 아님 |
| [공통 prompt](../experiments/prompts/version-2-agent-task.md) | 승인된 runner만 전달하는 E2E 과제 |
| [결과 인덱스](../results/README.md) | main 게시 규칙; 정식 본 실험 결과 없음 |

## 기계 계약과 증거 연결

| 주제 | 문서 | 기계 계약·구현 | 검증 경계 |
|---|---|---|---|
| 현재 E2E 범위 | 제품·실험 계약 | [baseline YAML](../experiments/config/version-2-baseline.yaml), 공통 prompt | fixture-only E2E 범위이며 `live_api_allowed_after_fixture: false`; N2 완료. 계획값은 승인 receipt가 아님 |
| provider/window 모델 | 제품 §3 | [UsageSnapshot schema](../experiments/schema/usage-snapshot.schema.json), [fixture matrix](../experiments/fixtures/provider-fixture-matrix.json) | 합성 입력의 구조·의미 검증 |
| transport | 통합·host-device 계약 | [frame schema](../experiments/schema/cdm-frame.schema.json), [host oracle](../scripts/host_device_pipeline.py) | host 성공이 I3/I4 실물 pass 아님 |
| 운영 기록 | 실험 프로토콜 | [run manifest schema](../experiments/schema/run-manifest.schema.json), [runner](../scripts/benchmark.py) | 실행 계측; E2E 평가 manifest와 다름 |
| E2E 평가 | 제품·기능·평가 계약 | [평가 manifest](../experiments/schema/end-to-end-manifest.schema.json), [result schema](../experiments/schema/end-to-end-result.schema.json), [validator](../scripts/validate-end-to-end-result.py) | 오프라인 범위에서 C1~C8 판정·token 정규화·manifest/archive/summary 연결 완료 (N3~N5); 실물 제품 합격은 별도 |
| historical 결과 | 과거 cohort 자료 | [historical schema](../experiments/schema/hardware-feature-result.schema.json), [validator](../scripts/validate-experiment-result.py) | E2E 결과의 대체물 아님 |

2026-09-25 AGY pilot 준비에 대한 최신 독립 기록은
[AGY launch review](experiments/agy-launch-review-20260925.md)와
[독립 검토](experiments/agy-launch-sol-review-20260925.md)다. 둘 다 해당 날짜의
관측 기록이며, 현재 설정·실행 승인 또는 실물 검증을 보증하지 않는다. 현재 gate와
새 실행의 선행 조건은 [benchmark readiness](experiments/benchmark-readiness.md)에서 확인한다.

문서 정비 결과와 미해결 결정은 [검토 보고서](DOCUMENTATION_REVIEW.md), 중단 후
작업 재개는 [체크리스트](DOCUMENTATION_REVIEW_CHECKLIST.md)를 따른다.
