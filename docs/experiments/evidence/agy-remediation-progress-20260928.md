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
| remediation r06 | 148.235초 후 환경 실패; 제품 추가 변경 없음 | `rg` 검색의 `--` 구분자 조합 거부. 입력 불변·전역 복구·bundle 보존 |
| r07 준비 | 실제 AGY 진단 실패로 보완 실행 시작 안 함 | Python 시험에서만 지원되는 검색 규칙의 negative lookahead 사용. 원래 준비 snapshot·정책·사전 검증·실패 진단 보존 |
| search-dialect 진단 2 | 통과 | RE2 호환 문자 클래스로 제한을 유지하고 실제 AGY에서 검색 구분자·옵션·문맥 출력 8회 확인. 전역 설정 byte 복구 확인 |
| remediation r08 | 107.859초 후 환경 실패; 제품 추가 변경 없음 | `git log -n 5` 조회 거부. 입력 불변·전역 복구·bundle 보존 |
| local-metadata 진단 | 통과 | 준비 커밋 두 개만 있는 진단 checkout에서 제한된 metadata 조회 3회 및 전역 설정 byte 복구 확인 |
| remediation r09 | 225.906초 후 환경 실패; 제품 추가 변경 없음 | 자체 CTest 4개·legacy 29개·PC regression 9개 통과 후 terminal `git grep` 구분자 조회 거부. 입력 불변·전역 복구·bundle 보존 |
| standard query/test 진단 | 권한 8회 통과; 기대 동작 7회 확인 | 실제 AGY에서 8개 명령 모두 dispatch. `git diff --unified 3 -- .`는 운영자 지정 인수 표기 오류이며 diff 성공이 아님. 진단 unittest 실제 1개 실행 및 전역 설정 byte 복구 확인 |
| remediation r10 | 940.172초 후 완주; 제품 합격 아님 | snapshot `f2063cfbda418f4003457a945e6f585731c5a58c`. 독립 빌드·CTest 4·PC 9·legacy 29·trusted 결과 형식 통과. 독립 수신/상태/송신 번호 시험에서 추가 결함 재현. 아직 업로드 안 함 |
| remediation r11 | 986.688초 후 환경 실패; 부분 수정 보존 | `python -c` 미등록 명령 거부. AGY 14개 source/test 파일 수정, snapshot `83014daa61fa7f836ed6b36a5664157eec8de566`, 전역 복구·입력 불변·bundle 확인. 독립 평가에서 개선과 남은 실패를 각각 기록 |
| remediation r12 | 1109.016초 후 완주; 제품 합격 아님 | snapshot `fb3b8e95c207fb9caff5869ed946cd80c4dcb715`. 독립 host/IDF 빌드·CTest·Python·legacy·trusted validator 통과, source 변경 없음. 추가 모듈 통합 검증에서 기본 fixture 거부·거부 후 상태 변경·잘못된 수치/단위 수락 재현 |
| remediation r13 | 241.5초 후 환경 실패; 제품 변경 없음 | `git grep -- "--candidate"` literal 조회 거부. snapshot `2210c2b0725fc0b2472be43748dac6829abfd427`; 입력 불변·전역 복구·bundle 보존 |
| literal option-pattern 조회 진단 | 통과 | 명시적 `--` 뒤의 제한된 dash 문자열 조회만 등록. 실제 AGY query 3회·전역 설정 byte 복구, 부모 경로/변환기/명령 결합 거부 유지 |
| remediation r14 | 실행 시작 | 제품 파일 116개가 r12 완성 source와 동일. preflight 121개·COM3·clean checkout·준비 commit 2개 및 실제 AGY query 확인. 전체 계약과 원본 순위 제외 유지 |

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
- 현재 raw root: `C:/Espressif/benchmark-remediation/20260928-agy-remediation-r10`.

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

## r08 검색 문법·엔진 차이 보완

r06은 검색 구분자 조합 때문에 중단됐고 제품 변경은 없었다. r07 준비 정책에는 quoted
옵션 위장을 차단하는 negative lookahead가 추가됐으나, Python 시험 통과와 달리 실제 AGY
진단에서는 규칙이 동작하지 않았다. 보완 agent는 시작하지 않고 해당 준비 원본을 보존했다.

