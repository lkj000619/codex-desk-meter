# AGY launch review — 2026-09-25

## 판정

현재 판정은 `BLOCKED / NOT_AUTHORIZED`다. 사용자 결정은 유지한다.

- Q1: 기존 6종 비교 계획 유지.
- Q2: 검토 후 local baseline commit/tag 생성 승인.
- Q3: 첫 pilot을 `antigravity-cli / gemini-3.8-flash-medium`으로 바꾸고 옵션 A(COM3
  flash 및 실물 평가)를 선택.

Q3는 R10 실행 인가가 아니다. Luna 감사 단계에서는 모델/provider 호출, prompt 실행,
serial 포트 open, COM3 flash, 새 `prepare`, commit/tag/push를 수행하지 않았다.

## Identity와 날짜

감사 시작 시 저장소는 clean `main`이었고 HEAD는
`a36747ab2f7ac50676343b3b53517c8491d54b03`였다. 선택 baseline ref
`benchmark-v2-baseline-20260923`은 annotated tag이며 peeled commit은
`9ef945efd9d6c2c4b4eedca75eccc9f280b3aced`다. HEAD는 이 baseline보다 5 commits
뒤에 있으며, candidate/evidence 보완은 baseline snapshot에 자동으로 포함되지 않는다.
Luna 감사 작성 시 작업 트리는 수정 파일 때문에 dirty였고, 이를 새 baseline으로
동결하지 않았다. 이후 저장 상태는 `git status`로 확인한다.

보존된 외부 run directory는
`C:\Espressif\benchmark-runs\20260924-antigravity-cli-agy-flash-medium-r01`이다.
manifest는 `status=prepared`, `base_commit=9ef945efd9d6c2c4b4eedca75eccc9f280b3aced`,
old semantic profile hash `e9b4bca27b82c8cfc2c49f914862835a2fe31b13dd0d036f6f1362012ecf94d6`을
기록한다. `benchmark.py execute`는 run ID의 KST 날짜가 오늘과 다르면
`prepared on a different date; reserve a new run`으로 차단하므로 2026-09-25에는
이 ID를 실행할 수 없다. candidate와 receipt도 정정되어 old profile/receipt hash와
더 이상 일치하지 않는다. 이 예약 ID와 checkout은 삭제하거나 재사용하지 않는다.

## 관측 evidence

| Artifact | SHA-256 | 관측 범위 |
|---|---|---|
| [`agy-preflight-20260924.txt`](evidence/agy-preflight-20260924.txt) | `3bd4294e5f56946c48f76b877457a6fe92c85b418eaeb61804f6c1f3d6874b00` | `agy --version`=`1.2.9`, no MCP servers configured, no imported plugins; memory/cache/routing은 CLI에서 직접 관측되지 않는다는 명시 |
| [`agy-cli-20260925.txt`](evidence/agy-cli-20260925.txt) | `cc5a85106dda4bf90e4f5b7f1d5ac2c3b676c4a7cd353f552da8755d93b4a6ff` | executable path/hash, `--version`, exact `--help`, MCP/plugin 목록 |
| [`agy-gemini-3.8-flash-receipt.json`](evidence/agy-gemini-3.8-flash-receipt.json) | `65b764715e0456fb76a7d9f6d9b4d7cbb35470260c6e8e3b019e7f81fdae03d9` | corrected blocked receipt; evidence map and profile/base bindings |

The observed executable is `C:\Users\이광진\AppData\Local\agy\bin\agy.exe` with binary
SHA-256 `6efbd9828df5d0f44d56cb5fd770d87387f40eb364360b06bfbeba7c76f89bec` and version
`1.2.9`. Help confirms `--disable-slash-commands`, `--effort`, `--model`,
`--input-format`, and `--output-format`. It does not establish model entitlement, effective
memory/cache/routing/user-instruction settings, builtin-only enforcement, approval behavior,
network policy, prompt scope, activity logging, or telemetry. Empty local MCP/plugin lists
are observations at capture time, not proof that extensions are disabled for a future run.

## Corrections

The candidate profile now has semantic SHA-256
`075f23c4ebb10c87b0d5bd54c86c9c03dd4ed1e21de44283b1cd65eb7c8caa84` and byte SHA-256
`e659219fad1e1981c9ba39d978ed5eaf9f63f25ca4a489fe040a3af1f3bbf549`. The model ID
`gemini-3.8-flash-medium` carries the selected effort variant, so no separate `--effort`
flag is passed. Although help exposes `--disable-slash-commands`, it disables all skill
expansion and is stricter than the `builtin-only-v1` condition that retains built-ins; it is
therefore not adopted as equivalent enforcement. The copied Codex-only
`cli --ask-for-approval never` string was removed; AGY approval behavior remains `unverified`
because help shows no equivalent flag.

Unsupported claims about cleared memory/user instructions, disabled cache, direct routing,
and verified builtin-only enforcement were replaced by explicit `unverified` statements.
The profile is schema-valid but `validate_resolved_profile` intentionally rejects it until
an operator supplies evidence-backed values.

The receipt is bound to base commit
`9ef945efd9d6c2c4b4eedca75eccc9f280b3aced` and the corrected semantic profile hash. Its
evidence hashes match the two files above. Checks are recorded as follows:

