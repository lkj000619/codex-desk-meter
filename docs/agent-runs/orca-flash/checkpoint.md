# Checkpoint: PC Manual Shared Deadline Full End-to-End Bound Fixes (orca-flash)

- 일시: 2026-10-10T02:19:00+09:00
- Task ID: `task_e2907fe00c34`
- Dispatch ID: `ctx_ca714297b040`
- 작업자 터미널: `term_3105fe45-46f8-4dce-9763-c24e2e98be09`
- 코디네이터 터미널: `term_54a83fa0-c831-41b9-8295-ca84d361c828`
- 담당 역할: PC 수집·전송 (`pc/`, `tests/pc/`, `docs/agent-runs/orca-flash/`)
- 현재 상태:
  1. **실제 최악 지연 반영 통합 예산 예약 (`total_reserved = 2.0s`) 및 인위적 클램프 제거**:
     - 시리얼 출력 큐 드레인 예산 1.0초와 네이티브 프로세스 정리 예산 1.0초(terminate wait 0.5초 + kill wait 0.49초)를 합산한 순수 2.0초를 필수 예약 시간으로 설정.
     - `pc/quota.py`의 `cleanup_process` 및 `fetch_native_rate_limits`에서 인위적 양수 하한 클램프(`max(0.1, ...)` 및 `max(0.01, ...)`)를 완전히 제거하고, `timeout <= 0`인 경우 대기 없이 즉시 `kill()` 및 `wait(0.0)` 처리.
     - 수동 요청 시점 기준 실제 경과 시간을 차감한 `remaining_budget = 5.0 - elapsed` 산정 시 인위적 클램프를 완전히 배제.
  2. **예산 소진 시 네이티브 RPC 스폰 회피 및 Bounded Error / Cache 보존 (`pc/state.py`, `pc/quota.py`)**:
     - `remaining_budget <= 2.0s`인 경우 네이티브 RPC(`fetch_native_rate_limits`) 프로세스를 일절 시작하지 않고(`collection_timeout = 0.0`), `QUOTA_TIMEOUT` 명시적 에러 스냅샷을 생성하여 기존 last-good 스냅샷의 관측치와 필드를 그대로 보존.
     - 외부 RPC를 스킵함으로써 불필요한 프로세스 스폰 및 1.0초에 달하는 cleanup 지연을 원천 차단하고, 로컬 세션 데이터(250 토큰 카운트)를 즉시 수집하여 신규 프레임으로 송출.
  3. **실질적 OS 시리얼 쓰기/드레인 타임아웃 바운딩 및 실패 순번 소비 (`pc/sender.py`, `pc/cli.py`)**:
     - `WindowsSerialSink.write_timeout` 세터가 pyserial `self.serial.write_timeout`도 동적으로 변경하도록 구현하여 느린 OS write 자체를 실질적으로 바운딩.
     - 수동 갱신 프레임 송출 시 실제 잔여 시간에 맞춘 `serial_write_timeout = min(1.0, max(0.0, 5.0 - (drain_now - manual_request_arrival) - 0.15))`를 전달하여 엄격한 데드라인 안전 마진 적용.
     - 잔여 드레인 예산이 고갈되거나 드레인 시간 초과 시, 순번은 사전 예약 소비(`reserve_next_sequence`)한 채 가짜 성공 로그 없이 명시적 전송 실패(`WRITE_IO_ERROR: Drain timed out`)로 안전하게 fail-closed 처리.
  4. **단위 및 회귀 테스트 검증**:
     - `tests/pc/test_cohort_probe_regressions.py`에 실제 `WindowsSerialSink` + `FakeSerial` 경계를 사용한 오퍼레이터 프로브 재현 케이스(`test_delayed_terminate_kill_and_near_limit_serial_drain_enforces_five_second_budget`) 보강 (거짓 양성 분기 배제, 실제 터미널 완료 또는 명시적 bounded failure 시점 <= 5.0s 엄격 검증).
     - slow-write 타임아웃 준수 및 복원 테스트(`test_slow_write_and_drain_shares_timeout_and_respects_os_write_timeout`) 추가.
     - 무예산 시 RPC 스킵 케이스(`test_pure_quota_when_no_budget_avoids_rpc_and_preserves_error_or_cache`) 추가.
     - `tests/pc` 내 전체 63개 단위/회귀 테스트 100% 통과 (63 tests, OK, 0 failures, 0 errors).
  5. **통합 테스트 및 Luna 인계 사항**:
     - `test_auto_rpc_remainder_manual_rpc_and_successful_serial_drains_share_five_second_budget`: 통과 (4.012s <= 5.0s).
     - `test_second_manual_request_during_manual_write_is_not_lost`: 통과.
     - Luna 소유 통합 테스트(`tests/integration/test_pc_producer_to_c.py` line 927)의 반환 스키마 접근 오타(`row["current"]` -> `row["usage"][0]["current"]`) 적응 사항은 유지 인계.
  6. **실물 하드웨어 제한사항**: 실제 COM 포트 통신/플래시/리셋은 수행하지 않았으며 physical/live evidence는 `not_run`, `product_pass=false`.

