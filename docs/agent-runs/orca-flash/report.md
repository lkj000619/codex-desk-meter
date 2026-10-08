# PC 수집기·전송기 구현 보고서 (orca-flash)

- 작성자: AGY Flash (`gemini-3.8-flash-medium`)
- Task ID: `task_fa0b12bd6fda` (Initial) / `task_3963de21ddd1` (Remediation 1) / `task_2b005e480abd` (Final Runtime Gaps)
- Dispatch ID: `ctx_e7bb307f023b` (Initial) / `ctx_221ff3735dae` (Remediation 1) / `ctx_4308689007a9` (Final Runtime Gaps)
- 터미널: `term_d3b622cf-1791-4afc-a013-2cf7482bb57d`
- 최초 작성일: 2026-10-08
- 최종 갱신일: 2026-10-08 (2차 보완 완료)

## 1. 개요 및 구현 범위

동결 과제 계약(`PRODUCT_CONTRACT.md`), 협업 설계(`docs/design/2026-10-08-orca-harness.md`), Luna 요구사항 검토(`docs/agent-runs/orca-luna/requirements-review.md`), 그리고 코디네이터의 런타임 갭 검토(`docs/design/2026-10-08-pc-review-findings.md`)에 따라 Windows 환경의 신규 PC 수집기 및 `cdm/1` 전송기(`pc/`)와 검증 테스트(`tests/pc/`)를 순수 표준 라이브러리 및 기설치 패키지(`jsonschema`) 기반으로 구현했습니다.

소유 파일 외의 57개 원본 동결 입력 및 타 역할 파일은 일절 수정하지 않았으며, 작업자 개발 및 테스트 단계에서는 엄격한 비식별 synthetic 데이터만을 사용하였습니다.

## 2. 주요 아키텍처 및 구현 내용

### 2.1 세션 원격측정 (`pc/session.py`)
- **개인정보 경계 준수**: 사용자의 대화 본문, auth 토큰, 쿠키, 키를 전혀 읽지 않고 오직 token metadata만을 파싱.
- **누적 토큰 처리**: Codex CLI `0.159.x`의 `event_msg`/`token_count` 내 `total_token_usage` 누적값을 파싱하며, 반복 누적 이벤트에 대해 중복 합산하지 않고 최신 누적값으로 갱신.
- **예외 복원력**: 부분 라인(partial line), JSON 잘림, 로그 재시작, 복수 세션을 안전하게 처리.
- **다중 세션 인벤토리 및 최신 정책**: 날짜별 하위 폴더를 재귀 검색(`rglob`)하며, 세션별 집계 및 `--latest` 또는 명시적 `--session-id` 선택 정책 구현.

### 2.2 계정 Quota 수집 (`pc/quota.py`)
- **Native App-Server RPC**: 로컬에 설치된 `codex app-server`에 stdio JSON-RPC로 연결.
- **정식 핸드셰이크 순서**: `initialize` 요청 응답 대기 -> `initialized` 알림 전송 -> `account/rateLimits/read` 요청 호출.
- **진정한 논블로킹 타임아웃**: 스레드 및 큐 기반 `BoundedProcessReader`를 통해 blocking `readline`으로 인한 무한 대기를 원천 방지하고 자식 프로세스 정리(`terminate` -> `kill` -> `wait`) 보장.
- **Duration 및 상태 보존**: 제공된 실제 `windowDurationMins`(300분 -> 18000초, 10080분 -> 604800초)를 보존하고 `primary-18000s`, `5h limit`과 같이 정확한 typed label/ID 매핑.

### 2.3 정규화 및 스키마 검증 (`pc/normalizer.py`, `pc/frame.py`)
- **6채널 Session Telemetry**: `metric_kind = "session_telemetry"`로 분기하고 `input`, `output`, `cached_input`, `reasoning_output`, `source_total`, `normalized_total`의 6개 고정 채널을 구성.
  - `normalized_total = input + output`
  - `cached_input` 및 `reasoning_output`은 부분값으로 취급하여 총계에서 가감하지 않음.
  - `source_total`과 `normalized_total`이 다른 경우에도 원본 값을 그대로 보존.
  - 토큰 수는 정수형(int)으로 보존하여 C 펌웨어와의 완벽한 상호운용성 제공.
