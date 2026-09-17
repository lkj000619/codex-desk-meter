# Version 2 기능별 비교 기준

이 문서는 AI 에이전트의 결과를 C1~C8 한 덩어리로만 판정하지 않고, 데이터가
생성되어 LCD에 표시되기까지의 기능을 독립적으로 비교하기 위한 기준이다.
기능 상태는 `pass / partial / fail / not_run / blocked / timeout` 중 하나로
기록하고, 상태만 적지 말고 실행 명령·로그·사진·영상·해시 등 확인 가능한
증거를 함께 남긴다. PC 수집기와 frame/receiver 경계의 설계는
[통합 계약 초안](integration-contract.md)을 참조한다.

## 1. 실험군과 제품 통합 범위

`version-2-hardware-autonomy-v1`은 과거 r01을 설명하기 위한 **준비용
firmware-only cohort**다. 이 범위에서 PC collector와 transport를 구현하지 않은
것은 제품 목표를 충족한 것이 아니며, 정식 제품 비교 결과로 승격할 수 없다.

향후 정식 제품 비교의 목표는 `version-2-end-to-end-v1`이다. 이 cohort는 개인
계정 자격증명을 에이전트에게 주지 않고도 검증할 수 있도록 표준 fixture collector와
로컬 transport를 사용해 F1~F9 전체를 다룬다. 실제 계정 source로의 전환은
소유자 승인 후 별도 integration 시험에서만 수행한다.

| 범위 | 포함 기능 | 데이터 | 결과 해석 |
|---|---|---|---|
| `version-2-hardware-autonomy-v1` (historical/prep) | F2, F4, F5, F6, F7, F8, F9 | 고정 fixture·오프라인 오류 주입 | firmware·화면·하드웨어 설계 참고; 제품 합격·정식 순위 제외 |
| `version-2-end-to-end-v1` (planned target) | F1~F9 | 표준 fixture collector·로컬 transport·오프라인 오류 주입 | PC 수집부터 ESP32 화면까지의 제품 pipeline 비교 |
| `version-2-live-integration-v1` (owner-only follow-up) | F1~F8 | 소유자 승인 live source + 동일 회귀 fixture | 실제 개인 계정 연동·운영 안정성 확인 |

F1과 F3을 준비용 cohort에서 실행하지 않았다는 사실을 제품 전체 합격으로
오해하지 않는다. 해당 결과에는 `not_run; out of cohort`를 남기며, 정식
end-to-end cohort에서는 F1/F3이 필수다.

정식 제품 합격 판정은 C1~C8과 I1~I4가 모두 pass이고, F1~F9의 범위·증거가
완결되며 C2와 실물 gate가 통과한 경우에만 가능하다. 기능 비교표는 어느 계층이
빠졌는지 드러내기 위한 것이며 누락 계층을 다른 기능 점수로 보상하지 않는다.

## 2. 기능별 비교표

| ID | 기능 모듈 | 비교 질문 | 핵심 증거 | cohort별 취급 |
|---|---|---|---|---|
| F1 | PC agent/provider 사용량 collector | PC의 허용된 provider source에서 사용량 창·잔여율·조회 시각을 안전하게 수집하고 provider와 host context를 분리하는가? 절대 token quota를 제공할 때만 단위·used/remaining/limit를 보존하고, 없으면 임의로 계산하지 않는가? | collector 실행 로그, 입력·출력 hash, capability matrix, 자격증명 비노출 확인 | 준비용: `not_run`; E2E: 필수 |
| F2 | 정규화·출처 분리 | 개인 사용량과 `codex-reset.com`, `codex-resets.com`을 공통 모델로 변환하고 임의 병합하지 않는가? | production parser host test, fixture 오류 시험, source 필드 | fixture parser 범위에서 평가 |
| F3 | PC→ESP32 transport | E2E baseline 고정인 USB serial(COM3) `cdm/1`에서 frame 버전·길이·무결성·재연결·오류 응답을 보장하는가? (local Wi-Fi는 별도 cohort) | protocol 문서, 송수신 raw log, checksum/재연결 시험 | 준비용: `not_run`; E2E: 필수 |
| F4 | ESP32 receiver·state | 수신/입력 데이터를 검증하고 last-good, stale, 오류 해제·복구를 상태 모델에 반영하는가? | 상태 전이 host test, 오류 주입, 시리얼 로그 | fixture 직접 입력으로 부분 평가 |
| F5 | LCD GUI | 정보 우선순위, 레이아웃, 가독성, 상태·출처·오류 표현, 320×820 최적화가 적절한가? | 동일 fixture의 화면 사진/영상, 구현 근거 | 필수 비교 |
| F6 | 입력·갱신 | BOOT·자율 기능으로 화면 전환과 수동/자동 갱신이 예측 가능하고 피드백이 명확한가? | 입력 전후 영상, 시리얼 로그, debounce 값 | 필수 비교 |
| F7 | 글로벌 리셋 표시 | 최근 리셋과 24h/48h 전망을 독립적으로 표시하고 예측을 일정으로 오해하게 하지 않는가? | 두 source fixture, 화면별 캡처, parser test | 필수 비교 |
| F8 | 빌드·배포·관측 | ESP-IDF 빌드, artifact hash, 로그, manifest와 결과 schema가 재현 가능한가? | build log, binary hash, manifest, validator | 필수 비교 |
| F9 | 자율 하드웨어 기능 | 후보 3개·선택 근거·구현 완성도·핵심 기능과의 분리가 설득력 있는가? | 선택 문서, 테스트, 하드웨어 증거 | 필수 비교 |

