# 요구사항 검토 — V2 live telemetry 및 LCD

- 검토일: 2026-10-08
- Task: `task_c4c03e6d2c02`
- Dispatch: `ctx_a4f395e58ecc`
- 담당 범위: 독립 요구사항 검토. 산출물은 이 보고서와 `checkpoint.md`뿐이다.
- 판정: **조건부 승인**. 공통 GUI 시안 작업과 schema-preserving session channel 설계는 진행 가능하다. 제품 구현 전에는 아래 데이터 의미/인터페이스 결정을 기록해야 한다. 이 보고서는 구현·실물 합격을 선언하지 않는다.

## 요약

기존 `UsageSnapshot`/`cdm/1`은 `session_telemetry`를 이미 허용한다. token component를 각 `windows[]` 항목의 `used_units` 채널로 표현하고 quota 필드를 null로 두는 synthetic 구조는 동결 schema, canonical CRC32, frame 크기 제한을 통과했다. 새 schema 필드는 필요하지 않으며, 펌웨어는 `metric_kind`와 고정 channel ID에 따라 이를 quota window와 구별해야 한다.

초기 검토에서 duration·source kind·available identity·cache/reasoning 총계의 네 가지 mapping gap을 찾았다. coordinator 질문 `msg_1a0585d74a22`는 답변 `msg_5d56c1876c49`로 해결됐고 cohort 규칙이 `docs/design/2026-10-08-orca-harness.md`에 기록됐다. 구현자는 duration을 exact seconds로 local typed metadata에 보존하고, 정확한 ID/label을 wire에 싣고, unknown을 추정하지 않으며, `local_runtime` provenance와 계정 범위를 지켜야 한다.

여섯 GUI `index.html` 경로가 존재하고 coordinator가 Sol 제출 완료를 알렸다. 별도 GUI review Task의 handoff completeness, independent visual QA와 사용자 선택은 pending이다. 경로 존재나 제출은 UI 승인 또는 firmware/실물 합격이 아니며, 이 리뷰는 콘텐츠·시각 품질을 판정하지 않았다.

## 검토 범위와 증거

직접 읽은 자료: `docs/PRODUCT_CONTRACT.md`, `docs/hardware/version-2-capabilities.md`, `docs/design/2026-10-08-orca-harness.md`, `experiments/orca-harness-20261008/design-brief.md`, `experiments/schema/usage-snapshot.schema.json`, `experiments/schema/cdm-frame.schema.json`, `experiments/schema/end-to-end-result.schema.json` 및 예제, manifest/provider fixture schema, 계획·재개 절차·readiness 상태.

coordinator의 최신 지시 후 여섯 `opendesign/mockups/{gemini,sol61}-{a,b,c}/index.html`이 모두 존재함을 확인했고 Sol 제출 완료 상태를 전달받았다. 이는 제출 상태와 경로 존재 확인이며, 콘텐츠·handoff completeness·visual QA는 별도 GUI review Task의 범위로 남겼다.

동결 입력을 수정하지 않고 Python `jsonschema 4.23.0`으로 메모리 안의 synthetic session/quota snapshot과 `cdm/1` frame을 검증했다. 입력·출력·cached input·reasoning output·provider source total·normalized total 채널, source total과 normalized total이 다른 변형, percent quota와 duration을 담은 기존 ID/label, canonical CRC32, 65,536-byte 한도를 확인했다. 모두 통과했다. `session_id` 또는 `duration_seconds`를 새 속성으로 추가한 음성 사례는 `additionalProperties: false`에 의해 거부됐다. 검증 코드는 파일로 저장하지 않았다.

## 요구사항 품질 평가

점수는 이번 live telemetry 및 LCD 범위에 대한 검토자 추정치다. 동결 계약 전체나 제품의 실측 점수가 아니다.

| 품질 | 점수 | 근거 |
|---|---:|---|
| 완전성 | 86% | 의미·window-duration mapping이 정해졌고 실제 runtime/API 응답·하드웨어 검증은 남음 |
| 명확성 | 86% | cohort mapping은 명시됐고 schema가 강제하지 않는 일부 semantic rule은 구현 검증 필요 |
| 일관성 | 82% | contract/schema nullability 차이는 semantic validator로 보완해야 함 |
| 시험가능성 | 92% | 30초, 300ms, 5초, 2초, 0/299/300초 및 wire 규칙으로 판정 가능 |
| 추적성 | 94% | C/I/F ID, persisted cohort mapping, JSON schema 및 운영 증거 경계가 연결됨 |
| 실현가능성 | 86% | 지정 SDK·보드·기존 wire 구조에 맞출 수 있으나 GPIO0 동작과 런타임 mapping 검증은 남음 |
| **평균** | **88%** | 위 여섯 항목의 산술 평균, 검토 범위 한정 |

