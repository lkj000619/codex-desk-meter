# AI 에이전트 비교 실험 프로토콜

이 프로토콜은 동일한 Version 2 과제를 여러 AI 에이전트에 실행하여 구현 품질,
실행 시간, 도구 사용과 토큰 사용을 비교하기 위한 운영 규칙이다. 제품 요구사항은
[Version 2 제품 계약](../PRODUCT_CONTRACT.md), 하드웨어 자율 기능 선택은
[하드웨어 자율 기능 실험](hardware-feature-discovery.md)을 따른다. 실제 CLI·IDE
실행 예시는 [에이전트 실행 명령 템플릿](agent-run-commands.md)을 따른다.

## 1. 실험 단위와 비교군

한 번의 실험(run)은 하나의 에이전트가 하나의 깨끗한 worktree에서 기준 커밋을
출발점으로 제품을 구현하고 자동·실물 시험을 시도하는 과정이다.

기본 비교군은 다음 실행 표면을 별도로 기록한다.

| provider | 실행 표면 | 기본 비교 여부 |
|---|---|---|
| OpenAI | Codex CLI 비대화형 실행 | 포함 |
| Google | Gemini CLI 비대화형 실행 | 포함 |
| Google | Antigravity CLI | 포함 가능. 버전과 계측을 확인한 뒤 고정 |
| Google | Antigravity IDE | 별도 interactive 군. 승인·화면 조작을 기록 |
| OpenAI | 일반 ChatGPT 웹 대화 | 기본 비교 제외. 로컬 저장소·COM3·토큰 계측 조건이 다름 |

“ChatGPT”라는 이름으로 실행할 때는 실제로 Codex CLI인지 ChatGPT 제품인지
manifest에 명시한다. 모델 이름만 같게 하고 실행 표면이 다른 실행을 같은
비교군의 반복으로 합치지 않는다.

## 2. 고정해야 할 입력

실험 시작 전에 다음을 하나의 baseline tag와 SHA-256 목록으로 고정한다.

- 제품 계약, 하드웨어 카탈로그, 개발환경 문서
- `experiments/config/version-2-baseline.yaml`
- `experiments/prompts/version-2-agent-task.md`
- `experiments/fixtures/`의 입력 데이터
- 스키마와 validator

공통 프롬프트는 바이트 단위로 동일하게 전달한다. `<run-id>`만 실행 manifest에
기록된 ID로 치환하며, 후속 질문은 모든 비교군에 동일한 순서와 문구로 전달한다.
인터넷, 검색, MCP, 파일·터미널 권한, 승인 정책과 sandbox 수준도 고정한다.

실험에는 계정 쿠키, Wi-Fi 비밀번호, API 키 또는 개인 사용량 원본을 입력하지
않는다. 개인 사용량은 고정 fixture로 먼저 시험하고, 소유자만 실제 계정 통합
시험을 별도로 수행한다.

## 3. 실행 전 preflight

운영자는 아래 순서로 확인한다.

1. 기준 브랜치에 미커밋 변경이 없고 baseline tag와 commit SHA를 기록한다.
2. 에이전트별 독립 branch/worktree를 기준 commit에서 만든다.
3. ESP-IDF v5.3.2와 ASCII 경로를 확인한다.
4. `python scripts/validate-experiment-result.py`를 실행한다.
5. 보드가 필요한 실행이면 COM3가 연결되고 다른 프로세스가 포트를 점유하지
   않는지 확인한다.
6. 보드 리비전, 플래시 백업 SHA-256, TF 카드 장착 여부와 네트워크 시험 조건을
   manifest에 기록한다.
7. prompt·config·fixture 해시와 agent/model/tool 버전을 기록한다.

preflight가 실패하면 본 실험을 시작하지 않고 pilot 준비 상태로만 기록한다.

## 4. 시간과 명령 측정

- `started_at`은 공통 프롬프트를 에이전트에게 전달한 UTC 시각이다.
- `ended_at`은 에이전트가 종료 메시지와 결과 파일을 남긴 UTC 시각이다.
- wall-clock은 두 시각의 차이로 계산하고, 대기·승인·다운로드 시간도 제외하지 않는다.
- 기본 hard timeout은 120분이다. timeout 뒤의 작업은 같은 run에 이어 붙이지 않는다.
- 모든 터미널 명령, 도구 호출, 실패 명령, 사용자 개입과 중단 사유를 보존한다.
- 에이전트가 실행한 플래시 명령은 명령문과 대상 포트를 기록한다. `erase_flash`는
  에이전트에게 허용하지 않고, 기준 이미지 복원은 운영자가 별도 기록으로 수행한다.

