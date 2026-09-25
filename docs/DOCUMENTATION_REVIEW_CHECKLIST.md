# 문서 검토 진행 기록

## 재개 지점

- 작업: main 문서의 목적·범위·정합성 검토, 근거 있는 수정, 재검증과 종합.
- 시작일: 2026-09-20 (Asia/Seoul).
- 시작 HEAD: `47b720d7f29185dd63a0d72737897966a4ea335f`.
- 시작 상태: `main`, `origin/main`보다 1 commit 앞섬, 작업 트리 깨끗함.
- 현재 단계 (2026-09-25): **N1~N5 완료, AGY pilot `BLOCKED / NOT_AUTHORIZED`**.
  Q1/Q2/Q3 결정과 baseline tag는 보존되어 있으며, 수정된 profile과 receipt는
  근거가 부족한 설정에서 의도대로 실행을 차단한다.
- 2026-09-25 후속 준비: R8의 pilot 전 harness 기준과 pilot 후 제품 평가를
  [readiness gate](experiments/benchmark-readiness.md#r8-pilot-전-완료-기준)에서 분리했다.
  AGY `stream-json` 결과·token·tool event의 오프라인 parser와 host report 파일 출력을
  구현해 현재 개발 checkout에서 85개 시험을 통과했다. 이 검사는
  [R8 개발 증거](experiments/evidence/r8-harness-development-20260925.md)이며 최종
  baseline의 R8 pass는 아니다. [로컬 AGY inventory](experiments/evidence/agy-local-inventory-20260925.md)는
  모델 목록·설정 파일 존재를 확인했지만 effective permission과 모델 실행 권한은 입증하지 않는다.
- 2026-09-25 추가 검증: `SUCCESS`와 함께 온 구조화된 권한 거부를 runner가 실패로
  처리하고 원본 usage·도구 실패 수는 보존하도록 보완했다. 현재 dirty-tree offline suite는
  87개 통과했다. stderr만의 soft-denial은 첫 pilot 후 원본 로그 검토가 필요하다.
- 2026-09-25 재검증: AGY가 `1.2.11`로 자동 갱신된 것을 확인하고 현 버전의 CLI·모델
  목록을 새 hash 증거로 보존했다. 후보 profile/receipt의 semantic SHA는
  `16452599165c2d3536134fa1962ebe2cf52eacede245f1aa472d7d9b2592065a`로
  일치한다. runner의 AGY 버전 검사와 실행 자식 프로세스에 자동 갱신 비활성화 환경을
  전달하도록 수정했으며 offline suite 88개가 통과했다. R4·R6·R7은
  `pilot_entry`와 `post_pilot`을 분리했고, R9의 candidate artifact 검사는 pilot 이후로
  옮겼다. 현재 상태는 여전히 `BLOCKED / NOT_AUTHORIZED`다.
- 다음 행동: [AGY Luna 감사](experiments/agy-launch-review-20260925.md)와
  [Sol 독립 검증](experiments/agy-launch-sol-review-20260925.md)을 먼저 읽는다.
  AGY 권한·전역 지침·확장 조건을 실측하고 실행 정책을 확정한다. R8은 새 runner가
  포함된 깨끗한 최종 baseline에서 재검증하고, R9 보드·백업·COM3 확인을 마친 뒤
  새 profile/bundle hash와 receipt를 발행한다. 날짜가 지난
  `20260924-antigravity-cli-agy-flash-medium-r01`은 재사용하지 않는다.
- 이번 감사 범위: 문서·profile·receipt 정정과 오프라인 검증. 모델 실행·COM3 open·
  flash·새 prepare는 수행하지 않았다.
- 문서 정비는 ADR 승인, baseline 동결, 실행 gate 통과를 뜻하지 않는다.
- 2026-09-25 AGY 감사: Q1/Q2/Q3 결정은 보존했다. 선택 baseline
  `benchmark-v2-baseline-20260923` → `9ef945efd9d6c2c4b4eedca75eccc9f280b3aced`와
  AGY target `gemini-3.8-flash-medium`을 확인했지만, effective settings·approval·
  network·host preflight 근거가 없어 R4=`not_ready`, R5=`blocked`, R6/R7=`not_ready`,
  R8/R9=`not_ready`, R10=`not_authorized`다. 상세 기록은
  [`agy-launch-review-20260925.md`](experiments/agy-launch-review-20260925.md)다.

## 체크리스트

- [x] 1. 브랜치·HEAD·기존 변경 확인.
- [x] 2. 적용 지침 확인, 전체 MD 목록과 역할·상태 분류. (DOCUMENTATION_MAP.md)
- [x] 3. 목적·현재 범위·후속 목표·완료 조건 추출.
- [x] 4. 전체 MD 검토 및 config/schema/fixture/validator 대조.
- [x] 5. 문제별 근거·심각도·수정 방향과 미해결 결정 기록.
- [x] 6. 근거가 명확한 문서 문제 수정.
- [x] 7. diff·상대 링크·용어·요구사항 ID·관련 기존 검사 재검증.
- [x] 8. 최종 평가·변경 내역·검증 결과·남은 작업 종합.

## 기록 규칙

단계가 끝날 때 체크하고 현재 단계와 다음 행동을 갱신한다. 검토 파일 목록과
발견 사항은 `DOCUMENTATION_REVIEW.md`에 기록한다. 중단 시 진행 중인 파일,
미완료 검사, 실패 원인도 이 파일에 남긴다. 완료 체크는 실제 산출물과 증거가
있을 때만 한다. 과거 검증 보고서를 현재 실행 증거로 취급하지 않는다.

## 작업 로그

- 2026-09-20: 사용자 요청에 따라 재개 가능한 검토 기록 생성. 변경 전 상태 확인.
- 2026-09-20: 추적 MD 전체 본문 검토. D01~D12 발견 사항과 코드 대조 근거를 검토 보고서에 저장. runner archive, token total, legacy evaluator와 E2E schema의 한계를 확인.
- 2026-09-20: 기존 MD 19개 수정, 문서 지도 추가. unittest 63개 통과(exit 0), E2E·matrix·historical validator 통과(각 exit 0). host dry-run exit 0, device_accessed=false. git diff --check 통과. 문서 링크·최종 보고서 검토 진행 중.
- 2026-09-20: D13(모델 필수 키 누락) 수정, D14(gate 순환 의존) 발견·미해결 기록. 보고서에 여섯 품질 축·변경 범위·후속 권고·실행 증거·관측 한계 종합.
- 2026-09-20: 최종 MD 45개/로컬 링크 209개 검사 통과, 지도 누락·필수 모델 키 누락·신규 문서 공백 오류 0. C/F/I/G ID 확인. 변경은 MD에 한정됨. 문서 검토 완료; N1~N8은 별도 후속 backlog로 보존.
- 2026-09-20: N1 완료. run ID를 만들지 않는 `benchmark.py check`와 baseline→receipt→승인→prepare/run 순서를
  runner/readiness/management/R4/run guide에 연결했다. N2 완료. baseline live flag를 fixture-only와 정합화했다.
- 2026-09-20: N3 완료. provider 원본 total과 E2E 정규화 total을 schema/runner/validator/test에 연결했다.
  N4 완료. C1~C8 및 F9 세부 증거를 E2E 결과 계약에 연결했다. N5 완료. E2E evaluation manifest,
  archive 정규화, summary 집계를 연결했다. offline unittest 77개와 validators exit 0.
- 2026-09-25: AGY `1.2.9`의 실제 `--version`/`--help`와 빈 MCP/plugin 목록을
  [`agy-cli-20260925.txt`](experiments/evidence/agy-cli-20260925.txt)에 보존했다.
  기존 raw preflight가 memory/cache/routing 비관측을 명시하므로 candidate의 false
  builtin-only/cleared/disabled/direct 및 Codex 전용 approval 주장을 제거하고,
  receipt의 근거 없는 pass를 `not_observed`/`blocked`로 정정했다. profile semantic
  당시 SHA는 `075f23c4ebb10c87b0d5bd54c86c9c03dd4ed1e21de44283b1cd65eb7c8caa84`다.
  help의 `--disable-slash-commands`는 모든 skill expansion을 차단해 builtin-only-v1과
  다르고, model ID에 effort가 포함되므로 `--effort medium`은 candidate argv에 넣지 않았다.

## 후속 backlog — 이번 문서 작업의 미완료 단계와 구분

아래는 검토에서 드러난 별도 계약 결정·구현 작업이다. 체크되지 않았다는 이유로
이번 문서 검토가 미완료인 것은 아니다. 후속 요청의 범위를 확인하고 진행하며,
기존 조건부 승인은 보존한다. 문서·코드 확인 자체에 실행 승인을 다시 요구하지 않는다.

- [x] N1 / D14 — gate 순환 의존 정리. maintainer가 입력/profile 사전 검사와 실제
  prepare를 구분하고 management/readiness/R4/실행 가이드의 종료 조건을 일치시킨다.
  완료: baseline 동결→receipt→승인 기록 확인→prepare→잔여 조건 확인·R10 발효→run의 순서를 순환 없이 설명 가능.
- [x] N2 / D11 — fixture-only와 baseline YAML live 플래그 정합화.
  완료: E2E 고정 입력에는 live 허용이 없고 owner-only 후속 범위와 혼동하지 않음.
- [x] N3 / D09 — provider 원본 total과 E2E 정규화 total의 정책 확정·구현.
  완료: 원본을 보존하며 OpenCode·Codex·미제공 telemetry의 변환 및 거부 조건 시험 통과.
- [x] N4 / D10 — C1~C8 개별 판정과 F9 세부 증거의 E2E 구조화 연결.
  완료: 개별 C가 누락/fail/not_run일 때 product_pass를 거부하고 historical 결과 호환 유지.
- [x] N5 / D07 — E2E 평가 manifest 생성·archive 정규화·집계 연결.
  선행: N3/N4 계약 확정. 완료: run/baseline identity 연결, 원본·실패 결과 보존,
  E2E round-trip 및 historical 회귀 통과. summary의 자동 집계 범위를 문서와 일치시킴.
- [ ] N6 — 모델·reasoning·builtin-only 설정 증거 및 profile-bound receipt 확정.
  AGY 1.2.9/argv는 help로 확인했지만 effective settings와 approval policy는
  미검증이다. candidate에는 `unverified` marker를 남겼고 receipt는 blocked다.
- [ ] N7 — ADR-0005/0006 검토, 입력·baseline 동결과 조건부 승인 발효 확인.
  선행: 관련 계약/준비 조건 충족. 이번 문서 정비나 tag 존재만으로 완료 처리하지 않음.
- [ ] N8 — 승인된 pilot 및 운영자 실물 평가.
  선행: N7 및 해당 run 조건. 실제 모델 실행·COM3·flash는 후속 범위에서만 수행.

## 새 세션 재개 절차

1. 이 파일 → `DOCUMENTATION_REVIEW.md` → `DOCUMENTATION_MAP.md` 순서로 읽는다.
2. `git status --short --branch`, `git rev-parse HEAD`, `git diff --stat`로 현재 상태를
   확인한다. 시작 HEAD와 다르면 새 변경을 파악하고 기존 산출물을 덮어쓰지 않는다.
3. 위 1~8 단계에 미완료가 남아 있으면 해당 지점부터 진행한다. 모두 완료면
   문서 검토를 처음부터 반복하지 않고, 사용자가 요청한 후속 backlog부터 진행한다.
4. 후속 코드 작업에서는 관련 함수·schema를 다시 읽어 문제의 현재 존재를 확인한다.
   이전 보고서만으로 구현 결함이 여전히 있다고 단정하지 않는다.
5. 각 항목의 파일·검증 명령·exit·남은 작업을 이 파일과 보고서에 갱신한다.

## 후속 구현 재개 상태 (N1~N5)

- N1: `python scripts/benchmark.py check --baseline <baseline-ref> --profile <verified-profile.json>`는
  run ID를 만들지 않는 입력/profile 검사다. baseline 동결·profile-bound receipt·명시적 승인을
  확인한 뒤 `prepare`를 실행한다. 조건부 승인에 남은 조건까지 확인해 R10을
  발효한 뒤에만 `run`을 실행한다.
- N2: `version-2-baseline.yaml`의 E2E cohort는 `live_api_allowed_after_fixture: false`이며
  live API는 `version-2-live-integration-v1` owner-only 후속 cohort다.
- N3: runner `measurement.tokens.provider_total`은 provider 원본을 보존하고 `total`은
  `input + output` 정규화 값이다. E2E telemetry도 같은 정책을 사용하며 raw total을
  normalized total에 재합산하지 않는다.
- N4: 모든 E2E 결과는 top-level `core_results.C1`~`C8`을 필수로 기록하고,
  `product_pass`에는 전부 `pass`가 필요하다. F9가 `pass`이면 세 후보·선택·점수·
  후보별 증거가 필요하다.
- N5: E2E `prepare`가 평가 manifest를 생성하고 archive가 result/manifest를 identity로 연결해
  보존한다. summary는 normalized/provider token, E2E product, C pass/8, F9를 집계한다.

오프라인 검증 기록 (이번 후속 작업):

| 명령 | exit | 결과 |
|---|---:|---|
| `python -m unittest discover -s scripts/tests -p 'test_*.py' -v` | 0 | 77 offline tests passed; no model/provider/hardware access |
| `python scripts/validate-end-to-end-result.py` | 0 | E2E schema/semantic round-trip passed |
| `python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json` | 0 | fixture matrix passed |
| `python scripts/validate-experiment-result.py` | 0 | historical regression passed |
| `git diff --check` | 0 | whitespace check passed |

AGY audit validation (2026-09-25):

| 명령 | exit | 결과 |
|---|---:|---|
| `agy --version` / `agy --help` / `agy mcp list` / `agy plugin list` | 0 | version `1.2.9`; help surface and empty local MCP/plugin inventories captured; no model/provider call |
| `python scripts/benchmark.py check --baseline benchmark-v2-baseline-20260923 --profile experiments/config/verified-profiles-candidate/agy-gemini-3.8-flash.candidate.json` | 1 | expected `BLOCKED`: unresolved profile settings |
| runner-profile schema + `validate_resolved_profile` | 0 | schema valid; resolver expected blocked on `unverified` marker |
| preserved AGY run manifest schema + operator validation | 0 | old prepared manifest is structurally valid; date/profile/receipt gates still block it |
| operator schema validation on example manifest | 0 | example operator object valid |
| corrected AGY receipt validation | 0 | expected blocked on `idf_build` because receipt now records `not_observed` |

The current 82 offline tests, E2E validators, and fixture matrix remain offline checks;
they do not close AGY R4/R5/R6/R7 or prove a product, provider, serial, or hardware result.

N6~N8은 실제 model/reasoning/settings, baseline hash 재검증, pilot/COM3/flash가 필요하므로
이번 turn에서 닫지 않는다. 현재 `R4 not_ready`, `R5 blocked`, `R6/R7 not_ready`,
`R8/R9 not_ready`, `R10 not_authorized`와 실행·하드웨어 조건부 승인 경계를 유지한다.
   중단 시 `현재 단계`와 `다음 행동`을 실제 상태로 남긴다.

재개 요청 예시:

```text
docs/DOCUMENTATION_REVIEW_CHECKLIST.md를 읽고 현재 Git 변경을 보존해 이어서 진행하라.
완료된 문서 검토는 반복하지 말고, 미완료 단계 또는 내가 지정한 후속 항목부터 처리하라.
진행 결과와 검증 증거를 같은 체크리스트에 계속 기록하라.
```
## Current implementation checkpoint (review feedback follow-up)

- [x] E2E core contract: every result requires top-level `core_results.C1` through
  `C8`; missing or incomplete entries fail schema/semantic validation.
- [x] F9 contract: `details` is accepted only under `feature_results.F9` and
  assessed F9 records three structured candidates. The canonical rubric is
  `hardware_understanding=5`, `user_value=5`, `selection_logic=5`,
  `implementation_completeness=10`, `separation_portability=5`; validator/tests
  require `total` to equal the sum (30 maximum).
- [x] Token contract: `provider_total` and its required definition are nullable/
  declared consistently; normalized `total` remains `input + output`.
- [x] Archive contract: E2E archive performs schema, semantic, manifest/evidence
  join, and post-normalization validation. Failed results retain only raw source
  snapshots; automated-test status is derived from integration evidence.
- [x] Check/prepare input bundle: prompt, config, fixtures, schema, evaluation
  criteria, profile, and baseline are read-only checked with shared hashes.
- [x] Summary contract: pilot and invalid results are excluded; valid groups show
  minimum repetition eligibility, success ratio, median, and range.

Previous stage: final offline consistency audit and documentation synchronization.
The earlier N4 summary sentence saying `core_results` is optional is superseded
by the implemented E2E schema: C1-C8 are now top-level required fields in every
E2E result. Historical `core_requirements` remains a separate legacy contract.
Next action: preserve this handoff checkpoint and obtain owner decisions only for
the remaining N6-N8 gates. No model/provider,
pilot/benchmark, COM3/hardware, flash, commit, tag, or push action is authorized
in this follow-up.

Required verification commands for this checkpoint:

```text
python -m unittest discover -s scripts/tests -p "test_*.py" -v
python scripts/validate-end-to-end-result.py
python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json
python scripts/validate-experiment-result.py
git diff --check
```

Previous offline verification before summary fixes (2026-09-21):

- [x] `python -m unittest discover -s scripts/tests -p "test_*.py" -v` — exit 0;
  77 tests passed, including archive semantic/evidence join, final mutation,
  summary eligibility, core C1-C8, F9, token, check/prepare, and semantic
  profile-bound receipt regressions.
- [x] `python scripts/validate-end-to-end-result.py` — exit 0.
- [x] `python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json` — exit 0.
- [x] `python scripts/validate-experiment-result.py` — exit 0.
- [x] `python scripts/run-host-device-pipeline.py --dry-run` — exit 0;
  3961 synthetic bytes rendered, `device_accessed=false`.
- [x] `git diff --check` — exit 0.

Previous assessment: offline implementation complete and handoff-ready. N6-N8 remain
conditionally blocked at the existing readiness boundary: model/reasoning and
profile-bound receipt evidence, baseline freeze, and owner-authorized pilot/
COM3/flash decisions are still manual. No real provider/model, pilot/benchmark,
COM3/hardware, flash, commit, tag, or push was performed.

## 재검토 결과 및 수정 (2026-09-21)

현재 단계: 기존 summary의 추가 결함 네 가지를 회귀 테스트로 고정하고 수정했다.
실제 provider/model, pilot/benchmark, COM3/hardware, flash는 실행하지 않았다.

- [x] Summary가 operator run manifest와 E2E evaluation manifest/result의
  identity 및 baseline을 교차 검증하도록 수정한다. 기존 summary 테스트의
  유효 입력에서 operator `execution.base_commit`만 `a` 40자로 바꿔도
  `collect_records`가 1개 유효 기록으로 수용하던 결함을 수정했다. E2E
  evaluation manifest의 run/manifest/result/baseline/ref/commit과 result의
  run/experiment/manifest/baseline 연결을 모두 확인한다.
- [x] 동일 실행의 중복 집계를 막는다. 같은 manifest 경로와 복사된 manifest의
  동일 run ID를 각각 중복으로 제외한다. 중복은 `duplicate` 제외 건수로
  기록되어 최소 반복 횟수를 충족시키지 못한다.
- [x] 서로 다른 실험 및 baseline/input 조건을 비교 그룹에서 분리한다.
  전체 group key에 agent 설정, experiment, baseline id/ref/commit,
  `input_bundle_sha256`를 사용하고 화면에는 긴 값을 축약해 표시한다.
- [x] 잘못된 manifest도 제외 건수로 처리한다. run-manifest schema를 중첩
  필드에 접근하기 전에 검증하며 `{}`와 잘못된 JSON을 `invalid`로 제외한다.

회귀 테스트 네 개를 `scripts/tests/test_summarize_benchmark.py`에 추가했다.
2026-09-21 수정 후 오프라인 검증은 다음과 같다.

- [x] `python -m unittest discover -s scripts/tests -p "test_*.py" -v` — exit 0;
  81 tests passed.
- [x] `python scripts/validate-end-to-end-result.py` — exit 0.
- [x] `python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json` — exit 0.
- [x] `python scripts/validate-experiment-result.py` — exit 0.
- [x] `git diff --check` — exit 0.

summary 계약은 [results/README.md](../results/README.md)와
[experiments/examples/README.md](../experiments/examples/README.md)에
동기화했다. N6~N8은 모델/reasoning/profile-bound receipt, baseline freeze,
owner-authorized pilot/COM3/flash 판단이 필요한 수동 gate로 남아 있다.

주 에이전트 독립 검증 (2026-09-21): 전체 81개 테스트, E2E validator,
fixture matrix, historical validator, `git diff --check` 모두 exit 0.
host pipeline dry-run은 3961 synthetic bytes, `device_accessed=false`로 통과했다.
현재 후속 수정 체크리스트 네 항목은 완료됐으며, 다음 작업은 N6~N8의
실행 설정·기준선 확정 및 실제 실험 준비 조건을 처리하는 것이다.

## 실험 시작 문서 검증 (2026-09-21)

판정: 오프라인 준비는 가능하나 문서를 그대로 따라 pilot/benchmark를 시작하기에는
절차 충돌과 실제 설정 미확정이 남아 있다. summary 수정 완료와 실행 준비 완료는
별도다. 이번 검증은 저장소 내부 절차·설정·코드 대조이며 직전 81개 시험 결과를
재사용했다. 외부 모델 지원이나 실물 상태는 재확인하지 않았다.

문서 보완:

- [x] `agent-run-commands.md` §4 prepare → §5 receipt 순서를 후반부의
  check → freeze → receipt → 승인 → prepare → run과 통일한다.
  준비 전 receipt의 semantic profile hash를 `benchmark.py check` 출력에서
  얻는다고 명시한다. 현재 예제는 준비 후 manifest 필드만 가리킨다.
- [x] `benchmark-readiness.md`의 "gate 순환이 아직 남음" 본문을 N1 완료와
  일치시키고, `preflight-evidence-20260918.md` 조건부 승인의 prepare 선행
  조건과 현재 prepare 이전 승인 규칙의 관계를 설명한다. 과거 사용자 승인
  내용은 임의로 변경하거나 취소하지 않는다.
- [x] 실행 가이드의 OpenCode total 미재계산 설명을 현재 구현의
  `provider_total` 원본 보존 / `total=input+output` 정규화와 일치시킨다.
- [x] readiness 표에 현재 검증 증거와 실제 남은 조건을 연결한다.
  R3/R8 등의 상태는 오프라인 검증 완료와 baseline 동결·실행 환경 증거
  미완료를 구분해 표시한다. 테스트 통과만으로 gate를 pass로 바꾸지 않는다.

실제 실행 준비:

- [ ] 모델/reasoning/settings 확정. `validate_resolved_profile`로 세 draft를
  검사했고 Codex/OpenCode/Antigravity 모두 placeholder/sentinel 때문에
  NOT_READY로 거부됐다. 모델 호출은 없었다.
- [ ] ADR-0005/0006 제안 상태 검토 및 최신 변경분을 포함한 baseline 확정.
  현재 main에는 수정·미추적 파일이 남아 있다.
- [ ] 해당 baseline/profile에 연결된 실제 preflight receipt와 승인 조건
  충족 증거 확보. 하드웨어 사용 시 COM3/백업/보드 확인도 필요하다.

다음 행동: 문서 절차 충돌 해소 → N6 profile/settings 확정 → N7 기준선·receipt·
조건부 승인 발효 확인 → N8 pilot. 이번에는 실제 실행이나 commit/tag를 하지 않았다.

## 문서 절차 수정 완료 (2026-09-21)

- [x] 실행 가이드 본문을 check → 최종 baseline/hash → receipt → 적용 승인 기록
  확인 → prepare → 원래 잔여 조건 충족/R10 발효 → run 순서로 정렬했다.
- [x] receipt hash 출처를 check 출력으로 명시하고 후보 commit과 최종 tag의
  ref 차이 및 미커밋 변경 미포함을 설명했다.
- [x] 과거 조건부 승인 원문을 보존하고 prepare 성공 조건의 확인 시점을 명시했다.
- [x] readiness·관리·protocol·R4 문서를 같은 순서로 통일하고 최신 검증 근거와
  미완료 조건을 구분했다. OpenCode 토큰과 summary 출력 설명도 코드에 맞췄다.

현재 단계: 문서 충돌 수정 완료. N6 실제 profile/settings, N7 baseline/receipt와
원래 승인 조건의 충족 증거, N8 pilot은 아직 미완료다. 문서 수정으로 이 조건을
자동 충족시키지 않았다. 다음 작업은 실제 모델·설정 확정 및 증거 수집이다.

검증: 변경 문서 7개 UTF-8·로컬 링크 30개·실행 가이드 §0~7 순서 확인 통과.
`benchmark.py check --help`로 명령 인자를 확인했고 `git diff --check`도 통과했다.
이번 수정은 문서만 대상으로 했으며 직전 81개 코드 시험은 반복하지 않았다.

## 실험 시작 준비 위임 및 재개 (2026-09-22)

현재 재개 지점은 [위임·결정 기록](experiments/launch-coordination-20260921.md)이다.
Luna max가 [준비 산출물](experiments/launch-readiness-20260921.md)을 작성했고,
Sol medium의 [독립 검증](experiments/launch-review-sol-20260921.md)에서 후보
profile·입력 hash와 빌드 파일 hash를 재현했다. 발견된 빌드 hash 오타는 수정됐다.

- [x] 설치 CLI·실제 인자 순서·로컬 모델 metadata 확인.
- [x] IDF v5.3.2 활성화 및 오프라인 ESP32-S3 hello-world 빌드.
- [x] 81개 테스트·validator·dry-run 및 후보 check 결과 기록.
- [x] Sol medium 최초 독립 검증 완료. 실행 가능 판정은 아직 아님.
- [x] 로컬 prompt-input 진단의 검증 범위 확인: 현재 세션 렌더러이며 후보 exec
  옵션의 실제 적용 증거로 대체할 수 없다. builtin-only 자체는 여전히 미검증.
- [x] 추가 prompt-input 진단 결과를 동일 Sol 세션에서 검토하고 잘못된 검증 제안 정정.
- [x] Q1 기존 6종 계획 유지, Q2 baseline commit/tag 승인, Q3 AGY
  `gemini-3.8-flash-medium` 및 옵션 A 결정은
  [`launch-coordination-20260921.md`](experiments/launch-coordination-20260921.md)에 기록했다.
  최종 AGY profile/settings evidence·receipt gate·R10 발효는 미완료다.

Luna의 추가 진단은 사용량 제한으로 중단됐고, 2026-09-22 사용자 재개 요청으로
동일 세션에 재전달했다. 완료된 환경 빌드·시험을 처음부터 반복하지 않는다.
첫 비교군 및 baseline commit/tag 문항에 대한 이전 미응답 문구는 2026-09-22
historical snapshot이다. 이후 사용자 Q1/Q2/Q3 결정은 coordination record에 반영됐고,
현재 AGY gate만 후속 검증한다. 실제 모델 실행·serial open·flash는 하지 않았다.

후속 feature 진단: [로컬 기능 제어 증거](experiments/evidence/codex-feature-controls-20260922.txt).
plugins/skill_search/enable_mcp_apps 비활성 값과 skip_host_skill_discovery 활성 값은
metadata로 확인됐다. 현재 세션의 SKILL.md 참조 수 감소는 관측됐지만 사용자 확장
제외를 증명하지 않는다. 실제 exec의 설정·출처와 결합된 증거가 있어야 R4/R5를 닫는다.
후보 profile은 변경하지 않았고 기존 hash는 유지된다.
