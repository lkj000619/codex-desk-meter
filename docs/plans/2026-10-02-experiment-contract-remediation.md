# 실험 기준 문서 정비 계획

상태: 2026-10-02 문서 정비·입력 축소 완료 항목과 남은 구현 작업을 기록한다.
실제 작업 방법은 현재 사용자 요청과 환경에 맞춰 선택한다.

2026-10-02 후속 구현: 아래 문서 정비 당시의 완료 기록은 보존한다. 당시 남겨둔
예산·집계·관측·복원·reference 연결은 [구현 계획](2026-10-02-comparison-tooling.md)에서 진행했다.
현재 남은 실측·동결 상태는 [readiness](../experiments/next-comparison-readiness.md)를 따른다.

**Goal:** 세 에이전트 실험에서 발견한 문서 결함을 정리하고, 동일 시작 조건의 첫 결과와 수정 비용을 해석할 수 있는 기준 문서를 만든다.

**Architecture:** 제품 계약, 실험 운영 규칙, 기계 결과 계약, 시점별 증거의 역할을 구분한다. 현재 schema 설명 오류를 정정하고 사용자가 선택한 비교 목표·수정 예산·BSP 제공 수준을 공통 운영 계약에 반영한다. 실제 후보 구현과 과거 frozen 입력은 변경하지 않는다.

**Tech Stack:** Markdown, Git, 기존 JSON Schema/Python unittest 기반 계약 검증. 제품 대상은 ESP-IDF v5.3.2·Waveshare ESP32-S3-LCD-3.16이다.

**Spec:** [세 에이전트 결과에 따른 아키텍처 평가](../experiments/architecture-review-20261002.md). 기존 채택 방향은 [reference-comparison-20260929.md](../experiments/reference-comparison-20260929.md)다.

## Global Constraints

- 최초 계획 작성 브랜치는 `docs/architecture-review-20261002`였다. 입력 축소와 이번 문서 정비의 대상은 로컬 `main`이다. 과거 검증·커밋 기록은 해당 작업 시점의 범위로 읽는다.
- 과거 입력 `aab0d493888f4fc0bb6eff726bfe7d93b167543c`와 원본 run·점수·코드 commit은 변경하지 않는다.
- 동일 비교군은 같은 제품 코드 없는 시작 자료·최초 prompt template·정책을 받는다. run ID 치환 후 전달 hash도 별도로 기록한다.
- fixture-only E2E와 owner-only live integration은 분리한다. 계정·credential source를 이 정비에서 추가하지 않는다.
- cdm/1은 host-to-device이며 ACK가 없다. 문서 정비로 ACK나 retry protocol을 암묵적으로 추가하지 않는다.
- validator 통과·host 시험·device acceptance·광학 LCD 출력·제품 합격을 별도 판정한다.
- token 원본 input/output/cached/reasoning/provider_total과 정의를 보존한다. 정규화 total은 input+output이며 cached/reasoning을 더하지 않는다.
- COM3를 열거나 flash·후보 실행을 하지 않는다. OpenCode 사용자 중지 상태를 유지한다.
- 이 계획의 질문 답변은 비교 설계값이며 새 실험 실행 지시로 해석하지 않는다.

## Review Focus

1. reference 제품에도 미확인인 항목을 후보의 필수 reference-match 합격 조건으로 끼워 넣지 않는다 → Task 2의 목표 목록 검토.
2. runtime uptime을 epoch로 비교해 정상 frame을 거부하거나 source timestamp를 송신 시각으로 덮어쓰지 않는다 → Task 3의 clock 시나리오.
3. host parser/GUI marker 성공으로 상수 표시·문자 미출력·검은 화면을 놓치지 않는다 → Task 4의 의미 연결과 광학 매핑.
4. 후보 sender와 운영자 capture의 별도 port open으로 수락 증거가 사라지거나 전원 제거를 통신 단절로 채점하지 않는다 → Task 5의 단일 소유·powered-disconnect 절차.
5. 명령 표기·정책 차이 또는 누락 evidence를 제품 능력/빠른 성공으로 집계하지 않는다 → Task 6의 capability 분리와 Task 7의 복원 기준.