에이전트가 제공하는 토큰 사용량은 `input`, `output`, `cached`, `reasoning`,
`total`을 가능한 만큼 각각 기록한다. 제공자가 토큰을 공개하지 않으면 `null`과
측정 불가 사유를 기록한다.

## 5. 하드웨어 슬롯 운영

현재 기준 장치는 COM3 한 대이므로 하드웨어 시험은 병렬 실행하지 않는다.

```text
기준 이미지·NVS 상태 확인
        ↓
에이전트 build/자동 시험
        ↓
운영자 승인 후 COM3 flash
        ↓
LCD·BOOT·RST·오류·네트워크 시험
        ↓
로그·사진/영상·SHA-256 보존
        ↓
다음 run 전 기준 상태 복원
```

각 run은 이전 run의 NVS, 캐시, 화면 자산과 Wi-Fi 상태에 의존하지 않아야 한다.
복원이 필요한 경우 운영자는 저장된 16MiB 백업과 해시를 확인한 뒤 복원하고,
복원 시각과 명령을 manifest에 남긴다.

## 6. pilot과 본 실험

### Pilot

각 실행 표면에서 1회씩 수행한다. 목적은 프롬프트, 권한, validator, fixture,
보드 슬롯과 로그 수집이 실제로 작동하는지 확인하는 것이다. pilot 결과는 순위
통계에 포함하지 않는다.

### 본 실험

pilot이 통과한 뒤 에이전트·모델별로 최소 3회 반복한다. 실행 순서는 무작위로
섞고, 반복 사이에 동일한 기준 상태를 복원한다. 모델 버전, reasoning level,
승인 정책이 바뀌면 새로운 비교군으로 분리한다.

## 7. 채점

먼저 C1~C8 핵심 요구사항을 합격/부분합격/실패로 판정한다. 핵심 요구사항이
실패한 run은 자율 기능 점수가 높아도 제품 합격 run으로 표시하지 않는다.

하드웨어 자율 기능은 별도 30점으로 채점한다.

| 항목 | 점수 |
|---|---:|
| 하드웨어 이해 | 5 |
| 사용자 가치 | 5 |
| 선택 논리 | 5 |
| 구현 완성도 | 10 |
| 핵심 코드와의 분리·이식성 | 5 |

비교 요약은 평균만 사용하지 않고 반복 결과의 중앙값과 범위를 함께 표시한다.
주요 지표는 다음 순서로 제시한다.

1. 핵심 요구사항 합격 여부
2. 실물 시험 합격 여부
3. 자율 기능 점수
4. wall-clock 중앙값과 범위
5. 실패 명령·사용자 개입 수
6. 제공자별 토큰 구성

서로 다른 제공자의 토큰 수는 tokenizer와 reasoning/cache 집계가 다르므로 하나의
절대 효율 순위로 합치지 않는다.

## 8. 결과 보존과 개인정보

각 run은 다음 파일을 보존한다.

```text
docs/agent-runs/<run-id>/hardware-feature-selection.md
results/<run-id>/run-manifest.json
results/<run-id>/hardware-feature.json
results/<run-id>/commands.jsonl
results/<run-id>/logs/
```

구조화 결과는 `experiments/schema/`를 통과해야 한다. 원본 로그에 Authorization,
Cookie, Wi-Fi 자격증명, 개인 계정 식별자와 민감한 프롬프트가 들어가면 저장 전에
마스킹한다. 실패 결과와 중단 결과도 삭제하지 않고 `status`와 사유를 기록한다.

## 9. OpenAI Evals와의 관계

OpenAI 공식 문서의 eval 개념처럼 데이터 입력 스키마와 testing criteria를 먼저
정의하고 같은 기준을 여러 모델에 적용한다. 이 저장소의 JSON Schema와 C1~C8
채점표가 하드웨어 실험의 고정 기준이며, 특정 제공자의 eval 서비스 사용 여부와
무관하게 로컬 결과를 재현할 수 있어야 한다.
