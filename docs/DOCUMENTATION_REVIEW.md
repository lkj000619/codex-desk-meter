# 문서 정합성 검토 — 2026-09-20

## 상태와 검토 기준

문서 검토·수정·종합 완료. 기준 HEAD는 `47b720d7f29185dd63a0d72737897966a4ea335f`이며,
후속 작업과 재개 지점은 [진행 체크리스트](DOCUMENTATION_REVIEW_CHECKLIST.md)를 따른다.
저장소에 추적된 MD 42개를 대상으로 본문을 검토했다. 로컬 설치 스킬과 생성
artifact는 제품 문서 목록에 포함하지 않는다. 적용되는 AGENTS.md는 저장소 및
상위 경로에서 발견되지 않았다. requirement-review의 여섯 품질 축을 적용한다.
문서별 역할·상태·읽는 순서는 [문서 지도](DOCUMENTATION_MAP.md)에 정리했다.

판정: 문서만으로 고칠 수 있는 설명·참조 문제는 수정했다. 목적과 E2E 평가의
큰 구조는 구체적이지만, formal E2E 준비 완료 판정은 **주요 보완 필요**다.
실행·평가·보존의 연결, token 정의, C별 판정, baseline 설정과 gate 의존 순서가
남아 있다. 아래 점수는 이번 검토의 checklist 기반 평가이며 제품 품질 점수나
R0~R10 상태 변경이 아니다.

## 목적과 현재 범위

- 제품: 화면 전환 없이 책상에서 사용량·개인 리셋·글로벌 리셋을 확인한다.
- 실험: 동일 입력으로 agent/model/설정의 기능·품질·시간·토큰을 비교한다.
- 현재 목표: Version 2, ESP-IDF v5.3.2, fixture collector부터 ESP32/LCD까지 E2E.
- 검토 중 계약의 선택: USB serial `cdm/1`, 가로 820×320, resets 단일 표시.
  ADR-0005/0006은 제안 상태이며 baseline 동결·실행 승인을 뜻하지 않는다.
- 후속: 실제 계정의 owner-only integration, Version 1 이식, 별도 Wi-Fi cohort.
- 완료 조건: C1~C8·I1~I4·F1~F9 및 실물 증거와 G1~G6 평가를 구분해 확인.
  host 시뮬레이션이나 schema 통과만으로 제품 합격을 선언하지 않는다.

근거: [목적](PROJECT_PURPOSE.md), [제품 계약](PRODUCT_CONTRACT.md),
[기능 비교](experiments/feature-comparison.md),
[현재 gate](experiments/benchmark-readiness.md).

## 발견 사항과 처리 결과

