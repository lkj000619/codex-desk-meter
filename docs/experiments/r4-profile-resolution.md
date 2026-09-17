# R4 profile 확정안 (2026-09-18 실측)

읽기 전용 실측(`--version`·`--help`)만 수행. 모델 호출·설치·실행 없음.
R10은 `not_authorized` 유지. 본 확정안은 draft이며, 모델 선택과
settings inventory 사용자 확인이 끝나야 R4가 닫힌다.

## 실측 결과

| 표면 | 실행 파일 | 버전 | 비고 |
|---|---|---|---|
| codex-cli | `C:\Users\이광진\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` (native) | 0.153.2 | `exec --json`, stdin `-` 또는 뒤첨부, `-m/--model` 지원 확인. **모델 2종(`sol`, `luna`)을 별도 엔트리로 테스트** |
| gemini-cli | 설치 파손 + 서비스 전환 (아래 참조) | **비교군 제외**. 개인 계정은 2026-06-18 이후 요청 중단. 후속 표면은 antigravity-cli |
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
- `model`·`reasoning`은 사용자가 표면마다 확정해야 한다. codex는 `sol`·`luna`
  2종을 별도 모델 엔트리로 테스트한다 (동일 surface, 모델만 다름. pilot는
  모델당 1회). opencode `opencode/muse-spark-1.3-contributor-free`는 1.18.31에서
  재확인됐다 (`evidence/opencode-models-20260918.log`).
- antigravity 모델 목록 원본은 `evidence/agy-models-20260918.log`에 보존했다.
  pilot 3종 ID는 사용자 확정 대기 중이다.
- `settings_inventory`의 skills/MCP/memory 등은 사용자 확인 전이라
  `operator-check-required`를 유지한다. `benchmark.py prepare`는 그대로 거부한다.
- gemini-cli는 draft를 작성하지 않았다. Google이 2026-05-19에 Gemini CLI →
  Antigravity CLI 전환을 발표했고, 2026-06-18부터 개인(Pro/Ultra/무료) 계정의
  Gemini CLI 요청이 중단됐다. 로컬 설치 파손(`dist/src`만 잔류)은 이 전환기의
  잔재로 보인다. Enterprise/API 키 계정이 아니면 재설치해도 실행 불가하므로,
  비교군은 antigravity-cli로 일원화한다. 근거:
  https://developers.googleblog.com/en/an-important-update-transitioning-gemini-cli-to-antigravity-cli/

## R4 종료 조건 (잔여)

1. 표면별 model/reasoning 사용자 확정 (codex `-m` 값 포함)
2. settings inventory 실측 기록 (builtin-only-v1 증거)
3. 위 2건 반영된 profile의 `prepare` 통과 + bundle hash 동결 (R1과 연계)