## 사용자 결정 항목

질문은 2026-10-02에 전달했고 사용자는 세 항목 모두 아래 선택값으로 답했다.
채택된 설계값은 [운영 계약](../experiments/comparison-operating-contract.md)에 기록했다.
최초 YAML·prompt의 조건 반영은 완료했다. 후속 입력·도구 연결과 최종 동결은 별도 작업이다.

| ID | 질문 | 사용자 선택 (2026-10-02) | 검토한 대안 | 영향을 받는 작업 |
|---|---|---|---|---|
| Q1 | 기준 도달의 의미 | 확인된 Codex 기능에 대한 reference-match; 전체 계약 합격은 별도 production-conformance | C1~C8·I1~I4·F1~F9 전체 계약 합격을 도달 조건으로 사용 | Task 2·4·5 |
| Q2 | 공통 최초/후속 실행 한도 | 최초 120분, 후속 최대 3회·누적 120분 | 후속 최대 6회·누적 120분 또는 회차 제한 없이 후속 누적 120분; 최초 120분 유지 | Task 2·6 |
| Q3 | 보드 기반 제공 수준 | 보드 사실·제조사 source만 동일 제공; BSP 작성 비용도 포함 | 검증된 공통 BSP를 제공하고 제품 로직·UI·통합을 비교 | Task 2·3 |

Q2의 누적 120분은 **후속 후보 실행 시간만** 합산한다. 최초 실행과 운영·독립 평가
비용은 별도다. 선택된 조건의 후보 실행 총 한도는 최초 120분+후속 누적 120분이다.
개별 timeout에 걸린 시간도 누적에 포함한다.

Q1~Q3의 사용자 결정은 완료했다. 기준 fixture/hash 복구와 실행 입력 동기화·동결은 남아 있다.

## 파일별 역할

| 파일 | 역할·변경 |
|---|---|
| `docs/experiments/architecture-review-20261002.md` | 평가 근거·A01~A10·원래 상태와 이번 정정 기록 |
| `docs/PRODUCT_CONTRACT.md` | C/I 제품 동작·현재 schema 설명·runtime 시계/관측 경계 |
| `docs/experiments/evaluation-contract.md` | production seam과 요구별 시험·증거 매핑 |
| `docs/archive/reviews/DOCUMENTATION_REVIEW.md` | 과거 D07/D09/D10의 당시 판정과 후속 완료를 구분 |
| `docs/DOCUMENTATION_MAP.md` | 최신 평가·계획·적용 상태의 진입점 |
| `docs/experiments/comparison-operating-contract.md` (Task 2 기록) | 새 비교의 규칙·우선순위·예산·역할을 소유하는 운영 계약 |
| `docs/experiments/reference-match-matrix.md` (Task 2 초안 기록) | 기준 commit에서 확인한 기능·미확인 항목·동일 stimulus·증거 |
| `docs/hardware/version-2-capabilities.md` | 기존 보드 사실·제조사 source 근거의 원본. 별도 보드 계약을 중복 생성하지 않음 |
| 기존 protocol·management·readiness·reference-comparison | 새 운영 계약에 적용/대체 조항을 연결하고 과거 gate를 역사 범위로 구분 |
| `experiments/config/version-2-baseline.yaml`·공통 prompt | 채택 조건 반영 완료. 후속 입력과 runner 연결·최종 동결은 남음; 이전 tag 보존 |
| `docs/experiments/host-device-pipeline-contract.md` | clock/freshness 의미와 단일 소유 관측 절차의 참조 |

## Task 1: 평가를 Git에 기록하고 실제 schema 설명을 정정한다 — A02

**Files:**
- Create: `docs/experiments/architecture-review-20261002.md`
- Modify: `docs/PRODUCT_CONTRACT.md`, `docs/experiments/evaluation-contract.md`, `docs/archive/reviews/DOCUMENTATION_REVIEW.md`, `docs/DOCUMENTATION_MAP.md`
- Evidence: `experiments/schema/end-to-end-result.schema.json`, `scripts/validate-end-to-end-result.py`, `docs/archive/reviews/DOCUMENTATION_REVIEW_CHECKLIST.md`

