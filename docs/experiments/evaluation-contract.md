# 공통 평가 인터페이스

에이전트는 실제 펌웨어에서 사용하는 파서·상태 전이 모듈에 연결된 host 실행 어댑터를
제공한다. 별도 구현한 모방 파서는 인정하지 않는다. 운영자가 소스 목록, 빌드/링크
로그와 SHA-256을 검토한다. 이 연결 검토는 자동 시험 통과로 대신할 수 없다.

어댑터는 stdin의 UTF-8 JSON 한 개를 읽고 stdout에 snapshot 배열만 출력한다.
각 호출은 새 상태에서 시작하고 events 순서대로 같은 상태를 갱신한다.

이 어댑터 계약은 firmware의 파서·상태 전이를 평가하기 위한 host seam이다. 이를
통과해도 PC에서 실제 Codex 사용량을 수집하거나 ESP32로 전송했다는 뜻은 아니다.
제품 전체 데이터 경로는 `PC collector → normalized snapshot → versioned transport
→ ESP32 receiver/cache/stale → LCD GUI`다. historical hardware-autonomy cohort에서
collector와 transport를 생략한 결과는 `not_run; out of cohort`로만 보존하고,
정식 E2E cohort에서는 I1~I4와 함께 검증한다. 실제 source 전환은 owner-only
live integration에서 송수신 frame, 재연결, 무결성, 승인 절차를 별도로 검증한다.

```json
{"source":"fixture","events":[{"now":"2026-09-11T00:00:00Z","body":{},"error":null}]}
```

`body`는 fixtures의 원본 객체, 잘못된 JSON 문자열 또는 null이다. `error`는
null, dns, tls, http_500 중 하나다. 로그는 stderr로 출력한다.

### 현재 evaluator의 legacy 회귀 출력

`scripts/evaluate-product.py`는 최상위 legacy fixture 3종을 사용하는 회귀
interface다. 현재 `check()`가 요구하는 출력은 최신 UsageSnapshot 전체와 다르다.

| 입력 source | event별 출력의 필수 검사 필드 |
|---|---|
| `fixture` (`personal-usage.json`) | `source: fixture`, 원본 `windows` 배열 그대로(`id` 키 포함), `observed_at: captured_at`, `stale`, `error_code` |
| `codex-reset.com` / `codex-resets.com` | `provider`, `fetched_at`, 정규화한 `latest_reset_at`, nullable `forecast_24h_percent`·`forecast_48h_percent`, `forecast_is_schedule: false`, `stale`, `error_code` |

각 호출에서 세 event에 대응하는 snapshot 세 개를 배열로 반환한다. 오류 event는
마지막 정상 값·조회 시각을 유지하고 `error_code`를 채우며, 정상 복구 후 해제한다.
forecast 필드는 파서 호환 검사이며 현재 C5 화면 표시 판정이 아니다.

이 legacy interface의 `source`/window `id`를 E2E wire 필드로 그대로 보내지 않는다.
E2E의 UsageSnapshot은 `usage-snapshot.schema.json`의 identity, `source_kind`,
window `window_id` 등을 사용하며, global wire 매핑은
[통합 계약](integration-contract.md)을 따른다. host 어댑터가 legacy 출력으로
변환하더라도 실제 제품 파서·상태 모듈 호출 증거가 필요하다. 최신 E2E provider
계약 전체를 이 evaluator 하나로 검사할 수 있다는 의미는 아니다.

운영자는 다음 adapter config를 실제 경로/해시로 채운다. 명령은 argv 배열이며
셸 문자열을 사용하지 않는다. 실행 파일은 절대 경로로 지정한다.

```json
{
  "checkout": "C:/Espressif/benchmark-runs/<run-id>/checkout",
  "argv": ["C:/Espressif/benchmark-runs/<run-id>/checkout/build-host/meter-test.exe"],
  "production_files": {"components/meter/parser.c": "<SHA256>"},
  "reviewer": "<operator>",
  "link_evidence": "C:/Espressif/benchmark-runs/<run-id>/link-evidence.txt",
  "link_evidence_sha256": "<SHA256>"
}
```

`python scripts/evaluate-product.py --adapter-config <config> --output <report>`는
정상값·null 보존, 0/299/300초 stale, 시간/필드/범위 오류, DNS/TLS/HTTP 실패,
마지막 정상값 보존 및 복구를 검사한다. 이는 C3~C7 자동 검사 범위의 회귀 시험이다.
C1 빌드와 C2/C8 실물 동작은 별도로 확인하며 이 도구가 제품 합격을 선언하지 않는다.

E2E result validator는 `core_results.C1`~`C8`의 필수 판정과 증거 참조를
검사하며 `product_pass: true`에는 모든 C 항목의 `pass`를 요구한다.
validator 자체가 C1 빌드나 C2/C8 실물 동작을 실행·측정하는 것은 아니다.
C별 판정은 아래 평가 기록과 증거로 남긴다. 구조화 연결 완료 근거는
[진행 체크리스트의 N4/D10](../archive/reviews/DOCUMENTATION_REVIEW_CHECKLIST.md)을 따른다.

