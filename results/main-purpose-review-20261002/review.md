# main 프로젝트 목적·실험 개선·문서 중복 검토

평가일: 2026-10-02. 대상: 로컬 `main`, `eb69163ed33ebf1afff4ba3d85d97677dc88b395`.
비교 기준: 과거 세 에이전트 평가, 수정 전 `d6da44a`, 최근 입력 축소 `83daf9f`와 스크립트 정리 `eb69163`.

**프로젝트 방향은 목적에 부합한다. 입력 과다·문서 탐색 부담·일부 기계 계약 설명 오류는 개선됐다. 그러나 첫 결과와 후속 수정 비용을 공정하게 비교하는 운영·평가 체계의 개선은 부분 완료다. 새 비교를 재현하고 그 결과를 확정적으로 해석할 준비가 끝났다고 평가할 수 없다.**

기존 144개 회귀시험은 143개 통과, Windows 심볼릭 링크 생성 권한으로 1개 건너뜀이다. 이 결과는 현재 도구의 회귀 안정성을 뒷받침한다. 아래에서 재현한 집계·source 시각 검사 공백이나 실제 LCD의 문제 해결을 증명하지는 않는다.

**평가 범위와 근거**

- [프로젝트 목적](../../docs/PROJECT_PURPOSE.md), 제품 계약, 최초 prompt, baseline YAML, 후보 allowlist, 운영·평가·통합·보드 문서를 대조했다.
- Git 추적 Markdown 90개에서 로컬 파일 링크를 검사했다. archive/evidence를 제외한 현행 문서 41개의 역할·반복 규칙·상태 설명을 검토했다. 제공 도구와 tests의 검사 범위를 코드에서 확인했다. 모든 원본 영상·대용량 로그·제품 source를 전수 재검토한 것은 아니다.
- 기존 미추적 AGY/Codex·OpenCode 비교 보고서와 로컬 OpenCode r06 최종 보드 판정도 읽었다. 과거 관측은 보존된 기록이며 이번에 새로 측정한 실물 결과가 아니다.
- 이번 검증은 offline unittest, schema/fixture/부정 예제, 입력 snapshot 검사, host dry-run, 최소 합성 재현이다. 후보 process 실행·COM port 접근·flash·실 계정 수집은 수행하지 않았다.
- 재실행 가능한 [검토 스크립트](verify_review.py), [검증 데이터](evidence.json), [시험 로그](unittest.log), [dry-run frame](host-frame.jsonl), [dry-run report](host-report.json)를 함께 보존했다.

**1. 프로젝트 목적과 현재 구조의 적합성**

| 목적 | 현재 상태 | 평가 |
|---|---|---|
| 책상 위 장치에서 사용량·리셋·상태 표시 | C1~C8·I1~I4가 PC→실제 receiver→LCD 경로를 요구함 | 목적에 부합. 실제 계정 자동 수집과 Version 1 이식은 후속 범위라 최종 제품 완성은 아님 |
| 동일 과제에서 AI 에이전트 품질·시간·token 비교 | 고정 입력, 독립 checkout, 원본 telemetry, 제품 결과·GUI·비용 분리가 있음 | 방향은 적절함. 후속 누적 예산·reference 판정·실패 비용 집계가 남음 |
| 다른 사람이 결과를 검토·재실행 | commit/hash, schema, 시험과 evidence 기록이 있음 | 부분 충족. reference의 실제 stimulus와 독립 artifact 복구 계약이 미완료 |
| main을 공통 시작 자료로 유지 | main에 후보 제품 펌웨어가 없고 allowlist만 전달함 | 저장소 역할에 부합. main에 제품 코드가 없다는 사실 자체는 결함이 아님 |

fixture E2E로 먼저 비교하고 실제 계정 연결을 owner-only 단계로 분리한 것은 단계적 검증에 적합하다. 다만 fixture 성공을 실시간 개인 계정 제품의 완성으로 읽어서는 안 된다. 과거 AGY·Codex·OpenCode 자료도 지시·권한·수정 기회·작성 책임·집계 범위가 달라 직접적인 성능/비용 순위 근거가 아니다.

