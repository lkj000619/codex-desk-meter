# 구현·재현·실물 관측 절차

## 재현 환경과 명령

ESP-IDF v5.3.2, Python, C/C++ compiler, CMake, Ninja가 미리 준비된 환경에서 checkout 루트에서 각 명령을 따로 실행한다. 이 실행은 제품 fixture만 사용했고 provider 계정이나 네트워크를 사용하지 않았다.

```powershell
idf.py --version
idf.py set-target esp32s3
idf.py build
python -m unittest discover -s tests -v
python tests/test_pc_pipeline.py
python tests/test_legacy_adapter.py
python tests/test_production_receiver.py
python -m py_compile pc/pipeline.py
python -m py_compile pc/collector.py
python -m py_compile pc/gui.py
python -m py_compile pc/sender.py
python -m py_compile pc/serial_sender.py
python -m py_compile pc/legacy_adapter.py
python -m py_compile tests/test_pc_pipeline.py tests/test_legacy_adapter.py tests/test_production_receiver.py
cmake -S tests/host -B build-host -G Ninja
cmake --build build-host
ctest --test-dir build-host --output-on-failure
python scripts/validate-end-to-end-result.py --result results/20261006-codex-cli-gpt-6-luna-r02/end-to-end-result.json --manifest .benchmark-inputs/e2e-evaluation-manifest.json --evidence-root . --matrix experiments/fixtures/provider-fixture-matrix.json
```

`tests/test_production_receiver.py`는 `components/meter_core/meter_core.c`를 빌드한 `build-host/meter_receiver_cli`를 stdin/stdout seam으로 호출한다. 고정 common seq0/seq1을 실제 C parser/state machine이 수락하고, 29개 wire/schema 입력의 수락·거절 결과와 last-good 보존을 확인한다. Python collector 시험은 고정 reference time으로 58%·82% remaining 및 stale 출처 의미를 확인하고 reference frame 두 개와 바이트 단위 비교한다. 이는 host 검증이며 USB 장치 수신이나 LCD 표시를 증명하지 않는다.

## 오류·stale·복구 시험

- `tests/test_pc_pipeline.py`: 0/299/300초 stale 경계, 300초 이상인 available 데이터 거절, provider/window별 정규화, 잘못된 percent 및 중복 window, 미래 시각, adapter 실패에서 last-good 유지와 정상 수집 재개, 고정 common payload 및 sequence 0/1.
- `tests/test_legacy_adapter.py`: fixture 정상→오류의 stale/last-good 보존, 정상 복구, 두 global source 분리.
- `tests/test_production_receiver.py`: CRC 오류와 중복 순번을 거절하고 직전 good frame을 유지, 이후 다음 순번을 수락, common seq0/seq1 및 29 입력 사례.
- `ctest --test-dir build-host --output-on-failure`: production C parser, receiver state, 선택 idle-dim 정책 세 시험.
- provider validity 전부는 `experiments/fixtures/provider-fixture-matrix.json`과 위 validator 명령으로 함께 검사한다. 사용 가능하지만 300초 이상 된 값을 stale로 바꿔 조용히 수락하지 않고 invalid로 보고한다.

## 운영자 실물 업로드와 관측

실행 중에는 COM port를 열지 않았고 flash, reset, `erase_flash`를 하지 않았다. 다음 절차는 운영자가 artifact를 동결한 뒤 수행한다.

1. COM3가 보드의 USB Serial/JTAG인지 확인하고 BOOT을 누르지 않은 정상 부팅을 준비한다. 후보 실행이 생성한 `build/codex_desk_meter.bin`을 업로드한다. 설정·partition을 다시 초기화하거나 전체 flash 삭제는 하지 않는다.

   app image SHA-256: `8861E741F3ACDB3C511B399F2E92B96F70904F7000FAF01B43266016ECEA9FD5`.

   LCD CS와 공유하는 BOOT GPIO0은 `board_lcd_init`이 ST7701 SPI 초기화 뒤 input/pull-up으로 돌린다. 버튼 반응은 운영자가 보드에서 확인한다.

   ```powershell
   idf.py -p COM3 flash
   idf.py -p COM3 monitor
   ```

   로그에서 정상 부팅, PSRAM 초기화, LCD 초기화, `boot screen submitted before USB receiver setup`, `USB Serial/JTAG receiver ready`를 기록한다. monitor를 종료한 후에 sender를 시작해 COM3를 동시에 열지 않는다.

