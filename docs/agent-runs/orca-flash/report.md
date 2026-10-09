# PC 수집기·전송기 전구간 실질 5.0초 공유 데드라인 수렴 보고서 (orca-flash)

- 작성자: AGY Flash (`gemini-3.8-flash-medium`)
- Task ID: `task_e2907fe00c34` (실제 프로세스 정리 및 시리얼 큐 드레인 한계 하 5.0초 데드라인 수렴)
- Dispatch ID: `ctx_ca714297b040`
- 작업자 터미널: `term_3105fe45-46f8-4dce-9763-c24e2e98be09`
- 코디네이터 터미널: `term_54a83fa0-c831-41b9-8295-ca84d361c828`
- 갱신일: 2026-10-10

## 1. 개요 및 구현 범위

오퍼레이터 합성 프로브(`experiments/orca-harness-20261008/operator/pc-shared-budget-cleanup-probe.json`)에서 재현된 실시간 6.125초 초과 결함을 해결하고, 네이티브 프로세스 정리와 시리얼 드레인이 극한 경계에 도달하는 조건 하에서도 수동 갱신 사이클이 5.0초 이내에 완결(또는 명시적 bounded failure)되도록 구현했습니다:
1. **프로세스 정리 및 시리얼 드레인 실질 2.0초 통합 예산 예약 (`total_reserved = 2.0s`) 및 인위적 클램프 제거**:
   - `WindowsSerialSink`의 실제 바운디드 드레인 예산 1.0초와 `cleanup_process`의 허용된 terminate(0.5초) + kill(0.49~0.5초) 대기 시간 1.0초를 온전히 포함한 2.0초를 필수 예약 시간으로 반영.
   - `pc/quota.py`의 `cleanup_process` 및 `fetch_native_rate_limits`에서 인위적 양수 하한 클램프(`max(0.1, ...)` 및 `max(0.01, ...)`)를 완전히 제거하고, `timeout <= 0`인 경우 대기 없이 즉시 `kill()` 및 `wait(0.0)` 처리.
   - 인위적으로 양수 예산을 위조하는 하한 클램프를 완전히 배제하고, 수동 요청 도착 시점 기준 잔여 예산 `remaining_budget = 5.0 - elapsed`를 엄격히 산정.
2. **예산 부족 시 네이티브 RPC 스폰 원천 차단 및 Bounded Error / Last-good 보존**:
   - `remaining_budget <= 2.0s`인 경우 네이티브 subprocess 생성을 일절 시도하지 않고(`collection_timeout = 0.0`), 상태 관리자(`SharedCollectionState`)를 통해 `QUOTA_TIMEOUT` 에러 스냅샷을 생성하여 기존 last-good 관측치 및 구조를 안전하게 보존.
   - 불필요한 프로세스 스폰 및 1초에 달하는 cleanup 지연을 생략하고, 신선한 로컬 세션 데이터(250 토큰 카운트)를 즉시 수집하여 신규 프레임으로 송출.
3. **실질적 OS 시리얼 쓰기/드레인 타임아웃 바운딩 및 실패 순번 소비**:
   - `WindowsSerialSink.write_timeout` 세터가 pyserial `self.serial.write_timeout`도 동적으로 변경하도록 구현하여 느린 OS write 자체를 실질적으로 바운딩.
   - 수동 갱신 프레임 송출 시 실제 잔여 시간에 맞춘 `serial_write_timeout = min(1.0, max(0.0, 5.0 - (drain_now - manual_request_arrival) - 0.15))`를 전달하여 엄격한 데드라인 안전 마진 적용.
   - 잔여 드레인 예산 고갈 시, 순번은 사전 예약 소비(`reserve_next_sequence`)한 채 가짜 성공 로그 없이 명시적 전송 실패(`WRITE_IO_ERROR`)로 안전하게 fail-closed 처리.

소유 파일인 `pc/`, `tests/pc/`, `docs/agent-runs/orca-flash/checkpoint.md`, `report.md`만 수정하였으며, firmware/designers/동결 57개 입력/타 역할 파일/`tests/integration/`은 일절 변경하지 않았습니다. 개발 및 검증에는 비식별 synthetic 데이터만을 사용하였습니다.

## 2. 세부 결함 분석 및 해결 내용

