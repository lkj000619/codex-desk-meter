# Checkpoint: PC Transport Drain & Manual Refresh Regression Fixes (orca-flash)

- 일시: 2026-10-10T00:57:00+09:00
- Task ID: `task_956c1c1b77b1`
- Dispatch ID: `ctx_2b9adeeceb2c`
- 작업자 터미널: `term_3105fe45-46f8-4dce-9763-c24e2e98be09`
- 코디네이터 터미널: `term_54a83fa0-c831-41b9-8295-ca84d361c828`
- 담당 역할: PC 수집·전송 (`pc/`, `tests/pc/`, `docs/agent-runs/orca-flash/`)
- 현재 상태:
  1. `WindowsSerialSink.flush`: 취소 불가능한 백그라운드 데몬 스레드 플러시를 완전히 제거하고, `self.serial.out_waiting` 기반의 동기식 바운디드 드레인(synchronous bounded drain)으로 대체 완료. `write`와 `drain`을 단일 타임아웃 예산(`write_timeout`) 내에서 통합 바운딩. `out_waiting` 프로퍼티 부재 시 또는 쿼리 중 오류 발생 시 즉시 명시적 `IOError`로 fail-closed 처리하며, 언바운디드 `serial.flush` 폴백은 일절 사용하지 않음.
  2. `CdmSender.transmit_payload`: 시리얼 쓰기 실패 및 드레인 타임아웃 발생 시에도 사전 예약된 순번(reserved sequence)을 영구 소비하고 전송 실패(`WRITE_IO_ERROR`)를 반환하도록 보장.
  3. `run_watch_loop`: 인플라이트 수집/전송 중 유입된 수동 이벤트를 이전 프레임에 섣불리 병합(coalesce)하거나 조기 클리어하지 않고, 세션 소스가 존재하는 경우 펜딩(pending) 상태로 유지하여 후속 틱에서 변경된 세션 데이터를 새로 수집하고 새 순번으로 전송 완료. 이전 프레임은 `MANUAL`로 라벨링되지 않음.
  4. 테스트 검증: `tests/pc` 내 전체 57개 단위/회귀 테스트 통과 (57 tests, OK, 0 failures, 0 errors).
  5. Luna 소유 통합 테스트(`tests/integration/test_pc_producer_to_c.py`) 적응 필요 사항 식별: `BlockingSerial` 및 `FakeSerial` 클래스에 `@property out_waiting` 속성이 정의되어 있지 않아 프로덕션 `WindowsSerialSink`에서 fail-closed(`WRITE_IO_ERROR`) 처리됨. Luna 소유자 적응(`@property def out_waiting(self): return 0`) 필요 사항을 코디네이터에 인계.
  6. 실물 하드웨어 제한사항: 실제 COM 포트 통신/플래시/리셋은 수행하지 않았으며 physical/live evidence는 `not_run`, 호스트 검증만 완료 (`product_pass=false`).

## 세부 수정 내역

1. **`pc/sender.py`**:
   - `WindowsSerialSink`: 백그라운드 스레드 flush 제거. `write` 시작 시각(`_write_start_time`)부터 `flush` 완료까지 경과 시간을 추적하여 단일 `write_timeout` 예산 초과 시 `TimeoutError` 발생.
   - `out_waiting` 접근 시 `hasattr` 및 게터 예외를 일관되게 `IOError("Serial output queue query failed: ...")`로 래핑.
   - `out_waiting` 인터페이스 미제공 시 언바운디드 `serial.flush`로 폴백하지 않고 `IOError("Serial transport does not provide output-queue out_waiting interface")`를 발생시켜 fail-closed 보장.
   - `LoopbackSink`: `@property out_waiting -> 0` 추가.
   - `CdmSender`: 전송 실패 시 예약된 순번을 소비한 상태로 유지하고 단일 인스턴스 락 및 리소스 정리 보장.

2. **`pc/cli.py`**:
   - `cmd_send`: `serial_sink`를 `try ... finally: serial_sink.close()`로 감싸 에러 발생 시에도 시리얼 핸들이 즉시 정리되도록 보장.
   - `run_watch_loop`:
     - 세션 소스 유무(`has_session_source`)를 판별하여, 수동 이벤트 유입 시 인플라이트 수집 중 세션 메타데이터가 이미 읽힌 상태라면 프레임을 MANUAL로 변경하지 않고 수동 이벤트를 펜딩으로 보존.
     - 프레임 전송 성공 후 `is_manual`인 경우에만 `manual_trigger_event.clear()` 수행.
     - 펜딩 수동 이벤트가 있을 경우 즉시 다음 루프에서 신규 수집을 수행하여 5.0초 이내에 새 세션 데이터를 반영한 신규 프레임 전송.

3. **`tests/pc/test_cohort_probe_regressions.py`**:
   - `test_windows_serial_sink_synchronous_bounded_drain_and_error_propagation`: 정상 지연 드레인, 정체 큐 드레인 타임아웃, 큐 쿼리 에러 전파, 스레드 누수 부재(active_count 동일), 닫힌 싱크 쓰기 거부 검증.
   - `test_cmd_send_drain_timeout_consumes_reserved_sequence_and_closes_wrapper`: 정체된 큐 타임아웃 시 순번 소비, 시리얼 닫힘, exit code 1 반환 검증.
   - `test_watch_manual_arrival_during_inflight_write_dispatches_fresh_collection_frame`: 전송 쓰기 중 수동 이벤트 유입 시 조기 클리어 방지 및 신규 세션 2차 프레임 전송 검증.
   - `test_watch_manual_event_during_auto_quota_collection_recollects_changed_session`: AUTO 쿼터 RPC 수집 중 세션 파일 변경 및 수동 요청 유입 시, 이전 프레임(50 토큰)에 병합하지 않고 즉시 2차 MANUAL 프레임(500 토큰)을 5초 이내 디스패치하는지 검증.

## 검증 결과
`python -B -X utf8 -m unittest discover -s tests/pc -p "test_*.py" -v`:
**57 tests run, OK, 0 failures, 0 errors**.
