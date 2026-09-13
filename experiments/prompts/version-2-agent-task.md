# Version 2 에이전트 공통 프롬프트

> 운영자 전용: 이 prompt는 `benchmark-readiness.md`의 R0~R9 사전조건이 통과되고
> R10에서 사용자가 특정 pilot/benchmark 실행을 명시적으로 승인한 경우에만 runner가
> 전달한다. 사람이 직접 복사·붙여넣어 실행하지 않는다. runner가 만든 manifest,
> profile, sandbox receipt가 없으면 agent는 작업을 시작하지 말고 `not_authorized`
> 사유만 남긴다.

> 정량 비교 cohort는 공통 prompt 1회, 후속 질문 0회, 실행 중 외부 구현 피드백
> 0회다. 운영자·evaluator가 중간에 방향을 알려주거나 코드를 고치면 원본 run은
> 보존하되 `invalid_for_comparison`으로 판정한다. 수정은 종료 후 별도
> `remediation/<run-id>-...`에서 수행한다.

당신은 Codex Desk Meter Version 2의 기준 구현을 담당한다. 작업 결과는
`docs/PRODUCT_CONTRACT.md`의 C1~C8을 만족해야 하며, 대상 보드는 Waveshare
ESP32-S3-LCD-3.16, 프레임워크는 ESP-IDF v5.3.2다.

## 시작 전 고정 입력

다음 파일을 모두 읽어라. 기준 commit과 prompt·config·fixture bundle SHA-256 및
실행 manifest는 운영 실행기가 기록한다. 에이전트는 manifest를 생성하거나 수정하지 않는다.

1. `docs/PROJECT_PURPOSE.md`
2. `docs/PRODUCT_CONTRACT.md`
3. `docs/hardware/version-2-capabilities.md`
4. `docs/DEVELOPMENT_ENVIRONMENT.md`
5. `docs/experiments/agent-experiment-protocol.md`
6. `docs/experiments/hardware-feature-discovery.md`
7. `experiments/config/version-2-baseline.yaml`
8. `experiments/fixtures/`의 모든 파일
9. `docs/experiments/benchmark-management.md`
10. `docs/experiments/evaluation-contract.md`
11. `docs/experiments/integration-contract.md` (현재는 설계 초안이며, historical
    cohort에서는 구현·합격으로 주장하지 않는다)

이 prompt가 현재 연결된 baseline은 `version-2-hardware-autonomy-v1`인
historical firmware-only 준비용 cohort다. 이 cohort에서 F1 PC collector와 F3
PC→ESP32 transport를 구현하지 않은 결과는 `not_run; out of cohort`로 기록하며,
제품 합격이나 정식 agent 순위로 재사용하지 말라. 정식 제품 비교 목표는
`version-2-end-to-end-v1`이지만, 그 실행에는 새 schema·validator·example과
새 baseline commit이 먼저 필요하다. 그 준비가 끝나기 전에는 이 prompt를
수동으로 실행하거나 E2E 실행으로 해석하지 말라.

공통 프롬프트의 `<run-id>`는 운영 실행기가 치환해 전달한다. 계정 쿠키,
Wi-Fi 비밀번호, API 키 또는 개인 사용량 원본을 요청하거나 커밋하지 말라.
개인 사용량은 fixture로 먼저 구현·검증하고, 실제 계정 통합이 불가능하면 그
사유를 기록하라.

## 구현 요구

- 기준 커밋에서 ESP-IDF 프로젝트를 생성하고 `idf.py set-target esp32s3`와
  `idf.py build`를 실행하라.
- C1~C8을 모두 구현하라. 핵심 요구사항을 제거하거나 축소하지 말라.
- 현재 historical cohort의 C3는 고정 fixture를 firmware 상태와 LCD에 표시하는
  준비용 범위다. F1/I1 collector와 F3/I3 transport를 검증했다는 의미가 아니며,
  이 cohort의 결과로 `product_pass`를 주장하지 말라.
- 개인 사용량, `codex-reset.com`, `codex-resets.com`을 공통 데이터 모델로
  정규화하되 출처와 시각을 보존하라.
- PC collector·정규화 adapter·transport·receiver로 이어지는 seam/interface를
  문서화하라. 현재 historical cohort에서는 이 계층의 구현·검증을 제품 합격으로
  주장하지 말고 F1/F3을 `not_run; out of cohort`로 남겨라. 정식 E2E prompt로
  승격할 때 I1~I4와 각 계층의 raw input/output, frame version·길이·무결성·
  재연결·오류 응답 시험을 추가해야 한다.
- collector와 공통 상태는 Codex 전용 필드에 하드코딩하지 말고 provider adapter
  registry와 동적 quota window 목록을 수용하도록 설계하라. 향후 Codex CLI,
  Claude Code, Gemini CLI, Orca/IDE host를 연결할 수 있어야 하며 provider, agent,
  model, host, account profile과 metric 단위를 분리하라. source가 절대 token
  잔량을 제공하지 않으면 percent/unknown과 `unsupported`/`unavailable` 상태를
  보존하고 임의로 token 수를 계산하지 말라.
