# Waveshare 제조사 예제 확보 및 빌드 검증

## 출처와 보관

대상 보드는 [Waveshare ESP32-S3-LCD-3.16 공식 Wiki](https://www.waveshare.com/wiki/ESP32-S3-LCD-3.16)의
Demo 리소스를 사용한다. 공식 패키지 다운로드 주소는 다음과 같다.

```text
https://files.waveshare.com/wiki/ESP32-S3-LCD-3.16/ESP32-S3-LCD-3.16-Demo.zip
```

2026-09-11에 받은 파일의 SHA-256은 다음과 같다.

```text
E5914BB732F47EB6A3D76856F707253EE6008847E6675011796180943683C3DE
```

원본 ZIP과 필요한 ESP-IDF 폴더는 저장소 밖의 ASCII 경로에 둔다.

```text
C:\Espressif\vendor\waveshare-esp32-s3-lcd-3.16\
├─ ESP32-S3-LCD-3.16-Demo.zip
├─ source\ESP32-S3-LCD-3.16-Demo\ESP-IDF\
└─ build\
```

저장소에는 205MB가 넘는 제조사 패키지를 커밋하지 않는다. clone 후 다음
스크립트로 동일한 공식 패키지를 다시 받을 수 있다.

```powershell
.\scripts\fetch-waveshare-demo.ps1
```

## 확인된 예제

압축 패키지의 `ESP-IDF` 폴더에는 다음 프로젝트가 있다.

`01_ADC_Test`, `02_I2C_PCF85063`, `03_I2C_QMI8658`, `04_SD_Card`,
`05_WIFI_AP`, `06_WIFI_STA`, `07_LVGL_V8_Test`, `08_LVGL_V9_Test`,
`09_FactoryProgram`

## 빌드 절차

환경 활성화 스크립트가 ESP-IDF v5.3.2와 Windows 경로 우회 설정을 적용한다.

```powershell
.\scripts\fetch-waveshare-demo.ps1
.\scripts\build-waveshare-example.ps1 -Example factory
.\scripts\build-waveshare-example.ps1 -Example lvgl9
```

두 스크립트 모두 플래시 쓰기나 시리얼 모니터를 실행하지 않는다. 업로드가
필요할 때는 백업 정책과 대상 이미지를 먼저 확정한 뒤 별도로 다음 명령을
실행한다.

```powershell
idf.py -C C:\Espressif\vendor\waveshare-esp32-s3-lcd-3.16\source\ESP32-S3-LCD-3.16-Demo\ESP-IDF\09_FactoryProgram `
  -B C:\Espressif\vendor\waveshare-esp32-s3-lcd-3.16\build\09_FactoryProgram-v5.3.2 `
  -p COM3 flash monitor
```

## 빌드 결과

| 예제 | ESP-IDF 의존성 확인 | 결과 | 산출물 | 비고 |
|---|---|---|---|---|
| `09_FactoryProgram` | `esp_lcd_st7701` 1.1.5, `esp_lcd_panel_io_additions` 1.0.1, `esp_io_expander` 1.2.1, LVGL 로컬 소스 | 성공, 1,839/1,839 단계 | `09_FactoryProgram.bin` (0x561320) | 16MB Flash 설정, 다음 하드웨어 테스트 기준 |
| `08_LVGL_V9_Test` | `esp_lcd_st7701` 1.1.5, `esp_lcd_panel_io_additions` 1.0.1, `esp_io_expander` 1.2.1, LVGL 9.5.0 | 성공, 1,890/1,890 단계 | `08_LVGL_V9_Test.bin` (0x12f020) | 제조사 기본 설정이 8MB Flash이므로 업로드 전 검토 필요 |

빌드 산출물의 SHA-256도 기록해 둔다.

```text
09_FactoryProgram.bin  5D2D7B8B6D8B1A2C965EC12331742A5C78062A06788DDA29066283D86336219D
08_LVGL_V9_Test.bin    4ACBC1C2CED3B53DDB3032B63BFCE4DAA3FB701A7EF7E2B7661980A81FE1D458
```

두 예제 모두 `Project build complete`와 ESP32-S3 bootloader, partition table,
application binary 생성을 확인했다. 빌드 로그의 모든 경로는 `C:\Espressif`
아래 ASCII 경로였다.

## 판단

- 제조사 ESP-IDF 예제는 현재 기준 ESP-IDF v5.3.2에서 호스트 빌드가 가능하다.
- ST7701 초기화 경로와 LVGL 그래픽 경로의 컴파일 호환성을 확인했다.
- 빌드 성공은 LCD가 실제로 표시된다는 뜻은 아니다. LCD 방향·색상·백라이트와
  입력 장치의 실제 동작은 보드에 업로드한 뒤 별도 확인해야 한다.
- `09_FactoryProgram`은 실제 보드가 16MB Flash인 현재 장치와 설정이 맞고,
  백업 후 COM3에 실제 업로드하여 부팅 로그까지 확인했다.

## 실제 업로드 및 부팅 검증

플래시를 변경하기 전에 16MiB 전체를 읽어 백업했다. 백업 파일은 저장소 밖에
보관한다.

```text
경로: C:\Espressif\vendor\waveshare-esp32-s3-lcd-3.16\backup\factory-flash-20260911-005604.bin
크기: 16777216 bytes
SHA-256: AA51BA15B975EC2E564506E609729F36D85DA23D8892023396A700846955A1E6
```

백업 검증이 성공한 뒤 다음 빌드 산출물을 COM3에 플래시했다.

```text
09_FactoryProgram.bin
SHA-256: 5D2D7B8B6D8B1A2C965EC12331742A5C78062A06788DDA29066283D86336219D
```

`idf.py flash`는 부트로더, factory 앱, 파티션 테이블을 기록하고 각 이미지의
해시 검증 및 `Hard resetting via RTS pin`을 성공적으로 마쳤다. `erase_flash`는
실행하지 않았다.

업로드 직후 모니터 로그에서 ESP-IDF v5.3.2 부트, 16MB Flash, 8MB Octal PSRAM,
ST7701 초기화, QMI8658 ID `0x7c` 및 가속도계·자이로 self-test 성공을 확인했다.
TF 카드가 없는 상태에서는 `ESP_ERR_TIMEOUT (0x107)`가 기록됐지만 앱은
`app_main()` 이후 Wi-Fi 초기화를 계속했다.

사용자가 촬영한 약 10초 영상에서도 파란 배경, 색상 패널, `flash:16M`,
`psram:8M`, RTC와 가속도 값이 확인됐다. RTC와 센서 값이 프레임마다 바뀌고,
세로 방향에서 문자가 읽히며 백라이트가 켜져 있어 LCD 출력·기본 방향·색상은
실물에서 확인된 것으로 기록한다. 영상에는 BOOT 버튼과 SD 읽기/쓰기 동작이
포함되지 않았으므로 입력과 SD 기능은 별도 검증이 필요하다.

```text
증거: C:\Users\이광진\Downloads\KakaoTalk_20260911_011356684.mp4
크기: 4526012 bytes
SHA-256: 1381B46B3A27BB878CAA6A07276978CC53BCA5FB24744D7E0768734C6B0033EA
```

## BOOT·RESET 동작 확인

두 번째 사용자 영상에서 BOOT 입력 후 메트릭 화면이 도시·해변 이미지 화면으로
전환되는 것을 확인했다. 제조사 안내의 인터페이스 전환 동작과 일치하는 것으로
보이지만, 정확한 클릭 횟수와 누름 시간은 측정하지 않았다.

사용자 관찰에 따르면 RESET 버튼을 누르면 USB-Serial/JTAG 장치가 잠시 COM3에서
사라졌다가 다시 열거된다. 이는 칩 리셋에 따른 정상 동작이며, 리셋 후에는
시리얼 모니터를 다시 열어야 한다.

```text
증거: C:\Users\이광진\Downloads\KakaoTalk_20260911_013525202.mp4
크기: 4981010 bytes
SHA-256: A9EE6ADFDED6A9138547B9F3385E27D50E8F259913F079F1C1E66B0917C0F381
길이: 약 10.37초
```

BOOT 단일 클릭의 백라이트 토글, 이중 클릭의 SD 읽기/쓰기와 TF 카드 상태는
추가 시험 항목으로 남긴다.

## 재현 기록

- 확인일: 2026-09-11
- 포트: COM3
- 보드: Waveshare ESP32-S3-LCD-3.16, ESP32-S3 rev v0.2
- 16MiB 출고 플래시 백업: 완료, SHA-256 검증 완료
- `09_FactoryProgram` 플래시 쓰기: 완료, 이미지 해시 검증 완료
- LCD 실제 출력: 사용자 영상으로 확인
- 플래시 삭제: 수행하지 않음