**2. 과거 문제의 개선 확인**

원래 문제 ID는 [세 에이전트 아키텍처 평가](../../docs/experiments/architecture-review-20261002.md)를 따른다.

| 과거 문제 | 현재 반영 | 판정 |
|---|---|---|
| A01: 기존 단회 규칙과 새 첫 결과+수정 비교의 관계 | 새 운영 계약과 문서 우선순위, 최초/후속 분리를 기록. YAML/prompt에도 선택값 반영 | 부분 개선. management와 runner의 기존 gate는 동기화되지 않음 |
| A02: 설명과 schema의 불일치 | 제품·평가 문서의 C1~C8 설명과 token 원본/정규화 구분 정정. 현재 기계 회귀시험 통과 | 주요 대상 개선. 자율 기능 안내에는 F9 구조 부재 설명이 남음(R06) |
| A03: 기준 도달·공통 수정 예산 없음 | reference-match와 product_pass 분리, 최초 120분·후속 3회/누적 120분 기록 | 부분 개선. 실제 기준 입력 복구와 예산 enforcement 미구현(R01/R02) |
| A04: epoch/uptime·source/수신 freshness | 제품 계약에 source 시각 보존과 수신 단조 시계를 명시 | 부분 개선. fixture anchor와 runtime 경계 정책은 미완료. host oracle에도 의미 검사 공백 재현(R04) |
| A05: 보드 전제 부족 | 핀·RGB 순서·백라이트 active-low·PSRAM·GPIO0 공유를 짧은 사실 문서에 반영 | 문서 개선. 제조사 파일 189개 hash도 일치. 후보 LCD가 수정됐다는 증거는 별도 |
| A06: parser 시험이 상수·잘못된 reset·glyph를 놓침 | legacy evaluator의 한계를 명시, C/F/I/G 결과와 증거 분리 | 설명 개선. 실제 receiver→state→view-model 검사 추가는 미완료(R05) |
| A07: write·수락·가시 출력·단절 시험 혼동 | ACK 없음, write receipt와 device acceptance 구분, powered 시험 요구를 유지 | 부분 개선. 공통 단일 port 관측·timing 절차는 미완료(R05) |
| A08: 정책·환경·제품 능력 혼합 | 운영 계약에서 축을 분리하고 과거 실패 보존 | 부분 개선. 공통 prompt의 AGY 명령 규칙과 표면별 실효 권한 검증은 남음(R07) |
| A09: 현재/과거 탐색 혼동 | README·문서 지도·archive 정리, 다음 비교 readiness 진입점 추가 | Git 진입 문서 개선. management·purpose 등에 과거 현재/승인 설명이 남음(R06) |
| A10: source bundle만으로 증거 복원 실패 | source/evidence 복구를 준비 backlog에 명시 | 미완료. 새 경로 복원 검증과 package manifest가 없음(R08) |

추가로 실제 측정한 입력 축소 결과는 필수 MD **570→245줄(57.0% 감소)**, 제공 파일 **57개(MD 3개)**다. README 189→54줄, 문서 지도 127→54줄, 통합 계약 211→13줄, host 도구 안내 109→15줄이다. `d6da44a` 이후 원본 `docs/experiments/evidence/`의 Git blob 변경은 없다. 입력 축소를 위해 과거 근거를 덮어쓰지 않은 점은 적절하다.

기존 제품의 수정 여부는 따로 읽어야 한다. 보존된 Codex 기록에는 stack·백라이트 수정 이후 값 표시·세 화면 전환이 확인돼 있다. 전체 제품 합격은 미입증이다. OpenCode r06은 host/validator/upload가 성공했어도 최종 소유자 관측이 검은 화면이며 `full_product_pass=false`다. 이번 main 도구 정리로 이 실물 실패까지 해결됐다고 볼 근거는 없다.

**3. 우선순위별 발견 사항**

**R01 — Critical: 새 운영 예산과 종료 조건이 runner에 연결되지 않았다.**

