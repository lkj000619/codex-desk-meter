# PC 수집기·전송기 결함 보완 및 전송/수동 갱신 수렴 보고서 (orca-flash)

- 작성자: AGY Flash (`gemini-3.8-flash-medium`)
- Task ID: `task_956c1c1b77b1` (Luna 리뷰 지적 결함 3건 독립 수정)
- Dispatch ID: `ctx_2b9adeeceb2c`
- 작업자 터미널: `term_3105fe45-46f8-4dce-9763-c24e2e98be09`
- 코디네이터 터미널: `term_54a83fa0-c831-41b9-8295-ca84d361c828`
- 갱신일: 2026-10-10

## 1. 개요 및 구현 범위

Task `task_4d49e747c570`에 대한 Luna 리뷰(`docs/agent-runs/orca-luna/product-review.md`) 및 코디네이터 지침(`msg_f8920b44318f`, `msg_de0869464ada`)에서 독립 재현된 PC 전송 계층 및 수동 갱신 처리 결함을 해결했습니다:
1. **시리얼 출력 큐 드레인 결함**: `WindowsSerialSink.flush`에서 예외 억제 및 타임아웃 시 데몬 스레드를 방치하던 비동기 flush 제거 -> 동기적 바운디드 드레인(synchronous bounded drain) 및 fail-closed 구현.
2. **수동 갱신 유입 시 조기 클리어 및 이전 관측 오라벨링 결함**: 인플라이트 수집/전송 중 수동 이벤트 도착 시 이전 데이터에 잘못 병합(coalesce)하거나 조기 클리어하던 문제 -> 수동 요청을 펜딩 상태로 유지하고, 신규 세션 수집 후 새 순번으로 전송 완결.
3. **E2E 5.0초 데드라인 보장**: 수동 요청 유입 및 포트 가용 시점부터 수집, 직렬화, 전송 및 드레인 완료까지 5.0초 예산 내 완결 보장.

소유 파일인 `pc/`, `tests/pc/`, `docs/agent-runs/orca-flash/checkpoint.md`, `report.md`만 수정하였으며, firmware/designers/동결 57개 입력/타 역할 파일/`tests/integration/`은 일절 변경하지 않았습니다. 개발 및 검증에는 비식별 synthetic 데이터만을 사용하였습니다.

## 2. 세부 결함 분석 및 해결 내용

### 2.1 동기적 바운디드 출력 큐 드레인 (`pc/sender.py`)
- **결함 원인**: 기존 구현은 Windows 상에서 pyserial의 무한 블로킹을 회피하기 위해 백그라운드 스레드를 띄웠으나, 타임아웃 발생 시 데몬 스레드가 백그라운드에 누수되고 성공을 반환하거나 예외를 억제하는 문제가 있었습니다. 또한 `out_waiting` 미지원 시 언바운디드 `serial.flush`로 폴백하여 프로덕션 무한 대기 경로가 노출되었습니다.
- **수정 내용**:
  - 백그라운드 스레드 방식을 완전히 삭제.
  - `WindowsSerialSink`: `write` 시작 시각(`_write_start_time`)부터 `flush` 종료까지의 총 소요 시간을 단일 예산(`write_timeout`, 기본 1.0s~1.5s) 내에서 엄격히 바운딩.
  - `self.serial.out_waiting`을 폴링하여 큐 바이트가 0이 될 때까지 동기적으로 대기하며, 기한 초과 시 `TimeoutError`를 발생시키고 즉시 반환.
  - `out_waiting` 인터페이스 미제공 시 또는 쿼리 도중 OS 예외 발생 시, `serial.flush`로의 임의 폴백을 금지하고 즉시 명시적 `IOError`를 발생시켜 fail-closed 원칙 준수.
  - `CdmSender.transmit_payload`: 쓰기 및 드레인 실패 시 예약된 순번(reserved sequence)을 확실히 소비(consumed)한 상태로 보존하고 `WRITE_IO_ERROR`를 반환.

