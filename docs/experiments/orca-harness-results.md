# Orca 역할 협업 실험 결과

지금까지의 작업은 아래와 같다. 기존 단독 모델 비교와 분리한 새 구현이며, 이번 협업의 구현·검증 완료를 제품 전체 실물 합격으로 계산하지 않는다.

| 작업 | 결과와 근거 |
|---|---|
| 실험 격리·역할 분담 | 별도 branch `lkj000619/experiment-orca-harness-20261008`, Orca Run `run_c968c43361da`, 동결 입력57개 보존. 실제 CLI 모델·자동 승인 옵션을 확인하고 역할별 Task/Dispatch로 진행 |
| LCD UX/UI 시안·선택 | AGY Gemini와 Codex Sol6.1이 각3개, 총6개 820×320 시안 제출. 사용자가 B Swiss Studio Meter를 선택했고 브라우저 결함 보완·독립 디자인 검증을 거쳐 firmware에 반영 |
| PC Codex 수집·전송 | 선택한 세션의 input/output/cached/reasoning 토큰과 native5h/weekly quota·reset 시각 수집. unknown·cache·선택·CRC frame·수동/자동 갱신·deadline 경계를 보완했으며 최종 PC64/64 및 당시 통합27/27 통과 |
| ESP32 구현·연결 | Sol이 Usage/Global/Status, BOOT 탐색, USB frame/CRC 수신·last-good/stale/error·F9 온도 경로 구현. ESP-IDF5.3.2 실제 build와 source/artifact hash를 검증하고 COM3 실데이터 연결 |
| 실물 점멸 보완 | 영상에서 반복 흰색 지워짐을 확인해 BSP 표시 교체를 수정·독립 검증·재업로드. 사용자가 이전 후보에서 반복 점멸 소멸을 직접 확인했고 수동 RST→WAITING과 자동 재부팅을 구분 |
| 숫자 잘림 보완 | 큰 토큰 값의 잘린 지수 문제를 실제 C pixel로 재현·수정. Luna numeric2/2·firmware20/20·presentation1/1·producer/selection20/20 및 source15/artifact4 PASS, coordinator numeric2/2 재실행 PASS. 새 후보 17:03 업로드 후35.25초 영상·직접 응답 범위에서 전체 숫자/%·화면 순환·CRC·무점멸 확인 |
| 중단 후 재개 안전장치 | 계획·재개 절차·context·native runtime snapshot·후보 tag·업로드/단일 writer 근거를 보존. Task26개 완료, 전송 순번·pinned 세션·locks를 유지하며 개인 세션/인증 원문은 Git 제외 |

**2026-10-10 17:12 KST 현재:** **Task26개 구현·독립 검증 완료, 숫자 잘림·점멸 보완의 기본 실물 확인 완료**. 새 tag `orca-harness-20261010-numeric-candidate` (`16b7d66`), 17:03 COM3 업로드·쓰기 hash 검증, 17:04 같은 세션/state seq116부터 live 재개. [35.25초 영상·직접 응답](../../experiments/orca-harness-20261008/operator/post-numeric-observation-20261010.json)에서 전체 숫자/%, 화면 순환·CRC VALID·수치 갱신과 RESET 없는 반복 점멸 소멸을 확인했다. 지연·물리 오류복구·센서 검교정·24시간은 미측정으로 전체 제품은 `product_pass=false`. 아래 원본 판정은 각각 당시 범위다.

2026-10-10 후속 직접 관측 답변: **‘반복 점멸이 사라짐’**. 기존 수정의 반복 점멸 개선은 사용자 관측·샘플 영상 범위에서 실물 확인했다. 화면 갱신 중 흰색 부분 지워짐과 사용자의 수동 RST를 구분했다. 숫자 잘림 FAIL 및 제품 전체 미측정 항목은 그대로이며 아래 직접 답변 대기는 응답 전 기록이다.

