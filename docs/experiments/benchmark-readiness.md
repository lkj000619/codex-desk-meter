# Benchmark 실행 전 준비 gate

## 현재 상태

**상태: `PLANNING / NOT_AUTHORIZED`**

2026-09-18 설계 검토 후속 변경과 최신 host 검증은
[design-remediation-20260918.md](design-remediation-20260918.md)에 기록한다.
계약·fixture·IDF 활성화 보완과 host 시험 통과는 개별 실행 profile/receipt 확정이나
실물 합격을 뜻하지 않는다. R4/R5/R10의 미충족 조건은 해당 기록을 함께 확인한다.

이 문서는 에이전트 제품 구현을 실행하는 지침이 아니라, 실행해도 되는지 판단하는
운영 gate다. 현재 이 gate가 `AUTHORIZED`로 바뀌지 않았으므로 agent prompt를
수동으로 붙여넣거나 `benchmark.py run`을 실행하지 않는다. 문서 보완·schema·runner
자체 시험은 제품 실험 실행이 아니다.

## 기준 저장소

- 정식 기준 브랜치: `main`
- 선택된 AGY pilot baseline tag: `benchmark-v2-baseline-20260923`
- 선택된 baseline commit: `9ef945efd9d6c2c4b4eedca75eccc9f280b3aced`
- 감사 시작 시점 HEAD: `a36747ab2f7ac50676343b3b53517c8491d54b03` (baseline 이후 5 commits).
  candidate/profile/evidence 보완은 이 baseline snapshot에 자동으로 들어가지 않는다.
  현재 HEAD·변경 여부는 `git rev-parse HEAD`와 `git status`로 확인하며, 새 입력을
  사용하려면 해당 입력의 hash를 다시 check하고 별도 commit/tag로 동결한다.
- 보존 중인 historical baseline tag: `benchmark-v2-baseline-20260911`
- 해당 historical tag의 commit: `34a1790ffeb31d47c1ae78c78a14d7cf4e318c6f`
- `main-2`는 runner tooling을 추가한 중간 개발 브랜치이며, 앞으로의 기준은
  검토·승인된 `main` commit과 tag로만 정한다.
- `experiment/...` 브랜치는 한 agent의 동결 결과를 보관한다. 다음 run의 시작점으로
  사용하지 않는다.

2026-09-20 로컬 ref 확인에서는 `version-2-baseline-20260911`과
`benchmark-v2-baseline-20260914`도 존재한다. 위 태그와 서로 다른 commit이며,
태그 존재만으로 현재 E2E 계약의 동결·승인 증거가 되지 않는다. ref별 commit은
[문서 검토 기록](../DOCUMENTATION_REVIEW.md)에 보존한다.

입력 검사와 run 준비를 분리해 순환 의존을 해소했다. 현재 순서는 마지막 절과
[실행 가이드](agent-run-commands.md) §1~6을 따른다. 기존 조건부 승인 기록을
확인하고 로컬 prepare를 수행한 뒤, 준비 성공을 포함한 원래 조건이 모두
충족됐는지 확인해 R10을 발효한다. 문서 정비만으로 gate를 통과시키지 않는다.

## 역할 분리

| 역할 | 허용 작업 | 금지 작업 |
|---|---|---|
| 기준 저장소 maintainer | 목적·계약·prompt·schema·runner·평가 기준 수정 | 실험 중인 agent 결과를 main에 섞기 |
| agent | 깨끗한 checkout에서 제품 구현·자체 시험·결과 초안 작성 | manifest 조작, COM3 flash, private credential 요청 |
| 공통 evaluator | 동결된 artifact를 read-only로 평가 | 평가 중 코드 수정·수정 지시 |
| hardware operator | 승인된 artifact를 COM3에 flash하고 사진/영상·로그 수집 | 평가 전 임의 수정, erase_flash |
| remediation 작업자 | 평가 후 별도 branch에서 수리·개선 | 원본 benchmark commit·점수 덮어쓰기 |

## 실행 단계

