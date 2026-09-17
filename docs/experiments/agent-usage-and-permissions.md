# 에이전트 사용법·계측·권한 옵션

실험 대상 표면을 runner로 실행하기 위한 조작법 정리. 2026-09-18 실측과 공식
문서를 근거로 하며, 미확인 항목은 `미확인`으로 표기한다. 본 문서를 읽는 것은
실행이 아니며, R10 승인 전에는 어떤 에이전트도 실행하지 않는다.

> **gemini-cli 비교군 제외.** Google이 2026-05-19에 Gemini CLI → Antigravity CLI
> 전환을 발표했고, 2026-06-18부터 개인(Pro/Ultra/무료) 계정의 Gemini CLI 요청이
> 중단됐다. 로컬 설치 파손(`dist/src`만 잔류)은 이 전환기의 잔재로 보인다.
> Enterprise/API 키 계정이 아니면 실행 불가하므로 기본 비교군은 antigravity-cli로
> 일원화한다. 근거:
> https://developers.googleblog.com/en/an-important-update-transitioning-gemini-cli-to-antigravity-cli/

## 1. 대상 모델 (사용자 지정)

| 표면 | 모델 | 확인 상태 |
|---|---|---|
| codex-cli | `sol`, `luna` | 계정 측 모델 ID. `-m` 값으로 전달, entitlement는 prepare 시 확인 |
| opencode-cli | `opencode/muse-spark-1.3-contributor-free` | `opencode models`에 존재 확인済み (2026-09-14 probe) |
| antigravity-cli | `gemini-3.8-flash-high/medium/low`, `gemini-3.1-pro-high/low`, `claude-opus-4-6-thinking` | `agy models` 실측 확인 (2026-09-18). effort 변형은 모델 ID에 포함됨 |

`sol`/`luna`는 OpenAI 내부 코드네임 계열로, `-m sol` 형태로 전달한다. 계정에
해당 모델 권한이 없으면 실행기가 아니라 모델 측에서 거부하므로, prepare 단계에서
짧은 `--help` 수준이 아닌 실제 권한 확인이 필요하다. 권한 확인용 가벼운 호출도
토큰을 쓰므로 사용자 승인 후 pilot에서 수행한다.

## 2. 비대화형 사용법

### codex-cli (0.153.2)

```powershell
codex exec --json -m <model> - < prompt.txt
```

- `exec`: 비대화형 실행. 진행 상황은 stderr, 최종 메시지는 stdout, `--json`이면
  stdout이 JSONL 이벤트 스트림이 된다. runner는 이 스트림을 raw로 보존한다.
- stdin `-`: 프롬프트 전체를 stdin으로 전달. prompt 인자와 파이프를 함께 쓰면
  파이프 내용은 `<stdin>` 블록으로 덧붙는다. runner는 prompt.txt 전체를 stdin
  UTF-8 bytes로 전달하므로 `-` 형태를 사용한다.
- `--ephemeral`: 세션 rollout 파일 미저장. 반복 간 상태 오염 방지에 사용 검토.
- `-o/--output-last-message`: 최종 메시지를 파일에 기록. runner는 raw 로그를
  별도 수집하므로 필수는 아니다.
