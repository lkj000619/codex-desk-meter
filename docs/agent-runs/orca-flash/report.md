# PC 수집기·전송기 구현 보고서 (orca-flash)

- 작성자: AGY Flash (`gemini-3.8-flash-medium`)
- Task ID: `task_fa0b12bd6fda`
- Dispatch ID: `ctx_e7bb307f023b`
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

## 3. 검증 결과

`tests/pc/test_collector.py` 테스트 스위트 13개 항목 전체 통과:
1. `test_cumulative_token_count_not_double_summed`: 누적 이벤트 중복 합산 방지.
2. `test_partial_line_and_truncation_handling`: 부분 라인 및 잘림 복원력.
3. `test_differing_source_total_and_normalized_total`: 원본 total과 정규화 total 불일치 보존.
4. `test_privacy_boundary`: 경로 및 대화 내용 비노출 검증.
5. `test_directory_scan_and_latest_selection`: 다중 세션 스캔 및 최신 선택 정책.
6. `test_app_server_response_parsing`: 네이티브 rateLimits RPC 응답 파싱 및 duration 매핑.
7. `test_semantic_rule_available_requires_agent_and_host`: available 상태의 identity semantic 강제.
8. `test_canonical_json_and_crc32`: 표준 canonical 인코딩 및 CRC32 일치.
9. `test_frame_size_and_newline_contract`: 64KB 및 LF 규격.
10. `test_sequence_wrap_around_logic`: uint32 래핑 및 모듈로 비교.
11. `test_atomic_sequence_reservation_consumes_on_failure`: 원자적 순번 예약 및 실패 시 소비.
12. `test_state_corruption_fails_closed`: 상태 손상 시 fail-closed.
13. `test_stale_boundaries_0_299_300`: 0초, 299초, 300초 stale 경계 판정.

## 4. 운영자 CLI 재현 절차

### 1) 디바이스 순번 초기화 (수신자 초기화 확인 후 1회)
```powershell
python -m pc.cli init-device --device-alias desk-meter-1 --initial-sequence 0
```

### 2) 세션 인벤토리 확인
```powershell
python -m pc.cli inventory --session-dir C:\path\to\sessions
```

### 3) 실시간 Quota 및 세션 데이터 수집 테스트 (Dry-run)
```powershell
python -m pc.cli collect --live-quota --global-reset experiments/fixtures/codex-resets-history.json
```

### 4) cdm/1 프레임 생성 및 파일 출력 (검증용)
```powershell
python -m pc.cli send --device-alias desk-meter-1 --dry-run --live-quota --global-reset experiments/fixtures/codex-resets-history.json --output frame_output.bin
```

### 5) 30초 주기 Watch 모드 실행
```powershell
python -m pc.cli watch --device-alias desk-meter-1 --interval 30 --dry-run --live-quota
```

실제 COM 포트(예: `COM3`)로의 전송은 코디네이터가 하드웨어 연결 확인 후 수행합니다.