## 주요 발견

### P1 — coordinator가 live mapping을 결정함

coordinator 질문/답변(`msg_1a0585d74a22` / `msg_5d56c1876c49`)과 설계 문서 변경으로 초기의 네 가지 데이터 의미 충돌은 이번 cohort에서 해소됐다.

- session token은 `metric_kind=session_telemetry`; `input`, `output`, `cached_input`, `reasoning_output`, `source_total`, `normalized_total`을 token `used_units` 채널로 싣는다. `cached_input`은 input의 부분값, `reasoning_output`은 output의 부분값이며 `normalized_total=input+output`; 두 부분값을 더하거나 빼지 않는다.
- quota duration은 정확한 seconds 값으로 PC local typed metadata에 보존한다. wire는 `primary-18000s` 같은 stable `window_id`와 정확한 duration label을 쓴다. 제공되지 않은 duration은 unknown으로 두며 5시간/주간을 추정하지 않는다.
- available account snapshot의 `agent_id=codex-cli`, `host_id`는 stable sanitized collector alias다. 둘은 수집 맥락이며 quota는 account 범위를 유지하고, 가능한 계정 식별은 `account_profile_id`로 구분한다.
- session JSONL과 native app-server `account/rateLimits/read`는 모두 `source_kind=local_runtime`; 세부 입력 provenance는 local metadata에 구분한다. fixture는 `fixture`다. frozen contract/schema 변경은 승인되지 않았다.

따라서 duration·source kind·cache/reasoning·account attribution은 미결정이 아니라 구현 규칙이다. 구현 전 shared handoff와 semantic check에 이 결정을 반영해야 한다.

### P2 — schema가 available identity 규칙을 완전히 강제하지 않음

제품 계약 §2는 available source의 agent/host identity를 요구하지만 usage schema 및 end-to-end `provider_matrix`는 키가 null인 available record도 받아들인다. 확정된 cohort mapping은 null을 쓰지 않는다. PC semantic validator와 negative cases에서 `status=available`이면 `agent_id`와 `host_id`가 non-null인지 검사한다. 동결 schema/contract는 수정하지 않는다.

### P2 — session channel은 schema 통과만으로 의미가 검증되지 않음

`usage-snapshot.schema.json`과 중첩 `cdm-frame.schema.json`은 `metric_kind=session_telemetry`를 허용하지만 channel 이름·부분합 관계·quota 값 null 조건을 강제하지 않는다. 이 검토의 synthetic 구조는 schema를 통과했고, source total이 normalized total과 달라도 원본이 유지되는 변형도 통과했다. 구현자는 `metric_kind`를 먼저 분기하고 `window_id`/label을 cohort mapping대로 해석해야 한다.

session snapshot의 `snapshot_id`는 선택 세션 identity를 식별해야 하며 local metadata에 native identity를 보존한다. schema ID pattern에 맞는 안정 ID를 사용하고 경로·세션 본문을 wire/log/UI로 보내지 않는다. `end-to-end-result.schema.json`의 `telemetry.agent_tokens`는 작업자 실행 telemetry이므로 live 세션 저장 공간으로 재사용하지 않는다.

### P2 — 실제 제공자/하드웨어 동작은 아직 미검증

정확한 app-server 응답 형태, 설치된 CLI JSONL 형식의 변화, source-age/receive-age 회복 동작, panel init과 GPIO0 전기적 상호작용은 본 schema 검토에서 입증되지 않았다. 정해진 source와 합성 metadata 이후 각 구현자가 지원 형식을 fail-closed로 확인하고, coordinator가 owner-only live/device 시험을 별도로 수행해야 한다.

## 구현 acceptance matrix

