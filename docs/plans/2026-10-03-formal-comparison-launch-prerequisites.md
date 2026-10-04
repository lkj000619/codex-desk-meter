# 정식 비교 시작 전 선행 작업

작성일: 2026-10-03. 재개일: 2026-10-04. 상태: 도구·모델 검증 완료, 최종 동결·예약·복원 연결 중.
실행 요청: 문서를 전체 재검토하고 필요한 선행 작업을 작성·실행한다.
원본: [다음 비교 상태](../experiments/next-comparison-readiness.md),
[실행 경계 검토 E1~E5](../../results/experiment-execution-review-20261003/report.md).

## 목표와 완료 조건

GPT-6를 포함한 활성 5개 조합이 동일 입력·제한·평가 조건에서 시작할 수 있도록 운영 결함을 수정하고,
현재 설치 환경과 실제 모델 도구 실행을 검증한다. 제품 실험 자체와 실물 관측은 준비 이후 단계다.
완료는 아래 작업별 증거로 판정한다. provider 제한 등 외부 실패는 미해결로 기록하며 pass로 바꾸지 않는다.

## 공통 제약과 결정

- 과거 baseline/tag/profile/receipt/판정은 변경하지 않는다. 현재 작업 중이던 보완은 보존한다.
- 후보 필수 입력 57개/MD 3개는 유지한다. 권한 정책은 운영자 설정이므로 후보 입력 포함 여부를 검사한다.
  필수 변경이 입력 bytes에 영향을 주면 새 동결에서 차이를 공개하고 5개 활성 조합에 동일 적용한다.
- `prompt-and-log`, `read_isolation: not_enforced`, `builtin-only-v1`을 유지한다.
  자동 재시도나 Stop hook으로 후보에게 숨겨진 추가 회차를 주지 않는다.
- 신규 실행의 정책 준수 검토는 필수로 만들되 과거 자료를 소급 제외하지 않는다.
  미검토·위반 결과도 전체 시도·비용에는 보존한다.
- 최초 7,200초, 후속 최대 3회·누적 7,200초, 독립 반복 3회라는 조건을 변경하지 않는다.
- 세 개 독립 결함은 파일 소유를 나눠 병렬 보완한다. 설정·전역 상태를 사용하는 실제 CLI 검증은 직렬로 한다.
- 사용자 요청은 계획 작성과 선행 작업 실행을 함께 승인한 것으로 해석한다. 본 제품 과제는 실행하지 않는다.

## 작업과 검증

### 1. E2: 후속 세션에도 동결된 과제와 증거를 전달

- [x] `scripts/comparison_manager.py`와 해당 시험에 실패 회귀 사례를 먼저 추가한다.
- [x] 동결 공통 과제 전문·새 run ID·회차·잔여 예산을 매 fresh session에 다시 전달한다.
- [x] 운영자 원본 증거 경로와 후보용 증거를 분리한다. 후보에는 checkout 안의 자기 자료 상대 경로·hash를 전달한다.
- [x] `benchmark.py`의 immutable 입력 확인과 package 복원까지 증거 연결을 검증한다.
- 완료 조건: 공통 제한 누락, 외부 경로 노출, 후보 증거 변조를 탐지하는 시험 통과.

### 2. E1: 정책 준수와 비교 적격성을 연결

- [x] `scripts/policy_review.py`·검토 CLI·운영 schema·집계 시험을 추가한다.
- [x] 신규 prepare에서 필수 검토를 표시한다. terminal manifest와 충돌하지 않는 별도 검토 기록으로
  run/profile/input/raw 로그/개입 기록을 hash에 연결한다.
- [x] eligible만 품질·순위·reference 도달에 인정한다. invalid/unverified 사유와 전체 비용을 보존한다.
- [x] package에 검토 기록을 보존하고 독립 복원·과거 호환을 검증한다.
- 완료 조건: 미검토/위반/변조 제외, 유효 검토 포함, 실패 비용 보존 회귀 통과.

