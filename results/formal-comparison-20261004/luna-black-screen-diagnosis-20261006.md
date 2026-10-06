# Luna 최초 검은 LCD 화면 원인 분석 — 2026-10-06

COM3의 원본 Luna 펌웨어에서 정상 부팅·PSRAM 검사·LCD 초기화 함수 완료·USB 수신 준비와 공통 frame0의 실제 수락을 확인했다. 사용자도 진단 리셋 이후 **계속 검은 화면**이라고 확인했다. 실패 경계는 LCD 표시 경로로 좁혀졌으며, 초기화 순서와 회전/물리 timing에서 두 코드 결함을 찾았다. 수정 펌웨어의 실물 비교를 수행하지 않았으므로 두 결함 중 어느 것이 단독으로 화면을 막는지까지 확정하지 않는다.

대상은 `20261006-codex-cli-gpt-6-luna-r01`, commit `c0d5d61160664923e0494302fae180089d02d247`이다. App SHA-256은 `3af7fd933b743ea7b16ba02627617e3adb3be0d5273eb9deb184f1be9c9d51d6`, 원본 ELF SHA-256은 `5a5fd3f3ad5bcb701bd1bfb421fa9b94ebbb11de1fd51a60525ca6500d3ca573`이다. [진단 결과 원본](evidence/20261006-codex-cli-gpt-6-luna-r01/diagnosis-20261006/diagnostic-findings.json)과 [source/ELF 결합 검토](evidence/20261006-codex-cli-gpt-6-luna-r01/diagnosis-20261006/source-review.json)에 확인 범위를 기록했다.

## 1. 확인한 실패 경계

| 검사 | 결과 | 판정 범위 |
|---|---|---|
| COM3 식별 | USB VID303A/PID1001·MAC `28:84:85:B0:85:18` | 21:03 재업로드와 같은 장치 |
| 리셋 없는15초 읽기·ROM 동기화 | 0 bytes·ROM probe exit2 | 이것만으로 앱 정지나 다운로드 모드를 판정할 수 없음 |
| 21:22:24 KST native hard reset부터20초 capture | 5,859 bytes, SPI_FAST_FLASH_BOOT·8MB PSRAM memory test OK | 기존 app의 실제 정상 부팅 확인 |
| LCD/USB 경계 | `meter_lcd` 초기화 완료와 `USB Serial/JTAG receiver ready` | LCD 초기화 오류 반환·초기 버퍼 할당 실패는 이 부팅에서 관측되지 않음. 로그 성공은 실제 LCD 표시 성공과 다름 |
| 첫 진단 공통 frame0 | 생산 수신기의 `accepted cdm/1 frame sequence=0` | frame0의 실제 수락 확인. 값 표시·frame1·지연 합격까지 뜻하지 않음 |
| 리셋 후 실물 보고 | 사용자의 “계속 검은 화면” | 새 사진/영상·BOOT·30초 유지 사실은 없음 |

[부팅 raw](evidence/20261006-codex-cli-gpt-6-luna-r01/diagnosis-20261006/hard-reset-serial.bin), [리셋/시각 기록](evidence/20261006-codex-cli-gpt-6-luna-r01/diagnosis-20261006/hard-reset-capture.json), [수락 raw](evidence/20261006-codex-cli-gpt-6-luna-r01/diagnosis-20261006/post-reset-reference-capture/device-serial.bin), [사용자 보고](evidence/20261006-codex-cli-gpt-6-luna-r01/diagnosis-20261006/user-after-diagnostic-reset.json)를 구분해 보존한다. Boot ELF 식별 문자열 `5a5fd3f3a...`는 원본 ELF와 일치한다. App version `d9579af`는 빌드 당시 입력 commit 문자열이며 최종 source 동결 commit을 대체하지 않는다.

## 2. 가장 유력한 원인: 설정 이후 LCD를 다시 리셋

