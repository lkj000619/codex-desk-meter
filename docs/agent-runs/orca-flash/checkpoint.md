# Checkpoint: PC Manual Deadline & Production Watch Budget (orca-flash)

- 일시: 2026-10-09T19:02:00+09:00
- Task ID: `task_2425d0e52884`
- Dispatch ID: `ctx_cbb151521cd0`
- 터미널: `term_57af52b9-738e-44cc-beb8-4d2204a41b46`
- 코디네이터 터미널: `term_b616990b-a6c9-4d5e-90c2-47af89701a69`
- 담당 역할: PC 수집·전송 (`pc/`, `tests/pc/`, `docs/agent-runs/orca-flash/`)
- 현재 상태: 코디네이터 재현 `operator/pc-manual-deadline-probe.json` 및 진행 중인 자동 수집 중 수동 요청 유입(`msg_7f22c0c2a3d8`) 해결 완료. 수동/포트복구 시 수집+전송 5초 예산(RPC 타임아웃 2.5s, 시리얼 타임아웃 1.5s 분할) 적용 및 in-flight 자동 수집 중 수동 이벤트 병합(coalesce) 적용. Windows ESP-IDF Python 3.11 환경에서 53개 테스트 전체 통과 (53 tests, OK, 0 failures, 0 errors).
- 측정 타이밍:
  - 수동 갱신 시 느린 소스(4.5s) + 느린 write(1.0s) 환경에서도 수집 2.5s 예산 cap 적용으로 총 소요 시간 3.5s <= 5.0s 완결 (`test_watch_manual_deadline_bounded_under_slow_source_and_write`).
  - 포트 가용 시 신규 순번 전송 완료 시간 <= 5.0s 완결 (`test_port_reopened_deadline_bounded_under_slow_source`).
  - 진행 중인 자동 수집 도중 수동 요청 유입 시, 직후 완료되는 신규 관측 프레임에 수동 플래그를 병합하여 요청 시점부터 프레임 전송 완료까지 1.8s <= 5.0s 완결 (`test_watch_manual_arrival_during_in_flight_automatic_collection`).
  - 자동 주기(<=60s)는 작업 소요 시간을 포함하며, 수동 갱신에 의해 데드라인이 연기되지 않음 (`test_watch_auto_period_includes_slow_collection_duration`, `test_watch_manual_trigger_does_not_move_automatic_deadline`).

## 주요 수정 및 검증 내역

1. **수동/포트 복구 5초 데드라인 예산 분할 및 in-flight 수동 요청 병합 (`pc/cli.py`, `pc/state.py`, `pc/quota.py`, `pc/sender.py`)**:
   - `operator/pc-manual-deadline-probe.json`에서 지적된 4.5s 수집 + 2.0s 전송 = 6.5s (> 5s) 결함을 수정하기 위해, 수동 및 포트 복구 갱신 시 `quota_timeout=2.5s`로 수집 예산을 할당하고, 시리얼 I/O timeout을 `1.5s`로 기본 설정하여 총 E2E 소요 시간이 5.0s를 절대 초과하지 않도록 보장.
   - 자동 수집/전송이 진행 중인 도중 수동 이벤트가 발생한 경우, 직후 수집 완료된 신규 관측 프레임에 수동 플래그를 병합(coalesce)하여 불필요한 연속 지연 수집 없이 요청 시점 기준 5초 이내 신규 순번 전송 완결.
   - 느린 소스나 RPC 타임아웃 시 기존 last-good 스냅샷을 `stale=True, status="error"`로 안전하게 보존하며 정상 소스 격리 유지.

2. **Watch/Send 수집 후 Stamping 및 Envelope-Time Invariant 검증 (`pc/cli.py`, `pc/frame.py`)**:
   - 수집(`sm.collect_all`) 완료 직후에 `sent_at`을 스탬핑하도록 보장.
   - `pc/frame.py`의 `build_frame` 및 `decode_frame`에서 `validate_envelope_time_invariant`를 검증하여 `SNAPSHOT_INVALID` 결함 방지.

3. **Untimed Token Event 관측 날조 방지 및 에러 격리 (`pc/normalizer.py`, `pc/state.py`)**:
   - 원본 관측 시각 부재 시 임의의 시각을 날조하지 않고 `SESSION_COLLECTION_ERROR`로 격리.

4. **Cold Source Error 타임스탬프 경계 준수 (`pc/state.py`)**:
   - 성공적인 관측이 없었던 콜드 에러 시 `observed_at: null`, `last_good_at: null`을 유지.

5. **Cold Global Reset 스키마 위반 방지 (`pc/state.py`, `pc/cli.py`)**:
   - 콜드 글로벌 오류는 와이어에서 생략(`[]`)하여 동결 스키마 위반을 방지하고 로컬 수집 실패로 기록.

6. **멀티 엔트리 프로바이더 파일 캐시 보존 및 말폼 격리 (`pc/state.py`)**:
   - 3개 엔트리가 담긴 프로바이더 파일 로드 실패 시에도 모든 엔트리를 100% 보존.

7. **세션 식별자 경로 맥락 격리 및 와이어 개인정보 보호 (`pc/state.py`)**:
   - 실제 세션 ID와 경로 맥락 결합으로 캐시 오염을 방지하고 와이어 상 경로 완전 마스킹.

8. **실제 프로덕션 C 수신기 (`cdm-host.exe --wire`) 연동 검증 (`tests/pc/test_cohort_probe_regressions.py`)**:
   - 실제 C 실행 파일(`tests/firmware/.build/cdm-host.exe --wire`)에 직렬화된 프레임을 전달하여 interop 검증.

## 테스트 결과
`C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe -B -X utf8 -m unittest discover -s tests/pc`:
**Ran 53 tests in 3.051s -> OK (0 failures, 0 errors)**.

