# Orca 협업 실험 설계

상태: 범위·역할·인터페이스 확정. GUI 6개 작성 후 사용자가 B · Swiss Studio Meter를 선택했다.
2026-10-08 사용자 변경: OpenCode 대신 AGY Gemini와 Codex CLI `gpt-6.1-sol`이
각각 GUI 후보 3개, 총 6개를 만든다. 사용자가 선택한 뒤 제품 구현에 반영한다.

2026-10-08 실제 선택 답변: **B · Swiss Studio Meter — 밝은 계기판**.
선택 B의 last-good 전이, 원본/정규화 토큰 합계, 가변 quota 목록을 보완·검증한 뒤 GUI를 구현한다.
PC 수집기는 이미 확정한 인터페이스로 병행 구현한다. A/C 및 D/E/F는 비교 시안으로 보존한다.

## 목표와 적용 범위

책상 위 LCD에서 Codex 세션의 실제 토큰, 개인 사용한도와 리셋, 글로벌 리셋을 구분해
확인할 수 있는 Version 2 제품을 새로 구현한다. 동결 baseline은
`272875140d1998d458e26fdb2f6deab5e5d8f7b5`, 입력 57개는 바이트 그대로 보존했다.
이전 후보 구현은 새 checkout에서 제거했으며 기존 worktree·원본 결과는 변경하지 않았다.

사용자는 역할별 팀·Orca 조율·새 구현·UX/UI 디자인·PC 세션 수집을 요청했다.
동결 과제의 독립 단일 에이전트, 120분/3회, 질문 금지, fixture 전용, builtin-only 제한은
이번 별도 cohort에 적용하지 않는다. 총 작업시간 제한은 없으며 오류에 대한 무한 재시도 대신
원인·실행 상태·다음 소유자를 기록한다. 사용자 질문은 필요한 의존 작업만 대기시킨다.
기존 제품 계약의 C/I/F·정합성·stale·CRC·시퀀스·안전한 오류 처리는 그대로 적용한다.

이번 실험은 모델·역할·디자인 스킬·live 범위가 함께 달라진다. 기존 단독 결과와의 차이를
오케스트레이션 하나의 효과로 단정하거나 기존 반복 비교·비용 합계에 넣지 않는다.

## 역할과 파일 소유권

| 역할 | 실행 도구·모델 | 소유 파일 | 제출 |
|---|---|---|---|
| 조율·사용자 질의·실물 시험 | 현재 coordinator | 본 계획/설계·AGENTS·실험 식별자·운영 증거 | DAG·판정·측정·동결·업로드 |
| 펌웨어·통합 | Codex Sol (`gpt-6-sol`) | `firmware/`, `tests/firmware/`, `docs/agent-runs/orca-sol/` | BSP·receiver/cache·LCD 구현·host C seam·빌드 |
| PC 수집·전송 | AGY Flash (`gemini-3.8-flash-medium`) | `pc/`, `tests/pc/`, `docs/agent-runs/orca-flash/` | 세션·quota 수집기·정규화·sender·자체 시험 |
| LCD UX/UI 후보 A/B/C | AGY Gemini, 기존 승인 Flash 설정 | `opendesign/mockups/gemini-{a,b,c}/`, `docs/design/lcd/gemini/` | 후보 3개·상태/탐색·좌표·구현 handoff |
| LCD UX/UI 후보 D/E/F | Codex CLI `gpt-6.1-sol` | `opendesign/mockups/sol61-{a,b,c}/`, `docs/design/lcd/sol61/` | 후보 3개·상태/탐색·좌표·구현 handoff |
| 독립 검증 | Codex Luna (`gpt-6-luna`) | `tests/integration/`, `docs/agent-runs/orca-luna/` | 계약/실제 코드 검증·결함·미측정 조건 |

모델 ID는 희망 설정이며 native launch의 실효 설정과 첫 응답을 확인한 뒤 실제 모델로 기록한다.
사용 불가·권한 거부는 임의 모델 대체 없이 질문한다. 같은 worktree에서 서로 다른 파일을
소유하며 build 폴더와 Git 조작은 Sol/coordinator에게 각각 한 명의 소유자를 둔다.
검증자는 구현 파일을 수정하지 않고 결함을 구현 담당자에게 돌려보낸다.

## 데이터와 PC 프로그램

```text
Codex 로컬 세션 token metadata → session_telemetry ┐
Codex app-server quota 읽기 → quota_window       ├→ 정규화 → cdm/1 USB → 검증/cache → LCD
동결 fixture·글로벌 리셋 입력                     ┘
```

