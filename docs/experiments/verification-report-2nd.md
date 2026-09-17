# 문서 2차 검증 보고서 (verification-report-2nd.md)

- **검증 일시**: 2026-09-17
- **검증 대상 브랜치/커밋**: `lkj000619/docs-verify-2nd-retry` (`aa54db5`)
- **검증 원칙 준수 확인**:
  - **READ ONLY 준수**: 본 보고서(`verification-report-2nd.md`) 작성 외 코드 및 문서 수정 일체 없음
  - **실행 금지 준수**: `git push` 미수행, 벤치마크 미실행, COM3 미접근, 실제 자격증명 미사용
  - **R10 상태**: `not_authorized` 상태 유지 확인

---

## 1. 1차 수정 확인

**종합 판정: PASS**

### 1.1 PRODUCT_CONTRACT C3 (동적 window 목록 + Codex 예시)
- **판정**: **PASS**
- **근거 파일 및 라인**:
  - `docs/PRODUCT_CONTRACT.md:84`:
    > `| C3 | 개인 사용량 | PC가 전달한 사용량 창(window) 목록을 표시. source가 제공하는 window를 모두 표시하고(예: Codex의 5시간 세션 창 five-hour와 주간 세션 창 weekly), 각 창의 사용률 또는 잔여율·조회 시각·resets_at을 표시. 제공되지 않은 창을 임의로 만들지 않음 |`
  - `experiments/fixtures/README.md:6-10`:
    > `PC 파트의 Codex 예시 창은 5시간 세션 창(five-hour)과 주간 세션 창(weekly)이며, 각 창의 percent_used/percent_remaining·resets_at을 C3 표시 입력으로 사용한다. 이 파일은 adapter 입력용이며 usage-snapshot.schema.json 직접 검증 대상이 아니다. 스키마 검증은 providers/*.json으로 수행한다. 타 provider는 각자 제공하는 window 목록을 그대로 사용한다.`
- **분석**:
  - 1차 수정 전의 "5시간 세션 창(`five-hour`)과 주간 세션 창(`weekly`)을 모두 표시하고... 창이 하나만 제공되면 있는 창만 표시하고"라는 서술은 특정 provider(Codex)의 창 이름에 종속된 것처럼 읽혀 `1.1절`의 provider-agnostic 원칙("provider 이름을 parser·transport·LCD 공통 상태에 하드코딩하지 않는다")과 긴장이 있었습니다.
  - 수정 후 C3는 "PC가 전달한 사용량 창 목록을 표시"하는 동적 window 모델을 기본으로 규정하고, 5시간/주간 세션 창은 "예:"로 명시함으로써 provider-agnostic 원칙과 완벽히 합치됩니다. 타 provider의 다중 창(`claude-code-windows.json`) 및 단일 창(`codex-percent-window.json`) 처리와도 모순이 없습니다.

### 1.2 통신행 USB 고정
- **판정**: **PASS**
- **근거 파일 및 라인**:
  - `docs/PRODUCT_CONTRACT.md:15`:
    > `| 통신 | E2E baseline은 USB serial(COM3) cdm/1 고정. local Wi-Fi 운용은 별도 cohort에서 비교. 네트워크 장애 시 마지막 정상 데이터 유지 |`
  - `docs/experiments/benchmark-readiness.md:129, 134-137, 144-145`:
    > `USB serial(COM3) cdm/1 transport adapter (E2E baseline 고정)`
    > `local Wi-Fi 운용은 별도 cohort에서 비교하며, E2E baseline의 transport 선택을 대체하지 않는다. baseline(experiments/config/version-2-baseline.yaml)의 transport_choice: usb-serial-cdm-1이 단일 진실이며, 본문의 “또는 local Wi-Fi” 표현은 선택지가 아닌 후속 cohort 항목으로 읽는다.`
    > `E2E baseline transport는 USB serial(COM3) cdm/1로 고정済み다. local Wi-Fi 운용은 별도 cohort에서 비교한다.`
  - `experiments/config/version-2-baseline.yaml:23, 95`:
    > `transport_choice: usb-serial-cdm-1`
    > `transport: usb-serial-cdm-1`
