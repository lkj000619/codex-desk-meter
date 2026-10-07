# LCD GUI 후보 6개 공통 brief

사용자 확정: AGY Gemini 후보 A/B/C와 Codex CLI `gpt-6.1-sol` 후보 D/E/F.
각 모델은 서로 다른 레이아웃·정보 우선순위·색감의 후보 3개를 만들며 사용자가 최종 선택한다.
별도 브랜드/디자인 시스템 없이 다양한 방향을 탐색한다. firmware 구현·업로드는 이 단계 밖이다.

## 화면과 검증 조건

- 실물 LCD 표시 영역은 정확히 820×320 CSS px, 가로. 프레임 밖에 preview 조작·설명을 둔다.
- quota percent/개인 리셋과 세션 token은 의미·단위·scope를 분리해 표시한다.
- usage / global reset / status 세 화면을 실제 BOOT 순환 버튼으로 탐색할 수 있는 HTML 시안.
  작은 버튼은 preview 조작이며 실물에 touch를 추가하는 설계가 아니다.
- usage 안에서 세션 토큰·quota를 동시에 읽거나 동등한 간단한 탐색을 제공한다.
  input/output/cached/reasoning/source total을 합산해 quota remaining처럼 표현하지 않는다.
- 정상, source stale, receive stale/disconnected, unknown/null, error/last-good, 초기 WAITING,
  recovery 상태를 preview 밖의 selector로 바꿀 수 있다. 단절 뒤 값을 유지하며 상태를 표시한다.
- 주요 수치는 멀리서 읽을 수 있게 크고, 단위/시간/출처는 충분한 대비로 배치한다.
  정해진 길이의 한두 provider/window만 그릴 수 있는 고정 하드코딩 GUI를 최종 계약으로 삼지 않는다.
- 글로벌 화면은 `codex-resets.com`, 조회 시각과 최근 reset/경과를 포함한다.
  forecast나 개인 quota reset을 global reset으로 표시하지 않는다.
- 시안의 data는 synthetic임을 preview 밖에 명시하고 실제 계정 값/대화를 쓰지 않는다.
- 오프라인 단일 HTML/CSS/native JS. CDN/font fetch·React·Babel·제품 서비스 설치 없이 동작한다.
  실제 LCD 가능한 폰트/타입 scale/RGB565색/그리기 영역/메모리 비용을 handoff에 남긴다.

## 후보 간 같은 synthetic 데이터

reference_time / observed_at: `2026-10-07T17:10:00Z` (KST 2026-10-08 02:10).
5h quota: used 42%, remaining 58%, duration 300min, resets_at `2026-10-07T18:20:00Z`.
weekly quota: used 18%, remaining 82%, duration 10080min, resets_at `2026-10-12T17:10:00Z`.
session: input 124800, output 16400, cached input 89600, reasoning output 2300,
source total 141200. Absolute limit/remaining and session percentages are unknown.
global source `codex-resets.com`, latest_reset_at `2026-10-07T10:00:00Z`,
captured_at `2026-10-07T17:10:00Z`. Global elapsed 7h10m at reference_time.
Errors/stale/unknown are controlled transformations of these samples, never fabricated fresh captures.

## 3개 후보 제출

각 후보 단일 `index.html`과 역할 `handoff.md`에 후보 이름·차이·선정 장단점·좌표/타입/색·
상태/BOOT 탐색·embedded 비용을 남긴다. 후보별 썸네일·종합 비교 페이지와 independent visual QA는
coordinator가 별도 Orca 검증 Task로 조율한다. 디자이너는 공유 viewer/manifest·다른 모델 파일을
변경하지 않는다. 심미적 결정은 각 모델이 하고 사용자는 6개 결과를 보고 선택한다.

각 역할 `checkpoint.md`는 시작·산출물·시험·질문·완료 전 갱신하며 native Task/Dispatch ID,
변경 파일, 마지막 확인 결과, 남은 작업, 다음 행동을 포함한다. 구현으로 넘어가지 않는다.