[후보 board_lcd.c](evidence/20261006-codex-cli-gpt-6-luna-r01/diagnosis-20261006/source-evidence/candidate/main/board_lcd.c)의407~417행은 `enable_io_multiplex=1`, RESET=GPIO16으로 panel을 생성한 뒤 `esp_lcd_panel_reset()`과 `esp_lcd_panel_init()`을 호출한다. 실제 결합된 [제조사 드라이버](evidence/20261006-codex-cli-gpt-6-luna-r01/diagnosis-20261006/source-evidence/vendor/09_FactoryProgram/managed_components/espressif__esp_lcd_st7701/esp_lcd_st7701_rgb.c)의 동작은 다음과 같다.

1. Multiplex 생성자에서 LCD를 리셋하고 제조사 초기 명령·Sleep Out·Display On을 전송한다.
2. 제어 SPI IO를 삭제하고 `io=NULL`로 바꾼다.
3. 후보가 호출한 panel reset은 GPIO16을 다시 낮췄다 올리는 **물리 LCD 리셋**을 실행한다.
4. Multiplex panel init은 제조사 명령 재전송을 생략하고 RGB 주변장치만 초기화한다.

따라서 화면을 켠 설정 뒤 LCD가 기본 상태로 돌아가며, 이후 제어 명령으로 복구하는 경로가 없다. 하드웨어 리셋이 화면을 blank 처리하고 기본 상태로 복귀시키는 동작은 [Sitronix ST7701S v1.4 §7.5.5,54~55쪽](https://files.waveshare.com/wiki/common/ST7701S_SPEC_V1.4.pdf#page=54)에 근거한다. 이 명세와 실제 호출 흐름을 연결한 원인 추론이다. LCD RESET 파형이나 panel register를 직접 측정한 것은 아니다.

제조사 main.cpp의 주석은 multiplex에서 RGB만 리셋한다고 설명하지만 실제 제공 드라이버는 RESET GPIO가 있으면 LCD도 리셋한다. 원본 ELF의 [reset 함수 disassembly](evidence/20261006-codex-cli-gpt-6-luna-r01/diagnosis-20261006/elf-panel_st7701_reset.txt)에서도 두 `gpio_set_level` 호출을 확인했다. [build binding](evidence/20261006-codex-cli-gpt-6-luna-r01/diagnosis-20261006/vendor-build-binding.txt)은 해당 제조사 파일이 원본 빌드에 쓰였음을 연결한다. 제조사 예제는 multiplex=0이므로 초기 명령을 reset 이후 init에서 보내는 다른 경로를 사용한다.

## 3. 함께 확인한 결함: 가로 화면과 물리 RGB timing의 혼동

같은 후보는 화면 크기820×320을 `rgb.timings.h_res/v_res`에도 사용하고 `MADCTL=0x20`의 D5를 MV라고 가정한다. 제공 제조사 예제의 물리 RGB timing은320×820이다. [ST7701S v1.4 §12.2.27,214쪽](https://files.waveshare.com/wiki/common/ST7701S_SPEC_V1.4.pdf#page=214)은 MADCTL의 ML/D4와 BGR/D3만 정의하며 D5의 축 교환 기능을 정의하지 않는다. SDK 공통 command header도 bit 위치가 제조사별로 다르므로 panel datasheet를 확인하라고 경고한다.

따라서 `0x20`만으로 물리 scan을820×320으로 바꾼다는 후보 설명은 근거가 없다. 논리 가로 렌더링과 물리320×820 scan을 구분해 검증해야 한다. 이 결함의 독립적인 화면 증상은 아직 측정하지 않았으며, 두 결함을 함께 수정해 성공하더라도 각각의 원인 기여를 분리한 시험은 아니다.

## 4. USB 관측의 남은 한계

첫 [진단 capture](evidence/20261006-codex-cli-gpt-6-luna-r01/diagnosis-20261006/post-reset-reference-capture/capture.json)는 frame0을1,543 bytes 쓰고 수락 로그65 bytes를 받았지만, frame1은 Write timeout으로 종료했다. 후보 수락 문구가 공통 도구의 기본 `CDM_RX` marker와 다르므로 capture.json의 `accepted_at_seconds=null`을 그대로 보존하고 raw와 생산 `finish_line()` 경로를 검토해 frame0 수락만 판정했다.

이어 [같은 포트에서 리셋 후 재시험](evidence/20261006-codex-cli-gpt-6-luna-r01/diagnosis-20261006/reset-and-frames-session.json)했다.2초 부팅 대기·각 frame1초 읽기 조건에서 두 host write는 완료됐지만 수락/거부 로그는 없었다. [두 번째 raw](evidence/20261006-codex-cli-gpt-6-luna-r01/diagnosis-20261006/reset-and-frames-capture/device-serial.bin)는 부팅/준비 로그만 포함한다. 이 재시험은 원래 공통 평가의5초 읽기와 다른 진단 조건이며 성공한 공통 평가로 대체하지 않는다.

이전0-byte capture의 이유·간헐 전송 실패·frame1 수락은 미확인이다. UART0 primary와 USB Serial/JTAG secondary가 함께 설정되어 있고 이번에 USB 부팅/수락 로그가 실제 확인됐으므로 “UART primary여서 COM3 로그가 없다”는 단일 설명은 성립하지 않는다. 누락 fixture만으로 검은 화면을 설명하기도 어렵다. 원본 `board_lcd_present()`는 수신 전에도 WAITING 화면을 그린다.

## 5. 다음 검증과 실험 기록의 범위

진단은 원인 후보와 실패 경계를 기록하는 범위에서 완료했다. 실제 수정 성공을 확인하려면 별도로 식별한 펌웨어에서 초기화 뒤 물리 reset 문제를 한 번에 한 원인씩 검증하고, 물리 timing/논리 회전도 따로 검증해야 한다. 같은 fixture의 두 수락·58/82 표시·세 페이지·BOOT 순환·30초 유지까지 확인해야 정상 동작을 판정할 수 있다.

진단 중 firmware source 수정·rebuild·flash write·후보 호출은0회다. Native hard reset은2회이며 각 시각과 stimulus를 별도 기록했다. 마지막 보드는 같은 Luna 최초 펌웨어에 두 공통 frame의 host write만 끝난 상태이고 실제 수락은 미확인이다. Serial은 닫았다.

[기존 최초 RM](evidence/20261006-codex-cli-gpt-6-luna-r01/evaluation-20261006/reference-review.json)의 RM1/2 partial·RM3 fail·RM4/5 not_run, reference fail·product_pass false와 policy invalid를 보존했다. 이번 frame0 수락과 부팅 확인은 **날짜 있는 추가 진단**이며 당시0-byte 원본 판정에 소급하지 않는다. 후보12회·정규화44,103,444 token·series 종료3/15·Luna 후속0회/잔여7,200초·3회도 그대로다.

[운영 계약5절](../../docs/experiments/comparison-operating-contract.md#5-첫-결과-보존과-후속-피드백)에 따라 정식 후속에는 자기 직전 결과·고정 요구·실제 관측과 근거·예산을 제공한다. 이 보고서의 수정 방향이나 운영자 patch를 중립 관측으로 후보에게 넘기면 구현 개입이 되므로 구분해야 한다. 본 진단에서 후보에게 메시지나 파일을 전달하지 않았다. 재개 상태는 [준비 상태](../../docs/experiments/next-comparison-readiness.md), 작업 완료 조건은 [진단 계획](../../docs/plans/2026-10-06-codex-luna-black-screen-diagnosis.md), raw 보존은 [진단 목록](evidence/20261006-codex-cli-gpt-6-luna-r01/diagnosis-20261006/snapshot-inventory.json)을 따른다.