- **분석**:
  - E2E baseline의 통신 방식이 `USB serial(COM3) cdm/1`로 고정되었음이 명확히 선언되었고, local Wi-Fi는 대체 선택지가 아닌 후속 비교 cohort임이 규정되어 모순이 해소되었습니다.

### 1.3 리셋키 매핑 (`last_reset_at` → `latest_reset_at`)
- **판정**: **PASS**
- **근거 파일 및 라인**:
  - `docs/PRODUCT_CONTRACT.md:151-153`:
    > `Legacy fixture key mapping: codex-reset-forecast.json의 last_reset_at과 codex-resets-history.json의 latest_reset_at은 모두 GlobalResetSnapshot의 latest_reset_at으로 정규화한다. fixture 키 자체는 변경하지 않는다.`
  - `experiments/fixtures/codex-reset-forecast.json:5`: `"last_reset_at": "2026-09-08T04:05:53Z"`
  - `experiments/fixtures/codex-resets-history.json:5`: `"latest_reset_at": "2026-09-08T01:56:00Z"`
  - `docs/PRODUCT_CONTRACT.md:139`: `latest_reset_at: RFC3339 timestamp | null`
  - `scripts/evaluate-product.py:65`:
    > `latest_reset_at=body.get("last_reset_at", body.get("latest_reset_at"))`
  - `scripts/host_device_pipeline.py:158`:
    > `"latest_reset_at": value.get("latest_reset_at", value.get("last_reset_at"))`
- **분석**:
  - 기존 합성 fixture 파일들의 키 불일치(`last_reset_at` vs `latest_reset_at`)를 fixture 원본을 변경하지 않고 공통 모델 `GlobalResetSnapshot`의 `latest_reset_at`으로 정규화하도록 명시하였으며, 평가 스크립트와 파이프라인 구현도 이를 양방향 fallback 처리하고 있어 완전한 일관성을 갖추었습니다.

### 1.4 stale 이중시계 분리 문구
- **판정**: **PASS**
- **근거 파일 및 라인**:
  - `docs/PRODUCT_CONTRACT.md:212-214`:
    > `snapshot stale(observed_at→reference_time 300초 이상)과 LCD stale(last_good_at→현재 5분 이상)은 duration은 같으나 기준 시계가 다르다. 기본 비교군은 이 값을 고정한다. 값을 바꾼 실행은 이유와 시험 결과를 기록하고 별도 비교군으로 분류한다.`
  - `docs/PRODUCT_CONTRACT.md:161-163`:
    > `Snapshot freshness is evaluated against the supplied reference_time (or the observation time used by the test), and an age of 300 seconds or more is stale. Available snapshots older than that threshold must be marked stale.`
  - `docs/experiments/host-device-pipeline-contract.md:58-59`:
    > `marks state stale at age 300 seconds relative to the supplied reference time, preserves provider-local error snapshots, and clears stale state on the next accepted frame.`
  - `scripts/evaluate-product.py:40-42`: 0초·299초·300초 기준 stale 판정 회귀 시험 검증.
- **분석**:
  - 호스트 상에서 데이터 무결성을 검증할 때 주입되는 고정 기준 시계(`reference_time`과 `observed_at` 간 차이)와 ESP32 펌웨어 상에서 LCD에 표시되는 런타임 갱신 시계(`last_good_at`과 런타임 현재 시각 간 차이)를 명확히 분리함으로써, 시계 소스 혼동으로 인한 시험 판정 오류를 효과적으로 방지하고 있습니다.

---

## 2. benchmark-readiness 상태값 일관성

**종합 판정: PASS**