2026-10-10 수정본 실물 관측 추가: [97.43초 영상](../../experiments/orca-harness-20261008/operator/post-flicker-observation-20261010.json)에서 BOOT 화면 순환·수치 갱신·FRAME/CRC VALID를 확인했다. 약63~70초의 검은 화면→WAITING은 사용자가 직접 RST를 누른 결과이며 자동 재부팅 실패로 판정하지 않는다. 파일명/전송 mtime로 촬영 일시를 확정하지 않고 ‘어제 업로드 한 결과’라는 사용자 귀속을 보존했다. 검사한 샘플에서는 이전 흰색 부분 지워짐이 없고 반복 점멸 소멸은 직접 확인 대기다. TOTAL의 `3.142388` 및 각 행의 지수부 잘림은 가독성 FAIL로 기록했다. [별도 숫자 보완](../plans/2026-10-10-lcd-numeric-readability.md)을 진행하며 300ms/2초 지연·긴 BOOT 다중 페이지·센서 검교정·24시간은 미측정, `product_pass=false`다. 아래 기존 판정은 당시 원본이다.

2026-10-10 15:52 KST 재개: Run generation6에서 기존 Task24개 completed·cleanup 미결0개와 source/artifact/입력 hash를 확인했다. Orca 재시작으로 종료된 PC watch는 사용자 USB 재연결 뒤 **같은 세션·state의 seq46부터 60초 갱신을 복구**했다. [live 복구](../../experiments/orca-harness-20261008/operator/live-watch-resume-20261010.json). 이번 재개에 새 firmware 업로드·리셋·소스 변경은 없으며 **수정 후 실물 점멸/CRC/BOOT/30초 관측은 여전히 대기**다. `product_pass=false`; 아래는 단계별 당시 검증과 관측이다.

2026-10-10 08:49 KST: **LCD 점멸 수정·독립 host 검증·COM3 재업로드·live 재개 완료, 수정 후 실물 관측 대기**. 표시 중 버퍼를 직접 지우는 경로를 수정했고, 60초 watch는 같은 세션과 sender 순번을 이어간다. `product_pass=false`이며 무점멸·BOOT 조작·30초 유지·반영 지연·센서 타당성·24시간 안정성은 아직 합격하지 않았다.

수정본 독립 **firmware19/19·producer/선택21/21·표시1/1 PASS**를 수락·release/ack하고 새 tag **`orca-harness-20261010-lcd-flicker-candidate` (`8fe1f9f`)**에 동결했다. 08:48 COM3에서 실제 ESP32-S3와 세 이미지 쓰기 hash 검증을 확인했으며 app은 `953782e5486adbe9743e5b753e716892cfdfbeef25d23b1702dc1d6050078f1f`다. 기존 watch가 정상 종료된 뒤 새 terminal `term_dcac760e-42fa-42f9-afa6-1da904d96d49`에서 **seq40** 전송을 확인했다. [독립 보고](../agent-runs/orca-luna/lcd-flicker-review.md), [수정본 업로드](../../experiments/orca-harness-20261008/operator/flash-lcd-flicker-20261010.json), [live 재개](../../experiments/orca-harness-20261008/operator/live-watch-lcd-flicker-20261010.json). HOST WRITE와 수정 후 실물 CRC·무점멸을 구분하며 새 관측을 요청했다. 아래는 단계별 당시 근거다.

후속 08:13 영상에서 실제 수치와 **FRAME/CRC VALID**를 확인했다. 적어도 한 live frame의 장치 수락은 실물로 확인됐으며 촬영 당시 5시간 31%/잔여69%, 주간 68%/잔여32%였다. 사용자가 지속적인 점멸을 보고했고 화면 일부가 흰색으로 지워지는 장면도 보여 **화면 안정성은 보완 필요**다. 새로운 `task_63d11f3c24cb` / `ctx_2363ff345723`에서 기존 Sol 모델이 표시 경로를 조사·수정한다. 원래 host 합격과 tag는 보존하며 물리 PASS로 소급하지 않는다. [후속 영상의 비식별 관측](../../experiments/orca-harness-20261008/operator/post-data-video-20261010/observation.json) · [점멸 보완 계획](../plans/2026-10-10-lcd-flicker.md).

08:37 KST 보완: Sol의 표시 수정은 **`9bbe333`**에 보존했다. RGB가 읽는 버퍼를 직접 지우는 대신 다른 버퍼에 화면을 완성하고, SDK bounce 경계에서 교체한다. 원래 production BSP는 컴파일 후 표시 중 pixel 변경 검사에서 실패했으며 수정본의 firmware **19/19**가 통과했다. source/staging15개와 새 app `953782e5…`의 hash를 확인했다. [재현·회귀 근거](../../experiments/orca-harness-20261008/operator/lcd-flicker-root-regression-20261010.json), [별도 수정 후보](../../experiments/orca-harness-20261008/operator/firmware-flicker-candidate.json). 독립 Luna `task_4386f8dbef93` / `ctx_1ab7525e89ae`가 검증 중이며, **수정본의 재업로드·실물 무점멸은 아직 미확인**이다. 긴 토큰 문자열의 지수부 잘림도 별도 미해결로 남긴다.

