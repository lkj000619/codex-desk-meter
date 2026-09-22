# 실험 fixture

이 디렉터리의 파일은 에이전트 비교를 재현하기 위한 공개·합성 입력이다.

- `personal-usage.json`은 개인 계정 데이터를 포함하지 않는 합성 사용량이다.
  PC 파트의 Codex 예시 창은 5시간 세션 창(`five-hour`)과 주간 세션 창(`weekly`)이며,
  각 창의 `percent_used`/`percent_remaining`·`resets_at`을 C3 표시 입력으로
  사용한다. 이 파일은 adapter 입력용이며 `usage-snapshot.schema.json` 직접 검증
  대상이 아니다. 스키마 검증은 `providers/*.json`으로 수행한다. 타 provider는
  각자 제공하는 window 목록을 그대로 사용한다.
- `codex-reset-forecast.json`은 과거 `codex-reset.com` 전망 스냅샷으로, 파서 호환·회귀용으로만
  보관한다. `confidence`·`forecast_*`는 표시 입력이 아니며, C4~C6 표시·판정에 사용하지 않는다.
  C5는 경과 시간 또는 default 화면으로만 판정한다.
- `codex-resets-history.json`은 `codex-resets.com`의 이력 출처를 별도로 표현한다.
  C4/C5 표시 계층의 기준 입력이다.

정식 E2E benchmark의 제품 입력은 고정 fixture다. 이 cohort에서는 live API를
허용하지 않으며, live API는 owner 승인 후속 cohort
`version-2-live-integration-v1`에서만 별도로 사용한다. baseline YAML의
`live_api_allowed_after_fixture: false`와 이 문서의 fixture-only 경계가 일치한다.
fixture가 있어도 live 조회나 자격증명 사용을 자동 승인하지 않는다.
