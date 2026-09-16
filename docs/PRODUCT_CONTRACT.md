# Version 2 제품 계약과 합격 기준

이 문서는 AI 에이전트가 동일한 제품을 구현하도록 Version 2의 핵심 요구사항,
데이터 계약, 화면 상태와 시험 방법을 고정한다. 에이전트가 선택하는 하드웨어
기반 추가 기능은 이 문서의 핵심 요구사항과 별도로 평가한다.

## 1. 대상

| 항목 | 고정값 |
|---|---|
| 보드 | Waveshare ESP32-S3-LCD-3.16 |
| 프레임워크 | ESP-IDF v5.3.2 |
| 디스플레이 | ST7701, 320 × 820, 세로 방향 기준 |
| 입력 | 보드 BOOT 버튼, RST 버튼은 시스템 리셋 전용 |
| 통신 | E2E baseline은 USB serial(COM3) `cdm/1` 고정. local Wi-Fi 운용은 별도 cohort에서 비교. 네트워크 장애 시 마지막 정상 데이터 유지 |
| 펌웨어 시작 상태 | 이 저장소의 기준 커밋에서 에이전트가 ESP-IDF 프로젝트 생성 |

Version 1의 ST7735S, ESP32-S3 Super Mini, 스위치와 저항은 이 계약의 합격
대상이 아니다. Version 2 핵심 기능이 검증된 뒤 공통 데이터 모델을 재사용하여
별도 이식 시험을 한다.

### 1.1 제품 계층과 단계별 범위

제품의 collector와 표시 모델은 provider-agnostic이어야 한다. `codex`,
`claude-code`, `gemini-cli`, `orca` 및 향후 agent runtime은 각각 독립 adapter로
연결하며, provider 이름을 parser·transport·LCD 공통 상태에 하드코딩하지 않는다.
Orca처럼 여러 agent/model을 실행하는 host는 `host`, `provider`, `agent`, `model`,
`account/profile`을 서로 다른 식별자로 보존한다. 같은 provider라도 서로 다른
IDE/CLI 세션을 임의로 합산하지 않는다.

공통 quota window는 최소한 `provider_id`, `source_kind`, `window_id`, `label`,
`percent_used`, `percent_remaining`, `resets_at`, `observed_at`, `stale`, `status`를
지원한다. `used_units`, `remaining_units`, `limit_units`, `unit=token`은 원본 source가
절대값을 제공할 때만 채운다. 구독 rate-limit percent, API token 소비량, agent 실행
telemetry는 서로 다른 metric이므로 같은 “남은 토큰” 숫자로 합치지 않는다.

실시간 개인 사용량을 표시하려면 다음 계층이 모두 연결되어야 한다.

```text
PC provider collectors → 정규화·출처 분리 → versioned transport
        → ESP32 receiver/validation/cache/stale → LCD GUI
```

과거 `version-2-hardware-autonomy-v1`은 계정 자격증명 없는 fixture, firmware,
LCD, 입력과 온보드 자율 기능만 확인한 준비용 cohort이며 제품 합격이나 정식
agent 순위에 사용하지 않는다. 향후 정식 제품 비교의 목표는
`version-2-end-to-end-v1`로, 표준 fixture collector와 로컬 transport를 포함해
F1~F9 전체를 다룬다. 실제 계정 source로의 전환은 소유자 승인 후
`version-2-live-integration-v1`에서 별도 계약·시험으로 수행한다.
PC 수집기·전송 frame·수신 계층의 상세 초안은
[PC 수집기·ESP32 통합 계약](experiments/integration-contract.md)을 따른다.

### 1.2 제품 통합 합격 조건

펌웨어 C1~C8만 통과한 결과는 제품 전체 합격이 아니다. end-to-end 제품 합격에는
다음 integration 조건도 필요하다.

| ID | 계층 | 합격 조건 |
|---|---|---|
| I1 | PC collector | 허용된 fixture/live source를 읽고 조회 시각·단위·source·오류를 보존하며 자격증명을 노출하지 않음 |
| I2 | 정규화 adapter | UsageSnapshot/GlobalResetSnapshot으로 변환하고 두 글로벌 source를 병합하지 않음 |
| I3 | transport | versioned frame, 길이·무결성, 재연결·오류 응답을 검증하고 raw 송수신 log를 남김 |
| I4 | ESP32 receiver/state | frame을 검증해 last-good cache·stale·복구·LCD 상태로 반영함 |

`version-2-end-to-end-v1`에서는 I1~I4와 C1~C8, F9를 모두 평가 대상으로 고정한다.
준비용 firmware-only 결과에서 I1/I3을 `not_run`으로 남기는 것은 정직한 범위
표시이며, 합격으로 간주하지 않는다.

