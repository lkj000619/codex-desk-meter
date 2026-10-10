# 현재 준비 상태 — 별도 Orca 협업 실험

**2026-10-10 17:12 KST 현재:** **Task26개 모두 완료, 숫자 잘림·점멸 보완의 기본 실물 관측 완료**. Luna 최종 제출 `msg_79be3c78e790` 수락·release/ack, coordinator pixel2/2 PASS, 후보 `orca-harness-20261010-numeric-candidate` (`16b7d66`) 동결. 17:03 COM3 업로드·세 이미지 쓰기 hash, 17:04 같은 세션/state seq116부터 live 재개. [35.25초 관측](../../experiments/orca-harness-20261008/operator/post-numeric-observation-20261010.json)에서 숫자 전체·%·Usage→Global→Status→Usage·CRC VALID·실데이터 갱신 확인. 사용자가 **RESET 미조작·반복 흰색/점멸 소멸**을 직접 확인했다. 현재 단일 writer를 유지하며 지연·물리 오류복구·센서 검교정·24시간은 미측정, `product_pass=false`. 아래는 각 시점 당시 기록이다.

**2026-10-10 16:46 KST 현재:** 반복 점멸 소멸을 사용자에게 확인했다. 숫자 수정 `7d20952`·firmware20/20·SDK build·root GUI3/3·source15/artifact4 hash 확인 완료. Luna는 숫자 pixel2/2·firmware20/20·presentation1/1·producer/selection20/20 및 source/artifact 대조를 통과하고 scoped host PASS 보고서를 작성했다. 다만 `task_5b1435a8c3c1` / `ctx_93b9c8f7189f`의 authoritative `worker_done`은 아직 없으며 같은 작업의 제출을 기다린다. Task26개 중25개 완료. [숫자 후보](../../experiments/orca-harness-20261008/operator/firmware-numeric-candidate.json)는 아직 미업로드, 현 COM3 sole watch/state/세션 유지, `product_pass=false`. 아래는 당시 이력이다.

2026-10-10 추가 사용자 확인: **반복 점멸이 사라짐**. [실물 기록](../../experiments/orca-harness-20261008/operator/post-flicker-observation-20261010.json)에 직접 응답을 반영하여 점멸 보완의 해당 실물 관측을 완료했다. 현재 작업은 Sol `task_2ae3cb0fe949` / `ctx_6fb4838726ea`의 숫자 잘림 수정이며 이후 Luna 검증→새 후보 업로드/관측이다. 아래 직접 점멸 확인 대기는 응답 전 상태다.

2026-10-10 후속 영상 확인: 사용자가 **이전 업로드 영상·BOOT 화면 전환·직접 RST에 따른 WAITING**임을 확인했다. 실물 Usage→Global→Status→Usage, 수치 갱신과 FRAME/CRC VALID를 기록했다. 검사한 영상 샘플에서 이전 흰색 부분 지워짐은 보이지 않지만 반복 점멸 소멸은 직접 관측 답변을 기다린다. **긴 토큰 지수부 잘림은 실제 결함**이므로 [숫자 보완 계획](../plans/2026-10-10-lcd-numeric-readability.md)에 따라 Sol 수정→Luna 독립 검증을 진행한다. [영상 근거](../../experiments/orca-harness-20261008/operator/post-flicker-observation-20261010.json). 현 보드는 기존 점멸 수정본, sole COM3 watch/state/세션은 유지하며 새 숫자 후보 검증 전 덮어쓰지 않는다. `product_pass=false`. 아래는 날짜별 당시 상태다.

2026-10-10 15:52 KST 최신 재개: **기존 Run generation6 연결·동결 source15/artifact4/입력57 hash 확인·PC watch 복구 완료**. Task24개 모두 completed, cleanup 미결0개다. USB 미연결을 확인해 사용자에게 요청했고, ‘com3 꽂았어’ 응답 뒤 COM3 VID303A/PID1001에서 같은 세션/state의 **seq46/2844B** 전송을 확인했다. 현재 terminal은 `term_5ef7b2be-8121-4f9b-be51-bbaadae18bfa`, 60초 갱신이다. 마지막 업로드는 08:48 점멸 수정본이며 이번 재개에 새 flash/reset/init를 수행하지 않았다. **수정 후 30초 무점멸/CRC/BOOT 관측 대기, 제품 전체 PASS 미확정**. [복구 근거](../../experiments/orca-harness-20261008/operator/live-watch-resume-20261010.json) · [최신 재개](orca-harness-resume.md). 아래는 당시 상태다.

2026-10-10 08:49 KST 최신 상태: **점멸 수정·독립 host PASS·COM3 재업로드·같은 세션 live 재개 완료**. 수정 `9bbe333`, 새 tag `orca-harness-20261010-lcd-flicker-candidate` (`8fe1f9f`), firmware19/19·관련 통합21/21·독립 표시1/1 통과. 08:48 업로드의 세 이미지 쓰기 hash 검증 후 같은 sender state로 seq40부터 60초 watch를 재개했다. 현재 watch는 `term_dcac760e-42fa-42f9-afa6-1da904d96d49`다. **수정 후 무점멸/30초·CRC·BOOT 실물 관측 대기**, 긴 토큰 지수부 잘림 별도 미해결, `product_pass=false`. [결과](orca-harness-results.md) · [최신 재개 절차](orca-harness-resume.md). 아래는 각 날짜 당시 상태다.