| ID | 합격 기준 | 검증 증거 |
|---|---|---|
| L1 세션 선택 | 사용자가 지정한 session ID/file이 명시적으로 선택되고 latest 정책이 문서화된다. 여러 세션 합산·묵시적 최신 선택이 없다. | metadata-only synthetic JSONL로 선택/목록/latest 정책 검증, 선택 ID와 출력 snapshot 대조 |
| L2 누적 token event | 누적 `event_msg/token_count`를 반복 합산하지 않는다. 재시작, partial line, truncate/replace, multi-session을 처리한다. 사용자 대화 본문은 읽거나 보관하지 않는다. | synthetic JSONL 경계 테스트와 재시작 전후 결과; 파일 내용 없이 metadata 결과만 남김 |
| L3 session channels | 별도 `metric_kind=session_telemetry` snapshot. 고정 ID `input`, `output`, `cached_input`, `reasoning_output`, `source_total`, `normalized_total`; token `used_units`; quota 값(remaining/limit/percent/resets_at)은 null, reset_status는 생략 또는 unknown. selected session identity는 snapshot_id/local metadata에 보존한다. | usage schema + cdm schema 통과; stable IDs, source total≠normalized total 변형, 부분값/합계 불변식 semantic 검사 |
| L4 계정 quota | 기존 로그인으로 read-only `account/rateLimits/read`만 사용한다. auth 파일/cookie/key 직접 읽기, thread/turn/reset 실행은 없다. quota는 account scope이며 available identity는 `agent_id=codex-cli`, stable sanitized collector `host_id`; `source_kind=local_runtime`, detailed provenance는 local metadata다. | synthetic provider response, 호출 범위/metadata 기록, credential-free log; owner-only live account 시험은 coordinator만 수행 |
| L5 quota window | 제공 window를 전부 보존하고 percent/resets_at/duration으로 구분한다. duration seconds는 local typed metadata, wire ID/label은 정확한 값(예: `primary-18000s`, `300 min`)을 담는다. duration 미제공은 unknown; 5h/week 하드코딩이나 절대 토큰 잔여량 추정이 없다. | 서로 다른 duration을 가진 synthetic window; source duration·wire ID/label·resets_at의 일치 및 unknown 경계 확인 |
| L6 의미/분리 | `normalized_total=input+output`; cache/reasoning은 subcount이며 총계에서 추가하거나 빼지 않는다. 계정 quota를 session별 복제·합산하지 않고 global reset을 quota reset으로 재사용하지 않는다. | source_total≠normalized_total synthetic 변형; 불변식 및 snapshot 분리 확인 |
| L7 시간/state | 원본 token event 시각과 quota 응답 획득 시각을 각각 보존. source-age와 frame receive-age 분리. 0/299초 정상, 300초 stale. 새 frame으로 stale source를 fresh 처리하지 않음. null/unknown/error에서 0/현재 시각 대체 없음. | 고정 reference_time synthetic 경계, receive monotonic-clock host/firmware seam 기록, last-good→error/stale→recovery 전이 |
| L8 개인정보 | 실제 대화·전체 세션 로그·auth 내용/secret을 로그나 결과물로 남기지 않는다. live 데이터는 역할 소유자의 실행 중 허용된 token metadata만 사용한다. | synthetic 개발 fixture 및 로그 검토; owner-only real-session 실행은 coordinator가 관리 |
| C1 build | `idf.py set-target esp32s3`와 `idf.py build` 성공 | 명령 출력, target/sdkconfig, binary/hash |
| C2 LCD | 정상 부팅 후 실제 820×320 가로 LCD에서 30초 이상 켜지고 잘림 없음 | 실물 사진/영상 및 관측 시각; browser preview만으로 대체 불가 |
| C3 quota | PC가 보낸 모든 provider/window의 값·단위·조회 시각·resets_at 표시; 제공되지 않은 값/창 생성 없음 | snapshot↔LCD 화면 대조, 서로 다른 duration/percent fixture |
| C4 global reset | 최근 `codex-resets.com` reset과 경과 시간 표시 | source payload와 화면 대조 |
| C5 reset fallback | 최신 reset 없으면 last-known 경과, 그것도 없으면 default 화면 | 3단계 fixture/state 캡처 |
| C6 global provenance | global 화면에 `codex-resets.com`과 조회 시각 표시 | LCD 증거와 wire `captured_at` 대조 |
| C7 오류/복구 | DNS/TLS/HTTP/JSON/empty/stale 오류에도 유지, last-good 보존, 오류 표기, 정상 복구 | 각 오류 입력 후 상태 전이와 값/시각 대조 |
| C8 입력/갱신 | 정상 boot 후 BOOT 화면 전환, 자동 주기 ≤60초, PC 수동 갱신, 수동 명령→전송 ≤5초, 수락→LCD ≤2초 | 버튼/갱신 타임스탬프와 세 화면 실물 기록 |
| I1 collector | 출처·시각·단위·오류/provenance 보존, credential 비노출 | structured output + synthetic fixture 결과 |
| I2 normalization | provider adapter, 서로 다른 global source 격리 | adapter별 fixture와 normalized snapshot |
| I3 transport | 실제 frame/길이/CRC/sequence/reconnect 검증, raw bytes 기록 | PC↔device serial evidence; host write receipt를 device ACK라 부르지 않음 |
| I4 firmware | 검증 frame만 cache/stale/LCD 반영, 잘못된 입력에도 last-good 유지·복구 | host C seam plus real device receive/state evidence |
| F1–F2 | collector inventory/선택/출처와 정규화 규칙을 각각 기록 | 기능별 결과 항목과 근거 경로 |
| F3 | 실제 USB transport만으로 frame 수용 확인 | sequence/CRC/raw serial evidence |
| F4–F5 | receiver/cache/stale와 LCD GUI를 별도 검증 | host C seam 및 실물 UI 증거 별도 |
| F6–F7 | 자동·PC 수동 갱신 및 글로벌 reset 수집/화면 검증 | trigger 시간, source/time, 복구 fixture |
| F8 | build·관측 근거와 미측정 null/not_run 기록 | build logs, artifact/hash, 운영 증거 |
| F9 | 정확히 3개 온보드 기능 후보 비교 후 1개 선택·분리 구현 | 가치/비용/위험/시험/선택 이유 및 재현시험 |