### 2.1 transport 확정 서술 vs 게이트표 (R1 `not_ready`)
- **판정**: **PASS**
- **근거 파일 및 라인**:
  - `docs/experiments/benchmark-readiness.md:61`:
    > `| R1 고정 입력 | prompt/config/fixture/schema/평가기준 commit·hash와 transport 선택 고정 | not_ready |`
  - `docs/experiments/benchmark-readiness.md:80-83`:
    > `matrix 본문 (experiments/fixtures/provider-fixture-matrix.json)과 provider adapter 결과 schema·validator·example은 존재하며, 남은 작업은 baseline commit·hash 동결과 검토 기록이다. 동결 전이므로 R1/R3은 계속 not_ready다.`
  - `docs/experiments/benchmark-readiness.md:144`:
    > `E2E baseline transport는 USB serial(COM3) cdm/1로 고정済み다.`
- **분석**:
  - 게이트 R1의 완료 조건은 "commit·hash와 transport 선택 고정"의 복합 조건입니다.
  - transport 선택은 `usb-serial-cdm-1`로 이미 확정되었으나, 작업 트리가 아직 커밋·동결되지 않아 baseline commit SHA 및 입력 파일들의 번들 hash 동결이 남아 있습니다. L80-83에서 "남은 작업은 baseline commit·hash 동결과 검토 기록이다. 동결 전이므로 R1/R3은 계속 not_ready다"라고 이유를 명시하고 있으므로, transport 확정 서술과 게이트표의 R1 `not_ready` 상태는 상호 모순이 아닙니다.

### 2.2 게이트표 vs 2026-09-13 addendum (스냅샷 격하)
- **판정**: **PASS**
- **근거 파일 및 라인**:
  - `docs/experiments/benchmark-readiness.md:58-70` (§필수 gate 표):
    > R0 `in_review`, R1 `not_ready`, R2 `in_review`, R3 `not_ready`, R4 `not_ready`, R5 `not_ready`, R6 `partial`, R7 `not_ready`, R8 `not_ready`, R9 `not_ready`, R10 `not_authorized`
  - `docs/experiments/benchmark-readiness.md:169-177` (Current review addendum):
    > `## Current review addendum (2026-09-13 snapshot)`
    > `The offline readiness review is recorded in readiness-review-20260913.md. The R0-R10 statuses below are that review's snapshot, not the current norm: R0 in_review, R1 in_review, R2 in_review, R3 in_review, R4 not_ready, R5 not_ready, R6 partial, R7 not_ready, R8 partial, R9 not_ready, and R10 not_authorized. The gate table above (§필수 gate) is authoritative for the current status.`
- **분석**:
  - 1차 수정에서 addendum 절 제목을 `(2026-09-13 snapshot)`으로 명시하고, "below are that review's snapshot, not the current norm" 및 "The gate table above (§필수 gate) is authoritative for the current status"를 추가하였습니다.
  - 과거 09-13 오프라인 도구 점검 당시의 임시 기록(R1 `in_review`, R3 `in_review`, R8 `partial`)과 현행 규범 게이트표(R1 `not_ready`, R3 `not_ready`, R8 `not_ready`) 사이의 상충이 "과거 스냅샷 vs 현행 권위 규범"으로 명확히 정리되어 상태값 충돌이 해소되었습니다.

---

## 3. schema 범위 서술과 실제 스키마 파일 일치 여부

**종합 판정: PASS**

### 3.1 문서 서술 확인
- **근거 파일 및 라인**:
  - `docs/experiments/feature-comparison.md:98-102`:
    > `E2E 결과 계약(end-to-end-result.schema.json)은 F1~F9·I1~I4·G1~G6 필드를 보유한다. 확장 대상은 historical hardware-autonomy용 hardware-feature-result.schema.json (C1~C8만 기록)이며, 이를 E2E 기준으로 오독하지 않는다.`
  - `docs/experiments/benchmark-management.md:125`:
    > `- 미완료: historical prep용 result schema의 F1~F9/I1~I4·G1~G6 기록 확장(E2E 결과 계약은 해당 필드 보유). 동결·승인 전이므로 새 baseline 확정 금지`

