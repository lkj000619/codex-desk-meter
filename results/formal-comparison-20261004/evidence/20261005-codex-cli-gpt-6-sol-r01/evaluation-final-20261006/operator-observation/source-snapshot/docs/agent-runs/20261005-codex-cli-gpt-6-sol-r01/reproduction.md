# 재현 및 실물 관측

## 빌드와 자체 시험

checkout 루트에서 준비된 ESP-IDF v5.3.2 환경을 사용한다. 각 줄은 개별 명령이다.

```text
idf.py --version
idf.py set-target esp32s3
idf.py build
python -m py_compile pc/desk_meter.py
python -m unittest discover -s tests -v
cmake -S host -B build-host -G Ninja
cmake --build build-host
ctest --test-dir build-host --output-on-failure
```

`build/codex_desk_meter.bin`, `build/bootloader/bootloader.bin`, `build/partition_table/partition-table.bin`이 업로드 artifact다. host CMake는 `main/receiver.c`와 선언된 ESP-IDF SDK의 `cJSON.c`를 직접 compile/link한다. Python→C pipeline 시험은 `pc/desk_meter.py`의 실제 serializer가 만든 frame을 host `receiver_cli`에 전달한다. 이 시험은 USB·LCD 실물 성공을 입증하지 않는다.

## PC fixture 사용

기본 collector는 `experiments/fixtures/providers/multi-provider-healthy.json`의 provider 세 개와 `codex-resets-history.json`을 사용한다. `--fixture providers/...json`을 반복하면 독립 소스를 지정한다. `--preview`는 serial port를 열지 않고 payload를 출력한다. 실시간 전송에서는 오래된 fixture의 `observed_at`을 보존하고 status를 stale로 표시한다. 조회 시각을 현재 시각으로 덮지 않는다. `codex-reset-forecast.json`은 화면에 보내지 않는다.

sender state는 alias와 마지막 **예약** 순번을 원자적으로 저장한다. 새 state는 receiver가 비어 있음을 확인한 경우에만 `--receiver-empty`로 초기화한다. 이미 state가 있으면 그 옵션을 주어도 순번을 재설정하지 않는다. state가 유실되거나 손상되면 전송을 중지한다. COM 재연결은 초당 최대 1번 시도한다. write receipt에는 ACK가 없음을 명시하고 raw frame hex를 남긴다.

운영자 명령 예시 (실제 포트/경로로 바꾼다):

```text
python pc/desk_meter.py --preview
python pc/desk_meter.py --port COMx --alias meter-01 --state sender-state.json --receiver-empty --log transport.jsonl
python pc/desk_meter.py --port COMx --alias meter-01 --state sender-state.json --manual --log transport.jsonl
```

자동 주기는 기본 60초다. 두 번째 PC 명령은 1회 재수집·전송하고 종료한다. BOOT는 화면 전환이고 PC 수동 갱신 요청이 아니다. serial은 115200 baud, 8N1, flow control 없음, DTR/RTS 비활성이다. 같은 device에 sender 한 개만 실행한다.

## 운영자 업로드·실물 시험

이번 실행에서는 포트 open, flash, reset, `erase_flash`를 하지 않았다. 운영자는 위 세 build artifact를 동결해 hash를 기록하고 보드를 식별한 뒤 업로드한다. 예시 업로드 명령은 `idf.py -p COMx flash`다. 전체 flash 삭제는 필요하지 않다. 부팅 후 USB Serial/JTAG 포트를 확인하고 sender를 단독 실행한다.

1. 정상 부팅 뒤 화면이 30초 이상 켜지고 820×320 가로 콘텐츠가 잘리지 않는지, USB를 뺀 상태에서 세 화면이 유지되는지 관측한다. BOOT를 짧게 누른 뒤 300ms 이내에 dashboard→global reset→status→dashboard를 순환해야 한다. RST는 시스템 reset으로만 취급한다. BOOT를 누른 채 reset하여 ROM 다운로드 모드로 들어간 경우는 입력 시험이 아니다.
2. receiver가 비었음을 확인한 뒤 sender state를 처음 만들고 fixture를 전송한다. 수신 로그의 `accepted seq`, frame raw bytes, 화면의 provider/window 값·source `codex-resets.com`·captured_at·last_reset_at·elapsed를 기록한다. host receipt만으로 수신을 판정하지 않는다. 수신 후 2초 안에 LCD가 바뀌는지 영상으로 확인한다.
3. 같은 receiver에 7이 수락된 상태에서 PC 프로세스를 재시작해 1을 보냈을 때 `SEQUENCE_OLD` 거부, 영속 state의 8은 수락하는지 확인한다. 사전 상태가 다른 경우 동일 논리를 해당 순번으로 시험한다. board reset으로 sender 복구를 대신하지 않는다.
4. PC가 frame CRC·pretty/CRLF·UTF-8·버전·길이 오류를 주입하면 receiver가 `rejected`를 남기고 마지막 정상 화면을 유지해야 한다. 제공 host C 시험은 해당 로직의 일부를 검증하며, 실물 주입은 별도 operator 도구와 raw bytes를 기록한다.
5. USB를 끊으면 receive-age 300초부터 stale가 되고 화면은 유지되어야 한다. fixture 자체가 오래되면 새 frame이 와도 source-age stale가 사라지지 않아야 한다. 재연결 뒤 다음 주기 60초 이내에 새 순번을 받고 화면이 복귀하는지 관측한다. DNS/TLS/HTTP/JSON 오류 fixture를 순차 입력해 source 오류와 last-good 보존도 확인한다.
6. 60초 데이터 미수신 후 백라이트가 감광되고 새 정상 frame 뒤 복귀하는지 확인한다. 화면 자체는 계속 켜져 있어야 한다. 전원 분리 상태의 USB 단절/복구는 별도 관측한다.

## 확인된 한계

실물 LCD 초기화, GPIO0 공유 BOOT 동작, USB 수신 시간, 감광 밝기, 가로 물리 방향은 여기서 관측하지 않았다. C receiver는 `sent_at`을 PC가 제공한 UTC 기준으로 source-age와 global elapsed를 계산한다. PC 시계가 틀리면 표시도 틀릴 수 있다. 5×7 ASCII bitmap font는 비 ASCII provider label을 `?`로 표시한다. dashboard는 provider/window 세 행씩 5초마다 자동 넘김하므로 다수 항목의 누락 여부와 작은 글자 가독성은 실물 시험에서 확인해야 한다. `product_pass`는 운영자 판정 전까지 false다.