- Git 저장소 안에서 실행해야 한다 (`--skip-git-repo-check`는 사용하지 않는다).
- 근거: [Non-interactive mode](https://developers.openai.com/codex/noninteractive/),
  로컬 `codex exec --help` 실측.

### opencode-cli (1.18.31)

```powershell
& "<native-exe>" run --pure --format json --model <provider/model> < prompt.txt
```

- `run [message..]`: positional message는 비워두고 stdin 파이프만 제공한다.
  stdin이 메시지로 전달됨을 probe로 확인했다 (`METER_STDIN_PROBE_OK`).
- `--format json`: `step_finish` 이벤트의 `part.tokens`를 계측에 사용한다.
- `--pure`: 외부 플러그인 비활성화. OS 격리가 아니므로 한계로 기록한다.
- `--variant`: reasoning effort 변형 (예: high/max/minimal). 비교군 고정값으로 기록.
- npm `.ps1` shim이 아닌 native exe 직접 호출. argv에 shell 문자열을 조합하지 않는다.
- 근거: 로컬 `opencode run --help` 실측, `opencode-preflight-check.md`,
  `opencode-stdin-probe-20260914.md`.

### antigravity-cli (agy 1.2.5, 후속 실측)

```powershell
agy --print --input-format text --output-format stream-json --print-timeout 120m --model <model-id>
```

- `--print` (alias `-p`, `--prompt`): 단일 프롬프트 비대화형 실행.
- runner는 prompt.txt를 일반 UTF-8 bytes로 stdin에 전달하므로 입력은 `text`다.
  출력만 `stream-json`으로 지정한다. `stream-json` 입력은 NDJSON 메시지가
  필요하므로 현재 runner와 호환되지 않는다. 위 명령의 stdin 전달은 runner가 담당한다.
- `--model`: `agy models`의 ID 그대로 사용 (예: `gemini-3.8-flash-high`).
- `--effort low|medium|high`: 모델 ID에 effort가 포함된 경우 중복 지정 금지.
  ID(`gemini-3.8-flash-high`)와 플래그(`--effort`) 중 하나를 비교군에 고정한다.
- `--print-timeout`: 기본 5m0s 대신 pilot draft는 `120m`으로 고정한다.
  runner도 7200초 hard timeout을 적용하며 먼저 종료된 사유를 기록한다.
- `--sandbox`: 터미널 제한 sandbox 실행. prompt-and-log 기본모드에서는 설정값으로만
  기록하고, external-sandbox 선택 시 내부 검증을 수행한다.
- 근거: 로컬 `agy --help`·`agy models` 실측 (2026-09-18).

## 3. 작업 소요시간 확인

runner(`scripts/benchmark.py run`)가 기록한다. 에이전트 자체 보고를 믿지 않는다.

- `started_at`: 공통 prompt 전달 UTC 시각 (실행기가 기록)
- `ended_at`: 에이전트 종료 UTC 시각 (실행기가 기록)
- 경과 시간: 단조 시계(`time.monotonic`) + UTC 차이 교차 검사. 대기·승인·다운로드 포함
- hard timeout 120분. timeout·중단은 자식 프로세스까지 종료 후 부분 산출물 보존
- 준비 시간·운영자 실물 평가 시간은 별도 기록 (실행 시간에 합치지 않음)

## 4. 토큰 사용량 확인

원본 이벤트를 raw stdout에서 파싱하며, 제공자 정의를 그대로 보존한다.
서로 다른 제공자의 토큰을 하나의 효율 순위로 합치지 않는다.

| 표면 | 원본 이벤트 | 수집 필드 | 미제공 |
|---|---|---|---|
| codex-cli | `turn.completed`의 `usage` | input/output/cached 합산, total=input+output (cached 중복 제외) | reasoning |
| opencode-cli | `step_finish`의 `part.tokens` | input/output/reasoning/total 합산, cache.read 별도 | tool 호출 수 (null) |
| antigravity-cli | 미구현 | 전부 null + 사유 | input/output/total 전부 |
| gemini-cli | 미구현 | 전부 null + 사유 | input/output/total 전부 |

- `command_metrics`(도구 호출·실패 수)는 codex만 지원. 나머지는 null이다.
- 미측정 값을 0으로 대체하지 않는다. `null` + 사유로 기록한다.
- 근거: `scripts/benchmark.py` `telemetry()`·`command_metrics()`,
  `test_benchmark.py` (gemini total null 단언 포함).

## 5. 승인 없이 실행하기 위한 권한 옵션

실험 정책(`builtin-only-v1`, `prompt-and-log`)과 별개로, 각 도구가 중간에
멈추지 않으려면 아래 승인을 사전에 고정하고 profile·receipt에 기록한다.
어디까지나 동일 비교군에 동일 조건으로 적용하며, 완화된 권한을 기본값처럼
기록하지 않는다.

### codex-cli

- `-s/--sandbox <mode>`: `workspace-write` (편집 허용) 또는
  `danger-full-access` (통제된 격리 환경에서만). 기본 read-only sandbox에서는
  빌드·파일 생성이 막혀 run이 중단된다.
- `--approve-for-me`: 승인을 workspace-write sandbox 자동 검토로 전달.
- `--dangerously-bypass-approvals-and-sandbox`: 모든 확인 생략. 외부 격리된
  환경에서만 사용하고, 사용 사실을 manifest에 기록한다.
- `--full-auto`는 deprecated이므로 사용하지 않는다.
- MCP·skills는 비교군 조건(`builtin-only-v1`)에 맞춰 비활성화하고 비활성화
  증거를 남긴다. `codex exec`는 MCP 초기화 실패 시 종료되므로, 비활성화한
  서버가 `required`로 남아 있지 않은지 확인한다.

### opencode-cli

- `run --auto`: 명시적 deny가 아닌 승인을 자동 승인. TUI의 auto-approve와 동일 효과.
- `opencode.json` `permission`으로 도구별 allow/ask/deny 고정. 예:
  `{ "permission": { "bash": { "*": "ask", "git *": "allow", "rm *": "deny" } } }`
  deny는 `--auto`에서도 강제된다.
- 비교군 실행에는 `run --pure`를 유지하고, permission 파일 해시를 profile에 기록한다.
- 근거: [Permissions](https://opencode.ai/docs/permissions/), 로컬 help 실측.

### antigravity-cli

- `--dangerously-skip-permissions`: 전 도구 승인 자동 통과. runner argv 사용 시
  실제 파싱 검증을 pilot 전에 별도 수행한다 (2026-09-16 Orca launcher 인자
  전달 실패 사례가 있어, agy 자체 문제가 아닌 전달 경로 문제도 의심한다).
- `--mode accept-edits|plan`: 실행 모드 고정. 비교군에 기록한다.
- MCP·plugin은 `agy mcp`·`agy plugin`으로 비활성화하고 목록 증거를 남긴다.

### 공통 주의

- 무승인 옵션은 실행 중 대기 시간을 0으로 만들지만, 실행 시간 계측에서는
  승인 대기가 있었다면 포함하는 것이 원칙이다. 조건이 다르면 별도 비교군이다.
- 권한 완화는 각 run의 manifest·profile·receipt에 버전을 포함해 기록한다.
- 자격증명·API 키를 argv·profile·prompt·로그에 넣지 않는다.