## 검증 결과
`python -B -X utf8 -m unittest discover -s tests/pc -p "test_*.py" -v`:
**63 tests run, OK, 0 failures, 0 errors**.

---

## 최신 갱신 Checkpoint (2026-10-10) — PC 데드라인 카운터 리뷰 및 OS 타임아웃 세터 보정 완료

- **문서화 Task/Dispatch (현재)**:
  - Task ID: `task_9becb3b414d9`
  - Dispatch ID: `ctx_41536de6636d`
  - 작업자 터미널: `term_25d7d35f-8e19-4188-9442-70cfee46313c`
  - 코디네이터 터미널: `term_9fb88ac7-32b2-43f6-8ba2-c203ed6531bf`
- **승인 소스 변경 Task/Dispatch (최신 코드 베이스)**:
  - Task ID: `task_d7aa5e059e8d`
  - Dispatch ID: `ctx_a7d558d25511` (완료 메시지: `msg_c1e14cc550e2`)
  - 안정 기준 커밋: `39e52bd`
  - 담당 역할: PC 수집·전송 (`pc/`, `tests/pc/`, `docs/agent-runs/orca-flash/`)
- **최신 구현 및 보정 상세**:
  1. **진행 중 루프 종료 시 수동 요청 오리진 보존 (`pc/cli.py`)**:
     - iteration 실행 도중 도착한 pending `MANUAL` 트리거가 iteration 종료 시 `manual_request_arrival = now_fn()`으로 덮어써져 5초 예산이 리셋되던 결함을 교정.
     - 해당 iteration 동안 소요된 작업 시간을 정직하게 유지하기 위해 `manual_request_arrival = in_flight_start`로 설정하여 이전 작업 시간을 5초 예산에서 정상 차감.
  2. **OS write_timeout 강제 적용 및 세터 실패 전파 (`pc/sender.py`)**:
     - `WindowsSerialSink.write_timeout` 세터에서 `self._custom_write_timeout` 업데이트 전 실제 `self.serial.write_timeout` 할당을 먼저 성공하도록 변경.
     - `CdmSender.transmit_payload`에서 `target_sink.write_timeout` 설정 실패를 삼키지 않고 `target_sink.write` 호출 전에 기존 `WRITE_IO_ERROR`로 즉시 전파.
     - 시퀀스는 사전에 예약(`reserve_next_sequence`)되어 소비(`consumed seq`)되고, 실제 전송 바이트는 0으로 보고(`zero bytes`). 정상 시도시 복원(`finally: orig_wt`) 유지.
  3. **터미널 SendOutcome 단조 시간 관찰 및 회귀 테스트 교정 (`tests/pc/test_cohort_probe_regressions.py`)**:
     - 지연 정리(0.5s terminate + 0.49s kill) 및 시리얼 드레인(0.99s) 테스트에서 `out_waiting` 폴링 경계의 인위적 플래그 대신, 실제 `CdmSender.transmit_payload`의 완료(terminal SendOutcome)와 단조 시간(`monotonic time`)을 직접 관찰하도록 래퍼 적용.
     - 남은 시간 부족 시 5초 이내의 유한 오류(`WRITE_IO_ERROR`)를 정상 인정하고, 닫힌 fake serial의 `out_waiting`에서 가짜 0 반환을 방지(`Closed fake queuezero never success`).
  4. **거부하는 실제 OS write_timeout 세터 음성 회귀 테스트 추가 (`tests/pc/test_cohort_probe_regressions.py`)**:
     - `test_rejecting_os_write_timeout_setter_fails_before_write_and_consumes_seq`: OS 레벨 write_timeout 설정 거부 시 write가 호출되지 않고, 0바이트 전송 및 `WRITE_IO_ERROR` 반환, 시퀀스 정상 소비를 검증하는 테스트 추가.
- **검증 명령 및 현황**:
  - 실행 명령: `C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe -B -X utf8 -m unittest discover -s tests/pc -q`
  - 결과: **64개 단위 테스트 전원 통과 (64 tests run, OK, 0 failures, 0 errors, 코디네이터 측정 10.898s / wall 11.062s)**.
  - 최신 PC 64개 테스트 통과는 호스트 증거(host evidence)에 국한되며, 독립적인 Luna 동일 과제 검토는 현재 `ctx_6b00e6339d06`로 진행 중.
  - COM 포트 통신/물리 펌웨어 플래시/하드웨어 리셋은 안전 격리 지침에 따라 미실행(`not_run`), 최종 제품 통과는 미결정(`product_pass=false`).
