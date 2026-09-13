# E2E 계약 도구 구현 계획

## 상태와 목적

이 문서는 `version-2-end-to-end-v1` 제품 실험을 실행하기 전에 maintainer가
준비해야 하는 fixture·schema·validator·example의 구현 계획이다. 이 작업은 실험
run이 아니며 agent 제품 구현, COM3 flash, 실제 계정 조회, baseline tag 생성 또는
결과 순위 산출을 하지 않는다.

## 고정 범위

### 1. 공통 snapshot 계약

`experiments/schema/usage-snapshot.schema.json`을 추가한다. 최소 필드는 다음과 같다.

- snapshot identity: schema version, snapshot ID, observed time
- quota identity: provider, agent, host, model, 비식별 account profile
- source/metric: source kind, metric kind, unit, status
- 동적 quota windows: window ID·label·used/remaining/limit·percent·reset
- freshness/error: stale, last-good time, error code와 안전한 reason

provider와 host는 분리한다. Orca·Antigravity·VS Code는 기본적으로 host context이며
OpenAI·Anthropic·Google과 같은 quota provider가 아니다. 원본이 절대 token을
제공하지 않으면 token 수를 만들지 않는다.

### 2. 다중-provider fixture matrix

`experiments/fixtures/providers/` 아래에 최소 다음 사례를 둔다.

1. Codex 정상 percent/window
2. Claude Code 5h·weekly·model sub-limit
3. Gemini CLI 정상 또는 지원 능력 미제공 상태
4. Orca host에서 실행된 Claude Code identity
5. 여러 provider가 동시에 정상
6. 한 provider만 stale/error이고 나머지는 정상
7. reset time 누락
8. percent만 있고 absolute token 없음
9. 실제 absolute token balance가 제공된 사례
10. unsupported provider
11. duplicate provider/window
12. 미래 observed/reset 또는 범위 밖 percent 등 invalid input

fixture는 합성 데이터만 사용하며 credential, 실제 계정 ID와 실제 개인 quota를
포함하지 않는다. 각 fixture에 기대 결과 또는 오류 코드를 기계 판독 가능하게 둔다.

### 3. E2E 결과 계약

`experiments/schema/end-to-end-result.schema.json`을 추가한다.

- `experiment_id`는 `version-2-end-to-end-v1`
- F1~F9, I1~I4 상태와 evidence/reason을 빠짐없이 기록
- G1~G6 점수는 0~3 또는 실물 미평가 시 null+reason
- provider capability/result matrix 기록
- build, host, transport, hardware 검증을 분리
- 시간·agent token telemetry 미제공 값은 null+reason
- hardware 또는 I1~I4가 통과하지 않으면 `product_pass=true` 금지

구조 검증으로 표현하기 어려운 교차 필드 규칙은 validator가 담당한다.

### 4. Example과 validator

다음을 추가한다.

- 정상 E2E result와 hardware-not-run result example
- pass-without-evidence, missing identity, fabricated token, invalid product pass 등
  대표 invalid examples
- `scripts/validate-end-to-end-result.py`
- validator 자체 단위 테스트

validator는 JSON Schema뿐 아니라 manifest/result ID·baseline 일치, 상태별
evidence/reason, evidence 경로 존재, product pass 논리, provider/host identity,
window 중복, 단위와 값의 일관성을 검사한다. 기존 historical schema와 validator의
동작을 깨뜨리지 않는다.

## 작업 순서

1. 기존 schema·validator·example·fixture 관례 조사
2. usage snapshot schema와 fixture matrix 작성
3. E2E result schema 및 valid/invalid examples 작성
4. validator와 테스트 작성
5. 전체 valid example 통과· invalid example 거부 확인
6. 기존 validator 회귀 시험
7. 문서 링크와 readiness 상태 갱신 제안 작성

## 완료 조건

- 모든 JSON 파일이 파싱됨
- 새 valid examples가 schema와 semantic validator를 통과함
- 모든 invalid examples가 의도한 오류 코드로 거부됨
- 기존 historical example/validator가 계속 통과함
- fixture에 credential·실제 quota·절대 사용자 경로가 없음
- `git diff --check` 통과
- 실행한 명령과 종료 코드가 보고됨

## 작업 제한

- benchmark agent나 제품 실험을 실행하지 않는다.
- COM3, ESP32 flash, 실제 provider endpoint와 실제 계정 파일에 접근하지 않는다.
- transport 방식을 임의로 확정하지 않는다.
- commit, push, tag, merge, stage를 수행하지 않는다.
- 기존 사용자의 uncommitted 변경을 되돌리거나 덮어쓰지 않는다.