`version-2-hardware-autonomy-v1`에서 C3는 **고정 fixture를 firmware 상태와 LCD에
정확히 표현하는 준비용 display 계약**만 뜻한다. 이 C3 결과는 PC collector 또는
transport 검증을 포함하지 않으며 I1/I3/F1/F3을 대체하지 않는다. historical
cohort는 C1~C8 준비 상태를 모두 기록할 수 있지만 구조적으로 `product_pass` 대상이
아니다. 제품 합격은 새 E2E cohort에서만 판정한다.

## 2. 핵심 요구사항

에이전트는 다음 항목을 모두 구현하거나, 구현할 수 없는 이유와 대체 검증을
결과에 남겨야 한다.

| ID | 요구사항 | 합격 조건 |
|---|---|---|
| C1 | ESP-IDF 프로젝트 | `idf.py set-target esp32s3`와 `idf.py build` 성공 |
| C2 | LCD 출력 | 부팅 후 화면이 켜지고 320 × 820 세로 UI가 잘리지 않음 |
| C3 | 개인 사용량 | PC가 전달한 사용량 창(window) 목록을 표시. source가 제공하는 window를 모두 표시하고(예: Codex의 5시간 세션 창 `five-hour`와 주간 세션 창 `weekly`), 각 창의 사용률 또는 잔여율·조회 시각·`resets_at`을 표시. 제공되지 않은 창을 임의로 만들지 않음 |
| C4 | 최근 글로벌 리셋 | 출처별 최근 리셋 시각을 표시하고 출처를 구분 |
| C5 | 다음 리셋 전망 | 24시간·48시간 공개 전망 확률을 퍼센트로 표시하며 일정 보장으로 표현하지 않음 |
| C6 | 데이터 출처 | `codex-reset.com`과 `codex-resets.com`의 값을 하나의 사실로 합치지 않음 |
| C7 | 장애 처리 | DNS/TLS/HTTP/JSON 오류, 빈 응답과 오래된 데이터가 장치 중단으로 이어지지 않음 |
| C8 | 입력과 갱신 | BOOT 입력으로 화면 또는 진단 상태를 전환하고, 자동 갱신 주기·수동 갱신 동작을 문서화 |

C3의 실험 합격은 개인 계정에 접근하지 않고 표준 fixture collector로 수행한다.
이는 PC collector와 transport seam을 검증할 수 있게 하는 비밀정보 없는 입력이며,
실제 계정 연동은 에이전트에게 자격증명을 제공하지 않는 별도의 소유자 통합
시험이다.

fixture를 firmware에 직접 내장해 그린 것만으로는 PC collector에서 ESP32로
전송했다는 증거가 되지 않는다. E2E cohort에서는 collector→transport→receiver
각 seam을 실행 log와 함께 검증하고, 준비용 cohort에서는 해당 계층을
`not_run; out of cohort`로 기록한다. 데이터 경로의 계층별 상태와 증거는
[기능·LCD GUI 비교 기준](experiments/feature-comparison.md)에 따라 별도로 기록한다.

## 3. 공통 데이터 모델

제품 로직과 보드별 UI를 분리하고, 아래의 논리 필드를 공통으로 유지한다.

```text
UsageSnapshot {
  schema_version: 1
  snapshot_id: string
  provider_id: string
  agent_id: string | null
  host_id: string | null
  model_id: string | null
  account_profile_id: string | null
  source_kind: "fixture" | "local_runtime" | "provider_api" | "ide_telemetry" | "unknown"
  metric_kind: "quota_window" | "token_balance" | "credits" | "session_telemetry"
  status: "available" | "unavailable" | "unsupported" | "unauthorized" | "error" | "stale"
  observed_at: RFC3339 timestamp | null
  windows: [
    {
      window_id: string
      label: string
      used_units: number | null
      remaining_units: number | null
      limit_units: number | null
      unit: "token" | "percent" | "credit" | "unknown"
      percent_used: 0..100 | null
      percent_remaining: 0..100 | null
      resets_at: RFC3339 timestamp | null
      reset_status: "unknown" | "scheduled" | "expired" | omitted
    }
  ]
  stale: boolean
  error_code: string | null
}

GlobalResetSnapshot {
  provider: "codex-reset.com" | "codex-resets.com"
  latest_reset_at: RFC3339 timestamp | null
  fetched_at: RFC3339 timestamp | null
  forecast_24h_percent: 0..100 | null
  forecast_48h_percent: 0..100 | null
  forecast_is_schedule: false
  stale: boolean
  error_code: string | null
}
```

