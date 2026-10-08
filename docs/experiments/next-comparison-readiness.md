# 현재 준비 상태 — 별도 Orca 협업 실험

2026-10-08 KST. 기존 단독 비교의 최초 블록은 기존 브랜치에서 종료되어 보존된다.
이 문서는 새 브랜치의 협업 확장 실험만 관리한다.

- branch: `lkj000619/experiment-orca-harness-20261008`
- Orca Run: `run_c968c43361da`
- frozen baseline: `272875140d1998d458e26fdb2f6deab5e5d8f7b5`; 입력 57개 보존 완료
- 사용자 확정: 새 구현, 별도 시간 제한 없음, 역할 분담, PC 세션 토큰+개인 quota 수집
- 진행: OpenDesign viewer 준비 완료, AGY Gemini GUI 3개·Codex Sol 6.1 GUI 3개 제출 수락
- 독립 검증: Luna 요구·인터페이스 보고와 최초 GUI 검토 `ctx_35a7c601f1d6`의 제출 `msg_ac9ec8fd93a3` 수락 완료. 여섯 820×320 캡처·비교 화면·상태/BOOT 검토를 보존함. coordinator의 static 검사 재실행 및 57개 동결 hash 검증 통과; B의 발견 결함 보완은 별도 Task
- 자동 승인: 사용자 요청대로 AGY/Codex 전용 PowerShell 터미널의 실제 argv 확인 완료
- 실제 사용자 선택: B · Swiss Studio Meter. 최초 검토 `bc27607` 보존 후 Gemini 보완 제출 `msg_dfc7bc18e0f1` 수락. 현재 Luna `task_0d62e820abfa` / `ctx_c9524d9d2327`에서 실제 동작 재검증; 문자열 검사·별도 모형 계산만으로 합격하지 않음
- PC 구현: 최초 AGY 초안 제출·13개 시험 재실행 통과 후 [결함 재현](../design/2026-10-08-pc-review-findings.md). native metadata·원본 시각·quota map·실행 중 state 유실·실제 전송/수동 갱신 누락을 `task_3963de21ddd1` / `ctx_221ff3735dae`에서 보완 중. 원본 초안과 B 보완 제출은 `86286c5`에 보존
- firmware·통합: `task_b1214421a314` 생성; native ready가 돼도 B 독립 재검증 수락 전에는 시작하지 않음. COM 접근·업로드: 아직 수행하지 않음

[설계](../design/2026-10-08-orca-harness.md) · [계획](../plans/2026-10-08-orca-harness.md)
· [세션 중단 후 재개](orca-harness-resume.md)
