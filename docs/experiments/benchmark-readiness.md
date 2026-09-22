# Benchmark 실행 전 준비 gate

## 현재 상태

**상태: `PLANNING / NOT_AUTHORIZED`**

2026-09-18 설계 검토 후속 변경과 최신 host 검증은
[design-remediation-20260918.md](design-remediation-20260918.md)에 기록한다.
계약·fixture·IDF 활성화 보완과 host 시험 통과는 개별 실행 profile/receipt 확정이나
실물 합격을 뜻하지 않는다. R4/R5/R10의 미충족 조건은 해당 기록을 함께 확인한다.

이 문서는 에이전트 제품 구현을 실행하는 지침이 아니라, 실행해도 되는지 판단하는
운영 gate다. 현재 이 gate가 `AUTHORIZED`로 바뀌지 않았으므로 agent prompt를
수동으로 붙여넣거나 `benchmark.py run`을 실행하지 않는다. 문서 보완·schema·runner
자체 시험은 제품 실험 실행이 아니다.

## 기준 저장소

- 정식 기준 브랜치: `main`
- 보존 중인 historical baseline tag: `benchmark-v2-baseline-20260911`
- 해당 tag의 commit: `34a1790ffeb31d47c1ae78c78a14d7cf4e318c6f`
- 이후 main에 반영된 변경과 작업 트리의 문서 보완은 새 E2E baseline 후보다.
  현재 HEAD·변경 여부는 `git rev-parse HEAD`와 `git status`로 확인한다.
  검토·승인·commit/tag 및 입력 hash 동결 전에는 새 baseline으로 사용하지 않는다.
- `main-2`는 runner tooling을 추가한 중간 개발 브랜치이며, 앞으로의 기준은
  검토·승인된 `main` commit과 tag로만 정한다.
- `experiment/...` 브랜치는 한 agent의 동결 결과를 보관한다. 다음 run의 시작점으로
  사용하지 않는다.

2026-09-20 로컬 ref 확인에서는 `version-2-baseline-20260911`과
`benchmark-v2-baseline-20260914`도 존재한다. 위 태그와 서로 다른 commit이며,
태그 존재만으로 현재 E2E 계약의 동결·승인 증거가 되지 않는다. ref별 commit은
[문서 검토 기록](../DOCUMENTATION_REVIEW.md)에 보존한다.

입력 검사와 run 준비를 분리해 순환 의존을 해소했다. 현재 순서는 마지막 절과
[실행 가이드](agent-run-commands.md) §1~6을 따른다. 기존 조건부 승인 기록을
확인하고 로컬 prepare를 수행한 뒤, 준비 성공을 포함한 원래 조건이 모두
충족됐는지 확인해 R10을 발효한다. 문서 정비만으로 gate를 통과시키지 않는다.

## 역할 분리

| 역할 | 허용 작업 | 금지 작업 |
|---|---|---|
| 기준 저장소 maintainer | 목적·계약·prompt·schema·runner·평가 기준 수정 | 실험 중인 agent 결과를 main에 섞기 |
| agent | 깨끗한 checkout에서 제품 구현·자체 시험·결과 초안 작성 | manifest 조작, COM3 flash, private credential 요청 |
| 공통 evaluator | 동결된 artifact를 read-only로 평가 | 평가 중 코드 수정·수정 지시 |
| hardware operator | 승인된 artifact를 COM3에 flash하고 사진/영상·로그 수집 | 평가 전 임의 수정, erase_flash |
| remediation 작업자 | 평가 후 별도 branch에서 수리·개선 | 원본 benchmark commit·점수 덮어쓰기 |

## 실행 단계

```text
P0 목적·범위·계약 고정
        ↓
P1 runner/profile/access-policy/schema 준비 및 독립 검증
        ↓
P2 도구별 preflight와 preflight receipt 검토
        ↓
P3 사용자 승인 후 pilot 1회
        ↓
P4 pilot 합격 후 agent/model별 benchmark 반복
        ↓
P5 결과 동결 → 공통 평가 → 운영자 하드웨어 평가
        ↓
P6 필요 시 remediation 별도 실험
```

P0~P2 중 하나라도 완료되지 않으면 P3 이후로 진행하지 않는다. pilot은 운영
인프라를 검증하는 단계이지 제품 구현을 개선하는 단계가 아니며, 순위 통계에서
제외한다.

