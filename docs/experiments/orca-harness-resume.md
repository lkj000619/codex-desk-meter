# 세션 중단 후 재개

사용자 요청으로 2026-10-08 작성. 토큰 세션 만료가 발생해도 같은 실험을 중복 실행하지 않고
남은 작업을 이어간다. 문서 보존은 진행 상황 복구이며 실행 프로세스를 자동 재시작하는 기능은 아니다.

## 먼저 읽을 파일

1. [현재 상태](next-comparison-readiness.md)
2. [계획의 체크리스트](../plans/2026-10-08-orca-harness.md)
3. [실험 식별자](../../experiments/orca-harness-20261008/context.json)
4. 각 역할 checkpoint: `docs/design/lcd/gemini/checkpoint.md`,
   `docs/design/lcd/sol61/checkpoint.md`, `docs/agent-runs/orca-luna/checkpoint.md`,
이후 구현자의 `docs/agent-runs/orca-{sol,flash}/checkpoint.md`.

직전 native runtime 관측은 `experiments/orca-harness-20261008/runtime-checkpoint.json`에
있다. 오래된 snapshot 대신 아래 명령으로 확인한다. 입력 57개 hash·branch·JSON 확인이
실패하거나 Orca 조회가 실패하면 이전 snapshot을 보존하고 오류를 표시한다.

```powershell
./scripts/checkpoint-orca.ps1 -VerifyOnly
./scripts/checkpoint-orca.ps1
```

branch: `lkj000619/experiment-orca-harness-20261008`
worktree: `C:/Users/이광진/orca/workspaces/codex-desk-meter/experiment-orca-harness-20261008`
Run: `run_c968c43361da`. 원래 coordinator handle은 context에 남기며 새 세션의 handle을
원래 handle로 가정하지 않는다. Task/Dispatch는 Orca 조회와 checkpoint에서 확인한다.

## 실행 확인 순서

현재 세션에서 `orca`를 선택하고 `orca skills get orchestration`으로 설치 버전의 가이드를 읽는다.
`orca status --json`과 `git status --short`, branch를 확인한다. 원래 입력을 지우거나 초기화하는
준비 helper를 다시 실행하지 않는다.

```powershell
orca orchestration run-use --id run_c968c43361da --json
orca orchestration task-list --run run_c968c43361da --brief --json
orca orchestration worker-list --run run_c968c43361da --include-remote --json
orca orchestration check --run run_c968c43361da --json
```

Run을 연결하는 새 coordinator는 이전 coordinator가 중단된 세션임을 확인한다.
live worker는 상태·메일을 확인하며 기다린다. `unverifiable`/timeout은 종료 증거가 아니다.
fleet의 `projection.liveness`와 `nextAction`을 따르고, 긍정적으로 failed/stopped로 확인된
동일 Task만 기존 Dispatch의 `--retry-of`로 이어간다. 실제 종료와 미보고가 확인되면 설치 버전의
recovery guide를 읽고 fencing/정리 후 재시도한다.

worker_done은 Task ID/Dispatch ID가 맞고 terminal report가 runtime에 수락되어야 완료다.
inbox Delivery의 모든 메시지·질문·소유권 조치를 처리한 후에만 ack한다. 수락된 worker를
다음 Task에 재사용하거나 release한다. 새 Run/Task로 실패·진행 상태를 덮어쓰지 않는다.

## 파일·검증·사용자 대기

- checkpoint와 실제 파일/diff를 대조한다. 부분 파일·불완전 JSON은 완료로 취급하지 않는다.
- native 모델 receipt·시험 결과·동결 hash를 확인하고 다음 필요한 검사만 재실행한다.
- GUI 6개가 완성되면 사용자에게 선택을 요청한다. 선택 전에 제품 GUI를 임의 확정하지 않는다.
- 업로드 여부는 날짜·COM port·동결 binary/hash·장치 수신·사용자 관측을 확인한다.
  문서의 예전 업로드 계획만으로 보드 상태를 단정하거나 다른 펌웨어를 자동 업로드하지 않는다.
- source/doc/비식별 결과는 coordinator가 체크포인트 commit으로 보존한다. 원본 개인 JSONL,
  auth/token/cookie/Dispatch capability는 Git에 넣지 않는다. 미커밋 source도 삭제하지 않는다.
- Orca reset·전체 flash 삭제·worktree 삭제는 재개 절차에 포함하지 않는다.

