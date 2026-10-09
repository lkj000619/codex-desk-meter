# 현재 준비 상태 — 별도 Orca 협업 실험

2026-10-09 18:02 KST 재개. 기존 단독 비교의 최초 블록은 기존 브랜치에서 종료되어 보존된다.
이 문서는 새 브랜치의 협업 확장 실험만 관리한다.

- branch: `lkj000619/experiment-orca-harness-20261008`
- Orca Run: `run_c968c43361da`
- frozen baseline: `272875140d1998d458e26fdb2f6deab5e5d8f7b5`; 입력 57개 보존 완료
- 사용자 확정: 새 구현, 별도 시간 제한 없음, 역할 분담, PC 세션 토큰+개인 quota 수집
- 진행: OpenDesign viewer 준비 완료, AGY Gemini GUI 3개·Codex Sol 6.1 GUI 3개 제출 수락
- 독립 검증: Luna 요구·인터페이스 보고와 최초 GUI 검토 `ctx_35a7c601f1d6`의 제출 `msg_ac9ec8fd93a3` 수락 완료. 여섯 820×320 캡처·비교 화면·상태/BOOT 검토를 보존함. coordinator의 static 검사 재실행 및 57개 동결 hash 검증 통과; B의 발견 결함 보완은 별도 Task
- 자동 승인: 사용자 요청대로 AGY/Codex 전용 PowerShell 터미널의 실제 argv 확인 완료
- 실제 사용자 선택: B · Swiss Studio Meter. 첫 Luna FAIL 근거는 `3929925`에 보존. Gemini 캐시 수정·실제 JS 검사 제출은 `a3aeebb`. [B 재검토](../agent-runs/orca-luna/gui-b-review.md)의 브라우저 PASS·새 PNG를 `aac81f3`에 보존하고 같은 Task 복구 `ctx_9477f122f8d4`의 제출 `msg_1f1335f9e59f`를 수락함. B 설계 gate 통과; 실제 LCD 합격은 별도
- PC 구현: 제출 `msg_9dc702168da7` 수락·release/ack, 코드 `14cc264` 보존. coordinator가 ESP-IDF Python 3.11에서 기존 39개 시험 통과 확인. 추가 실제 PC→C 검사에서 수집 전 sent_at 때문에 새 관측이 거절됨, cold global 오류가 스키마 위반, 3개 provider 파일 실패 시 캐시가 하나만 남는 결함을 재현함. [PC 보완 검토](../design/2026-10-08-pc-review-findings.md)와 [재현 결과](../../experiments/orca-harness-20261008/operator/pc-post-resume-probe.json)를 따라 `task_a6eebb977125` / `ctx_04111d8d4601`에서 수정함
- firmware·통합: Sol 제출 `msg_00816d094c2e` 수락·release/ack, `b6ec3d5`에 보존. 실제 C 렌더러 포함 host 시험 10개 coordinator 재실행 통과, ESP-IDF target/build 로그·15개 staging source·binary hash 일치 확인. 통합 검증 `task_4d49e747c570`의 firmware 부분은 이 동결 제출에서 시작하며 PC 보완과 병행함. 최종 PC→C 통합·검증 제출·COM gate는 최신 PC 보완 수락/시험을 기다림. COM 접근·업로드: 아직 수행하지 않음

[설계](../design/2026-10-08-orca-harness.md) · [계획](../plans/2026-10-08-orca-harness.md)
· [세션 중단 후 재개](orca-harness-resume.md)
