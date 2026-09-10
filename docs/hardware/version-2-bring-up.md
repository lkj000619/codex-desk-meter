# Version 2 hardware bring-up

## 대상

- Board: Waveshare ESP32-S3-LCD-3.16
- 연결 포트: COM3
- 확인일: 2026-09-11

## 현재 확인 결과

COM3에서 Espressif USB 장치가 정상적으로 인식됐다.

| 항목 | 관찰 결과 |
|---|---|
| USB VID/PID | `303A:1001` |
| Windows 장치 상태 | 정상 |
| SoC | ESP32-S3, chip revision v0.2 |
| 출고 펌웨어 프로젝트 | `RGB_Demo` |
| 출고 펌웨어 ESP-IDF | `v5.3.2-dirty` |
| SPI Flash | 16MB, DIO, 80MHz |
| PSRAM | 8MB Octal PSRAM, 80MHz |
| LCD 제어 | ST7701, 3-wire SPI initialization + RGB panel |
| ST7701 component | v1.1.2 |
| QMI8658 | ID `0x7c`, 가속도계·자이로 self-test 성공 |
| Wi-Fi | STA 초기화까지 진행 |

COM3를 115200 baud로 5초간 읽었을 때 출고 펌웨어가 부팅되어 `app_main()`까지
진행하는 것을 확인했다. 이 확인 과정에서는 펌웨어를 쓰거나 플래시를 지우지
않았다.

## 제조사 예제 업로드 결과 (2026-09-11)

플래시를 덮어쓰기 전에 보드의 16MiB 전체를 백업했다. 백업은 저장소 밖에
보관하며, 다음 파일의 크기와 SHA-256을 검증했다.

```text
경로: C:\Espressif\vendor\waveshare-esp32-s3-lcd-3.16\backup\factory-flash-20260911-005604.bin
크기: 16777216 bytes
SHA-256: AA51BA15B975EC2E564506E609729F36D85DA23D8892023396A700846955A1E6
```

백업 검증 후 Waveshare 공식 `09_FactoryProgram`을 COM3에 업로드했다.

```text
09_FactoryProgram.bin
SHA-256: 5D2D7B8B6D8B1A2C965EC12331742A5C78062A06788DDA29066283D86336219D
```

부트로더, 애플리케이션, 파티션 테이블의 쓰기와 각 이미지의 해시 검증이
성공했고, `Hard resetting via RTS pin` 뒤 `Done`으로 종료됐다. 전체 플래시
삭제 명령(`erase_flash`)은 실행하지 않았다.

업로드 직후 115200 baud 모니터에서 다음을 확인했다.

- ESP-IDF v5.3.2 부트로더가 `09_FactoryProgram`을 factory 파티션에서 로드
- 16MB SPI Flash와 8MB Octal PSRAM 초기화 성공
- ST7701 RGB 패널 초기화 경로 실행
- QMI8658 ID `0x7c` 확인 및 가속도계·자이로 self-test 성공
- Wi-Fi STA 초기화 및 앱의 `app_main()` 복귀
- TF 카드가 없을 때 `ESP_ERR_TIMEOUT (0x107)`가 기록되지만 앱은 계속 진행

시리얼 로그만으로 LCD의 실제 광학 출력, 방향, 색상과 백라이트 상태를
판정할 수 없다. 화면은 사용자가 직접 확인해야 한다.

## LCD 화면 확인 (사용자 영상)

사용자가 촬영한 영상을 확인한 결과, 업로드한 FactoryProgram 화면이 실제로
출력됐다.

- 파란 배경과 색상별 상태 패널이 표시됨
- `flash:16M`, `psram:8M`, `Vbat`, RTC와 가속도 값이 읽힘
- 약 10초 동안 RTC와 센서 값이 갱신됨
- 세로(포트레이트) 방향에서 문자가 정상적으로 읽힘
- 백라이트가 켜져 있고 화면 전체가 표시됨

증거 파일은 저장소 밖에 보관한다.