| ID | 심각도 | 근거와 영향 | 처리 결과 |
|---|---|---|---|
| D01 | Major | 목적 §3.1·README의 예측 표시와 C4~C6의 표시 제외 충돌 | 수정: 파서 호환과 화면 목표 분리, README USB/후속 Wi-Fi도 구분 |
| D02 | Minor | 목적 §4.5는 버전 추후 확정, 승인 ADR-0004는 v5.3.2 | 수정: 승인된 결정 연결; Version 1 검증은 후속으로 유지 |
| D03 | Major | 제안 ADR-0006을 ADR-0003에서 대체 완료로 서술; 계약의 동결 상태 불명확 | 수정: 제안 반영과 승인·동결 구분, 승인 상태 유지 |
| D04 | Minor | readiness의 현재 미커밋 설명과 검토 시작 Git 상태 불일치 | 수정: historical tag와 현재 HEAD/작업 상태 구분, 실제 tag 3개 확인 |
| D05 | Major | protocol 기본 Gemini 표, profile README 순서가 R4 후속 기록과 불일치 | 수정: 저장소 현재 계획으로 정렬, 과거 preflight JSON은 예제로 표시; 외부 서비스 사실 재검증 아님 |
| D06 | Major | 자율 기능·실행 가이드가 E2E 대신 historical 결과만 안내 | 수정: 운영 manifest/E2E 평가 manifest/결과 분리, F9 선택 문서 참조 |
| D07 | Major | `benchmark.py:archive_run`은 historical schema만 정규화; 가이드는 E2E 보존 완료처럼 읽힘 | 한계 명시 완료; 평가 manifest·archive·집계 연결의 구현은 후속 |
| D08 | Major | `evaluate-product.py:check`는 legacy source/windows 원형을 기대하지만 평가 계약은 최신 UsageSnapshot 출력으로 설명 | 수정: 현행 legacy 회귀 interface 문서화, E2E 전체 검사와 구분; 도구는 변경하지 않음 |
| D09 | Major | runner OpenCode total은 provider 합계, E2E validator는 input+output만 허용 | 한계 명시 완료; 변환 정책·schema/코드 연결 후속 |
| D10 | Major | E2E schema/validator에 C1~C8 개별 판정 필드가 없지만 계약은 전부 pass 요구 | 한계 명시 완료; 운영자 C별 증거 필요, 구조화 연결 후속 |
| D11 | Major | baseline YAML의 `live_api_allowed_after_fixture: true`와 fixture-only 문서 경계 충돌 | 문서의 owner-only 범위 명확화; YAML 정합화 후속 |
| D12 | Minor | fixture 중복, 과거 junction, 오래된 CLI/계측, 잘못된 PowerShell stdin 예시, BOOT 역할·종료 시각 혼동 | 수정: 중복 제거·시점별 기록 참조·runner argv 표기·역할/시각 정리 |
| D13 | Major | 제품 §3 모델에 실제 schema 필수 키 `unit`, `last_good_at`, `error_reason` 누락 | 수정: 필수 키 보충과 schema 링크; schema 변경 없음 |
| D14 | Major | 관리 문서는 모든 gate 뒤 baseline, R1은 baseline 동결 필요. R4는 prepare 통과 필요, readiness는 모든 gate 전 ID 예약 금지 | 순환 의존을 gate 문서에 명시; 준비/실행 단계 분리안과 후속 결정 기록 |

### 코드 대조 근거와 재현 방법

- D07: [runner](../scripts/benchmark.py)의 `prepare`는 E2E 결과 경로를 선택하지만
  `archive_run`은 `hardware-feature-result.schema.json`만 검증한다. 별도
  [E2E 평가 manifest schema](../experiments/schema/end-to-end-manifest.schema.json)는
  운영 manifest와 구조가 다르다. [summary](../scripts/summarize-benchmark.py)는
  manifest 행만 출력하며 통계·F/I/G 결과를 계산하지 않는다.
- D08: [evaluator](../scripts/evaluate-product.py)의 `cases`/`check`와
  `scripts/tests/test_benchmark.py`의 `EvaluatorTests`를 대조했다. personal 입력은
  `source=fixture`, 원본 windows의 `id`를 유지하지만 E2E 모델은 `source_kind`,
  `window_id`를 사용한다. 새 제품 요구를 legacy 출력으로 축소하지 않았다.
- D09: runner `telemetry`와 [E2E validator](../scripts/validate-end-to-end-result.py)의
  `_check_telemetry`를 대조했다. 저장된 OpenCode probe 예시 2005+15와 원본 total
  2065는 다르다. 기존 테스트의 provider total 보존과 E2E input+output 검사는
  각각 통과하지만 두 계약을 직접 연결할 수 있다는 검증은 아니다.
- D10: [E2E result schema](../experiments/schema/end-to-end-result.schema.json)와
  `_check_product_pass`는 F/I/validation/G를 검사하며 C1~C8 개별 결과는 검사하지
  않는다. F9도 상태·증거만 기록하며 후보 3개·30점 세부 구조는 선택 문서에 남겨야 한다.
- D11: [baseline YAML](../experiments/config/version-2-baseline.yaml)의 live 허용 키가
  true다. scripts에서 해당 키를 직접 소비하는 코드는 검색으로 발견하지 못했다.
  즉 이번 검토가 실제 live 호출을 발견한 것은 아니며, 고정 입력을 읽는 agent가
  범위를 오해할 수 있는 계약 불일치다.
- D13: [UsageSnapshot schema](../experiments/schema/usage-snapshot.schema.json)의
  required 키를 제품 문서와 대조했다.
- D14: [관리 기준](experiments/benchmark-management.md) §상태,
  [R4 종료 조건](experiments/r4-profile-resolution.md),
  [readiness](experiments/benchmark-readiness.md) §필수 gate를 대조했다.

## 품질 평가

