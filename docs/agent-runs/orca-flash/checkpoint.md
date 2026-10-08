# Checkpoint: Final PC Runtime Gaps Remediation (orca-flash)

- 일시: 2026-10-08T23:40:45+09:00
- Task ID: `task_2b005e480abd`
- Dispatch ID: `ctx_4308689007a9`
- 터미널: `term_d3b622cf-1791-4afc-a013-2cf7482bb57d`
- 담당 역할: PC 수집·전송 (`pc/`, `tests/pc/`, `docs/agent-runs/orca-flash/`)
- 현재 상태: 코디네이터 검토 결과 A, B, C, D 4대 런타임 갭 구현 및 32개 테스트 전체 통과 (OK). 최종 보고서 작성 준비.

## 주요 구현 및 검증 결과
1. **A. Watch 스케줄러 & 수동 입력 & 재연결 복구**:
   - `run_watch_loop` 및 `cmd_watch`: 자동 주기(<=60s)와 독립적으로 stdin Enter 또는 이벤트에 의한 즉시(<=5s) 수집/전송 구현.
   - 포트 연결 복구 시 재연결 1/s 이내 제한 및 가용 시 <=5s 이내 전송.
   - `--port` 또는 명시적 `--dry-run` 미지정 시 암묵적 루프백 거부.
   - 테스트: `test_watch_manual_trigger_immediate_dispatch`, `test_refuse_implicit_loopback_when_port_missing`.
2. **B. Bounded JSON-RPC Reader**:
   - `BoundedProcessReader`: 스레드 및 큐 기반 논블로킹 reader로 엄격한 타임아웃 구현.
   - stderr 백그라운드 드레인 및 자식 프로세스 terminate/kill/wait 정리 보장.
   - `observed_at`은 요청 시작 시각이 아닌 응답 성공 획득 시각으로 설정.
   - 테스트: `test_hung_stream_times_out_and_cleans_up_process`.
3. **C. SharedCollectionState & Fixture Provenance**:
   - `SharedCollectionState`: provider/source별 격리, last-good 보존, 에러 전이 시 이전 정상 값/시각 유지, 복구 검증.
   - 0s, 299s(정상) / 300s(stale) 경계 검증.
   - `experiments/fixtures/providers` 및 `personal-usage.json` 지원, fixture provenance 명시.
   - 글로벌 리셋 필수 키 검증 및 보존.
   - 테스트: `test_source_isolation_and_last_good_retention`, `test_stale_detection_0_299_300`.
4. **D. StateStore 초기화 확인 및 msvcrt OS 락**:
   - `initialize_new`가 기존 상태 존재 시 암묵적 덮어쓰기 거부(`STATE_ALREADY_EXISTS`), `confirmed_overwrite=True` 명시적 요구.
   - `DeviceLock`: Windows `msvcrt.locking` 기반 OS 프로세스 종료 시 자동 해제 락 구현.
   - 서브프로세스 강제 종료(crash) 후 즉시 락 재획득 가능 검증.
   - 테스트: `test_initialize_new_refuses_silent_overwrite`, `test_os_lock_released_on_subprocess_crash`.

## 테스트 결과 요약
- `python -m unittest discover -s tests/pc -p "test_*.py" -v`: **32 tests in 1.430s -> ALL OK**.

## 다음 행동
- `docs/agent-runs/orca-flash/report.md` 최종 갱신
- 최종 inbox 확인 후 `worker_done` 발행