C/I/F 상태는 각각 기록한다. host-only 검사·schema 통과·browser mockup을 실물 합격으로 승격하지 않는다. end-to-end 결과의 미측정 하드웨어/시간/token 값은 null/not_run과 사유로 남기고 `product_pass=true`를 쓰지 않는다.

## LCD·BOOT 하드웨어 제약

| 제약 | 구현 전 확인/수락 조건 |
|---|---|
| 패널 방향/영역 | ST7701 RGB565, 기본 landscape 820×320. 좌표/글꼴/색은 실제 화면의 clipping/가독성으로 검증 |
| framebuffer | 320×820×2 = 524,800 bytes 한 frame. 8MB Octal PSRAM/80MHz를 사용하고 실제 sdkconfig·할당 위치·추가 buffer headroom 기록 |
| BOOT/LCD 공유 | BOOT GPIO0 active-low + pull-up, LCD SPI CS도 GPIO0. 허용 vendor source와 IDF 5.3.2에 근거해 panel init/CS idle/input 전환 순서를 문서화. 초기화 중 BOOT 오검출/CS glitch가 없음을 실제 보드에서 확인 |
| 입력·reset | 정상 boot 이후 debounce된 BOOT가 300ms 이내 usage/global/status 화면 순환. RST는 reset만 수행. BOOT 누른 채 reset은 ROM download mode이므로 정상 입력 합격 절차에서 제외 |
| backlight | GPIO6 active-low; vendor PWM의 8-bit reverse-duty 동작을 확인하고 밝기/꺼짐 극성 검증 |
| 전원/지속 | C2 30초 유지와 USB 단절 중 전원 유지/복구는 coordinator의 실물 관측. 후보 검토자는 COM open/upload/reset 금지 |

## 안전한 재개 체크

`docs/experiments/orca-harness-resume.md` 기준으로 재개는 문서 요약만 믿지 말고 runtime 상태를 확인한다.

1. readiness, 계획 체크리스트, `experiments/orca-harness-20261008/context.json`, 역할 checkpoint를 읽는다. 현재 Run은 `run_c968c43361da`; Task/Dispatch는 live Orca와 이 checkpoint에서 다시 확인한다. 이전 checkpoint의 다른 Dispatch ID를 현재 권한으로 취급하지 않는다.
2. `orca status --json`으로 runtime 확인. coordinator는 필요할 때 resume 문서의 `scripts/checkpoint-orca.ps1 -VerifyOnly` 후 실제 checkpoint helper를 사용해 branch/57 frozen input hash/runtime를 대조한다. 오래된 runtime snapshot만으로 상태를 갱신하지 않는다.
3. coordinator가 `task-list`, `worker-list`, `check`로 Task·활성 Dispatch·liveness·미응답 질문·미확인 worker_done을 확인한다. 이 Task에서 질문/응답은 Orca를 사용하고, 전달된 모든 메시지는 처리한 뒤 ack한다.
4. timeout, token 만료, 미변경 파일은 실패/종료 증거가 아니다. 긍정적인 failure/stopped 확인과 recovery 절차 없이 새 agent/Dispatch를 시작하거나 retry하지 않는다. 재시작 필요 시 같은 Task 권한을 확인하고 기존 evidence를 보존한다.
5. checkpoint는 재개 요약이지 runtime 권한을 대체하지 않는다. Task/Dispatch ID, 수정 파일, 완료/미완료, 마지막 확인 명령/결과, 질문 ID, 정확한 다음 행동을 쓰고 capability, 대화 본문, auth/raw log는 쓰지 않는다.
6. COM 열기·업로드·reset은 coordinator만 수행한다. 후보는 COM을 열지 않고, 원본/다른 worktree/Git history를 검색하거나 수정하지 않는다.

