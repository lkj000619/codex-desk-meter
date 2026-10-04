# 목적·목표 대비 문서 재검증

검토일: 2026-10-03. 기준 HEAD: `681be5315f2b9c3c0e4083527c3ebc38f75b65d6` 및 현재 미커밋 보완·GPT-6 설정.
이 보고서는 이전 판정의 후속 검토이며 과거 보고서·동결 기록을 변경하지 않는다.
범위: 목적·문서 지도·제품/운영/평가 계약·접근 정책·준비 상태·모델 설정과 연결 도구.

## 종합 판단

**목적과 범위 설계는 양호하고, 문서의 구체성도 충분하다. 다만 새 평가 버전의 동결·기록 연결을 보완해야 재현 가능한 본 실험의 기준으로 완결된다.**
Critical 0건, Important 1건, Minor 2건과 선택적 운영 개선 1건을 확인했다.
앞선 '문서상 준비 완료' 설명은 과제·평가 내용의 준비를 뜻하는 범위로 한정한다.
새 평가 문서·도구와 기존 baseline hash 사이의 연결까지 완료됐다는 의미로 읽히면 과도한 판단이다.

프로젝트 목적은 (1) 책상 위 사용량·리셋 디스플레이 제품, (2) AI 에이전트의 첫 결과·후속 수정 비용 비교다.
현재 과제는 Version 2의 fixture collector→정규화→USB→ESP32 상태→LCD 연결이며 live 계정과 Version 1은 후속 단계다.
따라서 fixture 성공을 실제 계정 제품 완성으로, 적은 토큰을 제품 품질로, reference 도달을 전체 합격으로 바꾸지 않는 구조가 목적에 맞는다.
모델 구성은 GPT-6 Sol medium/Luna max와 Muse·Flash·Pro·Opus이고, GPT-6 capability는 아직 미검증이다.

## 강점

- 후보 필수 MD 3개와 운영자 문서·과거 기록을 분리한다. 후보 입력 57개를 allowlist와 hash로 관리한다.
- C/I/F/RM과 G 평가를 통해 기능·통합·화면·기준 도달을 추적한다. stale·sequence·시간·frame 경계가 구체적이다.
- 최초/후속/독립 반복, 실패/미측정/합격, host/실물/live 증거를 구분한다.
- GPT-6 설정을 새 profile로 분리하고 이전 GPT-5.6 검증 사실을 덮어쓰지 않았다. pending 차단은 준비 상태에 맞는 동작이다.
- 이전 검토의 수신 로그 의존 문제는 선택적 receiver-log 설정과 증거 보존으로 완화됐고, RM5 동등 탐색·제품 단계별 완료 목표가 보완됐다.

## R1 · Important · 새 평가 도구·기준과 baseline 식별자의 연결 절차가 미완결

근거: [준비 상태](../../docs/experiments/next-comparison-readiness.md) 66·79~89행,
[운영 관리](../../docs/experiments/benchmark-management.md) 107행,
[입력 hash 계산](../../scripts/benchmark.py) 131~182행,
[package 생성](../../scripts/evidence_package.py) 57~156행.

준비 상태는 제품 baseline `85ba108`을 보존하면서 수정한 관측 도구와 RM5 절차를 별도 snapshot/hash로 고정하도록 한다.
반면 runner의 `evaluation_criteria_sha256`와 `input_bundle_sha256`는 선택한 baseline snapshot에서 계산된다.
그 대상에는 운영 계약·RM 목록·관측 도구가 이미 포함돼 있다. 별도 snapshot을 어떤 파일명/manifest 항목으로
등록하고, 평가 결과와 연결하며, package에 넣어 복원 검증할지에 대한 구체적인 절차가 현재 안내에 없다.
package 도구는 등록된 operator evidence를 담을 수 있으므로 불가능한 설계는 아니다. 다만 자동 포함을 가정할 수 없다.

**재현:** baseline을 임시 경로에 추출하고 profile을 고정한 채 운영 계약·RM 목록·두 관측 도구만 현재 파일로 바꿨다.
후보 입력 inventory는 같지만 평가 hash는 `fa10b1fe…`에서 `fc8faa5a…`로 바뀌고 전체 bundle hash도 달라졌다.
[재현 기록](hash-reproduction.json)에 전체 hash와 대상 파일을 기록했다. 원본 저장소·실험 기록은 수정하지 않았다.

**영향:** 이전 평가 hash를 가진 run을 새 기준으로 평가한 뒤 보완 도구 snapshot을 연결하지 않으면,
제3자가 원래 baseline을 복원해도 실제 사용한 기준·도구를 얻지 못한다. 현재 이미 잘못 채점된 후보가 있다는 뜻은 아니다.

**권고:** 이번처럼 본 실험 전이면 후보 57개 내용은 동일하게 유지하고 보완된 운영 도구·평가 문서를 포함한
새 baseline commit을 고정한 뒤 check/prepare/receipt를 다시 연결하는 방식이 가장 단순하다.
기존 baseline 유지가 필요하면 평가 overlay manifest의 파일 목록·hash·결과 참조·operator evidence 등록·복원 명령을 명시한다.
둘 중 한 방식으로 동일 평가 버전이 manifest→판정→package→독립 복원까지 이어지는 것을 확인한다.
제품 합격을 새로운 시작 gate로 추가할 필요는 없다.

## R2 · Minor · 현재 접근 정책이 과거 gate를 현재 상태 원본으로 연결함

근거: [접근 정책](../../docs/experiments/isolation-policy.md) 64~66행과
[기존 readiness](../../docs/experiments/benchmark-readiness.md) 3~22행.