**Interfaces:**
- Consumes: 기존 core_results required, provider_total 정의, N3/N4 완료 기록.
- Produces: 현재 설명과 과거 평가가 구분된 문서. 제품 schema·코드 동작은 그대로다.

- [x] **Step 1:** 새 docs 계열 브랜치에서 A01~A10 평가를 기록한다.
- [x] **Step 2:** C1~C8 개별 필드 부재 설명을 실제 required와 product_pass 검사로 정정한다.
- [x] **Step 3:** provider_total 원본 보존과 total=input+output의 구현 완료 근거를 연결한다.
- [x] **Step 4:** 2026-09-20 검토 본문·점수는 역사 기록으로 유지하고 후속 완료 주석을 추가한다.
- [x] **Step 5:** `python -m unittest discover -s scripts/tests -p test_validate_end_to_end_result.py -v` 실행: 22개 통과. 기존 required·provider total·invalid product_pass 검사를 확인했다.
- [x] **Step 6:** 링크·문서/schema 대조·`git diff --check`를 통과했고 이번 문서 파일만 커밋 대상으로 지정했다.

## Task 2: 적용 규칙·기준 도달·수정 예산을 한 번 고정한다 — A01/A03

**Files:**
- Create (초안 기록 완료): `docs/experiments/comparison-operating-contract.md`, `docs/experiments/reference-match-matrix.md`
- Modify: `docs/experiments/agent-experiment-protocol.md`, `docs/experiments/benchmark-management.md`, `docs/experiments/benchmark-readiness.md`, `docs/experiments/reference-comparison-20260929.md`, `docs/DOCUMENTATION_MAP.md`, `experiments/config/version-2-baseline.yaml`, `experiments/prompts/version-2-agent-task.md`

**Interfaces:**
- Consumes: Q1/Q2/Q3 응답, 원래 실험 입력 commit, Codex 기준 commit `7923f96`의 확인/미확인 evidence.
- Produces: 최초 실행과 종료 후 수정의 적용 cohort·역할·한도·판정 의미가 일치하는 운영 계약. runner에 없는 기능은 구현 완료로 표현하지 않는다.

- [x] **Step 1:** Q1~Q3 응답을 날짜·선택값과 함께 이 계획 및 새 운영 계약에 기록한다.
- [ ] **Step 2:** reference-match 표의 관찰·기준 evidence 초안은 기록했다. 다음 입력 동결 전 실제 fixture 경로/hash·reference_time·명령·expected frame과 후보 판정 기록 형식을 복구·연결한다. RTC holdover·정밀 latency·30초 유지 등 미입증 항목은 기준 확인으로 채우지 않는다.
- [x] **Step 3:** Q1의 판정과 production-conformance 결과를 별도 이름으로 정의한다. 미검증은 pass로 바꾸지 않는다.
- [x] **Step 4:** Q2의 최초 시간·수정 회차·후속 누적 시간과 timeout/abort 집계 규칙을 기록한다. 수정 회차는 종료 후 별도 지시로 시작한 session이며 실행 내 자체 edit 수가 아니다.
- [x] **Step 5:** 최초 공통 prompt와 후속 피드백 template을 구분한다. 후속 template의 필수 내용은 관측·기대 동작·근거·직전 source commit·누적 한도다. 다른 후보 코드·구현 patch 제공은 개입으로 기록한다.
- [ ] **Step 6:** protocol·readiness·reference-comparison·문서 지도·management의 적용 관계와 최초 YAML·prompt의 조건은 반영했다. 남은 작업은 후속 feedback 입력·runner의 누적 예산·수정 회차·reference 도달 연결과 새 baseline 동결이다. 기존 pilot의 승인/결과는 historical로 보존한다.
- [x] **Step 7:** 문서의 적용 규칙·최초/후속 한도·Q1 판정 이름을 대조했다. Q1~Q3 결정 기록과 실행 준비 완료를 구분했다. 실제 입력·도구 연결의 완료 조건은 새 readiness에 남긴다.

