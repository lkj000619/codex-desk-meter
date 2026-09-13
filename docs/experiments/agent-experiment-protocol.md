# AI 에이전트 비교 실험 프로토콜

이 프로토콜은 동일한 Version 2 과제를 여러 AI 에이전트에 실행하여 구현 품질,
실행 시간, 도구 사용과 토큰 사용을 비교하기 위한 운영 규칙이다. 제품 요구사항은
[Version 2 제품 계약](../PRODUCT_CONTRACT.md), 하드웨어 자율 기능 선택은
[하드웨어 자율 기능 실험](hardware-feature-discovery.md)을 따른다. 실제 CLI·IDE
실행 예시는 [에이전트 실행 명령 템플릿](agent-run-commands.md)을 따른다.
실행 가능 여부는 [benchmark 실행 전 readiness gate](benchmark-readiness.md)가
우선하며, 이 문서 자체는 prompt 전달이나 agent process 시작을 승인하지 않는다.

## 1. 실험 단위와 비교군

브랜치·run ID·반복 격리·계측과 main 게시의 상세 기준은
[benchmark 관리 기준](benchmark-management.md)을 따른다. schema v2 운영 도구와
도구별 sandbox receipt, 모델 확정 및 새 baseline이 준비된 뒤 pilot을 시작한다.

한 번의 실험(run)은 사용자가 승인한 뒤 하나의 에이전트가 하나의 깨끗한 worktree에서
기준 커밋을 출발점으로 제품을 구현하고 자동·실물 시험을 시도하는 과정이다.
문서·schema·runner를 보완하는 현재 단계는 run이 아니다.

기본 비교군은 다음 실행 표면을 별도로 기록한다.

| provider | 실행 표면 | 기본 비교 여부 |
|---|---|---|
| OpenAI | Codex CLI 비대화형 실행 | 포함 |
| Google | Gemini CLI 비대화형 실행 | 포함 |
| Google | Antigravity CLI | 포함 가능. 버전과 계측을 확인한 뒤 고정 |
| Google | Antigravity IDE | 별도 interactive 군. 승인·화면 조작을 기록 |
| 별도 기록 | OpenCode CLI | 대상에 포함. 모델 제공자·정확한 모델 ID·계측 조건 고정 필요 |
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
기록된 ID로 치환한다. **기본 정량 비교군은 prompt 1회·후속 질문 0회·실행 중
외부 피드백 0회**로 고정한다. 사용자가 중간에 답변하거나 구현 방향을 수정하면
원본 run을 즉시 `invalid_for_comparison`으로 보존한다. 대화형 후속 질문을
시험하려면 `interactive` 별도 비교군과 별도 protocol을 미리 선언한다.
인터넷, 검색, MCP, 파일·터미널 권한, 승인 정책과 sandbox 수준도 고정한다.

실험에는 계정 쿠키, Wi-Fi 비밀번호, API 키 또는 개인 사용량 원본을 입력하지
않는다. 개인 사용량은 고정 fixture로 먼저 시험하고, 소유자만 실제 계정 통합
시험을 별도로 수행한다.

첫 hardware-autonomy cohort의 제품 범위는 fixture 기반 firmware·LCD·입력·자율
기능이다. PC agent/provider collector와 PC→ESP32 transport/receiver 통합은 후속
integration cohort다. 범위 밖 계층은 구현하지 않았다는 사실을 실패로 감추지
말고 `not_run; out of cohort`와 필요한 seam/interface를 결과에 남긴다.

## 3. 실행 전 preflight

운영자는 [readiness gate](benchmark-readiness.md)의 R0~R10을 먼저 확인하고,
모든 gate가 통과하며 사용자가 특정 run을 승인한 경우에만 아래를 수행한다.
아래 명령은 준비·검사 명령이지 자동 실행 승인이 아니다.

1. 기준 브랜치에 미커밋 변경이 없고 baseline tag와 commit SHA를 기록한다.
2. 매 run의 실행 checkout을 동일 baseline에서 새로 만들고 이전 결과 접근을 차단한다.
   agent/model 브랜치는 결과 보관용이며 다음 반복의 시작점이 아니다.
