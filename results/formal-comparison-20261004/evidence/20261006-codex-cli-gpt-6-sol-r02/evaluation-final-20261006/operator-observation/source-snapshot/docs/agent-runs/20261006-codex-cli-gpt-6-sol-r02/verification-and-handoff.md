# Followup 검증과 실물 인계

이번 source는 `pc/desk_meter.py`의 두 global reset에서 source age가 300초 이상일 때 `stale=true`만 설정한다. 원본 `error_code=null`은 그대로 남는다. `tests/test_pipeline.py`는 이 collector로 만든 seq0/1 frame이 제공된 `.benchmark-inputs/feedback-evidence/003-sent-frames.jsonl`과 바이트 단위로 같은지 확인하고, 같은 생산 C receiver 모듈을 링크한 host CLI에 전달한다.

`main/board.c`의 ST7701 3-wire SPI 초기화는 이제 명령과 각 parameter 바이트마다 D/C 비트와 CS 펄스를 전송한다. 제조사 `09_FactoryProgram`의 3-wire SPI 구현도 바이트마다 package를 전송한다. 이전 코드는 parameter 묶음에 D/C 비트 하나만 보냈다. 이 차이가 이전 사진의 무문자 화면 원인일 가능성이 높지만 수정 firmware의 실물 화면은 아직 측정되지 않았다. `main/main.c`는 BOOT로 페이지가 바뀔 때 `BOOT page=1/2/0`을 기록한다.

## 재현 명령과 자체 관측

checkout에서 명령을 각각 독립 실행한다. `idf.py --version`은 ESP-IDF v5.3.2, `idf.py set-target esp32s3`와 `idf.py build`는 성공했고 최종 `build/codex_desk_meter.bin` 크기는 0x4bb50 bytes였다. `python -m unittest discover -s tests -v`와 `python tests/test_pc.py`는 각각 6/6 통과했다. `cmake -S host -B build-host -G Ninja`, `cmake --build build-host`, `ctest --test-dir build-host --output-on-failure`는 최종 3/3 통과했다. CTest의 두 번째 항목은 실제 `main/receiver.c`를 compile/link한 CLI에 Python collector frame을 공급한다. 최초 CTest는 오래된 feedback 파일명, 다음 실행은 seq1의 `sent_at` 불일치 때문에 실패했고 둘 다 시험 코드를 고친 뒤 최종 통과했다. 빌드와 시험 성공은 실물 LCD 판정이 아니다.

추가 정적 점검 명령: `python -m py_compile pc/desk_meter.py`, `python -m py_compile tests/test_pipeline.py`. `git diff`와 `git status --short`로 변경을 확인한다.

## 운영자 실물 절차

1. 이 checkout의 동결 artifact `build/bootloader/bootloader.bin`, `build/partition_table/partition-table.bin`, `build/codex_desk_meter.bin`을 기록하고, 운영자가 선택한 포트로 `idf.py -p PORT flash`를 실행한다. `PORT`는 운영자가 실제 COM 이름으로 대체한다. 후보는 serial 열기·flash·reset을 수행하지 않았다.
2. 정상 부팅 뒤 화면을 가로로 놓고 30초 연속 촬영한다. 최초 `WAITING FOR PC FIXTURE`와 제목·상태 글자가 읽혀야 한다. 어두운 패널과 색 띠만 보이면 LCD 실패로 남긴다.
3. receiver state가 비어 있는 새 artifact임을 확인한 경우에만, 선택한 포트에서 `python pc/desk_meter.py --port PORT --alias desk-meter --state sender-state.json --receiver-empty --fixture personal-usage.json --log sender-receipts.jsonl`을 실행한다. 초기화 후에는 같은 state 파일을 보존하고 `--receiver-empty`를 빼고 재실행한다. 한 포트에서 sender와 monitor를 동시에 열지 않는다.
4. 송신 raw frame과 receiver serial log의 `frame accepted seq=...`를 따로 저장한다. host write receipt는 device ACK가 아니다. 수신 후 2초 안에 usage 화면에 58%/82% 남음과 SOURCE STALE, 원본 관측 시각을 확인한다. `codex-resets.com` 화면에서는 출처·조회 시각·최근 reset과 경과 시간이 보여야 한다.
5. 정상 부팅 후 BOOT를 짧게 세 번 눌러 dashboard → global reset → status → dashboard 순환과 serial log의 `BOOT page=1/2/0`을 확인한다. 각 전환은 debounce 후 300ms 이내여야 한다. RST는 시스템 reset 전용이며 BOOT를 누른 채 RST를 누르는 것은 이 시험이 아니다.
6. USB 연결 상태에서 60초 자동 갱신, PC 수동 재실행 뒤 새 sequence, USB 단절·복구, 300초 receive stale, 오류 frame 뒤 last-good 유지·정상 frame 복구를 각 raw bytes·시각·사진/영상으로 남긴다. 고정 fixture의 오래된 observed_at은 새 frame만으로 fresh가 되면 안 된다.

기존 r01 관측은 seq0/1 receiver 수락과 무문자 화면·버튼 무반응 보고까지만 입증한다. r02의 화면, BOOT, 30초 연속성, 시간 한계, 전체 collector→device 경로는 아직 실물 미측정이다. 운영자는 r02 source를 수정하지 않고 artifact와 관측 파일로 판정한다.

## 명령 정책 이탈 기록

이번 실행의 읽기 명령 중 ESP-IDF RGB driver·제조사 SPI source·validator·PC CLI를 발췌하면서 `Get-Content ... | Select-Object ...` PowerShell 파이프를 사용했다. 공통 과제의 셸 파이프 금지 규칙을 위반했다. 외부 파일을 변경하거나 권한 거부를 우회하지는 않았으며, 이 규칙의 준수 성공으로 보고하지 않는다.