| Check | Status | Reason |
|---|---|---|
| `idf_build`, `compiler`, `ninja`, `git`, `temp_write` | `not_observed` | The AGY evidence files do not contain these host checks. |
| `network_policy`, `prompt_scope`, `activity_logging` | `not_observed` | No corresponding effective-policy or activity evidence was captured. |
| `settings_inventory` | `blocked` | The raw transcript explicitly leaves memory/cache/routing unobservable; effective enforcement is not proven. |
| `read_isolation` | `not_enforced` | `prompt-and-log` policy does not claim OS read isolation. |
| `pilot_pass` | `false` | No pilot was executed or reviewed. |

The receipt therefore fails closed. It must not be treated as an executable preflight pass.

A read-only recomputation of `input_bundle_hashes` against the selected baseline snapshot
(without reserving a run ID) produced:

```text
prompt_sha256=f99d708ca9f3bdfc2134942c44e30b6c14bb7a098fe36f75ad5472c8210f4a77
config_sha256=f80d88b527c36f4ca591926be3842983fd61afa6ace517e6c31cf0ab197b337f
fixture_sha256=0a2964266df53a641dda4b4e9d460e2ffe990bfb38c6d40e32556610bbe42eec
schema_sha256=971a50e010d58a5c82f89dad5af9c99c6520130e63a96987ddc8e87e93a4bc79
evaluation_criteria_sha256=c3dd931a1e41ea3f74d2ae5f51701ff8545dcb2dbf4d2240849ae25dad8ce30e
profile_sha256=075f23c4ebb10c87b0d5bd54c86c9c03dd4ed1e21de44283b1cd65eb7c8caa84
input_bundle_sha256=ad574cbaacf93d876a0b4c2007e2065d6a2e164dff23f078abd213e377fd5389
```

This hash recomputation records identity only; it does not override the blocked profile
resolver or receipt gate.

## Offline validation

- `git rev-parse 'benchmark-v2-baseline-20260923^{commit}'` resolved to the selected
  `9ef945e...` commit; working-tree state was read before edits.
- `agy --version`, `agy --help`, `agy mcp list`, and `agy plugin list` exited 0. No model
  or provider command was invoked.
- `runner-profile.schema.json` validation passed. `validate_resolved_profile` and
  `benchmark.py check --baseline benchmark-v2-baseline-20260923 --profile ...agy...` both
  block on the intentional unresolved marker.
- The preserved AGY run manifest passes `run-manifest.schema.json` and `operator.schema.json`;
  those structural passes do not override its stale date or changed profile/receipt bindings.
- `operator.schema.json` validation also passed for the example operator object.
- Corrected receipt evidence hashes match. `validate_preflight_receipt` blocks on the first
  `not_observed` check, as required.
- The corrected offline suite ran 82 tests successfully; E2E and historical validators also
  passed in this checkout. These checks cover repository tooling and fixtures, not AGY access,
  effective settings, a product run, COM3, or hardware.
- The added AGY-shaped mock-stream test starts an offline subprocess, delivers the exact UTF-8
  prompt bytes once through stdin, preserves one raw JSONL event, verifies the prompt SHA-256,
  and confirms unsupported AGY token/tool metrics remain `null`. It does not prove the real
  AGY event format, provider access, user-intervention measurement, or evaluator read-only
  enforcement.

## Gate status and next operations

| Gate | Status | Remaining evidence |
|---|---|---|
| R0/R2/R3 | `pass` in the existing offline contract scope | Keep their product/tooling meaning separate from AGY execution. |
| R1 | `not_ready` | Re-run `check` after replacing unresolved profile values and record the resulting bundle hash. |
| R4 | `not_ready` | Evidence-backed AGY approval, settings, model entitlement, and exact invocation. |
| R5 | `blocked` | Host toolchain, network, prompt scope, activity logging, and effective settings evidence bound to this profile. |
| R6/R7 | `not_ready` | The offline AGY-shaped mock proves exact one-shot stdin delivery, raw JSONL preservation, and null fallback for unsupported metrics. Real AGY stream compatibility, user-intervention measurement, and evaluator read-only enforcement remain unproved; actual run telemetry is post-run evidence. |
| R8 | `not_ready` | Current evidence proves only fixture collection, host-simulated transport, and a reference receiver. Candidate production evaluation follows a run and cannot be a pre-pilot prerequisite. The gate remains blocking until the maintainer explicitly scopes pre-pilot R8 to evaluator-harness readiness and records its acceptance criteria; production result evidence must remain post-run. |
| R9 | `not_ready` | Historical 16MiB backup/hash is documented and recomputed as `AA51BA15B975EC2E564506E609729F36D85DA23D8892023396A700846955A1E6`, but current board/artifact linkage, COM3 exclusive ownership, and the completed operator checklist are absent. COM3 presence was read as USB serial status `OK`; the port was not opened here. |
| R10 | `not_authorized` | Verify the preserved conditional approval against this exact baseline/profile/run only after R0–R9 conditions are evidenced. |

The next safe sequence is to obtain effective-settings evidence for the exact AGY argv,
replace the unresolved candidate values, recompute the semantic and bundle hashes, issue a
new `pilot_pass: false` receipt, and run `benchmark.py check` against the selected tag. Only
after that review and the hardware R9 evidence should an operator consider a new date-valid
`prepare`. Before R10 can activate, the R8 pre-pilot/post-run boundary must also be resolved
without requiring the pilot's own production result as its prerequisite. R10 must still be
explicitly activated before any prompt or model execution.
