# OpenCode stdin 전달 probe — 2026-09-14

- Branch: `experiment/opencode/cli/muse-spark-1-3-contributor-free`
- Model: `opencode/muse-spark-1.3-contributor-free` (OpenCode 1.18.30, native exe)
- 목적: `docs/experiments/opencode-preflight-check.md`의 잔여항목
  "Stdin delivery for the full candidate task remains unverified" 중
  stdin 경로 자체가 메시지로 전달되는지 확인. 후보 프롬프트는 전달하지 않음.

## 명령 (빈 임시 디렉터리에서 실행, 저장소 밖)

```powershell
"Reply with exactly METER_STDIN_PROBE_OK and nothing else." | & "<native-opencode.exe>" run --pure --format json --model opencode/muse-spark-1.3-contributor-free
```

- positional message 없음. `run [message..]` 기본값 `[]` 상태에서 stdin 파이프만 제공.
- 실제 실행 파일: `<APPDATA>\npm\node_modules\opencode-ai\bin\opencode.exe`
  (npm `.ps1` shim이 아닌 native exe 직접 호출 — profile argv 조건과 동일).

## 결과

- Exit 0. 모델이 `METER_STDIN_PROBE_OK`를 그대로 반환 → stdin이 메시지로 전달됨을 확인.
- `step_finish` 이벤트 1건 (`type: step_finish`, part `type: step-finish`):
  input 8499 / output 17 / reasoning 40 / total 8797 / cache.read 241 / cache.write 0.
- `scripts/benchmark.py`의 `capture()`는 prompt를 stdin으로 전달하고,
  opencode profile argv에 positional이 없으므로 이 경로 그대로 사용 가능.
  telemetry 파서가 기대하는 최상위 `type == "step_finish"` 형태와 일치.

## 경계

- 후보 공통 프롬프트 전달·`benchmark.py run`·COM3·펌웨어 작업이 아님.
  R10은 여전히 `not_authorized`이며 run ID를 예약하지 않았음.
- Tool deny 없이 실행한 단순 문자열 응답 probe이며, 빈 임시 cwd에서 수행.
- Sandbox receipt(`read_isolation`, `idf_build`, `network_policy`,
  `settings_inventory`)와 E2E archive 정규화는 여전히 미완료 잔여항목.

## Access policy update (2026-09-14)

This report preserves the checks and evidence recorded at review time.
Its mandatory OS-sandbox/read-isolation gate is superseded by
[isolation-policy.md](isolation-policy.md): `prompt-and-log` is the default;
Docker/VM is optional. Host toolchain checks plus prompt scope, activity logging,
network/settings evidence can satisfy the revised R5 preflight requirement.
OS read isolation is `not_enforced` in the default mode. Lack of a Docker/sandbox
receipt alone does not exclude a run from quantitative comparison.
No preflight pass, candidate authorization or hardware evidence is granted by
this policy update. Prior measured results and historical limitations are unchanged.
