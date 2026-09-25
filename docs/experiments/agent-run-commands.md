# 에이전트 실행 가이드

## 상태

**현재 상태: `PILOT_ENTRY_READY / PREPARE_PENDING`** (2026-09-25 KST)

운영 도구의 일부 scaffold가 있어도 도구별 모델·sandbox·기능 결과 schema 검증이
끝난 것은 아니다. run 준비·실행·보존 명령은 [readiness gate](benchmark-readiness.md)의
조건과 해당 작업 승인을 확인한 뒤 수행한다. §1의 host 검사와 §2~3의 문서·설정
검토는 gate 충족을 준비하는 작업이며 agent 실행 승인을 요구하지 않는다. 이 문서를
읽거나 보완하는 것, 명령을 검토하는 것은 agent process를 시작하는 행위가 아니다.

공통 prompt는 사람이 CLI에 직접 붙여넣지 않는다. runner가 생성한 `prompt.txt`를
정확히 한 번 전달하고, 실행 중 follow-up·구현 피드백·코드 수정이 발생하면 해당
run을 정량 비교에서 제외한다. 아래의 환경·validator 명령을 실행했다고 해서
제품 구현이나 COM3 검증이 완료되었다고 해석하지 않는다.

## 0. 실행 승인 gate

실행 직전에 다음 사실을 모두 증거로 확인한다.

1. `main`의 승인된 baseline tag/SHA와 prompt/config/fixture/schema hash가 고정됨
2. 정식 E2E scope의 F1~F9·I1~I4 기능 범위와 G1~G6 LCD GUI rubric이 결과
   schema·validator·example에 반영됨
3. 선택한 표면에서 대상 모델이 목록에 노출되는지 확인하고 agent/product/interface/model/reasoning,
   argv/profile/settings/permission policy와 실제 실행 파일을 고정함. AGY는 필요한 명령만
   사전 허용하며, 목록 노출은 entitlement 확인이 아님
4. 도구별 preflight receipt, raw stdout/stderr, 명령 로그, token telemetry 수집이 준비됨
5. synthetic stream parser의 null/failure 보존과 one-shot mock의 prompt 1회·후속 개입 차단,
   evaluator read-only 절차를 검증함
6. COM3를 사용할 경우 제조사 예제/현재 보드 상태 백업과 운영자 checklist가 준비됨
7. 사용자가 baseline·profile·surface·반복 번호·pilot/benchmark를 명시적으로 승인함

하나라도 빠지면 prompt 전달을 진행하지 않고 `not_ready` 사유를 기록한다.
로컬 run 생성은 아래 준비 절차를 따른다. 승인 기록 확인과 실행 승인 발효를 구분한다.
누락 조건을 확인·보완하는 offline 검사는 계속할 수 있다.

R4·R6·R7은 pilot-entry 조건과 pilot 후 판정을 나누어 기록한다. 실제 model entitlement,
AGY stream/usage 및 soft-denial, 실제 operator intervention은 첫 pilot에서 관측·판정한다.
그 관측값을 그 pilot의 선행조건으로 요구하지 않는다. 실행 전에 위에 적힌 model-list/profile,
synthetic parser, one-shot mock, telemetry preservation, evaluator read-only 조건은 충족해야 한다.
AGY 명령 권한의 선택과 설정 검토 순서는
[scoped permission 계획](agy-scoped-permissions-20260925.md)에 따른다. 필요한 명령은 승인된
checkout에서 확인해 고정하며, `--dangerously-skip-permissions`는 후보 argv에 넣지 않는다.

## 1. 환경과 도구 검증

```powershell
. .\scripts\activate-idf.ps1
python -m pip install -r scripts/requirements-benchmark.txt
python -m unittest discover -s scripts/tests -v
python scripts/validate-end-to-end-result.py
python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json
python scripts/validate-experiment-result.py
.\scripts\check-experiment-preflight.ps1
```

