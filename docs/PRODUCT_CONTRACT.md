# Version 2 제품 계약

상태: fixture E2E 구현 요구사항. 실행 승인·baseline 동결은 운영자가 별도 관리한다.
제품 동작의 원본은 이 문서와 연결된 JSON schema다. 값이 다르면 결함으로 기록하며 추정하지 않는다.

## 1. 목표와 범위

Waveshare ESP32-S3-LCD-3.16, ESP-IDF v5.3.2, 가로 820×320 LCD.
구현 경로는 **PC fixture collector → 정규화 → USB serial `cdm/1` → 실제 ESP32
receiver/cache/stale → LCD GUI**다. 펌웨어 프로젝트와 BSP는 후보가 작성한다.
펌웨어 내장 상수 화면·host loopback만으로 PC→장치 연결을 대체하지 않는다.
실제 계정 수집·Wi-Fi transport·Version 1 이식은 이번 범위 밖이다.

| ID | 필수 동작·합격 조건 |
|---|---|
| C1 | `idf.py set-target esp32s3`·`idf.py build` 성공 |
| C2 | 정상 부팅 뒤 LCD가 30초 이상 켜지고 가로 UI가 잘리지 않음 |
| C3 | PC가 전달한 provider/window 목록의 사용률 또는 잔여율·조회 시각·resets_at 표시. 원본에 없는 창·값을 만들지 않음 |
| C4 | `codex-resets.com`의 최근 글로벌 리셋 시각과 경과 시간 표시 |
| C5 | 리셋 기록이 없으면 마지막 알려진 리셋의 경과 시간, 그것도 없으면 default 화면 표시 |
| C6 | 글로벌 화면에 `codex-resets.com` 출처·조회 시각 표시 |
| C7 | DNS/TLS/HTTP/JSON·빈 응답·오래된 입력에도 화면·장치 유지, last-good 보존·정상 복구 |
| C8 | 정상 부팅 후 BOOT 화면 전환, 자동 갱신·PC 수동 갱신 동작 구현·문서화 |
| I1 | fixture collector가 출처·시각·단위·오류를 보존하고 credential을 노출하지 않음 |
| I2 | provider adapter로 정규화하고 서로 다른 글로벌 source를 분리함 |
| I3 | 실제 transport의 frame·길이·CRC·순번·재연결을 검증하고 raw log를 남김 |
| I4 | 실제 firmware가 검증된 frame을 cache/stale/복구·LCD에 반영함 |

F1=collector, F2=정규화, F3=transport, F4=receiver, F5=GUI, F6=입력·갱신,
F7=글로벌 리셋, F8=빌드·관측, F9=선택 온보드 기능을 각각 기록한다.
C1~C8·I1~I4·F1~F9는 모두 평가 대상이다. 미구현·미검증은 사유와 해당 상태로 남긴다.

## 2. 데이터 의미

- UsageSnapshot의 필수 키·nullable·상태·window 구조는
  [usage-snapshot.schema.json](../experiments/schema/usage-snapshot.schema.json)을 따른다.
  provider/agent/host/model/account profile을 분리하고 provider·window 수를 하드코딩하지 않는다.
  available source의 agent_id·host_id는 필수며 unsupported/unauthorized/error는 null을 허용한다.
- source가 제공한 percent·token·credit만 사용한다. absolute token 잔량을 제공하지 않으면
  null·percent/unknown을 보존한다. 서로 다른 metric/provider/session을 임의로 합산하지 않는다.
  absolute window의 used+remaining=limit은 허용 오차 0.01, percent는 별도로 검증한다.
- 필드 누락·범위 밖 percent·잘못된 RFC3339 시각은 오류다. null을 0·현재 시각으로 대체하지 않는다.
  observed_at·last_good_at이 reference_time보다 미래이면 오류다.
- snapshot은 고정 reference_time을 주입해 시험한다. observed_at 기준 age≥300초는 stale이다.
  0·299·300초 경계를 시험한다. LCD는 last-good 수신 뒤 단조 시계의 age≥300초에서 stale을 표시한다.
  원본 조회 시각을 수집·전송 시각으로 덮어써 오래된 값을 새 값처럼 보이지 않는다.
- 미래 resets_at은 scheduled로 허용하고 과거 resets_at은 expired/재조회 상태로 표시한다.
  경과 시간과 예측을 확정 일정으로 표시하지 않는다.
- `codex-reset.com`과 `codex-resets.com`은 별개다. 첫 source의 forecast는 파서 호환용이며
  화면에는 두 번째 source만 표시한다. 다른 provider의 quota reset으로 재사용하지 않는다.
- legacy fixture last_reset_at은 latest_reset_at으로 매핑한다. 글로벌 wire는
  논리 provider→source, fetched_at→captured_at, schema_version=1을 사용한다.
  captured_at이 null이면 정상 wire를 만들지 않고 수집 오류를 기록한다.
  상세 필수 키는 [cdm-frame.schema.json](../experiments/schema/cdm-frame.schema.json)을 따른다.
- 한 adapter의 실패는 다른 adapter를 중단·삭제하지 않는다. 오류 입력에서 last-good 값·시각을
  보존하고 오류를 표시하며 정상 복구 시 해제한다. 정상값이 없을 때도 UI를 유지한다.

## 3. 전송·수신

- `cdm/1` frame은 protocol·uint32 sequence·sent_at·payload(usage/global_resets 배열)·integrity다.
  UTF-8 JSON의 key를 정렬하고 공백 없이 ensure_ascii=false로 직렬화하며 NaN/Infinity는 금지한다.
  integrity를 제외한 canonical envelope의 CRC32를 대문자 8자리 hex로 기록한다.