[운영 계약](../../docs/experiments/comparison-operating-contract.md) §3과 baseline의 `remediation_max_rounds`, `remediation_cumulative_timeout_seconds`는 후속 3회·7,200초와 reference 도달 종료를 정한다. 하지만 [benchmark.py](../../scripts/benchmark.py)의 `prepare`/`execute`/CLI는 단회 실행만 처리한다(299, 660, 909행). 후속 직전 commit, 회차, 잔여 예산, 누적 token, RM 판정 종료를 관리하는 경로가 없다. 681행은 benchmark phase에 여전히 `pilot_pass=true`를 요구한다. 이 receipt 필드를 인프라 준비와 어떻게 구분할지는 미연결 상태다. 따라서 문서에 예산을 써 둔 것과 실제 강제가 완료된 것을 구분해야 한다.

조치: 최초 결과와 연결되는 후속 session ledger·잔여 예산 검증·timeout 포함 누적 비용·RM 종료를 구현하고, 기존 pilot gate의 새 cohort 적용 의미를 명시한다. 별도 수동 절차를 택한다면 같은 항목과 강제 근거를 운영 기록으로 고정해야 한다.

**R02 — Critical: reference-match의 실제 시험 입력이 아직 동결되지 않았다.**

[reference-match 목록](../../docs/experiments/reference-match-matrix.md) 19~30, 48~51행은 RM1~RM5의 fixture 경로/hash·reference_time·collector 명령·expected frame 복구가 남았다고 명시한다. 58%·82%와 화면 전환 관찰만으로 정확한 source/window/frame을 추정할 수 없다. 다음 후보마다 다른 입력이나 시각을 사용하면 같은 기능 도달 비교가 되지 않는다.

조치: 보존된 원본에서 stimulus와 expected 값/bytes를 복구하고 각 RM의 관찰 증거와 연결한다. 이미 고정한 C/F/I 기준을 확대하거나 후보의 제품 합격을 실행 선행조건으로 추가할 필요는 없다.

**R03 — Major: 집계표는 전체 시도 성공률·실패 비용을 제공하지 않는다.**

[summarize-benchmark.py](../../scripts/summarize-benchmark.py) 211~213행은 timeout/aborted/environment_failed를 모두 `incomplete`로 묶어 제외한다. 305행의 성공률 분모는 남은 completed result 수다. 미완료 건수는 마지막에 전체 합계만 표시하고 비교군별 상태·경과 시간·token 비용은 빠진다. [관리 문서](../../docs/experiments/benchmark-management.md) 115~117행의 성공/시도 수와 상태별 실패·미완료 경과 시간 보고까지 충족하지 않는다.

합성 재현: schema와 operator 의미 검사를 통과한 **성공 completed 1건 + timeout 1건**을 입력했다. 제품 result 로딩만 stub했다. 집계 records는 1건이고 표의 `Success ratio`는 **1.000**, `incomplete=1`은 하단 제외 목록으로만 나온다. 전체 시도 성공률은 1/2=0.5이고 timeout 비용이 표에서 빠진다. 현재 출력은 completed 결과에 조건부인 비율임을 첫 문장에서 밝히므로 계산 오류로 단정하지 않는다. 문제는 프로젝트가 원하는 전체 시도·도달 비용 지표가 별도로 없다는 점이다.

조치: 기존 completed 지표를 유지하되 attempted/completed/timeout/aborted/environment_failed, 전체 시도 성공률, 실패 포함 비용과 단계별 누적값을 비교군별로 추가한다. 환경 실패와 제품 실패를 같은 원인으로 합치지 않는다.

**R04 — Major: host 기준 수신 모델의 성공은 source 시각 계약의 성공을 의미하지 않는다.**

[제품 계약](../../docs/PRODUCT_CONTRACT.md) 43~47행은 미래 source 시각을 오류로 처리하고 observed_at 기준 300초 stale을 요구한다. [host_device_pipeline.py](../../scripts/host_device_pipeline.py)의 snapshot/frame 검사는 schema 중심이며 `ReferenceReceiver` 479~507행은 frame의 `sent_at`으로 stale을 계산한다. source의 의미 검사와 수신 단조 시계를 모델링하지 않는다.