접근 정책은 '현재 상태'를 기존 `benchmark-readiness.md`로 안내하지만, 대상 문서는 historical 단회 cohort라고 명시한다.
대상 문서에 새 readiness로 가는 안내가 있어 회복 가능하지만, 현재/과거 원본을 한 번 더 해석해야 한다.
**권고:** 현재 실행 상태는 `next-comparison-readiness.md`로 바로 연결하고 R10·기존 gate 참조는 과거 cohort 설명에 한정한다.
과거 원본을 삭제하거나 당시 승인 기록을 현재 것으로 바꾸지 않는다.

## R3 · Minor · F9의 중간 점수에 대한 판정 기준이 GUI보다 약함

근거: [자율 기능 평가](../../docs/experiments/hardware-feature-discovery.md) 104~120행과
[GUI 관찰 조건](../../docs/experiments/feature-comparison.md) 90~105행.

F9에는 총 30점과 '0=증거 없음/중간=부분 충족/만점=전체 충족'이 있지만, 사용자 가치 2점과 4점,
구현 완성도 4점과 8점을 구분할 증거 수준이 구체적이지 않다. GUI는 거리·탐색 시간·오독·독립 채점 기준을 둔다.
**영향:** F9 총점의 작은 차이를 모델 품질 차이로 해석하기 어렵다. 핵심 기능 pass/fail이나 RM 판정을 막는 문제는 아니다.
**권고:** 최소 0/중간/만점의 구체적 예시와 부분점수 배점 규칙, 판정자 차이 조정 방식을 추가한다.
그 전까지 F9는 항목별 근거와 함께 탐색적 보조 지표로 제시한다.

## 선택적 운영 개선 · 전체 실험 규모를 한 곳에서 보여주기

baseline은 모델별 독립 반복 3회, 운영 계약은 최초 2시간+후속 누적 2시간을 정한다.
6개 조합을 모두 3회씩 실행하면 최초 18회, 후속 최대 54회이며 후보 실행 시간 상한은 합계 72시간이다.
준비·평가·flash·관측 시간은 별도다. 병렬 실행 여부에 따라 달력상 소요 시간과는 다르다.
첫 6개 블록과 전체 3회 반복을 구분한 단계표, 평가 슬롯과 중단 판단 시점을 운영 문서에 모으면 실현 가능성을 판단하기 쉽다.
이는 새로운 반복 횟수나 추가 실험을 요구하는 제안이 아니다.

## 여섯 품질 관점

점수는 검토자 판단값이며 시험 통과율·표준 인증·제품 성숙도 수치가 아니다.

| 관점 | 점수 / 100 | 근거 |
|---|---:|---|
| 완전성 | 88 | 현재 제품 과제는 구체적, 평가 버전의 연결 절차 보완 필요 |
| 명확성 | 90 | fixture/live/후속·판정 의미가 분리됨, F9 중간 점수 여지 |
| 일관성 | 82 | 현재/과거 gate 링크와 새 도구/기존 baseline 사이 연결 공백 |
| 검증 가능성 | 88 | 경계값·fixture·회귀·실물 절차 풍부, 실물은 실행 이후 검증 |
| 추적 가능성 | 85 | 요구 ID·evidence·hash 강점, 평가 overlay 식별 연결 미완결 |
| 실현 가능성 | 85 | 환경 준비 근거 존재, GPT-6 capability와 전체 일정은 미완료 |
| 평균 | 86.3 | 조건부 양호. 전면 재작성보다 R1 우선 보완 |

## 이번 검증

- 주요 현재 문서와 연결 도구를 직접 대조했다. 모든 과거 evidence의 내용·외부 하드웨어 사실을 재감사한 것은 아니다.
- 보고서 추가 전 Markdown 113개, 상대 로컬 링크 747건의 파일/디렉터리 대상 누락 0건. 외부 URL·앵커 정확성은 제외했다.
- `python -m unittest discover -s scripts/tests -q`: 181개 중 180개 통과·1개 skip, 실패 0개, 52.802초, exit 0.
  [원본 시험 로그](tests.txt)를 보존한다. Git 줄바꿈 경고가 있어 경고 0으로 표현하지 않는다.
- `python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json`: VALID.
- baseline hash 대조는 후보 입력 유지와 평가/bundle hash 변경을 재현했다. 이는 실제 run을 만든 것이 아니다.
- 실제 GPT-6 capability·계정 quota·보드·광학 관측은 실행하지 않았다. 현재 blocked profile은 알려진 준비 상태이며 새 결함으로 중복 집계하지 않았다.

## 조치 우선순위와 결론

| 순서 | 조치 | 담당 역할 제안 | 시점 | 상대 규모 |
|---|---|---|---|---|
| 1 | R1 새 baseline 또는 평가 overlay 연결 방식을 확정하고 복원까지 검증 | 실행·평가 도구 관리자 | 새 실행 조건 동결 전 | 중 |
| 2 | R2 현재 gate 링크 정리 | 문서 관리자 | 다음 문서 정비 | 소 |
| 3 | R3 F9 점수 예시·부분점수 기준 정리 | 평가자 | 점수 비교 발표 전, 가능하면 후보 결과 확인 전 | 소~중 |
| 4 | 전체 블록/평가 일정 요약 | 실험 운영자 | 실제 일정 수립 시 | 소 |

제품 목적과 실험 목적의 설계는 잘 맞는다. 다만 문서가 잘 작성됐다는 사실과 실행 조건이 완전히
고정됐다는 사실은 다르다. R1과 이미 알려진 GPT-6 실행 준비 조건을 해결한 뒤 본 실험에 사용하는 것을 권고한다.