### 2.1 실제 최악 지연 모델링 및 무예산 시 RPC 회피 (`pc/cli.py`, `pc/state.py`, `pc/quota.py`)
- **결함 원인**: 이전 코드는 예약 시간을 1.5초로 과소평가하여, 실제 terminate(0.5s) + kill(0.49s) = 0.99s와 시리얼 드레인(0.99s)의 합인 1.98s를 수용하지 못했습니다. 또한 `remaining <= 1.5`일 때도 양수 타임아웃을 부여하여 RPC 프로세스를 시작시킴으로써 프로세스 정리 지연(0.99s)과 시리얼 드레인(0.99s)이 누적되어 총 6.125초로 데드라인을 초과했습니다.
- **수정 내용**:
  - `run_watch_loop`에서 `reserved_serial = 1.0`, `reserved_cleanup = 1.0`을 합산한 `total_reserved = 2.0s`를 엄격한 하한으로 설정.
  - `remaining_budget <= 2.0s`인 경우 `collection_timeout = 0.0`을 할당.
  - `cleanup_process`에서 인위적 양수 하한 클램프를 제거하여 `timeout <= 0`이면 즉시 `kill()` 및 `wait(0.0)` 수행.
  - `SharedCollectionState.collect_all`에서 `quota_timeout <= 0`인 경우 `fetch_native_rate_limits`를 호출하지 않고 `QUOTA_TIMEOUT` 에러 스냅샷을 즉시 기록(기존 last-good 캐시 보존).
  - `fetch_native_rate_limits`에서도 `timeout_seconds <= 0` 가드를 추가하여 subprocess 스폰을 차단하고 즉시 fail-closed 처리.

### 2.2 실질적 시리얼 드레인 데드라인 바운딩 (`pc/sender.py`, `pc/cli.py`)
- **결함 원인**: 수집 후 시리얼 드레인을 수행할 때, 드레인 시작 시점에 남은 데드라인이 1.0초 미만인 경우 싱크가 기본 1.0초 전체를 기다려 5.0초를 초과할 수 있었습니다. 또한 OS serial.write 호출 시 write_timeout이 고정되어 느린 쓰기 발생 시 타임아웃이 초과될 수 있었습니다.
- **수정 내용**:
  - `WindowsSerialSink`: `_custom_write_timeout` 세터를 구현하고, `self.serial.write_timeout`에도 동적으로 값을 적용하여 실제 pyserial write 자체를 바운딩.
  - `CdmSender.transmit_payload`: `write_timeout` 매개변수를 지원하여, 잔여 드레인 예산이 0 이하일 경우 순번을 소비(`reserve_next_sequence`)한 채 즉시 `WRITE_IO_ERROR`를 반환. 유효 예산 전달 시 싱크의 `write_timeout`을 일시 설정하여 느린 쓰기 및 드레인 루프가 잔여 데드라인을 넘지 않도록 바운딩한 후 원복.
  - `run_watch_loop`: `now_fn()`을 사용하여 시간 공급자와의 정합성을 확보하고, `serial_write_timeout`에 0.15s 안전 마진을 적용하여 운영체제 스케줄링 틱에 의한 마이크로초 초과를 원천 방지.

## 3. 회귀 테스트 및 검증 결과

### 3.1 `tests/pc` 단위 및 회귀 테스트
`python -B -X utf8 -m unittest discover -s tests/pc -p "test_*.py" -v`:
**63개 테스트 전체 통과 (63 tests, OK, 0 failures, 0 errors)**:
- `test_delayed_terminate_kill_and_near_limit_serial_drain_enforces_five_second_budget`: 실제 `WindowsSerialSink` + `FakeSerial` 경계를 사용하여 0.5s terminate + 0.49s kill + 0.99s 드레인의 극한 오퍼레이터 프로브 시나리오 하에서 거짓 양성 분기 없이 실제 터미널 완료 또는 명시적 bounded failure가 5.0s 데드라인 내에 완결됨을 엄격히 검증 (신규 보강).
- `test_slow_write_and_drain_shares_timeout_and_respects_os_write_timeout`: 느린 OS write 발생 시 write_timeout을 준수하여 0.1s 내에 fail-closed되고 원래 타임아웃이 정상 복원됨을 검증 (신규 추가).
- `test_pure_quota_when_no_budget_avoids_rpc_and_preserves_error_or_cache`: 0 예산 시 RPC 미호출 및 bounded error / last-good 보존 검증 (신규 추가).
- 기존 60개 테스트(2차 수동 요청 보존, 바운디드 드레인, fail-closed, 순번 소비, 토큰 파싱, 에러 격리, 스키마 검증, 상태 락 등) 일체 회귀 없음.

### 3.2 통합 테스트 검증 및 Luna 소유자 적응 인계
- `tests/integration/test_pc_producer_to_c.py` 대상 검증:
  - `test_auto_rpc_remainder_manual_rpc_and_successful_serial_drains_share_five_second_budget`: 통과 (OK, 4.012s <= 5.0s, bounded error path).
  - `test_second_manual_request_during_manual_write_is_not_lost`: 통과 (OK).
  - `test_pure_quota_request_after_collection_requires_fresh_native_acquisition`: 테스트 line 927의 반환 스키마 접근 오타(`row["current"]` -> `row["usage"][0]["current"]`) 적응 사항은 Luna에게 유지 인계.

