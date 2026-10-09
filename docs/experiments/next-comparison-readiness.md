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
- 2026-10-09 18:30 KST 독립 firmware 결함: Luna `msg_5e1fc2e1c18a`에서 실제 C/framebuffer로 세션 A→B 선택 후 A가 기본 화면에 남음을 재현함. 전역 snapshot ID 제한·현재 source 목록 처리도 보완 범위. `task_e44125e18973` / `ctx_5f9f6d8e9d11`를 Sol에게 맡겨 수정·새 C 시험·build/hash를 진행함. 기존 성공 build는 보존하며 최종 업로드는 수정 제출의 독립 검증 이후
- 2026-10-09 18:41 KST 수정 firmware 제출 `msg_49bca57172a2` 수락·release/ack, `853ddf7` 보존. coordinator가 actual C 시험 18개와 Luna 세션 전환 시험 1개를 재실행해 통과했고, 실제 staging source 15개와 새 app/boot/partition/sdkconfig hash를 확인함. 새 app SHA-256은 `385130667ab15ca8dcc665e70fc06882b1e89535bde8d84af05fdc2b36c1ef72`. Luna에게 수정 제출 검토를 허용함. PC `ctx_04111d8d4601`은 working/live이며 수락된 완료가 없어 최종 통합·COM gate는 계속 대기함
- 2026-10-09 18:54 KST PC 제출 `msg_be047076a883` 수락·`0e39f0d` 보존, coordinator 실제 50개 시험 통과. wire·cache·누락 관측 시각은 보완됐으나 6.5초 manual 지연은 제출에 미포함이다. 같은 AGY terminal을 `task_2425d0e52884` / `ctx_cbb151521cd0`에 즉시 재사용했고 native turnStart observed다. 최종 통합 검증은 이 좁은 5초 deadline 수정의 제출을 기다린다. 업로드·실계정·실물 시험은 계속 `not_run`
- 2026-10-09 19:10 KST PC deadline 제출 `msg_abbf6fa3f33e` 수락·release/ack, commit `5ddef63`, coordinator 53개 시험 통과. 추가 실제 sink/scheduler probe에서 flush 예외의 성공 처리·blocked thread 3개·write 중 수동 요청 유실을 확인함. [PC 보완 검토](../design/2026-10-08-pc-review-findings.md)에 보존했다. PC owner는 idle이며 Luna의 현재 Task에 안정된 최신 PC→C 전체 시험을 허용했다. 알려진 결함을 독립 재현·정리 후 보완/재검증한다. 제품·deadline 합격은 아니며 COM/실계정/실물은 계속 미실행

[설계](../design/2026-10-08-orca-harness.md) · [계획](../plans/2026-10-08-orca-harness.md)
· [세션 중단 후 재개](orca-harness-resume.md)

2026-10-10 00:11 KST 재개: 같은 Run·branch와 입력 57개를 확인했다. 중단된 독립 검증 부분 작업은 `0f552c9`에 보존했다. 같은 review Task의 현재 Dispatch는 `ctx_125c9c02c0ed`이며 PC `5ddef63`·firmware `853ddf7`의 전체 검증을 이어간다. 기본 Codex launcher 인수 오류는 종료 확인·정리 후 모델/자동 승인 확인된 별도 터미널로 복구했다. 세 PC 결함의 독립 보고·보완·재검증 이전에는 제품 합격과 업로드를 선언하지 않는다.

2026-10-10 00:29 KST: Luna의 실패 제출 `msg_e69a6fb2be99` 수락·release/ack, `117a988` 보존. coordinator도 통합 22개 중 동일한 3개 실패를 확인했다. 제한 시간 내 큐 전송 완료 또는 명확한 전송 실패 처리와 전송 중 수동 요청의 새 데이터 수집을 `task_956c1c1b77b1` / `ctx_2b9adeeceb2c`의 Flash에게 맡겼다. 새 native turnStart observed이며 코드 수정 중이다. 보완 수락 후 같은 Luna Task로 재검증하고 업로드 gate를 판단한다. COM3 열거 외 실제 장치/계정 접근은 없었다.