## Task 3: clock과 보드 전제를 명시한다 — A04/A05

**Files:**
- Reference: `docs/hardware/version-2-capabilities.md` (보드 사실의 기존 원본)
- Modify: `docs/PRODUCT_CONTRACT.md`, `docs/experiments/integration-contract.md`, `docs/experiments/host-device-pipeline-contract.md`, `docs/hardware/version-2-capabilities.md`
- Evidence: `docs/hardware/vendor-source-index.json`, `docs/hardware/version-2-bring-up.md`

**Interfaces:**
- Consumes: Q3의 공통 BSP 제공 경계, 제조사 source·hash, 기존 observed_at/last_good_at/sent_at.
- Produces: epoch 유효 여부·monotonic 시간·fixture reference anchor와 source/수신 freshness의 의미; 검증된 보드 사실의 참조 목록.

- [ ] **Step 1:** source observed_at, frame sent_at, 장치 수신 시각, last_good_at의 의미와 단위를 표로 정의한다. uptime을 epoch로 취급하지 않는다.
- [ ] **Step 2:** 제품 계약에 fixture UTC 기준과 monotonic 경과의 구분·시각 미확정 시 unknown·source 시각 보존을 명시했다. 실제 runtime anchor 전달·부팅 후 경과 연결은 후보 절차/production 시험에서 확인해야 한다.
- [ ] **Step 3:** 평가 계약 E2~E4·E6~E7에 reset 경과·source/수신 299/300초·미래 시각·오래된 재전송·재부팅 사례를 연결했다. 실제 시험 입력·부팅 시각 anchor를 동결하고 실행하는 작업은 남아 있다.
- [ ] **Step 4:** 핀·극성·PSRAM/framebuffer·LCD API의 source 근거는 기존 보드 카탈로그를 따른다. 실제 USB-Serial/JTAG·UART 경로와 동작 설정은 실행 기록에서 추가 확인한다. 미확인 값은 확인된 보드 사실로 채우지 않는다.
- [x] **Step 5:** Q3의 보드 사실·제조사 source 제공 경계를 보드 카탈로그·운영 계약·prompt에 연결했다. BSP 구현은 후보 비용에 포함한다.
- [ ] **Step 6:** `python -m unittest discover -s scripts/tests -p test_host_device_pipeline.py -v`로 기존 wire·stale·sequence 계약이 유지됨을 확인한다. 이것은 새 clock 정책의 firmware 실행 검증이 아니다.

## Task 4: 요구사항에서 실제 표시까지의 검증 목록을 연결한다 — A06

**Files:**
- Modify: `docs/experiments/evaluation-contract.md`, `docs/experiments/feature-comparison.md`, `docs/PRODUCT_CONTRACT.md`
- Reference: `scripts/evaluate-product.py`, `experiments/fixtures/provider-fixture-matrix.json`

**Interfaces:**
- Consumes: Task 2의 목표 matrix, Task 3의 clock 의미, 기존 production parser/상태 링크 규칙.
- Produces: `요구 ID / stimulus·기준 시각 / 실행하는 production 경로 / 기대 값·상태 / 증거 종류 / 판정` 표.

- [x] **Step 1:** 평가 계약 E1/E2에 실제 fixture의 window/수치/reset/출처와 기준 시각을 기록하고 legacy→wire 매핑을 연결했다.
- [x] **Step 2:** E1/E2와 clock 절차에 production receiver→state→view-model 전환, 상수 42·reset 대체·uptime/epoch 혼동의 실패 기준을 정의했다.
- [x] **Step 3:** E3~E5에 손상/정상 복구·null/stale/error·last-good 관찰 항목을 정의했다.
- [x] **Step 4:** E1~E8에서 host 값 증거와 광학 증거를 구분했다. legacy 29개 시험의 범위는 그대로다.
- [x] **Step 5:** 새 readiness에 production 자동화·runtime anchor·공통 관측 harness의 미구현/미검증 상태를 명시했다.
- [x] **Step 6:** 기존 실물 채점 표와 E1~E8을 C1~C8·I1~I4·F1~F9에 연결했다. 이 체크는 시험 정의의 완료이며 제품 pass가 아니다.

