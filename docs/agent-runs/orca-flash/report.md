# PC 수집기·전송기 구현 보고서 (orca-flash)

- 작성자: AGY Flash (`gemini-3.8-flash-medium`)
- Task ID: `task_fa0b12bd6fda` (Initial) / `task_3963de21ddd1` (Remediation 1) / `task_c6f6d8f00810` (Runtime Gaps) / `task_a6eebb977125` (Cohort Probe Remediation & C Interop)
- Dispatch ID: `ctx_04111d8d4601`
- 터미널: `term_57af52b9-738e-44cc-beb8-4d2204a41b46`
- 코디네이터 터미널: `term_b616990b-a6c9-4d5e-90c2-47af89701a69`
- 최종 갱신일: 2026-10-09

## 1. 개요 및 구현 범위

동결 과제 계약(`PRODUCT_CONTRACT.md`), 협업 설계(`docs/design/2026-10-08-orca-harness.md`), 코디네이터 지침(`experiments/orca-harness-20261008/operator/pc-post-resume-probe.json`), 그리고 코디네이터 Task `task_a6eebb977125`에 따라 Windows 환경의 신규 PC 수집기 및 `cdm/1` 전송기(`pc/`)와 검증 테스트(`tests/pc/`)를 순수 표준 라이브러리 및 기설치 패키지(`jsonschema`) 기반으로 보완 완료했습니다.

소유 파일(`pc/`, `tests/pc/`, `docs/agent-runs/orca-flash/`) 외의 57개 원본 동결 입력 및 타 역할 파일은 일절 수정하지 않았으며, 작업자 개발 및 테스트 단계에서는 엄격한 비식별 synthetic 데이터만을 사용하였습니다.

## 2. 주요 아키텍처 및 Cohort 결함 보완 내용

### 2.1 Watch/Send 수집 후 Stamping 및 Envelope-Time Invariant 검증 (`pc/cli.py`, `pc/frame.py`)
- **결함 원인**: 이전 watch 구현에서 `sent_at`을 수집 수행 전에 먼저 생성하여, 수집 도중 발생한 새 관측 시각(`observed_at`)이 프레임 시각보다 미래가 되어 실제 C 수신자(`cdm-host.exe`)에서 `SNAPSHOT_INVALID`로 거부되었습니다.
- **수정 내용**:
  - `run_watch_loop` 및 `cmd_send`에서 수집(`sm.collect_all`) 완료 직후에 `sent_at`을 스탬핑하도록 순서 변경.
  - `pc/frame.py`의 `build_frame` 및 `decode_frame`에 `validate_envelope_time_invariant`를 추가하여, `observed_at > sent_at`, `last_good_at > sent_at`, `captured_at > sent_at`, window `resets_at`과 `reset_status` 불일치가 있을 시 `SNAPSHOT_INVALID` 또는 `GLOBAL_INVALID`로 즉시 fail-closed 처리. C 수신기의 검증 조건과 100% 동일하게 일치시켰습니다.

### 2.2 Cold Global Reset 스키마 위반 방지 (`pc/state.py`, `pc/cli.py`)
- **결함 원인**: 콜드 글로벌 오류 발생 시 `captured_at=None`인 딕셔너리를 와이어에 전송하여 `cdm-frame.schema.json`의 `captured_at` date-time 필수 제약을 위반(`FRAME_SCHEMA_INVALID`)했습니다.
- **수정 내용**:
  - 관측된 적 없는 콜드 글로벌 레코드는 임의의 시각을 조작하거나 null로 보내지 않고, 와이어(`global_resets`) 상에서 완전히 생략(`[]`).
  - 로컬 소스 실패는 `sm.source_errors`에 기록하고 stderr로 출력하며, `cmd_collect`에서 0이 아닌 종료 코드 1을 반환.
  - 웜 글로벌 오류는 이전 정상 수집 시점의 실제 `captured_at`을 그대로 유지하고 `stale=True`, `error_code="GLOBAL_RESET_ERROR"`로 보존하여 C 수신기에 정상 전달.

