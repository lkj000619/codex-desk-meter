# 에이전트 실행 명령 템플릿

> 현재 명령은 이전 시간 포함 run ID와 run별 브랜치를 사용하는 참고 예시다.
> [새 운영 기준](benchmark-management.md)의 명명·격리·계측 전환이 완료되기 전에는
> 이 문서를 따라 실험을 시작하지 않는다. 아래 코드 블록은 새 표준의 실행 절차가 아니다.

이 문서는 [AI 에이전트 비교 실험 프로토콜](agent-experiment-protocol.md)의
실행면을 실제 명령으로 옮긴 예시다. `<...>` 값은 run manifest에 기록한 값으로
치환한다. 실행 전에는 `new-experiment-run.ps1`로 결과 디렉터리와 해시를 먼저
만든다.

## 공통 준비

```powershell
$run = '20260911T120000Z-codex-pilot'
$worktree = "C:\src\codex-desk-meter-$run"

git worktree add -b "experiment/$run" $worktree <baseline-commit>
Set-Location $worktree
$prompt = (Get-Content -Raw experiments\prompts\version-2-agent-task.md).Replace('<run-id>', $run)
.\scripts\new-experiment-run.ps1 `
  -Provider openai -Product codex-cli -AgentVersion 0.153.2 `
  -Model <model-id> -Reasoning <reasoning-level> -Interface cli `
  -NetworkMode offline-fixture -Port COM3 -HardwareSlot desk-meter-1 `
  -RunId $run -Branch "experiment/$run" -Worktree $worktree
```

manifest의 `started_at`은 아래 에이전트 명령을 실제로 전달하는 순간으로
수정한다. `<run-id>`를 prompt에 넣을 때를 제외하고 prompt 본문은 바꾸지 않는다.

## Codex CLI

현재 기준 확인 버전은 `codex-cli 0.153.2`다. `--json` stdout은 명령 로그로
보존하고 마지막 메시지는 별도 파일로 저장한다.

```powershell
Set-Location $worktree
$prompt |
  codex exec -C $worktree -m <model-id> -s workspace-write `
    --json -o "results\$run\codex-last-message.md" - |
  Tee-Object -FilePath "results\$run\commands.jsonl"
```

실물 플래시가 필요한 명령은 운영자 승인 후 별도 단계에서 실행한다. 전체 플래시
삭제 옵션은 사용하지 않는다.

## Gemini CLI

Gemini CLI는 동일 worktree에서 비대화형 prompt와 `stream-json` 출력을 사용한다.
실행 전 `gemini --version`을 확인해 manifest에 기록한다.

```powershell
Set-Location $worktree
gemini --prompt $prompt --model <model-id> `
  --output-format stream-json |
  Tee-Object -FilePath "results\$run\commands.jsonl"
```

`--prompt`는 비대화형 실행을 시작한다. 추가 질문이 필요한 경우에는 같은
문구·순서로 별도 입력을 기록한다. 자동 승인(`--yolo`)은 기본 비교 조건으로 사용하지 않는다. 토큰과
도구 시간을 수집해야 하는 run에서는 Gemini CLI telemetry를 로컬 파일 또는
고정 OTLP collector로 보내고 `logPrompts` 설정을 manifest에 기록한다.

## Antigravity

Antigravity CLI/IDE는 설치 버전과 승인·터미널·파일 시스템 정책이 결과에 직접
영향을 준다. 실행 전 다음을 기록한다.

```powershell
agy --version
agy --help > "results\$run\agy-help.txt"
```

CLI가 비대화형 prompt와 JSON 또는 로그 출력을 지원하는지 해당 설치 버전의
help에서 확인한 뒤, 지원되는 동일 worktree 명령을 사용한다. IDE를 사용할
때는 agent panel의 prompt, 승인 클릭, terminal 정책, 생성 walkthrough와 화면
기록을 함께 보존하며 CLI run과 같은 통계에 섞지 않는다.

## ChatGPT 웹

일반 ChatGPT 웹 대화는 이 실험의 기본 비교면이 아니다. 로컬 worktree, COM3,
터미널 승인과 provider token telemetry를 동일하게 제공하지 않기 때문이다.
사용할 경우 `interface: web`인 별도 탐색군으로 기록하고, 로컬 파일을 실제로
수정·빌드한 시간과 웹 대화 시간을 합치지 않는다.

## OpenCode

대상 브랜치는 `experiment/opencode/cli/<model>`이다. 결과는
`results/YYYYMMDD-opencode-cli-<model>-rNN/`에 보관한다.
정확한 설치 버전의 비대화형 입력·사용량 출력·승인·sandbox 지원을 확인한 뒤
실행 어댑터를 작성해야 한다. 모델 제공자와 실제 모델 ID, 라우팅·fallback 정책을
별도로 기록한다. 현재 문서에는 검증된 OpenCode 실행 명령이 없다.

## 종료 기록

에이전트가 종료한 뒤 다음을 수행한다.

```powershell
git -C $worktree status --short
Get-ChildItem "results\$run" -Recurse -File | Select-Object FullName,Length
. .\scripts\activate-idf.ps1
python scripts\validate-experiment-result.py `
  --manifest "results\$run\run-manifest.json" `
  --result "results\$run\hardware-feature.json"
```

결과 파일이 아직 완성되지 않았다면 validator를 억지로 통과시키지 말고
`not_run`, `blocked` 또는 `timeout` 상태와 사유를 기록한다.