AGY 실행 파일의 Go regexp/syntax 표식과 [RE2 문법](https://github.com/google/re2/wiki/Syntax)을
대조하면 해당 표현 미지원이 원인이라는 추론을 뒷받침한다. AGY 내부 소스 확인은 하지
못했다. 같은 제한을 문자 클래스로 표현한 뒤 실제 CLI 진단 8개 명령이 모두 실행됐으며,
unsupported lookaround/backreference를 차단하는 사전 시험도 추가했다.

r08은 동일 AGY 제품 부분 소스를 사용한다. 하드웨어 접근·설치·history·명령 결합·임의
변환기 허용은 추가하지 않았다. 원본 업로드 결과를 해결·합격으로 승격하지 않으며 실행
종료 후 독립 빌드·시험과 보드 관찰을 진행한다.

- [r06 실패·보존](agy-remediation-r06-result-20260928.json)
- [r07 준비 반려·원본 보존](agy-remediation-r07-preparation-20260928.json)
- [r08 실제 검색 진단·사전 검증](agy-remediation-search-dialect-preflight-20260928.json)

## r09 현재 준비 메타데이터 조회

현재 isolated checkout에는 Git archive를 받아 만든 준비 커밋 두 개만 존재한다.
원본 실험 Git history·실패 run history는 포함하지 않는다. 제한된 `git log`의 현재
메타데이터 조회(최대 5개, 고정 옵션)만 추가하고, 실제 AGY 진단 3회로 확인했다.
bare/unbounded log·다른 ref·`--all`·patch/custom format·경로·shell 결합은 계속 거부한다.
실행 controller는 시작 전 commit 수가 정확히 두 개인지 확인하며, 일치하지 않으면
시작하지 않는다. 이 조건은 별도 보완에만 사용하고 정량 비교의 동결 조건에 반영하지 않는다.

AGY 제품 source는 변경하지 않았으며 r05 부분 수정에서 계속 이어간다. 보드 연결은
유지된 상태로 준비 시험을 통과했고, 제품 빌드·회귀 시험·BOOT/LCD/USB 실제 동작 판정은
AGY 종료 후 독립 평가에서 확인한다.

- [r08 실패·보존](agy-remediation-r08-result-20260928.json)
- [r09 제한된 local metadata 진단·사전 검증](agy-remediation-local-metadata-preflight-20260928.json)

## r10 표준 조회·시험 옵션 묶음

r09의 자체 시험은 이전 AGY 부분 수정 소스에서 CTest 4개·legacy evaluator 29개·PC
regression 9개가 실행돼 통과했다. 이는 GPIO0/BOOT와 실제 USB 수신·LCD 안정성의
실물 검증 근거가 아니며, 아직 개선 펌웨어를 보드에 올리지 않았다.

pathspec 없이 끝나는 Git grep의 `--`, 숫자로 제한된 diff 문맥 옵션, scoped unittest
filename pattern/long option, Python unbuffered flag를 기존 명령군 안에서 보완했다.
조회 자료 범위·실행 명령군·실물 보드 권한을 추가하지 않았다. 실제 AGY 진단 8회에서
모든 명령의 권한 검사가 통과했고 unittest는 실제 1개를 수행했다. `--unified 3`는 Git이
`3`을 revision으로 해석해 인수 오류가 났으며, 기대 동작 확인은 7/8이다. 올바른
`--unified=3` 형태는 운영자의 직접 Git 조회에서 확인했다. 진단 `diff --exit-code`의 1은
의도적으로 존재하는 진단 변경분에 따른 정상 반환이며 permission failure와 구분했다.

제한 경계 시험 후 preflight 120개·COM3·host runtime·clean checkout을 통과했다.
r10은 같은 AGY 부분 소스를 받고 단일 고정 prompt로 진행한다. 진단 기록 생성 시 해당
Git 인수 오류를 검출했으나 이후 실행 호출이 진행된 운영 절차 오류도 기록한다. 실행 중
정책·prompt를 바꾸거나 추가 지시를 전달하지 않았으며, 현재 결과를 진단 8개 기능 통과로
표현하지 않는다. 운영자의 제품 코드
수정이나 실행 중 추가 지시는 없으며 원본 성적·순위와 분리한 보완 기록이다.

- [r09 실패·자체 시험·보존](agy-remediation-r09-result-20260928.json)
- [r10 표준 옵션·실제 진단·사전 검증](agy-remediation-standard-options-preflight-20260928.json)

## r10 완주와 독립 검증, r11 보완 입력

r10은 고정 prompt 한 번으로 종료했고, 입력 불변·AGY 변경 snapshot·bundle·전역 설정 복구를
확인했다. fresh archive의 host/ESP-IDF 빌드, CTest 4개·PC regression 9개·legacy 29개,
운영자 trusted validator는 통과했다. 독립 빌드가 제품 source를 바꾸지 않았음도 hash로 확인했다.
운영자의 첫 Windows IDF 호출 오류는 후보 오류와 구분해 원본 기록을 보존했다.

그 이후 실제 제품 모듈을 호출한 별도 시험과 대상 object 분석에서 다음 결함을 확인했다.

- 대상 수신 함수 스택 20,144바이트에 비해 태스크 스택은 4,096바이트.
- CRLF 수락 및 oversized line의 delimiter 없는 suffix를 새 프레임으로 수락.
- 오류 응답이 last-good windows 1개를 0개로 덮어씀. 오래된 source가 tick 이후 fresh가 됨.
- 수신은 5개 provider를 파싱하지만 상태는 첫 provider만 보존. sequence 거부 후에도
  ESP 경로가 수신 시각을 갱신하고 Accepted 로그를 출력하는 source 경로 확인.
- PC production 클래스와 실제 명령 경로의 연결 누락. 동시 예약 32회에서 성공 17회 중
  고유 번호는 4개(중복 13개), write 오류 15개. 기존 번호 11을 초기화로 1로 되돌릴 수 있음.
- F9 JSON과 원래 후보 세 개·실제 IMU pin 설명이 불일치. 자체 점수는 운영자 평가가 아님.

이 결과는 제품 합격이 아니며, 해당 binary는 업로드하지 않았다. 보드는 사용자 재연결 후
COM3·VID/PID·serial이 기존 장치와 일치했다. BOOT/LCD/IMU 실물 동작은 여전히 미검증이다.

r11은 r10 canonical 제품 source를 그대로 받아 위 결함을 시작 전에 한 번만 제공한다.
제품 수정·회귀 시험 작성은 AGY가 수행한다. 운영자는 독립 평가 도구와 기록만 작성했다.
실행 중 추가 지시·정책 변경·제품 수정은 하지 않는다. 보완 시간·usage와 결과는 최초 단일
prompt 성적에 합산하지 않는다. 잘못된 Git `--unified 3` 표기는 회귀 실패 재현 뒤 정책에서
제외했고, 올바른 `--unified=3`와 기존 `-U3`만 허용한다. 권한 범위를 넓히지 않았다.

- [r10 실행·보존](agy-remediation-r10-result-20260928.json)
- [r10 독립 검증·원본 증거 경로와 hash](agy-remediation-r10-independent-review-20260928.json)
- [r11 사전 검증·실제 제한 명령 진단](agy-remediation-r11-preflight-20260928.json)

추가 독립 시험에서는 실제 ESP conditional 수신 source에 하드웨어 없는 timer/driver test
double을 붙여 실행했다. seq 7의 두 번째 입력은 accepted 1·rejected 1로 계수되지만,
last-update가 10초에서 999초로 바뀌고 Accepted 로그가 두 번 나왔다. 이는 앞서 r11에
사전 제공한 source 경로 문제의 실행 재현이며, 실행 중 AGY에 추가 전달하지 않았다.

독립 시험 입력·출력·보고서와 운영자 평가 source도 저장소 내 별도 archive로 보존했다.
이 archive에는 제품 변경이나 실제 하드웨어 합격 근거가 없으며, 각 entry와 archive hash를 기록했다.

- [독립 평가 archive receipt](agy-remediation-r10-independent-artifacts-20260928.json)
- [독립 평가 원본·재현 도구 archive](agy-remediation-r10-independent-artifacts-20260928.zip)

## r11 부분 수정 검증과 r12 준비

r11은 금지된 inline Python 실행으로 종료됐고, 명령 제한은 넓히지 않았다. 제품 14개 파일의
1190줄 추가·101줄 삭제를 AGY snapshot과 bundle에 보존했다. 독립 fresh archive에서
CRLF·oversized line 처리, HTTP_500 이후 last-good 유지, source stale 유지, 중복 프레임의
수신 시각/Accepted 로그 오염 방지가 개선된 것을 확인했다. 새 target 수신 함수 prologue는
64바이트, 태스크는 8192바이트이며 전체 call chain·제품 합격을 의미하지 않는다.

Host 빌드는 통과했으나 CTest 두 개가 실패했고, IDF build는 `esp_lcd_panel_io_del` 선언
누락으로 실패했다. canonical JSON 뒤 `junk`를 붙인 line도 아직 수락한다. 후보 CLI의 mock
초기화는 성공했지만 loopback 송신은 15.422초 후 LOCK_TIMEOUT으로 실패한다. 번호 예약과
내부 조회가 별도 file-lock context로 중첩되는 source 경로를 확인했다. Python suite는 첫
CLI 사례에서 실패한 뒤 동시 예약에서 반복 대기해 202.6초 후 운영자가 해당 시험 프로세스만
중단했다. 원본 일부 출력과 종료 기록을 보존하며 suite 완주·통과로 취급하지 않는다.

Legacy 29개는 통과했으나 r11의 완성된 structured result·binary·실물 검증은 없다. 현재
partial source의 주기 송신/재연결/단일 송신자 수명 관리와 F9 기록도 보완 대상이다. r12는
이 결과를 시작 전에만 전달하며, 올바른 시험 fixture를 제품 builder로 작성하되 계약을 약화해
실패를 없애지 않도록 명시한다. 제품 변경은 계속 AGY가 작성한다. 입력·정책·원본 실패 기록은
보존하고 최초 정량 비교에서 제외한다. 보드에 올릴 수정 binary는 아직 준비되지 않았다.

- [r11 실패·부분 수정·보존](agy-remediation-r11-result-20260928.json)
- [r11 독립 평가·시험 중단·남은 결함](agy-remediation-r11-independent-review-20260928.json)
- [r11 독립 평가 archive receipt](agy-remediation-r11-independent-artifacts-20260928.json)
- [r11 독립 평가 원본·재현 도구](agy-remediation-r11-independent-artifacts-20260928.zip)
- [r12 사전 검증·입력 보존·동일 정책](agy-remediation-r12-preflight-20260928.json)

## r12 완주·독립 모듈 통합 검증과 r13 준비

r12는 완주했고 fresh archive의 host/IDF 빌드, CTest 4개, Python regression, legacy 29개,
trusted 결과 형식 검증을 모두 통과했다. 평가 중 archive source 변경은 없었다. 동시 번호 예약은
32/32 고유 번호·오류 0이며 기존 번호 39의 재초기화를 거부했다. 실제 candidate CLI를 별도
프로세스로 실행해 7 송신→8 refresh→실패에서 9 소비→10 복구를 확인했다. 1초 주기 두 cycle은
1.875초에 완료돼 12까지 예약했다. 하드웨어 접근은 없으며 host write는 device ACK가 아니다.

그 이후 실제 PC 프레임을 실제 firmware parser/state/transport 모듈에 넣어 다음 결함을 재현했다.

- 후보 기본 reference/sent 시각 00:04:59와 fixture global captured 16:54:07이 충돌해 device가
  기본 전송을 거부한다. parser/schema/CRC는 통과하지만 거부 후 이미 provider 5개가 저장된다.
  같은 payload의 reference/sent를 16:54:07로 맞추면 수락한다. 이는 time/source 처리와 기본
  candidate 상호운용 문제이며, frozen fixture를 바꾸거나 source 시각을 새로 만들어 해결하지 않는다.
- 정상 seq 1에서 last-good 20%를 저장한 후 미래 global source를 포함한 seq 2를 거부하면서,
  sequence는 1로 유지하고 last-good은 40%로 바뀐다. 거부된 frame이 상태를 오염시키는 실행 증거다.
- 일관된 reference 시각에서 CRC가 올바른 150% 값과 `invalid-unit`도 수락한다. trusted schema는
  둘 다 거부한다. 이전 잘못된 시각 때문에 invalid case가 거부되던 사실과 구분해 검증했다.
- 다중 identity는 보존하지만 unsupported 두 항목까지 provider cycle에 포함된다. source 검토에서
  주기 owner가 실행 중인 manual refresh, reconnect/reopen, durable 예약과 recovery 기록의
  기존 계약 충족도 아직 확인되지 않았다. 문서의 물리 sender 명령에는 candidate flag가 누락됐다.

제품 source를 운영자가 수정하지 않았고 아직 수정 binary를 보드에 올리지 않았다. r13에는
검증된 개선을 유지하면서 위 결함과 기존 전체 계약을 마무리하도록 고정 지시를 시작 전에 제공한다.
실행 중 추가 지시는 없으며 원래 단일 prompt 정량 비교·순위와 합산하지 않는다.

- [r12 완주·보존](agy-remediation-r12-result-20260928.json)
- [r12 독립 검증·개선·남은 실패](agy-remediation-r12-independent-review-20260928.json)
- [r12 독립 평가 archive receipt](agy-remediation-r12-independent-artifacts-20260928.json)
- [r12 독립 평가 원본·재현 코드](agy-remediation-r12-independent-artifacts-20260928.zip)
- [r13 동일 정책·입력 보존·사전 검증](agy-remediation-r13-preflight-20260928.json)

## r13 조회 중단·r14 제한 문법 보완

r13은 제품 변경 전 literal `--candidate` 검색에서 중단됐다. 원본 source와 실패 로그·usage·
bundle·전역 설정 복구를 확인했다. `--`가 옵션을 끝낸 뒤의 dash로 시작하는 제한된 문자열
조회만 별도 등록했다. 기존 `--textconv` 실행 옵션을 등록한 것이 아니며, `--` 뒤 literal
문자열 검색은 실제 Git/AGY 진단에서 source marker를 출력했다. 검색 범위는 기존 checkout
읽기이며 native 파일 접근·실행 명령군·하드웨어 grant를 넓히지 않았다.

먼저 회귀 실패를 재현한 뒤 정책 시험 15개를 통과했고, 실제 AGY query 3개와 전체 preflight
121개·COM3·clean checkout을 통과했다. 부모/비허용 절대 경로·명령 결합·변환기 flag는 계속
거부한다. r14의 제품 파일 116개가 r13 시작 source와 hash 동일하며, 운영자 제품 변경은 없다.
시작 전에 고정 보완 지시를 제공하고 실행 중 추가 지시 없이 종료 후 평가한다.

- [r13 실패·원본 보존](agy-remediation-r13-result-20260928.json)
- [r14 literal 조회·권한 경계·사전 검증](agy-remediation-r14-preflight-20260928.json)

## r14 quota 중단·독립 검증·r15 실행

r14는 514.093초 후 AGY 서비스의 `RESOURCE_EXHAUSTED`/HTTP 429로 중단됐다. 마지막 제품 수정 뒤
정상 종료하지 않았으며, 제품 변경 4개 파일·404 insertions·111 deletions를 AGY 작성 checkpoint
`c72a6957b77b6f188daf17359beb58950f4cce92`로 보존했다. 입력 불변·전역 설정 복구·bundle hash를
확인했다. 실행 도중 추가 지시는 없었다. quota 중단·부분 source를 원래 단일 prompt 정량 비교에 합산하지 않는다.

Fresh archive 독립 검증에서 host/ESP-IDF 빌드와 legacy 29개는 통과했다. CTest는 3/4이며,
provider 화면 전환 fixture/assertion이 실패한다. Python suite는 10/11이며, 변경된 명시적 recovery
계약에 맞지 않는 force 초기화 test가 실패한다. 현재 run structured result는 없고 제품 합격도 아니다.
검증 후에도 archive source hash 변경은 없다.

개선 확인: 실제 candidate 기본 frame을 실제 firmware module이 수락했고 provider 5개가 유지된다.
지원되는 3개 identity의 cycle은 unsupported 2개를 건너뛴다. future-global frame 거부 후 last-good
20%와 sequence 1을 유지한다. ESP conditional transport 모의 시험은 duplicate를 거부하며 수신
시각 10을 유지한다. 32/32 번호 예약은 고유·오류 0이다. 실제 CLI의 7→8→실패 9 소비→10 복구와
전송 전 native fsync 및 next-sequence 8 저장을 확인했다. 모두 모의 시험이며 물리 장치 ACK 증거가 아니다.

남은 업로드 차단 사유:

- 실제 ESP32-S3 상태 처리 함수의 stack은 entry 32 + movsp 46,304 = **46,336 bytes**이다.
  수신 task stack 8,192보다 크다. transport 단독 prologue 64 bytes 통과만으로 호출 경로 안전을
  주장할 수 없다. 상태 전체 지역 복사본 변경으로 생긴 타깃 결함이므로 이 binary는 업로드하지 않았다.
- CRC와 시각이 정상인 nested schema negative 17개 중 11개, envelope negative 6개 중 5개를
  실제 receiver가 잘못 수락한다. fraction/overflow sequence, 잘못된 integrity algorithm,
  누락 필드·자료형·추가 속성 등이 포함된다. root decoder 자체도 malformed timestamp를 수락하므로
  그 항목은 trusted schema 차이로 계수하지 않으며 원래 date-time 계약 검토가 필요하다.
- 정상 absolute token fixture를 수락하지만 metric_kind를 quota_window로 바꾸고 사용량 250,
  잔량 750, 한도 1000을 null로 잃는다. mixed window의 100/900/1000도 잃는다.
- offline serial backend가 세 번 불가 후 네 번째부터 사용 가능해도 CLI가 세 번 뒤 종료한다.
  첫 write 이후 오류를 주면 실제 write sequence가 `[7,7,8]`로 실패한 번호를 재사용한다.
- active-owner refresh의 모의 frame은 0.468초 안에 나타났지만 명령은 owner lock에서 기다려
  8.859초 뒤 종료한다. request 파일 삭제를 전송 성공으로 표시하는 경로와 자동 timer 재설정은
  보완 대상이다. 명령 종료 지연을 frame 자체의 5초 조건 실패로 해석하지 않는다.
- 기존 old-source probe는 적용 전에 거부돼 stale false/false가 정상 aging의 증거가 아니다.
  정확한 nullable·error 계약, accepted stale 입력과 tick 검증이 필요하다.
- 현재 structured result·candidate 실제 운영 절차·물리 BOOT/LCD/IMU·owner 점수가 미완료다.

독립 raw 입력·stdout/stderr·재현 도구 268개를 ZIP와 entry별 hash로 보존했다. 운영자 검증 도구는
제품 source 바깥에 있으며 operator product edits는 계속 false다. 기존 보드에는 처음 올린 r01
firmware가 남아 있고 BOOT/flash 실패 영상은 그 firmware의 실패 증거로 유지한다.

사용량 한도는 서비스가 2026-09-28 21:09:44 KST쯤 초기화를 안내했다. 해당 시각은 서비스 예상이며
해제 확인 자체가 아니다. 사용자가 2026-09-29 `keep going`을 요청한 뒤 새 실행 전에 사전 검증을
다시 수행했다. 121개·host runtime·COM3·clean checkout을 통과했고 동일 보드
`303A:1001 / 28:84:85:B0:85:18`을 확인했다. 첫 사전 검증 로그도 별도로 보존했다.

r15는 위 관찰을 한 번의 고정 지시문으로 제공한다. AGY 제품 파일 116개가 r14 archive와 byte/hash
동일함을 확인했으며 모델 `gemini-3.8-flash-medium`과 finite 정책 hash `22ef9080…a02d`를
유지한다. 실행을 시작했고 AGY 종료 후 fresh archive로 독립 평가한다. 이는 환경 사전 검증 통과이며
제품 합격 또는 물리 검증 완료를 의미하지 않는다. 원래 정량 비교·순위에는 포함하지 않는다.

- [r14 quota 실패·부분 수정·보존](agy-remediation-r14-result-20260928.json)
- [r14 독립 검증·남은 결함·검증 한계](agy-remediation-r14-independent-review-20260928.json)
- [r14 독립 증거 archive receipt](agy-remediation-r14-independent-artifacts-20260928.json)
- [r14 raw 입력·출력·재현 도구](agy-remediation-r14-independent-artifacts-20260928.zip)
- [r15 동일 모델·정책·source·재검증](agy-remediation-r15-preflight-20260928.json)

## r15 조회 정책 중단·스택/회귀 개선·r16 실행

r15는 701.266초 후 `Get-ChildItem -Recurse -Filter *.json | Select-Object FullName`이 차단돼
중단됐다. terminal SUCCESS와 달리 denied_actions가 있어 environment_failed이며 완주가 아니다.
제품 3개 파일·127 insertions·72 deletions를 AGY checkpoint
`0d660d444e1aca593d42e6d5b7133fee2b6b283f`로 보존하고 입력 불변·전역 설정 복구를 확인했다.

Fresh archive의 host/IDF 빌드·CTest 4개·Python 11개·legacy 29개는 모두 통과했다. 현재 structured
result는 아직 없으므로 trusted current-result 검증과 제품 전체 합격은 미완료다. 코드 검토에서
화면 전환 test에 실제 window가 있는 정상 3개와 unsupported/error 2개 입력을 보강했고,
32개 고유 예약 assertion을 유지하며 미기록 복구와 reset 확인 누락의 거부를 추가했음을 확인했다.
시험 assertion을 삭제해 회귀 실패를 없앤 변경이 아니다.

실제 target 상태 함수 stack은 80 bytes로 줄었다. transport 단독 64 bytes와 수신 task 8192 bytes를
별도로 기록했으며, 이 함수 측정 자체를 전체 runtime stack 상한으로 해석하지 않는다. 잘못된
future-global frame 거부 후 last-good 20%·sequence 1 보존도 실제 독립 시험으로 유지됐다.

그 외 스키마 오수락 11+5개, normalized 절대값·metric_kind 손실, 세 번 뒤 종료하는 reconnect,
write 오류 뒤 번호 7 재사용, owner refresh/자동 timer·nullable stale·현재 운영 절차/결과의
미완료를 재현했다. root 검증 도구의 exit 0은 관측 실행 완료이며 해당 제품 조건의 pass가 아니다.
독립 자료 298개를 ZIP·entry hash로 보존했다. archive source 변경과 운영자 제품 변경은 없다.

r16에는 이미 통과한 스택·회귀 개선을 유지하고 unfinished parser/collector·절차/결과를 마무리할
고정 지시문을 제공했다. 기존에 허용된 `rg --files -g "*.json"`, `git ls-files "*.json"`,
`Get-ChildItem -Recurse -Filter "*.json"`을 사용하도록 명시했다. 파이프는 계속 거부하며
policy/데이터 grant는 변경하지 않았다. 사전 검증 121개·host runtime·COM3·clean checkout과
제품 파일 116개가 이전 archive와 같은 hash임을 확인하고 동일 모델로 실행을 시작했다.
실행 중 추가 지시 없이 종료 후 평가한다. 제품 합격·물리 검증·수정 firmware 업로드는 아직 없다.
이 실행도 원래 단일 prompt 정량 비교 및 순위에 포함하지 않는다.

- [r15 실패·부분 수정·원본 보존](agy-remediation-r15-result-20260928.json)
- [r15 독립 검증·스택 개선·남은 실패](agy-remediation-r15-independent-review-20260928.json)
- [r15 독립 archive receipt](agy-remediation-r15-independent-artifacts-20260928.json)
- [r15 raw 자료·재현 도구](agy-remediation-r15-independent-artifacts-20260928.zip)
- [r16 동일 정책·source·사전 검증](agy-remediation-r16-preflight-20260928.json)

## r16 완주·독립 재검증·실물 업로드 및 추가 결함

r16은 2026-09-29 02:09:28 KST에 1411.953초로 정상 종료했다. AGY 구현
`e103ad9eb024d53c9905dc65a0d90c05a775e24f`를 보존하고 입력 불변·전역 설정 복구를 확인했다.
제품 코드와 시험은 AGY가 작성했으며 운영자는 제품 소스를 수정하지 않았다. 이번을 포함한
보완 실행은 `ranking_eligible:false`이며 원래 단일 지시문 정량 비교의 실패·순위를 대체하지 않는다.

Fresh archive의 host 빌드·CTest 4개·Python 14개·legacy 29개·ESP-IDF 빌드·운영자 원본
current-result validator가 모두 통과했다. 이전 17개 nested schema와 6개 envelope 부정 입력은
실제 transport에서 거부됐다. 절대량 250/750/1000 및 100/900/1000과 metric_kind 보존,
네 번째 open에서 1Hz 재연결, 수동 갱신 응답 0.594초·frame 관측 0.578초, 독립 자동 timer,
32개 고유 durable 순번 예약·원자적 거부·last-good·duplicate freshness도 확인했다.

직접 parser 시험의 입력 buffer에 길이 밖 newline이 남아 실제 transport와 결과가 달랐다.
운영자 supplemental 도구에서 실제 transport처럼 NUL을 길이 위치에 두어 원인을 구분했다.
최초 결과를 삭제하지 않았고 제품 소스는 변경하지 않았다. CC 환경 변수 가정과 CRLF stack
추출 오류도 운영자 도구 오류로 보존했다. 실제 target 직접 stack은 state 80 bytes,
transport 64 bytes, parser 최대 단독 함수 1312 bytes이고 task는 8192 bytes다.
전체 runtime stack 상한이나 여유를 이 값만으로 합격 처리하지 않는다.

허용된 nullable 절대량 거부, 계약에 없는 값 합계 강제, 잘못된 recovery flag와 한 번 뒤 종료하는
주기 송신 안내가 남았다. agent 자체 F9 30점은 owner 평가로 인정하지 않으며 G/F9 점수는 미확인이다.
기본 실제 frame 수신·부정 입력 거부·빌드/시험/직접 stack 확인을 근거로 전체 합격과 구분한
실물 검증용 업로드 gate를 기록하고, 이미 허가된 업로드를 수행했다.

2026-09-29 02:17 KST COM3 동일 보드 `303A:1001 /28:84:85:B0:85:18`에 해당 binary를
업로드했다. flash exit 0·각 flash file hash 일치·boot ELF prefix `7f7644266` 일치,
20초 로그의 panic marker 없음, GPIO0 입력 복원과 QMI8658 WHO_AM_I `0x05`를 확인했다.
실물 LCD 안정성 자체를 부팅 로그만으로 통과 처리하지 않았다.

사용자 영상 `KakaoTalk_20260929_021948404.mp4` 원본 7,076,787 bytes·15.3초를 복사하고
SHA256 `db5131c531a7623b9b2992901f4db6a9d8b676b6a38d24a8b001d53fd1241248`를 남겼다.
1Hz 15개 샘플에서 버튼에 따른 dashboard/global/diagnostics 전환을 관찰했다. 이전 r01의
큰 blank/partial 화면은 샘플에서 관찰되지 않았다. 30초 연속 안정성과 BOOT 300ms 수치는
확정하지 않았다. 사용자 회전 동작 확인과 IMU 감지 로그를 기록했으며 전체 180도 동작 장면·
방진·모델 비공개 G/F9 평가는 별도 미확인이다. 영상의 대기/0 수신 화면은 quota 수신 증거가 아니다.

실제 CLI 순번 7의 host write receipt를 보존했다. 후속 CLI의 원래 backend에 로그 관측 proxy를
두어 실제 native write/open/control 설정을 유지하고 close 전에 3초 읽었다. 순번 8·9의 장치
수용은 확인했지만 중간 boot 로그가 나타났다. 이 관측 지연은 성능·정량 비교에 포함하지 않는다.
초기 별도 reader의 ClearCommError는 관측 실패로 기록했으며 panic이나 frame 거부로 단정하지 않았다.

전원이 유지된 보드에서 원래 candidate backend로 통제 시험을 수행했다. 같은 open stream은
순번 10을 수용하고 낮은 1을 거부했다. backend close/reopen 후 명시적 reset 없이 새 LCD/GPIO/IMU
초기화 로그가 나타났고 낮은 1을 수용한 뒤 persisted 11을 수용했다. 정상 PC 재시작에서 receiver
순번 상태를 유지해야 하는 조건은 실패다. 이 순번 부정 입력은 운영자 protocol conformance 시험이며
자동 collector 또는 ACK 구현으로 분류하지 않는다.

추가 canonical 시험에서 nested window/snapshot 키 순서 반전과 trailing comma 4개를 raw unsigned
bytes 기준으로 CRC 재계산했을 때 실제 transport가 수용했다. 원본 decoder는 거부한다. 이 자료는
이미 봉인한 최초 독립 ZIP을 변경하지 않고 하드웨어 supplemental ZIP에 보존했다.
`product_pass:false`를 유지하며 새 고정 보완 지시문에 증거와 한계를 제공했다.

- [r16 실행 완주·원본 보존](agy-remediation-r16-result-20260928.json)
- [r16 독립 software 검증·미합격 항목](agy-remediation-r16-independent-review-20260928.json)
- [r16 최초 독립 검증 archive receipt](agy-remediation-r16-independent-artifacts-20260928.json)
- [r16 최초 독립 raw 자료](agy-remediation-r16-independent-artifacts-20260928.zip)
- [r16 업로드·실물·영상·재시작 실패](agy-remediation-r16-hardware-review-20260929.json)
- [r16 하드웨어 supplemental archive receipt](agy-remediation-r16-hardware-artifacts-20260929.json)
- [r16 실물 raw logs·원본 영상·추가 canonical 시험](agy-remediation-r16-hardware-artifacts-20260929.zip)

## r17 동일 정책으로 남은 실패 보완 시작

r17은 r16 checkpoint 제품 파일 116개의 byte/hash 일치, 새 checkout 2개 준비 commit·clean 상태,
사전 검증 121개·host runtime·COM3·0 failure/0 warning을 확인하고 실행을 시작했다.
모델 `gemini-3.8-flash-medium`, 정책 SHA256 `22ef9080…a02d`와 제한된 command/data grant를
유지한다. 고정 지시문에 nested canonical/nullability, 실제 native serial open/close의 보드 reset,
write-error reconnect, 정확한 운영 명령과 owner F9 미확인 항목을 제공했다. 완료된 r16 뒤의
보완 입력이며 실행 중 feedback·root 제품 수정은 없다. `ranking_eligible:false`이고
실행 환경 준비를 제품 합격으로 분류하지 않는다. 보드는 실물 평가된 r16이 올라간 상태다.

- [r17 동일 정책·source·사전 검증](agy-remediation-r17-preflight-20260928.json)

## r17 target 정책 중단·파서 보완 검증·한정된 빌드 명령 사전 시험

r17은 666.297초 뒤 미등록 `cmake --build build-host --target test_meter_parser`에서 중단됐다.
terminal SUCCESS와 구분해 environment_failed로 기록하고 AGY partial commit
`acb9173fffb93bb0936b1d522822e72b7c9aca1a`의 제품 3개 파일·512 insertions·96 deletions를
보존했다. 해당 수정본은 업로드하지 않았으며 보드에는 앞서 평가한 r16이 올라가 있다.

Fresh host/IDF 빌드·CTest 4개·legacy 29개는 통과했다. 새 canonical 4개 부정 입력이 거부되고,
nullable token 3개와 독립 percent 값·0/100/null 긍정 입력도 수용됐다. 이전 schema/envelope
거부·절대량 보존·last-good·5개 identity cycling·32개 고유 durable 순번 예약은 유지됐다.
실제 parser 최대 단독 함수 stack은 1328 bytes이며 전체 runtime 상한 검증은 아니다.

PC 제품 코드 보완 전 새 회귀 시험만 추가된 상태로 중단돼 Python 17개 중 2 failures/1 error가
남았다. DTR/RTS를 open 전에 안전하게 설정하는 조건, 정상 serial session 유지, 복구 CLI flag
시험이 실패했다. 현재 r17 result는 없으므로 trusted current-result 검증도 실행하지 않았다.
새 assertion을 제거해서 실패를 숨기는 방식으로 처리하지 않는다. root 제품 코드 수정은 없다.

사용자가 앞서 선택한 '필요 명령 제한 유지·조회/파일/빌드/시험 명령군 정리와 별도 사전 검증'에 따라
`build-host` 아래 알려진 target 6개만 등록했다: `test_meter_parser`, `test_meter_state`,
`test_feature_imu`, `test_gui_regression`, `meter-test`, `meter_core`. 정책 시험에서 등록 전 6개
거부를 재현하고 등록 후 16개 시험을 통과했다. 임의/install/clean target·다른 build 경로·추가
argument·파이프·복합 명령은 거부한다. 다른 command 규칙과 data grant는 byte/목록 기준 동일하다.
정책 SHA256은 `22ef9080…a02d`에서 `6746977f…86187`로 변경됐으며 비교 순위 실행에 적용하지 않는다.

별도 checkout의 실제 AGY 정책 smoke는 33.171초에 지정한 6개 target build만 완료했다.
source hash 불변·전역 설정 byte 동일 복구·raw stream/stderr/usage/입력·정책 전후 사본을 보존했다.
이 diagnostic은 제품 구현·정량 비교 run이 아니다. smoke와 r17 평가에 원본 archive/hash receipt를 남겼다.

운영자가 두 SDK activation을 병렬로 시작해 공유 shim WriteAllText 경합이 발생했고 최초 additional
probe는 시작되지 않았다. 순차 activation 후 실제 probe를 모두 완료했다. 운영자 실행 오류이며
AGY 제품 실패로 분류하지 않았다. 원본 실패와 수정 경위를 review에 기록했다.

- [r17 중단·partial 보존](agy-remediation-r17-result-20260928.json)
- [r17 파서 개선·PC 실패·평가 한계](agy-remediation-r17-independent-review-20260928.json)
- [r17 독립 archive receipt](agy-remediation-r17-independent-artifacts-20260928.json)
- [r17 독립 raw 자료](agy-remediation-r17-independent-artifacts-20260928.zip)
- [6개 target 한정 정책·실제 AGY smoke](agy-build-target-policy-smoke-20260929.json)
- [정책 smoke raw 자료·전후 정책](agy-build-target-policy-smoke-20260929.zip)

## r18 PC 시리얼·재연결·운영 절차 보완 실행

r18은 확인된 r17 parser/회귀 변경을 그대로 가져왔으며 제품 파일 116개 byte/hash 일치·
checkout 2개 준비 commit·clean 상태와 새 사전 검증 122개·host runtime·COM3를 통과했다.
사전 시험된 한정 target 정책 `6746977f…86187`·동일 모델을 사용한다. 새 고정 지시문은 검증된
파서 개선을 유지하고 아직 수정되지 않은 PC native serial 제어선/open/close/reconnect·실패 순번·
운영 명령·현재 결과 문서부터 보완하도록 요청한다. 실행을 시작했고 runtime feedback은 하지 않는다.
보드에는 r16이 유지되며 root 제품 소스 수정·원래 비교 순위 편입은 없다. `product_pass:false`다.

- [r18 source·한정 정책 변경·사전 검증](agy-remediation-r18-preflight-20260928.json)

## r18 조회 형식 중단·제품 변경 없음·한정된 표준 grep 사전 검증

r18은 67.875초 뒤 `git grep -n "def test_" tests/test_pc_pipeline_regressions.py`에서 중단됐다.
기존 규칙이 pattern 뒤의 파일 경로에 `--`를 요구해 실제 Git의 표준 형식이 거부됐다.
제품 수정 전 종료였고 archive `90cd79b70de2bb1de607b86dde3880f41b85080f`의 diff는 없다.
제품 파일 116개를 hash 비교해 r17과 동일함을 확인했다. 전체 제품 빌드를 다시 반복하지 않고
r17 검증을 참조하며, 현재 result 미생성·미완주·제품 미합격·업로드 없음으로 별도 기록했다.

같은 사용자 제한 명령군 정리 요청에 따라 알려진 checkout 경로의 Git grep 파일 인자 형식을
추가 등록했다. source/시험/docs 등 현재 경로만 허용하며 HEAD/history refs·all·textconv·
외부/부모 경로·경로 순회·복합 명령·파이프는 계속 거부한다. 다른 규칙과 data grant는 동일하다.
새 정책 SHA256은 `2c79ccc4…1034f`다. 등록 전 4개 표준 조회 거부를 재현하고 등록 후
정책 시험 17개를 통과했다. 실제 AGY의 3개 조회 smoke는 27.687초에 모두 실행됐고 checkout
source hash 불변·전역 설정 byte 동일 복구를 확인했다. raw 입출력·usage·정책 전후 사본을 보존했다.

r18 launch gate의 console에 오래된 `policy_unchanged:true` label이 남아 있었지만 signed JSON은
이미 실제 한정 정책 변경을 기록했다. 운영자 helper의 다음 출력부터 label을 바로잡았으며 제품
변경이나 policy scope 변경으로 처리하지 않는다. source 수정은 계속 AGY만 담당한다.

- [r18 조회 중단·수정 없음·원본 보존](agy-remediation-r18-result-20260928.json)
- [r18 source 동일 확인·r17 검증 참조](agy-remediation-r18-independent-review-20260928.json)
- [표준 grep 한정 정책·실제 AGY 조회 시험](agy-standard-grep-policy-smoke-20260929.json)
- [표준 grep smoke 원본·정책 전후](agy-standard-grep-policy-smoke-20260929.zip)

## r19 PC 보완 실행 시작

r19는 r18 보존본의 제품 파일 116개를 byte/hash 그대로 이어받았다. 새 사전 검증 123개,
host runtime, COM3, 2개 준비 commit 및 clean checkout 조건을 통과한 뒤 실행을 시작했다.
명령 정책은 별도 AGY 조회 시험을 통과한 `2c79ccc4…1034f`이며 데이터 접근 범위는 동일하다.
PC serial 제어선·정상 session 유지·실패 후 재수집/새 순번·정확한 운영 명령·현재 결과 제출을
고정 지시문으로 요청했다. 실행 중 추가 피드백과 root 제품 소스 수정은 하지 않는다.
원래 단회 정량 비교 순위에 포함하지 않는 보완 실행이며 `ranking_eligible:false`다.
보드는 현재 r16이고 r19 업로드 및 전체 제품 합격은 아직 확인되지 않았다.

- [r19 source·제한 정책 변경·사전 검증](agy-remediation-r19-preflight-20260928.json)

## r19 PC 개선 검증·문서 외부 경로 중단·r20 시작

r19는 155.969초 후 이전 실행 디렉터리의 문서를 읽으려다 접근 제한으로 중단됐다.
AGY가 수정한 PC 파일 2개, 119 insertions/95 deletions를 commit
`6e629722f98857d83bdc2b128cbcdb7f136b71a4`와 bundle hash로 보존했다.
새 native backend는 포트 open 전에 DTR/RTS를 false로 설정하고 건강한 session을 재사용하며
owner 종료 시 정리한다. 독립 fresh archive에서 Python 17개·CTest 4개·legacy 29개·IDF build가
통과했다. 실제 보드 확인은 아직 하지 않았다. 현재 result가 없어 trusted current-result validator는
실행하지 않았다. 실제 도중 write 오류 주입은 순번 7을 소비하고 owner를 종료하므로 지속 복구가 남는다.
manual 요청 응답 0.641초·frame 관측 0.625초·자동 8초 설정 관측 8.532초, native fsync-before-write를
독립 확인했다. C/main/tests는 r17 보존본과 동일해 추가 nullable/canonical/scoped 시험은 r17을 참조한다.

r20는 이 PC 개선 116개 제품 파일을 byte/hash 그대로 이어받아 사전 검증 123개와 COM3·clean 조건을
통과한 뒤 시작했다. 정책·data scope는 유지한다. 현재 checkout 안의 상대 문서 경로를 명시하고
외부 이전 디렉터리 접근을 금지했으며, native write/flush 지속 복구·운영 절차·현재 결과를 요청했다.
제품 작성은 AGY만 하고 runtime feedback은 없으며 원래 정량 순위와 별도다. 보드는 r16이다.

- [r19 중단·AGY PC 변경 원본 보존](agy-remediation-r19-result-20260928.json)
- [r19 독립 검증·잔여 write 복구·물리 확인 미완료](agy-remediation-r19-independent-review-20260928.json)
- [r19 독립 원본 archive receipt](agy-remediation-r19-independent-artifacts-20260928.json)
- [r19 독립 시험 원본 자료](agy-remediation-r19-independent-artifacts-20260928.zip)
- [r20 제품 보존·정책 동일·사전 검증](agy-remediation-r20-preflight-20260928.json)

## r20 정상 완주·독립 소프트웨어 통과·업로드·실물 데이터 확인

r20는 596.484초에 정상 완주했고 전역 설정을 복구했다. AGY 제품 파일 3개 변경과 새 운영 문서·
현재 결과를 commit `6e00bd8ba518f008d50a762f035a5e8c7e8b6e5c`에 보존했다. 독립 fresh archive에서
host build·CTest 4개·Python 20개·legacy 29개·IDF build·root 원래 current-result validator가 통과했다.
실제 CLI main의 write 오류 주입은 7 소비 후 1초 재연결·재수집으로 8/9를 보내고 다음 10을 저장했다.
native fsync-before-write·manual과 독립 automatic·현재 운영 명령을 확인했다. C/main/C-test bytes는
r17과 동일하여 parser 추가 nullable/canonical/scoped 및 direct stack 증거는 그 보존본을 참조한다.
F9 22점은 AGY의 보수적 잠정 자체 점수이며 최종 owner 점수와 G 점수는 미확인이다.

검증된 바이너리를 COM3의 동일 보드에 업로드했다. 부팅 ELF prefix `056dfcca8`은 독립 빌드 ELF
SHA256 `056dfcca893b57cb237296c0744da305867abeed1b6adeed1a18e99f3b451b62`와 일치하며 20초 로그에
패닉 표시가 없다. 기록된 초기 flash/reset 뒤 새 store를 명시적으로 7로 초기화했다.
실제 CLI 7·재시작 8·manual 9 수신 로그가 같은 firmware uptime에서 이어졌다.
같은 USB 전원 상태에서 original native backend로 10 수신, 낮은 1 거부, close/reopen 후 낮은 1 재거부,
11 수신을 확인했다. 이 제한된 native reopen 순서 보존 시험은 통과했다. 마지막 11 수신 이후 passive
read에 ClearCommError가 한 번 발생했다. 원인을 확정하지 않고 원본을 보존했으며 전체 무오류로 판정하지 않는다.

별도 실제 두-process CLI 시험은 manual 명령 0.625초·frame 관측 0.594초·8초 automatic 관측 8.485초,
12/13/14 송신과 14 device 수신을 확인했다. 이후 미수정 AGY CLI를 15초 간격 12회 실행하여 15부터 26까지
송신했고 정상 종료·다음 27을 저장했다. 중간에 받은 실제 영상은 순번 20·9건 accepted·CONNECTED·
validated cache·사용량과 글로벌 reset 값이 표시되는 것을 확인했다. 고정 offline fixture이므로 STALE는
정상적인 출처 나이 표현이며 실제 온라인 quota를 의미하지 않는다.

첫 새 영상은 29.22초(SHA `dc644173…a439d`), 다음 영상은 9.02초(SHA `b95c6077…fe66`)다.
첫 영상에서 세 화면 BOOT 전환과 물리적 180도 회전을 확인했다. 각각 876/270개 전체 decode frame의
거친 색상 기준 검사에 whole-screen blank 후보가 없었지만 미세 flicker/timing 판정은 아니다.
두 영상을 이어서 30초 연속 합격으로 만들지 않는다. 35초 고정 영상을 추가 요청했다.
BOOT≤300ms·수신 후 LCD≤2s·별도 전원을 유지한 실제 USB cable 분리/재열거·50cm 모델 비공개 G/F9
정식 채점은 여전히 미확인이다. 완주는 확인됐고 전체 `product_pass:false`를 유지한다.
제품 코드/시험은 AGY 작성, root는 환경 준비·분리된 검증·기록·업로드만 담당하며 원래 정량 순위와 별도다.

- [r20 정상 완주·원본·계측](agy-remediation-r20-result-20260928.json)
- [r20 독립 소프트웨어 검증](agy-remediation-r20-independent-review-20260928.json)
- [r20 독립 시험 archive receipt](agy-remediation-r20-independent-artifacts-20260928.json)
- [r20 독립 시험 원본 자료](agy-remediation-r20-independent-artifacts-20260928.zip)
- [r20 upload·native reopen·actual CLI·영상 검증](agy-remediation-r20-hardware-review-20260929.json)

### r20 추가 41.73초 영상·사용자 RST 확인·기존 store 복구 송신

추가 영상 `KakaoTalk_20260929_033800739.mp4`는 41.73초, SHA256
`7ef18c6b11b6a7431d251794c55933ea777f50fcba14987f0cbd8d1cfc3005a8`다.
약 5~7초 LCD black 뒤 데이터 대기로 돌아간 것을 확인하여 원인을 질문했고 사용자는
**“RST를 눌렀음”**이라고 확인했다. 이 구간은 의도적인 reset으로 기록하며 spontaneous reboot나
BOOT 결함으로 처리하지 않는다. 영상에는 화면 뒷면/카메라 밖 구간도 있어 고정된 30초 연속 표시
증거로 처리하지 않고, 버튼·회전·reset 없이 LCD 전체를 보이는 35초 영상을 마지막으로 요청했다.
같은 영구 store의 다음 27을 실제 미수정 AGY CLI로 보내 receiver 수신을 확인했고 다음은 28이다.
root의 reinit/reset/flash·제품 변경은 없다. 기존 hardware review와 세 영상 원본을 모두 보존한다.

- [사용자 RST 확인·41.73초 영상·순번 27 복구 추가 기록](agy-remediation-r20-rst-video-supplement-20260929.json)

### r20 실물 원본 archive 고정

실제 flash/boot·원본 CLI·고유 store 순번·native reopen·실제 manual/automatic·유한 12회 송신·
세 영상 원본·추출 frame·관측 오류·RST 확인 후 27 수신·제품 외부 owner helper들을 255개 entry,
69,192,367 bytes의 archive로 고정했다. SHA256은
`2d058c873ec124a5060108dcd6c0af885c545d79862a815292ef5dcd2d061449`다.
packaging 직전 모든 제품 source/binary hash가 독립 build 보존본과 같은 것을 확인했다.
최종 고정 영상은 요청 대기 상태이며 archive를 덮어쓰지 않고 후속 증거로 추가한다.

- [r20 실물 원본 archive receipt](agy-remediation-r20-hardware-artifacts-20260929.json)
- [r20 실물 원본·세 영상·관측 도구](agy-remediation-r20-hardware-artifacts-20260929.zip)
