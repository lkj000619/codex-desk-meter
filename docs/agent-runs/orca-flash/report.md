# PC 수집기·전송기 구현 보고서 (orca-flash)

- 작성자: AGY Flash (`gemini-3.8-flash-medium`)
- Task ID: `task_fa0b12bd6fda` (Initial) / `task_3963de21ddd1` (Remediation)
- Dispatch ID: `ctx_e7bb307f023b` (Initial) / `ctx_221ff3735dae` (Remediation)
- 터미널: `term_d3b622cf-1791-4afc-a013-2cf7482bb57d`
- 날짜: 2026-10-08

## 1. 개요 및 구현 범위

동결 과제 계약(`PRODUCT_CONTRACT.md`), 협업 설계(`docs/design/2026-10-08-orca-harness.md`), Luna 요구사항 검토(`docs/agent-runs/orca-luna/requirements-review.md`)에 따라 Windows 환경의 신규 PC 수집기 및 `cdm/1` 전송기(`pc/`)와 검증 테스트(`tests/pc/`)를 순수 표준 라이브러리 및 기설치 패키지(`jsonschema`) 기반으로 구현했습니다.

소유 파일 외의 57개 원본 동결 입력 및 타 역할 파일은 일절 수정하지 않았으며, 작업자 개발 및 테스트 단계에서는 엄격한 비식별 synthetic 데이터만을 사용하였습니다.

## 2. 주요 아키텍처 및 구현 내용

### 2.1 세션 원격측정 (`pc/session.py`)
- **개인정보 경계 준수**: 사용자의 대화 본문, auth 토큰, 쿠키, 키를 전혀 읽지 않고 오직 token metadata만을 파싱.
- **누적 토큰 처리**: Codex CLI `0.159.x`의 `event_msg`/`token_count` 내 `total_token_usage` 누적값을 파싱하며, 반복 누적 이벤트에 대해 중복 합산하지 않고 최신 누적값으로 갱신.
- **예외 복원력**: 부분 라인(partial line), JSON 잘림, 로그 재시작, 복수 세션을 안전하게 처리.
- **다중 세션 인벤토리 및 최신 정책**: 세션 디렉터리 스캔, 세션별 집계, 그리고 가장 최근 `observed_at` 타임스탬프를 가진 세션을 자동 선택하는 정책(`select_latest_session`) 구현.

### 2.2 계정 Quota 수집 (`pc/quota.py`)
- **Native App-Server RPC**: 로컬에 설치된 `codex app-server`에 stdio JSON-RPC로 연결하여 `initialize` 후 읽기 전용 `account/rateLimits/read`만 호출.
- **무간섭 원칙**: 신규 스레드 생성, 턴 실행, 리셋 크레딧 소비를 일절 하지 않음.
- **Duration 및 상태 보존**: 5시간/주간 등의 임의 추정 대신 응답에서 제공된 실제 `windowDurationMins`(300분 -> 18000초, 10080분 -> 604800초)를 보존하고 `primary-18000s`, `5h limit`과 같이 정확한 typed label/ID 매핑.

### 2.3 정규화 및 스키마 검증 (`pc/normalizer.py`, `pc/frame.py`)
- **6채널 Session Telemetry**: `metric_kind = "session_telemetry"`로 분기하고 `input`, `output`, `cached_input`, `reasoning_output`, `source_total`, `normalized_total`의 6개 고정 채널을 구성.
  - `normalized_total = input + output`
  - `cached_input` 및 `reasoning_output`은 부분값으로 취급하여 총계에서 가감하지 않음.
  - `source_total`과 `normalized_total`이 다른 경우에도 원본 값을 그대로 보존.
  - 세션 채널의 quota 필드(`limit_units`, `remaining_units`, `percent_used`, `percent_remaining`, `resets_at`)는 전부 `null`로 유지.
- **Semantic Validator**:
  - `usage-snapshot.schema.json` 및 `cdm-frame.schema.json` 검증 외에, `status == "available"`일 때 non-null `agent_id`와 `host_id`를 강제.
- **cdm/1 프레이밍**:
  - canonical UTF-8 JSON (공백 없음, 키 정렬, `ensure_ascii=False`).
  - unsigned payload 대상 CRC32 (8자리 대문자 hex).
  - 단일 LF 포함 최대 65,536 바이트 한도 준수.