## Task 5: 실물 관측과 단절 시험을 실행 가능한 절차로 만든다 — A07

**Files:**
- Modify: `docs/PRODUCT_CONTRACT.md`, `docs/experiments/evaluation-contract.md`, `docs/experiments/host-device-pipeline-contract.md`, `docs/experiments/agent-run-commands.md`

**Interfaces:**
- Consumes: cdm/1 ACK 부재·단일 port 소유, Task 2의 판정 목표, Task 4의 증거 표.
- Produces: 후보 sender의 frame sequence/hash→device 수락→화면 관찰을 구분해 연결한 운영자 절차.

- [x] **Step 1:** 실물 채점 표와 E1~E8에 빌드·값/출처·30초/세 화면·입력·갱신의 증거 종류를 연결했다.
- [x] **Step 2:** 평가 계약에 단일 port 소유의 write/capture와 open/reset·DTR/RTS·재열거·capture 실패 기록 절차를 정의했다.
- [x] **Step 3:** E6/E7과 광학 관측 절차에 powered collector/link 단절과 RST/재전원을 구분했다.
- [x] **Step 4:** host write·receiver 수락·가시 갱신의 각 anchor와 측정 해상도·미확인 기록을 정의했다.
- [x] **Step 5:** 공통 harness 구현·실물 확인을 새 readiness에 남겼다. 문서 정의만으로 I3/I4/C2/C8 pass를 표시하지 않는다.

## Task 6: 정책 준수와 실패 분류를 분리한다 — A08

**Files:**
- Modify: `docs/DEVELOPMENT_ENVIRONMENT.md`, `docs/experiments/agent-usage-and-permissions.md`, `docs/experiments/isolation-policy.md`, `docs/experiments/benchmark-management.md`, `docs/experiments/comparison-operating-contract.md`
- Reference: `experiments/config/agy-pilot-permissions.json`, `scripts/agy_pilot_environment.py`, `scripts/tests/test_agy_command_policy.py`, 기존 runner profiles

**Interfaces:**
- Consumes: Task 2의 공통 운영 조건, 표면별 native 도구·허용 작업과 원본 실행 결과.
- Produces: 동일 작업군의 capability 표와 실행/정책/제품/비교 적격성의 별도 해석 규칙.

- [ ] **Step 1:** 권한 안내에 공통 작업군·대표 호출·필요 증거를 정의했다. 실제 표면별 argv/native 도구·실효 설정·허용/거부 로그 연결은 남아 있다. AGY 파일 제공만으로 권한 강제를 입증하지 않는다.
- [ ] **Step 2:** 상대 경로 표기 차이와 명령 허용 여부를 실행 전에 확인할 대표 호출 목록을 정한다. 필요한 정책 정규화가 있으면 별도 구현·검증·다음 baseline 변경으로 기록한다.
- [x] **Step 3:** 운영 계약·권한 안내·management에 실행 상태·지시 준수·제품 판정·비교 적격성을 구분했다. 기존 schema에 없는 필드는 후보 JSON에 추가 요구하지 않는다.
- [x] **Step 4:** prompt의 거부 후 종료 정책을 유지하고 권한 안내에 위반/환경/제품 판정의 별도 보존을 명시했다. 미완료를 빠른 성공으로 집계하지 않는다.
- [ ] **Step 5:** AGY environment_failed와 OpenCode 거부 후 계속 사례로 분류 예시를 작성한다. 과거 원본을 소급 변경하지 않는다.

## Task 7: 현재 상태 탐색과 artifact 복원을 정리한다 — A09/A10

**Files:**
- Modify: `docs/DOCUMENTATION_MAP.md`, `docs/experiments/benchmark-management.md`, `docs/experiments/agent-run-commands.md`
- External notes, 별도 후속: Lab-Notes `00 Home.md`, Codex Desk Meter `Overview.md`

**Interfaces:**
- Consumes: Task 2의 적용 범위, 원본 source/artifact/evidence 위치·hash.
- Produces: 현재 적용 문서와 역사적 상태의 링크, clone과 evidence package의 복구 조건.