### 3. E3: 표면별 권한과 공통 명령 일치

- [x] 새 OpenCode profile에서 정상 py_compile 허용, ref 조회 허용 제거, SDK/vendor 파일 편집 거부를 명시한다.
- [x] AGY의 금지된 git log 허용 규칙을 제거한다. 과거 동결 설정은 Git/이전 package에 보존한다.
- [x] 허용·거부 명령 표와 설정 회귀시험을 작성한다. native 실효 설정과 실제 도구 사용 로그를 확인한다.
- 완료 조건: 선언·실효 설정·모델 도구 결과를 구분한 증거, 후보 정상 빌드/시험 능력 확인.

### 4. E4/E5: 실행 안내와 AGY 전역 설정 경합

- [x] 문서의 `benchmark.py run --directory`를 실제 positional 문법으로 수정한다.
- [x] 독립 series별 ledger를 분리하는 명령 예제를 작성한다.
- [x] AGY root 단위 원자적 lock, 정상 복원·중단 복구·다른 backup root 경합 회귀를 구현한다.
- 완료 조건: CLI 구문 일치, 임시 전역 fixture에서 경합 차단과 원본 bytes 복원 검증.

### 5. 실제 환경·모델 capability 검증

- [x] 설치 CLI version/hash, 설정·hook·skills·MCP·plugin inventory, SDK/vendor/ASCII 임시 경로를 재확인한다.
- [x] 제품 구현과 무관한 별도 빈 앱에서 각 profile의 read/write/list/host_build/host_test/
  idf_build/vendor_reference/telemetry/settings를 실제 확인한다. 모든 시도/실패/비용을 보존한다.
- [x] 검증된 사실만 profile에 반영한다. quota/모델 접근/환경 결함으로 확인하지 못하면 pending을 유지한다.
- 완료 조건: 5개 활성 profile에 실제 근거가 연결되거나, 불가능한 항목과 재개 명령·조건을 구체적으로 남김.

### 6. 통합 검증·동결·당일 준비

- [ ] 전체 회귀, fixture validator, 문서 링크, diff 확인과 독립 검토를 수행한다.
- [ ] 새 baseline을 commit/tag로 동결하고 후보 입력 차이를 검증한다.
- [ ] 통과 profile에 대해 실제 시작일 기준 ID·독립 ledger·receipt를 생성하고 hash 결합을 검증한다.
- [ ] 독립 복원 확인, 3개 반복 블록의 실행 순서·단일 보드 관측 배정 절차를 기록한다.
- [ ] 문서 지도·최신 준비 상태·완료 보고서를 갱신한다. 보류/준비 완료 판단과 남은 외부 조건을 명시한다.

## 검토 초점

요구 충족(5개 동일 조건), 논리·상태(후속/검토/복원 순서), 안전 경계(증거 경로/권한/전역 복원),
측정 정확성(실패 비용/미계측/비교 적격성), 유지보수(원본 문서·동결 hash·과거 호환)를 함께 검토한다.

## 진행 기록

- 최초 재검토: E1~E5와 기존 baseline/capability/당일 receipt 미완료를 확인했다.
- 구현 전 판단: 제품 합격을 사전 gate로 추가하지 않는다. 실제 준비 검증 실패는 제품 성능 결과로 집계하지 않는다.
- 2026-10-04 사용자 결정: Claude 제외. 활성 5개×독립 3회=15개 최초 series, 후속 최대 45회, 후보 시간 상한 60시간이다. 모델을 대체하지 않는다.
- E1~E5와 Git 줄바꿈 복원 결함을 보완했다. 독립 최종 검토에서 후속 clone의 bytes·AGY 문법·OpenCode 탭 권한 3건을 추가 수정했다. 최종 회귀 220개 중 219개 통과·symlink 권한 제한 1개 skip, 실패 0개다.
- 활성 5개 실제 모델의 9개 capability와 native inventory를 검증했다. 제외한 Opus 실패와 hook 정정 전 Sol 시도도 비용·원본을 보존했다.
