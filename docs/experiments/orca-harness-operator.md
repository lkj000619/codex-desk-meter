# 별도 Orca 협업 구현 실행·관측

**2026-10-10 16:46 KST 현재:** 이전 반복 점멸은 사용자 직접 관측으로 해결 확인. 숫자 후보 source `7d20952`/build 및 Luna의 독립 검사·scoped host PASS 보고서 작성은 완료했지만 최종 `worker_done` 수락은 대기다. [새 후보](../../experiments/orca-harness-20261008/operator/firmware-numeric-candidate.json)의 upload gate는 false, 보드는 08:48 점멸 수정본이다. sole COM3 watch `term_5ef7b2be-8121-4f9b-be51-bbaadae18bfa`와 state/세션을 보존한다. 제출 수락·동결 전 추가 writer/flash는 실행하지 않는다. 아래 관측 대기는 각 시점 당시 상태다.

2026-10-10 관측 보완: 이전 점멸 수정본의 [영상/사용자 응답](../../experiments/orca-harness-20261008/operator/post-flicker-observation-20261010.json)을 기록했다. WAITING은 수동 RST, 화면 탐색은 BOOT였다. 현재60초 watch/state/세션은 유지한다. 다음 후보는 [숫자 잘림 보완](../plans/2026-10-10-lcd-numeric-readability.md)이며 Sol build·Luna 검증·동결 후에만 기존 sole writer의 정상 종료를 확인하고 업로드한다. 남은 점멸 직접 관측 답변과 숫자 수정 전/후 실물 자료를 각각 보존한다.

2026-10-10 15:52 KST 재개: 현재 COM3의 유일한 PC watch는 **`term_5ef7b2be-8121-4f9b-be51-bbaadae18bfa`**다. 기존 세션 선택/state로 seq46부터 전송을 복구했으며 새 flash/reset/init는 하지 않았다. [실행 근거](../../experiments/orca-harness-20261008/operator/live-watch-resume-20261010.json). 예전 terminal/PID는 현재 실행 근거가 아니다. 먼저 현재 watch와 OS 프로세스를 확인하고 같은 포트에 send/monitor를 중복 실행하지 않는다. 다음은 수정 후 RESET 없는 30초·CRC·BOOT 관측이다.

2026-10-10 08:49 KST: **점멸 수정본은 08:48에 COM3 업로드 완료**. [현재 수정 후보](../../experiments/orca-harness-20261008/operator/firmware-flicker-candidate.json), [쓰기 검증](../../experiments/orca-harness-20261008/operator/flash-lcd-flicker-20261010.json). 원래 watch의 정상 종료·프로세스 종료를 확인하고 **`term_dcac760e-42fa-42f9-afa6-1da904d96d49`**에서 같은 세션/state로 seq40부터 60초 watch를 재개했다. 현재 단계는 RESET 없는 30초 점멸/CRC/BOOT 관측이며 재업로드·sender 초기화를 반복하지 않는다. 아래 최초 운영 기록은 당시 근거다.

이 문서는 coordinator와 사용자가 실행할 절차다. 현재 gate는
[준비 상태](next-comparison-readiness.md)에서 확인한다. 2026-10-10 host 검증 후 `7ccbb24` 후보를
08:01 COM3에 업로드했다. 사용자의 밝은 Usage/WAITING 확인 후 sender state를 처음 생성했고,
08:08 fixture·08:09 실데이터 전송을 완료했다. 08:10부터 60초 watch가 COM3를 소유한다.
**현재 init-device를 다시 실행하거나 별도 send/serial monitor를 동시에 열지 않는다.**
초기 영상의 검은 화면은 사용자가 직접 RST를 눌렀다고 확인했다. 후속 실데이터 영상에서 숫자와
FRAME/CRC VALID를 확인했으나 반복 점멸이 보고되어 firmware 보완 중이다. 새 업로드는 보완된
source/build·독립 검증 뒤 기존 watch 종료를 확인하고 수행한다. BOOT·무점멸/30초 관측은
아직 합격하지 않았다. 이후 상태는 [결과](orca-harness-results.md)와 [재개](orca-harness-resume.md)가 소유한다.

## 업로드 전

1. 최신 PC 제출 수락·시험, Luna 독립 통합 검증·결함 처리를 완료한다.
2. [현재 수정 후보 목록](../../experiments/orca-harness-20261008/operator/firmware-flicker-candidate.json)의
   source commit·15개 source hash·app/boot/partition hash를 현재 파일과 비교한다.
   이 목록의 `upload_permitted=false`이면 업로드하지 않는다. 수정본은 이미 업로드되어 현재 false다. [원래 후보](../../experiments/orca-harness-20261008/operator/firmware-candidate.json)와 최초 업로드는 보존된 과거 근거다.
3. 현재 포트를 다시 열거하여 COM3의 Espressif USB VID `303A`/PID `1001`과 대상 보드를
   확인한다. 예전 연결 기록만으로 포트를 선택하지 않는다.
4. [Sol 보고](../agent-runs/orca-sol/report.md)의 **날짜별 수정 산출물**을 업로드한다.
   현재 후보 app은 `lcd-flicker-build/`의 SHA-256
   `953782e5486adbe9743e5b753e716892cfdfbeef25d23b1702dc1d6050078f1f`이다.
   `final-build/`에는 보존된 이전 제출이 있으므로 해당 app을 선택하지 않는다.