```text
P0 목적·범위·계약 고정
        ↓
P1 runner/profile/access-policy/schema 준비 및 독립 검증
        ↓
P2 도구별 preflight와 preflight receipt 검토
        ↓
P3 사용자 승인 후 pilot 1회
        ↓
P4 pilot 합격 후 agent/model별 benchmark 반복
        ↓
P5 결과 동결 → 공통 평가 → 운영자 하드웨어 평가
        ↓
P6 필요 시 remediation 별도 실험
```

P0~P2의 pilot-entry 조건이 완료되지 않으면 P3 이후로 진행하지 않는다. R4·R6·R7은
pilot 전 준비와 첫 pilot 후 관측을 나누어 기록한다. 첫 pilot 후에만 생길 수 있는
entitlement·실제 stream/usage·soft-denial·operator intervention 증거는 해당 pilot의
선행조건이 아니다. 현재 P3는 R4 profile 설정이 unresolved이고 R5/R8/R9와 R10 조건도
미완료라 여전히 진행할 수 없다. pilot은 운영 인프라를 검증하는 단계이지 제품 구현을
개선하는 단계가 아니며, 순위 통계에서 제외한다.

## 필수 gate

| Gate | 확인 조건 | 현재 상태 |
|---|---|---|
| R0 목적·범위 | 제품 목표, Version 2 계약, E2E product benchmark와 historical firmware prep 범위 분리 | `pass` |
| R1 고정 입력 | prompt/config/fixture/schema/평가기준 commit·hash와 transport 선택 고정 | `not_ready` |
| R2 비교 항목 | F1~F9·I1~I4 기능표와 LCD G1~G6 rubric 확정 | `pass` |
| R3 결과 계약 | feature_results·GUI 평가를 기록하도록 schema/validator/example 갱신 | `pass` |
| R4 profile | pilot 전: 모델 목록 노출, argv/profile/settings 및 필요한 명령만 허용하는 permission policy 확인. 첫 pilot 후: 실제 entitlement와 반환 stream 기록 | `not_ready` |
| R5 preflight receipt | compiler·Ninja·Git·TEMP·ASCII 경로·참조 제한·활동 로그·네트워크·도구 권한 증거; 전역 permission 범위 및 OS 격리 선택 | `blocked` |
| R6 runner telemetry | pilot 전: synthetic parser 사례와 null/failure 보존 규칙 검증. 첫 pilot 후: 실제 AGY usage·soft-denial 결과 판정 | `not_ready` |
| R7 one-shot 경계 | pilot 전: mock prompt 1회·후속 개입 차단 시험과 evaluator read-only 절차 확인. 첫 pilot 후: 실제 개입 기록 판정 | `not_ready` |
| R8 pilot 전 평가 harness | 동결된 fixture/reference 입력, evaluator 도구, positive/negative validator 사례와 산출물·maintainer 검토 | `not_ready` |
| R9 하드웨어 안전 | 제조사 기준 백업 hash, COM3 단독 점유, erase 금지, 운영자 checklist | `not_ready` |
| R10 승인 | 사용자가 해당 baseline·profile·pilot 실행을 명시적으로 승인 | `not_authorized` |

위 `현재 상태`는 pilot 이후까지 포함한 종합 상태다. 첫 pilot의 진입 여부는 아래
`pilot_entry`만으로 판정하고, pilot에서 처음 얻는 증거는 `post_pilot`에 기록한다.
R0~R9의 `pilot_entry=pass`와 대상에 적용되는 R10 승인 조건이 충족되어야 첫 pilot을
시작할 수 있다. `post_pilot=pending`은 그 pilot의 진입 실패를 뜻하지 않는다.

| Gate | `pilot_entry` | `post_pilot` | 판정 경계 |
|---|---|---|---|
| R4 | `not_ready` | `pending` | 고정된 CLI·profile·설정·필요 명령 권한 정책 확인 후 진입; 실제 entitlement·stream은 사후 확인 |
| R6 | `not_ready` | `pending` | 합성 telemetry·실패 보존 검증 후 진입; 실제 usage와 soft-denial은 사후 확인 |
| R7 | `not_ready` | `pending` | mock one-shot 차단·평가자 read-only 절차 확인 후 진입; 실제 개입 여부는 사후 확인 |

