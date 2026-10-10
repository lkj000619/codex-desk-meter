# Orca 협업 구현 계획

2026-10-10 후속 관측: 이전 업로드·BOOT 화면 전환·수동 RST 사실을 사용자 응답과 영상으로 기록했다. [관측](../../experiments/orca-harness-20261008/operator/post-flicker-observation-20261010.json)의 수치 갱신/CRC VALID는 확인, 반복 점멸 직접 확인 대기, 긴 토큰 숫자 잘림 FAIL이다。 [숫자 보완 계획](2026-10-10-lcd-numeric-readability.md)에 따라 같은 역할의 새 Task를 진행한다. 아래 완료는 당시 host/업로드 범위이며 전체 제품 합격은 아니다.

2026-10-10 15:52 KST 재개: 기존 Run generation6 연결, 입력57/source15/artifact4 hash 및 Task24개 completed 확인. PC watch는 Orca 재시작으로 종료돼 있었으며 사용자 COM3 재연결 후 같은 세션/state seq46부터 복구했다. [최신 재개 기록](../experiments/orca-harness-resume.md). 구현/검증/동결/업로드 완료는 보존하고, 수정 후 실물 점멸·CRC·BOOT·30초 관측을 이어간다.

2026-10-10 08:49 KST 추가: 점멸 표시 수정 `9bbe333`·Luna 독립 PASS를 새 tag `orca-harness-20261010-lcd-flicker-candidate` (`8fe1f9f`)로 동결하고 **08:48 COM3 재업로드·쓰기 검증 완료**. 같은 세션/state의 watch를 seq40부터 재개했다. [점멸 보완 계획](2026-10-10-lcd-flicker.md)의 코드/검증/업로드는 완료, 수정 후 사용자 무점멸·CRC·BOOT·30초 관측은 대기다. 기존 최초 host/관측은 보존하며 `product_pass=false`다.

2026-10-10 08:20 KST 추가: 사용자 후속 영상에서 실데이터와 FRAME/CRC VALID 확인. 반복 점멸은 보완 필요하여 [별도 점멸 계획](2026-10-10-lcd-flicker.md)과 기존 Sol 모델의 후속 Task를 시작했다. 아래 host 완료는 보존하고 실물 제품 PASS는 선언하지 않는다.

2026-10-10 08:13 KST 현재: 최종 PC 64/64·독립 통합 27/27 통과 및 역할 작업 정리 완료. `7ccbb24` host 후보를 COM3에 업로드했고, 초기 LCD 관측 후 fixture·실제 세션/quota 전송과 60초 watch를 실행했다. **전송 후 사용자 LCD/CRC·BOOT·30초 관측 대기**이며 `product_pass=false`다. 새 기능·재업로드·sender 재초기화 없이 관측을 이어간다.

2026-10-10 07:39 KST 당시 재개: Flash 제출 `e7c5b51`은 보존했으나 coordinator PC 63개 중 1개 실패(5.016초)와 남은 시각·OS timeout 문제로 완료 조건 미충족이었다. 좁은 후속 `task_d7aa5e059e8d` / `ctx_a7d558d25511`을 실행하고 수정 수락·같은 Luna Task 재검증 후 동결/업로드로 진행했다. 당시 업로드·live·실물은 미실행이었다.

목표: 별도 브랜치에서 동결 입력으로 새 구현, LCD UX/UI 디자인과 실제 PC Codex 세션·quota
수집을 연결하고 역할별 실행·품질·비용을 재현 가능한 근거로 기록한다.

원본 범위/인터페이스: [협업 설계](../design/2026-10-08-orca-harness.md).
시간 예산: 사용자 지시로 별도 제한 없음. 기존 비교 잔여 예산과 합산하지 않음.