### 3.2 실제 JSON Schema 파일과의 일치 검증
- **E2E 스키마 (`experiments/schema/end-to-end-result.schema.json`)**:
  - `L16-18`: `feature_results`, `integration_results`, `gui_scores`가 최상위 required 속성으로 선언됨
  - `L97-128`: `gui_scores` 내부에 `G1`~`G6`가 필수 속성으로 선언됨
  - `L348-369`: `$defs/featureResults` 내부에 `F1`~`F9`가 모두 필수 속성으로 선언됨 (`minProperties: 9, maxProperties: 9`)
  - `L370-386`: `$defs/integrationResults` 내부에 `I1`~`I4`가 모두 필수 속성으로 선언됨 (`minProperties: 4, maxProperties: 4`)
  - **검증 결과**: E2E 결과 스키마는 F1~F9, I1~I4, G1~G6 필드를 빠짐없이 보유하고 있음 (문서 서술과 완전 일치)
- **Historical prep용 스키마 (`experiments/schema/hardware-feature-result.schema.json`)**:
  - `L16, L194-233`: `core_requirements` 객체 내에 `C1`~`C8` 속성만 정의되어 있음
  - F1~F9, I1~I4, G1~G6 관련 필드는 정의되어 있지 않음
  - **검증 결과**: Historical prep용 스키마는 C1~C8만 기록하며 해당 필드들을 미보유하고 있음 (문서 서술과 완전 일치)

---

## 4. prompt 범위(F1~F9·I1~I4)와 fixtures의 C3~C5 일치 여부

**종합 판정: PASS**

### 4.1 Prompt 범위와 C3~C5
- **근거 파일 및 라인**:
  - `experiments/prompts/version-2-agent-task.md:38-41`:
    > `이 과제는 version-2-end-to-end-v1이다. F1~F9와 I1~I4를 모두 구현 범위에 포함한다. PC의 synthetic provider fixture → 정규화 → USB serial cdm/1 전송 → 실제 ESP32 receiver/cache/stale → LCD GUI를 연결하라.`
  - `experiments/prompts/version-2-agent-task.md:66-69`:
    > `C3는 PC에서 제공한 fixture가 전송·수신되어 firmware 상태와 LCD까지 반영되는 데이터 경로를 포함한다. firmware에 고정 fixture를 내장하는 것으로 대체하지 말라. 개인 사용량, codex-reset.com, codex-resets.com을 공통 데이터 모델로 정규화하되 출처와 시각을 보존하라.`
  - `experiments/prompts/version-2-agent-task.md:74-80`:
    > `collector와 공통 상태는 Codex 전용 필드에 하드코딩하지 말고 provider adapter registry와 동적 quota window 목록을 수용하도록 설계하라. ... source가 절대 token 잔량을 제공하지 않으면 percent/unknown과 unsupported/unavailable 상태를 보존하고 임의로 token 수를 계산하지 말라. 두 공개 출처의 값을 하나의 공식 리셋 일정으로 합치지 말라.`
  - `experiments/prompts/version-2-agent-task.md:82`:
    > `320 × 820 세로 LCD에서 대시보드, 글로벌 리셋, 상태/오류 화면을 제공하라.`
- **분석**:
  - Prompt는 F1~F9 및 I1~I4의 구현 범위를 명확히 지시하고 있으며, C3(동적 window 목록, 잔여율/사용률, 조회 시각), C4(출처별 최근 리셋 시각 구분), C5(24h/48h 공개 전망 확률 표시, 일정 보장 금지)의 핵심 계약 조건을 정확하게 에이전트 지침으로 전달하고 있습니다.

### 4.2 Fixtures와 C3~C5
- **`experiments/fixtures/personal-usage.json`**:
  - `L6-21`: `windows` 배열에 `id: "five-hour"` (5-hour window, 42% used / 58% remaining) 및 `id: "weekly"` (Weekly window, 18% used / 82% remaining)를 제공하여 C3의 동적 window 목록 및 Codex 예시 창 요구조건과 완벽히 부합함.
