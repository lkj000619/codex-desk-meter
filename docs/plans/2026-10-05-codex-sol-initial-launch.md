# Codex Sol 최초 실험

목표: 사용자 지시 “그럼 다음 모델로 넘어가자”에 따라 다음 순서 `gpt-6-sol`·medium의 독립 최초 실험을 동결 조건에서 실행한다.
상태: 시작 작업 완료. 최초 실행은 2026-10-05 23:56:01.520 KST에 시작해 2026-10-06 00:37:01.691 KST에 종료했다. 이후 [최초 평가 계획](2026-10-06-codex-sol-initial-evaluation.md)으로 동결·평가·업로드를 마쳤다. 최초 reference는 미도달이며 제품 구현 완료가 아니다. 이전 Pro series는 회차 한도로 종료했다.
원본: [운영 계약](../experiments/comparison-operating-contract.md) · [현재 상태](../experiments/next-comparison-readiness.md) · [전체 실행 계획](2026-10-04-formal-comparison-execution.md).

- [x] 같은 날짜의 미실행 예약·개별 ledger·깨끗한 checkout·공통 입력 57개·baseline/profile/receipt를 확인한다. 모델을 호출하지 않는 native inventory로 기존 비활성화 설정을 대조한다.
- [x] 동결 runner로 최초 1회만 시작하고 실제 process·thread 시작·argv·시각·원본 로그를 보존한다. CLI가 방출하지 않는 실효 model/cwd는 검증했다고 추정하지 않는다.
- [x] 현재 상태와 공개 시작 snapshot을 검증하고 커밋한다. 중단 후 manifest·ledger·실제 process를 먼저 확인해 중복 실행을 방지한다.

완료 조건: 최초 실행의 실제 시작과 현재 상태를 확인한다. 이 계획의 시작 완료는 제품 구현·평가 완료를 뜻하지 않는다. 최초 최대 7,200초, 후속 최대 3회 AND 누적 7,200초를 유지한다. 종료 후 후보 source·제출물·원본 비용을 동결하고 정책·host·제품/RM를 평가한다. 업로드 가능한 firmware가 있으면 동결 artifact를 COM3에 올려 사용자 실물 관측을 연결한다.

실행 중 운영자 구현 수정·피드백·serial/flash는 없었다. Pro 원본 결과와 Flash 잔여 예산·과거 업로드 근거는 보존한다. 종료 후에는 Sol 동결 펌웨어를 업로드했다. Codex Luna는 함께 시작하지 않는다.
