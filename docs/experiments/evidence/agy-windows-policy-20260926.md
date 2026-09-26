# Windows AGY 실행 환경 수정 — 2026-09-26

현재 정책은 full-line regex로 조회·Git 상태/diff·IDF 고정 동작·unittest의
명령과 옵션을 제한한다. 단순 prefix가 Windows에서 옵션을 포함한 명령과 매칭되지
않을 수 있다는 [공식 문서](https://www.antigravity.google/docs/permissions/#cli-cross-platform-command-matching)를 확인했다.
`Get-ChildItem -Force`, 상대 경로와 제한된 조회 옵션을 허용하며, 명령 결합,
변수 치환, 상위/절대 경로, git history, flash, 임의 Python은 규칙에 포함하지 않는다.
기존 unittest의 포괄적인 인자 패턴도 제거했다. 이는 OS 격리 보장이 아니다.

새 회귀 시험은 실제 사용될 명령의 매칭과 범위 밖 명령의 비매칭을 확인한다.
이 검사는 AGY 엔진의 대체물이 아니므로 별도 실제 CLI smoke를 실행했다.
smoke v3에서 명령 5개가 실행됐지만 `idf.py --version`이 v1.0.3을 반환했다.
활성화의 PowerShell 함수가 자식 셸에 상속되지 않아 다른 실행 파일을 선택한 것이다.
실패하는 자식 PowerShell 시험으로 재현한 뒤 ASCII 도구 경로에 idf.py.cmd launcher를
생성하고 PATH 앞에 둬 자식도 고정 Python과 ESP-IDF 5.3.2를 실행하도록 수정했다.

전체 97개 시험 통과. 실제 CLI smoke v4는 `Get-ChildItem -Force`, `git status --short`,
`idf.py --version`, `python --version`, `Get-Content README.md -TotalCount 1`을 각각
정확히 실행했고 권한 거부 없이 ESP-IDF v5.3.2를 확인했다.
[smoke 결과·hash](agy-windows-policy-smoke-20260926.json)를 보존한다.
smoke는 별도 fixture 폴더와 새 대화에서 수행한 도구 진단이다. 제품 prompt를 사용하지
않고 제품 비교 결과에 포함하지 않는다. 모델 호출과 cache 사용량은 원본에 기록하며
provider cache 격리는 주장하지 않는다. wrapper의 전역 설정 복원도 완료됐다.

다음 pilot은 이 정책과 shim이 포함된 새 baseline 및 windows candidate를 사용한다.
기존 run/receipt를 덮어쓰지 않고, 실행 중 허용 정책이나 구현 지시를 추가하지 않는다.
