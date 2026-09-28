# AGY 별도 보완 실행 — 2026-09-28

사용자가 BOOT 버튼 무반응과 계속되는 화면 깜빡임을 확인하고 남은 작업 진행을 요청했다.
기존 원본 pilot은 보존하며, 평가 결과와 사용자 관찰을 제공하는 별도 remediation으로 진행한다.
기존 단일 prompt 정량 비교 cohort·agent 순위와 합산하지 않는다.

## 작성 책임과 실행 조건

- 제품 구현 수정은 AGY가 수행한다. 운영자는 원본 source 복사, 고정 보완 지시,
  권한 사전 검증, 실행·보존·독립 평가·사용자가 승인한 flash를 수행한다.
- 입력 제품 source는 기존 AGY implementation `9d52fa50529ae8020c6d1f54f193c7f74f875181`.
  canonical Git archive의 제품 파일 111개를 그대로 복사하고 hash로 확인했다.
  Git이 정규화한 dependencies.lock의 line ending을 사용하며 의미 변경은 없다.
- AGY 1.2.11 / gemini-3.8-flash-medium / 제한 120분 / 고정 prompt 1회.
- 실행 중 추가 지시나 구현 수정 없음. agent의 실제 보드 접근·flash는 금지한다.
  실물 시험은 실행 종료 후 운영자가 수행한다.
- source lineage·prompt·model·policy·preflight·usage·도구 로그는 각각 별도 보존한다.

## 이력

| 실행 | 상태 | 근거 |
|---|---|---|
| remediation r01 | 58.359초 후 환경 실패; 제품 변경 없음 | `.gitignore`를 포함한 checkout Git index 조회 거부. 전역 설정 복구·source clean·bundle 보존 확인 |
| dotfile 진단 1 | 첫 조회 성공, 두 번째 조회 거부 | 두 번째 명령의 현재 디렉터리 `.` 선택자가 규칙에 없었음. 원본 진단·usage 보존 |
| dotfile 진단 2 | 통과 | `.gitignore`/`.gitattributes` 및 현재 checkout 조회 모두 실제 AGY에서 실행. 전역 설정 복구 |
| remediation r02 | 659.234초 후 환경 실패; 부분 수정 보존 | 상태·GUI 코드 및 회귀 시험 수정 뒤 이미 읽기 허용된 vendor source의 절대 경로 셸 조회 거부. snapshot `6bb5d7fdfa4d6ba80c3eb5a6205767e942e13fc7` 보존 |
| source-read 진단 | 통과 | 기존 SDK/vendor source grant 안의 두 셸 조회가 실제 AGY에서 실행. 기존 자료 접근 범위 유지 |
| remediation r03 | 73.5초 후 환경 실패; 제품 추가 변경 없음 | checkout Git index의 파일명 패턴 조회 거부. source·로그·usage·전역 복구와 bundle 보존 |
| checkout read-pattern 진단 | 통과 | 실제 AGY에서 quoted Git 파일명 패턴, bounded Get-ChildItem filter, .gitignore 읽기 모두 실행. 진단 usage 별도 기록 |
| remediation r04 | 175.718초 후 환경 실패; 제품 추가 변경 없음 | `git grep "16:54:07"` 미등록으로 중단. source·로그·usage·전역 복구·bundle 보존 |
| code-search 진단 | 통과 | 실제 AGY에서 제한된 git grep·rg·Select-String·rg --files 4회 실행 및 전역 설정 복구 확인 |
| remediation r05 | 613.047초 후 환경 실패; 부분 수정 7개 파일 보존 | 파일을 지정한 `git diff` 조회 거부. AGY PC 수집 경로·상태/GUI·회귀 시험 변경, snapshot `ee511516dd700e81e42ae1e266301f044ad1e894`, 전역 복구·입력 불변·bundle 확인 |
| working-tree/result-validation 진단 | 통과 | 실제 AGY에서 파일 지정 diff, directory diff, diff check, 복수 status flag, validator의 결과 파일 인수 5회 실행. 전역 설정 byte 복구 확인 |
| remediation r06 | 실행 시작 | r05 AGY 부분 수정 포함 제품 파일 115개 canonical archive 보존. preflight 116개·host runtime·COM3·clean checkout, 실패/경고 0 |

정책 보완은 `git ls-files`의 checkout-root `.gitignore`, `.gitattributes`, 현재 디렉터리
선택자뿐이다. parent/absolute 경로·history·compound shell·임의 Python·설치·flash는
기존대로 제외한다. 실패를 재현한 회귀 시험을 먼저 추가한 뒤 규칙을 수정했고,
negative boundary 시험과 실제 AGY 진단을 통과했다.
기존 동결 정량 비교 baseline과 receipt는 변경하지 않는다. 새 정책을 정식 비교에
사용하려면 모든 후보의 공통 조건을 다시 동결·검증해야 한다.