3. ESP-IDF v5.3.2와 ASCII 경로를 확인한다.
4. 결과 schema와 기능·GUI 확장 계약이 고정되었는지 확인한다. 예시 validator
   실행만으로 새 결과의 합격을 주장하지 않는다.
5. 보드가 필요한 실행이면 COM3가 연결되고 다른 프로세스가 포트를 점유하지
   않는지 확인한다.
6. 보드 리비전, 플래시 백업 SHA-256, TF 카드 장착 여부와 네트워크 시험 조건을
   manifest에 기록한다.
7. prompt·config·fixture 해시와 agent/model/tool 버전을 기록한다.

preflight가 실패하면 본 실험을 시작하지 않고 pilot 준비 상태로만 기록한다.

### 역할 경계

- **maintainer:** 실행 전에 목적·계약·prompt·schema·profile을 고정한다.
- **agent:** 고정된 checkout 안에서만 구현·자체 시험·결과 초안을 작성한다.
- **evaluator:** 종료 후 동결된 artifact를 read-only로 공통 평가한다. 평가 중
  agent에게 수정 방향을 알려주지 않는다.
- **hardware operator:** 별도 승인 뒤에만 COM3를 점유해 flash·사진·영상·로그를
  수집한다. agent가 임의로 보드를 초기화하지 않는다.
- **remediation worker:** 평가가 끝난 뒤 별도 branch에서 수리한다. 원본 점수와
  구현 commit을 덮어쓰지 않는다.

## 4. 시간과 명령 측정

- `started_at`은 공통 프롬프트를 에이전트에게 전달한 UTC 시각이다.
- `ended_at`은 에이전트가 종료 메시지와 결과 파일을 남긴 UTC 시각이다.
- 시각과 경과 시간은 운영 실행기가 기록한다. 준비 시간·종료 후 운영자 실물 평가는
  별도로 기록한다. 중단 시에도 실행 종료 시각과 부분 결과를 보존한다.
- 경과 시간은 단조 시계로 측정하고 UTC 시각 차이와 교차 검사한다. 대기·승인·다운로드 시간도 제외하지 않는다.
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

R0~R9 gate가 모두 통과하고 R10 사용자 승인이 남은 뒤 각 실행 표면에서 1회씩
수행한다. 목적은 프롬프트, 권한, validator, fixture,
보드 슬롯과 로그 수집이 실제로 작동하는지 확인하는 것이다. pilot 결과는 순위
통계에 포함하지 않는다.

### 본 실험

pilot이 통과한 뒤 에이전트·모델별로 최소 3회 반복한다. 실행 순서는 무작위로
섞고, 반복 사이에 동일한 기준 상태를 복원한다. 모델 버전, reasoning level,
승인 정책이 바뀌면 새로운 비교군으로 분리한다.

실행 순서의 seed와 비교군 ID를 보존한다. pilot·중단·환경 실패를 식별하고,
성공/시도 수를 시간 중앙값과 함께 표시한다. 3회 결과로 확정적인 우열을 주장하지 않는다.

## 7. 채점

먼저 C1~C8 핵심 요구사항을 합격/부분합격/실패로 판정한다. 핵심 요구사항이
실패한 run은 자율 기능 점수가 높아도 제품 합격 run으로 표시하지 않는다.

제품 pipeline 기능은 [기능·LCD GUI 비교 기준](feature-comparison.md)의 F1~F9로
분리해 상태와 증거를 기록한다. 특히 F1(PC collector)과 F3(PC→ESP32 transport)은
fixture-only firmware cohort에서 자동으로 합격 처리하지 않으며, 범위 밖이면
`not_run; out of cohort`로 남긴다. F5 LCD GUI의 G1~G6 점수(총 18점)는 C2
하드웨어 gate와 별도이며, 실물 사진·영상 없이 확정하지 않는다.

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

7. F1~F9 기능 상태와 G1~G6 GUI rubric(실험군 범위·증거 포함)

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
