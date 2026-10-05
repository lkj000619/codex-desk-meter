# Codex Sol 후속 1회차

목표: 최초 RM 미도달 결과에서 자신의 동결 구현만 이어서 같은 `gpt-6-sol`·medium/profile/입력/권한으로 수정 비용과 도달 여부를 측정한다.
상태: 후속 1회차가 2026-10-06 03:34:01.746 KST에 시작돼 구현 중이다. 실제 thread/process argv·receipt·source 동일성을 확인했다. 최초 평가와 453개 파일의 최종 독립 복원, 공개 원본 검증·커밋 `017490e`를 보존한다. 후속의 제품·평가·최종 비용은 pending이다.
원본: [운영 계약](../experiments/comparison-operating-contract.md) · [최초 평가](2026-10-06-codex-sol-initial-evaluation.md) · [현재 상태](../experiments/next-comparison-readiness.md).

- [x] 자기 직전 run/commit과 RM2~RM5 관측·고정 기대·evidence hash·남은 회차/초를 담은 피드백을 준비한다.
- [x] 동결 manager로 새 후속 checkout을 준비한다. 그 사본에서만 build/build-host 생성 출력을 제거하고 원본 source·57개 입력·profile 동일성을 검증한다. 이전 freeze/package·판정·비용은 그대로다.
- [x] 현재 CLI/SDK/native inventory와 새 run-bound receipt를 확인하고 동결 runner로 한 번 실행한다. 실제 thread/process argv·시작 snapshot·현재 상태를 보존한다.
- [ ] 종료 후 원본 source·비용을 보존하고 정책·host·동일 artifact 실물/RM를 검토한다. 최초 결과를 후속 결과로 대체하지 않는다.

완료 조건: 원본 조건을 유지한 후속 1회차의 종료·평가·독립 보존과 예산 차감이 연결된다. 후속 최대 3회 AND 누적 7,200초이며 시작 실패·timeout도 사용한 회차다. 최초 2,460.156초는 후속 예산에서 차감하지 않는다. 사용자 `keep going`은 해당 series 진행을 이어가며 Codex Luna 시작을 뜻하지 않는다.

운영 보완 범위: 생성된 이전 build 출력의 절대 경로·executable을 새 checkout에서 제거한다. 새 저장소의 local Git exclude에 build/build-host만 기록해 이후 source 동결에 생성 캐시가 다시 혼입되지 않도록 한다. 제품 source·공통 입력·global 설정·profile·권한은 바꾸지 않고 제거 전후 목록/hash/Git source 동일성을 별도 기록한다. 운영자 환경 준비 시간은 후보 실행 비용과 구분한다.

Run ID `20261006-codex-cli-gpt-6-sol-r01`의 날짜 뒤 suffix는 당일 예약 번호이며 ledger의 `round: 1`이 후속 1회차를 뜻한다. 직전 최초는 `20261005-codex-cli-gpt-6-sol-r01`이다. 준비 commit `3a01a5012180cec2b32bba18fa4287a79a35de69`에서 생성 출력 1,413개만 제외했고 product source 18개의 Git blob/줄바꿈 정규화 내용과 고정 입력 57개를 검증했다. Receipt SHA-256 `16c93563e8187b59c6488c00a33209adbd38ebc8e26448e73067bb2cb6007132`, native thread `01a10d58-20e1-7eb2-93f7-97fb84a5eb89`다. 후보 실행 중 구현 피드백·serial/flash는 없으며 현재 보드는 최초 artifact를 유지한다.
