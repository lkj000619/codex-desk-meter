# 평가 baseline·문서 일관성 보완 계획

목표: 문서 재검증 R1~R3와 전체 일정 피드백을 반영한다.
상태: 구현·문서 보완 완료. 실제 새 baseline commit 동결과 실행 준비는 별도 잔여 조건이다.
[검토 원본](../../results/documentation-review-20261003/report.md) ·
[보완 결과](../../results/documentation-review-20261003/remediation.md).
실행 방법: 현재 세션에서 테스트 우선으로 순차 구현·문서 정비한다.

## 선택한 방식

평가 overlay를 별도 운영하지 않고 후보 입력을 보존한 새 baseline에 운영 기준·도구를 함께 고정한다.
prepare는 baseline 원본 파일 ZIP과 profile을 후보 checkout 밖의 operator evidence로 보존한다.
후속도 같은 ZIP을 이어받고 package 생성/독립 복원 때 평가·입력 hash를 다시 계산한다.
과거 ZIP 없는 run은 기존 경로를 유지한다. 본 실험·실물·GPT-6 capability 실행은 별도다.

## 작업 및 완료 조건

- [x] R1: baseline ZIP 보존·후속 전달·package 복원 hash 재계산의 회귀시험과 구현.
- [x] R1: 기존 baseline/overlay 병행 안내를 새 공통 baseline 경로로 통일하고 원본 commit을 보존.
- [x] R2: 접근 정책의 현재 상태 연결을 새 readiness로 수정.
- [x] R3: F9의 항목별 증거 체크 배점·독립 채점·이견 조정을 정의.
- [x] 전체 3블록·최초/후속 예산·단일 보드 슬롯·중단 기록을 운영 계약에 정리.
- [x] 전체 회귀, 후보 입력 불변, 링크와 독립 복원 확인 후 보완 결과 기록.

새 실제 실험 baseline의 commit 동결·GPT-6 profile 검증·날짜별 prepare/receipt는 실행 준비 단계다.
이번 보완은 그 절차를 구현·검증하며 미실행 모델 capability를 통과로 기록하지 않는다.