2026-10-10 08:20 KST 최신 상태: 새 영상에서 실제 숫자와 FRAME/CRC **VALID** 확인. 반복적인 LCD 점멸은 보완 필요이며 Sol `task_63d11f3c24cb` / `ctx_2363ff345723`가 같은 Run에서 원인 재현·firmware 수정을 진행한다. PC watch의 60초 실데이터 전송은 유지한다. 새 업로드 gate는 수정/build·Luna 검증 이후 열며 기존 sender state/순번을 보존한다. **무점멸/30초·제품 전체 PASS는 아직 아니다.** [점멸 계획](../plans/2026-10-10-lcd-flicker.md) · [재개](orca-harness-resume.md). 아래는 당시 상태다.

2026-10-10 08:13 KST 최신 상태: PC 64/64·최종 독립 통합 27/27 및 host 동결 `7ccbb24` 완료. **08:01 COM3 업로드, 사용자 초기 LCD 확인, sender 최초 생성, 08:08 fixture seq0·08:09 실제 세션/quota seq1 전송 완료**. 08:10부터 별도 Orca 터미널 watch가 COM3를 소유하고 같은 state로 60초 자동 갱신한다. 08:03 영상의 Usage/Global/Status 표시와 직접 RST에 따른 재부팅을 기록했다. **현재 전송 후 LCD 값·FRAME/CRC·BOOT·RESET 없는 30초 유지 관측 대기**다. init/reset/두 번째 sender를 실행하지 않는다. device acceptance·지연·센서 타당성·장시간 판정은 미측정이며 product_pass=false다. [결과](orca-harness-results.md) · [재개](orca-harness-resume.md). 아래 날짜별 기록은 당시 상태다.

2026-10-10 08:05 KST 당시 상태: PC 64/64·최종 독립 통합 27/27 완료, coordinator 통합 재실행 27/27 통과. `orca-harness-20261010-host-candidate` (`7ccbb24`)에 동결하고 **08:01 COM3 업로드·쓰기 검증 완료**, **08:03 실제 세션 토큰·native quota 수집 성공**. USB 부팅 로그는 0바이트로 미확인되어 사용자 LCD 초기 상태·BOOT 관측을 기다렸다. sender state 생성·fixture/실데이터 전송은 아직 하지 않았던 시점이다.

2026-10-10 07:47 KST 최신 상태: 남은 PC 시각·OS 제한 문제 수정 제출 `msg_c1e14cc550e2`를 `39e52bd`에 보존·release/ack했다. coordinator 최종 소스 PC **64/64 통과(10.898초)**. 같은 Luna 독립 Task 재시도 `ctx_6b00e6339d06`에서 전체 PC→C 검증을 시작했고, Flash는 보고서·checkpoint만 동기화한다. firmware 소스·산출물 hash 19개 일치. 독립 합격 전 업로드 gate는 닫혀 있고 COM/live/실물은 계속 미실행이다. 아래 날짜별 기록은 당시 상태다.

2026-10-10 07:39 KST 최신 상태: 이전 Flash 제출 `msg_2729ab88db05`를 `e7c5b51`에 보존·release/ack했다. 재개 후 coordinator PC 63개 중 1개 실패(전체 경계 5.016초), 요청 시각 회귀·OS 제한 설정 실패 무시도 확인했다. 새 좁은 수정 `task_d7aa5e059e8d` / `ctx_a7d558d25511`이 실제 AGY Flash에서 실행 중이다. 이후 같은 Luna 독립 Task를 재시도한다. 선택 B·firmware `853ddf7`은 보존하며 업로드·live·실물 gate는 닫혀 있다. [재개 기록](orca-harness-resume.md)이 현재 terminal·generation·다음 작업의 원본이다. 아래 날짜별 기록은 당시 상태다.

2026-10-10 01:43 KST 최신 상태: Flash60 제출 `msg_617eb8c04968`을 수락·release/ack하고 `5d16e97`에 보존했다. coordinator PC 60/60 통과, producer-to-C 모듈은 18개 중 17개 통과·시험 반환 구조 오류 1개다. 허용된 RPC 종료 wait와 실제 queue drain을 모두 적용한 [추가 경계 검사](../../experiments/orca-harness-20261008/operator/pc-shared-budget-cleanup-probe.json)에서 전체 6.125초로 실패했다. `task_e2907fe00c34`의 좁은 PC 보완 후 같은 Luna Task로 최종 재검증한다. 업로드 gate는 닫혀 있으며 firmware `853ddf7`, COM/live/실물 미실행 상태를 유지한다. 아래 날짜별 기록은 당시 상태다.

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

2026-10-10 01:01 KST: Flash 제출 `msg_d704518dc1f4` 수락·release/ack, `1c8181e` 보존 및 coordinator PC 57/57 통과. 전체 manual 경쟁 조건·실제 5초 조건은 별도 검증하며 같은 Luna Task의 재시도 `ctx_08869eb488a4`가 working/live다. 정상 serial fake만 실제 queue 인터페이스에 맞추고 실패 조건은 유지한다. 독립 보고를 기다리며 업로드 gate는 닫혀 있다.

2026-10-10 01:14 KST: Luna 실패 제출 `msg_a690f4aef171` 수락·release/ack, `9721f71` 보존. coordinator도 통합 26개 중 같은 3개 실패(실제 5.562초, MANUAL 중 두 번째 요청 유실, quota 취득 후 요청 유실)를 확인했다. 좁은 후속 `task_1b01674fbb8c` / `ctx_41e3573faa6e`를 Flash에게 dispatch했고 실제 working/live다. 수정 후 같은 독립 Task로 재검증하며 업로드·live·실물은 미실행이다.