- [x] **Step 1:** 문서 지도·readiness·management·실행 예제의 현재/과거 범위를 연결하고 계획을 `docs/plans/`로 이동했다.
- [ ] **Step 2:** Lab-Notes 후속 갱신은 README·템플릿 규칙에 따라 수행하고 Version 1·세로·전망 목표를 역사/후속 범위로 분리한다. 이는 Git docs 커밋의 포함 파일이 아니다.
- [x] **Step 3:** management에 source bundle·binaries/ELF/map/partition·frame/광학/telemetry·manifest의 목록과 상대 경로/hash를 정의했다.
- [ ] **Step 4:** 새 임시 경로의 복원 검증을 완료 조건으로 명시했다. 실제 package 제작과 source/evidence 복원 검증은 미완료다.

## 최초 평가 기록 당시의 검증 범위

아래는 입력 축소 이전 평가 기록의 검증이다. 당시 docs 업데이트는 Task 1과 Task 2의 사용자 결정·운영 계약·기준 목록 초안을
기록한다. 실행 입력 동기화·도구 구현·Lab-Notes 추가 갱신·실험 재개는 완료하지 않았다.

- [x] 변경 Markdown 11개의 로컬 링크 190개 존재를 확인했다. 로컬 전용 evidence는 따로 표시했다.
- [x] 문서/schema의 core_results와 token 설명을 대조했다.
- [x] Task 1의 기존 validator 시험 22개가 통과했다.
- [x] 당시 `git diff --check`가 통과했고 해당 Markdown 11개만 커밋 범위로 지정했다.
- [x] 계획의 A01~A10 누락·결정 의존 관계·파일 경로를 자체 검토했다.
- [x] 최초 평가·채택 조건 기록은 로컬 main 이력에 반영돼 있다. 이 기록은 후속 수정의 자동 commit 지시가 아니다.

현재 남은 작업은 Task 2의 실제 기준 입력·판정 형식 복구와 후속 feedback/runner 연결이다.
원본 코드 수리나 새로운 후보 실행은 이 계획 저장·커밋을 근거로 시작하지 않는다.


## 2026-10-02 승인된 입력 축소 작업

사용자 승인: 후보 입력을 실행 과제·제품 계약·보드 자료로 제한하고 운영/평가·과거 기록을 분리한다.
작업은 현재 main에서 수행한다. 실제 후보 실행·보드 접근·원격 push는 포함하지 않는다.

**설계:** 기존 세 MD 경로를 유지하고 내용 소유자를 명확히 한다. JSON allowlist로
schema/fixture/필요 도구를 선택하고, runner는 전체 baseline을 운영자 임시 snapshot에서
검증한 뒤 허용 파일만 독립 candidate checkout에 복사한다. 운영 criteria hash는
checkout 밖에서 계산한다. 목록·파일 hash를 운영자 증거와 candidate 사본으로 보존하고
실행 전/후 변경을 검사한다. 과거 frozen baseline은 당시 전달 방식을 유지한다.
이것은 제공 파일 제한이며 OS 차원의 외부 읽기 sandbox를 보장하지 않는다.

**변경 파일:** 세 필수 MD, `experiments/config/agent-inputs.json`, `scripts/benchmark.py`,
`README.md`, `docs/DOCUMENTATION_MAP.md`, 관련 운영 안내와 날짜별 검토의 archive 경로.
**검증 파일:** `scripts/tests/test_candidate_bundle.py`, `test_agent_inputs.py`, `test_benchmark.py`.

- [x] 목록 밖 문서/결과/runner, 누락 입력·unsafe path 차단 시험을 먼저 실패시킨다.
- [x] 명시적 파일 목록을 검증·복사하고 input bundle에 내용 hash를 연결한다.
- [x] 운영 criteria는 candidate에게 전달하지 않고 run별 inventory와 immutable 검사에 연결한다.
- [x] 14개 입력 묶음의 전부 읽기 지시를 세 MD와 계층별 필요한 JSON으로 줄인다.
- [x] dated review 17개를 archive로 옮기고 진입 문서·상대 링크를 정리했다. 원본 evidence 212개는 변경하지 않았다.
- [x] 지원 도구 변경 시 bundle hash 변경·입력 변조·실제 prepare 격리·historical 회귀 시험을 확인했다.
- [x] 전체 시험·링크/공백·출처를 확인했다. 검증한 변경은 로컬 main에 commit해 보고한다.

