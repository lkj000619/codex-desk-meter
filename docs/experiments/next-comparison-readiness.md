# 다음 동일 조건 비교 준비 상태

확인일: 2026-10-02. 상태: **실행 준비 완료·본 실험 시작 전 정지**.

이 문서는 다음 실험을 준비할 때의 진입점이다. 제품 전체 합격을 후보 시작의
전제조건으로 삼지 않는다. 실행 인프라의 준비 상태와 후보 제품 품질을 구분한다.
문서 반영만으로 새 후보 실행이나 중지된 OpenCode 작업을 시작하지 않는다.

## 채택한 조건

- 기준 도달: Codex에서 확인한 기능의 `reference-match`. 전체 `product_pass`는 별도다.
- 한도: 최초 120분, 후속 최대 3회·후속 누적 120분.
- 하드웨어: 보드 사실과 고정 제조사 source만 제공하며 BSP 작성도 후보 비용에 포함.
- 범위: synthetic fixture 기반 Version 2 E2E. 실제 계정 수집은 별도 owner-only 통합.

상세 기준은 [운영 계약](comparison-operating-contract.md),
[기준 기능 목록](reference-match-matrix.md),
[정비 계획](../plans/2026-10-02-experiment-contract-remediation.md)을 따른다.

## 준비 연결 상태

| 순서 | 상태 | 준비 항목 | 현재 근거·완료 조건 |
|---|---|---|---|
| 1 | 완료 | 운영 조건·판정 의미를 문서로 기록 | Q1~Q3 선택과 최초/후속 예산, reference와 전체 합격 구분 |
| 2 | 복구·동결 완료 | reference 입력 복구 | [기계 목록](../../experiments/reference/codex-7923f96/reference-inputs.json)의 raw fixture/hash·기준 시각·원본 collector 호출·seq 0/1 frame·5초 간격을 baseline `85ba108`에 고정. 영상 58/82의 당시 의미는 유지 |
| 3 | 도구 완료·실물 미확인 | clock·production·공통 관측 | source/수신 300초 oracle, 실제 production adapter 실행·hash, 단일 포트 capture, 광학 annotation/frame/지연 결합 구현. 실제 후보 코드 연결·시각 anchor·단절/BOOT/화면 측정은 별도 실행 필요 |
| 4 | 구현 완료 | YAML·최초/후속 prompt 동기화 | 후속 feedback의 직전 run/commit·목표·관측·기대·근거 hash·잔여 회차/초를 manager가 prompt에 고정 |
| 5 | 구현 완료 | runner의 수정 회차·누적 예산·도달 결과 연결 | 최초 7,200초, 후속 최대 3회/누적 7,200초 적용. 자기 직전 frozen bundle 출발·같은 profile·동시 실행 차단·hashed RM 전체 pass 시 종료. 중단은 reconcile 전 새 실행 차단 |
| 6 | 실제 검증 완료 | 원래 pilot gate와 새 비교 적용 범위 연결 | 새 입력/profile에 묶인 CLI 6개 실제 infrastructure/capability receipt를 검증. comparison 없는 historical run의 pilot_pass gate 유지 |
| 7 | 동결 완료 | 새 평가 문서·도구의 입력 hash 연결 | `85ba108`의 operator 도구·reference bytes·criteria hash와 같은 파일 57개/필수 MD 3개를 6개 준비 예약에 연결. 기존 frozen hash 기준 유지 |
| 8 | 실제 검증 완료 | 표면별 CLI/model/설정·권한·계측 | [새 프로필](../../experiments/config/verified-profiles-20261002/README.md)과 native settings/usage·빌드 근거 확인. Flash SDK 컴파일러의 간헐 오류와 Codex 계측기 한계를 [보고서](../../results/experiment-preparation-20261002/report.md)에 명시 |
| 9 | 준비 package 검증 완료 | 독립 복구와 조건 동결 | operator source 186개/package 파일 325개, 6개 원래 commit/tree/input/profile/receipt/준비 artifact를 새 root에서 독립 복원 확인. 제품 terminal artifact package는 실제 후보 종료 후 생성 |
| 10 | 구현 완료 | 전체 시도·실패 비용·도달 비용 집계 | 유효 completed 조건부 표와 별도 전체 시도/실패 비용/coverage, 최초·후속·누적·RM 도달 비용 표시. 후속은 독립 반복 수에서 제외 |

실물 기능 관측과 제품 terminal artifact는 후보 실행 이후의 평가 작업이다.
준비 package의 범위와 날짜별 예약 재생성은 [실행 준비 보고서](../../results/experiment-preparation-20261002/report.md)를 따른다.
후보가 실제 실행에서 기능을 구현하지 못한 경우는
실험 결과이며 이 준비 목록을 다시 제품 합격 gate로 늘리는 이유로 삼지 않는다.

## 후보 입력 경계: 구현 완료

[allowlist](../../experiments/config/agent-inputs.json)는 필수 MD 3개와 기계 입력·지원 도구를
고정한다. runner는 운영자 snapshot에서 전체 입력을 hash한 뒤 목록의 파일만 candidate
checkout에 복사한다. 운영·평가·archive·이전 evidence·결과·runner는 복사하지 않는다.
목록과 각 파일 hash는 run 밖 `candidate-inputs.json`, 후보의
`.benchmark-inputs/input-files.json`에 기록하며 실행 전/후 변경을 거부한다.
새 제품 파일 작성은 허용한다. 외부 읽기의 OS 격리 보장은 별도 접근 정책이다.
과거 policy 없는 frozen baseline의 전달 방식·hash는 변경하지 않는다.

## 이미 존재하는 준비 검증 명령

아래 명령은 로컬 도구 시험과 입력 검사다. 후보 실행·보드 접근은 수행하지 않는다.

```powershell
python -m unittest discover -s scripts/tests -v
python scripts/validate-end-to-end-result.py
python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json
python scripts/benchmark.py check --baseline <고정한-새-commit> --profile <확인한-profile.json>
```

`check`는 선택한 commit의 snapshot에서 입력을 검사하고 run ID를 예약하지 않는다.
`check`는 입력 검사다. 새 예산·후속·reference 관리는 `comparison.py init`으로 ledger를
연결한 run에 적용한다. [도구 안내](comparison-tooling.md)의 receipt·평가·복원 절차와
[구현 계획](../plans/2026-10-02-comparison-tooling.md)의 검증 기록을 따른다.

## 완료 판정과 다음 실행

준비 담당자는 [실행 준비 계획](../plans/2026-10-02-experiment-launch-preparation.md)에
실제 산출물·검증 근거를 연결한다. 이전 tag를
덮어쓰지 않고 모든 후보에 같은 새 입력을 제공한다. 첫 결과는 종료 시 동결하고
후속 수정은 자신의 결과에서 이어서 비용을 기록한다.

실행 시작 시에는 사용할 표면/model·고정 입력·한도·단일 보드 관측 일정을 실제
실행 지시와 연결한다. 이 준비 문서를 작성한 것 자체는 실행 시작이 아니다.
전체 제품 합격이 확인되지 않은 후보도 실패·미도달 결과로 보존한다.

현재 후보 6개는 시작 시각 null·소비 시간 0초로 준비됐으며 제품 실험은 0회다.
예약 ID는 2026-10-02 KST에만 유효하다. 이후 날짜에는 새 ID·ledger를 준비하고
CLI/설정/환경을 재확인한 뒤 receipt를 다시 연결한다. Flash SDK의 간헐적 컴파일러 오류와
provider quota·Codex 원본 계측의 한계는 준비 보고서에 보존했다.