```text
파일: C:\Users\이광진\Downloads\KakaoTalk_20260911_011356684.mp4
크기: 4526012 bytes
SHA-256: 1381B46B3A27BB878CAA6A07276978CC53BCA5FB24744D7E0768734C6B0033EA
```

## BOOT·RESET 확인 (두 번째 사용자 영상 및 관찰)

두 번째 영상에서 BOOT 입력 후 메트릭 화면이 도시·해변 이미지 화면으로
전환되는 것을 확인했다. 제조사 안내의 인터페이스 전환 동작과 일치하는
것으로 보이지만, 영상만으로 정확한 클릭 횟수와 누름 시간을 측정하지는
않았다.

RESET 버튼을 누르면 USB-Serial/JTAG 장치가 잠시 COM3에서 사라졌다가 다시
열거되는 현상은 정상적인 칩 리셋 동작이다. 리셋 직후에는 시리얼 모니터를
다시 열어야 하며, 이전 부팅 로그의 `USB_UART_CHIP_RESET` 원인과도 일치한다.

```text
파일: C:\Users\이광진\Downloads\KakaoTalk_20260911_013525202.mp4
크기: 4981010 bytes
SHA-256: A9EE6ADFDED6A9138547B9F3385E27D50E8F259913F079F1C1E66B0917C0F381
길이: 약 10.37초
```

BOOT 단일 클릭에 의한 백라이트 토글, 이중 클릭에 의한 SD 읽기/쓰기와 SD
카드 장착 상태는 별도 시험이 필요하다.

## 관찰된 오류

TF 카드 초기화에서 다음 오류가 발생했다.

```text
sdmmc_init_ocr: send_op_cond (1) returned 0x107
sdmmc_card_init failed (0x107)
```

오류 후 RTC, QMI8658과 Wi-Fi 초기화가 계속 진행됐으므로 부팅을 중단시키는
오류는 아니었다. TF 카드 장착 여부를 확인하기 전까지 원인을 보드 결함으로
판정하지 않는다.

## 개발 PC 상태

- Espressif Installation Manager CLI 0.19.0 설치 완료
- ESP-IDF v5.3.2와 ESP32-S3 툴체인 설치 완료
- 설치 경로: `C:\Espressif`
- `idf.py`, `esptool.py`, Python 3.11.15, CMake 3.30.2, Ninja 1.12.1 확인
- COM3에서 `esptool.py chip_id` 통신 성공
- ESP32-S3 공식 `hello_world` 전체 빌드 성공
- Waveshare 공식 `09_FactoryProgram` 및 `08_LVGL_V9_Test` 빌드 성공
- 출고 16MB 플래시 전체 백업 및 SHA-256 검증 성공
- Waveshare 공식 `09_FactoryProgram` COM3 업로드 및 이미지 해시 검증 성공
- 전체 플래시 삭제(`erase_flash`)는 수행하지 않음

한글 사용자 경로에서 ESP-IDF v5.3.2 도구의 인코딩 문제가 재현됐다. 빌드와
임시 파일은 ASCII 경로에 두고 ccache를 비활성화하는 것으로 해결했다. 자세한
절차는 [Windows 개발 환경](../DEVELOPMENT_ENVIRONMENT.md)에 기록했다.

## 다음 확인 순서

1. 보드 PCB의 V1/V2 리비전 표기와 TF 카드 장착 상태 확인
2. BOOT 단일·이중 클릭, 전원 스위치와 SD 동작을 별도 시험
3. 최소 LCD 테스트 펌웨어를 에이전트 실험의 첫 구현으로 생성·업로드
4. 30분 이상 장시간 실행, 네트워크 단절과 재부팅 복구 시험
5. Version 2 제품 계약의 C1~C8 실물 합격 시험

## 남은 확인 사항

- BOOT 단일·이중 클릭, 전원 스위치와 SD 테스트 동작
- 보드 PCB 리비전과 TF 카드 장착 여부
- 출고 펌웨어의 전체 기능 동작
- 장시간 실행과 재부팅 후 LCD 상태
- `08_LVGL_V9_Test`의 8MB Flash 기본 설정을 실제 보드에 적용할지 여부