### 다중 agent/provider 호환성

F1~F5 평가는 Codex 한 종류의 고정 JSON에만 맞춘 구현을 완전한 것으로 보지 않는다.
최소 fixture matrix는 Codex, Claude Code, Gemini CLI, Orca/IDE host 및 unsupported
provider를 포함한다. 각 fixture는 서로 다른 window 수, 누락된 absolute token,
reset 미제공, stale/error와 복수 model을 포함해야 한다. 실제 source를 사용할 수
없는 provider도 adapter capability와 `unsupported`/`not_run` 상태를 정직하게
표현하면 되며, 임의의 잔여량을 만들어서는 안 된다.

LCD GUI는 다음도 비교한다.

- provider/agent/model/host가 혼동되지 않는 식별과 화면 전환
- provider별 서로 다른 quota window와 단위의 동적 배치
- 한 provider 장애 시 다른 provider 화면 유지
- 지원하지 않는 source와 0% 잔량의 명확한 구분
- provider가 하나뿐일 때 불필요한 빈 화면을 만들지 않는 적응형 UI

F1의 “잔여량”은 제품 데이터이고, runner가 기록하는 agent input/output token은
실험 계측 데이터다. 두 값을 같은 필드나 같은 효율 순위로 합치지 않는다.

## 3. LCD GUI 품질 rubric

C2는 LCD가 켜지고 화면 밖으로 잘리지 않는지 판단하는 기능 gate다. GUI rubric은
C2를 통과한 동결 산출물의 설계·표현 품질을 별도로 비교하며, 실물 증거가 없으면
점수를 확정하지 않는다. 각 항목은 0~3점, 총 18점이다.

| ID | 항목 | 0점 | 1점 | 2점 | 3점 |
|---|---|---|---|---|---|
| G1 | 정보 우선순위·레이아웃 | 핵심 정보 식별 불가 | 정보는 있으나 우선순위 불명확 | 주요 정보가 구분됨 | 사용 목적에 맞는 명확한 계층과 여백 |
| G2 | 가독성·시각 계층 | 읽을 수 없음 | 일부 값만 읽힘 | 대부분 읽힘 | 글자·대비·색상·긴 시각·퍼센트가 일관되게 읽힘 |
| G3 | 상태·출처 구분 | 상태/출처 혼동 | 라벨 일부만 구분 | 세 화면과 출처가 구분됨 | 확정·예측·개인·글로벌 의미가 즉시 구분됨 |
| G4 | 오류·stale·null 표현 | 정상값처럼 표시 | 오류 표시가 약함 | 오류와 오래된 값이 구분됨 | 마지막 정상 시각·재시도·미확인이 명확함 |
| G5 | 상호작용·갱신 피드백 | 입력 결과를 알 수 없음 | 전환은 되나 피드백 부족 | 입력/갱신 결과가 확인됨 | 전환·자동/수동 갱신·실패 상태가 자연스럽게 이해됨 |
| G6 | 보드별 최적화 | 화면비·패널 특성 무시 | 잘림/성능 위험 존재 | 320×820에 맞게 동작 | ST7701 초기화·세로 비율·메모리·렌더링을 근거와 함께 최적화 |

GUI 총점은 제품 합격률로 환산하지 않는다. C2가 `not_run` 또는 `fail`이면
제품 합격은 `false`이며, GUI 점수는 설계 품질 참고값으로만 제시한다.

## 4. 결과 기록 규칙

- 모든 F1~F9의 상태와 scope를 결과에 기록한다. 범위 밖 기능은 `not_run`과
  `out of cohort`를 함께 적는다.
- 정식 E2E 결과에는 I1~I4(collector·정규화·transport·receiver)의 상태·입출력
  증거·오류/복구 시험을 F 기능과 별도로 기록한다.
- GUI 평가에는 각 화면의 fixture 상태, 사진/영상 경로, 촬영 시각, 판정자와
  SHA-256을 기록한다.
- agent 자체 시험, 공통 host 시험, 운영자 하드웨어 시험을 별도 열로 구분한다.
- 구현자가 실행 후 코드를 고친 경우 원본 run 점수에는 반영하지 않고
  `remediation/...` 결과로 분리한다.
- E2E 결과 계약(`end-to-end-result.schema.json`)은 F1~F9·I1~I4·G1~G6 필드를 보유한다.
  확장 대상은 historical hardware-autonomy용 `hardware-feature-result.schema.json`
  (C1~C8만 기록)이며, 이를 E2E 기준으로 오독하지 않는다. 정식 E2E baseline을
  만들기 전에 F1/F3 fixture collector·transport 시험을 포함한 검증을 먼저
  통과해야 한다.
- schema·validator·example과 F3 transport를 설계할 때 Waveshare 공식
  [`waveshareteam/codex-meter`](https://github.com/waveshareteam/codex-meter)의 host,
  device payload 및 Wi-Fi/BLE transport 구현을 참고할 수 있다. 단, 우리 결과
  schema와 ESP32-S3-LCD-3.16 실물 검증을 대신하지 않으며, 사용한 upstream commit
  SHA·확인 날짜·라이선스를 결과 provenance에 기록한다.