실물 시험에는 `-RequireHardware -Port COM3`를 추가한다. COM 포트 탐지만으로
보드 모델이나 포트 독점 사용 가능 여부를 확정하지 않는다. 빌드 작업 경로와 TEMP는
ASCII 경로를 사용한다. 기본 모드는 host 최소 빌드를 확인하고 external-sandbox 선택 시 그 내부에서 확인한다.

## 2. Profile 확정

`experiments/config/runner-profile.example.json`을 복사하고 실제 모델 ID, slug,
reasoning, 설치 버전, argv, skills/plugins/MCP/메모리/사용자 지침/캐시/라우팅을 확정한다.
비밀번호·토큰을 profile에 넣지 않는다. 예제의 placeholder는 실행 준비 단계에서 거부된다.
반복마다 동일 profile을 사용한다. 순수 모델 비교가 아닌 agent+model+설정 비교다.

버전·실행 파일의 시점별 실측과 남은 설정은
[R4 profile 검토 기록](r4-profile-resolution.md)을 따른다. 해당 기록의 버전을
현재 설치본이나 실행 가능한 profile의 증거로 간주하지 않는다. 설치 확인은
로그인·모델 접근·sandbox 합격을 뜻하지 않는다.

- Codex: stdin `-`, `exec --json` 사용. turn.completed usage를 합산하고 cache는 input에 중복 가산하지 않는다.
- Gemini: 현재 기본 비교군에서 제외하고 Enterprise/API 키 조건에서만 별도 검토한다.
  보존된 profile 템플릿은 실행 가능 증거가 아니다.
- OpenCode: `run --format json --model provider/model` 사용. stdin 전달과 승인 정책을 pilot 전에 검증한다.
- Antigravity: runner는 일반 text stdin, stream-json 출력과 고정 timeout을 사용한다.
  model-list 노출은 기록됐지만 계정 entitlement 확인은 아니다. pilot 전 선택
  model/reasoning, argv/profile/settings와 permission policy를 근거로 고정한다. 실제
  entitlement와 returned stream은 첫 pilot 후 판정한다.

Windows npm의 .ps1/.cmd 파일을 shell 문자열로 조합하지 않는다. profile argv에는
실제 node.exe와 CLI JavaScript 진입점 또는 검증된 실행 파일을 지정한다.
실행기는 stdin UTF-8 bytes를 전달하므로 각 CLI가 추가하는 wrapper 문구까지 입력 조건으로 기록한다.
현재 runner는 Codex와 OpenCode 모두 `total`을 `input + output`으로 정규화한다.
cached/reasoning은 다시 더하지 않고, 제공자의 원본 합계는 `provider_total`에
별도로 보존한다. 미제공 값은 null과 사유로 기록하고 원본 이벤트도 보존한다.
Codex tool_calls는 완료된 command_execution/mcp_tool_call/web_search/file_change item 수이며
다른 도구의 호출 정의와 직접 동일시하지 않는다. 명령 내부의 실패는 원본 로그로 별도 검토한다.

공식 근거: [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive/).
현재 설치본의 `--help`와 함께 확인했다.

## 3. 새 baseline 고정

공통 문서·스키마·평가 도구 변경을 커밋하고 운영 도구 검증과 profile 검토를 완료한다.
기능·GUI 결과 필드가 schema와 validator에 반영되기 전에는 새 baseline을 만들지
않는다. 이 단계는 readiness 작업이지 agent 실행이 아니다.
기존 baseline 태그는 모두 보존한다. `version-2-baseline-20260911`,
`benchmark-v2-baseline-20260911`, `benchmark-v2-baseline-20260914`는 서로 다른
commit을 가리킨다. 날짜나 이름만으로 현재 계약과 일치한다고 판단하지 않는다.
새 기준을 동결할 때 새 이름의 태그와 전체 SHA를 기록한다.

확정 profile로 후보 commit을 검사하고, 최종 tag가 정해지면 다시 검사한다.
`check`는 Git commit을 읽으므로 미커밋 변경을 포함하지 않는다. ref 이름도
bundle hash에 포함되므로 최종 tag의 출력값을 보존한다.

```powershell
python scripts/benchmark.py check --baseline <candidate-commit> --profile <verified-profile.json>
# 기준선 확정 후 실행
python scripts/benchmark.py check --baseline <new-baseline-tag> --profile <verified-profile.json>
```