각 축에 아래 네 조건을 두고 충족 1점, 미충족 0점으로 계산했다. 부분 구현의
존재만으로 완료 처리하지 않았다. 대상은 정비 후 문서와 구현 연결의 준비도다.

| 축 | 충족한 조건 | 미충족 조건 | 점수 |
|---|---|---|---:|
| 완전성 | 제품/실험 목적 구분; 현재/후속/제외 범위; 계층별 F/I/G 기준 | E2E C별 판정과 보존 경로의 전체 연결 | 3/4 = 75% |
| 명확성 | 문서 역할·상태; 표시/파서 범위; legacy/E2E interface; 미측정/시뮬레이션 구분 | 없음(이번 검토 기준) | 4/4 = 100% |
| 일관성 | 제품·prompt의 E2E 범위; snapshot schema 설명 | 원본/정규화 token 및 live 설정 정합화; gate 의존 순서 | 2/4 = 50% |
| 검증 가능성 | 시간·stale 수치 기준; 오류 fixture; F/I/G 증거 규칙 | C1~C8 전체를 E2E validator로 검증 | 3/4 = 75% |
| 추적 가능성 | 문서 지도; 요구 ID와 도구 대응; 시점별 증거 구분 | run→평가 manifest→archive/집계 연결 | 3/4 = 75% |
| 실현 가능성 | offline 도구 검증; 환경·보드 제약 기록 | 모델·설정·receipt 확정; 실제 candidate/하드웨어 검증 | 2/4 = 50% |

총 **17/24 = 70.8%**. 통계적 측정이나 산업 표준 인증 점수가 아니라 명시한
24조건의 충족률이다. 문서 정비 작업은 완료했지만 정식 benchmark 준비 완료를
선언할 수준은 아니다. 특히 테스트 통과가 위 미충족 조건의 해소를 뜻하지 않는다.

## 미해결 결정·구현 후보

문서 범위를 넘어서는 코드·schema·baseline 설정은 이번 검토에서 변경하지 않는다.
아래는 원인과 필요한 완료 증거를 보존하기 위한 목록이며 실행 승인이 아니다.

- D14: **먼저** gate 의존 순서 결정. 권고안은 run ID를 만들지 않는 입력/profile
  검증 → R1 동결 → profile-bound receipt 검토 → 조건부 승인 발효 확인 → 실제
  prepare/run 순서다. R4의 `prepare 통과`를 준비 검사와 실행 직전 재검사로 나누는
  방안을 권고한다. 문서 간 종료 조건을 함께 바꿔야 하므로 승인 상태는 변경하지 않았다.
- D11: baseline의 live API 플래그를 fixture-only와 일치시키고, owner-only live
  조건을 별도 cohort에 두는 방안을 권고한다. 결정 후 config·prompt 대조 검증.
- D09: 원본 total·정의는 보존하고 E2E 정규화 total을 별도로 기록하는 방안을
  권고한다. 변환 정책을 먼저 확정하고 missing telemetry와 합계 불일치 회귀 시험.
- D10: C1~C8 개별 판정을 E2E schema/validator에 추가하고, 누락·fail·not_run 상태에서
  product_pass 거부를 검증하는 방안을 권고한다. F9 세부 평가 연결도 함께 검토한다.
- D07: 위 계약 확정 뒤 E2E 평가 manifest 생성·archive 정규화·결과 집계 연결.
  후보 원본 보존, manifest identity, schema 버전 및 실패 결과 보존 회귀 시험 필요.
- 모델·reasoning·settings inventory, profile-bound receipt, ADR 검토와 동결,
  실물 시험은 기존 readiness 잔여 작업이다. 2026-09-18 조건부 승인 기록은
  보존하되 이번 문서 작업으로 발효 처리하지 않는다.

모든 후속 항목의 우선 기한은 **새 E2E baseline 동결/정식 pilot 전**이다.
계약·gate 결정은 maintainer, runner 연결은 runner maintainer, C별 schema는
evaluator maintainer, 실물 증거는 hardware operator가 담당한다. 역할 배정이며
실제 사람·일정·노력 추정치는 확정하지 않았다. 실행 가능한 체크박스는
[진행 기록](DOCUMENTATION_REVIEW_CHECKLIST.md)에 있다.

## 변경 범위

