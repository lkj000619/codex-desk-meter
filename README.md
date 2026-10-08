# Codex Desk Meter — Orca 협업 실험

PC에서 Codex 세션 토큰과 개인 사용한도·리셋 시각을 수집해 USB로 ESP32에 전달하고,
820×320 LCD에서 읽기 쉽게 표시하는 새 구현이다. 기존 동결 입력에서 시작하며
역할별 모델과 Orca 오케스트레이션, LCD UX/UI 디자인을 별도 실험 조건으로 기록한다.

- [범위·역할·데이터 설계](docs/design/2026-10-08-orca-harness.md)
- [진행 계획](docs/plans/2026-10-08-orca-harness.md)
- [현재 상태](docs/experiments/next-comparison-readiness.md)
- [문서 지도](docs/DOCUMENTATION_MAP.md)
- [GUI 6개 비교](opendesign/comparison.html) · [독립 검토](docs/agent-runs/orca-luna/gui-review.md)

사용자는 **B · Swiss Studio Meter**를 선택했다. 최초 시안 검토를 보존하고 선택 B의 결함을
보완하며 PC 수집기를 구현 중이다. localhost 서버가 실행 중이면
[비교 화면](http://localhost:8289/opendesign/comparison.html)을 브라우저에서 열 수 있다.

기존 단독 비교 실험의 원본과 결과는 기존 브랜치에 보존되어 있다.
이번 브랜치는 새로운 확장 과제이며, 기존 비교의 반복 표본으로 합산하지 않는다.