최종 checkpoint는 질문 `msg_1a0585d74a22`와 답변 `msg_5d56c1876c49`를 기록해야 한다. coordinator의 최신 결정은 이번 cohort mapping으로 반영했으며, source/runtime/hardware 증거의 `not_run` 상태는 유지한다.

## 향후 GUI 후보 검토 gate

최신 확인에서 여섯 `index.html` 경로가 모두 존재하며 coordinator는 Sol 제출 완료를 알렸다. 별도 GUI review Task의 독립 검토와 사용자 선택은 pending이다. 이 검토는 제출 상태와 파일 경로만 확인했으며 visual approval을 하지 않았다.

1. 독립 GUI review Task에서 각 후보의 `index.html`과 역할 handoff 완성 여부, 세 모델/레이아웃 차이를 점검한다. offline 단일 HTML, CDN/font fetch·React·Babel·실제 계정 값 금지 조건을 확인한다.
2. 여섯 후보 모두 동일 brief의 820×320 synthetic data를 사용하고 quota와 session token을 구별해야 한다. input/output/cache/reasoning/source total을 quota 잔여량처럼 합치지 않는다. usage/global reset/status, 정상·unknown·source stale·receive disconnected·error/last-good·WAITING·recovery를 selector로 확인한다.
3. handoff에 BOOT 탐색, 좌표/type/color, 출처·단위·조회 시각, clipping/가독성, 실물 폰트/RGB565/그리기·메모리 비용이 있어야 한다. global reset은 `codex-resets.com`의 source/time만 사용한다.
4. coordinator가 공통 썸네일/비교와 independent visual QA를 만들고 G1–G6 증거를 남긴다. browser review는 firmware/실물 성공이 아니며 미측정 hardware 점수는 null/not_run.
5. 6개 후보 비교 후 사용자가 선택하고 interface/설계를 확정한 뒤 제품 GUI 구현을 시작한다. 실제 LCD/BOOT/오류/복구 gate는 별도 실물 증거가 필요하다.

## 구현 전 조치

| 우선순위 | 담당 | 조치 / gate |
|---|---|---|
| P1 | PC + firmware owners | persisted mapping을 구현 handoff에 그대로 반영한다: fixed telemetry channel IDs, `snapshot_id`/local identity, exact duration metadata+wire ID/label, unknown duration, `local_runtime`와 fixture provenance. frozen schema 변경 없이 semantic test를 추가하고 source_total≠normalized_total 예제를 포함한다. |
| P1 | PC owner | available snapshot은 non-null `agent_id=codex-cli`/stable sanitized collector `host_id`를 출력하고 quota를 account scope로 유지한다. schema의 nullable 허용을 이용하지 않도록 validator negative case를 둔다. |
| P1 | firmware owner | `metric_kind` 분기, channel label, null quota field/reset_status 처리, GPIO0 BOOT/CS 초기화 근거를 host seam 및 실물 시험에 둔다. |
| P1 | GUI owners/coordinator | 여섯 GUI variant의 제출과 경로 존재는 확인됐지만 handoff completeness, independent visual QA 및 사용자 선택은 pending이다. 비교·선택을 제품 GUI 확정 gate로 둔다. |
| P2 | coordinator | source age/receive age, RTC/epoch 미확정 시 unknown, last-good 복구, 실제 Codex owner-only 시험 및 하드웨어 미측정을 별도 evidence로 판정한다. |

동결 `PRODUCT_CONTRACT.md`와 schema는 수정하지 않는다. 이번 cohort의 채널·duration·provenance 세부 규칙은 변경된 협업 설계에 기록된 결정을 따른다.

## 독립 검토 한계

실제 Codex 계정, session JSONL, auth material, COM/보드, 제조사 raw source를 읽지 않았다. 실제 app-server 응답 형태, runtime 파서 호환, 빌드, LCD/BOOT 전기 동작, USB 수신, 30초/24시간 지속성은 `not_run`이다. 본 검토의 schema 결과는 오직 synthetic data가 기존 JSON schema와 명시한 의미 조건에 맞는다는 증거다.