## 기능·GUI 결과 분리

공통 evaluator는 C1~C8과 별도로 다음 기능 상태를 기록한다.

| 기능 | historical hardware-autonomy cohort | 정식 E2E/live integration |
|---|---|---|
| F1 PC agent/provider collector | `not_run; out of cohort` | 다중-provider fixture collector, 이후 owner-approved live source |
| F2 정규화·출처 분리 | fixture/parser 범위 | live 승인 source와 fixture 회귀 |
| F3 PC→ESP32 transport | `not_run; out of cohort` | frame·무결성·재연결 raw log |
| F4 ESP32 receiver/state/cache | firmware 직접 입력 범위 | 실제 수신·오류·stale 전이 |
| F5 LCD GUI | 실물 화면 증거 필요 | 동일 |
| F6~F9 | 입력·갱신·리셋·빌드/관측·자율 기능별 증거 | 동일 |

F5 GUI는 `feature-comparison.md`의 G1~G6(각 0~3점)를 사용한다. 화면 사진·영상,
촬영 UTC 시각, fixture 상태, 판정자와 SHA-256이 없으면 점수를 확정하지 않는다.
fixture parser 통과나 GUI 점수는 PC collector·transport의 구현 증거가 아니며,
F1/F3 `not_run` 상태를 제품 전체 합격으로 바꾸지 않는다. 정식 E2E에서는 I1
(collector), I2 (normalization), I3 (transport), I4 (receiver/state)도 각각
pass/partial/fail/not_run과 증거를 남긴다.

## 실물 채점 기록

운영자가 각 항목에 pass/partial/fail/not_run, 판정자, UTC 시각, 증거 경로와
SHA-256을 기록한다. 미검증은 합격으로 간주하지 않는다.

| 항목 | 검증 |
|---|---|
| C1 | ESP-IDF v5.3.2 esp32s3 빌드와 종료 코드 |
| C2 | 부팅 후 30초 LCD 유지, 세 화면의 잘림 없음 |
| C3~C6 | fixture 수치·경과·미확인·출처 표시 |
| C7 | 정상→오류→복구, USB 통신 단절(Wi-Fi cohort는 Wi-Fi 단절), watchdog reset 없음 |
| C8 | BOOT 화면 전환(debounce 후 300ms 이내), PC 수동 재수집(5초 이내 전송·수신 후 2초 이내 LCD 반영), 60초 이하 자동 주기, RST 재부팅 |
| 자율 기능 | 기능 선정 문서의 5/5/5/10/5 점수와 각각의 증거 |

BOOT를 누른 채 reset하는 동작은 ROM 다운로드 모드 진입 조건이다. 애플리케이션
실행 이전 동작을 펌웨어가 방지한다고 요구하지 않는다. 정상 부팅 후 BOOT 입력을 시험한다.

I3/I4 복구 시험은 USB 재연결과 PC collector 프로세스 재시작을 별도로 수행한다.
후자는 보드를 켜 둔 상태에서 수행하고, 영속 순번의 연속성·정상 화면 복구를
확인한다. 순번 저장소 유실은 자동 복구 성공으로 채점하지 않고, 전송 차단과
운영자 복구 절차를 검증한다. 상세 기준은 host-device-pipeline-contract.md를 따른다.

## 기계 결과와 archive 연결

필수 필드·nullable·F9.details 구조는
[E2E result schema](../../experiments/schema/end-to-end-result.schema.json)가 소유한다.
F9의 점수 의미는 [자율 기능 평가](hardware-feature-discovery.md)를 따른다.
validator는 schema, 판정/증거, 평가 manifest의 identity 연결과 점수 합계를 검사한다.
archive는 경로 정규화 전·후 모두 검증하며 실패한 경우 raw snapshot만 보존한다.
`automated_test_status`는 integration-test 항목과 증거에서 계산하며 product_pass를 복사하지 않는다.

## production 경로의 평가 사례

아래는 기존 C/F/I 요구를 검사할 사례다. host view-model 검사와 운영자 관측을 연결할
목록이며, 현재 legacy 29개 시험이 이 목록을 모두 실행한다는 뜻은 아니다.
reference-match의 58%·82% stimulus는 [RM 목록](reference-match-matrix.md)에서
원본을 복구한다. 아래 다른 fixture를 그 원본으로 대신하지 않는다.

E1의 파일은 `experiments/fixtures/providers/`, E2의 파일은 `experiments/fixtures/`에 있다.
E1의 정상 시험 기준 시각은
`2026-09-10T00:00:01Z`이며 E2는 해당 원본의 captured_at을 기준으로 한다.
관측할 raw frame·sequence·수신 시각·표시 값과 fixture hash를 실행 기록에 남긴다.

