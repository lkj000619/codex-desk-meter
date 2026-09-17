# PC 수집기·ESP32 통합 계약 초안

## 상태

**`DRAFT / NOT_AUTHORIZED`**

## 외부 참조 구현

2번 결과 계약(schema·validator·example)과 3번 PC→ESP32 transport를 설계할 때
Waveshare 공식 GitHub 계정의
[`waveshareteam/codex-meter`](https://github.com/waveshareteam/codex-meter)를 참조할 수
있다. 특히 Windows host collector, versioned device payload, 로컬 cache, Wi-Fi
HTTP/HMAC, BLE GATT chunking·ACK·재연결 구조는
[`docs/transport.md`](https://github.com/waveshareteam/codex-meter/blob/main/docs/transport.md)를
우선 참고한다.

이 저장소는 **참고 구현(reference implementation)**이지 현재 benchmark의 고정
입력이나 합격 증거가 아니다. 다음 경계를 지킨다.

- upstream의 소스·문서·프로토콜을 참고하거나 재사용하면 URL, commit SHA, 확인
  날짜, 재사용 파일과 라이선스를 기록한다.
- upstream이 사용하는 보드는 ESP32-S3-Touch-AMOLED-2.16이므로, 현재 대상인
  ESP32-S3-LCD-3.16의 LCD·입력·IMU·핀맵·BSP 검증을 대신하지 않는다.
- upstream의 device payload는 제품 통합 계약 설계에 참고할 수 있지만,
  F1~F9·I1~I4·G1~G6를 기록하는 우리 실험 결과 schema를 대체하지 않는다.
- upstream이 E2E 동작한다고 해서 이 저장소의 collector, transport, receiver 또는
  hardware 상태를 `pass`로 승격하지 않는다. 동일 baseline에서 직접 시험한 증거가
  필요하다.
- 실제 계정 자격증명·OAuth token·cookie는 firmware, 결과 파일, raw log에 넣지
  않는다. 에이전트 benchmark에서는 계속 합성 fixture를 사용한다.

추가로 다음 두 `claude-codex-monitor` 구현을 서로 다른 목적으로 참고할 수 있다.

- [`haomingkoo/claude-codex-monitor`](https://github.com/haomingkoo/claude-codex-monitor):
  Claude Code와 Codex를 독립 provider로 수집하고, 동적 quota window·reset·cache·
  stale·pace/burnout를 표현하는 host-side 참고 구현
- [`mathd/claude-codex-monitor`](https://github.com/mathd/claude-codex-monitor):
  Go daemon→MQTT/Home Assistant→ESP32 물리 화면 계층 분리와 provider별 센서 상태,
  unavailable/NAN 방어를 참고하는 물리 장치 통합 구현

두 저장소도 비공식 reference implementation이다. endpoint, credential 파일,
refresh 방법이나 polling 주기를 안정적인 공개 API 계약으로 간주하지 않는다.
정식 baseline에서는 참조한 repository URL과 commit SHA를 고정하고, 라이선스와
보안 경계를 검토한다.

## 다중 agent/provider 호환 계약

collector는 quota를 읽는 provider adapter와 실행 표면을 설명하는 host-context
adapter를 분리한다. 둘은 normalization 단계에서 identity로 결합되며, host를 quota
provider처럼 취급하지 않는다.

```text
OpenAI provider adapter ────┐
Anthropic provider adapter ─┼─> normalized quota snapshots ─> transport ─> ESP32
Google provider adapter ────┘                    ↑
                              Terminal/Orca/Antigravity/VS Code host context
```

각 snapshot은 다음 identity를 분리해서 보존한다.

- `provider_id`: `openai`, `anthropic`, `google` 또는 안정적인 vendor ID
- `agent_id`: `codex-cli`, `claude-code`, `gemini-cli` 등
- `host_id`: `terminal`, `orca`, `antigravity`, `vscode` 등 실행 표면
- `model_id`: source가 보고할 때만 기록하며 추정하지 않음
- `account_profile_id`: 원본 계정 ID 대신 로컬 비식별 alias 사용
- `metric_kind`: `quota_window`, `token_balance`, `credits`, `session_telemetry`
- `unit`: `percent`, `token`, `credit`, `unknown`

adapter가 지원되지 않거나 IDE가 사용량 정보를 노출하지 않으면 `unsupported` 또는
`unavailable`을 반환한다. 다른 provider의 값, 로컬 transcript token 합계 또는
임의 계산값으로 대체하지 않는다. firmware는 provider 수와 window 수가 달라도
동작하도록 배열/목록으로 받고, LCD는 사용 가능한 provider만 순환하며 source,
stale, reset과 단위를 함께 표시한다.

이 문서는 PC에서 허용된 provider source의 사용량을 읽어 ESP32 LCD에 전달하는
제품 계층을 구체화하기 위한 설계 초안이다. E2E baseline transport는 USB
serial(COM3) `cdm/1`로 고정되었으나, 최종 baseline commit·hash 동결과 R10 사용자
승인 전이므로 이 문서만으로 agent 실행·COM3 전송·실제 계정 조회를 시작하지 않는다.

## 목표와 경계

```text
PC collector → normalization adapter → transport adapter
        → ESP32 receiver → validation/cache/stale → common state → LCD GUI
```

- PC collector는 사용자의 PC에서만 실행하며, 계정 쿠키·API key·Wi‑Fi 비밀번호를
  ESP32에 보내지 않는다.
- 비교 cohort에서는 고정 fixture collector를 사용한다. owner-only live source는
  별도 운영 시험이며 agent benchmark 입력이 아니다.
- ESP32는 원본 API JSON을 해석하지 않고 versioned normalized frame만 받는다.
- `codex-reset.com`과 `codex-resets.com`은 서로 다른 `GlobalResetSnapshot`으로
  운반하며 하나의 공식 일정으로 병합하지 않는다.

## 계층별 interface

### I1 — PC collector

입력은 fixture 또는 owner adapter가 제공하는 source 응답이다. 출력은 다음 필드를
채운 `UsageSnapshot`/`GlobalResetSnapshot`이다.

- source, observed/fetched 시각, window ID와 label
- percent used/remaining
- source가 절대 quota를 공개할 때만 used/remaining/limit와 단위
- 오류 코드, 마지막 정상 시각과 stale 후보

절대 token quota가 없으면 `unit: percent|unknown`과 null을 유지한다. 총량을
임의로 정해 퍼센트를 token 수로 바꾸지 않는다.

I1은 단일 Codex 함수가 아니라 provider adapter registry로 구현한다. 각 adapter의
capability(`quota_windows`, `absolute_tokens`, `credits`, `reset_time`,
`session_telemetry`)와 상태(`available`, `unsupported`, `unauthorized`, `error`,
`stale`)를 조회할 수 있어야 한다. 한 adapter의 장애가 다른 provider snapshot을
삭제하거나 전체 collector를 중단시키지 않아야 한다.

### I2 — normalization adapter

원본 응답과 정규화 결과를 각각 hash하고 parser 버전을 기록한다. 누락·범위 밖
값·미래 시각·잘못된 RFC3339는 오류로 반환하며, nullable 값은 0이나 현재 시각으로
대체하지 않는다.

### I3 — transport adapter

E2E baseline은 USB serial(COM3) `cdm/1`로 고정한다. local Wi-Fi 운용은 별도
비교 cohort에서 다룬다.

| 후보 | benchmark 적합성 | 제약 |
|---|---|---|
| USB serial(COM3) | 지연·재현성·원시 송수신 log 측정이 쉽고 Wi‑Fi 자격증명이 불필요함 | 한 번에 한 장치만 점유, 케이블·COM 재열거 처리 필요 |
| local Wi‑Fi | 케이블 없이 책상에서 운용 가능 | AP/주소/재연결·네트워크 변동을 통제해야 함 |

권장 순서는 benchmark에서 USB serial을 먼저 고정하고, 제품 운용성은 별도의
local Wi‑Fi cohort에서 비교하는 것이다. E2E baseline의 transport 변경은 새
cohort 정의와 사용자 승인을 통해서만 가능하며, 실행 중 선택 변경은 허용하지
않는다. 어떤 선택을 하든 모든 agent에 같은 선택·프로토콜·timeout을 제공한다.

### I4 — ESP32 receiver/state

수신 frame을 검증한 뒤에만 공통 상태를 갱신한다. 잘못된 frame·단절·timeout은
마지막 정상 상태를 유지하고 `stale`/오류를 표시하며, 정상 frame이 다시 오면
오류를 해제하고 갱신 시각을 변경한다. receiver가 없거나 fixture를 firmware에
직접 내장한 결과는 I4/F4의 E2E 합격이 아니다.

## 제안 frame envelope

아래는 E2E baseline으로 고정된 `cdm/1` 형식이며, baseline commit 동결 시 최종 확정된다.

```json
{
  "protocol": "cdm/1",
  "sequence": 42,
  "sent_at": "2026-09-11T00:00:00Z",
  "payload": {
    "usage": {},
    "global_resets": []
  },
  "integrity": {
    "algorithm": "crc32",
    "value": "<computed-over-canonical-envelope>"
  }
}
```

정식 형식에서는 canonical serialization, 최대 frame 크기, line/length framing,
checksum 범위, sequence 재생·순서 뒤바뀜 처리, ACK/재전송 여부와 timeout을
명시한다. 후보 envelope를 구현했다고 해서 아직 I3 합격으로 기록하지 않는다.

## 공통 통합 시험

| 시험 | 기대 결과 |
|---|---|
| 정상 frame | receiver가 상태·갱신 시각·LCD를 갱신 |
| 잘못된 version/길이/checksum | frame 폐기, 마지막 정상값·오류 표시 유지 |
| truncation/빈 frame | parser crash 없이 timeout/stale 처리 |
| 중복·역순 sequence | 정책에 따라 무시 또는 명시적 오류, 상태 오염 없음 |
| PC/USB 단절·COM 재열거 | receiver가 watchdog 없이 유지·재연결 후 복구 |
| source 필드 누락/미래 시각 | normalization 오류와 null 표시, 임의 대체 금지 |
| absolute token 미제공 | percent/unknown만 전송, token 수 추정 금지 |

각 시험은 PC raw input, 전송 raw bytes, ESP32 log, 결과 상태와 SHA-256을 별도로
보존한다. F1~F4와 I1~I4를 한 개의 “LCD 정상” 결과로 합치지 않는다.

## 정식 고정 전 checklist

- [x] transport 선택(USB serial `cdm/1`) 고정 선언 (ADR-0005 승인 + baseline commit/hash 동결 대기)
- [ ] canonical JSON/CRC 또는 대체 무결성 규칙 승인
- [ ] fixture collector와 owner-only live adapter의 경계 승인
- [ ] F1~F4/I1~I4 결과 schema·validator·example 반영
- [ ] PC collector·transport·receiver의 host/integration 시험 통과
- [ ] COM3 운영자 checklist와 단일 점유 정책 확인