**검토 초점:** 기록 없는 allowlist 누락, 상위/절대/symlink 경로, Git LF/CRLF hash,
기준 MD 수정으로 요구 축소, 기존 baseline 복구 호환성. 후보 제품 파일 생성은 허용하며
제공 기준 파일 변경은 거부한다. 수정 회차 누적 예산·reference fixture 복구·실물 평가 자동화는
기존 Tasks 2~6의 남은 작업으로 유지한다.


입력 축소 검증: 필수 MD 570→245줄, 제공 파일 57개(MD 3 + JSON/도구 54).
전체 133개 시험 중 132개 통과, symlink 생성 권한이 없는 Windows 시험 1개 건너뜀.
마지막 profile snapshot 저장 순서 조정 뒤 runner 회귀 44개도 통과했다.
문서 로컬 링크 272개 누락 없음, 제조사 source 189개 hash 일치,
원본 evidence 212개 Git blob 변경 없음. OS sandbox·실물 동작·새 실험 승인 또는
후속 회차/누적 예산 구현 완료를 주장하지 않는다.

## 2026-10-02 스크립트 중복 축소

사용자 요청에 따라 [공개 Ponytail 원본 지침](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md)을 적용했다. 설치 플러그인의 지침·도구는 이 세션에 노출되지 않았다.
루트 Python 10개 중 allowlist로 후보에게 제공하는 공통 도구는 6개, 운영자용은 4개다.
스키마와 중복된 legacy 검사, 토큰 합산, fixture 어댑터 오류 처리의 중복을 줄였다. CLI·스키마·후보 입력 목록은 유지했다.
시간 파싱·전체 문자열 hash/ID·정수 계측·후보 선택·증거 검사는 보존했다. 날짜 형식 검사기의 선택 의존성과 정규식 `$`의 마지막 개행 허용 때문에 명시적 검사가 필요하다.
실행용 Python은 3,374→3,193줄(181줄, 5.4% 감소). 전체 144개 시험 중 143개 통과, Windows symlink 권한 시험 1개 건너뜀.
기존 검증기와 수정본의 필드 변형·삭제 2,230개에서 합격/불합격 판정이 일치했다. 예제 CLI·fixture matrix 검사와 `git diff --check`도 통과했다.

## 2026-10-02 main 검토 보고서에 따른 문서 정비

[검토 보고서](../../results/main-purpose-review-20261002/review.md)의 발견 사항을 반영한다.
문서 설명·역할·참조 정비가 범위이며 실행 도구·기계 schema·과거 evidence를 수정하는 작업은 아니다.

- R06: F9 기계 구조·후보 입력 목록·ADR 채택·최초 입력 반영 상태를 정정하고 중복 규칙을 원본 문서 참조로 줄였다.
- R04/R05: host frame 모델의 의미 검사 한계를 명시하고 source/수신 시각·E1~E8·광학/단절 관측 절차를 정의했다. 실제 자동화·실물 검증은 남아 있다.
- R03/R07/R08: 집계 범위와 실패 비용 공백, 표면별 capability 확인, 독립 package 복원 조건을 문서화했다. 도구 구현·실효 권한·실제 복원 통과는 남아 있다.
- R09: 기존 미추적 AGY/Codex 비교 보고서의 archive 이동 링크를 정정했다.
- 계획을 도구 이름과 독립된 `docs/plans/`에 배치하고 프로젝트 지침·문서 지도·현행 참조를 갱신했다.

실행 준비의 남은 항목은 [다음 비교 준비 상태](../experiments/next-comparison-readiness.md)가 소유한다.
이번 변경의 검증 결과는 [문서 수정 기록](../../results/main-purpose-review-20261002/document-fixes.md)에 남긴다.