Contract clarifications for the synthetic E2E validator:

- Legacy fixture key mapping: `codex-reset-forecast.json`의 `last_reset_at`과
  `codex-resets-history.json`의 `latest_reset_at`은 모두 `GlobalResetSnapshot`의
  `latest_reset_at`으로 정규화한다. fixture 키 자체는 변경하지 않는다.

- A source-provided absolute window must satisfy `used_units + remaining_units =
  limit_units` within an absolute tolerance of `0.01`; percentages are checked
  separately and are never used to invent absolute token totals.
- `resets_at` is allowed to be in the future when it is a scheduled reset. A
  reset in the past is classified as `expired` and must be displayed as an
  expired/refetch state; it is not silently treated as a current quota window.
- Snapshot freshness is evaluated against the supplied `reference_time` (or
  the observation time used by the test), and an age of 300 seconds or more is
  stale. Available snapshots older than that threshold must be marked stale.
- `agent_id` and `host_id` may be null for unsupported, unauthorized, or error
  sources that cannot expose execution context. Available snapshots require
  both identities.
- Agent token telemetry defines `total = input + output`. `cached` and
  `reasoning` are annotations and are excluded from `total`, so they cannot be
  double-counted. This definition is represented by the schema value
  `input_plus_output_excludes_cached_and_reasoning`.

`GlobalResetSnapshot`은 현재 Codex 관련 공개 서비스에만 적용되는 보조 데이터다.
Claude Code, Gemini 또는 Orca/IDE의 quota reset으로 재사용하거나 provider 사이에서
병합하지 않는다. 다른 provider에 동등한 공개 데이터가 생기면 별도 source adapter와
계약을 추가한다.

`provider_id`는 quota를 발행한 공급자를, `host_id`는 agent가 실행되는 표면을 뜻한다.
예를 들어 Orca에서 Claude Code를 실행한 경우 `provider_id=anthropic`,
`agent_id=claude-code`, `host_id=orca`로 기록한다. Orca를 Anthropic·OpenAI·Google과
같은 quota provider로 취급하지 않는다.

실제 API의 원본 JSON 전체를 UI에 직접 연결하지 않는다. 파서가 위 필드로
정규화한다. 필수 필드 누락·범위 밖 값·유효하지 않은 RFC3339 시각은 오류로 처리한다.
nullable 필드의 null은 미확인으로 표시하며 0이나 현재 시각으로 대체하지 않는다.
PC source가 절대 token quota를 제공하지 않으면 `unit: "percent"` 또는
`"unknown"`과 백분율만 전달하고, 임의의 총량을 곱해 token 수를 만들어내지 않는다.
반대로 절대 사용량을 제공하는 source라면 `used_units`, `remaining_units`,
`limit_units`의 단위·source·조회 시각을 함께 보존한다. 이 필드는 PC collector와
transport가 실제로 구현된 정식 E2E 결과에서 검증한다.
`observed_at`과 `last_good_at`이 기준 시각보다 미래이면 오류로 처리한다.
개인 창의 미래 `resets_at`은 예약된 리셋으로 허용하고, 과거 `resets_at`은
만료/재조회 상태로 표시한다. 확률을 확정 리셋 시각으로 변환하지 않는다.

## 4. 화면과 상호작용

최소 화면은 다음 세 상태를 제공한다.

1. **대시보드:** 개인 사용량 창과 잔여율을 가장 크게 표시하고 최근 조회 시각을
   함께 표시한다.
2. **글로벌 리셋:** 두 공개 출처의 최근 리셋 시각을 구분하고, 전망을 제공하는 출처의
   `24h`, `48h` 퍼센트만 표시한다. 전망이 없는 출처는 미제공으로 표시한다.
   “예측” 또는 “확률”임을 표시한다.
3. **상태/오류:** 네트워크 단절, 오래된 값, 파싱 오류, 마지막 정상 갱신 시각과
   재시도 상태를 표시한다. 정상 데이터가 없을 때도 화면은 켜져 있어야 한다.

BOOT는 짧은 입력으로 위 화면을 순환시키거나 에이전트가 제안한 동등한 화면
전환을 제공해야 한다. debounce 기준과 입력 시간은 결과 문서에 기록한다.
정상 부팅 후 BOOT 입력을 검증한다. BOOT를 누른 채 reset하는 ROM 다운로드
모드 진입은 애플리케이션 제어 대상이 아니다. RST는 제품 기능 입력으로 사용하지 않는다.