| 재현 입력 | ReferenceReceiver | validate_snapshot |
|---|---|---|
| reference/sent_at 00:10, source observed_at 00:00, available/stale=false | accepted=true, stale=false | `STALE_THRESHOLD_EXCEEDED` |
| reference/sent_at 00:10, source observed_at 00:11 | accepted=true, stale=false | `FUTURE_TIMESTAMP` |

원인: receiver는 `decode_frame_line`의 schema·CRC·순번과 envelope 시각을 확인하지만 source semantic validator를 호출하지 않는다. 문서에 적힌 host-only 범위를 넘어서 그 성공을 firmware freshness 합격 근거로 사용하면 잘못된 판정이 된다. 이 재현은 실제 ESP32 firmware의 같은 결함을 입증하는 것이 아니다.

조치: source-age와 receive-age를 각각 검사하는 oracle 및 runtime clock anchor 시험을 연결하거나, 이 도구를 frame/sequence 모델로 더 좁게 명시하고 별도 의미 검사를 필수로 연결한다.

**R05 — Major: 과거 실물 실패를 잡는 생산 경로·광학 검증 연결이 부족하다.**

[evaluate-product.py](../../scripts/evaluate-product.py)는 현재도 legacy fixture 파서·상태 seam **29개**를 검사한다. 이 범위에서 payload 대신 상수 42 표시, reset 대신 sent_at 표시, glyph 무늬, 실제 serial backend 부재를 검출하지 않는다. 평가 문서가 이 제한을 밝힌 점은 개선이지만, 새 요구 ID→stimulus→production receiver/state/view-model→기대 값→실물 관찰의 고정 매핑은 [수정 계획](../../docs/plans/2026-10-02-experiment-contract-remediation.md)의 Task 4~5에 남아 있다.

조치: 서로 다른 fixture를 연속 전달해 실제 production view-model의 값·reset·source 변화를 확인하고, device acceptance와 glyph·가독성·30초 유지의 광학 근거를 별도로 수집하는 공통 절차를 고정한다. cdm/1의 ACK 부재를 암묵적으로 바꾸지 않는다. 새 평가 기준의 추가와 기존 기준을 검증할 방법의 구현을 구분한다.

**R06 — Major: 중복 설명의 갱신 누락이 문서 일관성을 깨뜨린다.**

아래는 historical archive의 당시 표현이 아니라, 현재 운영/목적 안내로 연결된 파일에 남은 사례다.

| 위치 | 남은 설명 | 현재 근거와 차이 |
|---|---|---|
| `hardware-feature-discovery.md:18~26` | purpose/environment/YAML/feature/readiness 등을 모든 agent에게 제공 | allowlist는 필수 MD 3개와 명시한 기계 입력만 제공. 옛 목록에 operator-only 문서 포함 |
| 같은 파일 100~103행 | E2E schema가 후보·점수 구조를 직접 포함하지 않음 | schema의 F9.details에 candidates·selected_candidate·score_breakdown이 있고 validator가 검사(379~481행, validator 436~484행) |
| `benchmark-management.md:5~11` | AGY 첫 pilot의 현재 상태가 PILOT_PREPARED, gate의 단일 진실이 기존 readiness | 첫 실행·r21 종료 기록과 10월 2일 새 readiness/운영 계약이 존재. 날짜·cohort 범위 표시가 부족 |
| `PROJECT_PURPOSE.md:47` | ADR-0006이 제안 상태 | ADR 문서는 9월 26일 선택 AGY pilot 범위의 채택을 명시. 과거 채택과 새 baseline 동결을 구분해야 함 |
| 같은 파일 310~319행 | 관련 문서 모두를 함께 읽고 동일하게 제공 | operator가 읽을 문서와 candidate 전달 목록이 구분되지 않음 |
| `agent-experiment-protocol.md:7` | YAML/prompt 동기화가 후속 작업 | 현재 두 파일에는 이미 채택값 반영. runner/후속 feedback 미완료와 분리해야 함 |
| `benchmark-management.md:135~145` | 모델·receipt·telemetry 미완료 설명 반복 | 같은 상태 정보가 두 곳에 있어 이후 또 갱신이 갈릴 수 있음 |

