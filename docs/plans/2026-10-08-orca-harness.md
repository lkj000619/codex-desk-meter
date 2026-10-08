# Orca 협업 구현 계획

목표: 별도 브랜치에서 동결 입력으로 새 구현, LCD UX/UI 디자인과 실제 PC Codex 세션·quota
수집을 연결하고 역할별 실행·품질·비용을 재현 가능한 근거로 기록한다.

원본 범위/인터페이스: [협업 설계](../design/2026-10-08-orca-harness.md).
시간 예산: 사용자 지시로 별도 제한 없음. 기존 비교 잔여 예산과 합산하지 않음.

| 작업 | 상태 | 완료 조건 |
|---|---|---|
| 별도 Orca worktree·입력 보존 | 완료 | 실제 branch 생성, 57개 입력 바이트/hash 일치, 과거 제품 제거는 새 checkout에만 적용 |
| 사용자 범위·역할 확정 | 완료 | Sol/Flash/Luna, GUI는 AGY Gemini 3개+Codex CLI gpt-6.1-sol 3개, 세션 토큰+quota 확인 |
| 역할별 기술 검토·DAG | 초기 요구·인터페이스 보고 수락 완료 | 실제 Task/Dispatch·실효 모델 기록, 인터페이스/하드웨어/시험 보고서 |
| LCD UX/UI·OpenDesign | B 첫 독립 재검증 FAIL 보존 (`3929925`); 실제 JS 캐시 수정 `task_57d8de5426b5` 진행 | pinned skills, 820×320 정상/오류/unknown/stale·BOOT 시안, 사용자 선택·LCD handoff |
| PC 프로그램 구현 | runtime 보완 제출 보존 (`7264e76`); 32개 시험 중 Windows 종료 시험 1개 실패·오류 aging/privacy 결함 보완 `task_c6f6d8f00810` | 실제 metadata 수집·quota RPC·fixture·정규화·영속 sender·자동/수동 갱신 자체 시험 |
| firmware·통합 | Task `task_b1214421a314` native blocked; B 독립 재검증 PASS 후 ready로 변경·시작 | BSP·receiver/cache·GUI·선택 F9, 실제 C seam 시험·idf build |
| 독립 검증·수정 | `task_4d49e747c570` native blocked; 최신 PC 보완 검증과 firmware 제출 후 시작 | Luna의 결함 처리, 계약·경계·실패→last-good→복구 통합 검증 |
| 업로드·owner-only live·실물 관측 | 예정 | 동결 binary/hash·COM3 수신·LCD/BOOT·30초·단절/복구·지연 근거 |
| 결과·실행 정리 | 예정 | 판정·미측정·실효 모델·시간/token coverage·질문·실패 기록, worker 소유권 정리 |

인터페이스와 사용자의 B 선택은 설계·context에 기록됐다. PC 구현은 병행 진행하며,
펌웨어 GUI는 선택 B의 결함 보완·검증된 handoff를 받은 뒤 dispatch한다.

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
- [ ] 선택 B 실제 JS 회귀 검사와 캐시 수정 (`task_57d8de5426b5` / `ctx_fa13d9a20591`)
- [ ] 같은 선택 B 검증 Task `task_0d62e820abfa`를 failed `ctx_c9524d9d2327`의 retry-of로 재검증; PASS가 firmware 시작 gate
- [x] PC 수집기 구현 Task/Dispatch 시작 (`ctx_e7bb307f023b`); 완료·검증은 별도
- [x] PC 최초 제출 보존·실제 native event/시각/quota/state 유실 결함 재현 및 보완 연결 (`ctx_221ff3735dae`)
- [x] PC runtime 보완 제출 `ctx_4308689007a9` 보존·worker release/Delivery ack; 제출과 실제 품질 판정 구분
- [ ] PC 오류 aging·경로 비노출·source별 캐시·초기화·실제 Windows crash 시험 보완 (`task_c6f6d8f00810`)
- [ ] PC·firmware 구현 및 host 통합 검증
- [ ] 독립 결함 수정·제품 commit/binary 동결
- [ ] COM3 업로드·fixture/live·사용자 실물 관측
- [ ] 결과·시간/token coverage·미측정 기록, worker 소유권 정리

각 단계의 시작/완료는 실제 Task/Dispatch와 검증 결과를 근거로 갱신한다.
중단되면 [재개 절차](../experiments/orca-harness-resume.md)와 각 역할 checkpoint부터 읽는다.
