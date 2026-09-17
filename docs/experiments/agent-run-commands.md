# 에이전트 실행 가이드

## 상태

**현재 상태: `PLANNING / NOT_AUTHORIZED`**

운영 도구의 일부 scaffold가 있어도 도구별 모델·sandbox·기능 결과 schema 검증이
끝난 것은 아니다. 아래 명령은 [readiness gate](benchmark-readiness.md)의 R0~R9
사전조건이 통과하고 R10 사용자 명시 승인이 기록된 뒤에만 실행한다. 이 문서를
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
3. 선택한 agent/product/interface/model/reasoning profile과 실제 실행 파일이 검증됨
4. 도구별 preflight receipt, raw stdout/stderr, 명령 로그, token telemetry 수집이 준비됨
5. one-shot(공통 prompt 1회, 외부 feedback 0회)와 독립 evaluator 경계가 검증됨
6. COM3를 사용할 경우 제조사 예제/현재 보드 상태 백업과 운영자 checklist가 준비됨
7. 사용자가 baseline·profile·surface·반복 번호·pilot/benchmark를 명시적으로 승인함

하나라도 빠지면 다음 명령을 실행하지 말고 `not_ready` 사유만 문서화한다.

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

현재 로컬에서 확인한 실행 표면은 Codex CLI 0.153.2, Gemini CLI 0.35.0,
OpenCode 1.18.30 및 agy CLI다. 설치 확인은 로그인·모델 접근·sandbox 합격을 뜻하지 않는다.

- Codex: stdin `-`, `exec --json` 사용. turn.completed usage를 합산하고 cache는 input에 중복 가산하지 않는다.
- Gemini: `--prompt`와 `--output-format stream-json` 사용. stdin을 prompt에 덧붙이는 동작을 설치 버전에서 검증한다.
- OpenCode: `run --format json --model provider/model` 사용. stdin 전달과 승인 정책을 pilot 전에 검증한다.
- Antigravity: 실제 실행 파일은 `agy`. print/stream-json/sandbox를 지원하는 로컬 help를 확인했으며 정확한 입력·timeout·버전 확인은 남아 있다.

Windows npm의 .ps1/.cmd 파일을 shell 문자열로 조합하지 않는다. profile argv에는
실제 node.exe와 CLI JavaScript 진입점 또는 검증된 실행 파일을 지정한다.
실행기는 stdin UTF-8 bytes를 전달하므로 각 CLI가 추가하는 wrapper 문구까지 입력 조건으로 기록한다.
현재 Codex 이외의 usage 정규화는 미검증이며 null로 남는다. 원본 이벤트는 보존한다.
Codex tool_calls는 완료된 command_execution/mcp_tool_call/web_search/file_change item 수이며
다른 도구의 호출 정의와 직접 동일시하지 않는다. 명령 내부의 실패는 원본 로그로 별도 검토한다.

공식 근거: [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive/).
현재 설치본의 `--help`와 함께 확인했다.

## 3. 새 baseline 고정

공통 문서·스키마·평가 도구 변경을 커밋하고 운영 도구 검증과 profile 검토를 완료한다.
기능·GUI 결과 필드가 schema와 validator에 반영되기 전에는 새 baseline을 만들지
않는다. 이 단계는 readiness 작업이지 agent 실행이 아니다.
기존 `version-2-baseline-20260911` 태그를 옮기지 않는다. 새 이름의 태그와 전체 SHA를
기록한다. 아직 새 baseline이 확정되었다고 간주하지 않는다.

## 4. 실행 준비

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
```

원본 baseline SHA와 로컬 snapshot SHA를 구분한다. mkdir로 번호를 예약하고
실패한 준비도 번호를 재사용하지 않는다. 시작 날짜가 바뀌면 새 run을 준비한다.

## 5. 실행 환경·참조 범위 preflight receipt

기본 모드는 [실행 환경 정책](isolation-policy.md)의 `prompt-and-log`다.
host toolchain·TEMP·네트워크·설정과 prompt scope·activity logging 준비를 확인한다.
Docker/VM은 필수가 아니다. 통과하지 않은 항목을 pass로 채우지 않는다.

```json
{
  "base_commit": "<original-baseline-SHA>",
  "profile_sha256": "<prepared-profile.json-SHA256>",
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

## 6. 실행과 평가

이 절의 `benchmark.py run`은 R0~R10 승인 이후에만 허용된다. runner가 아닌
사람이 prompt를 전달하거나 evaluator가 실행 중 코드를 수정하면 run은
`manual pilot; invalid for cross-agent quantitative comparison`으로 기록한다.

```powershell
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

결과가 작성된 경우 `--result <hardware-feature.json>`를 추가한다.
manifest/result 상태와 구현 SHA는 운영자가 원본 증거와 대조해 정리한다.
에이전트의 원본 결과는 코드 snapshot에 그대로 보존한다.
공통 평가와 실물 기록은 [평가 인터페이스](evaluation-contract.md)를 따른다.

## 7. 보존 및 게시

코드의 자격증명·개인정보 여부를 확인한 뒤 다음 명령으로 로컬 보관한다.

```powershell
python scripts/benchmark.py archive <run-directory> `
  --archive C:\Espressif\benchmark-archive.git
```

## Current operator-check boundary

The version strings and command examples in the historical profile notes above are
not evidence for this readiness review. The repository does not assert a verified
model ID, CLI version, executable name, or telemetry surface for Codex, Gemini,
OpenCode, or Antigravity. Before any future run, the operator must perform
read-only `--version` and `--help` checks for the selected surface, record an
unavailable or ambiguous result as an operator check, and replace every
`operator-check-required` sentinel in the profile. `benchmark.py prepare` rejects
those sentinels; no profile in this planning state is executable.

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