PC 프로그램의 첫 결과물은 Windows에서 실행하는 CLI 수집·watch·수동 갱신 프로그램이다.
세션 선택/목록과 구조화 결과를 제공하고, 새 PC 트레이 앱·별도 설치 서비스는 요구하지 않는다.
실제 수집과 fixture 실행을 명시적으로 선택하며 provenance로 구분한다.

- 세션 입력·출력·캐시·reasoning·원본 total은 Codex 로컬 `event_msg/token_count`의
  누적값을 읽는다. 누적 event를 반복 합산하지 않고, 재시작·부분 line·축소/교체·복수 세션을
  처리한다. 개발용 입력은 metadata만 있는 synthetic JSONL이다. 실제 세션 내용은 보관하지 않는다.
- 프로그램은 대상 세션 ID/파일을 명시적으로 선택하고 latest 선택 정책을 문서화한다.
  세션 토큰은 `metric_kind=session_telemetry`로 별도 snapshot/window에 표현하며
  known used_units와 unknown limit/remaining/percent를 구분한다. 원본 total을 보존하고
  정규화 합계=input+output, cached/reasoning은 이미 포함된 부분으로 취급한다.
- 개인 quota는 native `codex app-server`의 읽기 전용 `account/rateLimits/read`를 우선한다.
  기존 Codex 로그인이 처리하며 수집기가 auth 파일·cookie·키를 직접 읽지 않는다.
  초기화 후 읽기만 수행하고 thread 생성·turn 실행·reset 권리 소비·메일 발송은 수행하지 않는다.
- primary/secondary 창은 제공된 duration·percent·resets_at으로 식별한다. 5시간/주간이라고
  하드코딩해 다른 duration을 재명명하지 않는다. percent_remaining=100-used_percent는
  percent에서만 도출하고 절대 잔여 token 수를 추정하지 않는다.
- 원본 token event 시각과 quota 응답 획득 시각을 각각 보존한다. 로그 fallback은 마지막 관측값으로
  표시하고 새 읽기 시각으로 신선하게 만들지 않는다. source age와 receive age는 독립적이다.
- session telemetry와 계정 quota는 합산하지 않는다. 계정 quota를 각 세션에 복제해 합산하지 않는다.
  지원되지 않는 값·오래된 값·제공자 실패는 unknown/stale/error 및 last-good 상태로 유지한다.
- 기존 UsageSnapshot와 cdm/1 schema를 재사용하고 frozen schema를 변경하지 않는다.
  표현이 불가능한 필드는 의미를 비틀기 전에 coordinator에게 인터페이스 질문을 한다.

