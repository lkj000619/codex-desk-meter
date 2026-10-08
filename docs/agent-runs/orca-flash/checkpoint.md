# Checkpoint: Remediation of PC Implementation (orca-flash)

- 일시: 2026-10-08T23:24:45+09:00
- Task ID: `task_3963de21ddd1`
- Dispatch ID: `ctx_221ff3735dae`
- 터미널: `term_d3b622cf-1791-4afc-a013-2cf7482bb57d`
- 담당 역할: PC 수집·전송 (`pc/`, `tests/pc/`, `docs/agent-runs/orca-flash/`)
- 현재 상태: 6대 지적 사항 수정 및 25개 테스트 전체 통과 완료. 보고서 갱신 준비.

## 수정 및 검증 내역
1. **pc/session.py**:
   - Codex 0.159의 중첩 구조(`event_msg -> payload.type == "token_count" -> payload.info.total_token_usage`) 및 `session_meta -> payload.id` 완전 지원.
   - `observed_at`은 수락된 토큰 이벤트 시각만 기록(이후 무관 이벤트로 갱신 금지).
   - `cached <= input`, `reasoning <= output`, 음수 토큰 거부 불변식 적용.
   - 날짜 폴더 재귀 스캔 지원 및 명시적 세션 선택(`--session-id` 또는 `--latest`) 강제.
2. **pc/quota.py**:
   - `initialize` 후 `initialized` notification 전송 프로토콜 핸드셰이크 구현.
   - `rateLimits`와 `rateLimitsByLimitId` 둘 다 파싱하여 창 누락 방지.
   - 프로세스 타임아웃 및 kill/wait 정리 보장.
3. **pc/sender.py**:
   - 실행 중 상태 파일 유실/변조 시 fail-closed 정지(캐시로 재생성하지 않음).
   - 단일 센더 락(`DeviceLock`) 적용으로 동시 실행 차단.
   - 순번 7 -> 재시작 -> 8 영속화 검증.
   - Windows 115200/8N1 `WindowsSerialSink` 구현 및 "HOST WRITE" 표기 준수.
4. **pc/frame.py & pc/normalizer.py**:
   - 정수형 토큰 보존 (float 변환 방지).
   - 미래 타임스탬프 vs reference time 검증, percent 합계 100 검증.
   - 글로벌 리셋 필수 키 검증 및 불변성 유지.
5. **테스트 결과**:
   - `python -m unittest discover -s tests/pc -p "test_*.py" -v`: 25개 테스트 전원 통과 (OK).

## 다음 행동
- `docs/agent-runs/orca-flash/report.md`에 날짜가 기재된 Remediation 섹션 추가.
- 최종 inbox 확인 및 `worker_done` 전송.
