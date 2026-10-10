# LCD 주기적 점멸 보완

2026-10-10 최종 직접 확인: 사용자가 **‘반복 점멸이 사라짐’**이라고 답했다. 영상 샘플·이 응답·BOOT/수동 RST 사실을 근거로 기존 반복 점멸 개선을 실물 확인했다. 아래 ‘직접 확인 대기’는 응답 전 기록이다. 긴 숫자 결함 및 다른 제품 미측정 조건은 별도로 유지하며 전체 제품 PASS는 아니다.

2026-10-10 수정본 영상 추가: [영상/사용자 응답](../../experiments/orca-harness-20261008/operator/post-flicker-observation-20261010.json)에서 실물 BOOT 순환·수치 갱신·CRC VALID를 확인했다. 약63초 뒤 WAITING은 직접 RST에 따른 것이며 자동 재부팅 실패가 아니다. 검사한 샘플에는 이전 흰색 부분 지워짐이 없으나 반복 점멸 소멸은 직접 관측 답변 대기다. 긴 숫자 잘림은 [별도 보완](2026-10-10-lcd-numeric-readability.md)으로 연결한다. 아래 08:49/15:52의 대기는 당시 상태다.

2026-10-10 15:52 KST 재개: 기존 수정·검증·08:48 업로드는 보존했다. source15/artifact4/입력57 hash·Task24개 완료를 확인했고, 사용자의 COM3 연결 뒤 같은 state/세션의 seq46부터 60초 watch를 복구했다. [복구 기록](../../experiments/orca-harness-20261008/operator/live-watch-resume-20261010.json). 새 flash/reset/init는 하지 않았다. 남은 사용자 점멸/30초·CRC·BOOT 관측을 다시 요청했다.

목표: 사용자 08:13 실데이터 영상에서 관측된 반복적인 화면 지워짐/점멸을 없애고, 선택 B·데이터 의미·BOOT 탐색·stale 갱신을 보존한다. 원래 host 후보 `7ccbb24`와 초기 관측은 보존한다. 별도 새 비교 실험을 시작하지 않는다.

| 작업 | 상태 | 완료 조건 |
|---|---|---|
| 사용자 영상·기존 갱신 경로 관측 | 완료 | 원본 hash·정확한 frame404/494의 부분 지워짐·실제 숫자/CRC 기록. 식별자가 보이는 이미지는 Git 제외 로컬 보존 |
| Sol의 원인 재현·좁은 firmware 수정 | 완료 | `9bbe333`: 원래 production BSP의 표시 중 pixel 변경 재현; 별도 버퍼 완성 후 두 bounce 경계로 교체 |
| 실제 host 검사·ESP-IDF build | 완료 | 원래 코드의 의도된 재현 실패, 수정 firmware19/19·선택 세션1/1, SDK build·source15/15·artifact4 hash 일치 |
| Luna 독립 표시 경로 검증 | 완료 | `msg_999781af4044` PASS: firmware19/19·producer/선택21/21·독립 표시1/1, SDK/source/artifact 확인; release/ack 완료 |
| coordinator 동결·재업로드·live 재개 | 완료 | tag `orca-harness-20261010-lcd-flicker-candidate` / `8fe1f9f`; 08:48 COM3 세 이미지 쓰기 hash 통과, 기존 writer 종료 후 같은 state/세션 seq40부터 watch 재개 |
| 사용자 점멸/30초 관측 | 범위 내 완료 | 영상의 RST 이전 구간에서 표시·데이터/CRC·BOOT 관측, 사용자 반복 점멸 소멸 직접 확인. 계측/전 프레임 분석은 미실행 |

2026-10-10 08:49 KST: [독립 검증](../agent-runs/orca-luna/lcd-flicker-review.md), [업로드](../../experiments/orca-harness-20261008/operator/flash-lcd-flicker-20261010.json), [live 재개](../../experiments/orca-harness-20261008/operator/live-watch-lcd-flicker-20261010.json)를 보존했다. 사용자에게 수정 후 관측을 요청했다. 긴 토큰 지수부 잘림은 이번 표시 교체 수정과 별도이며 미해결이다.

역할: firmware/자체 시험/보고는 기존 Codex `gpt-6-sol`, 독립 검증은 `gpt-6-luna`, coordinator는 지정 영상 관측·문서·Git·COM·실계정만 담당한다. PC 코드·동결 입력 57개·기존 판정은 바꾸지 않는다. 자동 승인 옵션은 기존 사용자 요청을 유지한다.

원인 후보의 검증은 실제 코드 경계와 영상에 근거한다. 화면 갱신 빈도를 낮추거나 source 시각을 갱신해서 증상을 숨기지 않는다. 센서·시간 표시의 주기 갱신과 BOOT/새 frame 반영을 유지한다. 화면 지워짐/부분 표시와 USB 재연결/RST/카메라 노출을 구분한다. host 검사는 실물 무점멸을 보장하지 않으므로 새 영상 확인 전 물리 PASS를 선언하지 않는다.

중단 시 [재개 기록](../experiments/orca-harness-resume.md)의 같은 Run/Task/Dispatch와 PC watch 소유권을 확인한다. 두 번째 sender·반복 초기화·중복 수정 worker를 시작하지 않는다.