## 필수 gate

| Gate | 확인 조건 | 현재 상태 |
|---|---|---|
| R0 목적·범위 | 제품 목표, Version 2 계약, E2E product benchmark와 historical firmware prep 범위 분리 | `in_review` |
| R1 고정 입력 | prompt/config/fixture/schema/평가기준 commit·hash와 transport 선택 고정 | `not_ready` |
| R2 비교 항목 | F1~F9·I1~I4 기능표와 LCD G1~G6 rubric 확정 | `in_review` |
| R3 결과 계약 | feature_results·GUI 평가를 기록하도록 schema/validator/example 갱신 | `not_ready` |
| R4 profile | agent/product/interface/model/reasoning/버전/argv 확정 | `not_ready` |
| R5 preflight receipt | compiler·Ninja·Git·TEMP·ASCII 경로·참조 제한·활동 로그·네트워크·설정 증거; OS 격리 선택 | `not_ready` |
| R6 runner telemetry | 시작·종료·단조 시간·명령·실패·사용자 개입·raw log·token 원본 | `partial` |
| R7 one-shot 경계 | prompt 1회, 실행 중 외부 피드백 0회, evaluator read-only | `not_ready` |
| R8 host 평가 | production parser/state와 fixture collector·transport의 오류·stale·복구 시험 | `not_ready` |
| R9 하드웨어 안전 | 제조사 기준 백업 hash, COM3 단독 점유, erase 금지, 운영자 checklist | `not_ready` |
| R10 승인 | 사용자가 해당 baseline·profile·pilot 실행을 명시적으로 승인 | `not_authorized` |

