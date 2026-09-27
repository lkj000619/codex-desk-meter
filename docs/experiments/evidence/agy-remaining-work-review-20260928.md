# AGY 남은 작업 재점검 — 2026-09-28

## 현재 판정과 점검 범위

**pilot 실행 진입 준비 통과 / 기존 AGY run 완주 실패 / 제품 전체 합격 미확인.**

원본 implementation `9d52fa50529ae8020c6d1f54f193c7f74f875181`, 독립 빌드 소스,
제품 계약·공통 prompt, 실행·업로드·사진·영상 기록을 대조했다.
제품 코드 변경, 재빌드, 추가 flash, AGY 추가 실행·피드백은 수행하지 않았다.
원본 실행 측정과 archive는 그대로 유지한다.

## 이미 확인된 범위

| 항목 | 확인된 근거와 한계 |
|---|---|
| 실행 환경 | 고정 기준본 사전 시험 111개·host C/C++ runtime·COM3·clean checkout 통과. 실행 시 날짜·COM3 점유는 다시 확인해야 함 |
| 제품 빌드 | 별도 소스 복사본의 host build, ESP-IDF set-target/build exit 0 |
| 부분 자동 시험 | CTest 2개, 기존 evaluate-product 29개 통과. 전체 provider·통합 시험을 대신하지 않음 |
| 보드 업로드·부팅 | flash 검증, runtime ELF 식별 일치, 20초 boot 관찰 중 panic 없음 |
| LCD 기본 출력 | 업로드 후 사진의 기본 화면·문구가 GUI 소스와 일치 |
| IMU 초기화 | QMI8658 인식 로그. 회전 동작 합격 근거는 아님 |

## 남은 작업과 종료 조건

| 우선순위 | 작업 | 현재 증거·문제 | 확인 완료 조건 |
|---|---|---|---|
| P0 | 데이터 의미·null 처리 | GUI가 데이터 부재 시 잔여 58%, 고정 조회 시각을 표시하고 유효한 현재 시각이 없을 때 고정 경과 시간을 표시함 | 데이터 없음·unknown·stale·error가 실제 값과 구분되고, 조회·경과 시각을 임의로 만들지 않음. fixture와 실제 LCD 출력 대조 |
| P0 | BOOT 핀·화면 전환 | `main.c:24-25`에서 BOOT와 LCD SPI CS가 GPIO0 공유. `main.c:243-246`은 입력 초기화 뒤 LCD 초기화. boot log에서 GPIO0 출력 전환 및 입력 조작 기록 없는 BOOT 이벤트 관측 | 핀 사용 상태와 실제 버튼 입력을 확인하고, 누르지 않을 때 전환 없음·누를 때 계약에 맞는 전환을 영상과 로그로 재현 |
| P0 | 실제 USB 수신 경로 | upload log의 연결은 USB Serial/JTAG. `meter_transport.c:13,83`은 UART0 수신. sdkconfig는 UART primary/USB Serial-JTAG secondary console. startup 문구는 실제 frame 수신 근거가 아님 | 지정 COM3에 보낸 동일 frame의 raw 송신·수신·수락·LCD 반영 증거. 코드·연결 방식 정합성 확인. 현재는 실제 통신 실패를 재현한 상태는 아님 |
| P0 | PC collector·전체 데이터 경로 | 원본 변경에 제품용 PC collector·송신 구현이 없고, 구현된 C receiver와 host 시험 adapter만으로 I1~I4를 입증할 수 없음 | 표준 fixture collector → 정규화 → PC 송신 → 실제 보드 receiver/state → LCD까지 구현·검증. 순서 영속성·재시작·재연결·수동 갱신 포함 |
| P0 | 시간 경과·stale | receiver가 `now_str=NULL`로 처리하고, main은 GUI에도 NULL 전달. `meter_state_tick`은 정의만 있고 main/components에 호출 없음. 함수 자체도 300초 비교 없이 데이터가 있으면 즉시 stale로 설정 | 실제 제품 경로에서 299/300초 경계·오래된 frame·미래 시각·오류 후 last-good·복구를 시간 근거와 함께 검증. host legacy 시험 통과를 이 경로의 증거로 사용하지 않음 |
| P1 | LCD 표시 안정성 | 19.52초 영상의 sampled frame에 blank/partial 출력 관측. 시야각·반사 영향 및 원인은 미확정 | 고정 시야각에서 세 화면·전환·회전 시 정보 누락·잘림을 재현/배제하고 G1~G6 평가 증거 확보 |
| P1 | IMU 선택 기능 | module·host 시험·센서 인식 근거는 있지만 실물 방향 변경·안정성 판정 없음 | 선언된 회전 동작·응답·deadband·정보 보존을 실제 보드 영상/로그로 검증 |
| P1 | 전체 provider·장애 평가 | 기존 29개 사례는 개인 usage·글로벌 reset legacy 시험. 새 provider matrix 전체 결과 없음 | 원본 계약의 provider/agent/metric/window·unsupported/unavailable/null·오류·CRC·sequence·recovery 시험과 결과 근거 확보 |
| P0 | AGY 완주·제출 | 미등록 pytest 명령 거부로 environment_failed. 최종 구조화 E2E 결과 없음 | 새 유효 run이 제한 정책을 지키고 결과 파일을 제출. schema·manifest join·증거·feature/integration/GUI 판정 확인 |
| P0 | 정량 비교 유효성 | 서로 다른 입력으로 수행한 실패 pilot 이력, 미제출 결과, command exit code 누락 | 공통 baseline·prompt·권한·toolchain·시간 제한·평가를 모든 후보에 고정. 미측정 failed_commands는 null 유지. 순위 반영은 계약상 유효한 결과에 한함 |

GPIO0과 transport는 코드·설정의 구체적 충돌 근거다. 실제 버튼·수신 결과를 아직 측정하지
않았으므로 각각을 실물 실패 확정으로 확대하지 않는다. 화면 partial 출력의 원인을 이 충돌과
동일하다고 단정하지 않는다.

## 다음 작업의 실험 경계

현재 결함 목록은 운영자 평가 기록이다. 원본 AGY run에 후속 지시로 보내거나 코드를
고쳐 원본 성적으로 대체하지 않는다. 이 목록을 전달해 기존 구현을 보완하도록 실행하면
별도 remediation run으로 분류하고 최초 단일 prompt 비교와 합산하지 않는다.
정식 비교 준비를 위한 새 pilot은 동일한 공통 과제와 고정 입력에서 시작하고, 이번
구현이나 이 평가의 맞춤형 해결 힌트를 후보 하나에만 제공하지 않는다.

새 pilot 실행 환경의 진입 준비는 이미 완료됐다. 그러나 준비 통과가 위 제품 결함의
해결이나 AGY 완주를 보장하지는 않는다. 현재 사용자 요청은 재점검이므로 새 pilot은 시작하지 않았다.

## 근거

- [원본 실행·독립 빌드](agy-r01-result-20260928.md)
- [업로드·runtime 식별](agy-r01-hardware-upload-20260928.json)
- [실물 사진·영상 평가](agy-r01-hardware-visual-20260928.md)
- [새 기준본 사전 검증](agy-test-entry-preflight-20260928.json)
- [제품 계약](../../PRODUCT_CONTRACT.md), [PC 통합 계약](../integration-contract.md)

원본 소스는 `C:/Espressif/benchmark-runs/evaluation-r01-20260928/checkout`에서 확인했다.
세부 파일 hash와 원본 증거 불변성 확인은 [점검 metadata](agy-remaining-work-review-20260928.json)에 기록했다.
