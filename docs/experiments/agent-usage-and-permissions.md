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
| codex-cli | `sol`, `luna` | 기록된 모델 후보. 정확한 ID·설정을 profile에 확정하고 entitlement는 승인된 pilot에서 확인 |
| opencode-cli | `opencode/muse-spark-1.3-contributor-free` | `opencode models`에 존재 확인済み (2026-09-14 probe) |
| antigravity-cli | `gemini-3.8-flash-high/medium/low`, `gemini-3.1-pro-high/low`, `claude-opus-4-6-thinking` | `agy models` 목록 노출 관측; 계정 entitlement 확인 아님. effort 변형은 모델 ID에 포함됨 |

`sol`/`luna`는 OpenAI 내부 코드네임 계열로, `-m sol` 형태로 전달한다. 계정에
해당 모델 권한이 없으면 모델 측에서 거부할 수 있다. R4 pilot 전에는 모델 목록 노출과
slug/profile 설정을 확인하고, 실제 entitlement는 승인된 첫 pilot 결과로 판정한다.
`prepare`와 읽기 전용 `--help` 검사는 실제 모델 권한을 확인하지 않으므로 entitlement를
pilot-entry 조건으로 요구하지 않는다. 권한 확인용 가벼운 호출도 토큰을 쓰므로 별도 호출은
하지 않고 첫 pilot에서 결과를 관측한다.

## 2. 비대화형 사용법

### codex-cli (0.153.2)

```text
codex exec --json -m <model> -
```

위는 runner argv의 설명이다. `prompt.txt`의 UTF-8 bytes는 runner가 stdin으로
전달한다. PowerShell의 `< prompt.txt` 리다이렉션이나 수동 prompt 전달 예시가 아니다.

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

```text
<native-exe> run --pure --format json --model <provider/model>
```

위 argv에 대한 UTF-8 stdin 전달은 runner가 담당한다.

- `run [message..]`: positional message는 비워두고 stdin 파이프만 제공한다.
  stdin이 메시지로 전달됨을 probe로 확인했다 (`METER_STDIN_PROBE_OK`).
- `--format json`: `step_finish` 이벤트의 `part.tokens`를 계측에 사용한다.
- `--pure`: 외부 플러그인 비활성화. OS 격리가 아니므로 한계로 기록한다.
- `--variant`: reasoning effort 변형 (예: high/max/minimal). 비교군 고정값으로 기록.
- npm `.ps1` shim이 아닌 native exe 직접 호출. argv에 shell 문자열을 조합하지 않는다.
- 근거: 로컬 `opencode run --help` 실측, `opencode-preflight-check.md`,
  `opencode-stdin-probe-20260914.md`.

### antigravity-cli (agy 1.2.11 관측; 현재 profile 검증은 별도)

