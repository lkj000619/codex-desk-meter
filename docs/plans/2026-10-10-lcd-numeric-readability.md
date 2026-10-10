# LCD 숫자 잘림 보완 계획

목표: 선택 B의 토큰 수·사용한도 숫자가 표시 영역에서 잘려 크기나 단위가 달라 보이는 결함을 고친다. 기존 점멸 수정과 동결 판정은 보존한다.

 실행 체크포인트: Sol `task_2ae3cb0fe949` / `ctx_6fb4838726ea`, terminal `term_c11b9d1c-4c32-4a5c-ac0d-1c4814fd426d`. 실제 argv·TUI에서 `gpt-6-sol` 및 자동 승인 옵션 확인, pasted draft를 읽은 후 Enter1회 제출, 실제 응답과 파일 읽기 실행을 확인했다. native reused-terminal model은 null이고 fleet `missing_status`는 종료 증거가 아니다. 아직 제출/build/PASS 전이다.

2026-10-10 Sol 제출 수락: `msg_8aa6b9b04c59`의 succeeded를 native completed로 확인하고 release/ack했다. source commit `7d20952`, 자체 firmware20/20 및 genuine IDF5.3.2 build 통과. coordinator는 GUI3/3(2.134초), source15·artifact4의 staging/export hash, BSP 보존을 확인했다. [보고](../agent-runs/orca-sol/numeric-readability-report.md)·[build receipt](../agent-runs/orca-sol/numeric-readability-build-receipt.json). receipt는 UTF8 BOM(`utf-8-sig`), 원본 PowerShell build console은 UTF16 BOM(`utf-16`)으로 읽고 원본 바이트를 보존한다. app `953152b0…`, 308992바이트. Luna Task `task_5b1435a8c3c1`은 이제 실행 가능하며 새 후보는 아직 보드에 올리지 않았다.

설계 근거: [제품 계약](../PRODUCT_CONTRACT.md)의 잘리지 않는 가로 UI, [협업 역할](../design/2026-10-08-orca-harness.md), [실물 관측](../../experiments/orca-harness-20261008/operator/post-flicker-observation-20261010.json).

구조: production `firmware/main/gui.c`의 숫자 형식과 그리기 폭을 함께 다룬다. 실제 314,238,800 같은 정수는 가능한 경우 정확한 십진수 전체를 표시하고 기존 bitmap 글꼴의 정수 배율을 낮춰 맞춘다. 극단값·비정수는 전체 지수와 단위를 보존하는 폭 내 표기로 처리한다. wire 값·PC 수집·합계 정의를 바꾸거나 잘린 문자열을 그대로 숫자로 표시하지 않는다.

범위: `number`, `session_row`, Usage TOTAL, quota used/remaining의 모든 호출부; `tests/firmware/test_gui.py`의 실제 C pixel 회귀 검사. 새 의존성·일반 GUI 재설계·데이터 추정·BSP 변경은 필요 없다. quota 남은 값의 `USED / REM` 접두사도 실제 남은 폭을 계산한다. unknown `--`, percent `%`, 원본 합계와 정규화 합계의 분리, cached/reasoning 포함 관계를 보존한다.

| 작업 | 담당 | 상태 | 완료 조건 |
|---|---|---|---|
| 이전 영상·RESET/BOOT 사실 기록 | coordinator | 완료 | 영상 hash·상대 촬영 시점·수동 RESET·잘림을 비식별 기록, 원본 이미지는 Git 제외 |
| 실제 C 숫자 표시 재현→수정→시험 | Codex gpt-6-sol | 완료 | 원래 production GUI에서314238800 잘림 의도된 실패; 수정 firmware20/20, root GUI3/3 PASS |
| ESP-IDF 빌드·source/artifact 제출 | Sol | 완료 | SDK5.3.2 genuine build, 별도 `firmware/.host-tools/numeric-readability-build/` 결과 및15개 source/4개 artifact SHA 일치. 기존 flicker-build 보존 |
| 독립 검증 | Codex gpt-6-luna | 완료 | `msg_79be3c78e790` succeeded/native completed 수락·release/ack. [검토](../agent-runs/orca-luna/numeric-readability-review.md)·source commit `460fb49`. 숫자 pixel2/2·firmware20/20·presentation1/1·producer/selection20/20, source15/artifact4 대조 PASS. coordinator pixel2/2 재실행(21.977초)도 PASS |
| coordinator 동결·COM3 업로드·관측 | coordinator | 동결 후 업로드 진행 | 새 tag `orca-harness-20261010-numeric-candidate`. 기존 sole watch 정상 종료 확인→업로드→같은 state/세션 재개→새 실물 숫자/점멸 관측. host PASS와 실물 판정은 분리 |

실행: 사용자 지정 실제 Orca Run `run_c968c43361da`의 새 Task/Dispatch로 진행한다. Sol만 `firmware/`, `tests/firmware/`, `docs/agent-runs/orca-sol/`을 수정한다. Luna는 구현 파일을 수정하지 않는다. Git·COM·실계정은 coordinator만 소유한다. Codex 자동 승인 옵션은 기존 사용자 지시를 유지한다. 과거 source/tag·입력57개·개인 로그는 변경/커밋하지 않는다.

리뷰 초점: 큰 정수의 정확한 자리수, 과학 표기 지수/단위의 보존, quota 접두사를 제외한 공간, null의 `--` 유지, 배율 변경이 글자 높이·주변 label/경계를 침범하지 않는지 확인한다. 숫자 pixel 전체를 검증하며 문자열 길이만 시험해 실제 그리기 결함을 놓치지 않는다.

2026-10-10 숫자 후속 범위의 시험 수 명확화: 현재 unittest loader는 selected-session 1개, producer-to-C 19개, 합계 **20개**를 열거한다. 이번 검증 보고의20/20이 실제 실행 수이며 Task가 이전 보고에서 가져온21이라는 표기는 이번 suite의 개수로 사용하지 않는다. 수를 맞추기 위한 시험 추가/재실행은 필요하지 않다. 이 명확화는 현재 숫자 후속에만 적용하며 이전 원본 판정·evidence를 덮어쓰지 않는다. coordinator 메시지 `msg_8197337d2963`로 동일 내용을 전달했다.

중단 시 [재개 절차](../experiments/orca-harness-resume.md)와 context의 이 Task 상태를 확인한다. 오래된 task24 완료만으로 후속 완료를 단정하지 않는다. live writer·sender state를 초기화하거나 두 번째 sender를 실행하지 않는다. host PASS와 실물 PASS는 분리한다.
