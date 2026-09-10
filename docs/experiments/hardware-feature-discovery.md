# 하드웨어 기반 자율 기능 실험

## 목적

동일한 핵심 과제를 받은 각 AI 에이전트가 대상 보드의 하드웨어 사양을 어떻게
해석하고 어떤 추가 기능을 선택하는지 비교한다. 이 실험은 단순 아이디어 제안이
아니라 선택한 기능의 구현과 검증까지 포함한다.

핵심 제품 요구사항 평가는 모든 에이전트에 동일하게 적용한다. 하드웨어 자율
기능은 별도 점수로 평가하여, 추가 기능 때문에 핵심 기능의 미완성을 가리지
않도록 한다.

## 고정 입력

모든 에이전트에 다음 파일의 동일 커밋을 제공한다.

- `docs/PROJECT_PURPOSE.md`
- `docs/hardware/version-2-capabilities.md`
- `docs/DEVELOPMENT_ENVIRONMENT.md`
- `experiments/config/version-2-baseline.yaml`
- `experiments/prompts/version-2-agent-task.md`

공식 제조사 문서를 추가로 조회할 수 있지만, 인터넷 접근 허용 여부는 동일
비교군의 모든 실행에서 같아야 한다. 에이전트별로 다른 힌트나 기능 예시를
추가 제공하지 않는다.

## 기본 실행 규칙

1. 에이전트는 핵심 요구사항과 전체 하드웨어 카탈로그를 먼저 읽는다.
2. 하드웨어를 활용한 기능 후보를 정확히 3개 작성한다.
3. 각 후보에 사용자 가치, 사용 자원, 구현 비용, 위험과 검증 방법을 기록한다.
4. 에이전트가 사용자에게 선택을 넘기지 않고 후보 1개를 스스로 선택한다.
5. 선택 기능을 핵심 기능과 분리된 모듈 또는 선택 가능한 설정으로 구현한다.
6. 자동 검증과 실제 보드 검증 절차를 함께 작성한다.
7. 선택하지 않은 후보와 탈락 이유도 결과에 보존한다.

안전, 인증 정보 또는 외부 서비스 변경처럼 새로운 권한이 필요한 경우에는
자율 선택보다 해당 제한이 우선한다.

## 범위 제한

- 후보 수: 정확히 3개
- 구현 수: 정확히 1개
- 외부 하드웨어 추가: 금지
- 제조사 예제 코드를 그대로 노출하는 기능: 추가 기능으로 불인정
- 핵심 요구사항 제거 또는 축소: 금지
- Version 2 전용 기능의 Version 1 필수화: 금지

후보 수와 구현 수를 바꾸려면 비교 실행을 시작하기 전에 구성 파일을 변경하고,
같은 비교군 전체에 동일하게 적용한다.

## 결과 기록

각 실행은 최소한 다음 내용을 남긴다.

```text
run_id
agent / model / version / reasoning level
base commit
hardware profile revision
candidate features[3]
selected feature and rationale
implementation files and commits
build and automated test results
hardware verification result
hardware discovery phase start/end time
input/output/cache/total tokens when available
user intervention count
failures and unresolved risks
```

실행 manifest는 `experiments/schema/run-manifest.schema.json`, 구조화 결과는
`experiments/schema/hardware-feature-result.schema.json`을 따른다. 권장 결과
경로는 다음과 같다.

```text
docs/agent-runs/<run-id>/hardware-feature-selection.md
results/<run-id>/hardware-feature.json
```

## 평가

최종 점수는 운영자가 구현 commit과 증거를 검토해 기록한다. 에이전트 자체 평가는
참고 자료로 구분한다. 각 항목에서 0점은 증거 없음, 중간 점수는 부분 충족,
만점은 기준 전체 충족으로 판정하고 점수별 근거를 남긴다. 실물 미검증 구현은
구현 완성도 만점을 부여하지 않는다. 동일 평가표와 판정 기준을 비교군 전체에 적용한다.

핵심 요구사항은 기존 합격 기준으로 먼저 평가한다. 자율 기능은 다음 30점
척도로 별도 채점한다.

| 평가 항목 | 점수 | 판단 기준 |
|---|---:|---|
| 하드웨어 이해 | 5 | 실제 사양과 제약을 정확히 사용했는가 |
| 사용자 가치 | 5 | 책상 위 사용 경험이나 안정성을 개선하는가 |
| 선택 논리 | 5 | 후보 비교와 최종 선택 근거가 명확한가 |
| 구현 완성도 | 10 | 빌드·테스트·실물 동작과 오류 처리가 충분한가 |
| 분리와 이식성 | 5 | 핵심 로직 및 Version 1과 불필요하게 결합하지 않았는가 |

구현하지 못한 기능은 아이디어가 좋아도 구현 완성도 점수를 받을 수 없다.
반대로 단순한 기능을 구현했다는 이유만으로 선택 논리나 사용자 가치 점수를
자동으로 부여하지 않는다.

## 시간·토큰 해석

전체 실행의 시간과 토큰을 기본 비교값으로 사용하고, 도구가 지원하면 자율 기능
탐색 단계의 시작·종료 시각과 토큰을 별도로 기록한다. 토큰은 입력·출력·캐시·
reasoning·전체를 분리하고, 제공자가 공개하지 않으면 `null`과 사유를 기록한다.
서로 다른 제공자의 tokenizer와 reasoning 집계는 직접 합산하지 않는다. 자율
기능 점수와 비용을 함께 제시하되, 낮은 비용만으로 더 좋은 결과라고 판단하지
않는다. 반복 횟수·무작위 순서·하드웨어 슬롯은
[에이전트 실험 프로토콜](agent-experiment-protocol.md)을 따른다.
