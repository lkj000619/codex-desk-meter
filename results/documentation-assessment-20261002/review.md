# 프로젝트 목적·문서 품질 검토

검토일: 2026-10-02. 검토 기준 commit: `681be5315f2b9c3c0e4083527c3ebc38f75b65d6`.
이 보고서는 해당 시점의 후속 검토다. 이전 보고서의 원본 판정·evidence·동결 baseline을 변경하지 않는다.

## 종합 판단

**문서 구조와 요구사항의 구체성은 양호하다. 평가 계약 보완을 조건으로 활용 가능하다.**
검토 범위에서 Critical 0건, Major 1건, Minor 3건을 발견했다.
주요 문제는 문서 수보다, 후보에게 공개한 요구와 실제 평가 도구 사이의 누락 및 현재 상태의 중복 서술이다.
이 판단은 본 실험 시작 승인이나 제품 합격 판정이 아니다.

프로젝트는 두 결과를 함께 추구한다.

1. PC의 사용량·개인 리셋·글로벌 리셋 상태를 책상 위 디스플레이에서 확인하는 제품.
2. 같은 제품 개발 과제를 받은 AI 에이전트의 첫 결과 품질과 후속 수정 비용을 비교하는 재현 가능한 실험.

현재 구현 과제는 Version 2 보드와 ESP-IDF v5.3.2에서 fixture collector → 정규화 → USB serial → ESP32 receiver/cache/stale → LCD를 연결하는 것이다.
실제 계정 수집, Version 1 이식, Wi-Fi transport는 이번 비교 범위 밖이다.
최초 120분과 후속 최대 3회·누적 120분을 구분하고, Codex reference 기능 도달과 전체 제품 합격을 따로 판정한다.
현재 준비 문서는 6개 후보의 실행 준비 완료·제품 실험 0회를 보고한다. 이번 검토에서 CLI capability나 실물 상태를 다시 측정한 것은 아니다.

근거: [목적](../../docs/PROJECT_PURPOSE.md), [제품 계약](../../docs/PRODUCT_CONTRACT.md),
[운영 계약](../../docs/experiments/comparison-operating-contract.md), [준비 상태](../../docs/experiments/next-comparison-readiness.md).

## 잘 작성된 부분

- **독자와 원본의 구분:** 후보용 필수 MD 3개, 운영·평가 문서, 과거 기록을 문서 지도와 allowlist로 분리한다. plans/design/archive의 역할도 분명하다.
- **시험 가능한 제품 조건:** stale 0/299/300초, 65,536-byte frame 제한, 순번 wraparound, 재연결 5초, LCD 반영 2초, BOOT 300ms 등 경계값이 있다.
- **증거 해석의 절제:** schema 통과·host oracle·실물 동작·실제 계정 연동을 구분한다. 26.87초 reference 영상으로 30초 유지 성공을 주장하지 않는다.
- **실험 무결성:** 첫 실패 보존, 후속 수정 비용 분리, 토큰 원본과 정규화 값 구분, 미측정 null 보존, 입력 hash와 복원 package를 연결한다.
- **과거 기록 보존:** 과거 cohort의 판정과 새 운영 조건을 분리하고 후속 정정 날짜·범위를 표시한다.

## 상세 발견 사항

### DOC-01 · Major · 후보 계약에 없는 수신 로그 형식을 평가 도구가 요구함

근거: [제품 계약 3·5절](../../docs/PRODUCT_CONTRACT.md),
[capture 구현](../../scripts/product_observation.py), [광학 결합 구현](../../scripts/production_evaluation.py),
[후보 allowlist](../../experiments/config/agent-inputs.json).

`product_observation.py:172`는 `CDM_RX sequence=<n> result=0` 패턴을 찾을 때만 `accepted_at_seconds`를 채운다.
`production_evaluation.py:127-129`는 이 값이 없으면 `optical observation has no accepted frame` 오류로 광학 관측 결합을 거부한다.
그러나 후보용 제품 계약은 raw log와 실제 수신 검증을 요구할 뿐 이 문자열이나 동등한 로그 연결 인터페이스를 정의하지 않는다.
도구 안내에는 marker 이름이 있지만 후보에게 전달되지 않는다. `--writer-adapter`는 송신을 연결하며 수신 로그 형식의 차이를 해소하지 않는다.

