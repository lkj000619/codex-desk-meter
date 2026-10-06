# Codex Luna 최초 실험

목표: 사용자 지시 “luna 시작하자”에 따라 block1/seed1의 다음 순서 `gpt-6-luna`·max 최초 실험을 같은 동결 조건으로 한 번 시작한다.
상태: 시작 작업 완료. `20261006-codex-cli-gpt-6-luna-r01` 최초 실행을2026-10-06 10:10:26.658 KST에 시작했고 후보 구현은 실행 중이다. Sol series 종료·원본 보존을 확인했으며 전날의 미실행 Luna 예약은 보존했다.
원본: [운영 계약](../experiments/comparison-operating-contract.md) · [현재 상태](../experiments/next-comparison-readiness.md) · [전체 실행 계획](2026-10-04-formal-comparison-execution.md).

- [x] 깨끗한 baseline `272875140d1998d458e26fdb2f6deab5e5d8f7b5`에서 오늘 날짜의 새 ID·독립 후보 저장소·ledger를 준비하고 입력57개·동결 profile·제품 코드 없는 최초 상태를 검증했다.
- [x] 원본 capability 근거와 오늘의 CLI/SDK/native 설정·hook inventory 확인을 구분하고 새 run-bound receipt를 발급했다. 준비 중 모델 호출은0회다.
- [x] 동결 runner로 최초1회만 실행하고 실제 thread·process argv·시각·원본 로그를 보존했다. CLI가 방출하지 않는 실효 model/cwd는 확인했다고 추정하지 않는다.
- [x] 공개 시작 snapshot25개 파일·기존 근거를 포함한1,230개 파일의 원본 bytes/hash·문서 링크338개·과거 판정 보존을 검증했다. 시작 기록을 커밋하며 실행 중 후보를 다시 호출하지 않는다.

완료 조건: 실제 최초 시작과 복구 가능한 현재 상태를 확인한다. 시작 작업의 완료는 제품 구현·평가 완료가 아니다. 최초 최대7,200초, 후속 최대3회 AND 누적7,200초를 유지한다. 종료 후 source·제출·원본 비용을 동결하고 정책·host·제품/RM를 평가한다. 업로드 가능한 genuine firmware가 있으면 같은 artifact를 COM3에서 평가한다.

후보에게 이전 Sol/다른 모델의 구현·관측·수정 방법을 제공하지 않는다. 운영자 구현 수정·실행 중 피드백·serial/flash를 하지 않는다. Sol 종료·Pro 회차 종료·Flash 보류와 각 원본 비용·판정·동결 ref를 보존한다.

[시작 근거](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r01/launch-20261006/native-start-observation.json)·
[새 사본 검증](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r01/launch-20261006/luna-preparation.json)·
[현재 설정 확인](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-luna-r01/launch-20261006/operator-launch-preflight/current-checks.json)을 연결했다.
Thread `01a10ec3-0ebc-75f1-8060-d2ee9aff0262`·candidate PID7052·launcher PID8376, receipt SHA-256 `44ba7ad2e5ad8c6f01784531cfbea792b783f58e1df4201cb2c350d9eff7204b`다.
독립 저장소의 준비 commit은 `d9579af28c8952b963454e9e2d32b8322d7ed472`다. Manifest branch label은 `experiment/openai/codex-cli/gpt-6-luna`이며 실제 local branch는 master로 구분한다. 다른 후보와 저장소·Git 이력을 공유하지 않는다.
