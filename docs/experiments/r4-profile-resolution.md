# R4 profile 확정안 (2026-09-18 실측)

읽기 전용 실측(`--version`·`--help`)만 수행. 모델 호출·설치·실행 없음.
R10은 `not_authorized` 유지. 본 확정안은 draft이며, 모델 선택과
settings inventory 사용자 확인이 끝나야 R4가 닫힌다.

## 실측 결과

| 표면 | 실행 파일 | 버전 | 비고 |
|---|---|---|---|
| codex-cli | `C:\Users\이광진\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` (native) | 0.153.2 | `exec --json`, stdin `-` 또는 뒤첨부, `-m/--model` 지원 확인 |
| gemini-cli | 설치 파손 (`@google/gemini-cli`에 package.json 없음, bin shim 없음, `dist/src`만 잔류) | 미확인 | 재설치 후 `--version`/`--help` 재측정 필요 |
| antigravity-cli | `C:\Users\이광진\AppData\Local\agy\bin\agy.exe` | 1.2.4 | `--print`·`--input-format stream-json`·`--output-format stream-json`·`--model`·`--sandbox`·`--print-timeout` 확인 |
| opencode-cli | `C:\Users\이광진\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe` (native) | 1.18.31 (기존 profile 1.18.30에서 변경) | `run --pure --format json --model` + stdin 전달 probe 통과済み |

## Orca launcheraser 주의 (측정 사실)

`agy --help`에는 `--dangerously-skip-permissions`가 존재한다. 2026-09-16 Orca
자동 dispatch 실패(`unexpected argument "'--dangerously-skip-permissions'"`)는
인자가 따옴표 포함 형태로 전달된 것으로 보이며, agy 자체 미지원이 아니다.
runner argv에 해당 플래그를 넣을 경우 실제 파싱 검증을 pilot 전에 별도 수행한다.

## Draft profiles

`experiments/config/verified-profiles-draft/*.draft.json` 3종을 작성했다.
공통 규칙:

- 측정된 실행 파일·버전·argv 골격은 기입, `{model}`은 사용자 선택 자리 표시자다.
- `model`·`reasoning`은 사용자가 표면마다 확정해야 한다. opencode는 기존 기록
  `opencode/muse-spark-1.3-contributor-free`가 후보이나 재확인이 필요하다.
- `settings_inventory`의 skills/MCP/memory 등은 사용자 확인 전이라
  `operator-check-required`를 유지한다. `benchmark.py prepare`는 그대로 거부한다.
- gemini-cli는 설치 파손으로 draft를 작성하지 않았다. 복구 명령:
  `npm install -g @google/gemini-cli` 후 `--version`·`--help` 재측정.

## R4 종료 조건 (잔여)

1. 표면별 model/reasoning 사용자 확정 (codex `-m` 값 포함)
2. settings inventory 실측 기록 (builtin-only-v1 증거)
3. gemini-cli 재설치 + draft 작성
4. 위 3건 반영된 profile의 `prepare` 통과 + bundle hash 동결 (R1과 연계)