| 시험 | 요구 ID | stimulus·기대값 | 실행 경로·증거 |
|---|---|---|---|
| E1 값·window 변화 | C3/F1~F5/I1~I4 | `codex-percent-window.json`: openai 5h used 20%/remaining 80%, reset `2026-09-10T05:00:00Z`. 다음 새 sequence에 `claude-code-windows.json`: anthropic 5h 35/65, weekly 40/60, model-sub-limit 10/90. window 수와 값·identity가 payload대로 바뀜 | candidate collector→실제 receiver→state→view-model 값·로그와 실제 글자/값 사진. 상수 42는 실패 |
| E2 글로벌 source·시각 | C4~C6/F2/F5/F7/I2/I4 | `codex-resets-history.json`: captured `2026-09-10T16:54:07Z`, latest reset `2026-09-08T01:56:00Z`. 경과는 captured−latest=226,687초이며 sent_at은 reset 시각이 아님 | legacy→wire 매핑, 실제 state/view-model, 출처·조회 시각·경과 표시 사진. reset의 sent_at 대체는 실패 |
| E3 source freshness | C3/C7/F2/F4/I2/I4 | E1 원본에서 reference_time을 observed_at+0/+299/+300초로 변경. 300초 available 입력은 의미 오류 또는 stale로 정규화. 미래 observed_at/last_good_at은 오류. source 시각을 바꿔 새 값으로 만들지 않음 | semantic validator와 production 상태를 별도 대조. envelope sent_at만 새롭게 해도 source-stale이 유지됨 |
| E4 수신·오류 복구 | C7/F3/F4/I3/I4 | 정상→CRC 손상/잘림/중복·역순→새 정상 frame. 마지막 정상 값·순번 보존, 오류 표시·정상 복구. 유효 수신 후 단조 경과 299/300초 경계는 source 상태와 별도로 관찰 | production receiver/cache/view-model, raw bytes·last-good hash·오류/복구 로그 |
| E5 null·복수 source | C3/C7/F1/F2/F5/I1/I2 | matrix의 reset 미제공·unsupported·error·stale·복수 provider. 미제공은 unknown, 0%와 구분. 한 adapter 실패로 다른 provider를 삭제하지 않음 | fixture identity별 의미 대조, production 상태·화면 및 source별 last-good |
| E6 화면·입력 | C2/C8/F5/F6/F8 | 동일 artifact의 30초 유지·세 정보 화면·BOOT/RST·자동/수동 갱신. 시간 한도는 제품 계약을 따름 | LCD 가시 출력과 읽을 수 있는 glyph 영상, 입력·전송·수락·표시 시각의 개별 anchor |
| E7 재연결 | C7/F3/F4/I3/I4 | 보드 전원을 유지한 collector stop/restart, powered link 단절/복구, sender 순번 저장소 유실을 각각 관찰 | 단일 port capture, 후보 frame 수락과 화면 복구. USB 전원 제거/RST는 별도 시나리오 |
| E8 선택 기능 | F9 | 선택 문서의 자원·위험·검증 방법, 미장착/오류 동작 | 실제 선택 기능별 시험과 증거. 후보 자체 점수를 운영자 판정으로 복사하지 않음 |

firmware epoch 기준의 확보·fixture anchor·부팅 후 단조 경과 연결은 후보의 시험 절차에서
확인한다. 같은 frame을 uptime 초와 epoch로 비교해 정상 입력을 거부하면 I4 실패다.
시각 기준이 없는 부팅 상태를 정상 시각으로 간주하지 않는다.

## 송신·수락·광학 관측

1. 운영자가 고정 artifact/fixture/frame hash와 sequence를 기록하고 한 process에서 port를
   점유해 write와 capture를 수행한다. port open/reset, DTR/RTS, 재열거·read 실패를 운영 이벤트로 남긴다.
2. 후보 sender를 관측 경로와 연결할 수 없으면 그 후보의 device acceptance는 미확인으로 남긴다.
   별도 운영자 sender의 수락 로그를 후보 sender의 성공으로 승격하지 않는다.
3. host write 완료, 장치 frame 수락, LCD 가시 변화는 각각 다른 event다. cdm/1에는 ACK가 없어
   seq를 포함한 receiver 로그와 동시 화면 관측으로 연결한다. 해당 로그가 없으면 수락을 추정하지 않는다.
4. BOOT debounce 완료→가시 전환, 수동 명령 시작→write, 장치 수락→LCD 변화의 시작/끝 anchor를
   기록한다. 측정 해상도와 실패한 capture를 남기고 추정 시간을 확정 pass로 바꾸지 않는다.
5. collector 정지/재시작과 powered link 단절은 보드가 켜진 조건에서 수행한다.
   배터리 없는 USB 제거는 재전원 시험이다. 정상 부팅, RST, 재전원과 혼합 채점하지 않는다.

관측 harness와 E1~E8 production 자동화의 구현·실물 실행은 새 비교 준비 상태에서 관리한다.
이 절차 정의와 도구 회귀 통과만으로 C/F/I 실물 pass를 기록하지 않는다.