- **`experiments/fixtures/codex-reset-forecast.json`**:
  - `L5-8`: `last_reset_at` (C4 출처 최근 리셋 시각), `forecast_24h_percent: 22`, `forecast_48h_percent: 39`, `forecast_is_schedule: false` (C5 24h/48h 전망 확률 및 비일정 보장) 제공.
  - `experiments/fixtures/README.md:11-13`: `confidence`는 주석일 뿐 스키마 필드가 아니며 C5 판정은 24h/48h 퍼센트와 `forecast_is_schedule: false`로 수행함을 명시하여 C5 계약과 일치함.
- **`experiments/fixtures/codex-resets-history.json`**:
  - `L3-5`: `source: "codex-resets.com"`, `latest_reset_at: "2026-09-08T01:56:00Z"`를 제공하여 C4의 출처 구분 및 최근 리셋 시각 표시에 부합함.
- **`experiments/fixtures/provider-fixture-matrix.json`**:
  - 단일 window(`codex-percent-window.json`), 다중 window(`claude-code-windows.json`), unsupported 상태(`gemini-cli-unsupported.json`), stale 및 timeout 상태 등을 포괄하여 C3의 동적 윈도우 수용 및 provider adapter registry 계약을 검증하도록 설계됨.

---

## 5. 새로 발견한 모순 및 불일치 보고

문서 횡단 검토 결과, Critical 수준의 결함은 없으나 1차 수정에서 E2E baseline transport를 USB serial로 확정함에 따라 발생한 **하위 문서 잔재 표현(Major 2건, Minor 3건)**이 식별되었습니다.

| 심각도 | 항목 ID | 대상 파일 및 라인 | 모순/불일치 내용 요약 |
|---|---|---|---|
| **Major** | M-01 | `docs/experiments/feature-comparison.md:41` | F3 transport 항목에 "USB serial(COM3) 또는 로컬 Wi-Fi에서"라는 양자택일형 표현 잔재 |
| **Major** | M-02 | `docs/experiments/integration-contract.md:76-78, 124, 144, 183` | Baseline transport가 이미 고정되었음에도 "아직 transport 선택이 끝나지 않았다"는 미확정 서술 유지 |
| **Minor** | m-01 | `docs/PRODUCT_CONTRACT.md:239`, `docs/experiments/evaluation-contract.md:75` | USB baseline 하에서 C7 실물 시험 기준에 "Wi-Fi 단절"만 기재됨 (USB 케이블 단절 누락) |
| **Minor** | m-02 | `docs/experiments/benchmark-readiness.md:90` | R1 종료 산출물에 "transport ADR"이 명시되어 있으나 ADR 미작성 및 남은 작업 목록 누락 |
| **Minor** | m-03 | `docs/experiments/e2e-contract-readiness-proposal.md:25` | 제안 문서의 R1 상태에 "transport remains unset" 서술 잔재 |

---

### [Major M-01] `feature-comparison.md`의 F3 transport 평가 기준 서술 불일치
- **파일:라인**: `docs/experiments/feature-comparison.md:41`
- **현재 문구**:
  > `| F3 | PC→ESP32 transport | USB serial(COM3) 또는 로컬 Wi‑Fi에서 frame 버전·길이·무결성·재연결·오류 응답을 보장하는가? | protocol 문서, 송수신 raw log, checksum/재연결 시험 | 준비용: not_run; E2E: 필수 |`
- **모순 이유**:
  - `PRODUCT_CONTRACT.md:15`, `version-2-baseline.yaml:23,95`, `benchmark-readiness.md:129,136,144`에서는 E2E baseline의 transport가 `USB serial(COM3) cdm/1`로 단일 확정되었으며, local Wi-Fi는 후속/별도 cohort로 분리되었습니다.
  - 그러나 기능 비교표(F3) 본문에는 "USB serial(COM3) 또는 로컬 Wi-Fi에서"라고 서술되어 있어, 단일 baseline 내에서 에이전트가 둘 중 하나를 임의로 선택할 수 있는 것처럼 오독될 소지가 있습니다.