branch `lkj000619/experiment-orca-harness-20261008`, Run `run_c968c43361da`, 호스트 동결 tag `orca-harness-20261010-host-candidate` (`7ccbb24`). 동결 입력 57개를 보존했고 원래 비교 브랜치 `prepare/formal-comparison-20261004`는 수정하지 않았다.

## 역할과 산출물

| 역할·실제 모델 | 결과 | 근거 |
|---|---|---|
| GUI A/B/C · AGY Gemini | 후보 3개 제출, 사용자 선택 B 수정·독립 브라우저 검증 통과 | [B handoff](../design/lcd/gemini/handoff.md), [B 검증](../agent-runs/orca-luna/gui-b-review.md), `aac81f3` |
| GUI D/E/F · Codex `gpt-6.1-sol` | 후보 3개 제출·검증, 비교 시안 보존 | [Sol 6.1 handoff](../design/lcd/sol61/handoff.md) |
| PC · AGY `gemini-3.8-flash-medium` | 세션·quota·영속 sender·자동/수동 갱신 보완 완료, PC **64/64 통과** | [Flash 보고](../agent-runs/orca-flash/report.md), 코드 `39e52bd`, [coordinator 시험](../../experiments/orca-harness-20261008/operator/pc-final-deadline-unittest-20261010.json) |
| firmware · Codex `gpt-6-sol` | 활성 세션 전환·C receiver/cache·B GUI·BOOT·온도 센서 구현, 실제 ESP-IDF build 완료 | [Sol 보고](../agent-runs/orca-sol/report.md), 코드 `853ddf7`, [후보 manifest](../../experiments/orca-harness-20261008/operator/firmware-candidate.json) |
| 독립 검증 · Codex `gpt-6-luna` | 현재 호스트 검증 PASS, 통합 **27/27**, PC 64/64, firmware 18/18, 선택 B 실행 검증 | [Luna 보고](../agent-runs/orca-luna/product-review.md), `6f52105`, [coordinator 통합 재실행 27/27](../../experiments/orca-harness-20261008/operator/integration-final-unittest-20261010.json) |
| coordinator · 실장치/실계정 | COM3 업로드·쓰기 hash 검증, 초기 LCD 관측, 명시적 현재 세션/native quota 수집·전송, 60초 watch 실행 | [업로드](../../experiments/orca-harness-20261008/operator/flash-host-candidate-20261010.json), [수집 metadata](../../experiments/orca-harness-20261008/operator/live-collection-metadata-20261010.json), [watch](../../experiments/orca-harness-20261008/operator/live-watch-20261010.json) |

실효 모델·승인 argv·전체 Task/Dispatch 연결은 [context](../../experiments/orca-harness-20261008/context.json)에 있다. Claude는 사용자 요청에 따라 제외했다. host 단계의 구현 보완 `task_d7aa5e059e8d` / `ctx_a7d558d25511`, 문서 동기화 `task_9becb3b414d9` / `ctx_41536de6636d`, 같은 독립 Task 재시도 `task_4d49e747c570` / `ctx_6b00e6339d06`는 모두 성공 제출을 수락·release/ack했다. 당시 정리 결정이 필요한 reclaimable worker는 0개였다. 새 실물 점멸 보완 Task는 위 후속 상태와 구분한다.

## 검증 범위와 남은 작업

현재 통합 시험은 실제 PC 수집/정규화/canonical bytes를 제품 C receiver에 입력한다. 토큰·quota scope, unknown/error/last-good, 원본 관측 시각, 299/300초 stale, 세션 A→B 교체, CRC/sequence, 수동 요청 경쟁 조건, 실제 sender 반환까지의 5초 경계를 검증했다. 예산이 남아 native RPC를 시작하는 경우와 소진되어 RPC를 생략하는 경우를 별도로 보존했다. SDK/GUI 전체 재빌드는 새 변경이 없어 반복하지 않았다.