- **Semantic Validator**:
  - `usage-snapshot.schema.json` 및 `cdm-frame.schema.json` 검증 외에, `status == "available"`일 때 non-null `agent_id`와 `host_id`를 강제.
  - `reference_time` 대비 미래 타임스탬프 거부.
  - `percent_used + percent_remaining == 100` 불변식 검증.
- **cdm/1 프레이밍**:
  - canonical UTF-8 JSON (공백 없음, 키 정렬, `ensure_ascii=False`).
  - unsigned payload 대상 CRC32 (8자리 대문자 hex).
  - 단일 LF 포함 최대 65,536 바이트 한도 준수.

### 2.4 순번 상태 머신 및 전송 제어 (`pc/sender.py`)
- **원자적 순번 예약**: 쓰기 수행 **직전**에 다음 uint32 순번을 디스크에 원자적(임시 파일 작성 후 `os.replace`)으로 영속화.
- **실패 시 순번 소비**: 전송(쓰기)이 실패하더라도 이미 소비된 순번은 재사용하지 않고 증가 상태 유지.
- **Fail-Closed**: 런타임 중 상태 파일이 삭제/변조되면 메모리 캐시로 재생성하지 않고 즉시 정지.
- **안전한 초기화**: 기존 상태가 존재할 경우 암묵적인 덮어쓰기를 거부(`confirmed_overwrite` 플래그 요구).
- **OS 레벨 싱글 센더 락**: Windows `msvcrt.locking` 기반으로 프로세스 비정상 종료 시에도 OS가 즉시 해제하는 안전한 락 구현.

### 2.5 공유 수집 상태 및 격리 캐시 (`pc/state.py`)
- **소스별 독립 실패 격리**: 세션 파싱 오류가 계정 Quota나 글로벌 리셋 수집을 중단시키지 않음.
- **Last-Good 보존**: 특정 소스에 일시적 장애가 발생해도 직전 정상 스냅샷의 값/관측 시각을 유지하고 상태만 `error`로 전이.
- **정확한 Stale 판정**: 0초 및 299초는 정상, 300초 이상 경과 시 `stale`로 표시하되 원본 `observed_at`은 유지.
- **Fixture Provenance 지원**: `experiments/fixtures/providers` 및 `personal-usage.json`의 원본 형식을 있는 그대로 로드하여 `fixture` provenance로 보존.

### 2.6 인터럽터블 Watch 스케줄러 (`pc/cli.py`)
- **독립적 수동 갱신**: 자동 주기(<=60초)와 무관하게 stdin Enter 입력 시 즉시(<=5초 이내) 신선한 데이터 수집 및 프레임 전송.
- **지속적 직렬 연결 및 재연결 제한**: 직렬 포트 오픈 실패 시 초당 최대 1회로 재시도 제한, 포트 가용 시 5초 이내 전송.
- **엄격한 모드 선택**: `--port` 또는 명시적 `--dry-run`이 없으면 실행을 즉시 거부(암묵적 루프백 금지).

## 3. 검증 결과