- **추가 수정 제안 (문구 수준)**:
  - `docs/experiments/feature-comparison.md:41`의 "비교 질문" 열을 다음과 같이 수정:
    > `E2E baseline 고정인 USB serial(COM3) cdm/1(별도 cohort인 로컬 Wi-Fi 포함)에서 frame 버전·길이·무결성·재연결·오류 응답을 보장하는가?`

---

### [Major M-02] `integration-contract.md`의 transport 미확정 상태 서술 잔재
- **파일:라인**: `docs/experiments/integration-contract.md:76-78, 124, 144, 183`
- **현재 문구**:
  - `L76-78`: `아직 transport 선택과 schema 확정이 끝나지 않았으므로, 이 문서만으로 agent 실행·COM3 전송·실제 계정 조회를 시작하지 않는다. 정식 E2E baseline을 만들 때 이 문서의 선택값과 hash를 고정한다.`
  - `L124`: `정식 baseline에서 **한 가지**를 선택한다.`
  - `L144`: `아래는 후보 형식이며, transport_choice와 함께 정식 baseline에서 고정한다.`
  - `L183`: `- [ ] transport 선택과 protocol version 승인`
- **모순 이유**:
  - 상위 계약 문서(`PRODUCT_CONTRACT.md:15`), baseline YAML(`version-2-baseline.yaml:23`), 준비 게이트 문서(`benchmark-readiness.md:144`)에서는 transport가 이미 `USB serial(COM3) cdm/1`로 고정 선언되었습니다.
  - 하지만 통합 계약 초안 문서(`integration-contract.md`)는 초안 작성 시점의 문구가 그대로 유지되어 "아직 transport 선택이 끝나지 않았다", "baseline에서 한 가지를 선택한다", 체크리스트 상의 미완료 항목으로 서술되어 상위 문서와 상태 충돌이 발생합니다.
- **추가 수정 제안 (문구 수준)**:
  - `L76-78`:
    > `E2E baseline transport는 USB serial(COM3) cdm/1로 고정되었으나, 최종 baseline commit·hash 동결과 R10 사용자 승인 전이므로 이 문서만으로 agent 실행·COM3 전송·실제 계정 조회를 시작하지 않는다.`
  - `L124`:
    > `E2E baseline은 USB serial(COM3) cdm/1로 고정한다 (local Wi-Fi는 별도 비교 cohort).`
  - `L144`:
    > `아래는 E2E baseline으로 고정된 cdm/1 형식이며, baseline commit 동결 시 최종 확정된다.`
  - `L183`:
    > `- [x] transport 선택(USB serial cdm/1) 고정 (baseline commit/hash 동결 대기)`

---

### [Minor m-01] C7 장애 처리 및 실물 채점 표의 "Wi-Fi 단절" 잔재 표현
- **파일:라인**:
  - `docs/PRODUCT_CONTRACT.md:239`: `실제 Wi-Fi 단절 시험은 운영자 실물 평가로 구분한다.`
  - `docs/experiments/evaluation-contract.md:75`: `| C7 | 정상→오류→복구, Wi-Fi 단절, watchdog reset 없음 |`
- **모순 이유**:
  - E2E baseline의 transport가 USB serial `cdm/1`로 고정되었으므로, E2E 실물 평가의 C7 핵심 단절 시험은 `USB 케이블 단절 / COM 포트 재열거`가 되어야 합니다.
  - 현재 문구에는 과거 Wi-Fi 우선 계약 시절의 "Wi-Fi 단절"만 기재되어 있어, USB baseline의 실물 시험 기준과 불일치합니다.
- **추가 수정 제안 (문구 수준)**:
  - `docs/PRODUCT_CONTRACT.md:239`:
    > `실제 USB 케이블/통신 단절(Wi-Fi cohort의 경우 Wi-Fi 단절) 시험은 운영자 실물 평가로 구분한다.`
  - `docs/experiments/evaluation-contract.md:75`:
    > `| C7 | 정상→오류→복구, USB 통신 단절(Wi-Fi cohort는 Wi-Fi 단절), watchdog reset 없음 |`