receipt의 `base_commit`에는 최종 출력의 `baseline_commit`, `profile_sha256`에는
동일 이름의 출력값을 사용한다. `input_bundle_sha256`과 구성 hash도 보존한다.
receipt 작성에 prepared manifest나 run ID는 필요하지 않다.

## 4. 실행 환경·참조 범위 preflight receipt

기본 모드는 [실행 환경 정책](isolation-policy.md)의 `prompt-and-log`다.
host toolchain·TEMP·네트워크·설정과 prompt scope·activity logging 준비를 확인한다.
Docker/VM은 필수가 아니다. 통과하지 않은 항목을 pass로 채우지 않는다.

```json
{
  "base_commit": "<original-baseline-SHA>",
  "profile_sha256": "<check 출력의 profile_sha256>",
  "access_policy": "prompt-and-log",
  "checks": {
    "idf_build": "pass",
    "compiler": "pass",
    "ninja": "pass",
    "git": "pass",
    "temp_write": "pass",
    "network_policy": "pass",
    "read_isolation": "not_enforced",
    "settings_inventory": "pass",
    "prompt_scope": "pass",
    "activity_logging": "pass"
  },
  "evidence": {"preflight-probe.txt": "<SHA256>"},
  "pilot_pass": false
}
```

profile의 기존 `sandbox_policy` 필드에도 같은 `prompt-and-log`를 기록한다.
evidence 경로는 receipt 폴더 기준이며 존재와 SHA-256을 검사한다.
제품 fixture 입력과 모델 호출 네트워크를 구분해 기록한다.
external-sandbox 선택 시 profile과 receipt를 `external-sandbox`로 맞추고 실제
sandbox 내부 검증과 `read_isolation: pass` 증거를 확보한다.
본 실험에는 같은 조건의 검토된 pilot 합격이 추가로 필요하다.

## 5. 승인 기록 확인과 로컬 실행 준비

### AGY 첫 pilot의 실행 순서

다음 순서는 준비 작업의 판단 기준이다. 모든 선행 조건과 적용 가능한 조건부 승인
조항을 충족하고 R10이 발효되기 전에는 마지막 `run` 단계로 진행하지 않는다.

1. 선택 baseline `benchmark-v2-baseline-20260925`와 검증된 candidate
   `experiments/config/verified-profiles-candidate/agy-gemini-3.8-flash.candidate.json`을
   확인한다. baseline commit은 `eef278013428a79c29d6b9456018049af149ca61`이다.
2. [제한 정책](agy-scoped-permissions-20260925.md)과 wrapper가 기존 전역 허용 규칙·
   공통 지침·hook을 일시 분리하는지 확인한다. `--dangerously-skip-permissions`는 사용하지
   않는다. 아래 check가 `inputs_valid`를 반환하는지 확인한다.
3. [profile-bound receipt](evidence/agy-gemini-3.8-flash-receipt.json)의 evidence SHA와
   pilot 전 check를 검증한다. `pilot_pass=false`는 첫 pilot 전의 정상 상태다.