5. flash 명령·파일 hash·대상 포트·시간·부팅 로그를 남긴다. 자동 rebuild가 실행됐다면
   새 source/hash를 다시 검증한다. 완전 erase나 BOOT를 누른 채 reset은 필요하지 않다.

위 gate를 통과한 뒤 사용할 명령은 아래와 같다. 설치된 `esptool` 4.12.0의 help와
후보 manifest의 주소·설정으로 확인했다. 2026-10-10 08:01 실제 실행·hash 검증 기록이 있다.
`python`은 아래 PC 절차의 ESP-IDF Python 환경이다. 현재 대상이 COM3임을 다시 확인한다.

```powershell
python -m esptool --chip esp32s3 --port COM3 --baud 460800 --before default_reset --after hard_reset write_flash --flash_mode dio --flash_freq 80m --flash_size 16MB 0x0 firmware/.host-tools/lcd-flicker-build/bootloader.bin 0x8000 firmware/.host-tools/lcd-flicker-build/partition-table.bin 0x10000 firmware/.host-tools/lcd-flicker-build/codex_desk_meter.bin
```

후보 app을 자동으로 다시 build하는 명령이 아니므로 검사한 binary를 그대로 올린다.
기존 sender state를 초기화하는 명령과 구분한다. receiver가 비어 있어도 기존 sender state가 있으면 그대로 이어간다. 최초 state 생성은 해당 장치에서 state를 한 번도 만든 적이 없을 때만 수행한다.

## PC 프로그램

실행 위치는 이 실험 checkout의 루트이며 진입점은 `python -m pc.cli`다.
현재 설치 환경에서는 `C:/Espressif/user-tools/python_env/idf5.3_py3.11_env/Scripts/python.exe`에
필요한 `jsonschema`와 `serial`이 있다. 아래 `python`은 해당 환경을 가리킨다.

```powershell
python -m pc.cli --help
python -m pc.cli inventory --session-dir '<Codex sessions 폴더>'
python -m pc.cli collect --session-file '<직접 선택한 session JSONL>' --live-quota
```

inventory는 세션 ID·시각·token metadata를 보여준다. 실제 시험은 명시적으로 선택한
파일 또는 `--session-dir ... --session-id ...`를 사용한다. `--latest`는 사용자가
최신 세션을 고르는 정책을 선택했을 때만 사용한다. 기존 Codex 로그인이 quota 읽기를
담당하며 수집기는 auth 파일·키·cookie를 직접 읽지 않는다.

처음 sender state를 만들 때는 업로드 뒤 정상 부팅으로 receiver가 비어 있음을 확인한다.
sender의 state와 lock은 Git에서 제외되는 로컬 `artifacts/`에 둔다.

```powershell
python -m pc.cli init-device --device-alias orca-harness-com3 --confirmed-empty-receiver --state-file artifacts/orca-harness-runtime/sender-state.json --lock-dir artifacts/orca-harness-runtime/locks
python -m pc.cli send --device-alias orca-harness-com3 --port COM3 --session-file '<직접 선택한 session JSONL>' --live-quota --state-file artifacts/orca-harness-runtime/sender-state.json --lock-dir artifacts/orca-harness-runtime/locks
python -m pc.cli watch --device-alias orca-harness-com3 --port COM3 --session-file '<직접 선택한 session JSONL>' --live-quota --interval 60 --state-file artifacts/orca-harness-runtime/sender-state.json --lock-dir artifacts/orca-harness-runtime/locks
```

watch에서 Enter는 PC 수동 재수집, Ctrl+C는 종료다. PC 재시작·COM 재연결 시 같은 state를
이어 사용하며 init/reset/force-overwrite로 순번을 되돌리지 않는다. state 유실·손상은
전송 중지 사유다. `[HOST WRITE]`만으로 장치 수락을 판정하지 않는다.

fixture 시험은 `--provider-fixture`, `--personal-usage`, `--global-reset`의 동결 입력을
별도로 선택해 provenance를 보존한다. 글로벌 리셋 fixture와 실제 계정 quota의 reset은
서로 다른 source다. 제공되지 않은 값은 unknown/null이며 0이나 현재 시각으로 채우지 않는다.

## 실물 관측

- 업로드 전후 파일 hash·port·시간과 실제 보드 관측을 같은 기록에 연결한다.
- 데이터 전 Usage/Global/Status의 WAITING/default, 데이터 후 실제 숫자·단위·source·시각을 확인한다.
- BOOT 짧게 3번으로 세 화면과 처음 화면 복귀, 600ms 이상 누르기로 모든 window page 접근을 확인한다.
- 30초 동안 표시 유지·잘림·가독성·깜박임·꺼짐·자동 reboot를 확인한다. RST 조작은 별도로 기록한다.
- fixture로 오류→last-good→복구, source age 299/300초와 receive age 분리, 새 frame 반영 지연을 시험한다.
- USB 링크 단절 중 표시 유지 시험에는 별도 전원이 필요하다. 전원을 뽑은 재부팅과 링크 단절을 구분한다.
- 실제 LCD/BOOT·지연·sensor·24시간 안정성은 측정 전까지 `not_run`이다. 브라우저·C framebuffer·host write로 대체하지 않는다.

중단되면 [재개 절차](orca-harness-resume.md)를 따른다. 개인 원본 JSONL·인증 내용·전체 대화는
Git에 넣지 않고, 필요한 source/시각/숫자 metadata와 비식별 시험 결과만 남긴다.