quota 공식 원본: [Codex App Server](https://learn.chatgpt.com/docs/app-server).
로컬 로그 구조는 현재 설치된 CLI `0.159.2`에서 관측한 형식이며 고정된 공개 API로 단정하지 않는다.
수집기는 지원 형식을 검사하고 변경 시 명시적으로 실패해야 한다.

2026-10-08 인터페이스 결정 (`msg_1a0585d74a22` 질문 / `msg_5d56c1876c49` 답변):
동결 schema의 `session_telemetry` snapshot에서 `windows`를 토큰 구성요소 채널로 사용한다.
`window_id`는 `input`, `output`, `cached_input`, `reasoning_output`, `source_total`,
`normalized_total`을 구분하고, 각 채널의 `used_units`는 해당 토큰 수다. quota 창과 혼동하지
않도록 `metric_kind`를 먼저 분기하며 limit/remaining/percent/reset은 모두 null로 둔다.
cache는 input에, reasoning은 output에 포함된다. 두 부분 수치를 합계에서 더하거나 빼지 않는다.
세션 식별자는 snapshot 식별자와 로컬 metadata에 보존한다.

quota 창은 제공된 duration을 정확한 초로 보존하고 `primary-18000s` 같은 안정적인 ID와
정확한 duration label로 전송한다. typed duration은 로컬 metadata에 둔다. duration 미제공은
unknown이며 5시간/주간으로 추정하지 않는다. available source의 `agent_id=codex-cli`,
`host_id`는 안정적인 비식별 수집 PC alias다. 이 둘은 수집 맥락이며 계정 quota의 범위를
세션별 quota로 바꾸지 않는다. 계정 식별 가능 시 `account_profile_id`로 구분한다.
로컬 JSONL과 native app-server RPC는 모두 `source_kind=local_runtime`으로 표시하고
정확한 입력 경로 종류는 로컬 provenance에 구분한다. synthetic 입력은 `fixture`다.
이 결정은 이번 cohort에만 적용하며 동결 입력은 변경하지 않는다.

## LCD 디자인과 하드웨어

실제 LCD는 820×320 가로다. quota와 세션 token을 구분해 한눈에 읽고, 글로벌 리셋·상태를
BOOT 순환으로 확인한다. 긴 목록은 잘림 대신 명시적인 탐색을 제공한다.
정상·unknown·stale·error·단절·재연결·대기 상태의 표현, 조회 시각·단위·출처를 모두 설계한다.
브라우저 mockup은 디자인 증거이며 firmware·실물 성공을 대신하지 않는다.

OpenDesign은 동명 전체 앱 대신 portable Markdown skills
[`manalkaff/opendesign`](https://github.com/manalkaff/opendesign)의 pinned 원본을 검토해
프로젝트 내부 `tools/opendesign/`에서 적용한다. 고정 commit은
`cecd9bb6b59408cb96a3974449b8e6ef9f5b17bb`이며 원본과 embedded 적용 지침을 분리한다.
별도 디자인 시스템은 없으므로 디자이너가 필요한 디자인 방향을 구체적인 시안과 함께 질문한다.
웹 폰트·CSS 효과는 실제 LCD에 옮길 수 있는 폰트·색·메모리·그리기 비용으로 바꾸어 제출한다.

SDK v5.3.2, 제조사 raw source, ST7701 timing, PSRAM framebuffer, active-low backlight GPIO6,
LCD CS/BOOT 공유 GPIO0를 [보드 자료](../hardware/version-2-capabilities.md)로 확인한다.
특히 BOOT 런타임 입력과 LCD 초기 제어의 공유 핀을 검증한다. 온보드 기능 후보 정확히 3개와
선택 1개는 Sol이 설계하며 핵심 화면·통신을 약화하지 않는다.

## 의존 순서와 완료 경계

1. 두 디자인 담당자가 GUI 후보를 각각 3개 작성하고 Luna가 요구·시험 검토를 병행한다.
2. 실제 launch 모델·설정과 후보별 차이·상태/탐색·embedded 구현 근거를 기록한다.
3. 6개 후보를 비교할 수 있게 제시하고 사용자 선택과 인터페이스 검토를 반영해 설계·계획을 확정한다.
4. PC 프로그램·firmware를 별도 파일에서 구현하고 같은 snapshot/wire로 host 통합 검증한다.
5. Luna 독립 검증의 결함은 각 구현자에게 전달한다. 수정 뒤 필요한 검사를 재실행한다.
6. 검증된 commit·binary/hash를 동결한 뒤 coordinator만 COM3에 업로드하고 공통 데이터와
   owner-only 실제 Codex 수집을 시험한다. BOOT·30초·복구·지연·상태를 사용자 실물 관측과 연결한다.
7. worker_done·모델·실행시간·제공되는 token·질문·실패·설계/동작 증거를 기록한다.
   모든 Task와 worker 소유권을 정리하고 실물 미검증은 그대로 남긴다.

완료는 build와 host 검증, 실제 fixture/live PC→장치 연결, LCD/BOOT와 오류·stale·복구 관측을
각각 근거로 판정한다. full product/24시간 live 안정성은 해당 측정이 끝나야 합격이다.
기존 RM 도달, 시안 만족, PC write 완료만으로 제품 완료를 선언하지 않는다.

## 중단 안전장치

실행 상태는 Orca native Run/Task/Dispatch가 소유한다. 체크리스트와 역할별 `checkpoint.md`는
세션 초기화 후 읽을 재개 요약이며 runtime의 실행·종료 상태를 대체하지 않는다.
각 역할은 작업을 시작할 때, 산출물/시험 체크포인트마다, 질문·완료 전에 checkpoint를 갱신한다.
checkpoint에는 실제 Task/Dispatch ID, 수정 파일, 완료/미완료, 마지막 검증 명령·결과,
정확한 다음 행동과 질문 ID를 쓰고 secret capability나 전체 개인 대화는 쓰지 않는다.
coordinator는 수락한 worker_done·결정·동결/업로드마다 계획과 재개 파일을 갱신하고 commit한다.

재개자는 [재개 절차](../experiments/orca-harness-resume.md)를 먼저 따른다. 기존 Run에 연결한 뒤
살아 있는 worker와 미응답 질문·미확인 worker_done을 확인한다. timeout/토큰 만료/파일 미변경만으로
새 agent를 시작하지 않는다. Git에는 source·문서·비식별 증거를 보관하고 개인 원본 로그는 제외한다.
