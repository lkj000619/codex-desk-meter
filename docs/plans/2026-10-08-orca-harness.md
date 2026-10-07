# Orca 협업 구현 계획

목표: 별도 브랜치에서 동결 입력으로 새 구현, LCD UX/UI 디자인과 실제 PC Codex 세션·quota
수집을 연결하고 역할별 실행·품질·비용을 재현 가능한 근거로 기록한다.

원본 범위/인터페이스: [협업 설계](../design/2026-10-08-orca-harness.md).
시간 예산: 사용자 지시로 별도 제한 없음. 기존 비교 잔여 예산과 합산하지 않음.

| 작업 | 상태 | 완료 조건 |
|---|---|---|
| 별도 Orca worktree·입력 보존 | 완료 | 실제 branch 생성, 57개 입력 바이트/hash 일치, 과거 제품 제거는 새 checkout에만 적용 |
| 사용자 범위·역할 확정 | 완료 | Sol/Flash/Luna, GUI는 AGY Gemini 3개+Codex CLI gpt-6.1-sol 3개, 세션 토큰+quota 확인 |
| 역할별 기술 검토·DAG | 진행 중 | 실제 Task/Dispatch·실효 모델 기록, 인터페이스/하드웨어/시험 보고서 |
| LCD UX/UI·OpenDesign | 두 모델 각 3개 제출 완료; 독립 검증·선택 대기 | pinned skills, 820×320 정상/오류/unknown/stale·BOOT 시안, 사용자 선택·LCD handoff |
| PC 프로그램 구현 | 예정 | 실제 metadata 수집·quota RPC·fixture·정규화·영속 sender·자동/수동 갱신 자체 시험 |
| firmware·통합 | 예정 | BSP·receiver/cache·GUI·선택 F9, 실제 C seam 시험·idf build |
| 독립 검증·수정 | 예정 | Luna의 결함 처리, 계약·경계·실패→last-good→복구 통합 검증 |
| 업로드·owner-only live·실물 관측 | 예정 | 동결 binary/hash·COM3 수신·LCD/BOOT·30초·단절/복구·지연 근거 |
| 결과·실행 정리 | 예정 | 판정·미측정·실효 모델·시간/token coverage·질문·실패 기록, worker 소유권 정리 |

계획을 읽는 것만으로 구현 단계를 시작하지 않는다. 현재 승인된 GUI 후보 작성·검토를 진행하고
인터페이스·디자인 선택에 의존하는 제품 구현은 그 결정이 기록된 뒤 dispatch한다.

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
- [ ] Luna의 요구·검증 보고서 수락
- [ ] GUI 후보 6개 자체/독립 검증·사용자 비교 화면 제시
- [ ] 사용자 선택과 구현 인터페이스 확정
- [ ] PC·firmware 구현 및 host 통합 검증
- [ ] 독립 결함 수정·제품 commit/binary 동결
- [ ] COM3 업로드·fixture/live·사용자 실물 관측
- [ ] 결과·시간/token coverage·미측정 기록, worker 소유권 정리

각 단계의 시작/완료는 실제 Task/Dispatch와 검증 결과를 근거로 갱신한다.
중단되면 [재개 절차](../experiments/orca-harness-resume.md)와 각 역할 checkpoint부터 읽는다.