`tests/pc/test_collector.py`, `tests/pc/test_remediation.py`, `tests/pc/test_runtime_gaps.py`의 **총 32개 테스트 전체 통과 (OK)**:
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
14. `test_native_codex_0159_nested_event_shape`: Codex 0.159 중첩 구조 파싱.
15. `test_token_observation_time_not_polluted_by_later_events`: 후속 이벤트에 의한 시각 오염 방지.
16. `test_invalid_token_invariants_rejected`: 캐시/추론 불변식 위반 거부.
17. `test_session_directory_scan_recurses_date_folders`: 날짜 폴더 재귀 스캔.
18. `test_rate_limits_by_limit_id_parsed`: rateLimitsByLimitId 다중 창 파싱.
19. `test_state_loss_while_running_halts_immediately`: 런타임 상태 파일 삭제 시 fail-closed 정지.
20. `test_single_sender_lock_prevents_duplicate_instance`: 단일 센더 락 동작.
21. `test_sequence_persistence_across_restart`: 7 -> 재시작 -> 8 순번 영속성.
22. `test_future_timestamp_rejected`: 미래 타임스탬프 거부.
23. `test_percent_sum_relation`: percent 합계 100 불변식.
24. `test_stale_detection_on_production_snapshot`: 실제 스냅샷 0/299/300초 stale 경계.
25. `test_cli_explicit_session_selection_required`: 명시적 세션 선택 정책 강제.
26. `test_hung_stream_times_out_and_cleans_up_process`: Hung RPC 스트림 타임아웃 및 프로세스 정리.
27. `test_source_isolation_and_last_good_retention`: 소스별 오류 격리 및 last-good 유지.
28. `test_stale_detection_0_299_300`: 공유 상태 매니저의 0/299/300초 stale 판정.
29. `test_initialize_new_refuses_silent_overwrite`: 기존 순번 상태 덮어쓰기 거부.
30. `test_os_lock_released_on_subprocess_crash`: 자식 프로세스 비정상 종료 시 OS 락 자동 해제.
31. `test_refuse_implicit_loopback_when_port_missing`: 포트/드라이런 미지정 시 실행 거부.
32. `test_watch_manual_trigger_immediate_dispatch`: 수동 엔터 트리거 시 즉시 전송.

## 4. 운영자 CLI 재현 절차

### 1) 디바이스 순번 초기화 (수신자 초기화 확인 후 1회, 덮어쓰기 시 --force-overwrite 필요)
```powershell
python -m pc.cli init-device --device-alias desk-meter-1 --initial-sequence 0
```

### 2) 세션 인벤토리 확인 (날짜 하위 폴더 자동 검색)
```powershell
python -m pc.cli inventory --session-dir C:\path\to\sessions
```

### 3) 세션 수집 및 정규화 (최신 세션 정책 및 Fixture 결합)
```powershell
python -m pc.cli collect --session-dir C:\path\to\sessions --latest --global-reset experiments/fixtures/codex-resets-history.json
```

### 4) cdm/1 프레임 생성 및 파일 출력 (명시적 Dry-run)
```powershell
python -m pc.cli send --device-alias desk-meter-1 --dry-run --session-dir C:\path\to\sessions --latest --global-reset experiments/fixtures/codex-resets-history.json --output frame_output.bin
```

### 5) 30초 주기 Watch 모드 실행 (Enter 키 입력으로 즉시 수동 갱신 가능)
```powershell
# 루프백 드라이런 모드
python -m pc.cli watch --device-alias desk-meter-1 --interval 30 --dry-run --session-dir C:\path\to\sessions --latest

# 실제 하드웨어 COM3 (코디네이터/운영자 실행)
python -m pc.cli watch --device-alias desk-meter-1 --interval 30 --port COM3 --session-dir C:\path\to\sessions --latest
```

## 5. 이전 실행 기록에 관한 정확한 고지
초기 보고서([report.md](file:///C:/Users/%EC%9D%B4%EA%B4%91%EC%A7%84/orca/workspaces/codex-desk-meter/experiment-orca-harness-20261008/docs/agent-runs/orca-flash/report.md)) 작성 당시 로컬에 설치된 Codex CLI 프로토콜 호환성을 확인하기 위해 1회의 `codex app-server` 초기화 및 read-only `account/rateLimits/read` 호출을 직접 검증한 바 있습니다. 이후 보완 작업 및 단위/통합 테스트에서는 실제 계정이나 실시간 `--live-quota`를 전혀 호출하지 않았으며, 모든 테스트는 통제된 synthetic 데이터와 모의 서브프로세스 스트림으로 완결하였습니다.