| 작업 | 상태 | 완료 조건 |
|---|---|---|
| 별도 Orca worktree·입력 보존 | 완료 | 실제 branch 생성, 57개 입력 바이트/hash 일치, 과거 제품 제거는 새 checkout에만 적용 |
| 사용자 범위·역할 확정 | 완료 | Sol/Flash/Luna, GUI는 AGY Gemini 3개+Codex CLI gpt-6.1-sol 3개, 세션 토큰+quota 확인 |
| 역할별 기술 검토·DAG | 초기 요구·인터페이스 보고 수락 완료 | 실제 Task/Dispatch·실효 모델 기록, 인터페이스/하드웨어/시험 보고서 |
| LCD UX/UI·OpenDesign | B 수정 `a3aeebb`; 독립 PASS 제출 `msg_1f1335f9e59f` 수락 완료 | pinned skills, 820×320 정상/오류/unknown/stale·BOOT 시안, 사용자 선택·LCD handoff |
| PC 프로그램 구현 | `39e52bd` 수락; coordinator PC 64/64·최종 독립 통합 PASS; 실제 수집·전송/watch 실행 | 실제 metadata 수집·quota RPC·fixture·정규화·영속 sender·자동/수동 갱신 자체 시험 |
| firmware·통합 | 활성 source 수정 제출 `853ddf7` 수락; coordinator 실제 C 시험 18개·선택 세션 통합 1개 통과 | BSP·receiver/cache·GUI·선택 F9, 실제 C seam 시험·idf build |
| 독립 검증·수정 | 같은 Luna Task `ctx_6b00e6339d06` PASS 수락·release/ack; root 통합 27/27; 이전 FAIL 보존 | Luna의 결함 처리, 계약·경계·실패→last-good→복구 통합 검증 |
| 업로드·owner-only live·실물 관측 | COM3 업로드·수집・전송・watch 및 초기 LCD 확인 완료; 전송 후 실제 값/BOOT·30초 대기 | 동결 binary/hash·COM3 수신·LCD/BOOT·30초·단절/복구·지연 근거 |
| 결과·실행 정리 | 역할별 source/evidence·host 결과·미측정 범위 문서화, worker 소유권 정리 완료; 실물 후속 기록 진행 | 판정·미측정·실효 모델·시간/token coverage·질문·실패 기록, worker 소유권 정리 |

인터페이스와 사용자의 B 선택은 설계·context에 기록됐다. PC 구현은 병행 진행하며,
펌웨어 GUI 최종 통합·제출은 선택 B의 결함 보완·독립 검증을 받은 뒤 수행한다.

2026-10-09 00:02 KST 실행 순서 조정: 사용자 B 선택과 데이터 의미는 이미 확정됐다.
B의 남은 결함은 prototype의 캐시 전환과 회귀 검사이며 보드 초기화·C 수신기 구현과 독립적이다.
Sol의 core 작업은 병행 시작하고, GUI 최종 통합·제출·통합 검증은 B 독립 PASS 이후에만 수행한다.
이 조정은 제품 합격 gate를 완화하지 않는다. 이전의 전체 firmware 시작 차단 기록은 당시 상태다.

## 재개 체크리스트

- [x] 사용자의 새 구현·무제한 별도 예산·PC 수집 범위·GUI 6개 요청 기록
- [x] Orca branch/worktree·Run 생성, 동결 입력 57개 바이트 검증
- [x] 역할별 파일 소유권과 재개 절차 작성
- [x] OpenDesign pinned 원본 설치·검토 완료
- [x] AGY Gemini GUI 후보 3개 Task/Dispatch 시작·실효 모델 확인
- [x] Codex CLI gpt-6.1-sol GUI 후보 3개 Task/Dispatch 시작·실효 모델 확인
- [x] OpenDesign viewer 원본 hash 확인·AGY 준비 보고 수락
- [x] AGY Gemini 후보 3개·handoff 제출 수락 (독립 GUI 검증은 별도)
- [x] Codex Sol 6.1 후보 3개·handoff 제출 수락; 실제 행동 검사 재실행 통과
- [x] Luna의 요구·검증 검토 시작
- [x] Luna의 요구·검증 보고서 수락; 인터페이스 질문 해결·조건별 acceptance 기록
- [x] GUI 독립 브라우저 검증·비교 화면 Task 시작
- [x] GUI 후보 6개 브라우저 검토·보고 수락·사용자 비교 화면 제시 (발견 결함은 선택 B 보완으로 연결)
- [x] 사용자 선택(B · Swiss Studio Meter)과 구현 인터페이스 확정
- [x] 선택 B 첫 보완 제출·독립 재검증 FAIL 원본 보존: Unknown/Waiting 전환 시 last-good 유실
- [x] 선택 B 실제 JS 회귀 검사와 캐시 수정 제출 수락·coordinator 검사 통과 (`a3aeebb`)
- [x] 같은 선택 B Task 복구 `ctx_9477f122f8d4`; 독립 PASS native 제출 수락·release/ack
- [x] PC 수집기 구현 Task/Dispatch 시작 (`ctx_e7bb307f023b`); 완료·검증은 별도
- [x] PC 최초 제출 보존·실제 native event/시각/quota/state 유실 결함 재현 및 보완 연결 (`ctx_221ff3735dae`)
- [x] PC runtime 보완 제출 `ctx_4308689007a9` 보존·worker release/Delivery ack; 제출과 실제 품질 판정 구분
- [x] PC aging·privacy·초기화·Windows crash 제출 수락 및 기존 39개 시험 (`14cc264`)
- [x] 추가 PC→C watch timestamp·cold global·provider별 캐시·null 관측 시각 보완 (`task_a6eebb977125`, `0e39f0d`); 50개 시험 coordinator 재실행 통과
- [x] 수집·RPC cleanup·write/drain을 포함한 5초 수동/연결 복구 **host 경계** 검증 (`39e52bd`, 독립 `6f52105`; 원래 두 RPC와 무예산 경계 별도 보존, 이전 6.125초/5.016초 FAIL 원본 유지)
- [x] firmware BSP·C receiver·선택 B GUI·F9 및 실제 ESP-IDF build (`b6ec3d5`)
- [x] 독립 검토의 firmware 활성 세션·scoped source identity 수정 및 새 build (`task_e44125e18973`, `853ddf7`); 최종 독립 검증은 별도
- [x] 최신 PC 보완·host 통합 독립 검증 (PC 64/64, 통합 27/27)
- [x] firmware core `ctx_d5c857a3d228` 실제 Sol 6 working/live 시작 및 checkpoint 확인 (GUI 최종 gate는 유지)
- [x] 독립 결함 수정·host 후보 commit/binary 동결 (`orca-harness-20261010-host-candidate`, `7ccbb24`)
- [x] COM3 업로드·fixture/live host 전송・60초 watch・초기 사용자 LCD 관측
- [ ] 전송 후 LCD 숫자・FRAME/CRC 수락・BOOT 3회/길게・RESET 없는 30초 유지
- [ ] 실물 반영 지연・오류/복구・센서 타당성・분리 전원 링크 단절・24시간 안정성
- [x] host 결과·시간/token coverage unknown·미측정 기록, 역할 worker 소유권 정리
- [ ] 실물 최종 관측을 반영한 제품 판정・실행 정리