AGY 자식 프로세스에는 `AGY_CLI_DISABLE_AUTO_UPDATE=true`를 전달하고 실행 직전 버전과
바이너리 hash를 다시 확인한다. 2026-09-25 `agy models` 호출 중 1.2.9에서 1.2.11로
자동 갱신된 사례가 있어, 다른 AGY 프로세스의 갱신 여부도 확인해야 한다.

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
- 근거: 로컬 `agy --version`·`agy --help` 실측
  ([2026-09-25 CLI 기록](evidence/agy-cli-20260925-v1211.txt))과 `agy models` 출력
  ([2026-09-25 inventory](evidence/agy-local-inventory-20260925.md)). 이 목록은 모델 가용성
  확인이며 계정 entitlement 증거는 아니다. protocol 의미는
  [Google Antigravity headless mode 문서](https://www.antigravity.google/docs/cli/headless/)를 따른다.

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
| antigravity-cli | terminal `result` event의 `usage` | input/output; `total=input+output`; `cached=cache_read_tokens`, `reasoning=thinking_tokens`, `provider_total=total_tokens` 보존 | terminal result 또는 해당 usage 필드가 없으면 해당 값을 null + 사유 |
| gemini-cli | 미구현 | 전부 null + 사유 | input/output/total 전부 |

- AGY 출력은 `init` 1개, `step_update` 0개 이상, 마지막 `result` 1개다. token usage는
  누적값이므로 step별 usage를 더하지 않고 terminal `result.usage`만 사용한다.
- 현재 parser 지원은 synthetic stream 사례로 검증하는 사전 계측이다. 실제 AGY usage와
  permission soft-denial 결과는 첫 pilot의 raw stream/stderr를 통해 사후 판정하며, 그 결과를
  해당 pilot의 선행조건으로 삼지 않는다. 누락·실패 데이터는 0으로 꾸미지 않고 null과 사유,
  원본 로그로 보존한다.
- terminal `SUCCESS`라도 완료된 tool step의 `tool_info.error.type`이 permission/approval
  거부를 나타내면 runner는 `environment_failed`로 기록한다. 이 경우에도 terminal usage와
  실패 도구 수를 원본에서 추출한다. CLI가 stderr에만 거부를 알리거나 다른 오류 유형을
  사용하는 경우까지 자동 검출했다고 주장하지 않으며, pilot 후 stdout/stderr를 검토한다.
- AGY `tool_calls`는 완료된(`DONE`) 도구 step 수이며, `failed_commands`는 그중
  `run_command` step의 명시적 `tool_info.error` 수다. 이는 모든 도구 승인 거부나 사용자
  개입을 완전하게 세는 계측으로 검증된 것이 아니다.
- OpenCode의 `command_metrics`는 아직 null이다. Codex와 AGY는 각자의 event 정의로
  계측하며 호출 수를 표면 간 직접 비교하지 않는다.
- 미측정 값을 0으로 대체하지 않는다. `null` + 사유로 기록한다.
- 근거: `scripts/benchmark.py` `inspect_antigravity_stream()`·`telemetry()`·
  `command_metrics()`, synthetic stream cases in `scripts/tests/test_benchmark.py`.
  테스트 통과는 실제 provider 실행 증거가 아니다.

## 5. 실행 중 도구 승인 대기 설정

이 절은 R10 실행 승인을 생략하는 방법이 아니다. 승인된 run 안에서 도구 호출의
대기·허용 조건을 고정하기 위한 기록이다.

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

- Google 문서상 headless 기본 permission mode는 `request-review`다. terminal/도구
  승인을 요청할 수 없는 환경에서는 해당 도구가 soft-deny되어도 실행이 계속되고 exit
  code가 0일 수 있다. 성공 exit code만으로 요청된 도구 작업이 수행됐다고 판정하지 않는다.
- 실행 전에는 선택 model, mode와 permission policy를 settings/profile 근거로 고정한다.
  runner는 execute 중 AGY stream의 `init.model`과 `init.permission_mode`가 각각 profile의
  `model`, `approval_policy`와 일치해야 결과를 수락하며, 값 누락·불일치는 process exit 0이어도
  거부한다. 실제 stream 값과 soft-denial 결과는 첫 pilot에서 판정한다.
- 첫 pilot은 필요한 명령만 사전 허용하는 정책을 사용한다. 현재 global
  [`settings.json` inventory](evidence/agy-local-inventory-20260925.md)에는 14개의 `command`와
  100개의 `unsandboxed` allow rule이 관측되었으나, 이는 실제 적용 범위나 미래 실행의 effective
  policy를 증명하지 않는다. 승인된 checkout에서 필요한 명령을 실제로 확인해 exact rule을
  고정하고 기존 global rule의 범위·영향을 재검토한다. 구체 허용 목록은 추정으로 쓰지 않는다.
- 공식 [CLI permissions 문서](https://antigravity.google/docs/permissions?tab=cli)는
  `permissions.allow` 설정과 Deny > Ask > Allow 우선순위를 정의한다. Windows PowerShell은
  명령을 단어로 안전하게 나눌 수 없는 경우 full-line 또는 `regex:` 매칭이 필요할 수 있다.
- `--dangerously-skip-permissions`는 문서상 모든 도구를 자동 승인한다. 비교군에 사용할
  경우 profile에 이를 명시하고 격리 조건 및 전체 허용의 위험을 검토해야 한다. 첫 pilot의
  선택 정책에서는 이 flag를 candidate argv에 넣지 않는다. 현재 candidate의 유효 권한
  설정이나 실제 실행 동작은 검증되지 않았다.
- `--mode accept-edits|plan`: 실행 모드 고정. 비교군에 기록한다.
- MCP·plugin은 `agy mcp`·`agy plugin`으로 비활성화하고 목록 증거를 남긴다.
- 공식 근거: [Permissions in headless mode](https://www.antigravity.google/docs/cli/headless/).
  문서 설명은 실제 설치본의 effective settings 또는 permission 결과를 입증하지 않는다.

### 공통 주의

- 무승인 옵션은 실행 중 대기 시간을 0으로 만들지만, 실행 시간 계측에서는
  승인 대기가 있었다면 포함하는 것이 원칙이다. 조건이 다르면 별도 비교군이다.
- 권한 완화는 각 run의 manifest·profile·receipt에 버전을 포함해 기록한다.
- 자격증명·API 키를 argv·profile·prompt·로그에 넣지 않는다.