F9 필드 부재는 A02의 설명 오류가 다른 파일에 남은 사례다. 제품·평가 문서 두 곳의 정정만으로 전체 설명이 동기화된 것은 아니다.

조치: 제공 파일 목록은 allowlist, 실행 상태는 next-comparison-readiness, 채택 운영 규칙은 comparison-operating-contract, F9 기계 필드는 schema/validator를 참조한다. 각 설명의 적용 시점·cohort를 표시한다. archived 원본 기록은 수정 대상에서 제외한다.

**R07 — Major: 표면별 실효 권한·환경의 동등성을 새 입력에 대해 확인하지 않았다.**

최초 prompt 49~51행은 여전히 모든 후보에게 `agy-pilot-permissions.json`과 명령별 금지/거부 종료 규칙을 안내한다. 파일 제공은 각 CLI가 같은 capability를 강제한다는 증거가 아니다. `benchmark.py check`는 입력 snapshot·profile 구조·hash를 검사하지만 실제 CLI entitlement, 적용 설정, 읽기/build/test 호출, telemetry를 검증하지 않는다. 이번 입력 check 통과를 그런 live preflight 통과로 해석하지 않았다.

조치: 읽기·쓰기·조회·host build/test·IDF build의 공통 작업군을 각 표면의 실제 도구에 매핑하고 대표 호출·실효 설정·거부 동작을 사전 확인한다. 과거 권한 거부 후 계속 실행한 사실은 지시 준수 결과로 보존하되 모델 능력과 환경 원인을 구분한다.

**R08 — Major(재현성): 독립 artifact 복구가 미완료다.**

현행 문서 41개의 로컬 파일 링크 202개는 이 컴퓨터에서 모두 존재하지만 **8개는 로컬 절대 경로**다. reference와 평가의 일부 핵심 증거는 미추적 results 또는 저장소 밖 benchmark-runs에 있다. Git clone만으로 해당 증거가 복구되는 것은 아니다. 소스 bundle에서 ignore된 frame evidence가 빠졌던 과거 문제를 막는 새 package manifest와 임시 경로 복원 검증은 미완료다.

조치: source와 원본 binaries/frame/log/evidence를 상대 경로·hash의 package manifest로 연결하고 새 경로에서 result validator를 실행한다. 대용량 원본을 main에 모두 커밋할 필요는 없다.

**R09 — Minor: 기존 미추적 비교 보고서에 archive 이동 전 링크가 남았다.**

`results/agy-codex-progress-comparison-20261001.md:57`은 `docs/experiments/codex-reference-build-brief-20260929.md`를 가리키지만 실제 파일은 `docs/archive/experiments/`로 이동했다. 추적 Markdown 90개의 파일 대상 링크에는 누락이 없었고, 기존 미추적 결과 보고서까지 포함한 검사에서 이 1개를 발견했다. URL 접근과 Markdown heading anchor의 유효성은 이번 파일 존재 검사 범위 밖이다.

**4. 문서 중복 평가**

문서 압축은 실질적으로 효과가 있다. integration-contract와 host-device-pipeline-contract가 제품 계약을 가리키는 짧은 안내가 됐고, README·문서 지도·후보 입력의 역할도 선명해졌다.

현행 문서 41개에서 공백을 정규화한 90자 초과 prose paragraph의 완전 일치 중복은 0개다. 제목·code/table/quote로 시작하는 block은 제외한 제한된 검사이므로 의미상 중복이 없다는 뜻은 아니다.

