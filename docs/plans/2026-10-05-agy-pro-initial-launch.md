# AGY Pro 최초 실행 시작

목표: 사용자의 “다음 모델 ㄱㄱ” 지시에 따라 첫 블록의 다음 모델 `gemini-3.1-pro-high`를 동결 조건의 독립 최초 실험으로 시작한다.
상태: 2026-10-05 실제 native 시작 검증 완료. 최초 호출은 22:15:28.585~22:16:36.793 KST, 68.203초 후 첫 command 권한 거부로 environment_failed. 코드·제출물이 없어 RM1 fail/RM2~RM5 not_run이며 정책 eligible다. 338개 파일의 독립 복원을 마쳤다. Flash 남은 예산은 보존하고 [별도 Pro 후속 계획](2026-10-05-agy-pro-followup-execution.md)으로 이어간다.
원본: [운영 계약](../experiments/comparison-operating-contract.md), [현재 상태](../experiments/next-comparison-readiness.md), [전체 실행 계획](2026-10-04-formal-comparison-execution.md).

- [x] 미시작 Pro 예약·개별 ledger·깨끗한 candidate checkout·57개 입력·baseline/profile/receipt hash와 현재 CLI/SDK/native 설정을 검증한다. 같은 날짜 예약만 사용한다.
- [x] 기존 scoped wrapper와 동결 runner로 최초 1회만 시작하고 native model·permission mode·cwd를 실제 로그로 확인한다. 실제 PID·시각·입력·receipt를 보존했다. 시작 기록 수집 전에 종료해 최종 snapshot에서 native init을 검증한다.
- [x] 현재 준비 상태·진행 기록을 갱신하고 기록의 bytes/hash를 검증·커밋한다. 다른 모델이나 Flash 후속을 함께 시작하지 않는다.

완료 조건: Pro 최초 run `20261005-antigravity-cli-agy-pro-r01`의 실제 시작을 native 로그와 개별 ledger로 확인한다. 시작 실패나 미관측을 성공으로 기록하지 않는다. 공통 baseline `272875140d1998d458e26fdb2f6deab5e5d8f7b5`·57개 입력·최초 7,200초·후속 최대 3회/누적 7,200초·거부 시 종료 규칙을 유지한다. 원본 AGY Flash 대기 기록과 결과·예산을 수정하지 않고 새 사용자 지시의 범위를 별도로 기록한다.

종료 후에는 Pro 제출물과 비용을 동결하고 정책·host·실물/RM 평가를 수행한다. 후보 실행 중에는 운영자 source 수정·구현 피드백·serial/flash가 없다. 보드는 기존 Flash 후속 원본을 유지하며 Pro의 종료·동결 이후 업로드한다. 현재 진행 상태는 `progress.json`으로 남겨 대화 중단 후 동일 후보를 재호출하지 않는다.
