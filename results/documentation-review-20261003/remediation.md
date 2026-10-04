# 문서 재검증 피드백 보완 결과

확인일: 2026-10-03. 대상: [재검증 보고서](report.md)의 R1~R3 및 선택적 일정 개선.
원본 보고서의 당시 판정과 `85ba1089226a2e3198983a42eea375a3fd7e6ed0`의
과거 baseline·receipt·package는 변경하지 않았다. 본 모델 실험은 시작하지 않았다.

## 반영 내용

| 항목 | 반영과 확인 경계 |
|---|---|
| R1 | 새 비교는 후보 입력 57개를 유지한 새 공통 baseline commit을 쓰도록 [준비 상태](../../docs/experiments/next-comparison-readiness.md)와 [도구 안내](../../docs/experiments/comparison-tooling.md)를 통일했다. `prepare`가 전체 Git snapshot ZIP과 profile을 후보 checkout 밖에 hash로 보존하고, 후속 회차가 이어받는다. package 생성·독립 복원 시 원본 평가·입력 hash를 재계산한다. 과거 ZIP 없는 package는 이전 방식으로 복원한다. 실제 새 commit 동결은 아직 하지 않았다. |
| R2 | [접근 정책](../../docs/experiments/isolation-policy.md)의 현재 상태 링크를 새 준비 상태로 바꾸고 기존 gate를 과거 단회 cohort로 한정했다. |
| R3 | [F9 기준](../../docs/experiments/hardware-feature-discovery.md)에 5점 항목별 다섯 증거 조건, 구현 10점의 다섯 0~2점 축, 미검증 처리, 독립 채점과 이견 조정을 추가했다. 새 비교에만 적용한다. |
| 일정 | [운영 계약](../../docs/experiments/comparison-operating-contract.md)에 6개 조합×독립 반복 3회의 3블록, 최초 18회·후속 최대 54회·후보 실행 시간 상한 72시간, 단일 보드 슬롯과 블록별 중단 기록을 명시했다. 준비·평가·관측 시간은 별도다. |

## 검증

- 전체 회귀: `python -m unittest discover -s scripts/tests -q`에서 **182개 실행, 181개 통과·1개 skip, 실패 0개** (94.115초). [원본 로그](remediation-tests.txt).
- 전체 회귀 뒤 보존 도구 자체의 hash 민감도 단언을 기존 시험에 추가하고 해당 시험 1개를 다시 실행해 통과했다.
- 최초/후속 합성 run에서 baseline ZIP/profile을 보존하고 package 생성 후 별도 root에 복원했다. 복원 보고서의 `operator_baseline_verified`를 확인했다. 평가 hash 변조도 거부됨을 회귀시험으로 확인했다.
- `python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json`: VALID.
- allowlist 57개는 과거 `85ba108`과 현재 HEAD의 Git blob 바이트가 모두 같다. 작업 트리의 3개 파일은 CRLF 차이만 있으며 새 baseline 비교는 `git archive` 바이트로 수행하도록 정했다.
- Markdown 115개에서 로컬 상대 링크 774개 대상 누락 0개. `git diff --check` 오류 0개(줄바꿈 변환 경고는 있음).

## 실행 준비의 잔여 조건

이 결과는 도구·평가 기준의 보완 검증이다. 실제 새 비교의 재현 기준으로 쓰기 전에는
보완 문서와 도구를 새 commit으로 고정하고 깨끗한 checkout에서 57개 archive 바이트·전체 회귀를
다시 확인해야 한다. GPT-6 두 profile의 `pending` capability 검증, 모든 후보의 당일 환경 확인,
새 run ID·ledger·receipt 연결도 남아 있다. 이 조건을 충족했다는 기록이나 제품·실물 시험 결과는 없다.