### 2.4 순번 상태 머신 및 전송 제어 (`pc/sender.py`)
- **원자적 순번 예약**: 쓰기 수행 **직전**에 다음 uint32 순번을 디스크에 원자적(임시 파일 작성 후 `os.replace`)으로 영속화.
- **실패 시 순번 소비**: 전송(쓰기)이 실패하더라도 이미 소비된 순번은 재사용하지 않고 증가 상태 유지.
- **Fail-Closed**: 상태 파일 손상(corrupt) 또는 유실 시 전송을 즉시 중단.
- **안전한 초기화**: 암묵적인 보드 리셋 대신, 명시적인 수신자 빈 상태 확인 후 `init-device` 명령을 통해서만 초기화.
- **COM 포트 경계**: 작업자 도구 내에서는 loopback/dry-run 싱크만 사용하고, 실제 COM 포트 제어는 코디네이터/운영자 절차로 분리.

### 2.5 CLI 인터페이스 (`pc/cli.py`)
- `inventory`: 세션 파일 목록 및 토큰 메타데이터 확인.
- `collect`: `--session-file`, `--session-dir`, `--session-id`, `--live-quota`, `--global-reset` 옵션을 조합하여 정규화된 페이로드 추출.
- `init-device`: 대상 디바이스 alias 및 초기 순번 영속화.
- `send`: 원샷 전송 (dry-run 및 output 파일 저장 지원).
- `watch`: 주기적 자동 갱신(<= 60초) 및 원샷 실행 지원.

## 3. 검증 결과 (Initial)

`tests/pc/test_collector.py` 테스트 스위트 13개 항목 전체 통과.

---

## 4. 2026-10-08 코디네이터 코드 리뷰 및 프로브 보완 (Remediation)

코디네이터의 정밀 검토 및 `experiments/orca-harness-20261008/operator/pc-initial-probe.json`의 지적 사항에 따라 다음 6개 핵심 영역을 전면 보완하였습니다:

### 4.1 실제 Codex 0.159 중첩 구조 파싱 및 observed_at 오염 방지 (`pc/session.py`)
- 실제 Codex 0.159의 중첩 로그 구조인 `event_msg -> payload.type == "token_count" -> payload.info.total_token_usage` 및 세션 메타 `session_meta -> payload.id`를 완벽 지원.
- **토큰 관측 시각 오염 방지**: `observed_at` 타임스탬프는 유효한 토큰 이벤트가 수락되었을 때만 갱신하며, 이후의 무관한 턴/이벤트 시각으로 덮어쓰지 않음. 이벤트 부재 시 0이나 현재 시각으로 임의 대체하지 않고 `None` 유지.
- **엄격한 불변식 검증**: `cached_input <= input`, `reasoning_output <= output`, 음수 토큰 거부.
- **세션 선택 정책 엄격화**: 날짜 폴더(`YYYY-MM-DD`) 재귀 스캔 지원, 세션 디렉터리 지정 시 명시적 `--session-id` 또는 `--latest` 플래그를 요구하여 묵시적 임의 선택 방지.

### 4.2 Native Quota JSON-RPC 프로토콜 및 다중 창 지원 (`pc/quota.py`)
- **JSON-RPC 정식 핸드셰이크**: `initialize` 요청 응답 수신 대기 -> `initialized` notification 전송 -> `account/rateLimits/read` 요청의 엄격한 프로토콜 순서 준수.
- **다중 창 누락 방지**: `rateLimits`뿐만 아니라 `rateLimitsByLimitId`를 함께 파싱하여 반환된 별개의 창들을 누락 없이 typed window로 매핑.
- **프로세스 안전성**: stdout 읽기 타임아웃 제한 및 모든 실패/예외 경로에서 자식 프로세스 terminate/kill/wait 정리 보장.
- **합성 개발 원칙**: 작업자 테스트 단계에서는 실계정 및 실시간 `--live-quota`를 절대 호출하지 않고 synthetic/mock 스트림만 사용.