### 2.3 멀티 엔트리 프로바이더 파일 캐시 보존 및 말폼 격리 (`pc/state.py`)
- **결함 원인**: 파일 단위 단일 키로 캐싱하여 3개 엔트리가 담긴 프로바이더 파일(`multi-provider-healthy.json`) 로드 실패 시 마지막 1개(google)만 남고 2개(openai, anthropic)가 유실되었습니다.
- **수정 내용**:
  - 각 엔트리를 파일 경로와 엔트리 식별자를 결합한 고유 소스 ID(`fixture:<path>:<entry_key>`)로 개별 캐싱.
  - 파일 로드 실패 시 이전에 성공했던 모든 엔트리를 `FIXTURE_LOAD_ERROR`로 100% 보존.
  - 파일 내 특정 엔트리가 비정상(malformed)인 경우 해당 엔트리만 `FIXTURE_ENTRY_ERROR`로 격리하고 정상 엔트리는 정상 업데이트.

### 2.4 세션 식별자 경로 맥락 격리 및 와이어 개인정보 보호 (`pc/state.py`)
- **수정 내용**:
  - 단순 파일명 basename이나 리터럴 "latest" 대신 실제 선택된 세션 ID와 정규화된 경로 맥락을 결합하여 캐시 키 생성.
  - 글로벌/개인 입력 경로가 변경되어도 타 소스 캐시를 상속하지 않음.
  - 와이어 상의 `snapshot_id` 및 `error_reason`에 로컬 파일시스템 경로(Windows 드라이브 및 Unix 경로)나 대화 내용이 일절 노출되지 않도록 완전 마스킹(`<local_path>`).

### 2.5 Watch 주기 및 데드라인 타이밍 보정 (`pc/cli.py`)
- **수정 내용**:
  - 자동 갱신 주기(<=60초)에 수집 및 전송 소요 시간을 포함하도록 데드라인 기반 스케줄링 적용.
  - 수동 갱신(Enter 키 또는 이벤트)이 발생해도 기존 자동 갱신 데드라인을 뒤로 밀지 않음.
  - 포트 재연결 시 1초 throttle을 준수하며 재연결 즉시(<=5초 이내) 전송 수행.

### 2.6 실제 프로덕션 C 수신기 (`cdm-host.exe --wire`) 연동 검증 (`tests/pc/test_cohort_probe_regressions.py`)
- 파이썬 페이크 수신기가 아닌 실제 C 실행 파일(`tests/firmware/.build/cdm-host.exe --wire`)에 `line_hex`, `mono_ms`, `now_ms` 프로토콜로 직접 프레임을 전달하여 interop 성공 확인.

### 2.7 Untimed Token Event 관측 날조 방지 및 에러 격리 (`pc/normalizer.py`, `pc/state.py`)
- **결함 원인**: 세션 파일에 `session_meta` 및 `token_count`가 존재하나 이벤트 타임스탬프가 없는 경우, 임의의 시각이나 현재 시각을 날조하여 가짜 성공(`available`) 관측을 생성하던 문제.
- **수정 내용**: 원본 관측 시각이 없으면 가짜 성공 관측을 만들지 않고 `SESSION_COLLECTION_ERROR`로 격리. `build_session_telemetry_snapshot`에서 `observed_at`에 임의의 reference/current time을 주입하지 않음.

### 2.8 Cold Source Error 타임스탬프 경계 준수 (`pc/state.py`)
- **수정 내용**: `CollectionSourceState.update_error`의 콜드 경로(이전 성공 스냅샷 부재 시)에서 성공적인 관측이 없었으므로 `observed_at: None`, `last_good_at: None`을 유지(스키마 nullable 허용)하여 C 수신기에 스키마 준수 에러 스냅샷 전송.

