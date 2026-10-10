# LCD 숫자 잘림 보완 계획

목표: 선택 B의 토큰 수·사용한도 숫자가 표시 영역에서 잘려 크기나 단위가 달라 보이는 결함을 고친다. 기존 점멸 수정과 동결 판정은 보존한다.

설계 근거: [제품 계약](../PRODUCT_CONTRACT.md)의 잘리지 않는 가로 UI, [협업 역할](../design/2026-10-08-orca-harness.md), [실물 관측](../../experiments/orca-harness-20261008/operator/post-flicker-observation-20261010.json).

구조: production `firmware/main/gui.c`의 숫자 형식과 그리기 폭을 함께 다룬다. 실제 314,238,800 같은 정수는 가능한 경우 정확한 십진수 전체를 표시하고 기존 bitmap 글꼴의 정수 배율을 낮춰 맞춘다. 극단값·비정수는 전체 지수와 단위를 보존하는 폭 내 표기로 처리한다. wire 값·PC 수집·합계 정의를 바꾸거나 잘린 문자열을 그대로 숫자로 표시하지 않는다.

범위: `number`, `session_row`, Usage TOTAL, quota used/remaining의 모든 호출부; `tests/firmware/test_gui.py`의 실제 C pixel 회귀 검사. 새 의존성·일반 GUI 재설계·데이터 추정·BSP 변경은 필요 없다. quota 남은 값의 `USED / REM` 접두사도 실제 남은 폭을 계산한다. unknown `--`, percent `%`, 원본 합계와 정규화 합계의 분리, cached/reasoning 포함 관계를 보존한다.

| 작업 | 담당 | 상태 | 완료 조건 |
|---|---|---|---|
| 이전 영상·RESET/BOOT 사실 기록 | coordinator | 완료 | 영상 hash·상대 촬영 시점·수동 RESET·잘림을 비식별 기록, 원본 이미지는 Git 제외 |
| 실제 C 숫자 표시 재현→수정→시험 | Codex gpt-6-sol | 준비 | 314238800 등 현재 크기의 합계/각 행, 0·null·큰 정수·quota 절대값·percent를 production render로 검사. 원래 코드에서 의도된 잘림 실패 후 수정 PASS |
| ESP-IDF 빌드·source/artifact 제출 | Sol | 준비 | SDK5.3.2 genuine build, 별도 `firmware/.host-tools/numeric-readability-build/` 결과 및15개 source/4개 artifact SHA. 기존 flicker-build를 덮어쓰지 않음 |
| 독립 검증 | Codex gpt-6-luna | 준비 | `tests/integration/` 및 자신의 보고서만 수정. 실제 C의 숫자 전체/단위/경계, 기존 표시 교체 검사와 producer/selection 회귀 통과 |
| coordinator 동결·COM3 업로드·관측 | coordinator | 준비 | accepted worker_done·검증·hash 일치 후 새 tag. 기존 sole watch 정상 종료 확인→업로드→같은 state/세션 재개→새 실물 숫자/점멸 관측 |

실행: 사용자 지정 실제 Orca Run `run_c968c43361da`의 새 Task/Dispatch로 진행한다. Sol만 `firmware/`, `tests/firmware/`, `docs/agent-runs/orca-sol/`을 수정한다. Luna는 구현 파일을 수정하지 않는다. Git·COM·실계정은 coordinator만 소유한다. Codex 자동 승인 옵션은 기존 사용자 지시를 유지한다. 과거 source/tag·입력57개·개인 로그는 변경/커밋하지 않는다.

리뷰 초점: 큰 정수의 정확한 자리수, 과학 표기 지수/단위의 보존, quota 접두사를 제외한 공간, null의 `--` 유지, 배율 변경이 글자 높이·주변 label/경계를 침범하지 않는지 확인한다. 숫자 pixel 전체를 검증하며 문자열 길이만 시험해 실제 그리기 결함을 놓치지 않는다.

중단 시 [재개 절차](../experiments/orca-harness-resume.md)와 context의 이 Task 상태를 확인한다. 오래된 task24 완료만으로 후속 완료를 단정하지 않는다. live writer·sender state를 초기화하거나 두 번째 sender를 실행하지 않는다. host PASS와 실물 PASS는 분리한다.