| 반복되는 의미 | 문서들 | 권장 소유자와 처리 |
|---|---|---|
| C/F/I 전체 합격·fixture와 live의 경계 | purpose, product, feature, evaluation, protocol, readiness, management | 제품 의미는 product, 평가 증거는 evaluation. 나머지는 짧은 요약과 링크 |
| F9 후보 3개·선택 1개·30점·구조화 필드 | purpose, product, prompt, hardware-feature-discovery, feature, evaluation, YAML/schema | 후보 동작은 product, 점수 rubric은 자율 기능 평가 문서, 필드는 schema. 동일 상세 필드 설명은 한 곳으로 줄임 |
| 최초/후속 시간·개입·분리 보존 | 운영 계약, readiness, plan, prompt, protocol, management | 운영 계약을 원본으로 유지. prompt는 해당 호출의 행동 요약, readiness는 상태만 관리 |
| 현재 pilot 상태·남은 작업 | management, 기존 readiness, 실행 명령, 새 readiness, plan | 새 readiness는 새 비교 상태, 기존 pilot는 날짜/cohort가 있는 역사 기록 |
| 제공 파일·읽기 범위 | README, purpose, 자율 기능 안내, prompt, 문서 지도, allowlist | 실제 제공 목록은 allowlist. 나머지 목록은 reader 역할과 용도를 명시 |

후보 prompt에 제품 목표를 한두 문장 요약하거나 README가 읽기 순서를 안내하는 반복은 유용하다. 줄일 대상은 자세한 규칙·상태·필드 설명을 여러 문서가 각각 소유하면서 R06 같은 차이가 생기는 반복이다. archive/evidence의 동일 내용 반복은 당시 기록을 보존하는 목적이므로 현행 규칙 중복과 다르게 취급했다.

**5. 직접 실행한 검증 결과**

| 검증 | 결과 | 입증 범위 |
|---|---|---|
| `python -m unittest discover -s scripts/tests -v` | 144개 실행, 143 통과·1 skip, 25.729초, exit 0 | runner/입력 격리/schema/host 도구의 기존 회귀 |
| 정상 E2E 예제 validator | exit 0 VALID | 예제 계약·identity/evidence 연결 |
| provider fixture matrix validator | exit 0 VALID | 정해진 정상/부정 fixture의 분류 |
| invalid-product-pass 예제 | exit 1, `PRODUCT_PASS_REQUIRES_CORE_RESULTS` | 부적절한 제품 합격 주장의 거부 |
| `benchmark.py check` — 정확한 HEAD와 candidate Codex profile | exit 0, inputs_valid, run ID 미예약·worktree 미변경 | 고정 snapshot의 파일·profile/hash 검사. 해당 profile 실행 적격성은 별도 |
| host pipeline dry-run | exit 0, 3,961 bytes, device_accessed=false, collection_failures=[] | host fixture→frame 생성 |
| 제조사 source index | 189/189 파일 존재·SHA-256 일치 | 로컬 공통 source가 고정 index와 동일 |
| Markdown 로컬 파일 링크 | 추적 문서 90개 누락 없음. 현행 41개 링크 202개 존재. 기존 미추적 보고서 1개 누락 | 로컬 파일 대상 존재. 외부 URL/heading anchor는 미검사 |
| 최소 source 시각 재현 | 오래된/미래 source를 host 수신기가 수락, 의미 validator는 거부 | 두 도구의 검사 범위 차이 |
| 최소 summary 재현 | 성공 1+timeout 1 → 표 비율 1.000, timeout은 incomplete로 제외 | 전체 시도/실패 비용 지표 공백 |

unit suite의 symlink skip은 Windows 생성 권한에 따른 것이며 해당 escape 경로의 실행 검증을 통과로 세지 않았다. artifact 디렉터리에는 이번 보고서와 검증 근거만 새로 작성했다. 기존 문서·프로덕션 코드·과거 결과·Git refs는 변경하지 않았다.

재검증:

```powershell
python results/main-purpose-review-20261002/verify_review.py
python -m unittest discover -s scripts/tests -v
```

**6. 품질 체크리스트와 권고**