r03에서는 native 파일 읽기에 이미 허용된 SDK·vendor source 안의 read-only 셸 조회를
같은 자료 범위로 맞췄다. 외부 source의 작성·실행, vendor build/backup, 사용자 파일,
parent traversal·명령 결합·설치·flash는 허용하지 않았다. 실패 재현 뒤 negative boundary
시험과 실제 AGY 진단으로 별도 확인했다. r02의 부분 수정은 AGY 작성이며 운영자는
추가 제품 코드를 작성하지 않았다. 시작 source와 각 시도의 시간·usage는 별도 기록한다.

r04에서는 checkout 내부 읽기 명령의 파일명 패턴·Git 메타파일 형태를 묶어서 검증했다.
파일명 pattern은 Git/PowerShell 조회 인수이며 `command(*)` 같은 실행 권한 wildcard가
아니다. parent/absolute non-granted 경로·`.git/config`·`.env`·shell 결합·치환은 negative
시험으로 차단 확인했다. `docs/hardware/vendor-source-index.json`의 실제 위치와 부분
수정 source에서 이어간다는 안내도 고정 보완 prompt에 명시했다. 후보 하나에만 이 정보를
제공하는 정식 비교는 수행하지 않으며, 모든 시도는 별도 보완 이력으로만 남긴다.

## 보완 범위

GPIO0/BOOT, LCD 렌더링 안정성, 데이터 부재·null·stale 표시, 실제 USB Serial/JTAG
수신, PC fixture collector·정규화·frame·재연결, 시간 경과/300초 stale 처리,
provider 전체·오류·복구 시험, 선택 IMU 기능과 최종 구조화 결과 제출을 포함한다.
독립 평가와 실물 시험 없이 제품 합격을 선언하지 않는다.

## 기록 위치

- [첫 보완 시작·사용자 관찰](agy-remediation-launch-20260928.json)
- [r01 실패 원본·측정·hash](agy-remediation-r01-result-20260928.json)
- [r02 제한 정책·진단·사전 검증](agy-remediation-policy-preflight-20260928.json)
- [r02 실패·부분 구현·측정](agy-remediation-r02-result-20260928.json)
- [r03 source 조회·진단·사전 검증](agy-remediation-source-read-preflight-20260928.json)
- [r03 실패 원본·측정](agy-remediation-r03-result-20260928.json)
- [r04 조회 명령군·진단·사전 검증](agy-remediation-read-groups-preflight-20260928.json)
- [기존 남은 작업 점검](agy-remaining-work-review-20260928.md)
- 현재 raw root: `C:/Espressif/benchmark-remediation/20260928-agy-remediation-r06`.

이 문서는 시작 시점의 진행 기록이다. 실행 종료 판정은 별도 결과 보고서로 추가한다.

## r05 실행 준비 및 하드웨어 대기

제한된 코드 검색 명령군을 실패 재현 시험 후 보완했다. `git grep`의 파일 경로는 `--` 뒤로 제한하고, rg·Select-String도 checkout 또는 이미 허용된 source 읽기 범위로 제한했다. 임의 명령·history·외부 변환기·권한 우회는 허용하지 않았다. 실제 AGY 진단의 4개 명령과 usage를 별도로 기록했다.

현재 COM3 미연결은 보드 업로드의 미충족 조건이다. `-RequireHardware` 사전 검증 실패 원본을 보존한 뒤, 실제 보드에 접근하지 않는 AGY 코드 보완용 사전 검증은 0 실패·1 경고로 통과했다. 전체 제품 합격이나 보드 검증 통과로 처리하지 않는다. 실행 중 추가 지시 없이 종료 후 독립 평가를 진행한다.

- [r04 실패 및 보존](agy-remediation-r04-result-20260928.json)
- [r05 검색 명령·실제 진단·사전 검증](agy-remediation-search-preflight-20260928.json)

## r06 실행 준비

사용자가 보드를 다시 연결했고, COM3의 VID/PID 및 serial이 이전 보드와 일치함을 확인했다.
연결 사실은 버튼·LCD·통신 기능 합격을 의미하지 않는다. r06 preflight는 COM3 필수 조건을
포함해 0 실패·0 경고였다.

Git 변경 조회의 제한된 파일 경로·옵션 조합과 기존 결과 validator의 파일 인수만 보완했다.
bare revision/branch, history, 외부 변환기, 파일 출력, parent/비허용 absolute 경로와 shell
결합은 negative 시험으로 거부했다. 실제 AGY 진단 5개 명령의 출력과 별도 usage를 보존했다.

115개 source 파일에는 AGY가 보완한 maintainer 제공 host oracle 모듈
`scripts/host_device_pipeline.py`를 추가해 추적한다. 모든 제품 source는 r05 canonical
archive와 byte 일치하며 운영자는 제품 구현을 수정하지 않았다. r06 prompt는 원본
업로드 결과의 결함 기록과 이미 작성된 AGY 부분 수정을 구분하며, 실행 중 피드백은 없다.
이번 보완 이력은 최초 단일 prompt 정량 비교·순위에서 계속 제외한다.

- [보드 재연결 확인](agy-remediation-board-reconnected-20260928.json)
- [r05 실패·부분 구현·보존](agy-remediation-r05-result-20260928.json)
- [r06 변경 조회·실제 진단·사전 검증](agy-remediation-working-tree-preflight-20260928.json)
