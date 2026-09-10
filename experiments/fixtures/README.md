# 실험 fixture

이 디렉터리의 파일은 에이전트 비교를 재현하기 위한 공개·합성 입력이다.

- `personal-usage.json`은 개인 계정 데이터를 포함하지 않는 합성 사용량이다.
- `codex-reset-forecast.json`은 `codex-reset.com` forecast 응답의 필요한 필드만
  고정한 스냅샷이다.
- `codex-resets-history.json`은 `codex-resets.com`의 이력 출처를 별도로 표현한다.

실험 중 live API를 사용할 때도 fixture 실행을 먼저 끝내고, 조회 URL·시각·HTTP
상태·응답 해시를 함께 기록한다. fixture의 날짜가 지나도 자동으로 갱신하지 않는다.
