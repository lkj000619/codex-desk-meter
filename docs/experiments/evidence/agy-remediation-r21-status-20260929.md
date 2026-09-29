# AGY r21 BOOT 입력 보완 상태

## 범위와 현재 상태

사용자가 USB 단절·RST·재전원 인가 후 값이 오지 않고, BOOT는 짧은 입력에서 간헐적으로 반응하지
않으며 두 번 누르거나 약 500ms 이상 누르면 페이지가 바뀐다고 보고했다.
현재 r20 보드의 30초 LCD 출력 판정은 유지하되, 짧은 BOOT 입력의 신뢰성과 정확한 latency는
합격으로 취급하지 않는다. 공급자 순환에 따른 같은 페이지 번호 유지와 입력 누락은 구분한다.

최초 process 조회에서 실행 중인 PC 송신기는 없었고 COM3는 열거되어 있었다. 앞선 유한 송신이
종료된 뒤 RST/재전원 인가로 수신 값이 지워지면 다음 송신이 없는 운영 상태였다.
기존 AGY r20 CLI를 같은 store/alias로 5초 주기·최대 61회 실행했다. 사용자는 송신 실행 중
RST 후 **약 3초, 10초 이내에 값이 돌아옴**을 확인했다. 이는 사용자 관찰이며 동기화된 latency
계측이 아니다. 자동 주기 대기까지 포함한 reset→복구와 수신→LCD 2초 조건은 구분한다.
실제 USB 단절/재전원 시험 결과는 아직 별도로 확인되지 않았다.
기존 CLI는 327.016초 후 정상 종료했으며 61개 successful cycle을 보고했다. 파일 관측은
60개 변경을 잡았고 마지막 순번 90·다음 영구 순번 91이다. 29→91의 62개 reservation 중
최소 하나는 successful cycle로 반환되지 않았으나 원인을 특정 reset으로 단정하지 않는다.
종료 후 안전한 native read는 0 bytes/오류 없음이었다. 모든 cycle의 device ACK를 확인한 것으로
기록하지 않는다. 진단 sender는 현재 종료됐고 재리셋 복구 관찰에는 송신 실행이 필요하다.

## r21 고정 입력과 실행

- 시작 보존본: AGY r20 `6e00bd8ba518f008d50a762f035a5e8c7e8b6e5c`, 제품 파일 116개 byte/hash 동일.
- 모델: `gemini-3.8-flash-medium`, 기존 finite 정책 `2c79ccc4…1034f`, data scope 동일.
- 환경 사전 검증: 123개 통과, host runtime·COM3·clean checkout·준비 commit 2개 확인.
- 시작: `2026-09-29T06:31:27.025335Z`, 현재 실행 중. 보드는 아직 r20이다.
- 고정 요청: 실제 firmware 입력 handler가 짧은 입력·bounce·hold·release를 처리하고,
  느린 renderer/IMU에 입력 수집이 종속되지 않도록 실패 재현과 생산 코드 회귀 시험을 먼저 작성.
- 기존 provider 순환·framebuffer·IMU·parser·USB와 고정 fixture를 유지하고, PC 송신 운영 조건을 명시.
- 새 online collector·autorun service·ACK·수신 cache 영속화는 이번 범위에 추가하지 않음.
- root는 제품 코드/시험을 작성하지 않는다. AGY 실행 중 추가 피드백은 없다.
- 시작 후 들어온 약 3초 RST 복구 관찰은 운영자 증거로만 보존하며 실행 중 AGY에 전달하지 않았다.
- 보완 실행은 `ranking_eligible:false`, 원래 단회 비교·순위와 별도이며 전체 `product_pass:false`다.

운영자 launch helper를 preflight 완료 전에 한 번 호출하여 guard가 거부했다. 이후 사전 검증 완료를
확인했다. wrapper CLI의 argparse 옵션 위치도 한 번 잘못 호출해 AGY 시작 전에 종료됐고,
옵션을 action보다 앞에 둔 정상 호출로 시작했다. 두 사건은 제품 실패/AGY trial로 계산하지 않는다.

- [r21 사전 검증 및 입력 고정 receipt](agy-remediation-r21-preflight-20260928.json)
- [r20 RST 복구·BOOT 진단 기록](agy-remediation-r20-reconnect-boot-diagnosis-20260929.json)
- [r20 진단 원본 archive receipt](agy-remediation-r20-reconnect-boot-artifacts-20260929.json)