기본 자동 갱신 주기는 60초 이하로 하고, 마지막 정상 데이터가 5분 이상
오래되면 `stale` 상태를 표시한다. snapshot stale(`observed_at`→`reference_time`
300초 이상)과 LCD stale(`last_good_at`→현재 5분 이상)은 duration은 같으나 기준
시계가 다르다. 기본 비교군은 이 값을 고정한다. 값을 바꾼
실행은 이유와 시험 결과를 기록하고 별도 비교군으로 분류한다.

LCD GUI의 설계 품질은 C2의 전원·출력 gate와 별도로 G1~G6 rubric으로 기록한다.
레이아웃, 가독성, 출처/상태 구분, 오류·stale·null 표현, 상호작용 피드백과
320×820 보드 최적화를 사진·영상과 구현 근거로 평가한다. GUI 점수는 C2
`not_run`/`fail`을 상쇄하지 않는다.

## 5. 데이터 출처 정책

- `codex-reset.com`은 공개 신호와 이력을 바탕으로 한 독립 전망 서비스다.
- `codex-resets.com`은 별도의 리셋 이력 서비스다.
- 두 서비스의 시각·분류·예측을 합쳐 하나의 공식 일정으로 만들지 않는다.
- 공개 서비스는 개인 OpenAI 계정의 실제 quota를 볼 수 없으므로, 개인 사용량은
  소유자 제공 데이터 또는 실험 fixture만 사용한다.
- API 응답은 조회 시각, HTTP 상태, 파서 버전과 함께 로그에 남기되 계정 쿠키와
  Authorization 헤더는 기록하지 않는다.

## 6. 자동·실물 합격 시험

### 자동 시험

공통 평가에는 고정 기준 시각을 주입한다. 각 fixture의 조회 시각 기준 0초·299초·
300초 후를 시험해 300초 이상에서 stale임을 확인한다. PC 현재 시각으로 기대값을
바꾸지 않는다. offline-fixture에서는 교체 가능한 전송 계층으로 DNS/TLS 실패,
HTTP 오류, 빈/잘못된 JSON을 주입한다. 실제 Wi-Fi 단절 시험은 운영자 실물 평가로 구분한다.
공통 테스트는 실제 제품 파서·상태 전이를 호출해야 하며 별도 모방 파서로 대체하지 않는다.
오류 후 마지막 정상 값 유지와 정상 응답 후 오류 해제·갱신 복구를 모두 검사한다.
공통 평가 도구는 `scripts/evaluate-product.py`이며
[평가 인터페이스](experiments/evaluation-contract.md)를 따른다. 실제 제품 모듈 연결과
실물 검증은 운영자가 증거로 확인하며, 아래 항목은 전체 합격 기준이다.

- 핵심 파서 단위 시험: 정상, 누락, 범위 오류, 잘못된 시간, 빈 응답, HTTP 오류
- fixture 회귀 시험: 개인 사용량, `codex-reset.com` forecast, 두 서비스의 최근 리셋
- ESP-IDF 빌드 시험: 대상 `esp32s3`, 경고와 오류 로그 보존
- 결과 문서 시험: manifest와 structured result validator 통과

기능 비교에서는 PC collector(F1), 정규화·출처(F2), transport(F3), receiver/state(F4),
LCD GUI(F5), 입력·갱신(F6), 글로벌 리셋(F7), 빌드·관측(F8), 자율 기능(F9)을
각각 `pass / partial / fail / not_run / blocked / timeout` 중 하나로 기록한다.
현재 결과 schema v2에 이 기능·GUI 필드를 추가하기 전에는 새 정식 baseline을
고정하지 않는다.

### 실물 시험

- 보드 부팅 후 LCD가 30초 이상 켜진 상태 유지
- 모든 화면에서 글자·막대·퍼센트가 화면 밖으로 잘리지 않음
- BOOT 입력으로 화면 전환, RST 후 자동 재부팅
- 정상·오류·오래된 fixture가 각각 식별 가능한 상태로 표시
- Wi-Fi를 끊어도 마지막 값과 오류 상태가 유지되고 watchdog reset이 없음

실물 시험은 사진·영상 또는 시리얼 로그의 파일명, 시각, 판정자를 결과에
기록한다. USB 포트는 한 실행에서 한 에이전트만 점유한다.

## 7. 범위와 안전

개인 계정 우회 수집, 사용량 제한 우회, 예측 일정 보장, 전체 플래시 삭제,
보드 외부 하드웨어 추가는 핵심 구현과 기본 에이전트 실험에서 허용하지 않는다.
실험 운영자가 기준 이미지 복원에 필요하다고 판단한 경우에만 별도 운영 절차로
플래시를 복원하고, 원본 백업과 SHA-256을 먼저 확인한다.
