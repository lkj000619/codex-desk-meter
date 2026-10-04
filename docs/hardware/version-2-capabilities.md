# Version 2 보드 사실과 제조사 source

이 문서는 공통 보드 사실이다. 후보 제품 코드·검증된 공통 BSP는 제공하지 않는다.
BSP 구현·시험은 후보 작업에 포함한다. GPIO·극성·API를 추정하지 않는다.

## 보드 자원

| 항목 | 사실 |
|---|---|
| 보드/MCU | Waveshare ESP32-S3-LCD-3.16 / ESP32-S3R8, 최대 240MHz |
| 메모리 | 16MB Flash, 8MB Octal PSRAM |
| LCD | ST7701 RGB565, 원래 320×820; 제품 기본은 가로 820×320 |
| LCD 제어 SPI | CS=0, SCK=2, SDO=1 |
| RGB 제어 | DE=40, PCLK=41, VSYNC=39, HSYNC=38, RESET=16 |
| RGB R0..R4 | 17, 46, 3, 8, 18 |
| RGB G0..G5 | 14, 13, 12, 11, 10, 9 |
| RGB B0..B4 | 21, 5, 45, 48, 47 |
| RGB data_gpio_nums[0..15] | B0..B4 → G0..G5 → R0..R4 (RGB565 bit order) |
| 백라이트 | GPIO6, active-low. 제조사 PWM은 8-bit duty를 255-밝기로 역변환 |
| BOOT | GPIO0, active-low 입력·pull-up. LCD CS와 공유하므로 초기화·입력 동작 확인 |
| RST | 시스템 reset, 앱의 일반 입력 아님 |
| I2C | SCL=7, SDA=15 |
| IMU / RTC | QMI8658 주소 0x6B / PCF85063 주소 0x51 |
| 전원·배터리 | 전원 스위치·3.7V 배터리 커넥터·ADC 예제. 배터리/RTC 백업 전원 장착은 운영자가 확인 |
| TF | FAT32 슬롯, 현재 공통 관측은 카드 미장착; 미장착 실패가 앱을 중단하지 않아야 함 |
| 무선 | Wi-Fi/BLE 자원 있음. 이번 기본 transport는 USB serial |

핀·bit order는 제조사 `09_FactoryProgram/main/user_config.h`, `main/main.cpp`,
극성은 `components/lcd_bl_pwm_bsp/lcd_bl_pwm_bsp.{c,h}`,
입력은 `components/button_bsp/button_bsp.c`를 근거로 한다.
이 파일들의 hash는 아래 source index에 있다. 본 표는 이전 후보의 구현 해법을 제공하지 않는다.

## 설정·API 확인

제조사 `09_FactoryProgram/sdkconfig.defaults`에는 esp32s3·Flash 16MB·
SPIRAM=y·Octal·80MHz 설정이 있고, RGB framebuffer는 PSRAM을 사용한다.
RGB565 한 frame은 320×820×2=524,800 bytes다. PSRAM 초기화·할당·framebuffer 위치와
실제 빌드의 sdkconfig를 확인하고 메모리 예산을 남긴다.
LCD timing·초기 명령·ST7701 panel API 지원은 제공 제조사 source와 ESP-IDF v5.3.2에서 확인한다.
지원되지 않는 panel 동작 호출을 성공으로 가정하지 않는다.
BOOT를 누른 채 reset하면 ROM 다운로드 모드에 들어갈 수 있다. 정상 부팅 뒤 입력을 시험한다.
RTC 시각 설정·backup 전원, 배터리 ADC 실패/null, TF 미장착 동작은 선택 기능의 시험에 포함한다.

## 제조사 source 범위

[고정 source index](vendor-source-index.json)의 source_root·파일 목록·SHA-256만 참조한다.
운영자가 실제 파일/hash를 확인해 동일하게 제공한다. index만으로 설치·검증 완료를 주장하지 않는다.
Demo ZIP SHA-256: `E5914BB732F47EB6A3D76856F707253EE6008847E6675011796180943683C3DE`.
기본 source_root는 `C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16/source/ESP32-S3-LCD-3.16-Demo/ESP-IDF`다.
SDK root는 `C:/Espressif/v5.3.2/esp-idf`이며 toolchain은 운영자가 준비한다.

제조사 source·header·설정만 허용한다. vendor build·backup·운영자 제품 프로젝트·
다른 후보의 source/patch를 읽거나 완성 BSP로 가져오지 않는다.
이전 제조사 데모의 성공은 이번 candidate 제품의 LCD/입력/IMU 합격 증거가 아니다.