아래는 새 비교 기준의 품질을 검토하기 위해 이번에 정의한 24개 binary 조건이다. 완전히 확인된 조건만 1점으로 계산했다. 요구사항 충족률·실험 성공률·제품 합격률이나 인증 점수가 아니다. 과거 62.5% 검토와는 checklist가 달라 수치 증감으로 비교하지 않는다.

| 속성 | 확인된 조건 | 미확인/불일치 조건 | 점수 |
|---|---|---|---:|
| 완전성 | 제품/실험 범위 정의; C/F/I/G 결과 구조; null/오류/last-good 규칙 | RM stimulus·복구 package가 모두 완결 | 3/4, 75% |
| 명확성 | 개인/글로벌·token 의미 분리; 수치 timing; 최초/후속 정의 | epoch·fixture anchor·수신 시계가 실행 가능하게 정의 | 3/4, 75% |
| 일관성 | product/prompt/YAML 주요 조건 일치; C/F9 schema/validator 일치 | 모든 운영 문서 상태/필드 설명 일치; runner와 새 운영 정책 일치 | 2/4, 50% |
| 검증 가능성 | 기존 도구 회귀 재실행; 부정 입력 거부; host/실물 증거 경계 명시 | production 표시 의미·광학 추적 시험 완결 | 3/4, 75% |
| 추적성 | 문서 역할/원본 링크; 입력·criteria·파일 hash 연결 | 실제 reference stimulus→증거; C/F/I→runtime→실물 표 완결 | 2/4, 50% |
| 실행 가능성 | credential 없는 fixture 범위; Windows host 시험 실행; 제조사 source hash 일치 | 후속 운영·표면별 실효 정책·독립 복구를 함께 실행 가능 | 3/4, 75% |

합계 **16/24 = 66.7%**. 판단은 **Major Revision — 다음 동일 조건 비교의 운영·검증 연결에 보완 필요**다. 프로젝트 방향을 폐기할 이유는 없으며 전체 후보 제품 합격을 새로운 실행 gate로 추가하는 권고도 아니다.

| 우선순위 | 작업 | 책임 역할 | 완료 시점 | 상대 규모 | 확인 조건 |
|---|---|---|---|---|---|
| P0 | RM의 fixture/hash/기준 시각/명령/expected frame 복구(R02) | maintainer·evaluator | 다음 baseline 동결 전 | 중 | 같은 입력으로 모든 RM 재판정 가능 |
| P0 | 후속 ledger·회차/누적 예산·종료와 gate 적용 연결(R01) | runner maintainer | 다음 수정 비용 비교 전 | 큼 | 3회·7,200초 경계, timeout/중단 포함 비용·직전 commit 추적 |
| P1 | source-age/receive-age와 production 의미·관측 시험 연결(R04/R05) | evaluator·hardware operator | 다음 비교 채점 전 | 큼 | 상수·시각 혼동·검은 LCD가 해당 요구 실패로 판정 |
| P1 | 전체 시도·상태별 실패·실패 비용 집계 추가(R03) | runner maintainer | 다음 비교 보고 전 | 중 | 성공1+timeout1을 조건부/전체 시도 비율로 구분 |
| P1 | 문서의 제공 목록·F9·현재/역사·ADR 상태 정리(R06) | docs maintainer | 다음 baseline 동결 전 | 작음 | allowlist/schema/운영 상태 설명의 상충 없음 |
| P1 | 표면별 capability·effective 설정·telemetry 검증(R07) | operator | 각 표면 실행 준비 시 | 중 | 실제 대표 호출·설정 receipt가 새 입력에 연결 |
| P1 | 독립 source/evidence 복원 검증(R08) | artifact maintainer | 다음 결과 보존·게시 전 | 중 | 임시 경로에서 validator가 모든 증거를 찾음 |
| P2 | 기존 미추적 보고서 archive 링크 수정(R09) | docs maintainer | 보고서 정리 시 | 작음 | 올바른 archive 파일로 이동 |

규모는 계획용 상대 판단이며 일정 약속은 아니다. 이번 작업은 평가·검증과 보고서 작성이며 위 개선을 구현한 작업은 아니다.