## 4. 물리 하드웨어 검증 한계 및 상태
- 실제 COM 포트 열기, 물리 장치 펌웨어 플래시, 하드웨어 리셋은 안전 규칙에 따라 수행하지 않음 (`COM/flash/reset calls prohibited`).
- 물리 하드웨어 및 실계정 검증 증거는 `not_run` 상태이며, 호스트 기반 시뮬레이션 및 실제 프로덕션 C 바이너리(`cdm-host.exe --wire`) 연동 검증만 통과함 (`product_pass=false`).

---

## 5. 최신 승인 소스 데드라인 보정 및 OS 세터 예외 전파 (2026-10-10)

- **문서화 Task/Dispatch**: `task_9becb3b414d9` / `ctx_41536de6636d` (터미널: `term_25d7d35f-8e19-4188-9442-70cfee46313c`, 코디네이터: `term_9fb88ac7-32b2-43f6-8ba2-c203ed6531bf`)
- **최신 소스 승인 Task/Dispatch**: `task_d7aa5e059e8d` / `ctx_a7d558d25511` (완료 메시지: `msg_c1e14cc550e2`, 동결 커밋: `39e52bd`)

### 5.1 해결된 잔여 결함 및 최소 완전 수정

1. **진행 중 루프 종료 시 대기 중인 수동 요청 오리진 보존 (`pc/cli.py`)**:
   - 기존 루프는 iteration 수행 도중 수동 요청 이벤트가 발생했을 때 루프 하단에서 `manual_request_arrival = now_fn()`으로 새로 갱신하여, 앞선 AUTO/MANUAL 작업 소요 시간을 지우고 5초 예산을 리셋하는 결함이 있었습니다.
   - 보수적 기준인 `in_flight_start`를 오리진으로 설정(`manual_request_arrival = in_flight_start`)하여, 이미 진행된 소요 시간을 예산에 온전히 반영하고 5초 데드라인을 재시작하지 않도록 수정했습니다.
2. **실제 OS write_timeout 적용 선행 및 CdmSender 예외 전파 (`pc/sender.py`)**:
   - `WindowsSerialSink.write_timeout` 프로퍼티 세터에서 커스텀 필드 갱신 전 실제 `self.serial.write_timeout = value` 할당이 먼저 성공하도록 보장했습니다.
   - `CdmSender.transmit_payload`에서 타임아웃 세터 실행 실패를 try-except pass로 삼키지 않고 바깥 블록으로 노출하여, `target_sink.write` 호출 이전에 명시적 `WRITE_IO_ERROR`로 전환되도록 수정했습니다. 이 경우에도 시퀀스는 정상 예약(`reserve_next_sequence`)되어 소비(`seq consumed`)되며, 전송 바이트는 0으로 보고됩니다.
3. **지연 정리 및 시리얼 드레인 회귀 테스트 교정 (`tests/pc/test_cohort_probe_regressions.py`)**:
   - `test_delayed_terminate_kill_and_near_limit_serial_drain_enforces_five_second_budget`에서 가짜 serial `out_waiting` 폴링 경계에서 강제로 완료 신호를 주는 방식 대신, 실제 프로덕션 `CdmSender.transmit_payload`의 종료 시점(terminal SendOutcome)과 실제 단조 시간(`monotonic time`)을 직접 관찰하는 테스트 래퍼를 도입했습니다.
   - 잔여 시간 부족으로 인한 유한 오류(`WRITE_IO_ERROR`)를 정당한 동작으로 인정하고, 닫힌 가짜 포트에서 0을 반환하여 거짓 성공을 유발하지 않도록 `raise IOError`로 방어했습니다.
4. **거부하는 실제 OS write_timeout 세터 음성 회귀 테스트 추가 (`tests/pc/test_cohort_probe_regressions.py`)**:
   - `test_rejecting_os_write_timeout_setter_fails_before_write_and_consumes_seq`를 추가하여, OS 타임아웃 설정 실패 시 write 미호출, 0바이트 전송, 시퀀스 소비, `WRITE_IO_ERROR` 반환을 검증했습니다.

### 5.2 최신 검증 결과 및 범위 한계

- **단위 테스트 실행 명령**:
  ```sh
  C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe -B -X utf8 -m unittest discover -s tests/pc -q
  ```
- **검증 결과**: **64개 단위 테스트 전원 통과 (64 tests run, OK, 0 failures, 0 errors, 코디네이터 기준 10.898s / wall 11.062s)**.
- **물리 하드웨어 및 독립 검토 한계**:
  - 최신 64/64 통과는 호스트 시뮬레이션 및 단위 검증 증거(host evidence)이며, 독립된 Luna 측 검토(`ctx_6b00e6339d06`)가 진행 중입니다.
  - 안전 지침에 따라 실제 COM 포트 통신, 펌웨어 플래싱, 하드웨어 리셋은 일절 실행하지 않았으며(`not_run`), 물리 장치 검증 통과는 미결정(`product_pass=false`) 상태를 엄격히 유지합니다.