---

### [Minor m-02] `benchmark-readiness.md` R1 산출물의 "transport ADR" 부재
- **파일:라인**: `docs/experiments/benchmark-readiness.md:90`
- **현재 문구**:
  - `L90`: `| R1 | hash가 고정된 prompt/config/fixture bundle과 transport ADR | maintainer | 모든 agent가 동일 입력·transport를 사용 |`
- **모순 이유**:
  - R1의 완료 산출물로 "transport ADR"이 명시되어 있으나, 현재 `docs/decisions/` 디렉토리에는 0001~0004만 존재하고 transport 결정(USB serial cdm/1 baseline 고정 및 local Wi-Fi cohort 분리)에 대한 ADR 문서(예: `0005-transport-usb-serial-baseline.md`)가 아직 생성되지 않았습니다.
  - L80-83의 남은 작업 설명("남은 작업은 baseline commit·hash 동결과 검토 기록이다")에도 ADR 작성이 누락되어 있습니다.
- **추가 수정 제안 (문구 수준)**:
  - `docs/experiments/benchmark-readiness.md:82`:
    > `남은 작업은 baseline commit·hash 동결, transport ADR 작성 및 검토 기록이다. 동결 전이므로 R1/R3은 계속 not_ready다.`
  - 또는 `docs/decisions/0005-transport-usb-serial-baseline.md`를 신규 작성하여 R1 산출물 요건을 충족.

---

### [Minor m-03] `e2e-contract-readiness-proposal.md`의 "transport remains unset" 서술 잔재
- **파일:라인**: `docs/experiments/e2e-contract-readiness-proposal.md:25`
- **현재 문구**:
  > `| R1 inputs | schema, fixture, baseline, and transport inputs | in_review: schemas and fixtures are present; transport remains unset |`
- **모순 이유**:
  - 비록 proposal 문서이나, "transport remains unset"이라는 서술이 현행 baseline(`transport_choice: usb-serial-cdm-1`) 및 PRODUCT_CONTRACT의 고정 선언과 배치됩니다.
- **추가 수정 제안 (문구 수준)**:
  - `docs/experiments/e2e-contract-readiness-proposal.md:25`:
    > `| R1 inputs | schema, fixture, baseline, and transport inputs | in_review: schemas, fixtures, and transport choice (usb-serial-cdm-1) are present; baseline commit/hash freeze pending |`

---

## 6. 결론 요약

1. **1차 수정 확인 결과**: C3 동적 window 목록화, 통신행 USB 고정, 리셋키 정규화 매핑, stale 이중시계 분리 문구는 상호 모순 없이 정합성을 완벽하게 만족합니다 (**PASS**).
2. **benchmark-readiness 검증 결과**: 1차 수정의 스냅샷 격하 조치로 게이트표의 규범적 권위가 확립되었으며, commit/hash 동결 대기 논리가 명시되어 상태값 충돌이 없습니다 (**PASS**).
3. **스키마 범위 검증 결과**: E2E 스키마의 F1~F9·I1~I4·G1~G6 보유 및 historical prep 스키마의 C1~C8 전용 기록 서술은 실제 스키마 파일들과 100% 일치합니다 (**PASS**).
4. **Prompt 및 Fixtures 검증 결과**: Agent task prompt의 요구 범위와 합성 fixtures의 데이터 구조는 C3~C5 계약을 완전히 충족합니다 (**PASS**).
5. **추가 발견 사항**: Critical 결함은 없으나, USB serial baseline 확정에 따라 하위 문서(`feature-comparison.md`, `integration-contract.md`, `evaluation-contract.md`)에 남아있는 잔재 표현 및 미작성 transport ADR 등 5건(Major 2건, Minor 3건)의 문구 수준 정비가 권장됩니다.
