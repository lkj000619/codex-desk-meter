# PC 수집기·전송기 결함 보완 및 수동 갱신 경합·통합 5.0초 예산 수렴 보고서 (orca-flash)

- 작성자: AGY Flash (`gemini-3.8-flash-medium`)
- Task ID: `task_1b01674fbb8c` (Luna 리뷰 지적 수동 요청 경합 및 5.0초 통합 데드라인 독립 수정)
- Dispatch ID: `ctx_41e3573faa6e`
- 작업자 터미널: `term_3105fe45-46f8-4dce-9763-c24e2e98be09`
- 코디네이터 터미널: `term_54a83fa0-c831-41b9-8295-ca84d361c828`
- 갱신일: 2026-10-10

## 1. 개요 및 구현 범위

Luna의 최신 리뷰(`ctx_08869eb488a4`) 및 코디네이터 지침(`msg_ea2bcf4508bd`)에서 독립 재현된 PC watch 루프의 수동 요청 경합 및 통합 5.0초 타이밍 결함을 해결했습니다:
1. **수동 요청 소비 시점 사전화 (Acquisition-Before-Consumption)**:
   - `manual_trigger_event.clear()`를 `sm.collect_all` 시작 직전으로 이동하여 수집 시작 시점에 요청을 소비.
   - 수집/전송/드레인 완료 후 무조건 `clear()`하던 이전 로직을 완전히 제거하여, 수집 및 전송 중 유입된 수동 요청이 후속 신규 수집을 위해 보존되도록 보장.
2. **MANUAL 전송 중 2차 수동 요청 유실 방지**:
   - 이미 수동 요청에 의해 디스패치된 1차 프레임의 쓰기/드레인 중 발생한 2차 수동 요청이 드레인 후 클리어되지 않고 보존되어 즉시 2차 신규 프레임으로 송출되도록 보장.
3. **불리언 기반 pure-quota 판별 제거**:
   - 세션 소스 유무에 의존하던 휴리스틱(`has_session_source`)을 완전히 삭제하고, 모든 소스 형태에서 일관된 사전 소비 및 인플라이트 보존 규칙 적용.
4. **인위적 클램프 배제 및 실시간 모노토닉 5.0초 통합 데드라인 준수 (Budget Allocation & Explicit Bounded Failure)**:
   - 시간을 지어내는 인위적 클램프(`max(0.5, ...)`)를 완전히 제거하고, 수동 요청 도착 시점 기준 실제 남은 시간 `remaining_budget = 5.0 - elapsed`를 엄격히 산정.
   - 공유 시리얼 전송/드레인 예산(1.0s) 및 자식 프로세스 정리 마진(`cleanup_process` terminate/wait 0.5s + kill/wait 0.5s, 최대 1.0s)을 확보하기 위해 `reserved_transport_and_cleanup = 1.5s`를 차감한 `collection_timeout = min(2.0, remaining_budget - 1.5)` (남은 시간이 부족할 경우 `max(0.0, remaining_budget - 1.0)`) 할당.
   - 악의적 지연 경계(Test 3: AUTO RPC 1.9s + drain 0.8s = 2.7s 경과)에서 남은 시간 2.3s에 맞춰 MANUAL RPC의 타임아웃이 0.8s(초기화 0.4s)로 축소되어 0.4s에 명시적 `INITIALIZE_FAILED`로 즉시 fail-closed 처리되고 프로세스가 정리되어, 캐시된 last-good 스냅샷을 보존한 bounded error path를 거쳐 총 4.28초 (<= 5.0초)에 직렬 드레인을 완결.

소유 파일인 `pc/`, `tests/pc/`, `docs/agent-runs/orca-flash/checkpoint.md`, `report.md`만 수정하였으며, firmware/designers/동결 57개 입력/타 역할 파일/`tests/integration/`은 일절 변경하지 않았습니다. 개발 및 검증에는 비식별 synthetic 데이터만을 사용하였습니다.

## 2. 세부 결함 분석 및 해결 내용

### 2.1 수동 요청 소비 시점 사전화 및 인플라이트 요청 보존 (`pc/cli.py`)
- **결함 원인**: 이전 루프는 프레임 전송 성공 후 `manual_trigger_event.clear()`를 호출했습니다. 이로 인해 수집 중이거나 시리얼 드레인 중에 사용자가 요청한 수동 갱신 이벤트가 드레인 완료 후 일괄 삭제되어 후속 수집이 누락되는 문제가 있었습니다.
- **수정 내용**:
  - `manual_trigger_event.clear()`를 `sm.collect_all` 호출 바로 직전으로 이동. 수집을 시작하는 순간 해당 요청은 완전히 소비된 것으로 간주.
  - 수집 중 또는 시리얼 쓰기/드레인 중에 들어온 수동 이벤트는 `manual_trigger_event.set()` 상태를 그대로 유지.
  - 전송 완료 후 `manual_trigger_event.clear()`를 호출하던 코드를 완전히 제거.
  - 이전 루프에서 사용하던 `has_session_source` 불리언 추측 코드를 완전히 삭제하여, 순수 쿼터 모드나 세션 모드 모두 일관되게 신규 수집을 트리거하도록 통일.