### 4.3 런타임 상태 유실 Fail-Closed 및 단일 센더 락 (`pc/sender.py`)
- **런타임 상태 유실 감지**: 센더 객체 생성 이후 디스크의 상태 파일이 삭제되거나 변조될 경우, 메모리 캐시로 재생성하지 않고 즉시 전송을 중단(`STATE_LOST`, fail-closed).
- **단일 센더 락(`DeviceLock`)**: 동일 디바이스 alias에 대한 복수 센더 동시 실행 방지.
- **순번 영속성**: 7 -> 프로세스 재시작 -> 8 순번 계승 및 실패 시 순번 소비 보장.
- **실제 전송 드라이버 존재**: Windows 115200/8N1 통신을 위한 `WindowsSerialSink` 구현 및 호스트 쓰기 완료를 "HOST WRITE"로 명시(장치 ACK 혼동 방지).

### 4.4 시맨틱 검증기 및 숫자 규격 고도화 (`pc/frame.py`, `pc/normalizer.py`)
- 정수형 토큰을 불필요한 float로 변환하지 않고 int 그대로 보존하여 C 펌웨어와의 호환성 확보.
- 기준 시각(`reference_time`) 대비 미래 타임스탬프 거부.
- percent quota의 합계 불변식(`percent_used + percent_remaining == 100`) 검증.
- 세션 6채널(`input`, `output`, `cached_input`, `reasoning_output`, `source_total`, `normalized_total`)의 고유성 및 불변식 검증.

### 4.5 보완 검증 결과
`tests/pc/test_collector.py` 및 신규 `tests/pc/test_remediation.py`를 포함한 **총 25개 테스트 전체 통과 (OK)**:
- `test_native_codex_0159_nested_event_shape`: Codex 0.159 중첩 구조 파싱 확인.
- `test_token_observation_time_not_polluted_by_later_events`: 후속 이벤트에 의한 시각 오염 방지 확인.
- `test_invalid_token_invariants_rejected`: 캐시/추론 불변식 위반 거부 확인.
- `test_session_directory_scan_recurses_date_folders`: 날짜 폴더 재귀 스캔 확인.
- `test_rate_limits_by_limit_id_parsed`: rateLimitsByLimitId 다중 창 파싱 확인.
- `test_state_loss_while_running_halts_immediately`: 런타임 상태 파일 삭제 시 fail-closed 정지 확인.
- `test_single_sender_lock_prevents_duplicate_instance`: 단일 센더 락 동작 확인.
- `test_sequence_persistence_across_restart`: 7 -> 재시작 -> 8 순번 영속성 확인.
- `test_future_timestamp_rejected`: 미래 타임스탬프 거부 확인.
- `test_percent_sum_relation`: percent 합계 100 불변식 확인.
- `test_stale_detection_on_production_snapshot`: 실제 스냅샷 0/299/300초 stale 경계 확인.
- `test_cli_explicit_session_selection_required`: 명시적 세션 선택 정책 강제 확인.

---

## 5. 운영자 CLI 재현 절차

### 1) 디바이스 순번 초기화 (수신자 초기화 확인 후 1회)
```powershell
python -m pc.cli init-device --device-alias desk-meter-1 --initial-sequence 0
```

### 2) 세션 인벤토리 확인 (날짜 하위 폴더 자동 검색)
```powershell
python -m pc.cli inventory --session-dir C:\path\to\sessions
```

### 3) 세션 수집 및 정규화 (최신 세션 정책 적용)
```powershell
python -m pc.cli collect --session-dir C:\path\to\sessions --latest --global-reset experiments/fixtures/codex-resets-history.json
```

### 4) cdm/1 프레임 생성 및 파일 출력 (Dry-run)
```powershell
python -m pc.cli send --device-alias desk-meter-1 --dry-run --session-dir C:\path\to\sessions --latest --global-reset experiments/fixtures/codex-resets-history.json --output frame_output.bin
```

### 5) 30초 주기 Watch 모드 실행 (Loopback 또는 실제 COM3)
```powershell
# 루프백 모드
python -m pc.cli watch --device-alias desk-meter-1 --interval 30 --dry-run --session-dir C:\path\to\sessions --latest

# 실제 하드웨어 COM3 (코디네이터/운영자 실행)
python -m pc.cli watch --device-alias desk-meter-1 --interval 30 --port COM3 --session-dir C:\path\to\sessions --latest
```