- 두 공개 출처의 값을 하나의 공식 리셋 일정으로 합치지 말라.
- 네트워크·TLS·HTTP·JSON 오류와 오래된 데이터에서도 화면을 중단시키지 말라.
- 320 × 820 세로 LCD에서 대시보드, 글로벌 리셋, 상태/오류 화면을 제공하라.
- BOOT 입력 동작과 자동·수동 갱신 주기를 문서화하고 시험하라. RST는 시스템
  리셋 전용으로 유지하라.
- 추가 하드웨어를 사용하지 말라. Version 1 전용 하드웨어를 요구하지 말라.

정식 E2E 제품 통합 조건(I1~I4)은 `docs/PRODUCT_CONTRACT.md`와
`docs/experiments/feature-comparison.md`에 정의되어 있지만, 현재 schema v2와
이 historical prompt의 실행 범위에는 포함되지 않는다. maintainer가 R3 gate에서
schema·validator·example·prompt를 함께 갱신한 뒤에만 새 E2E baseline을 고정한다.

## 하드웨어 자율 기능

핵심 기능과 별도로 보드의 IMU, RTC, 배터리 ADC, TF, BOOT, Wi-Fi/BLE 등 실제
자원을 활용하는 후보를 정확히 3개 작성하라. 각 후보에 사용자 가치, 자원,
구현 비용, 위험과 검증 방법을 적고, 사용자에게 선택을 넘기지 말고 1개를
스스로 선택·구현하라. 선택하지 않은 2개와 탈락 이유를 보존하라.

선택 기능은 핵심 코드와 분리된 모듈 또는 설정으로 구현하라. 제조사 예제 기능을
그대로 복사한 것은 추가 기능으로 인정하지 않는다. 추가 기능 점수는 핵심 C1~C8
점수와 별도로 계산한다.

## 검증과 산출물

변경 뒤 가능한 범위에서 다음을 실행하고 결과를 명령 로그에 남겨라.

1. 파서 및 fixture 단위 시험
   - `docs/experiments/evaluation-contract.md`에 따라 실제 제품 모듈을 호출하는 host 어댑터 제공
2. `idf.py build`
3. 선택 기능 자동 시험
4. 운영자 승인 뒤 COM3에 플래시하는 실물 시험 계획

각 산출물에는 다음 기능 상태를 핵심 C1~C8과 분리해 기록하라: F1 PC agent/provider collector,
F2 정규화·출처, F3 PC→ESP32 transport, F4 receiver/state/cache, F5 LCD GUI,
F6 입력·갱신, F7 글로벌 리셋, F8 빌드·관측, F9 자율 하드웨어. 현재 scope의
F1/F3은 `not_run; out of cohort`로 기록한다. F5 화면은
`docs/experiments/feature-comparison.md`의 G1~G6 rubric과 화면별 사진·영상
증거를 사용한다.

`erase_flash`는 실행하지 말라. 실제 보드 검증을 할 수 없으면 `blocked` 또는
`not_run`과 구체적인 이유를 기록하라.

다음 선택 문서와 구조화 결과를 남겨라. manifest의 실행 식별·계측 필드와
commands.jsonl은 운영 실행기가 관리한다. 실행 중 원본 로그를 읽거나 덮어쓰지 말라.
시간·토큰을 추정해 채우지 말고 미측정 값은 null과 사유로 남겨라.

```text
docs/agent-runs/<run-id>/hardware-feature-selection.md
results/<run-id>/hardware-feature.json
```

`hardware-feature.json`은 schema_version 2와
`experiments/schema/hardware-feature-result.schema.json` 계약을 지켜라.
운영 기록에만 있는 시각·해시·계측값을 추정하지 말라. 최종 보고에 확인 가능한 다음을 포함하라.

- agent / product / interface / version / model / reasoning
- 기준 commit, prompt/config/fixture SHA-256
- 시작·종료 시각, 제한 시간, wall-clock
- 도구 호출·실패 명령·사용자 개입 수
- input/output/cached/reasoning/total 토큰(제공되는 경우)
- 빌드·자동 시험·실물 시험과 실패·미해결 위험

자체 시험 결과는 운영자의 공통 평가와 구분하라. 최종 제품 합격과 자율 기능
점수는 운영자가 증거를 검토해 확정한다. 실제 전송 계층 오류와 주입 시험 결과를
구분하고, 판정 기준 시각은 제품 계약을 따르라.

토큰 수와 시간만으로 결과를 판단하지 말라. 핵심 기능의 정확성, 장치 안정성,
오류 처리와 선택 기능의 실제 가치를 함께 검증하라.
