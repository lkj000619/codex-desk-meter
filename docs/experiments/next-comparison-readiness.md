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
- 실제 사용자 선택: B · Swiss Studio Meter. 첫 Luna 재검증 `ctx_c9524d9d2327`는 FAIL: Unknown/Waiting 이후 Error/Disconnected에서 이전 정상값이 유실됨. [B 원본 판정](../agent-runs/orca-luna/gui-b-review.md)과 브라우저 근거는 `3929925`에 보존. Gemini가 `task_57d8de5426b5` / `ctx_fa13d9a20591`에서 실제 JS 회귀 검사와 캐시를 수정 중. 수정 후 같은 검증 Task를 retry-of로 재개하며, 문자열·별도 모형만으로 합격하지 않음
- PC 구현: native metadata·원본 시각·quota map·state 유실 첫 수정 후 watch/RPC/cache/OS lock 구현이 제출됨 (`ctx_4308689007a9`, `7264e76`). coordinator의 32개 재실행에서 Windows crash 시험 1개 실패; cached error stale=false 및 wire 경로 노출 재현. [PC 보완 검토](../design/2026-10-08-pc-review-findings.md)를 근거로 source별 상태·privacy·초기화·실제 crash 시험을 `task_c6f6d8f00810`에서 수정. 제출 완료와 제품 합격을 구분함
- firmware·통합: 2026-10-09 00:02 KST에 core와 최종 GUI 통합 gate를 분리함. `task_b1214421a314`에서 B 캐시 수정과 독립적인 BSP·C 수신기부터 병행 구현하며 B 독립 PASS 전에는 GUI 최종 통합·제출하지 않음. 통합 검증 `task_4d49e747c570`는 native blocked이고 최신 PC 보완 검증과 실제 firmware build 이후 시작함. 기존 native deps는 최신 후속 PC Task를 포함하지 않으므로 coordinator gate도 확인해야 함. COM 접근·업로드: 아직 수행하지 않음

[설계](../design/2026-10-08-orca-harness.md) · [계획](../plans/2026-10-08-orca-harness.md)
· [세션 중단 후 재개](orca-harness-resume.md)
