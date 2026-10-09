# Checkpoint: Final PC Runtime Gaps Remediation (orca-flash)

- 일시: 2026-10-09T00:24:00+09:00
- Task ID: `task_c6f6d8f00810`
- Dispatch ID: `ctx_b3dca8602ce8`
- 터미널: `term_39c072ad-cf9b-4974-84a0-baa02d99974f`
- 코디네이터 터미널: `term_ce8a35be-a6e6-4508-aba9-5c5400b95a21`
- 담당 역할: PC 수집·전송 (`pc/`, `tests/pc/`, `docs/agent-runs/orca-flash/`)
- 현재 상태: Windows ESP-IDF Python 3.11 환경에서 39개 단위/통합 테스트 전체 통과 (39 tests in 1.6s, OK).

## 주요 수정 및 검증 내역
1. **Windows launcher vs 자식 프로세스 OS Lock 해제**:
   - `test_os_lock_released_on_subprocess_crash`에서 venv의 `python.exe` 런처와 실제 핸들을 보유한 자식 프로세스 트리를 `taskkill /F /T /PID`로 강제 종료하고 stdout을 명시적으로 닫아 OS 락 즉시 재획득 검증 완료.
2. **타임스탬프 보존 및 에이징/Stale 판정**:
   - `compute_stale` 및 에러 스냅샷에서 `reference_time` 생략 시 현재 UTC를 비교 기준으로만 사용하고 스냅샷의 원본 `observed_at` 및 `captured_at` 타임스탬프를 덮어쓰지 않음.
   - 300초 이상 경과 시 stale=true 전이, 콜드 에러 시 임의의 성공 캡처 시각을 조작하지 않고 `None` 처리.
3. **개인정보 보호 및 에러 경로 일관성**:
   - 콜드 에러 와이어 페이로드 및 `error_reason`에서 로컬 파일시스템 경로(Windows 드라이브 및 Unix 경로)를 제거(`<local_path>`)하여 개인정보 비노출 보장.
   - 세션 콜드 에러의 `metric_kind`를 `session_telemetry`로 유지하고 `unit="token"` 보존.
   - 누락되거나 잘못된 `personal-usage` 및 `global-reset` 파일은 침묵 생략되지 않고 last-good/error 경로로 라우팅.
4. **선택 세션 격리 및 멀티 프로바이더 캐시**:
   - 세션 A 선택 후 존재하지 않는 세션 B로 변경 시, 세션 A의 값이 세션 B로 오염되지 않도록 타깃 키별 격리.
   - 멀티 프로바이더 픽스처 캐시를 전체 경로 기준으로 독립 유지.
5. **선택적 토큰 카운트 null 보존**:
   - `cached_input`, `reasoning_output`, `source_total`이 원본 이벤트에 없을 때 0으로 왜곡하지 않고 `None`(JSON null)으로 보존.
   - 정규화 합계 `normalized_total = input + output`은 독립적으로 유지.
6. **디바이스 초기화 가드 및 락 해제**:
   - `init-device` CLI에 `--confirmed-empty-receiver` 또는 `--force-overwrite` 명시적 플래그 요구.
   - 디바이스 별칭(alias) 경로 순회 차단(`_validate_safe_alias`) 및 `updated_at` 유효성(NaN/음수/무한대 거부) 검증.
   - `CdmSender` 초기화 중 `StateStore.load` 실패 시 획득했던 디바이스 락 즉시 해제.

## 테스트 결과
`C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe -B -X utf8 -m unittest discover -s tests/pc`:
**Ran 39 tests -> OK (0 failures, 0 errors)**.