2. 갱신 때까지 BOOT을 누르지 않고 화면이 켜져 있는지 확인한다. 새 firmware를 막 올린 뒤 첫 전송에 한해 sender state가 비어 있고 receiver가 새 부팅으로 비어 있는 것을 확인한 다음 고유하고 이후 계속 쓸 alias를 사용한다. 이후에는 alias의 sender state를 보존하고 `--initialize-empty-receiver`를 다시 쓰지 않는다.

   ```powershell
   python -m pc.serial_sender --port COM3 --device-alias waveshare-lcd-316-r02 --profile common --reference-time 2026-09-30T18:40:49Z --sent-at 2026-09-30T18:40:49Z --initialize-empty-receiver --device-log results/20261006-codex-cli-gpt-6-luna-r02/device-serial.log
   python -m pc.serial_sender --port COM3 --device-alias waveshare-lcd-316-r02 --profile common --reference-time 2026-09-30T18:40:49Z --sent-at 2026-09-30T18:40:54Z --device-log results/20261006-codex-cli-gpt-6-luna-r02/device-serial.log
   ```

   각 실행은 raw host frame을 저장하고 ESP_LOG를 최대 2초 캡처한다. `accepted cdm/1 frame sequence=0` 및 sequence 1 로그는 firmware 수신 진단이며 protocol ACK가 아니다. 로그가 없거나 reject 로그라면 host의 `written` receipt를 수신 확인으로 간주하지 말고 원시 device log와 frame을 함께 보관한다.

3. 각 frame 뒤 2초 이내 LCD에서 openai 출처, five-hour remaining 58%, weekly remaining 82%, source stale 표시 및 원본 reset 시각/null을 확인한다. provider가 보내지 않은 추가 quota나 reset time이 나타나지 않는지도 확인한다. BOOT을 눌러 dashboard → global reset → status/errors 순환과 돌아오는 동작을 확인한다. RST는 reset 기능으로만 취급하며 BOOT을 누른 채 reset하지 않는다.

4. 정상 부팅부터 광학적으로 30초 이상 화면이 켜져 있는지 타이머와 영상/사진으로 기록한다. 전원이 유지되는 상태에서 USB data link를 분리했다 다시 연결해 accepted last-good 유지, receive-age stale 전환, 새 순번 수락 뒤 복구를 기록한다. USB 분리 중 전원이 유지되지 않으면 그 제약을 기록하고 연속성 시험을 미측정으로 남긴다.

5. flash 직후 BOOT 한 번, 각 화면, 수동 PC 갱신, automatic refresh, 오류/stale 후 복구, reset button과 30초 continuity 기록을 분리한다. 각 관측에는 artifact SHA-256, 실제 COM alias, frame sequence, raw host frame, device log, 관측 시각과 사진/영상을 남긴다.

## 남은 확인 사항

- r01 검증에서 첫 재업로드 뒤 LCD가 검었다는 보고가 있다. 별도 진단 부팅은 정상 boot/PSRAM/LCD-init/receiver-ready 로그를 남겼지만 30초 광학 관측은 없고, 이후 캡처에도 common seq0/seq1 모두의 firmware acceptance log는 없다. 이 수정의 LCD 출력, frame→LCD 2초 조건, BOOT 화면 순환 및 30초 연속성은 미확인이다.
- sender는 device ESP_LOG를 diagnostics로 캡처할 뿐 ACK protocol을 만들지 않는다. host frame write가 성공해도 firmware 수락은 해당 로그와 화면으로 확인해야 한다.
- source-age, receive-age와 BOOT의 실물 버튼 동작은 단조 시계 및 카메라로 운영자가 측정해야 한다. RTC/배터리/IMU 선택 기능은 구현하지 않았다.
- 공통 run 규칙을 지키지 못한 read-only 파이프 시도가 두 번 있었다. 첫 파일 목록 조회에서 PowerShell 파이프를 썼고, `rg`가 설치되지 않은 것을 확인하기 전 `rg --files | rg ...` 검색을 시도했으나 실패했다. 그 뒤에는 파이프·복합 명령을 쓰지 않았고 검색은 PowerShell direct file search로 진행했다. device access는 하지 않았다.

## 결과 경계

`end-to-end-result.json`은 schema 상태와 증거 파일만 기록한다. product_pass는 false이고 hardware/optical/USB sender-to-board acceptance/GUI rubric은 운영자 판단 전이다. 실행 시간과 token 사용량도 측정되지 않았다.
