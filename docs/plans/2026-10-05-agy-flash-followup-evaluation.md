# AGY Flash 후속 1회차 종료 후 평가

목표: `20261005-antigravity-cli-agy-flash-r02`의 종료 결과와 비용을 보존하고, 같은 공통 입력으로 독립 검증·업로드·실물/RM 평가를 수행한다.
상태: 2026-10-05 동결·정책·독립 host 검증·원본 업로드·사용자 영상·최종 RM 평가·501개 파일의 독립 복원 완료. RM1 pass/RM2 partial/RM3 fail/RM4 partial/RM5 partial로 기준 미도달이며 정책은 invalid_for_comparison이다. 사용자가 다음 모델로 넘어가지 말고 기다리도록 지시해 추가 AGY 회차와 다음 모델을 보류한다. 현재 원본 펌웨어와 잔여 예산을 유지한다.

원본 규칙은 [운영 계약](../experiments/comparison-operating-contract.md), [RM 목록](../experiments/reference-match-matrix.md), [접근 정책](../experiments/isolation-policy.md)을 따른다.
현재 상태는 [준비 상태](../experiments/next-comparison-readiness.md)와 [진행 기록](../../results/formal-comparison-20261004/report.md)에서 관리한다.

- [x] 기존 raw 사본과 현재 bytes를 대조하고 source를 Git 동결·bundle로 보존한다. terminal manifest/ledger 원본은 유지한다.
- [x] native 도구·명령·외부 경로·거부 이후 행동을 검토하고 정책 sidecar를 기록한다. 이전 회차 실행 파일 참조를 적격 검토에 반영한다.
- [x] 동결 validator로 제출물·입력을 검증하고 Python 시험·공통 collector/encoder를 독립 실행한다.
- [x] 후보의 CTest 통과 기록과 이번 source의 별도 host 검증을 구분한다. 동일 compiler로 checkout 밖에서 host만 빌드했다. firmware를 운영자가 재빌드하거나 후보 source를 고치지 않았다.
- [x] 동결 firmware의 source/build/artifact 연결과 COM3 보드 식별을 확인한 뒤 업로드하고 원본 공통 seq 0·1을 전송·기록한다. 실패도 보존한다.
- [x] 사용자 영상/관측을 run·artifact·업로드 슬롯에 연결하고 RM review를 한 번 적용한다. 미관측을 pass로 바꾸지 않는다.
- [x] 최종 package를 독립 복원하고 비용·정책·RM·후속 잔여 예산을 기록한다.

완료 조건: 원본 비용·첫 결과·baseline/tag를 보존하고, 이번 회차의 source 동결·정책·독립 host 검증·실물/RM 판정·독립 복원을 근거/hash로 연결한다. 영상이 아직 없으면 평가 완료로 보고하지 않고 관측 대기 단계와 촬영 대상을 명시한다. 현재 회차를 재실행하거나 다른 모델을 먼저 시작하지 않는다.

완료 근거: [최종 RM](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-final-20261005/reference-review.json)과 [독립 복원](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-final-20261005/restore-audit.json).
이번 평가 계획은 완료했으며 전체 비교와 AGY Flash series는 사용자 재개 지시를 기다린다. 후속 잔여 5,710.781초·2회를 보존하고 추가 회차를 준비·시작하지 않는다.
