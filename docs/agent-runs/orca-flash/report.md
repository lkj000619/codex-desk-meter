# PC 수집기·전송기 구현 보고서 (orca-flash)

- 작성자: AGY Flash (`gemini-3.8-flash-medium`)
- Task ID: `task_fa0b12bd6fda` (Initial) / `task_3963de21ddd1` (Remediation 1) / `task_c6f6d8f00810` (Final PC Runtime Gaps)
- Dispatch ID: `ctx_e7bb307f023b` (Initial) / `ctx_221ff3735dae` (Remediation 1) / `ctx_b3dca8602ce8` (Final PC Runtime Gaps)
- 터미널: `term_39c072ad-cf9b-4974-84a0-baa02d99974f`
- 코디네이터 터미널: `term_ce8a35be-a6e6-4508-aba9-5c5400b95a21`
- 최종 갱신일: 2026-10-09

## 1. 개요 및 구현 범위

동결 과제 계약(`PRODUCT_CONTRACT.md`), 협업 설계(`docs/design/2026-10-08-orca-harness.md`), Luna 요구사항 검토(`docs/agent-runs/orca-luna/requirements-review.md`), 그리고 코디네이터 지시 및 런타임 갭 검토(`docs/design/2026-10-08-pc-review-findings.md`)에 따라 Windows 환경의 신규 PC 수집기 및 `cdm/1` 전송기(`pc/`)와 검증 테스트(`tests/pc/`)를 순수 표준 라이브러리 및 기설치 패키지(`jsonschema`) 기반으로 보완 구현했습니다.

소유 파일 외의 57개 원본 동결 입력 및 타 역할 파일은 일절 수정하지 않았으며, 작업자 개발 및 테스트 단계에서는 엄격한 비식별 synthetic 데이터만을 사용하였습니다.

## 2. 주요 아키텍처 및 런타임 갭 보완 내용

### 2.1 세션 원격측정 및 선택적 카운트 보존 (`pc/session.py`)
- **개인정보 경계 준수**: 사용자의 대화 본문, auth 토큰, 쿠키, 키를 전혀 읽지 않고 오직 token metadata만을 파싱.
- **누적 토큰 처리**: Codex CLI `0.159.x`의 `event_msg`/`token_count` 내 `total_token_usage` 누적값을 파싱하며 최신 누적값으로 갱신.
- **선택적 토큰 카운트 null 보존**: 원본 이벤트에 `cached_input_tokens`, `reasoning_output_tokens`, `total_tokens`가 생략된 경우, 이를 측정된 0으로 왜곡하지 않고 `None`(JSON null)으로 정확히 보존. 정규화 총합 `normalized_total = input + output`은 별도로 일관되게 산출.

### 2.2 계정 Quota 수집 (`pc/quota.py`)
- **Native App-Server RPC**: 로컬 `codex app-server`에 stdio JSON-RPC 연결.
- **정식 핸드셰이크 순서**: `initialize` -> `initialized` -> `account/rateLimits/read`.
- **진정한 논블로킹 타임아웃**: 스레드 및 큐 기반 `BoundedProcessReader`를 통해 blocking `readline`으로 인한 무한 대기 방지 및 자식 프로세스 정리(`terminate` -> `kill` -> `wait`) 보장.

### 2.3 정규화 및 스키마 검증 (`pc/normalizer.py`, `pc/frame.py`)
- **6채널 Session Telemetry**: `input`, `output`, `cached_input`, `reasoning_output`, `source_total`, `normalized_total` 채널 구성.
  - `cached_input` 및 `reasoning_output`은 부분값으로 취급하며, null인 경우 invariant 검사 시 안전하게 처리.
- **Semantic Validator & cdm/1 프레이밍**:
  - `usage-snapshot.schema.json` 및 `cdm-frame.schema.json` 검증.
  - canonical UTF-8 JSON (공백 없음, 키 정렬, `ensure_ascii=False`).
  - unsigned payload 대상 CRC32 (8자리 대문자 hex), 최대 65,536 바이트 한도 준수.

