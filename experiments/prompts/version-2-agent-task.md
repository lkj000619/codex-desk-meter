# Version 2 에이전트 공통 프롬프트

> 운영자: 이 템플릿은 현재 문서 개정 중이다. `docs/experiments/benchmark-management.md`의
> 구현 전환 항목과 새 baseline 확정 전에는 실행하지 않는다.

당신은 Codex Desk Meter Version 2의 기준 구현을 담당한다. 작업 결과는
`docs/PRODUCT_CONTRACT.md`의 C1~C8을 만족해야 하며, 대상 보드는 Waveshare
ESP32-S3-LCD-3.16, 프레임워크는 ESP-IDF v5.3.2다.

## 시작 전 고정 입력

다음 파일을 모두 읽고, 기준 commit과 prompt·config·fixture bundle SHA-256을
결과 manifest에 기록하라.

1. `docs/PROJECT_PURPOSE.md`
2. `docs/PRODUCT_CONTRACT.md`
3. `docs/hardware/version-2-capabilities.md`
4. `docs/DEVELOPMENT_ENVIRONMENT.md`
5. `docs/experiments/agent-experiment-protocol.md`
6. `docs/experiments/hardware-feature-discovery.md`
7. `experiments/config/version-2-baseline.yaml`
8. `experiments/fixtures/`의 모든 파일
9. `docs/experiments/benchmark-management.md`

공통 프롬프트의 `<run-id>`는 실제 실행 manifest의 ID로 치환하라. 계정 쿠키,
Wi-Fi 비밀번호, API 키 또는 개인 사용량 원본을 요청하거나 커밋하지 말라.
개인 사용량은 fixture로 먼저 구현·검증하고, 실제 계정 통합이 불가능하면 그
사유를 기록하라.

## 구현 요구

- 기준 커밋에서 ESP-IDF 프로젝트를 생성하고 `idf.py set-target esp32s3`와
  `idf.py build`를 실행하라.
- C1~C8을 모두 구현하라. 핵심 요구사항을 제거하거나 축소하지 말라.
- 개인 사용량, `codex-reset.com`, `codex-resets.com`을 공통 데이터 모델로
  정규화하되 출처와 시각을 보존하라.
- 두 공개 출처의 값을 하나의 공식 리셋 일정으로 합치지 말라.
- 네트워크·TLS·HTTP·JSON 오류와 오래된 데이터에서도 화면을 중단시키지 말라.
- 320 × 820 세로 LCD에서 대시보드, 글로벌 리셋, 상태/오류 화면을 제공하라.
- BOOT 입력 동작과 자동·수동 갱신 주기를 문서화하고 시험하라. RST는 시스템
  리셋 전용으로 유지하라.
- 추가 하드웨어를 사용하지 말라. Version 1 전용 하드웨어를 요구하지 말라.

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
2. `idf.py build`
3. 선택 기능 자동 시험
4. 운영자 승인 뒤 COM3에 플래시하는 실물 시험 계획

`erase_flash`는 실행하지 말라. 실제 보드 검증을 할 수 없으면 `blocked` 또는
`not_run`과 구체적인 이유를 기록하라.

다음 선택 문서와 구조화 결과를 남겨라. manifest의 실행 식별·계측 필드와
commands.jsonl은 운영 실행기가 관리한다. 실행 중 원본 로그를 읽거나 덮어쓰지 말라.
시간·토큰을 추정해 채우지 말고 미측정 값은 null과 사유로 남겨라.

```text
docs/agent-runs/<run-id>/hardware-feature-selection.md
results/<run-id>/run-manifest.json
results/<run-id>/hardware-feature.json
results/<run-id>/commands.jsonl
```

`run-manifest.json`은 `experiments/schema/run-manifest.schema.json`,
`hardware-feature.json`은 `experiments/schema/hardware-feature-result.schema.json`
계약을 지켜라. 마지막에 다음을 포함하라.

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