다른 R0~R9 gate의 `pilot_entry`는 위 표의 `현재 상태`를 따른다. R5의 `blocked`와
R1/R8/R9의 `not_ready`가 남아 있으므로 현재 첫 pilot은 시작할 수 없다. 첫 pilot
완료 후 raw stdout/stderr를 함께 검토하고 도구 거부·개입 여부와 근거 hash를 기록하기
전에는 `post_pilot=pass` 또는 receipt의 `pilot_pass=true`로 승격하지 않는다.

R3 결과 계약과 R1/R3의 transport 설계에는 Waveshare 공식
[`waveshareteam/codex-meter`](https://github.com/waveshareteam/codex-meter)를 참조할 수
있다. 참고 범위와 provenance·라이선스·보드 차이·검증 경계는
[PC 수집기–ESP32 통합 계약 초안](integration-contract.md)의 “외부 참조 구현”을
따른다. 참고했다는 사실만으로 gate 상태를 `pass`로 바꾸지 않는다.

R1~R3을 확정할 때에는 다중 provider fixture matrix도 고정한다. 최소 대상은 Codex,
Claude Code, Antigravity CLI(Google 기본), Orca/IDE host와 unsupported
provider이며 (`gemini-cli`는 Enterprise/API 키 conditional),
source가 제공하지
않는 절대 token 잔량을 추정하지 않는 계약을 포함한다. matrix 본문
(`experiments/fixtures/provider-fixture-matrix.json`)과 provider adapter 결과
schema·validator·example은 존재한다. 선택 baseline tag는 존재하지만, 2026-09-25
candidate 수정 뒤 profile이 unresolved 상태여서 R1의 최종 check/bundle hash는
아직 닫히지 않았다. R3 결과 계약은 오프라인 validator 범위에서 유지된다.

### 현재 검증 증거와 남은 조건 (2026-09-21)

위 gate 상태는 실행 준비 판정이며 코드 구현 여부와 구분한다.
최신 검증 기록은 [진행 체크리스트](../DOCUMENTATION_REVIEW_CHECKLIST.md)에 있다.

| Gate | 확보한 증거 | 남은 조건 |
|---|---|---|
| R0/R2 | 목적·C/F/G/I 계약과 비교 항목 정비 | 최종 범위·ADR 검토 기록 |
| R1 | 선택 tag와 check/prepare 공통 hash 설계 | AGY candidate 정정 후 `check` 재통과와 bundle hash 기록 |
| R3 | E2E·historical·fixture matrix validator 통과 | 동결 기준선 재검증·검토 기록, CI 증거는 별도 |
| R4/R5 | AGY 1.2.11 `--version`/`--help`, CLI model-list 기록, raw preflight·receipt audit, 공식 permission 문서 검토 | R4 pilot 전: 목록에 노출된 선택 모델, argv/profile/settings, 필요한 명령만 사전 허용하는 policy를 고정한다. 실제 entitlement와 반환 stream은 첫 pilot 결과로 판정한다. 현재 global settings의 allow 범위가 넓어 범위 검토가 필요하다. R5는 host checks·prompt/activity evidence와 valid profile-bound receipt가 필요하며, `request-review` soft-denial은 pilot에서 관측한다 |
| R6/R7 | 현재 offline suite 재실행 결과는 evidence ledger 참조. synthetic AGY stream의 terminal result·누적 usage·명시적 command error, missing/ERROR/multi-turn 거부 시험이 있음 | R6 pilot 전은 synthetic parser와 null/failure 보존 확인; 실제 AGY usage·soft-denial은 첫 pilot 후 판정. R7 pilot 전은 one-shot/mock 개입 차단과 evaluator read-only 절차 확인; 실제 개입 기록은 첫 pilot 후 판정. 실제 결과를 해당 pilot의 선행 증거로 요구하지 않음 |
| R8 | 2026-09-25 감사 당시 offline suite 82개와 host dry-run 3961 bytes, device_accessed=false. 이후 dirty HEAD offline suite 재실행 결과는 evidence ledger 참조 | 아래의 pilot 전 harness evidence ledger와 maintainer/date review가 아직 완료되지 않음; candidate production parser/receiver, 실제 serial·LCD 및 I3/I4 판정은 pilot 이후 평가 |
| R9 | 운영 checklist 문서 | 보드·백업 hash·COM3 단독 점유 실측 |
| R10 | 2026-09-18 조건부 승인 기록 보존 | 대상 일치 및 prepare 성공 등 원래 조건 충족 확인 |

### AGY 감사 결과 (2026-09-25)

첫 pilot target은 사용자 Q3 결정대로 `antigravity-cli / gemini-3.8-flash-medium`이며
hardware 옵션 A 결정도 보존한다. 이 결정은 R10 발효가 아니다. 선택 baseline tag는
`benchmark-v2-baseline-20260923`이고 commit은
`9ef945efd9d6c2c4b4eedca75eccc9f280b3aced`이다. 감사 시작 HEAD는
`a36747ab2f7ac50676343b3b53517c8491d54b03`였으며 baseline 뒤 5 commits다.

`agy --version`은 최초 `1.2.9`, 재확인 시 자동 갱신된 `1.2.11`로 관측됐다. 현재 `--help`는 `--disable-slash-commands`,
`--effort`, `--model`, `--input-format text`, `--output-format stream-json`을
노출한다. 원문과 실행 파일 SHA-256은
[`agy-cli-20260925-v1211.txt`](evidence/agy-cli-20260925-v1211.txt)에 보존했다. 이 명령들은
model/provider 호출을 하지 않았다.

Google의 [Antigravity headless 문서](https://www.antigravity.google/docs/cli/headless/)
는 `stream-json` 이벤트가 `init`, `step_update`, terminal `result` 순서이며,
terminal usage가 누적값이라고 설명한다. 기본 headless permission mode는
`request-review`이고, 승인할 수 없는 tool 요청은 soft-deny되어도 process가 exit 0으로
끝날 수 있다. 따라서 exit code만으로 요청한 도구 작업이 실행됐다고 판단할 수 없다.
이 문서는 protocol과 documented default의 근거이지, candidate profile의 effective
permission settings나 실제 권한 동작 증거는 아니다. R4=`not_ready`, R5=`blocked`를
유지한다. R4의 pilot-entry 조건은 intended permission policy와 profile 근거를 확인하는
것이며 실제 stream의 mode 및 soft-denial 동작은 첫 pilot에서 판정해 기록한다.

첫 pilot의 권한 정책은 필요한 명령만 사전 허용하는 것으로 정했다. 현재
[local inventory](evidence/agy-local-inventory-20260925.md)는 global `settings.json`에
114개 allow rule(14 `command`, 100 `unsandboxed`)이 있음을 기록하지만, rule의 실제 영향이나
미래 실행의 effective policy는 입증하지 않는다. 승인된 checkout에서 필요한 명령을 실측해
정확한 rule을 고정하고 기존 global rule의 범위·영향도 재검토해야 한다. 공식
[permissions 문서](https://antigravity.google/docs/permissions?tab=cli)는 `permissions.allow`,
우선순위 Deny > Ask > Allow를 설명하고, Windows PowerShell에서는 구문에 따라 full-line
또는 regex 일치가 필요할 수 있다고 안내한다. 구체 rule 목록을 추정하지 않는다.
`--dangerously-skip-permissions`는 후보 argv에 넣지 않는다. 이 설정·정책 검토와 profile-bound
receipt가 끝나지 않았으므로 R4/R5 상태는 그대로 유지한다.

기존 [`agy-preflight-20260924.txt`](evidence/agy-preflight-20260924.txt)는 version,
MCP 서버 없음, imported plugin 없음만 관측한다. 해당 기록은 memory/cache/routing이
CLI에서 직접 관측되지 않는다고 명시하며, host toolchain·network·prompt scope·activity
logging·effective permissions·model entitlement·telemetry를 입증하지 않는다. AGY model
entitlement와 실제 stream은 첫 pilot에서 판정할 관측이며 pilot-entry 증거로 요구하지 않는다.
따라서
candidate의 `cleared`, `disabled`, `direct`, `builtin-only enforcement verified` 및
Codex 전용 `--ask-for-approval` 문구를 제거·미검증으로 고쳤다. help에
`--disable-slash-commands`와 `--effort`가 보이지만, 전자는 모든 skill expansion을
차단해 built-in 기능을 유지하는 `builtin-only-v1`과 다르고, 후자는 model ID에 effort가
포함된 경우 중복 지정하면 안 된다. 따라서 candidate argv에는 둘 다 넣지 않았고,
effective enforcement는 입증하지 않았다.

AGY receipt는 현재 profile semantic SHA-256
`16452599165c2d3536134fa1962ebe2cf52eacede245f1aa472d7d9b2592065a`와 evidence
SHA-256을 갱신했다. receipt의 `idf_build`, `compiler`, `ninja`, `git`, `temp_write`,
`network_policy`, `prompt_scope`, `activity_logging`은 `not_observed`,
`settings_inventory`는 `blocked`, `read_isolation`은 `not_enforced`, `pilot_pass`는
`false`다. receipt 자체는 실행 receipt로 통과하지 않으며, 상세 chain은
[`agy-launch-review-20260925.md`](agy-launch-review-20260925.md)에 기록한다.

수정된 profile은 `runner-profile.schema.json`에 맞지만 unresolved marker 때문에
`benchmark.py check`와 `validate_resolved_profile`이 의도대로 차단한다. 예시 operator는
`operator.schema.json`을 통과한다. 이 상태에서 profile을 실행 가능하다고 표시하거나
receipt를 `pass`로 올리지 않는다.

보존된 `C:\Espressif\benchmark-runs\20260924-antigravity-cli-agy-flash-medium-r01`
은 `prepared` 상태지만 2026-09-25에 `benchmark.py execute`의 날짜 검사에 걸리고,
이 감사에서 바뀐 profile/receipt SHA와도 맞지 않는다. 예약된 ID와 checkout은 보존하고
재사용하지 않는다. 새 `prepare`는 effective settings와 receipt가 해결되고 R10 조건을
검토한 뒤에만 수행한다. 과거 16MiB 백업 artifact와 SHA-256
`AA51BA15B975EC2E564506E609729F36D85DA23D8892023396A700846955A1E6`은 문서와 파일로
확인되지만, 현재 보드 식별·백업의 해당 보드 연계·COM3 단독 점유·운영자 checklist는 미완료다.
Candidate artifact/hash는 pilot 후 flash 전에 확인한다. COM3
장치 존재는 USB serial status `OK`로 읽었지만 포트를 열거나 flash하지 않았다.

R8은 첫 pilot의 산출물을 요구하는 production 결과와 pilot 전 evaluator-harness 준비를
구분한다. pilot 전 R8의 통과 증거는 아래 고정 명령의 재현 가능한 출력, exit code와
입력·출력 hash를 모은 evidence ledger, 그리고 maintainer/date가 적힌 검토 기록이다.
이 gate는 harness가 pilot 결과를 수집·검증할 준비가 됐는지를 판정한다. 검토자가
`python` 명령이 저장소 루트에서 실행되고 현재 frozen candidate를 대상으로 하는지
확인한다. 현재 offline suite 통과만으로 R8이 충족되지 않으며 ledger와 maintainer review가
완료되지 않아 R8은 `not_ready`다.

### R8 pilot 전 완료 기준

저장소 루트에서 아래 명령을 실행하고 각 명령의 UTC 시각, HEAD, 종료 코드, stdout/stderr
또는 생성 파일, 관련 입력·출력 SHA-256을 evidence ledger에 기록한다.

```powershell
python -m unittest discover -s scripts/tests -p 'test_*.py' -v
python scripts/validate-end-to-end-result.py
python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json
python scripts/validate-end-to-end-result.py --result experiments/examples/invalid/invalid-product-pass.example.json
python scripts/run-host-device-pipeline.py --dry-run --output "$env:TEMP\cdm-host-frame-20260925.jsonl" --report-output "$env:TEMP\cdm-host-report-20260925.json"
```

첫 세 validator/test 명령은 exit 0이어야 한다. negative example은 exit 1 및
`PRODUCT_PASS_REQUIRES_CORE_RESULTS`를 반환해야 한다. host dry-run은 exit 0,
machine-readable host frame은 `--output`이 기록하고 JSON report는 `--report-output`이
기록한다. report의 `device_accessed: false`, 빈 `collection_failures`를 확인하고 두
machine-readable 파일을 모두 보존·해시한다. 명령의 실행일에 맞춰 TEMP 파일명을 고유하게 바꾼다.

현재 dirty HEAD에서 얻은 offline test 결과는 개발 검증 기록이다. runner와 문서 변경을
최종 baseline commit에 동결한 뒤, 깨끗한 baseline checkout에서 위 명령 전체를 다시 실행해
R8 evidence ledger를 완성한다. maintainer는 최종 checkout의 HEAD, 각 출력·파일 hash와
검토 일자·이름을 대조해 기록한다. 이 단계들은 오프라인 평가 harness 검증이며 provider
실행이나 실물 합격 증거가 아니다. final checkout의 ledger와 검토 기록이 완료될 때까지
R8은 `not_ready`다.

candidate production parser/receiver의 실제 제품 artifact 평가, fixture collector와
실제 transport의 동작, serial 수신, LCD 표시, I3/I4 실물 합격은 pilot이 만든 결과물을
대상으로 하는 post-run 평가다. 이를 해당 pilot의 선행조건으로 삼지 않는다. fixture나
reference-model의 pass는 production pass가 아니다. R6은 offline parser/mock stream의
긍정·부정 사례를 사전에 검증할 수 있지만 실제 AGY stream telemetry는 실행 후 evidence로
확인해야 한다. 실행 전에는 R6/R7의 종합 상태와 `post_pilot`을 통과로 승격하지 않는다.
각 `pilot_entry`는 합성 검증·절차 증거만으로 별도 판정한다.

후속 offline 구현에서는 AGY NDJSON terminal `result`의 누적 usage로부터 `input + output`을
normalized total로 기록하고 provider의 원본 `total_tokens`를 별도 보존한다. 완료된 tool
step과 명시적인 `run_command` 오류도 분류한다. 현재 offline suite 재실행 결과는 evidence
ledger에 기록하며, synthetic/parser 경로 검증은 실제 AGY 호출·stream 호환성, effective
permission mode, soft-denial 결과와
전체 user-intervention 계측을 검증하지 않았다. 따라서 R6/R7은 `not_ready`다.
2026-09-25 audit의 82-test 값은 당시 기록으로 보존하고 최신 결과는 evidence ledger에서 확인한다.

### Gate 종료 산출물과 책임자

| Gate | 종료 산출물 | 책임자 | 완료 판정 |
|---|---|---|---|
| R0 | 목적·cohort·C/F/G/I 범위 diff | maintainer | historical prep와 E2E 제품 합격 조건에 모순 없음 |
| R1 | hash가 고정된 prompt/config/fixture bundle과 transport ADR | maintainer | 모든 agent가 동일 입력·transport를 사용 |
| R2 | 다중-provider capability/fixture matrix와 GUI rubric | maintainer | Codex·Claude·Antigravity·Orca host·unsupported 사례 포함 |
| R3 | E2E schema, validator, valid/invalid examples와 CI log | maintainer | F1~F9·I1~I4·G1~G6 및 provider/host identity를 기계 검증 |
| R4 | pilot 전 model-list·argv/profile/settings/permission-policy evidence, pilot 후 entitlement·실제 stream 관측 | maintainer | 실행 조건이 사전 고정되고 pilot 관측을 별도 사후 판정; entitlement/stream 사후 관측을 pilot 선행조건으로 요구하지 않음 |
| R5 | preflight receipt example과 preflight log | runner maintainer | 경로·도구·네트워크·쓰기 범위 재현 가능 |
| R6 | pilot 전 synthetic parser·null/failure 보존 시험, pilot 후 실제 usage·soft-denial telemetry | runner maintainer | 사전 합성 사례와 보존 규칙으로 pilot entry를 판정하고 실제 AGY telemetry는 첫 pilot 결과로 사후 판정 |
| R7 | pilot 전 one-shot/mock 개입 차단 시험·evaluator read-only 절차, pilot 후 actual intervention record | runner maintainer | 사전 경계와 평가 절차로 pilot entry를 판정하고 실제 개입 기록은 첫 pilot에서 수집·사후 판정 |
| R8 | offline test/validator/fixture-matrix/negative-case/host-dry-run evidence ledger | maintainer | 명령별 exit·출력·hash 확인 후 maintainer/date review 기록; 실제 제품·serial·LCD 평가는 pilot 이후 |
| R9 | artifact/flash/COM3 운영 checklist | hardware operator | hash·단독 점유·비파괴 절차 확인 |
| R10 | 대상 baseline/profile/run 수가 적힌 사용자 승인 기록 | user | 명시 승인 전 실행 불가 |

R0~R9의 pilot-entry 증거와 해당 baseline/profile에 적용되는 승인 기록을 확인한 뒤 로컬
`prepare`로 ID를 예약할 수 있다. R4·R6·R7의 첫 pilot 후 판정 항목은 pilot-entry 증거가
아니며, 실제 pilot 결과를 선행 증거로 요구하지 않는다. 조건부 승인의 prepare 성공 등 잔여 조건을
모두 확인해 R10을 발효하기 전에는 prompt를 전달하지 않는다.
`not_run`, `partial`, `blocked`를 근거 없이 `pass`로 바꾸어 gate를 통과시키지 않는다.

## 한 번의 정식 run 규칙

1. runner가 새 checkout, manifest, 실제 prompt, profile, receipt를 만든다.
2. runner가 `<run-id>`를 치환한 prompt를 agent에게 정확히 한 번 전달한다.
3. agent는 실행 중 자체적으로 빌드·시험·수정을 반복할 수 있지만, 운영자·evaluator가
   오류 원인이나 구현 방향을 알려주지 않는다.
4. agent 종료 후 branch와 결과 파일을 동결한다. 이 시점 전후의 수동 코드 수정은
   benchmark run에 포함하지 않는다.
5. evaluator가 동결된 artifact를 read-only로 공통 시험하고, operator가 별도 승인 후
   COM3 하드웨어 시험을 수행한다.
6. 문제를 고치려면 평가 결과를 먼저 저장한 뒤 `remediation/<run-id>-...`에서 한다.

다른 agent에 prompt를 직접 복사·붙여넣은 수동 실행은 정식 benchmark가 아니라
`manual pilot; invalid for cross-agent quantitative comparison`으로 기록한다.

## 제품 데이터 범위

정식 `version-2-end-to-end-v1` benchmark는 계정 쿠키·API key·Wi‑Fi 자격증명 없는
표준 fixture collector와 로컬 transport를 사용한다. 현재 r01처럼 펌웨어에
fixture를 직접 내장하는 것은 historical preparation 자료로만 인정한다. 실제
제품은 다음 interface를 모두 연결해야 한다.

```text
PC provider collectors
        ↓ normalized UsageSnapshot / GlobalResetSnapshot
USB serial(COM3) `cdm/1` transport adapter (E2E baseline 고정)
        ↓ framed data
ESP32 receiver → validation/cache/stale → common state → LCD GUI
```

local Wi-Fi 운용은 별도 cohort에서 비교하며, E2E baseline의 transport 선택을
대체하지 않는다. baseline(`experiments/config/version-2-baseline.yaml`)의
`transport_choice: usb-serial-cdm-1`이 단일 진실이며, 본문의 “또는 local Wi-Fi”
표현은 선택지가 아닌 후속 cohort 항목으로 읽는다. transport 결정의 근거는
[ADR-0005](../decisions/0005-transport-usb-serial-baseline.md)를 따른다.

`UsageSnapshot`은 백분율과 함께 source가 제공하는 경우에만 used/remaining/limit
token 및 단위를 운반한다. source가 절대 quota를 공개하지 않으면 null과
`unit: percent|unknown`을 유지하며, agent나 runner가 임의의 token 총량을 추정하지
않는다.

검토 중인 E2E 계약의 transport 선택값은 USB serial(COM3) `cdm/1`이다.
ADR-0005 승인과 baseline 동결은 아직 남아 있다. local Wi-Fi 운용은
별도 cohort에서 비교한다. 실제 계정 source로의 전환은 별도의 owner-only live integration이다.
collector·transport·receiver를 구현·검증하기 전에는 “실시간 Codex 사용량 표시
완료”라고 보고하지 않는다. 계층별 frame·재연결·무결성 시험의 설계는
[통합 계약 초안](integration-contract.md)을 참고한다.

## 무효 처리 조건

다음 중 하나라도 발생하면 run을 정량 비교에서 제외한다.

- 기준 commit이 아닌 branch에서 시작
- prompt가 1회 초과 전달되거나 실행 중 구현 피드백·수정 지시가 제공됨
- runner manifest·preflight receipt·raw log·원본 token telemetry가 없음
- 실행 후 사람이 같은 branch의 코드를 수정하고 원본과 구분하지 않음
- fixture/reference test를 production C 또는 hardware 합격으로 주장
- COM3 artifact·보드·flash hash를 확인하지 않고 hardware pass를 기록
- 범위 밖 PC integration을 구현하지 않았는데 제품 전체 pass로 표시

## 승인 방법

2026-09-18의 [조건부 pilot 승인 기록](preflight-evidence-20260918.md)은 보존한다.
아직 충족되지 않은 모델·설정·동결·receipt 조건과 R10 발효를 구분하며, 문서 정비로
승인을 새로 부여하거나 기존 조건부 승인을 취소하지 않는다.

승인은 모든 R0~R9의 pilot-entry 증거와 사후 판정 계획을 검토한 뒤 사용자가 특정 baseline, profile, 실행
표면, 반복 번호와 pilot/benchmark 여부를 명시하는 방식으로 남긴다. 승인 전에는
현재 저장소의 prompt와 실행 명령을 읽거나 시험할 수는 있지만 agent process를
시작하지 않는다.

## Current review addendum (2026-09-13 snapshot)

The offline readiness review is recorded in
[`readiness-review-20260913.md`](readiness-review-20260913.md). The R0-R10 statuses
below are that review's snapshot, not the current norm: R0 `in_review`, R1
`in_review`, R2 `in_review`, R3 `in_review`, R4 `not_ready`, R5 `not_ready`,
R6 `partial`, R7 `not_ready`, R8 `partial`, R9 `not_ready`, and R10
`not_authorized`. The gate table above (§필수 gate) is authoritative for the
current status.

Current policy (2026-09-14): [isolation-policy.md](isolation-policy.md) defines
`prompt-and-log` as the default: current main inputs in a dedicated checkout,
prompt restrictions against other branches/prior results, and activity/reference logs.
Docker/VM is optional. Quantitative comparison is allowed with the same declared
conditions and adequate evidence. OS read isolation is recorded as `not_enforced`.
R5 remains `not_ready` pending a reviewed policy-bound preflight receipt;
R10 remains `not_authorized`. Actual reference violations and incomplete manual
delivery/evidence remain comparison exclusions.

All checks in this review are read-only/offline. A host simulation is not I3/I4
or a hardware pass, and no candidate-agent run, provider access, serial open,
ESP32 operation, or firmware/LCD implementation was performed. Profiles remain
operator-check-only sentinels; final baseline hashes and any commit/tag require
explicit user approval.

## Linear preparation order (N1)

The gate order is intentionally acyclic: run the runner's input/profile `check`
without reserving a run ID; freeze and hash the selected baseline; obtain a
profile-bound preflight receipt; verify the applicable approval record; run
`benchmark.py prepare`; verify all remaining conditional-approval requirements
and record R10 activation; only then run `benchmark.py run`. `prepare` repeats the
baseline/profile checks immediately before reserving an ID. A readiness gate
must not require a prepared run as its own evidence, and a prepared run is not
an authorization. R4 remains `not_ready`, R5 remains `blocked`, R6/R7 remain
`not_ready`, and R10 remains `not_authorized` until the applicable pre-pilot evidence
and approval conditions are met. Their first-pilot observations are assessed afterward.