### 2.4 순번 상태 머신 및 전송 제어 (`pc/sender.py`)
- **원자적 순번 예약**: 쓰기 수행 **직전**에 다음 uint32 순번을 디스크에 원자적(`os.replace`)으로 영속화. 실패 시에도 순번 소비.
- **Fail-Closed & 안전한 초기화**:
  - `DeviceSequenceState.from_dict`: `device_alias`의 경로 순회(`..`, `/`, `\`) 차단, `updated_at`이 유한한 양의 실수인지 엄격히 검증.
  - `StateStore.initialize_new`: 디바이스 락 획득 지원 및 암묵적 덮어쓰기 거부.
  - `CdmSender.__init__`: `StateStore.load` 실패 시 획득한 디바이스 락을 안전하게 즉시 해제.
- **Windows OS 레벨 싱글 센더 락**: Windows `msvcrt.locking` 기반으로 프로세스 비정상 종료 시 OS가 즉시 해제.

### 2.5 공유 수집 상태, 격리 캐시 및 에러 경로 (`pc/state.py`)
- **타깃 세션 격리 캐시**: 세션 A 선택 후 존재하지 않는 세션 B로 변경 시, 세션 A의 값이 세션 B로 오염되지 않도록 타깃 키별 독립 격리.
- **멀티 프로바이더 캐시 보존**: 여러 프로바이더 픽스처를 독립된 경로 식별자로 분리 관리.
- **누락 파일 에러 라우팅**: 누락된 `personal-usage` 및 `global-reset` 파일은 조용히 무시되지 않고 error/last-good 경로로 라우팅. 콜드 에러 시 임의의 성공 캡처 시각을 위조하지 않고 `None` 처리.
- **와이어 에러 개인정보 보호**: `error_reason`에 포함된 로컬 파일 경로를 `<local_path>`로 치환하여 네트워크 와이어 상에 파일시스템 경로 노출 차단.
- **Stale 에이징 판정**: `reference_time` 생략 시 현재 UTC를 비교 기준으로만 사용하여 stale 여부를 판정하며, 스냅샷의 원본 `observed_at` 타임스탬프는 일절 변조하지 않음.

### 2.6 인터럽터블 Watch 스케줄러 및 CLI (`pc/cli.py`)
- **수동 갱신 인터럽트**: stdin Enter 입력 시 대기 시간 없이 즉시(<=5초 이내) 수집 및 전송.
- **초기화 가드**: `init-device` 명령 시 `--confirmed-empty-receiver` 또는 `--force-overwrite` 명시 플래그 필수화.
- **모드 가드**: `--port` 또는 명시적 `--dry-run` 미지정 시 실행 거부.

## 3. 검증 결과

`C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe -B -X utf8 -m unittest discover -s tests/pc` 실행 결과:
**총 39개 테스트 전체 통과 (OK, 0 failures, 0 errors)**:
1. `test_cumulative_token_count_not_double_summed`
2. `test_partial_line_and_truncation_handling`
3. `test_differing_source_total_and_normalized_total`
4. `test_privacy_boundary`
5. `test_directory_scan_and_latest_selection`
6. `test_app_server_response_parsing`
7. `test_semantic_rule_available_requires_agent_and_host`
8. `test_canonical_json_and_crc32`
9. `test_frame_size_and_newline_contract`
10. `test_sequence_wrap_around_logic`
11. `test_atomic_sequence_reservation_consumes_on_failure`
12. `test_state_corruption_fails_closed`
13. `test_stale_boundaries_0_299_300`
14. `test_native_codex_0159_nested_event_shape`
15. `test_token_observation_time_not_polluted_by_later_events`
16. `test_invalid_token_invariants_rejected`
17. `test_session_directory_scan_recurses_date_folders`
18. `test_rate_limits_by_limit_id_parsed`
19. `test_state_loss_while_running_halts_immediately`
20. `test_single_sender_lock_prevents_duplicate_instance`
21. `test_sequence_persistence_across_restart`
22. `test_future_timestamp_rejected`
23. `test_percent_sum_relation`
24. `test_stale_detection_on_production_snapshot`
25. `test_cli_explicit_session_selection_required`
26. `test_hung_stream_times_out_and_cleans_up_process`
27. `test_source_isolation_and_last_good_retention`
28. `test_stale_detection_0_299_300`
29. `test_initialize_new_refuses_silent_overwrite`
30. `test_os_lock_released_on_subprocess_crash` (Windows 프로세스 트리 강제 종료 및 OS 락 해제 검증)
31. `test_refuse_implicit_loopback_when_port_missing`
32. `test_watch_manual_trigger_immediate_dispatch`
33. `test_alias_safety_and_updated_at_validation` (경로 순회 거부 및 NaN updated_at 차단)
34. `test_lock_released_on_failed_load` (상태 로드 실패 시 디바이스 락 즉시 해제)
35. `test_init_device_confirmed_empty_guard` (CLI 초기화 확인 가드)
36. `test_wire_error_privacy_and_metric_kind` (와이어 경로 마스킹 및 session_telemetry 메트릭 유지)
37. `test_session_isolation_across_selections` (세션 A -> 누락 세션 B 선택 간 값 격리)
38. `test_missing_personal_usage_and_global_reset_routed_to_error` (누락 파일 error 경로 라우팅)
39. `test_absent_optional_counts_remain_null` (생략된 선택적 토큰 카운트 null 보존)

## 4. 운영자 CLI 재현 절차

### 1) 디바이스 순번 초기화 (미초기화 수신자 확인 플래그 필수)
```powershell
python -m pc.cli init-device --device-alias desk-meter-1 --initial-sequence 0 --confirmed-empty-receiver
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