- 기존 MD 19개 수정: README, 목적·제품·개발환경, ADR-0003 설명 주석,
  protocol/run/usage/management/readiness/evaluation/feature/autonomy/integration,
  하드웨어 카탈로그, profile/example/fixture 안내, 결과 인덱스.
- MD 3개 추가: 문서 지도, 본 검토 보고서, 진행·재개 체크리스트.
- 코드·JSON schema·fixture·YAML·공통 agent prompt는 변경하지 않았다.
- 날짜별 과거 보고서의 관측값·승인 기록·시험 수는 보존했다. 해당 자료의 역할은
  문서 지도에서 구분했다. ADR-0003의 수정은 후속 제안 상태를 설명하는 주석뿐이다.

## 확인한 baseline ref

로컬 tag를 commit으로 해석한 값이다. 이 목록은 새 baseline 승인 기록이 아니다.

| tag | commit |
|---|---|
| `version-2-baseline-20260911` | `abed99c4bdded2366a719fdc7f7e8a49e60570ac` |
| `benchmark-v2-baseline-20260911` | `34a1790ffeb31d47c1ae78c78a14d7cf4e318c6f` |
| `benchmark-v2-baseline-20260914` | `1b5ce1c26a52d2dc72b6f771e575aa0e75843ce0` |

## 검증

2026-09-20, 로컬 Python에서 `PYTHONUTF8=1`, `PYTHONDONTWRITEBYTECODE=1`로 실행했다.

| 실행한 검사 | exit | 결과 |
|---|---:|---|
| `python -m unittest discover -s scripts/tests -p 'test_*.py' -v` | 0 | 기존 63개 테스트 통과, 8.993초 |
| `python scripts/validate-end-to-end-result.py` | 0 | E2E 기본 합성 예제 통과 |
| `python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json` | 0 | provider matrix 통과 |
| `python scripts/validate-experiment-result.py` | 0 | historical 예제 통과 |
| `python scripts/run-host-device-pipeline.py --dry-run` | 0 | 3961 bytes, collection_failures=[], device_accessed=false |
| 로컬 Markdown 링크·지도 목록 검사 | 0 | 최종 MD 45개, 로컬 링크 209개 모두 존재, 기존 42개 지도 누락 없음 |
| 모델 필드·요구 ID·변경 범위 검사 | 0 | UsageSnapshot 필수 키 누락 0, C1~C8/F1~F9/I1~I4/G1~G6 확인, non-MD 변경 0, 신규 문서 trailing whitespace 0 |
| `git diff --check` | 0 | 공백 오류 없음 |

host dry-run frame SHA-256:
`02724a9eff07e5667cdd3b0056ffe301e6be85d66ed130cf34d2e6a7ca24feec`.
기존 테스트는 임시 저장소의 synthetic prepare/archive를 포함하며 실제 모델 실행은
하지 않는다. 새 테스트를 만들거나 제품 firmware를 빌드하지 않았다.

검토 중 일부 탐색 명령은 잘못된 Windows glob·존재하지 않는 예상 test 파일 때문에
실패했고 실제 파일 목록으로 수정했다. 두 patch는 문맥 불일치로 적용되지 않아
수정 후 다시 적용했다. 최종 테스트 실패를 숨긴 것이 아니며, 위 검증은 실제
성공한 실행 결과다.

## 관측 한계

- 외부 URL 응답, 최신 CLI/API 제공 조건, 제조사 사양을 이번 작업에서 재조회하지
  않았다. 해당 문서의 날짜별 주장과 repository 내부 정합성만 검토했다.
- 링크 검사는 로컬 Markdown 대상 경로의 존재 검사다. 외부 링크·heading anchor,
  inline-code 경로 전부의 유효성 보장은 아니다.
- 저장소 밖 과거 영상·로그·백업 hash는 재검증하지 않았다. 식별 가능한 파일명·hash를
  보존했고, 과거 절대 사용자 경로의 공개 여부는 배포 전 별도 검토 대상이다.
- provider 자격증명·모델·COM3·실물 장치에 접근하지 않았다. 실제 제품 구현·통합
  합격이나 신규 R4/R5 receipt가 생긴 것은 아니다.
- commit/push/tag/stage는 현재 저장소에 수행하지 않았다. 산출물은 로컬 변경으로
  남아 있으므로 재개 시 파일 존재와 Git diff부터 확인한다.