R3 결과 계약과 R1/R3의 transport 설계에는 Waveshare 공식
[`waveshareteam/codex-meter`](https://github.com/waveshareteam/codex-meter)를 참조할 수
있다. 참고 범위와 provenance·라이선스·보드 차이·검증 경계는
[PC 수집기–ESP32 통합 계약 초안](integration-contract.md)의 “외부 참조 구현”을
따른다. 참고했다는 사실만으로 gate 상태를 `pass`로 바꾸지 않는다.

R1~R3을 확정할 때에는 다중 provider fixture matrix도 고정한다. 최소 대상은 Codex,
Claude Code, Antigravity CLI(Google 기본), Orca/IDE host와 unsupported
provider이며 (`gemini-cli`는 Enterprise/API 키 conditional),
source가 제공하지
않는 절대 token 잔량을 추정하지 않는 계약을 포함한다. matrix 본문
(`experiments/fixtures/provider-fixture-matrix.json`)과 provider adapter 결과
schema·validator·example은 존재하며, 남은 작업은 baseline commit·hash 동결과
검토 기록이다. 동결 전이므로 R1/R3은 계속 `not_ready`다.

### 현재 검증 증거와 남은 조건 (2026-09-21)

위 gate 상태는 실행 준비 판정이며 코드 구현 여부와 구분한다.
최신 검증 기록은 [진행 체크리스트](../DOCUMENTATION_REVIEW_CHECKLIST.md)에 있다.

| Gate | 확보한 증거 | 남은 조건 |
|---|---|---|
| R0/R2 | 목적·C/F/G/I 계약과 비교 항목 정비 | 최종 범위·ADR 검토 기록 |
| R1 | check/prepare 공통 hash 시험 | 최신 변경을 포함한 commit/tag·최종 hash 동결 |
| R3 | E2E·historical·fixture matrix validator 통과 | 동결 기준선 재검증·검토 기록, CI 증거는 별도 |
| R4/R5 | draft 3종의 sentinel 거부 확인 | 실제 model/reasoning/버전/settings 확정·profile-bound receipt |
| R6/R7 | 토큰·timeout·runner 오프라인 시험 | 선택 CLI의 로그·telemetry·one-shot 전달 증거 |
| R8 | 전체 81개 시험, host dry-run 3961 bytes, device_accessed=false | 동결 기준선·환경 확인; 실물/production 합격으로 대체 불가 |
| R9 | 운영 checklist 문서 | 보드·백업 hash·COM3 단독 점유 실측 |
| R10 | 2026-09-18 조건부 승인 기록 보존 | 대상 일치 및 prepare 성공 등 원래 조건 충족 확인 |

### Gate 종료 산출물과 책임자

| Gate | 종료 산출물 | 책임자 | 완료 판정 |
|---|---|---|---|
| R0 | 목적·cohort·C/F/G/I 범위 diff | maintainer | historical prep와 E2E 제품 합격 조건에 모순 없음 |
| R1 | hash가 고정된 prompt/config/fixture bundle과 transport ADR | maintainer | 모든 agent가 동일 입력·transport를 사용 |
| R2 | 다중-provider capability/fixture matrix와 GUI rubric | maintainer | Codex·Claude·Antigravity·Orca host·unsupported 사례 포함 |
| R3 | E2E schema, validator, valid/invalid examples와 CI log | maintainer | F1~F9·I1~I4·G1~G6 및 provider/host identity를 기계 검증 |
| R4 | surface별 profile 파일 | maintainer | product/interface/model/reasoning/version/argv 확정 |
| R5 | preflight receipt example과 preflight log | runner maintainer | 경로·도구·네트워크·쓰기 범위 재현 가능 |
| R6 | raw log·시간·명령·token telemetry example | runner maintainer | 미제공 값은 null과 사유로 보존 |
| R7 | one-shot 위반 감지 시험 | runner maintainer | prompt 1회, 시도된 follow-up은 위반 증거로만 보존 |
| R8 | collector·normalizer·transport·receiver host/integration test log | evaluator maintainer | 오류·stale·복구·provider 격리 통과 |
| R9 | artifact/flash/COM3 운영 checklist | hardware operator | hash·단독 점유·비파괴 절차 확인 |
| R10 | 대상 baseline/profile/run 수가 적힌 사용자 승인 기록 | user | 명시 승인 전 실행 불가 |

R0~R9 증거와 해당 baseline/profile에 적용되는 승인 기록을 확인한 뒤 로컬
`prepare`로 ID를 예약할 수 있다. 조건부 승인의 prepare 성공 등 잔여 조건을
모두 확인해 R10을 발효하기 전에는 prompt를 전달하지 않는다.
`not_run`, `partial`, `blocked`를 `pass`로 바꾸어 gate를 통과시키지 않는다.

## 한 번의 정식 run 규칙

1. runner가 새 checkout, manifest, 실제 prompt, profile, receipt를 만든다.
2. runner가 `<run-id>`를 치환한 prompt를 agent에게 정확히 한 번 전달한다.
3. agent는 실행 중 자체적으로 빌드·시험·수정을 반복할 수 있지만, 운영자·evaluator가
   오류 원인이나 구현 방향을 알려주지 않는다.
4. agent 종료 후 branch와 결과 파일을 동결한다. 이 시점 전후의 수동 코드 수정은
   benchmark run에 포함하지 않는다.
5. evaluator가 동결된 artifact를 read-only로 공통 시험하고, operator가 별도 승인 후
   COM3 하드웨어 시험을 수행한다.
6. 문제를 고치려면 평가 결과를 먼저 저장한 뒤 `remediation/<run-id>-...`에서 한다.

다른 agent에 prompt를 직접 복사·붙여넣은 수동 실행은 정식 benchmark가 아니라
`manual pilot; invalid for cross-agent quantitative comparison`으로 기록한다.

## 제품 데이터 범위

정식 `version-2-end-to-end-v1` benchmark는 계정 쿠키·API key·Wi‑Fi 자격증명 없는
표준 fixture collector와 로컬 transport를 사용한다. 현재 r01처럼 펌웨어에
fixture를 직접 내장하는 것은 historical preparation 자료로만 인정한다. 실제
제품은 다음 interface를 모두 연결해야 한다.

```text
PC provider collectors
        ↓ normalized UsageSnapshot / GlobalResetSnapshot
USB serial(COM3) `cdm/1` transport adapter (E2E baseline 고정)
        ↓ framed data
ESP32 receiver → validation/cache/stale → common state → LCD GUI
```

local Wi-Fi 운용은 별도 cohort에서 비교하며, E2E baseline의 transport 선택을
대체하지 않는다. baseline(`experiments/config/version-2-baseline.yaml`)의
`transport_choice: usb-serial-cdm-1`이 단일 진실이며, 본문의 “또는 local Wi-Fi”
표현은 선택지가 아닌 후속 cohort 항목으로 읽는다. transport 결정의 근거는
[ADR-0005](../decisions/0005-transport-usb-serial-baseline.md)를 따른다.

`UsageSnapshot`은 백분율과 함께 source가 제공하는 경우에만 used/remaining/limit
token 및 단위를 운반한다. source가 절대 quota를 공개하지 않으면 null과
`unit: percent|unknown`을 유지하며, agent나 runner가 임의의 token 총량을 추정하지
않는다.

검토 중인 E2E 계약의 transport 선택값은 USB serial(COM3) `cdm/1`이다.
ADR-0005 승인과 baseline 동결은 아직 남아 있다. local Wi-Fi 운용은
별도 cohort에서 비교한다. 실제 계정 source로의 전환은 별도의 owner-only live integration이다.
collector·transport·receiver를 구현·검증하기 전에는 “실시간 Codex 사용량 표시
완료”라고 보고하지 않는다. 계층별 frame·재연결·무결성 시험의 설계는
[통합 계약 초안](integration-contract.md)을 참고한다.

## 무효 처리 조건

다음 중 하나라도 발생하면 run을 정량 비교에서 제외한다.

- 기준 commit이 아닌 branch에서 시작
- prompt가 1회 초과 전달되거나 실행 중 구현 피드백·수정 지시가 제공됨
- runner manifest·preflight receipt·raw log·원본 token telemetry가 없음
- 실행 후 사람이 같은 branch의 코드를 수정하고 원본과 구분하지 않음
- fixture/reference test를 production C 또는 hardware 합격으로 주장
- COM3 artifact·보드·flash hash를 확인하지 않고 hardware pass를 기록
- 범위 밖 PC integration을 구현하지 않았는데 제품 전체 pass로 표시

## 승인 방법

2026-09-18의 [조건부 pilot 승인 기록](preflight-evidence-20260918.md)은 보존한다.
아직 충족되지 않은 모델·설정·동결·receipt 조건과 R10 발효를 구분하며, 문서 정비로
승인을 새로 부여하거나 기존 조건부 승인을 취소하지 않는다.

승인은 모든 R0~R9를 증거와 함께 검토한 뒤 사용자가 특정 baseline, profile, 실행
표면, 반복 번호와 pilot/benchmark 여부를 명시하는 방식으로 남긴다. 승인 전에는
현재 저장소의 prompt와 실행 명령을 읽거나 시험할 수는 있지만 agent process를
시작하지 않는다.

## Current review addendum (2026-09-13 snapshot)

The offline readiness review is recorded in
[`readiness-review-20260913.md`](readiness-review-20260913.md). The R0-R10 statuses
below are that review's snapshot, not the current norm: R0 `in_review`, R1
`in_review`, R2 `in_review`, R3 `in_review`, R4 `not_ready`, R5 `not_ready`,
R6 `partial`, R7 `not_ready`, R8 `partial`, R9 `not_ready`, and R10
`not_authorized`. The gate table above (§필수 gate) is authoritative for the
current status.

Current policy (2026-09-14): [isolation-policy.md](isolation-policy.md) defines
`prompt-and-log` as the default: current main inputs in a dedicated checkout,
prompt restrictions against other branches/prior results, and activity/reference logs.
Docker/VM is optional. Quantitative comparison is allowed with the same declared
conditions and adequate evidence. OS read isolation is recorded as `not_enforced`.
R5 remains `not_ready` pending a reviewed policy-bound preflight receipt;
R10 remains `not_authorized`. Actual reference violations and incomplete manual
delivery/evidence remain comparison exclusions.

All checks in this review are read-only/offline. A host simulation is not I3/I4
or a hardware pass, and no candidate-agent run, provider access, serial open,
ESP32 operation, or firmware/LCD implementation was performed. Profiles remain
operator-check-only sentinels; final baseline hashes and any commit/tag require
explicit user approval.

## Linear preparation order (N1)

The gate order is intentionally acyclic: run the runner's input/profile `check`
without reserving a run ID; freeze and hash the selected baseline; obtain a
profile-bound preflight receipt; verify the applicable approval record; run
`benchmark.py prepare`; verify all remaining conditional-approval requirements
and record R10 activation; only then run `benchmark.py run`. `prepare` repeats the
baseline/profile checks immediately before reserving an ID. A readiness gate
must not require a prepared run as its own evidence, and a prepared run is not
an authorization. R4 remains `not_ready`, R5 remains `not_ready`, and R10
remains `not_authorized` until the operator supplies the missing evidence.