### 2.2 인플라이트 수동 갱신 펜딩 및 신규 수집 디스패치 (`pc/cli.py`)
- **결함 원인**: 수동 갱신 이벤트가 유입되었을 때, 자동 수집(AUTO)이 진행 중이면 이미 요청 전에 읽힌 구 세션 데이터를 전송하면서도 프레임 라벨을 `MANUAL`로 표기하고 수동 이벤트를 조기 클리어(`clear()`)하여 새 세션 변경사항이 전송되지 않는 레이스 컨디션 발생.
- **수정 내용**:
  - `run_watch_loop`에서 세션 소스 유무(`has_session_source`)를 검사.
  - 세션 소스가 존재하는 경우, 인플라이트 수집 도중 발생한 수동 이벤트를 이전 프레임에 강제로 병합하지 않고 `is_manual`을 거짓으로 유지하여 이전 프레임을 `AUTO`로 정상 전송.
  - `is_manual` 전송 성공 시에만 `manual_trigger_event.clear()`를 수행하므로, 수동 이벤트는 펜딩 상태로 유지됨.
  - 루프 틱에서 펜딩된 수동 이벤트를 감지하여 즉시 다음 반복을 실행, 변경된 세션 파일을 신규 수집하여 새 순번으로 전송 완료 (요청 시점 기준 <= 5.0초 보장).

### 2.3 CLI 시리얼 리소스 안전 클린업 (`pc/cli.py`)
- **수정 내용**:
  - `cmd_send`에서 시리얼 싱크를 `try ... finally: serial_sink.close()` 블록으로 보호하여, 드레인 타임아웃이나 쓰기 I/O 오류 발생 시에도 운영체제 COM 포트 핸들이 즉시 닫히도록 보장.

## 3. 회귀 테스트 및 검증 결과

### 3.1 `tests/pc` 단위 및 회귀 테스트
`python -B -X utf8 -m unittest discover -s tests/pc -p "test_*.py" -v`:
**57개 테스트 전체 통과 (57 tests, OK, 0 failures, 0 errors)**:
- `test_windows_serial_sink_synchronous_bounded_drain_and_error_propagation`: 정상 지연 드레인, 정체 큐 드레인 타임아웃, 큐 쿼리 에러 전파, 스레드 누수 부재(active_count 동일), 닫힌 싱크 쓰기 거부 검증.
- `test_cmd_send_drain_timeout_consumes_reserved_sequence_and_closes_wrapper`: 정체된 큐 타임아웃 시 순번 소비, 시리얼 닫힘, exit code 1 반환 검증.
- `test_watch_manual_arrival_during_inflight_write_dispatches_fresh_collection_frame`: 전송 쓰기 중 수동 이벤트 유입 시 조기 클리어 방지 및 신규 세션 2차 프레임 전송 검증.
- `test_watch_manual_event_during_auto_quota_collection_recollects_changed_session`: AUTO 쿼터 RPC 수집 중 세션 파일 변경 및 수동 요청 유입 시, 이전 프레임(50 토큰)에 병합하지 않고 즉시 2차 MANUAL 프레임(500 토큰)을 5초 이내 디스패치하는지 검증.
- 기존 53개 PC 테스트(토큰 파싱, 에러 격리, 스키마 검증, 상태 락 등) 일체 회귀 없음.

### 3.2 Luna 소유 통합 테스트(`tests/integration/test_pc_producer_to_c.py`) 적응 필요 사항 식별
- 코디네이터 지침("A fake interface may need its real out_waiting/write_timeout property; notify coordinator if a Luna test needs owner adaptation instead of changing it")에 따라 조사한 결과:
  - `tests/integration/test_pc_producer_to_c.py`의 `BlockingSerial` 및 `FakeSerial` 클래스가 실제 하드웨어/pyserial의 `out_waiting` 속성을 정의하지 않음.
  - 프로덕션 `WindowsSerialSink`는 언바운디드 대기를 방지하기 위해 `out_waiting` 부재 시 의도대로 fail-closed(`WRITE_IO_ERROR`) 처리함.
  - `BlockingSerial`에 `@property def out_waiting(self): return 0`을 정의할 경우 `test_watch_manual_event_during_write_collects_new_session_before_clearing`이 즉시 정상 통과(OK)됨을 확인.
  - 해당 파일은 Luna 소유이므로 본 작업자는 직접 수정하지 않고, Luna 소유자 적응 사항으로 코디네이터에 인계함.

## 4. 물리 하드웨어 검증 한계 및 상태
- 실제 COM 포트 열기, 물리 장치 펌웨어 플래시, 하드웨어 리셋은 안전 규칙에 따라 수행하지 않음 (`COM/flash/reset calls prohibited`).
- 물리 하드웨어 및 실계정 검증 증거는 `not_run` 상태이며, 호스트 기반 시뮬레이션 및 실제 프로덕션 C 바이너리(`cdm-host.exe --wire`) 연동 검증만 통과함 (`product_pass=false`).
