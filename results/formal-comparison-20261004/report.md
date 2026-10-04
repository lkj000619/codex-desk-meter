# 정식 동일 조건 비교 실행 기록

상태: 첫 블록 OpenCode Muse 최초 실행 중. 시작 시각 2026-10-04 22:47:50 KST.
제품 실험 시작 1회, 완료·정책 판정·RM 판정·제품 합격은 아직 미확정이다.
준비 당시의 0회 기록과 동결 tag는 보존한다.

원본 계약은 [운영 계약](../../docs/experiments/comparison-operating-contract.md),
실행 순서·완료 조건은 [실행 계획](../../docs/plans/2026-10-04-formal-comparison-execution.md)을 따른다.
baseline은 `272875140d1998d458e26fdb2f6deab5e5d8f7b5` / `comparison-baseline-20261004`다.
활성 5개·독립 3블록·Claude 제외라는 구성을 유지한다.

## 첫 실행

- 모델: OpenCode `opencode/muse-spark-1.3-contributor-free`.
- run: `20261004-opencode-cli-opencode-muse-r01`.
- 최초 예산: 최대 7,200초. 자동 재시도·추가 session·운영자 구현 피드백을 제공하지 않는다.
- 원본 위치: `C:/meter-runs-20261004/20261004-opencode-cli-opencode-muse-r01/`의 manifest·stdout.jsonl·stderr.txt·checkout.
- ledger: `C:/meter-runs-20261004/ledgers/20261004-opencode-cli-opencode-muse-r01.json`.
- runner: 깨끗한 operator checkout `C:/meter-operator-20261004`의 동결 `scripts/benchmark.py`.
- 실행 process는 대화와 별도다. [launcher 기록](first-run-launch.json)과 [관측한 진행 상태](progress.json)를 남겼다.

후보 입력·공통 과제·profile은 준비 때의 hash를 유지한다. 후보는 serial/flash를 수행하지 않는다.
결과 제출 후 운영자가 source를 수정하지 않고 자체 시험·빌드·정책 준수와 COM3 실물 동작을 검토한다.
원본 계측의 null은 0으로 바꾸지 않는다. 준비 비용과 제품 비용을 분리하며 실패·미검증 결과도 보존한다.

## 재개 시 확인 순서

manifest·ledger 상태와 launcher PID의 실행 여부를 먼저 확인한다. running 후보를 다시 실행하지 않는다.
terminal 상태이면 실제 비용·raw 로그를 검토하고 결과 동결·정책 review·실물/RM 관측으로 이어간다.
강제 중단이 있었다면 기존 reconcile 절차로 종료 비용을 연결한다.
다른 날의 미시작 최초 예약은 새 ID·ledger·receipt로 준비하며 기존 기록을 보존한다.