### 2.9 수동 갱신 및 포트 가용 시 5초 데드라인 예산 분할 (`pc/cli.py`, `pc/state.py`, `pc/quota.py`, `pc/sender.py`)
- **결함 원인**: 코디네이터 재현 `operator/pc-manual-deadline-probe.json`에서 발견되었듯이, 수집 단계 4.5s와 시리얼 write 2.0s가 순차 실행되어 수동 디스패치 완료에 6.5s가 소요됨으로써 동결 계약(`PRODUCT_CONTRACT` 3, 4절)의 최대 5.0s 데드라인을 위반하던 결함.
- **수정 내용**:
  - `SharedCollectionState.collect_all`에 `quota_timeout` 파라미터를 추가하여 수동 갱신(`is_manual`) 및 포트 재개방(`is_port_reopened`) 디스패치 시 수집 RPC 예산을 2.5s로 엄격히 제한.
  - `WindowsSerialSink`의 기본 write 타임아웃을 1.5s로 설정하여, 수집(<=2.5s) + 직렬화 및 전송(<=1.5s) 합계가 4.0s~5.0s 내에 완결되도록 예산 분할.
  - 느린 소스나 RPC 타임아웃 발생 시에도 기존 last-good 스냅샷을 `stale=True, status="error"`로 안전하게 보존하며 정상 소스에 영향을 주지 않음.
  - 자동 주기(<=60s)는 작업 소요 시간을 온전히 포함하며 수동 갱신에 의해 데드라인이 연기되지 않음.

## 3. 검증 결과

`C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe -B -X utf8 -m unittest discover -s tests/pc` 실행 결과:
**총 53개 테스트 전체 통과 (OK, 0 failures, 0 errors)**:
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
30. `test_os_lock_released_on_subprocess_crash`
31. `test_refuse_implicit_loopback_when_port_missing`
32. `test_watch_manual_trigger_immediate_dispatch`
33. `test_alias_safety_and_updated_at_validation`
34. `test_lock_released_on_failed_load`
35. `test_init_device_confirmed_empty_guard`
36. `test_wire_error_privacy_and_metric_kind`
37. `test_session_isolation_across_selections`
38. `test_missing_personal_usage_and_global_reset_routed_to_error`
39. `test_absent_optional_counts_remain_null`
40. `test_watch_sent_at_stamped_after_acquisition_accepted_by_production_c` (실제 C 수신기 SNAPSHOT_INVALID 결함 수정 검증)
41. `test_future_observation_rejected_by_envelope_validation_and_production_c` (봉투 시간 불변식 위반 거부)
42. `test_cold_global_omitted_on_wire_and_reports_locally_nonzero` (콜드 글로벌 와이어 생략 및 로컬 1 반환)
43. `test_warm_global_retains_true_capture_accepted_by_production_c` (웜 글로벌 진정 캡처 시각 유지 및 C 수신)
44. `test_multi_provider_file_failure_retains_all_entries_accepted_by_production_c` (3개 프로바이더 전원 보존)
45. `test_malformed_provider_entry_isolated_from_healthy_updates` (비정상 엔트리 개별 격리)
46. `test_session_identity_path_context_and_no_contamination_on_path_change` (경로 맥락 결합 격리 및 와이어 경로 차단)
47. `test_watch_auto_period_includes_slow_collection_duration` (자동 주기 내 수집 시간 포함 검증)
48. `test_watch_manual_trigger_does_not_move_automatic_deadline` (수동 갱신 시 자동 데드라인 불변 검증)
49. `test_untimed_token_event_routes_to_error_with_null_observed_at` (타임스탬프 없는 토큰 이벤트 관측 날조 방지 및 null 에러 스냅샷 C 수신 검증)
50. `test_cold_source_error_has_null_timestamps` (콜드 소스 에러 null 타임스탬프 스키마 및 C 수신 검증)
51. `test_watch_manual_deadline_bounded_under_slow_source_and_write` (수동 갱신 시 느린 소스/write에서도 5.0s 데드라인 완결 검증)
52. `test_port_reopened_deadline_bounded_under_slow_source` (포트 가용 시 신규 순번 전송 5.0s 완결 검증)
53. `test_watch_manual_arrival_during_in_flight_automatic_collection` (진행 중인 자동 수집 도중 수동 요청 유입 시 coalesce로 5.0s 완결 검증)

## 4. 운영자 CLI 재현 절차

### 1) 디바이스 순번 초기화
```powershell
python -m pc.cli init-device --device-alias desk-meter-1 --initial-sequence 0 --confirmed-empty-receiver
```

### 2) 세션 인벤토리 확인
```powershell
python -m pc.cli inventory --session-dir C:\path\to\sessions
```

### 3) 세션 수집 및 정규화
```powershell
python -m pc.cli collect --session-dir C:\path\to\sessions --latest --global-reset experiments/fixtures/codex-resets-history.json
```

### 4) cdm/1 프레임 생성 및 파일 출력 (Dry-run)
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