## 현재 다음 행동

2026-10-08 02:31 KST 체크포인트:

- OpenDesign 준비 `task_1a7eaeade56c` / `ctx_3827dfbe5be1`는 수락 완료다.
  viewer 원본 SHA-256은 `997514c7e099015531f64ab7e6fc267eecd8577f1379cfb7d06a386943d5b5f9`다.
- Gemini GUI `task_b4a978f1fe36` / `ctx_7cc34b44b75e`는 3개 후보·handoff 제출 수락 완료다.
  `worker-release` 결과는 `retained/external_terminal`, processAction=none이다.
  제출 완료와 독립 검증 통과를 구분한다.
- Sol 6.1 GUI `task_871ad3d94f9f` / `ctx_43a32c7bf49d`는 02:37 KST 제출 수락 완료다.
  `node docs/design/lcd/sol61/check.mjs`를 coordinator가 재실행해 3개 모두 통과했다.
  `worker-release` 결과는 `retained/external_terminal`, processAction=none이다.
- Luna 계약 검토 `task_c4c03e6d2c02`는 `ctx_a4f395e58ecc`로 같은 Task·같은 실제 Luna에 재연결했다.
  인터페이스 질문 `msg_1a0585d74a22`는 답변 `msg_5d56c1876c49`로 해결했으며 설계에 반영했다.
  이전 `ctx_85d922e4b68d`의 최종 turn은 보고서를 마쳤지만 coordinator가 잘못 안내한 worker
  `check --run` 때문에 `consumer_fenced` 후 worker_done 없이 끝났다. 최종 transcript와 native
  미제출 상태를 확인해 이전 attempt를 abandon하고 retry-of로 복구했다. 프로세스 종료나 파일
  삭제는 없었다. worker check/ack는 `--terminal <자신의 handle> --json`만 사용하며 `--run`을
  붙이지 않는다. 기존 완성 보고서를 다시 작성하지 않고 제출 절차만 마무리한다.
- GUI 독립 검증·비교 화면 `task_c0ecb13ae179`는 위 두 GUI와 Luna 보고 수락에 의존한다.
  세 보고 모두 수락 후 `ctx_28254a047a7d`로 시작했다. 같은 실제 Luna 터미널을 재사용했다.
  `ctx_a4f395e58ecc`의 요구 검토는 `msg_6760a8fcc0e4`로 수락 완료다.
  현재 browser 검증·비교 화면을 기다리고, 검증/필요 수정 후 사용자 선택을 받는다.

첫 native launch는 cmd.exe의 작은따옴표 처리 오류로 종료되어 원인·시도 ID를 보존했고,
PowerShell에서 같은 agent/model을 시작해 기존 Task에 retry-of로 연결했다.
모델 header와 실제 native 상태에서 Luna/AGY가 working인 것을 확인했다.
첫 재연결에서 자동 승인 옵션 누락이 확인되어 사용자의 명시적 요청을 반영했다.
권한 요청 중인 이전 두 전용 agent PID만 식별해 종료하고 기존 Dispatch를 fence했다.
이후 AGY `--dangerously-skip-permissions`, Codex
`--dangerously-bypass-approvals-and-sandbox`가 실제 argv에 있는 전용 PowerShell 터미널을
시작해 동일 Task에 재연결했다. 두 시작은 native turn_start=observed이며
이전 파일·실패 기록은 보존했다. 이후 모든 launch에도 이 옵션을 적용한다.
재개할 때 이 문장만 믿지 말고 live runtime와 checkpoint를 다시 확인한다.
AGY GUI의 실효 CLI는 1.3.1, Gemini 3.8 Flash Medium이며 모델은 argv/header로 확인했다.
Codex CLI는 0.159.2이며 Sol 6.1/Luna는 실제 header와 native hook에서 확인했다.
coordinator가 CLI를 설치하거나 업데이트한 것은 아니다. 버전 차이는 실행 기록으로 보존한다.
preview는 coordinator가 Python stdlib로 127.0.0.1:8289에 시작했다. HTTP 200 및 context의
Run/branch 일치로 새 checkout을 확인했다. 현재 PID는 context에 있으나 재개 시 다시 확인한다.
제품 구현·COM3 업로드는 아직 시작하지 않았다. 사용자에게 필요한 다음 결정은 6개 GUI 중 선택이다.