- canonical JSON 뒤 LF 한 바이트, LF 포함 최대 65,536 bytes다. CRLF·pretty JSON·추가 LF·
  잘못된 UTF-8·잘림·schema/version/CRC 오류를 거부하고 last-good를 유지한다.
- 순번은 `0 < (candidate-current) mod 2^32 < 2^31`일 때만 새 값이다.
  중복·역순·half-range를 거부하고 4,294,967,295 다음 0은 수락한다.
- sender는 안정적인 device alias별 마지막 예약 순번을 원자적으로 영속화한 뒤 쓴다.
  실패한 write도 번호를 소비한다. 재시작·COM 재열거 후 다음 번호를 사용한다.
  disconnect/stale/새 sent_at을 이유로 receiver 순번 상태를 초기화하지 않는다.
- sender state 유실·손상 시 전송을 중지한다. 초기 생성은 receiver state가 비었음을 확인한
  명시적 절차다. 보드 reset을 정상적인 PC 재시작 복구 수단으로 쓰지 않는다.
  같은 receiver에 7 수락→재시작 뒤 1 거부→영속화한 8 수락을 시험한다.
- USB serial은 115200 baud·8N1·flow control 없음, device당 sender 한 개다.
  재open 시도는 초당 최대 1회, port 사용 가능 후 5초 안에 새 snapshot 전송,
  frame 수락 후 2초 안에 LCD 반영. host write receipt는 device ACK가 아니다.
  `cdm/1`에 device ACK/retry는 정의돼 있지 않다.
- 운영자가 지정한 COM port를 사용한다. 후보 실행 중 보드 접근은 수행하지 않고 절차를 제출한다.

## 4. 화면·입력·추가 기능

| 화면 | 표시 |
|---|---|
| 대시보드 | provider/window별 사용량·잔여율, 단위·조회 시각·resets_at |
| 글로벌 리셋 | 최근 리셋·경과 시간 또는 default, 단일 출처·조회 시각 |
| 상태/오류 | 단절·파싱 오류·stale·last-good 시각·재시도 상태 |

BOOT는 debounce 후 300ms 안에 세 화면을 순환하거나 동등한 탐색을 제공한다.
RST는 시스템 reset 전용이다. BOOT를 누른 채 reset하는 ROM 다운로드 모드는 정상 입력 시험이 아니다.
자동 수집 주기는 최대 60초다. 수동 갱신은 PC collector 재수집 명령이며 BOOT 요청이 아니다.
수동 명령 후 5초 안에 새 순번으로 전송하고 수락 후 2초 안에 LCD 반영한다.
자동 주기와 독립적으로 작동하며 실패 시 last-good·오류/stale 상태를 보존한다.
가로 UI의 정보는 잘리지 않아야 한다. 선택 IMU 회전은 조건·debounce·복귀를 기록한다.

온보드 자율 기능 후보를 정확히 3개 작성하고 1개를 스스로 선택·구현한다.
각 후보의 가치·자원·비용·위험·시험과 선택하지 않은 이유를 기록한다.
추가 부품·credential 없이 재현 가능해야 하며 핵심 기능을 약화하지 않는다.
핵심과 모듈/설정으로 분리하고 제조사 데모 반복을 선택 기능으로 제출하지 않는다.

## 5. 시험·제출 경계

실제 제품 파서·상태 C 모듈을 호출하는 host adapter를 제공하고 compile/link 근거를 남긴다.
legacy adapter는 stdin UTF-8 JSON `{source, events:[{now, body, error}]}`를 읽고
stdout snapshot 배열, stderr log를 출력한다. 호출마다 초기 상태, event 안에서는 같은 상태다.
body는 원본 객체·잘못된 JSON 문자열·null, error는 null/dns/tls/http_500이다.
fixture 출력은 source=fixture·원본 windows(id 포함)·observed_at=captured_at·stale·error_code,
글로벌 출력은 provider·fetched_at·latest_reset_at·nullable forecast_24h/48h_percent·
forecast_is_schedule=false·stale·error_code다. legacy 출력은 wire 모델과 구분한다.
`scripts/evaluate-product.py`는 이 legacy seam만 검사하며 전체 E2E·실물 합격을 증명하지 않는다.

빌드·정상/null/오류/시간 경계·last-good·복구·transport·선택 기능 시험을 남긴다.
운영자가 실제 송수신·세 화면·BOOT/RST·30초 유지·전원 유지 상태의 USB 링크 단절/복구를
확인한다. candidate source를 수정하지 않고 artifact·raw bytes·log·사진/영상으로 판정한다.

[end-to-end-result.schema.json](../experiments/schema/end-to-end-result.schema.json)에
C/F/I/G·build/host/transport/hardware 상태와 증거를 기록한다. schema 검증은 실제 동작의 증명이 아니다.
reference 도달과 전체 제품 합격은 별도다. `product_pass=true`에는 전체 계약과 운영자 증거가 필요하다.
G1~G6(레이아웃·가독성·출처/상태·오류/null·상호작용·보드 최적화)는 운영자가 관찰해 채점한다.
미측정 시간/token/실물 상태는 null·not_run·blocked와 사유로 남긴다.
정규화 실행 token total=input+output, cached/reasoning은 제외한다.
원본 provider_total은 정의와 함께 별도로 보존하고 정규화 값으로 덮어쓰지 않는다.

계정 우회 수집·제한 우회·예측 일정 보장·전체 flash 삭제·외부 부품 추가는 허용하지 않는다.
