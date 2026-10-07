# Orca 협업 실험

- 문서 역할과 원본은 [문서 지도](docs/DOCUMENTATION_MAP.md)를 따른다. 계획은 `docs/plans/`, 설계는 `docs/design/`에 작성한다.
- 이번 범위·역할·완료 조건은 [협업 설계](docs/design/2026-10-08-orca-harness.md)를 먼저 읽는다. 동결 과제의 독립 실행·120분·질문 금지·fixture 전용 규칙은 이번 사용자 지시로 대체되며, 제품 의미·하드웨어 사실·원본 입력은 보존한다.
- 실행은 실제 Orca Run/Task/Dispatch로 조율한다. 주입된 worker preamble의 질문·메일 확인·heartbeat·worker_done 명령을 따른다. 다른 하네스의 하위 에이전트로 대체하지 않는다.
- 자신의 Task에 지정된 파일만 수정한다. 원본 57개 입력과 다른 역할 파일의 변경은 coordinator에게 요청한다. Git commit·branch 전환·push는 coordinator만 수행한다.
- 새 checkout의 입력과 이번 팀이 만든 결과, 지정 SDK·제조사 raw source만 읽는다. 다른 worktree·과거 제품·Git history·운영자 자료를 검색하지 않는다.
- PC 수집기는 자신의 프로그램 실행 중 허용된 Codex token metadata만 읽는다. 개발·시험에는 비식별 synthetic 입력을 사용한다. 사용자 대화·인증 파일·전체 세션 로그를 출력·복사·커밋하지 않는다. 실계정 시험은 coordinator가 수행한다.
- SDK/제조사 source는 하드웨어 자료에 지정된 경로를 사용한다. COM 포트 열기·업로드·리셋은 coordinator만 수행한다.
- 모호한 데이터 의미·인터페이스·실행 권한은 Orca ask로 질문한다. 차단되지 않은 자신의 작업은 계속한다. 근거가 없는 값과 결과는 unknown/null/not_run으로 기록한다.
- 사용자가 실행 중 직접 승인하지 않도록 자동 승인 옵션을 요청했다. coordinator는 AGY `--dangerously-skip-permissions`, Codex `--dangerously-bypass-approvals-and-sandbox`를 실제 argv에 적용하고 확인한다. 작업 범위·파일 소유권·개인 정보·COM 경계는 위 지침을 따른다.