**영향:** `RX seq=1 accepted`처럼 다른 형식으로 정상 수신을 기록한 후보는 제품 동작과 무관하게 공통 자동 광학 평가 경로가 막힐 수 있다.
이는 모든 수동 RM 평가가 불가능하다는 뜻이나 실제 후보가 실패했다는 뜻은 아니다. 미공개 도구 관례가 평가 부담을 추가한다는 문제다.

**권고:** 수신 로그를 운영자가 읽는 adapter를 정의해 후보별 동등한 증거를 연결하거나, 공통 marker의 형식·발행 시점·sequence 의미를 후보 계약에 명시한다.
새 요구를 이미 동결된 입력에 조용히 추가하지 않는다. 입력을 바꿀 경우 모든 후보에 같은 새 baseline/hash를 적용한다.
원본 capture를 수동 수정해 수신 시각을 채우는 방식은 피한다.

**완료 조건:** 계약상 허용한 로그 형식마다 raw bytes→수신 시각→동일 frame→광학 관측의 연결을 검증하고, 평가 도구의 미지원 형식을 제품 실패로 오판하지 않는다.

### DOC-02 · Minor · 현재 상태가 여러 문서에서 다르게 표현됨

근거: [README](../../README.md), [준비 상태](../../docs/experiments/next-comparison-readiness.md),
[운영 계약](../../docs/experiments/comparison-operating-contract.md), [도구 안내](../../docs/experiments/comparison-tooling.md).

README는 실제 표면 권한 확인·새 입력 동결이 남았다고 설명하지만 준비 상태는 각각 실제 검증 완료·동결 완료로 기록한다.
운영 계약 49~50행은 구조화 기록 연결을 후속 작업으로 설명하지만 도구 안내에는 RM review JSON과 `comparison.py review`가 이미 정의돼 있다.
준비 보고서가 명확하므로 전체 준비 근거가 없는 것은 아니다. 진입 문서의 상태 요약이 뒤처진 문제다.

**권고:** README는 현재 상태를 직접 나열하기보다 준비 상태 문서로 연결한다.
운영 계약에는 현재 사용하는 별도 RM review/ledger 형식을 연결하고, 후보 result schema에 새 필드를 넣지 않는 규칙은 유지한다.
동결 YAML의 `planning`·`hash freeze pending` 표현은 원본을 소급 변경하지 말고 템플릿 상태와 실제 freeze 기록의 차이를 설명한다.

**완료 조건:** 최신 진입 문서끼리 미완료 항목이 일치하고, 과거·템플릿·실제 준비 상태를 독자가 구분할 수 있다.

### DOC-03 · Minor · RM5의 동등한 탐색 판정이 아직 운영자 재량에 의존함

근거: [RM5와 입력 동결 전 보완 목록](../../docs/experiments/reference-match-matrix.md),
[제품 계약 92행](../../docs/PRODUCT_CONTRACT.md), [GUI 관찰 조건](../../docs/experiments/feature-comparison.md).

RM5는 세 화면 순환 또는 동등한 탐색을 허용하고, 마지막 체크리스트에는 동일 관찰 조건 적용이 미체크로 남아 있다.
GUI에는 거리·시각 식별 과제 등 공통 조건이 있으나, 탭·스크롤·한 화면 구성의 어느 범위를 RM5의 동등한 탐색으로 인정할지는 구체적이지 않다.
미체크 자체가 준비 실패를 뜻하지는 않는다. 실행 이후 적용할 항목인지, 실행 전에 정할 항목인지 구분이 필요하다.

**권고:** 필수 정보의 도달 가능성, BOOT의 역할, 시작 상태, 조작 순서와 증거를 사전에 정한다.
RM5에 reference에서 미입증인 정밀 300ms 조건을 추가하지 말고 C8에서 따로 판정한다.
체크리스트를 '규칙 확정'과 '각 후보에 적용'으로 구분한다.

**완료 조건:** 서로 다른 UI 구성의 예시를 같은 규칙으로 판정할 수 있고 후보 결과를 본 뒤 기준을 바꾸지 않는다.

### DOC-04 · Minor · 장기 제품 목표의 완료 조건이 실험 목표보다 약함

근거: [프로젝트 목적 3·7절](../../docs/PROJECT_PURPOSE.md), [제품 계약 범위](../../docs/PRODUCT_CONTRACT.md).

