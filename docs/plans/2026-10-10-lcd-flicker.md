# LCD 주기적 점멸 보완

목표: 사용자 08:13 실데이터 영상에서 관측된 반복적인 화면 지워짐/점멸을 없애고, 선택 B·데이터 의미·BOOT 탐색·stale 갱신을 보존한다. 원래 host 후보 `7ccbb24`와 초기 관측은 보존한다. 별도 새 비교 실험을 시작하지 않는다.

| 작업 | 상태 | 완료 조건 |
|---|---|---|
| 사용자 영상·기존 갱신 경로 관측 | 완료 | 원본 hash·정확한 frame404/494의 부분 지워짐·실제 숫자/CRC 기록. 식별자가 보이는 이미지는 Git 제외 로컬 보존 |
| Sol의 원인 재현·좁은 firmware 수정 | 완료 | `9bbe333`: 원래 production BSP의 표시 중 pixel 변경 재현; 별도 버퍼 완성 후 두 bounce 경계로 교체 |
| 실제 host 검사·ESP-IDF build | 완료 | 원래 코드의 의도된 재현 실패, 수정 firmware19/19·선택 세션1/1, SDK build·source15/15·artifact4 hash 일치 |
| Luna 독립 표시 경로 검증 | 진행 | `task_4386f8dbef93` / `ctx_1ab7525e89ae`; front buffer 쓰기·표시 완료/동기화·오류 경로와 B/BOOT/stale 회귀 확인 |
| coordinator 동결·재업로드·live 재개 | 대기 | 기존 watch 종료 확인 후 COM3 업로드, sender state/순번 유지, 같은 세션/계정으로 재개 |
| 사용자 점멸/30초 관측 | 대기 | RESET 없이 표시 유지, 데이터·CRC·BOOT 탐색, 점멸 개선 실물 확인 |

역할: firmware/자체 시험/보고는 기존 Codex `gpt-6-sol`, 독립 검증은 `gpt-6-luna`, coordinator는 지정 영상 관측·문서·Git·COM·실계정만 담당한다. PC 코드·동결 입력 57개·기존 판정은 바꾸지 않는다. 자동 승인 옵션은 기존 사용자 요청을 유지한다.

원인 후보의 검증은 실제 코드 경계와 영상에 근거한다. 화면 갱신 빈도를 낮추거나 source 시각을 갱신해서 증상을 숨기지 않는다. 센서·시간 표시의 주기 갱신과 BOOT/새 frame 반영을 유지한다. 화면 지워짐/부분 표시와 USB 재연결/RST/카메라 노출을 구분한다. host 검사는 실물 무점멸을 보장하지 않으므로 새 영상 확인 전 물리 PASS를 선언하지 않는다.

중단 시 [재개 기록](../experiments/orca-harness-resume.md)의 같은 Run/Task/Dispatch와 PC watch 소유권을 확인한다. 두 번째 sender·반복 초기화·중복 수정 worker를 시작하지 않는다.