업로드 후 읽기 전용 USB 관측에는 0바이트가 수신됐다. 이후 사용자의 밝은 Usage/WAITING 확인과 08:03 영상으로 실제 초기 표시를 확인했다. 영상에는 Usage/Global/Status/Usage 전환, Status의 CONNECTED·FRAME/CRC WAITING·칩 온도 36.5 C가 보인다. 약 13초의 검은 화면은 사용자가 **직접 RESET(RST)을 누른 것**으로 확인했다. 해당 구간을 자동 재부팅으로 판정하지 않는다. 영상이 데이터를 보내기 전 자료이므로 전송 후 숫자·CRC 수락을 증명하지 않는다. [영상 관측](../../experiments/orca-harness-20261008/operator/initial-video-20261010/observation.json)에 원본 hash와 시점별 frame을 보존했다.

08:08:54 KST fixture seq0(832바이트), 08:09:21 KST 실제 세션·native quota seq1(2,844바이트)의 host write가 성공했다. fixture는 동결된 과거 관측값이므로 실제 시계 기준 STALE가 정상이다. 08:10부터 별도 Orca 터미널의 watch가 같은 state로 seq2 이후를 60초마다 전송한다. [fixture 전송](../../experiments/orca-harness-20261008/operator/fixture-send-20261010.json), [실제 전송](../../experiments/orca-harness-20261008/operator/live-send-20261010.json). **HOST WRITE는 장치 ACK가 아니며**, 전송 후 LCD의 FRAME/CRC와 값은 사용자 관측으로 확인한다. [운영 절차](orca-harness-operator.md)에 따라 다음을 이어간다.

1. 전송 후 LCD 수치·FRAME/CRC·방향·잘림·BOOT 3회/600ms 이상 누르기·RESET 없는 30초 유지 관측. 초기 영상의 정확한 BOOT 조작은 아직 미확인이다.
2. 같은 sender state와 명시적 세션 선택을 유지한다. 재개 시 기존 watch의 실행·COM 소유권을 확인하고 중복 실행하지 않는다.
3. 오류→last-good→복구·분리 전원에서 링크 단절·센서 타당성·반영 지연·장시간 안정성 기록. 측정 전 PASS 처리하지 않음.

PC의 실제 수집은 `CODEX_THREAD_ID`가 가리키는 파일 한 개를 명시적으로 선택했다. 사용자 대화·auth·원본 JSONL은 복사하지 않았으며 실제 원본 식별자가 있는 구조화 metadata와 고정 선택 경로는 Git에서 제외되는 `artifacts/`에 있다. 공개 기록에는 provider/metric/status/시각/숫자만 남겼다. 최초 계정 관측은 5시간 24% 사용·76% 잔여, 168시간 67% 사용·33% 잔여였다. 이 값은 관측 시점 값이며 현재 잔여량을 보장하지 않는다. 토큰 source 이벤트가 갱신되지 않으면 재수집해도 관측 시각을 현재로 바꾸지 않으며, 300초 이후 해당 source의 STALE 표시는 정상이다. 새 quota 관측과 구분한다.

이번 대화의 누적 토큰 값은 이전 작업과 세션 재개를 포함한다. 이를 이번 협업 실험의 비용으로 계산하지 않는다. 역할별 실제 AI 실행시간·토큰·금액은 완전한 측정 근거가 없어 unknown이다. 기존 단독 비교와 역할·모델·시간 예산·GUI 선택·live 범위가 달라 결과 차이를 Orca의 단독 효과나 공정한 모델 순위로 해석하지 않는다.

## 보존된 실패와 재개

이전 독립 실패 원본은 `117a988`, `9721f71`, 이전 Flash 제출은 `e7c5b51`에 보존했다. 추가 경계 6.125초와 재개 후 5.016초 실패를 삭제하거나 소급 PASS로 바꾸지 않았다. 수동 요청 기준 시각 보존, OS timeout 설정 실패 시 쓰기 차단, 실제 SendOutcome 완료 시각 검증으로 보완했고 현재 통합에서 재확인했다.

Orca 메시지 enqueue·화면의 check 실행은 처리/ack의 증거가 아니다. 실제 FIFO Delivery 처리·ack와 현재 Dispatch별 안내를 확인하고, 독립 시험이 기존 경계를 대체한 경우 해당 경계를 별도 복원했다. 세션 재시작 시 [재개 기록](orca-harness-resume.md)과 [체크리스트](../plans/2026-10-08-orca-harness.md)를 따른다. 현재는 수정본 업로드 후 사용자 실물 관측 대기다. 같은 sender state로 이미 갱신 중이므로 초기화·두 번째 writer·임의 재업로드를 반복하지 않는다.
