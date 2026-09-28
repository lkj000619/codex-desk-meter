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
| remediation r13 | 실행 시작 | r12 제품 source 116개 byte 보존. preflight 120개·COM3·clean checkout 실패/경고 0. 동일 제한 정책과 진단 hash 확인. 실제 남은 결함·확인된 개선을 고정 prompt로 사전 제공. 원본 순위 제외 유지 |

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