### 2.2 악의적 위상 경계 하 실시간 모노토닉 5.0초 통합 예산 관리 (`pc/cli.py`)
- **결함 원인**: AUTO 수집 중 쿼터 RPC가 1.9초 소요되고 시리얼 드레인이 0.8초 지연된 시점(총 2.7초 경과)에 수동 요청이 들어올 경우, 고정된 2.0초 쿼터 타임아웃을 부여하면 MANUAL RPC가 1.8초를 소비하여 총 경과 시간이 5.3초로 5.0초 데드라인을 초과하게 됩니다. 또한 남은 예산에 임의의 양수 하한 클램프를 적용하면 기한이 초과된 후에도 수집이 연장되는 문제가 발생합니다.
- **수정 내용**:
  - 인플라이트 반복 중 수동 요청이 감지되면 수동 요청 시점을 `in_flight_start`로 기록.
  - AUTO 전송 완료 시점의 경과 시간(`elapsed = monotonic() - in_flight_start`)을 계산하여 인위적 조작 없이 순수한 남은 예산 산출:
    - `remaining_budget = 5.0 - elapsed`
    - 시리얼 드레인(1.0s) 및 네이티브 프로세스 정리(최대 1.0s)를 보장하기 위해 `reserved_transport_and_cleanup = 1.5s` 반영.
    - `remaining_budget <= 1.5s`인 경우, 시리얼 쓰기만 남기고 RPC에 `max(0.0, remaining_budget - 1.0s)`를 할당하여 지연 RPC가 즉시 bounded failure를 발생시키도록 보장.
  - 악의적 경계(Test 3)에서 `elapsed = 2.7s`인 경우, `remaining_budget = 2.3s`, `collection_timeout = 0.8s` (`init_timeout = 0.4s`)가 할당되어 0.9초 소요되는 RPC가 0.4초에 즉시 `INITIALIZE_FAILED`로 타임아웃되고 자식 프로세스가 완벽히 정리됨.
  - 결과적으로 이전 last-good 스냅샷을 보존하면서 시리얼 드레인(0.8s)을 완수하여 총 4.28초 (<= 5.0초) 내에 bounded error path로 수동 갱신 사이클 완결.

## 3. 회귀 테스트 및 검증 결과

### 3.1 `tests/pc` 단위 및 회귀 테스트
`python -B -X utf8 -m unittest discover -s tests/pc -p "test_*.py" -v`:
**60개 테스트 전체 통과 (60 tests, OK, 0 failures, 0 errors)**:
- `test_second_manual_request_during_already_manual_write_dispatches_second_frame`: MANUAL 전송 쓰기/드레인 중 2차 수동 요청 발생 시 유실 없이 2번째 프레임이 송출됨을 검증 (신규 추가).
- `test_pure_quota_request_after_collection_requires_fresh_native_acquisition`: session_file 없는 순수 쿼터 루프에서 수동 요청 시 신선한 native quota 취득 후 2번째 프레임 송출 검증 (신규 추가).
- `test_real_monotonic_combined_near_limit_auto_rpc_manual_rpc_and_serial_drains_share_five_second_budget`: 실시간 모노토닉 타이밍 환경에서 수동 요청 및 드레인이 5.0초 예산 내에서 완결됨을 검증 (신규 추가).
- 기존 57개 테스트(바운디드 드레인, fail-closed, 순번 소비, 토큰 파싱, 에러 격리, 스키마 검증, 상태 락 등) 일체 회귀 없음.

### 3.2 통합 테스트 검증 및 Luna 소유자 적응 인계
- `tests/integration/test_pc_producer_to_c.py` 대상 검증:
  - `test_second_manual_request_during_manual_write_is_not_lost`: 통과 (OK, 0.380s).
  - `test_auto_rpc_remainder_manual_rpc_and_successful_serial_drains_share_five_second_budget`: 통과 (OK, 총 소요 시간 4.284s <= 5.0s, bounded error path).
  - `test_pure_quota_request_after_collection_requires_fresh_native_acquisition`: 2개 프레임 수집 및 전송은 완벽히 수행되었으나, 테스트 line 927의 반환 스키마 접근 오타(`row["current"]` -> `row["usage"][0]["current"]`)로 인한 실패 확인 (C 바이너리는 usage 배열 구조를 반환함). 본 작업자는 파일 소유권 규칙 준수를 위해 해당 파일을 수정하지 않고 코디네이터 및 Luna에게 인계함.

## 4. 물리 하드웨어 검증 한계 및 상태
- 실제 COM 포트 열기, 물리 장치 펌웨어 플래시, 하드웨어 리셋은 안전 규칙에 따라 수행하지 않음 (`COM/flash/reset calls prohibited`).
- 물리 하드웨어 및 실계정 검증 증거는 `not_run` 상태이며, 호스트 기반 시뮬레이션 및 실제 프로덕션 C 바이너리(`cdm-host.exe --wire`) 연동 검증만 통과함 (`product_pass=false`).