2026-10-09 18:16 KST: 동결된 firmware 제출 검토는 PC 보완과 독립적이므로 Luna가
이를 먼저 진행한다. 같은 통합 Task의 최종 PC→C 검증·제출과 업로드 gate는 최신 PC
보완 수락/시험 이후다. PC 담당이 수정 중인 파일을 완성된 제출로 판정하지 않는다.

## 2026-10-10 재개 후 남은 보완 순서

목표는 선택 B와 실제 수집 데이터를 연결해 보드에서 검증 가능한 제출을 만드는 것이다. 중단된 검증 파일은 `0f552c9`에 보존했고, 같은 통합 Task의 `ctx_125c9c02c0ed`에서 실행을 이어간다.

1. Luna가 안정된 PC `5ddef63`와 firmware `853ddf7`을 실제 PC→C 경로로 검증하고 실패 목록을 제출한다. fake 누락으로 통과했던 이전 10개 시험은 근거로 사용하지 않는다.
2. Flash가 확인된 PC 결함을 공유 sender/watch 경로에서 보완한다. serial queue 대기를 시간 내 동기적으로 끝내고 오류·timeout을 실패로 전달하며, 백그라운드 flush 작업을 남기지 않는다. 실패한 전송의 예약 sequence는 유지한다.
3. 요청 전에 수집이 끝난 frame으로 전송 중 발생한 manual 요청을 소거하지 않는다. 재수집한 다음 sequence를 전송하고 자동 60초 deadline을 유지한다. 수집·RPC 종료·write·queue drain을 모두 포함한 수동/연결 복구 5초 검사를 수행한다.
4. coordinator가 보완 제출을 보존·검증한 뒤 같은 Luna Task를 재검증한다. 최종 보고에서 해결된 결함·남은 미측정 조건을 구분한다. 결함이 남으면 upload gate를 열지 않는다.
5. 통과 시 현재 binary/source hash·COM 대상 확인 후 업로드하고, 실제 session/quota 수집·사용자 LCD/BOOT 관측으로 연결한다. 물리·24시간 검사는 실제 근거가 있을 때만 합격 처리한다.

완료 조건: native 제출 수락과 역할별 후속 소유권 정리, 의미 있는 production-path 회귀 검사 통과, 원본 57개 보존, 업로드/장치 관측 근거와 미측정 범위 기록. 모델 역할과 기존 비교 결과는 변경하지 않는다.

각 단계의 시작/완료는 실제 Task/Dispatch와 검증 결과를 근거로 갱신한다.
중단되면 [재개 절차](../experiments/orca-harness-resume.md)와 각 역할 checkpoint부터 읽는다.