이번 fixture E2E 범위는 충분히 구체적이다. 반면 장기 목표인 실시간에 가까운 실제 계정 표시와 책상 위 지속 사용에는
live source 전환의 완료 조건, 연속 운용 시간, 사용자 가독성 확인의 목표가 아직 모여 있지 않다.
이는 현재 fixture 비교의 결함이나 착수 전 추가 gate가 아니라 장기 제품 완성 판단의 공백이다.

**권고:** 기존 목적 문서에 fixture E2E / owner-only live / Version 1 이식의 단계별 완료 조건과 근거 링크를 짧게 추가한다.
live 단계에서 허용 source·오류/갱신 동작·연속 운용 검증 목표를 정하되 현재 후보 과제에 소급하지 않는다.

## 품질 평가

점수는 여섯 관점의 검토자 판단값이며 요구사항 통과율, 제품 성숙도, 외부 표준 인증 점수가 아니다.

| 관점 | 점수 / 100 | 판단 근거 |
|---|---:|---|
| 완전성 | 84 | 현재 E2E 범위는 상세하나 관측 로그 계약과 장기 완료 조건에 공백 |
| 명확성 | 87 | 범위·경계값 명확, 동등한 탐색의 해석 여지 |
| 일관성 | 80 | 현재 상태 서술 일부 지연, 평가 도구의 숨은 형식 의존 |
| 검증 가능성 | 88 | 경계 시험·fixture·증거 도구 강점, 후보 연결은 추가 확인 필요 |
| 추적 가능성 | 93 | C/I/F/RM ID, schema, hash, evidence, 문서 지도 연결 |
| 실현 가능성 | 82 | 준비 검증 근거와 예산 명시, 실제 후보 E2E·실물 달성은 아직 미확인 |
| 평균 | 85.7 | 구조 전면 개편보다 계약 누락·상태 관리 보완을 권고 |

## 이번에 수행한 검증과 한계

- Git 추적 Markdown 107개에서 정규식으로 추출한 상대 로컬 링크 687건: 대상 누락 0건. 앵커·외부 URL·HTML 링크·자유 형식 경로는 이 수치에 포함하지 않는다.
- `python -m unittest discover -s scripts/tests -q`: 176개, 175개 통과·1개 skip, exit 0, 55.034초. Git 줄바꿈 경고 등이 출력됐으며 경고 0이라고 주장하지 않는다.
- `python scripts/validate-end-to-end-result.py`: VALID, exit 0.
- `python scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json`: VALID, exit 0.
- 후보 allowlist: 57개 파일·필수 MD 3개 확인. 관측 marker의 후보 계약 노출 여부와 capture/광학 결합 구현을 대조했다.
- 주요 목적·제품·운영·평가·준비 문서를 정독하고 연결된 계획·보고서·도구를 대조했다. Markdown 107개 전체의 모든 문장을 내용 감사한 것은 아니다.
- 기존 실제 CLI·package 복원 결과는 해당 보고서의 근거로 읽었다. 이번에 이를 재실행하거나 외부 제조사 사실·서비스 현황·SDK 호환성·실물 동작을 독립 검증하지 않았다.
- 테스트 통과는 문서 완전성이나 제품 합격을 증명하지 않는다. DOC-01의 미공개 로그 형식 의존은 현재 회귀시험이 통과해도 남는다.

## 권고 순서

아래 담당 역할·시점은 제안이며 배정이나 실행 승인이 아니다. 소요 규모는 상대적인 추정이다.

| 우선순위 | 조치 | 담당 역할 | 권장 시점 | 규모 |
|---|---|---|---|---|
| 1 | DOC-01 관측 계약·adapter 경계 정리 | 평가 도구·제품 계약 관리자 | 후보별 공통 평가 방식 확정 전; 후보 입력 변경은 실행 전 동일 동결 | 중 |
| 2 | DOC-03 RM5 동등성 규칙 확정 | 실험 운영자·평가자 | 후보 결과를 보기 전 | 소 |
| 3 | DOC-02 최신 상태 참조 정리 | 문서 관리자 | 다음 문서 정비 | 소 |
| 4 | DOC-04 제품 단계별 완료 조건 정리 | 제품 소유자 | live 통합 착수 전 | 소~중 |

문서를 더 잘게 나누거나 과거 기록을 삭제할 필요는 없다. 현재 문서 지도를 유지하고
원본 요구→후보 제공 입력→평가 도구→관측 증거 사이의 누락을 메우는 것이 가장 효과적이다.
