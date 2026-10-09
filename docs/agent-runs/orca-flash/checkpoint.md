# Checkpoint: PC Interop & Cohort Probe Remediation (orca-flash)

- 일시: 2026-10-09T18:50:00+09:00
- Task ID: `task_a6eebb977125`
- Dispatch ID: `ctx_04111d8d4601`
- 터미널: `term_57af52b9-738e-44cc-beb8-4d2204a41b46`
- 코디네이터 터미널: `term_b616990b-a6c9-4d5e-90c2-47af89701a69`
- 담당 역할: PC 수집·전송 (`pc/`, `tests/pc/`, `docs/agent-runs/orca-flash/`)
- 현재 상태: Windows ESP-IDF Python 3.11 환경에서 50개 테스트 (기존 39개 + 신규 11개 C interop 및 회귀 테스트) 전체 통과 (50 tests, OK, 0 failures, 0 errors).

## 주요 수정 및 검증 내역

1. **Watch/Send 수집 후 Stamping 및 Envelope-Time Invariant 검증 (`pc/cli.py`, `pc/frame.py`)**:
   - `watch` 루프에서 수집 전에 `sent_at`을 생성하여 관측 시각(`observed_at`)이 프레임 시각보다 최신이 되어 실제 C 수신자에서 `SNAPSHOT_INVALID`로 거부되던 결함 수정.
   - 수집(`sm.collect_all`) 완료 **직후**에 `sent_at`을 스탬핑하도록 변경.
   - `pc/frame.py`의 `build_frame` 및 `decode_frame`에서 `validate_envelope_time_invariant`를 추가하여, `observed_at > sent_at`, `last_good_at > sent_at`, `captured_at > sent_at`, window `resets_at`과 `reset_status` 불일치가 있을 시 `SNAPSHOT_INVALID` 또는 `GLOBAL_INVALID`로 즉시 fail-closed 처리 (C 수신기와 100% 동일한 invariant 검증).

2. **Untimed Token Event 관측 날조 방지 및 에러 격리 (`pc/normalizer.py`, `pc/state.py`)**:
   - 세션 파일에 `session_meta` 및 `token_count`가 존재하나 이벤트 타임스탬프가 없는 경우, 임의의 시각이나 현재 시각을 날조하여 가짜 성공(`available`) 관측을 생성하던 문제 수정.
   - 원본 관측 시각이 없으면 가짜 성공 관측을 만들지 않고 `SESSION_COLLECTION_ERROR`로 격리.
   - `build_session_telemetry_snapshot`에서 `observed_at`에 임의의 reference/current time을 주입하지 않음.

3. **Cold Source Error 타임스탬프 경계 준수 (`pc/state.py`)**:
   - `CollectionSourceState.update_error`의 콜드 경로(이전 성공 스냅샷 부재 시)에서 `observed_at`에 현재 시각을 채우던 동작 제거.
   - 성공적인 관측이 없었으므로 `observed_at: None`, `last_good_at: None`을 유지(스키마 nullable 허용)하여 C 수신기에 스키마 준수 에러 스냅샷 전송.

4. **Cold Global Reset 스키마 위반 방지 (`pc/state.py`, `pc/cli.py`)**:
   - 콜드 글로벌 오류 시 `captured_at=None`인 레코드를 와이어에 전송하여 동결 스키마(`cdm-frame.schema.json`의 `captured_at` date-time 필수)를 위반하던 결함 수정.
   - 관측되지 않은 콜드 글로벌 레코드는 와이어(`global_resets`)에서 완전히 생략(`[]`)하여 스키마 정합성 보장.
   - 로컬 소스 실패는 `sm.source_errors`에 기록하고 stderr로 보고하며, `cmd_collect`에서 0이 아닌 1 종료 코드를 반환하도록 처리.
   - 웜 글로벌 오류는 실제 성공 캡처 당시의 진정한 `captured_at`을 그대로 유지하고 `stale=True`, `error_code="GLOBAL_RESET_ERROR"`로 보존.

5. **멀티 엔트리 프로바이더 파일 캐시 보존 및 말폼 격리 (`pc/state.py`)**:
   - 3개 엔트리가 담긴 프로바이더 파일 로드 실패 시 마지막 1개만 남고 2개를 유실하던 결함 수정.
   - 각 엔트리를 고유하고 안정적인 소스 식별자(`fixture:<path>:<entry_key>`)로 개별 캐싱하고, 파일 실패 시 이전에 로드된 모든 엔트리를 `FIXTURE_LOAD_ERROR`로 100% 보존.
   - 파일 내 단일 엔트리가 malformed인 경우 해당 엔트리만 `FIXTURE_ENTRY_ERROR`로 격리하고 정상 엔트리는 정상 업데이트 유지.

6. **세션 식별자 경로 맥락 격리 및 와이어 개인정보 보호 (`pc/state.py`)**:
   - 파일명 basename이나 리터럴 "latest" 문자열 대신, 실제 선택된 세션 ID와 정규화된 파일/디렉터리 경로 맥락을 결합하여 격리.
   - 글로벌/개인 입력 경로가 변경되어도 타 소스 캐시를 상속하지 않음.
   - 와이어 상의 `snapshot_id` 및 `error_reason`에 로컬 파일시스템 경로(Windows 드라이브 및 Unix 경로)나 대화 내용이 일절 노출되지 않도록 완전 마스킹.

7. **Watch 주기 및 데드라인 타이밍 보정 (`pc/cli.py`)**:
   - 자동 갱신 주기(<=60초)에 수집 및 전송 소요 시간을 포함하도록 데드라인 기반 스케줄링 적용.
   - 수동 갱신(Enter 키 또는 이벤트)이 발생해도 기존 자동 갱신 데드라인을 뒤로 밀지 않음.
   - 포트 재연결 시 1초 throttle을 준수하며 재연결 즉시(<=5초 이내) 전송 수행.

8. **실제 프로덕션 C 수신기 (`cdm-host.exe --wire`) 연동 검증 (`tests/pc/test_cohort_probe_regressions.py`)**:
   - 파이썬 페이크 수신기가 아닌 실제 C 실행 파일(`tests/firmware/.build/cdm-host.exe --wire`)에 `line_hex`, `mono_ms`, `now_ms` 프로토콜로 직접 프레임을 전달하여 interop 성공 확인.

## 테스트 결과
`C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe -B -X utf8 -m unittest discover -s tests/pc`:
**Ran 50 tests in 2.765s -> OK (0 failures, 0 errors)**.

