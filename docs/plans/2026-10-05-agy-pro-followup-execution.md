# AGY Pro 후속 1회차 실행

목표: 기존 정식 비교의 허용된 후속 절차로 Pro 최초 실패를 보존하고 자기 직전 동결 source·관측만 전달해 후속 1회차를 실행한다.
상태: 2026-10-05 후속 r02는 22:29:17.277~22:30:38.899 KST 실행 후 native Copy-Item 거부로 environment_failed. 81.625초·정규화 94,452 token과 partial CMakeLists·정책 eligible·RM1 fail/RM2~RM5 not_run을 보존했다. 346개 파일의 독립 복원을 완료했으며 [남은 후속 계획](2026-10-05-agy-pro-remaining-followups.md)으로 이어간다.
원본: [운영 계약](../experiments/comparison-operating-contract.md), [현재 상태](../experiments/next-comparison-readiness.md), [전체 실행 계획](2026-10-04-formal-comparison-execution.md).

- [x] 최초 결과·정책/RM·338개 파일의 독립 복원·비용을 연결한 자기 피드백으로 별도 후속 checkout을 준비한다. 최초를 재호출하지 않는다.
- [x] 동일 `gemini-3.1-pro-high`·profile·고정 입력·권한·거부 시 종료 규칙과 새 receipt를 검증한 뒤 한 번 시작한다. Native model·cwd·request-review를 실제 로그로 확인한다.
- [x] 실제 상태와 원본 계측을 보존하고 현재 문서에 기록한다. 종료 후에는 source를 고치지 않고 제출물·정책·host·실물/RM를 검토한다.

완료 조건: 후속 1회차의 실제 시작·현재 상태가 새 ID와 같은 Pro ledger에 연결되고 최초 68.203초·정규화 89,861 token 비용과 최초 실패 원본이 유지된다. 후속 최대 3회 AND 누적 7,200초 안에서 실제 종료 시간을 차감한다. 권한을 완화하거나 실행 중 구현 피드백을 제공하지 않는다. Flash 남은 회차는 보류하며 현재 보드의 Flash 펌웨어를 Pro 종료·동결 전까지 유지한다. 다음 Codex 모델을 함께 시작하지 않는다.