4. 현재 [R0~R9 gate](benchmark-readiness.md#필수-gate)에서 각 gate의 pilot-entry 조건과
   첫 pilot 후 판정 항목을 구분하고, 대상에 적용되는 조건부 승인 기록을 대조한다. 특히
   R4·R6·R7의 사전 조건, R8 evaluator harness, R9 보드·백업·COM3 안전 증거를 확인한다.
5. 모든 prepare 전 조건이 충족된 경우에만 현재 날짜의 새 run을 준비한다. hardware 옵션 A의
   COM3를 쓰는 명령에는 `-Port COM3`를 지정한다. 포트 단독 점유, 보드 식별·제조사 기준
   백업 hash와 비파괴 checklist가 확인되지 않으면 prepare를 진행하지 않는다. agent가 생성할
   candidate artifact와 flash hash는 pilot 산출물로 기록하고 하드웨어 flash 직전에 대조한다.
   아직 생성되지 않은 candidate artifact를 pilot 준비 조건으로 요구하지 않는다.
6. 새 manifest의 baseline/profile hash와 receipt를 대조하고, 기존 조건부 승인에서 남은 조건을
   확인해 R10 발효 근거를 기록한다. 이 기록 전에는 agent를 실행하지 않는다.
7. R0~R10의 pilot-entry 조건이 충족되고 승인이 발효된 경우에만 새 run ID로
   `benchmark.py run`을 수행한다.
8. 첫 pilot 종료 후 model entitlement와 실제 stream/usage·soft-denial, user/operator
   intervention 기록을 검토해 R4·R6·R7의 `post_pilot` 판정을 별도로 갱신한다. raw
   stdout과 stderr의 hash·검토 결론을 남기기 전에는 receipt의 `pilot_pass`를 `true`로
   바꾸지 않는다. stderr에만 남는 거부 통지도 검토한다.

2026-09-24에 예약된 `20260924-antigravity-cli-agy-flash-medium-r01`은 날짜와
profile/receipt hash가 현재 준비와 맞지 않으므로 보존만 하고 재사용하지 않는다.

먼저 profile과 baseline 입력을 검사한다. 이 검사는 모델을 호출하지 않고 run ID를
예약하지 않는다.

```powershell
python scripts/benchmark.py check `
  --baseline benchmark-v2-baseline-20260925 `
  --profile experiments/config/verified-profiles-candidate/agy-gemini-3.8-flash.candidate.json
```

check 성공만으로 준비·승인이 완료되지 않는다. receipt와 R0~R9의 pilot-entry 증거가
검토되고 조건부 승인 조항을 적용할 수 있을 때 아래 명령을 사용한다. R4·R6·R7의
첫 pilot 후 판정 항목은 이 준비 단계의 선행조건이 아니다. 오늘 날짜를 seed로 쓰고,
hardware 옵션 A인 COM3를 명시한다. `prepare`는 선택 태그와 HEAD가 같은 깨끗한
checkout에서만 실행되므로 먼저 별도 ASCII 경로의 baseline worktree로 이동한다.

```powershell
git worktree add --detach C:\Espressif\benchmark-baseline-20260925 benchmark-v2-baseline-20260925
Set-Location C:\Espressif\benchmark-baseline-20260925
.\scripts\new-experiment-run.ps1 `
  -Baseline benchmark-v2-baseline-20260925 `
  -Profile experiments/config/verified-profiles-candidate/agy-gemini-3.8-flash.candidate.json `
  -RunRoot C:\Espressif\benchmark-runs `
  -Seed 20260925 -Phase pilot -Port COM3
```

COM3 준비 조건이 확인되지 않았거나 적용되는 승인 기록이 prepare 전 실행을 금지하면
명령을 실행하지 않고 해당 gate를 미완료로 둔다.

먼저 §4 receipt를 작성한다. R0~R9의 pilot-entry 증거와 대상 baseline/profile/phase/횟수에
적용되는 승인 기록을 확인한 뒤 아래 명령을 실행한다. 기존 조건부 승인이
prepare 성공을 요구하면 로컬 준비 후 그 조건을 확인한다. `prepare`는 모델을
호출하지 않으며 R10 실행 승인 발효를 의미하지 않는다. 대상·조건이 일치하는
기존 승인에 대해 동일 승인을 다시 요청하지 않는다.

항상 선택한 baseline 자체의 깨끗한 checkout에서 준비 명령을 실행한다.
run root는 운영자가 관리하는 단일 ASCII 경로를 사용한다. root를 바꾸면 반복 번호의
전역 유일성을 자동 보장할 수 없으므로 기존 예약 목록을 먼저 확인한다.

```powershell
.\scripts\new-experiment-run.ps1 -Baseline <new-baseline-tag> `
  -Profile <verified-profile.json> -RunRoot C:\Espressif\benchmark-runs `
  -Seed 20260911 -Phase pilot
```

결과:
```text
C:/Espressif/benchmark-runs/<run-id>/
  checkout/          이력 한 개와 remote 없는 baseline 사본
  profile.json       확정된 실행 조건
  prompt.txt         run ID가 치환된 실제 UTF-8 입력
  run-manifest.json  운영 기록, 초기 상태 prepared
  e2e-evaluation-manifest.json  E2E 평가 manifest
```

원본 baseline SHA와 로컬 snapshot SHA를 구분한다. mkdir로 번호를 예약하고
실패한 준비도 번호를 재사용하지 않는다. 시작 날짜가 바뀌면 새 run을 준비한다.

준비 후 manifest의 `execution.base_commit`과 `execution.profile_sha256`이 receipt와
일치하는지 확인한다. prepare 성공·COM3 확인 등 원래 승인 조건을 모두 충족하고
R10 발효 근거를 기록한 뒤 §6으로 진행한다. 미충족이면 prepared 상태에서 멈춘다.

## 6. 실행과 평가

이 절의 `benchmark.py run`은 R0~R9의 pilot-entry 조건을 확인하고 R10 승인이 발효된 뒤에만
허용된다. R4·R6·R7의 post-pilot 판정은 run 후 실제 evidence를 검토해 갱신한다. runner가 아닌
사람이 prompt를 전달하거나 evaluator가 실행 중 코드를 수정하면 run은
`manual pilot; invalid for cross-agent quantitative comparison`으로 기록한다.

```powershell
python scripts/agy_pilot_environment.py `
  --backup-dir C:\Espressif\benchmark-runs\<run-id>-agy-config run -- `
  python scripts/benchmark.py run C:\Espressif\benchmark-runs\<run-id> `
  --receipt <preflight-receipt.json>
```

120분 제한을 적용하며 Ctrl+C 중단과 timeout은 자식 프로세스까지 종료한다.
원본 stdout/stderr는 checkout 밖에 기록한다. OS 강제 종료/정전은 running 상태가
남을 수 있으므로 프로세스 종료를 확인한 뒤 별도 운영 복구 기록을 남긴다.
토큰·시간을 추정하지 않는다. 에이전트가 정상 종료해도 제품 합격을 뜻하지 않는다.
실행기 자체는 보드에 플래시하지 않는다.

```powershell
python scripts/validate-experiment-result.py --manifest <run-manifest.json> `
  --evidence-root <run-directory>
python scripts/evaluate-product.py --adapter-config <reviewed-adapter.json> `
  --output <new-evaluation.json>
```

historical 결과만 위 validator에 `--result <hardware-feature.json>`를 추가한다.
E2E 결과에는 별도의 평가 manifest와 validator를 사용한다.

```powershell
python scripts/validate-end-to-end-result.py --result <end-to-end-result.json> `
  --manifest <e2e-evaluation-manifest.json> --evidence-root <evidence-root>
```

runner의 `run-manifest.json`은 운영 기록(schema v2)이며 위 평가 manifest(schema v1)의
대체물이 아니다. `prepare`가 run ID·baseline에 연결된 평가 manifest를 생성하고,
archive가 이를 E2E result와 함께 보존한다. agent에게 운영 시각·해시·토큰을 추정해
채우게 하지 않는다. archive 후 result의 manifest path는 보관 위치로 정규화한다.

manifest/result 상태와 구현 SHA는 운영자가 원본 증거와 대조해 정리한다.
에이전트의 원본 결과는 코드 snapshot에 그대로 보존한다.
공통 평가와 실물 기록은 [평가 인터페이스](evaluation-contract.md)를 따른다.

## 7. 보존 및 게시

`archive`는 historical 결과에는 `hardware-feature-result.schema.json`을 사용하고,
E2E cohort에는 `end-to-end-result.schema.json`과 생성된 평가 manifest를 사용한다.
E2E 결과의 manifest path는 archive 위치로 정규화되며, raw logs는 여전히 별도
운영 증거다. 이 명령의 성공은 제품 합격이나 실물 검증을 뜻하지 않는다.

코드의 자격증명·개인정보 여부를 확인한 뒤 다음 명령으로 로컬 보관한다.

```powershell
python scripts/benchmark.py archive <run-directory> `
  --archive C:\Espressif\benchmark-archive.git
```

## Current operator-check boundary

The version strings and command examples in the historical profile notes above are
not evidence for this readiness review. The repository records dated observations,
not a currently executable profile or verified model entitlement.
Before any future run, the operator must perform
read-only `--version` and `--help` checks for the selected surface, record an
unavailable or ambiguous result as an operator check, and replace every
`operator-check-required` sentinel in the profile. `benchmark.py prepare` rejects
those sentinels; no profile in this planning state is executable.

The non-cyclic order is: `benchmark.py check` (no run ID) → freeze the baseline
and record its hashes → obtain a profile-bound receipt → verify the applicable
approval record → `benchmark.py prepare` → verify remaining approval conditions
and record R10 activation → `benchmark.py run`. The first command is a
maintainer input check; it is not a readiness approval and it does not replace
the receipt or R10 decision.

`benchmark.py check` materializes the selected baseline into a temporary read-only
snapshot before hashing it. The shared `input_bundle_sha256` covers the baseline
ref/commit, semantic profile hash, prompt, config, recursive fixtures, schemas, and
evaluation criteria; `prepare` writes the same component hashes into
`run-manifest.execution`. The check does not reserve a run ID, create a worktree,
or modify the repository.

Telemetry policy: `provider_total` is the provider-reported raw total when the
adapter supplies one. E2E `agent_tokens.total` is always the normalized
`input + output` total, excluding cached and reasoning tokens; the raw value is
retained separately and is never added again. Missing telemetry remains null
with an availability reason.

Every E2E result requires `core_results.C1` through `C8`; `product_pass` requires
all eight individual entries to be `pass`. F9 is the only feature whose result
entry may contain `details`. A passing or partial F9 requires exactly three
candidate records with user value, resource/implementation cost, risk,
verification method, selection/rejection rationale or selection-document
evidence, and the canonical 30-point rubric
(`hardware_understanding:5`, `user_value:5`, `selection_logic:5`,
`implementation_completeness:10`, `separation_portability:5`). The validator
requires the declared F9 total to equal the sum of those five fields.
The runner creates the E2E evaluation manifest during `prepare`; archive stores
that manifest and the normalized result together only after schema, semantic,
and evidence-join validation. A failed result keeps only the raw snapshot;
summary excludes pilot/invalid results and reports valid-group repetitions,
success ratio, median, and range without inferring automated-test status from
`product_pass`.

전용 bare archive에 agent/model 브랜치를 만들고 구현 commit과 bundle을 보존한다.
다음 실행의 소스는 항상 baseline에서 시작한다. 이전 results와 agent-runs 기록은
보관 브랜치에 누적한다. 원본 stdout/stderr는 자동으로 Git에 넣지 않는다.
명령은 GitHub에 자동 push하지 않는다. 운영자 검토 후 보관 브랜치를 원격에 게시한다.

`scripts/summarize-benchmark.py`로 main 요약 초안을 만들고 평가·증거·고정 링크를
추가해 검토한다. 실험 브랜치 전체를 main에 merge하지 않는다.

## 확장 설정 목록과 실제 사용 기록

첫 비교군은 `builtin-only-v1`로 고정한다. 사용자 설치 스킬·외부 플러그인·MCP를
실제로 비활성화했는지 확인한 뒤 settings_inventory 증거에 기록한다.
profile 템플릿의 정책 문자열 자체를 검증 증거로 사용하지 않는다.
도구 내장 기능 목록, 이름·버전·출처·설정·해시와 확인 방법을 함께 남긴다.
실행 후 실제 사용 기능·호출 횟수·raw log 위치를 별도 운영 기록에 추가한다.
수집 불가능한 항목은 null과 사유를 사용한다. 명령/도구 로그가 일부만 제공되면
그 범위를 명시하고 관측되지 않은 호출을 미사용으로 간주하지 않는다.
기록을 profile/receipt 증거 파일과 연결하며 원본 로그와 함께 보존한다.
ponytail 적용 실행은 기본 비교군에 합치지 않고 별도 확장 비교군으로 표기한다.
