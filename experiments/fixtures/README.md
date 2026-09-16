# 실험 fixture

이 디렉터리의 파일은 에이전트 비교를 재현하기 위한 공개·합성 입력이다.

- `personal-usage.json`은 개인 계정 데이터를 포함하지 않는 합성 사용량이다.
  PC 파트의 Codex 예시 창은 5시간 세션 창(`five-hour`)과 주간 세션 창(`weekly`)이며,
  각 창의 `percent_used`/`percent_remaining`·`resets_at`을 C3 표시 입력으로
  사용한다. 이 파일은 adapter 입력용이며 `usage-snapshot.schema.json` 직접 검증
  대상이 아니다. 스키마 검증은 `providers/*.json`으로 수행한다. 타 provider는
  각자 제공하는 window 목록을 그대로 사용한다.
- `codex-reset-forecast.json`의 `confidence`는 fixture-only 주석이며
  `GlobalResetSnapshot` 스키마 필드가 아니다. C5 판정은 24h/48h 퍼센트와
  `forecast_is_schedule: false`로만 수행한다.
- `codex-reset-forecast.json`은 `codex-reset.com` forecast 응답의 필요한 필드만
  고정한 스냅샷이다.
- `codex-resets-history.json`은 `codex-resets.com`의 이력 출처를 별도로 표현한다.

실험 중 live API를 사용할 때도 fixture 실행을 먼저 끝내고, 조회 URL·시각·HTTP
상태·응답 해시를 함께 기록한다. fixture의 날짜가 지나도 자동으로 갱신하지 않는다.
