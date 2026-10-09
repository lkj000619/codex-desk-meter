# Checkpoint: PC Watch Manual Request Race & Combined 5.0s Deadline Fixes (orca-flash)

- 일시: 2026-10-10T01:31:00+09:00
- Task ID: `task_1b01674fbb8c`
- Dispatch ID: `ctx_41e3573faa6e`
- 작업자 터미널: `term_3105fe45-46f8-4dce-9763-c24e2e98be09`
- 코디네이터 터미널: `term_54a83fa0-c831-41b9-8295-ca84d361c828`
- 담당 역할: PC 수집·전송 (`pc/`, `tests/pc/`, `docs/agent-runs/orca-flash/`)
- 현재 상태:
  1. **수동 요청 소비 시점 사전화 (Acquisition-Before-Consumption)**:
     - `manual_trigger_event.clear()`를 `sm.collect_all` 시작 직전으로 이동하여 수집 시작 시점에 요청을 소비.
     - 수집/전송/드레인 완료 후 무조건 `clear()`하던 이전 로직 및 `has_session_source` 불리언 추측 코드를 완전히 제거.
     - 인플라이트 수집/전송 중 유입된 수동 요청은 후속 틱 신규 수집을 위해 유실 없이 100% 보존.
  2. **MANUAL 전송 중 2차 수동 요청 보존**:
     - 1차 수동 프레임의 쓰기/드레인 중 추가로 발생한 2차 수동 요청도 보존되어 직후 2차 신규 프레임으로 송출됨.
  3. **인위적 클램프 없는 실시간 모노토닉 5.0초 통합 데드라인 준수 (Budget Allocation & Bounded Failure)**:
     - 인위적으로 시간을 조작하는 `max(0.5, ...)` 클램프를 완전히 배제하고, 수동 요청 도착 시점 기준 실제 남은 시간 `remaining_budget = 5.0 - elapsed`를 엄격히 산정.
     - 공유 시리얼 전송/드레인 예산(1.0s) 및 자식 프로세스 정리 마진(`cleanup_process` terminate 0.5s + kill 0.5s, 최대 1.0s)을 확보하기 위해 `reserved_transport_and_cleanup = 1.5s`를 차감한 `collection_timeout = min(2.0, remaining_budget - 1.5)` (남은 시간이 부족할 경우 `max(0.0, remaining_budget - 1.0)`) 할당.
     - 악의적 경계(Test 3: AUTO RPC 1.9s + drain 0.8s = 2.7s 경과)에서 남은 시간 2.3s에 맞춰 MANUAL RPC의 타임아웃이 0.8s(초기화 0.4s)로 축소되어 0.4s에 명시적 `INITIALIZE_FAILED`로 즉시 fail-closed 처리되고 프로세스가 정리되어, 캐시된 last-good 스냅샷을 보존한 bounded error path를 거쳐 총 4.28초 (<= 5.0초)에 직렬 드레인을 완결.
  4. **단위 및 회귀 테스트 검증**:
     - `tests/pc/test_cohort_probe_regressions.py`에 신규 3건 회귀 테스트 추가 완료.
     - `tests/pc` 내 전체 60개 단위/회귀 테스트 100% 통과 (60 tests, OK, 0 failures, 0 errors).
  5. **통합 테스트 및 Luna 인계 사항**:
     - `test_second_manual_request_during_manual_write_is_not_lost`: 통과 (0.380s).
     - `test_auto_rpc_remainder_manual_rpc_and_successful_serial_drains_share_five_second_budget`: 통과 (4.284s <= 5.0s, bounded error path).
     - `test_pure_quota_request_after_collection_requires_fresh_native_acquisition`: 2개 프레임 송출 및 수집은 완벽 통과했으나, Luna 소유 테스트(`tests/integration/test_pc_producer_to_c.py` line 927)의 반환 스키마 접근 오타(`row["current"]` 대신 C 바이너리가 반환하는 `row["usage"][0]["current"]`)로 인한 실패 확인. Luna 소유권 규칙 준수를 위해 본 작업자는 해당 파일을 수정하지 않고 코디네이터 및 Luna에게 인계.
  6. **실물 하드웨어 제한사항**: 실제 COM 포트 통신/플래시/리셋은 수행하지 않았으며 physical/live evidence는 `not_run`, `product_pass=false`.

## 세부 수정 내역

1. **`pc/cli.py` (`run_watch_loop`)**:
   - `manual_trigger_event.clear()`를 `sm.collect_all` 시작 직전으로 이동하여 수집 시작 전 사전 소비.
   - 루프 종료부의 무조건적인 `manual_trigger_event.clear()` 제거.
   - `has_session_source` 불리언 분기 완전 제거.
   - `remaining_budget = 5.0 - elapsed`와 `reserved_transport_and_cleanup = 1.5`를 적용한 `collection_timeout` 정밀 계산.

2. **`tests/pc/test_cohort_probe_regressions.py`**:
   - `test_second_manual_request_during_already_manual_write_dispatches_second_frame`: MANUAL 쓰기/드레인 중 2차 수동 요청 발생 시 유실 없이 2번째 프레임이 송출됨을 검증.
   - `test_pure_quota_request_after_collection_requires_fresh_native_acquisition`: session_file 없는 순수 쿼터 루프에서 수동 요청 시 신선한 native quota 취득 후 2번째 프레임 송출 검증.
   - `test_real_monotonic_combined_near_limit_auto_rpc_manual_rpc_and_serial_drains_share_five_second_budget`: 실시간 모노토닉 타이밍 환경에서 수동 요청 및 드레인이 5.0초 예산 내에서 완결됨을 검증.

## 검증 결과
`python -B -X utf8 -m unittest discover -s tests/pc -p "test_*.py" -v`:
**60 tests run, OK, 0 failures, 0 errors**.
