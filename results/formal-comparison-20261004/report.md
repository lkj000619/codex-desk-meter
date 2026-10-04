# 정식 동일 조건 비교 실행 기록

상태: 2026-10-05 AGY Flash 후속 1회차의 동결·정책·독립 host 검증과 COM3 업로드/공통 데이터 전송 기록까지 완료했다. 05:38:52 KST 원본 펌웨어 업로드 후 장치 수락 로그 0건·LoadProhibited panic/재부팅 2회를 관측했으며 사용자 LCD/BOOT 영상과 최종 RM·복원이 남아 있다. 최초 environment_failed·제출 누락·USB write timeout·기준 미도달·eligible 정책은 보존한다. 전체 비교는 진행 중이다.
후보 실행 시작 4회·종료 4회(최초 2·후속 2). AGY Flash 후속 정책은 invalid_for_comparison이며 원래 CTest 기록과 별도 새 host source 검증을 구분한다. AGY Pro·Codex Sol/Luna는 미시작이다. 독립 series 완료는 OpenCode 1개/예정 15개다.
준비 당시의 0회 기록과 동결 tag는 보존한다.

원본 계약은 [운영 계약](../../docs/experiments/comparison-operating-contract.md),
실행 순서·완료 조건은 [실행 계획](../../docs/plans/2026-10-04-formal-comparison-execution.md)을 따른다.
baseline은 `272875140d1998d458e26fdb2f6deab5e5d8f7b5` / `comparison-baseline-20261004`다.
활성 5개·독립 3블록·Claude 제외라는 구성을 유지한다.

## 첫 실행

- 모델: OpenCode `opencode/muse-spark-1.3-contributor-free`.
- run: `20261004-opencode-cli-opencode-muse-r01`.
- 최초 예산: 최대 7,200초. 자동 재시도·추가 session·운영자 구현 피드백을 제공하지 않는다.
- 원본 위치: `C:/meter-runs-20261004/20261004-opencode-cli-opencode-muse-r01/`의 manifest·stdout.jsonl·stderr.txt·checkout.
- ledger: `C:/meter-runs-20261004/ledgers/20261004-opencode-cli-opencode-muse-r01.json`.
- runner: 깨끗한 operator checkout `C:/meter-operator-20261004`의 동결 `scripts/benchmark.py`.
- 실행 process는 대화와 별도다. [launcher 기록](first-run-launch.json)과 [관측한 진행 상태](progress.json)를 남겼다.

후보 입력·공통 과제·profile은 준비 때의 hash를 유지한다. 후보는 serial/flash를 수행하지 않는다.
결과 제출 후 운영자가 source를 수정하지 않고 자체 시험·빌드·정책 준수와 COM3 실물 동작을 검토한다.
원본 계측의 null은 0으로 바꾸지 않는다. 준비 비용과 제품 비용을 분리하며 실패·미검증 결과도 보존한다.

실행 중 `cmake --version`에 native permission 거부가 발생했고 이후 후보 작업이 계속됨을 기록했다.
권한·profile·prompt를 바꾸거나 후보에게 구현 피드백을 주지 않았다. 종료 후 필수 policy review에서 동결 과제의 권한 거부 시 종료 규칙 위반으로 비교 부적격을 판정했다.
사용자는 결과 동결 후 보드를 직접 보고 LCD·BOOT 관측 결과를 제공할 수 있다고 답했다.
직접 관측과 영상/사진·시각 정렬 증거를 구분하며, 확보하지 못한 정밀 지연·광학 항목을 합격 처리하지 않는다.

## 2026-10-04 종료·운영자 검증

- 실행: 22:47:50~23:04:54 KST, 실제 1,024.64초. 종료 code 0은 제품 합격을 뜻하지 않는다.
- 원본 token: input 242,001, output 64,857, 정규화 합계 306,858. cached 20,034,116, reasoning 25,419, provider total 20,366,393은 별도 원본 필드로 보존한다. provider total을 다른 공급자의 비용 순위에 직접 섞지 않는다.
- 정책: native 거부 1회 뒤 새 assistant 단계에서 도구 실행이 계속됐다. 거부 이후 도구 호출 123개, 전체 raw event 447개다. 실행 중 개입·권한 완화·대체 최초 실행은 없었다. runner의 미계측 null은 유지하고 운영자 개입 0회 감사 기록을 별도로 남겼다.
- 구현 동결: `e14689fea0cee5c0bd1e3812f7bd5dfbd122d5db`. 공통 입력 검증과 clean 상태 확인 후 관측을 시작했다. 운영자는 후보 source를 수정하지 않았다.
- 독립 재실행: result/schema/fixture matrix validator, Python 25개, 제품 C 모듈을 연결한 host 실행 파일 6개 통과. 이는 host 검증 범위다.
- 실물: COM3, ESP32-S3 revision v0.2. decode한 NVS 24K 영역만 초기화하고 동결 app/bootloader/partition artifact를 업로드했다. app SHA-256 `f91ff86ea8c80ab5ec03f47948259d7de96bd87e0384ceb3d427eb52d0e72dd9`, 333,232 bytes. 전체 flash erase는 수행하지 않았다.
- 공통 자극: reference UTC `2026-09-30T18:40:49Z`, 원본 seq 0·1 frame, 약 5초 간격. 전송 bytes SHA-256 `811c399098ff8ffefc587469d49e61d30ea7c7ffa440c477d47dbe0cffabb2cd`가 원본과 같다.
- 장치 수락: raw serial의 `accepted seq 0 crc 203D8DF3`, `accepted seq 1 crc C4CAA941`를 실제 receiver source의 성공 분기와 대조했다. 가변 timestamp/ANSI prefix 때문에 자동 capture의 수락 시각 null은 유지한다. source 검토에 따른 수락 확인과 광학 지연 측정은 별개다.
- 연결성 한계: 실제 collector checker가 공통 legacy personal-usage fixture를 `SCHEMA_INVALID`로 판단한다. 후보 sender의 frame 생성은 고정 frame과 byte 단위로 일치하지만 이번 실물 송신은 `operator_replay`다. 전체 후보 collector→sender→장치 경로를 통과로 표시하지 않는다.

[증거 목록](evidence/20261004-opencode-cli-opencode-muse-r01/snapshot-inventory.json)에 원본 bytes·hash를 연결했다.
[정책 review](evidence/20261004-opencode-cli-opencode-muse-r01/policy-review.json),
[동결 artifact](evidence/20261004-opencode-cli-opencode-muse-r01/operator-source-freeze.json),
[독립 host 검증](evidence/20261004-opencode-cli-opencode-muse-r01/operator-observation/host-checks.json),
[업로드](evidence/20261004-opencode-cli-opencode-muse-r01/operator-observation/hardware-slot.json),
[실물 capture](evidence/20261004-opencode-cli-opencode-muse-r01/operator-observation/reference-capture-r1/capture.json),
[수락 의미 검토](evidence/20261004-opencode-cli-opencode-muse-r01/operator-observation/receiver-source-review.json)를 보존했다.

사용자는 현재 화면에 값이 없다고 보고했고, 제공 사진을 확인해 파란 가로 줄과 문자·숫자 부재를 기록했다.
원본 [사진](evidence/20261004-opencode-cli-opencode-muse-r01/operator-observation/user-lcd-photo-01.png)과
[관측 범위](evidence/20261004-opencode-cli-opencode-muse-r01/operator-observation/user-observation-01.json)를 보존했다.
BOOT 조작·30초 연속 유지·정밀 지연은 답변이나 영상 근거가 없어 미측정이다.

| 최초 RM 항목 | 판정 | 확인 범위 |
|---|---|---|
| RM1 빌드·동일 artifact 실행 | pass | 업로드 hash 검증과 장치 성공 로그 |
| RM2 공통 fixture→후보 경로→장치 수락 | partial | 실제 수락 확인, 후보 collector 연결 미입증 |
| RM3 남은 비율 58%·82% 표시 | fail | 사용자 보고·사진에서 표시 값 부재 |
| RM4 세 정보 화면 | not_run | 각 화면의 전체 관측 없음 |
| RM5 BOOT 탐색 | not_run | 실제 조작·복귀 경로 보고 없음 |

[RM review](evidence/20261004-opencode-cli-opencode-muse-r01/reference-review.json)를 ledger에 연결했다.
기준 도달과 전체 제품 합격을 구분하고 미관측을 합격이나 제품 실패로 채우지 않았다.

## 보존·독립 복원의 실제 결과

동결된 `package-evidence.py`는 checkout의 `build/`만 수집하므로 이번 `firmware/build/` artifact를
찾지 못해 일반 package 생성을 거부했다. app/ELF/map/bootloader/partition 실제 파일과 hash는 존재한다.
이 운영 도구의 경로 제한을 후보의 build 실패로 바꾸지 않았고 동결 runner·평가 기준·후보 source도 수정하지 않았다.

별도 원본 보존 archive `C:/meter-run-packages-20261004/opencode-muse-r01-forensic.zip`에
전체 run·정확한 checkout bytes·동결 source bundle·원본 ledger를 저장했다. 385,407,142 bytes,
SHA-256 `0f57722acd65288fa84b0fa5f4c52bece841c36fba05e3b342eb37116e242fc4`다.
새 root `C:/meter-run-restores-20261004/opencode-muse-r01-forensic`에서 1,807개 원본 파일 hash,
동결 commit/tree/clean 상태·57개 입력·policy review·operator baseline·result validator를 확인했다.
최종 검증 코드는 복원된 operator ZIP에서 읽었으며 원래 run 경로에 의존하지 않는다.
처음의 Git CRLF cached index 판정 실패도 보존하고, index 갱신 후 HEAD tree 동일성과 모든 원본 bytes를 재검증했다.
[복원 기록](evidence/20261004-opencode-cli-opencode-muse-r01/forensic-restore-report.json)은 일반 package 거부와
별도 원본 보존·독립 검증 성공을 구분한다. 일반 포장 도구의 layout 지원 보완은 남은 운영 작업이다.

### 2026-10-05 운영자 보관 도구 보완

종료 후 artifact 수집 단계에 한정해 `scripts/evidence_package.py`를 보완했다.
도구 변경 commit은 `87fe032`이며 실제 사용 파일의 SHA-256과 검증 결과는
[검증 기록](operator-remediation-20261005/validation.json)에 보존했다.
result의 build artifact 경로에서 빌드 폴더를 찾아 수집하고, 한 폴더에 필수 다섯 종류가
모두 있어야 한다. 무관한 root build로 부족한 artifact를 대신 채우지 않는다.
`sdkconfig` 원본 bytes도 함께 보관한다. 관련 회귀 21개가 통과했다.

새 일반 package는 `C:/meter-run-packages-20261005/opencode-muse-r01-layout-fixed`이며,
manifest SHA-256은 `c4f845c4a887a91379e293810824f16dda3e8f590d27b45048baa87ad4a854f0`이다.
독립 경로 `C:/meter-run-restores-20261005/opencode-muse-r01-layout-fixed`에서 348개 inventory 파일,
57개 입력·source commit·7개 artifact·`firmware/sdkconfig` bytes를 확인했다.
package의 operator ZIP에서 추출한 동결 validator로 정책·평가·결과를 다시 검증했다.
[복원 원본](operator-remediation-20261005/restore-audit.json)은 원래 후보 경로를 사용하지 않았음을 기록한다.

원본 일반 package 거부와 별도 원본 보존 archive는 유지한다. 이번 정정은 보관 경로 지원에만
적용하며 최초 정책 부적격·화면 실패·RM 미도달·계측을 바꾸지 않는다.
실행 중 runner·profile·후보 입력·평가 기준·후보 source는 변경하지 않았고 같은 수집 규칙을
이후 모든 후보에 적용한다. [보완 계획과 완료 조건](../../docs/plans/2026-10-04-evidence-artifact-layout-remediation.md)을 따른다.
첫 보완 commit의 Git text 정규화가 감사 JSON의 CRLF bytes를 LF로 저장한 사실을 확인했다.
후속 commit에서 이 감사 디렉터리의 binary 속성을 지정해 원본 bytes를 보존하고 inventory와 Git blob을 재대조했다.

## 후속 1회차

- run `20261004-opencode-cli-opencode-muse-r02`, round 1. 2026-10-04 23:30:48 KST 시작, 최대 7,200초.
- 자신의 최초 동결 commit에서 준비한 새 session이다. 전체 후속 최대 3회·누적 7,200초 안의 첫 회차이며 대체 최초 실행이 아니다.
- [feedback](evidence/20261004-opencode-cli-opencode-muse-r02/candidate-feedback.json)에 사진·장치 수락·공통 입력 연결 진단·고정 기대 동작과 남은 예산을 전달했다. 구현 방법이나 다른 후보 코드는 제공하지 않았다.
- [새 receipt](evidence/20261004-opencode-cli-opencode-muse-r02/execution-preflight.json)와 [실행 직전 검증](evidence/20261004-opencode-cli-opencode-muse-r02/current-checks.json)을 보존했다. CLI 1.18.34, native config/skills·SDK·profile·입력·clean source를 대조했다. 두 운영자 준비 오류는 후보 호출 없이 정정했고 비용 범위를 구분했다.
- 동결 operator checkout에서 별도 hidden process PID 1900으로 실행한다. [launcher](evidence/20261004-opencode-cli-opencode-muse-r02/experiment-launch.json)와 [현재 상태](progress.json)를 확인한다.
- 원본 위치 `C:/meter-followups-20261004/20261004-opencode-cli-opencode-muse-r02/`. 최초와 같은 ledger에 연결한다. 실행 중 새 피드백·권한 변경·보드 접근은 제공하지 않는다.

후속에서도 `git log --oneline -8; echo ---; git status --short | head -n 50` 복합 명령이
native 권한에서 거부됐고 이후 작업이 계속되는 것을 관측했다. 중간 기록은 [현재 상태](progress.json)에 보존한다.
첫 실행 때와 같은 종료 규칙으로 terminal policy review를 수행하며, 권한 완화나 숨은 재시도를 하지 않는다.

[중간 비용 집계](comparison-checkpoint-01.md)는 최초의 실제 1,024.64초·306,858 정규화 token을
전체 시도 비용으로 보존하고 정책 부적격 회차를 품질 표에서 제외한다. 후속 실행 중의 미확정 시간/token은
미측정이며 최초·후속 2개 중 coverage 1/2인 시점의 기록이다. 전체 15개 독립 series의 완료 집계가 아니다.
SDK 설정 완료 후 새 모델 출력 대기 구간도 [현재 상태](progress.json)에 기록한다. 후보 프로세스가 살아 있다고
빌드가 실행 중이거나 제품이 통과한 것으로 간주하지 않으며, 중간 재호출 없이 고정 timeout을 적용한다.

2026-10-05 재개 시 같은 PID/회차가 실행 중임을 확인했다. 23:55:56 KST 펌웨어 빌드 완료 후
23:56:04 KST의 native `Tool execution aborted`를 관측했지만, 00:18 KST 이후 같은 session의
새 read event가 이어졌다. 중간 무응답을 종료나 성공으로 간주하지 않고 기존 회차를 유지한다.
사용자의 `try again` 요청에 따라 운영 작업을 재개했으며 후보를 중복 호출하거나 회차/예산을 초기화하지 않았다.

남은 순서는 후속 종료→새 제출물 동결·정책 review→운영자 업로드·실물/RM 관측→남은 회차/시간 내 판단이다.
정책 위반이 있었던 최초 회차의 비교 부적격을 후속 성공으로 지우지 않는다. 미관측을 제품 실패로 바꾸거나 영상·정밀 시간 증거를 만들어 넣지 않는다.
최초 관측 슬롯은 기록상 종료했고 보드에는 최초 artifact를 유지한다. 다음 업로드는 후속 결과가 동결된 뒤 새 슬롯으로 수행한다. 나머지 4개 최초 예약은 아직 실행하지 않았다.

## 2026-10-05 미시작 예약 갱신

현재 OpenCode series와 후속 회차는 유지하고, 날짜가 지난 나머지 4개 최초 예약만 새 날짜의
ID·개별 ledger·run-bound receipt로 준비했다. 순서는 AGY Flash→AGY Pro→Codex Sol→Codex Luna다.
[예약 원본](reservations-20261005/renewal.json)에 이전 미시작 ID와 새 ID·commit/tree·receipt hash를 연결했다.
10월 4일 예약은 원본 prepared 상태로 보존했다. 갱신 중 제품/모델 구현 호출은 0회다.

동결된 깨끗한 operator checkout에서 준비했으며 기존 baseline/profile·공통 57개 입력을 유지한다.
현재 CLI는 AGY 1.2.14/Codex 0.159.2, SDK는 ESP-IDF v5.3.2이고 native 설정·skills·feature를
이전 준비와 byte 단위로 대조했다. AGY의 MCP·plugins·custom agents가 비어 있음을 native 조회했고
scope 해제 후 전역 파일 원본 bytes 복원을 확인했다. [실행 전 재확인](reservations-20261005/current/current-checks.json)을 따른다.
모델 목록은 선택한 AGY ID의 노출만 확인한다. 새 모델 호출로 entitlement나 quota를 검증한 것으로
표현하지 않고 10월 4일의 실제 capability 원본과 10월 5일 환경 재확인을 구분한다.
실제 시작 직전에도 현재 version·설정·준비 날짜·보드 관측 슬롯을 확인한다.

## 재개 시 확인 순서

manifest·ledger 상태와 launcher PID의 실행 여부를 먼저 확인한다. running 후보를 다시 실행하지 않는다.
terminal 상태이면 실제 비용·raw 로그를 검토하고 결과 동결·정책 review·실물/RM 관측으로 이어간다.
강제 중단이 있었다면 기존 reconcile 절차로 종료 비용을 연결한다.
다른 날의 미시작 최초 예약은 새 ID·ledger·receipt로 준비하며 기존 기록을 보존한다.

## 2026-10-05 후속 1회차 timeout 확인과 종료 후 관측

01:37 KST 확인에서 OpenCode와 runner 프로세스가 모두 종료됐고 manifest/ledger가
`timeout`으로 일치함을 확인했다. 시작 10월 4일 23:30:48.681 KST, 종료 10월 5일
01:30:48.846 KST, 사유 `hard timeout`, 실제 7,200.156초다. runner가 고정 7,200초 후
자식 process tree를 종료했고 종료 처리의 0.156초도 원본 비용에 포함했다.
강제 종료된 회차를 completed나 성공으로 바꾸지 않았으며 숨은 재호출은 없다.

- 후속 원본 token: input 329,658, output 13,117, 정규화 합계 342,775.
  cached 7,565,060, reasoning 11,335, provider total 7,919,170은 별도 필드로 보존한다.
  이 계측은 provider가 내보낸 완료 step의 usage이며 중단된 마지막 요청의 미보고 token을 0으로 추정하지 않는다.
- 최초와 후속 실제 시간 합계 8,224.796초, 보고된 정규화 token 합계 649,633.
  [새 비용 집계](comparison-checkpoint-02.md)는 모든 시도 비용을 보존하고 두 부적격 회차를 품질 표에서 제외한다.
  표의 token coverage 2/2는 두 manifest에 보고값이 있다는 뜻이며 공급자의 미보고 usage까지 입증하지 않는다.
- 원본 raw event 257개, native tool event 107개. line 17에서 복합 git 명령이 거부됐고
  line 20의 새 assistant message에서 작업이 계속됐다. 이후 다른 message의 tool event 96개를 확인했다.
  [운영자 정책 감사](evidence/20261004-opencode-cli-opencode-muse-r02/operator-policy-audit.json)와
  [정책 review](evidence/20261004-opencode-cli-opencode-muse-r02/policy-review.json)에 부적격 판정을 연결했다.
- 최종 result JSON과 선택 문서가 없다. 마지막 native todo는 제출 문서 작성을 in_progress로 남겼다.
  운영자가 후보의 최종 제출물을 대신 생성하지 않는다.
- 후속 최대 3회와 누적 120분은 함께 적용한다. 1회차가 누적 예산을 모두 사용했으므로
  남은 허용 후보 실행 시간은 0초다. 남은 회차 숫자만으로 2·3회차를 시작하지 않는다.

종료 후 57개 입력과 원본 raw/hash·terminal ledger binding을 확인하고 남은 구현을
`354c6475345cb521c92f92e3dce448b0dc5ef58b`에 동결했다.
[동결 기록](evidence/20261004-opencode-cli-opencode-muse-r02/operator-source-freeze.json)에
app/ELF/map/bootloader/partition·sdkconfig·flash 설정의 원본 bytes와 운영자 사본을 연결했다.
후보 source를 수정하거나 firmware를 다시 빌드하지 않았다.
[별도 source bundle](evidence/20261004-opencode-cli-opencode-muse-r02/operator-source-bundle.json)을
생성해 Git 검증과 bytes/hash를 보존했다. 이는 제출 누락 상태의 남은 코드 보존이며 최종 RM·package 완료 판정은 아니다.

독립 Python 28개와 제품 C 모듈을 연결한 host 실행 파일 6개가 통과했다.
그러나 실제 collector CLI에서 동일한 legacy fixture와 기준 시각 `2026-09-30T18:40:49Z`를
사용하면 `STALE_THRESHOLD_EXCEEDED`로 personal-usage 입력을 거부하고 exit 2를 반환한다.
후보 시험의 더 이른 시각에서 통과한 사실과 공통 stale 자극의 실패를 구분한다.
[실제 경로 확인](evidence/20261004-opencode-cli-opencode-muse-r02/operator-observation/common-stimulus-check.json)을 따른다.
후보 sender encoder는 고정 seq 0·1 frame과 byte 단위로 일치하지만 collector→장치 연결 합격은 아니다.

01:45 KST 시작한 별도 운영자 슬롯에서 COM3 VID/PID를 재확인하고 NVS 24K만 초기화했다.
app SHA-256 `8e4eaaab7dd6c66abdc069043583c3805cd942d2afca496e48073bcc0255c75b`의
동결 artifact를 업로드하고 원본 공통 frame을 전송했다. 전송 bytes hash가 기준과 같고
장치의 seq 0/CRC `203D8DF3`, seq 1/CRC `C4CAA941` 수락 로그를 확인했다.
[슬롯 기록](evidence/20261004-opencode-cli-opencode-muse-r02/operator-observation/hardware-slot.json)과
[receiver source 대조](evidence/20261004-opencode-cli-opencode-muse-r02/operator-observation/receiver-source-review.json)를 보존했다.
이번에도 `operator_replay`이며 자동 수락 시간/광학 marker의 null은 유지한다.

사용자에게 현재 LCD 값·화면 방향/잘림·BOOT 세 번 탐색/복귀·30초 유지 상태를 요청했다.
답변 전 RM3~RM5·광학/정밀 시간은 미확인이다. 후속 RM review와 최종 독립 package는
이 관측을 기록한 뒤 진행한다. 보드는 후속 동결 artifact를 유지하고 serial은 닫혀 있다.
다음 후보는 AGY Flash이며 현재 슬롯 평가가 끝나기 전 새 후보를 호출하거나 보드를 덮어쓰지 않는다.

## 2026-10-05 timeout 재개·독립 보존·사용자 요청 재업로드

세션 만료 뒤 동일한 terminal 상태와 예산 소진을 재확인했다. 원본 manifest SHA-256
`b755c90492ef34e6056e1654aae4be48b73723e968666d61a720271af15227f5`와 ledger binding,
동결 source·57개 입력·정책 판정을 다시 검증했고 후보 프로세스는 없다.

실물 관측 전 별도 staging에 운영자 원본을 복사해 보존 package를 생성했다.
원본 manifest의 implementation commit은 아직 null이며 ledger의 reviewed는 false다.
포장용 파생본에만 검증한 동결 commit과 추가 evidence hash를 연결했다.
[변경 필드 기록](timeout-preservation-20261005/manifest-derivation.json)은 두 필드와 원본 hash를 명시한다.
원본 terminal·ledger·정책·후보 source는 그대로 보존했고 제출 누락을 대신 작성하지 않았다.

- package: `C:/meter-run-packages-20261005/opencode-muse-r02-provisional`.
- manifest SHA-256: `9a7c506fe8cd3e861184232134dd2127b847d523997b44a51941ad7a9c045fc3`.
- 독립 복원: `C:/meter-run-restores-20261005/opencode-muse-r02-provisional`.
- [동결 validator 감사](timeout-preservation-20261005/restore-audit.json): inventory 396개·입력 57개·source 사본 46개·artifact 사본 9개·원본 terminal/ledger 결합·정책 확인.
  검증에는 원래 후보 경로를 사용하지 않았다. source 사본과 Git blob, artifact 사본과 원본 hash가 일치한다.
- `result_valid: false`, 정책 부적격과 후속 예산 0초를 유지한다. result가 없어 checkout artifact_paths 목록은 빈 목록이며
  실제 artifact는 byte 단위의 운영자 사본과 동결 Git source로 보존했다. artifact 소실을 뜻하지 않는다.

사용자의 “다시 업로드해줘” 요청으로 02:50 KST 같은 동결 app/bootloader/partition을 COM3에
다시 업로드했다. receiver의 sequence를 초기화하기 위해 기존과 같은 NVS 24K만 초기화했고,
원본 공통 frame seq 0·1을 전송해 두 수락 로그와 wire hash 일치를 확인했다.
[별도 재관측 슬롯](evidence/20261004-opencode-cli-opencode-muse-r02/operator-observation/recapture-r2-20261005/hardware-slot.json)에
요청·artifact·명령·실제 종료 시각·수락·serial 종료를 기록했다. 최초 슬롯을 덮어쓰지 않았다.
이는 운영자 실물 관측 재시도이며 후보 호출·수정 회차·예산 변경·재빌드는 없다.
관측 전 package는 이 재전송과 이후 영상을 포함하지 않는 당시 snapshot이다.

사용자가 제공한 `KakaoTalk_20261005_014936412.mp4`의 원본을 별도 운영자 경로에 보존했다.
길이는 66.57초, 33,013,814 bytes, SHA-256은
`72d18b2e492948ce51f8502f84dd391b0f5ee31d13148e3e7ee7dafcc3f09a4c`다.
파일은 02:48경 저장돼 02:50 재업로드보다 앞선 자료이며 embedded 촬영 시각은 없다.
최초 후속 업로드 뒤 촬영한 자료인지 사용자에게 확인을 요청했다. 파일명 시각을 확정 촬영 시각으로 쓰지 않는다.

[영상 검토](evidence/20261004-opencode-cli-opencode-muse-r02/operator-observation/user-video-01/video-review.json)에서
약 28.5초의 사용량 `openai/five-hour REM 58%`, 30.5초의 글로벌 리셋 `default (no history)`,
32.5초의 STATUS와 시작 STATUS로 돌아오는 탐색을 확인했다. 주간 82%는 보이지 않으며
공통 reset 값 대신 no history가 나온다. STATUS의 STALE:NO와 전송 시각을 LAST-GOOD로 표시한 것도
원본 payload의 stale/관측 시각과 구분해 기록했다. 원본 source의 문자열 검색 범위와 화면 출력도 대조했다.
50초 부근의 실제 USB 케이블 분리·재연결은 전원 차단이며 powered USB 링크 복구 시험이 아니다.
1초 간격 영상 표본이나 전체 길이만으로 30초 무깜박임·정밀 지연·정식 GUI 점수를 확정하지 않는다.

촬영 대상이 확인됐을 때 적용할 RM 초안은 RM1 pass/RM2 partial/RM3 partial/RM4 partial/RM5 pass다.
최종 원본 RM review는 아직 적용하지 않았으며 이 초안은 비용/품질 집계의 최종 판정이 아니다.
촬영 대상 확인 후 RM·최종 package·series 종료 기록을 보존하고 다음 AGY Flash를 시작한다.

## 2026-10-05 후속 최종 RM·증거 복원·다음 대상 시작

사용자가 “맞음: 처음 후속 업로드 이후 촬영”이라고 확인했다. 영상은 최초 후속 업로드 슬롯의
관측에 연결했고 02:50 재업로드 뒤의 영상으로 바꾸지 않았다. 정확한 촬영 UTC는 여전히 알 수 없다.
[확인 기록](review-finalization-20261005/capture-identity-confirmation.json)과
[최종 영상 검토](review-finalization-20261005/confirmed-video-review.json)를 보존했다.

[최종 RM](review-finalization-20261005/reference-review.json)은 다음과 같다.

| 항목 | 판정 | 근거와 한계 |
|---|---|---|
| RM1 | pass | 후보 빌드 성공, 같은 동결 artifact 업로드·실제 receiver 수락. 최종 후보 제출 누락은 별도 유지 |
| RM2 | partial | encoder·수락 성공, 실제 collector의 공통 stale fixture 거부. 실물 전송은 operator replay |
| RM3 | partial | 5h 남은 58% 표시, 주간 82% 미표시 |
| RM4 | partial | 세 종류 화면 표시, 글로벌 리셋 값 누락·stale/관측 시각 부정확 |
| RM5 | pass | 영상의 STATUS→DASHBOARD→GLOBAL RESET→STATUS와 물리 버튼 조작. 화면 데이터 정확성·300ms 정밀 지연은 별도 |

후속 reference는 fail, 정책은 invalid_for_comparison, 제품 합격은 false다. 한 번만 가능한
원본 RM review를 적용해 동결 commit·reference-review·source bundle을 연결했다.
원본 terminal 사본과 review 직후 manifest도 보존했고 종료 후 기록의 추가 evidence만 별도로 연결했다.
최초·후속의 실제 비용과 실패를 지우지 않았다. [series 종료](review-finalization-20261005/series-completion.json)는
누적 수정 예산 소진을 이유로 기록한다. 동결 ledger의 active 표시는 잔여 실행 허가를 뜻하지 않으며
prepare-next의 예산 guard가 추가 회차를 거부한다. 사용자 취소나 새 초기 예산으로 바꾸지 않는다.

최종 package는 `C:/meter-run-packages-20261005/opencode-muse-r02-final`, manifest SHA-256은
`948261ab0ea75f3742b11664086976816dd353cf5f6cd39394a7270422117fd4`다.
독립 경로 `C:/meter-run-restores-20261005/opencode-muse-r02-final`에서 430개 파일을 복원했다.
[동결 validator 감사](review-finalization-20261005/restore-audit.json)는 57개 입력·46개 raw source·9개 artifact·
원본 비용·영상 원본/hash·확인·최종 RM·정책을 대조했고 원래 후보 경로를 사용하지 않았다.
최종 제출이 없어 result_valid는 false이며 전체 제품 합격을 뜻하지 않는다.

다음 순서의 AGY Flash `20261005-antigravity-cli-agy-flash-r01`을 03:09:41.487 KST 시작했다.
모델은 `gemini-3.8-flash-medium`, 최초 한도 7,200초, 동결 baseline·runner·57개 입력·새 receipt를 유지한다.
[실행 launcher](evidence/20261005-antigravity-cli-agy-flash-r01/launch-20261005/experiment-launch-attempt2.json)의
PID 19644와 실제 native init의 model/request-review/candidate checkout을 확인했다.
[실행 직전 확인](evidence/20261005-antigravity-cli-agy-flash-r01/launch-20261005/operator-launch-preflight-r2/current-checks.json)에
CLI 1.2.14·IDF 5.3.2·native MCP/plugins/custom agents 비어 있음·선택 모델 catalog·private scope를 연결했다.
전역 지침/hook은 동결 조건에 따라 session 동안 제거하며 종료 후 원본 bytes로 복원한다.
prompt-and-log·read_isolation:not_enforced·builtin-only-v1이라는 한계는 유지한다.

첫 운영자 런처는 내부 함수 이름인 execute를 CLI 명령에 사용해 parser에서 exit 2로 종료됐다.
[준비 오류 원본](evidence/20261005-antigravity-cli-agy-flash-r01/launch-20261005/operator-launch-attempt1-review.json)에
모델 호출 0회·prepared 유지·예산 예약 0초·전역 설정 복원을 확인했다.
동결 CLI의 실제 `run <directory> --receipt <receipt>` 형식으로 고쳤고 첫 실제 후보를 시작했다.
두 launcher/console/preflight 원본을 구분해 보존하며 숨은 제품 재시도나 허용 조건 변경이 아니다.
AGY 실행 중 운영자 구현 피드백과 보드 접근은 제공하지 않는다. 현재 보드에는 관측을 마친 OpenCode 후속 동결본이 유지된다.

[세 번째 비용 snapshot](comparison-checkpoint-03.md)은 OpenCode의 최종 RM 이후 원본 비용과
새 AGY running 회차를 함께 기록한다. AGY의 최종 비용·제출·정책은 아직 미확정이고 실행 중 policy missing은
최종 부적격 판정이 아니다. OpenCode의 보고된 정규화 token coverage 2/2도 중단된 요청의 미보고 사용량을 뜻하지 않는다.
[native 시작 관측](evidence/20261005-antigravity-cli-agy-flash-r01/launch-20261005/native-start-observation.json)에
지정 모델·request-review·후보 cwd와 raw log prefix의 시점·hash를 연결했다. 진행 중 prefix를 전체 terminal 로그로 보존한 것으로 해석하지 않는다.

## 2026-10-05 AGY Flash 최초 종료·실물 평가·독립 복원

위의 AGY running 기록은 시작 시점의 원본이다. 현재 최초 실행은 03:09:41.488~03:22:24.306 KST,
762.813초에 종료됐다. 마지막 `Test-Path build-host/test_meter_parser.exe, build-host/link_evidence.txt`가
native 권한 정책에서 거부됐으며 이후 도구 호출은 0개다. adapter의 environment_failed·최종 JSON 누락을
유지한다. native result SUCCESS/프로세스 exit 0은 제품 완료를 뜻하지 않는다.
input 1,232,914/output 120,044/정규화 합계 1,352,958, cached 18,738,962/reasoning 46,801/
provider total 1,352,958을 원본 정의대로 보존했다. native tool 123개·raw event 383개이며
per-command exit unknown 25개와 failed lower bound 1개를 실패 1개 확정 계측으로 바꾸지 않았다.
원본 user_interventions null은 유지하고 실행 중 운영자 메시지·권한 grant·피드백 0회를 별도 감사했다.

[별도 종료 snapshot](evidence/20261005-antigravity-cli-agy-flash-r01/terminal-20261005/snapshot-inventory.json)은
102개 파일과 원본 manifest/ledger·전역 설정 복원·57개 입력을 묶는다. 과거 launch snapshot은 유지한다.
[정책 review](evidence/20261005-antigravity-cli-agy-flash-r01/terminal-20261005/policy-review.json)는
접근 범위와 거부 후 즉시 종료를 검토해 eligible이다. prompt-and-log와 OS read 격리 미적용 한계는 유지한다.

남은 구현을 `29e1d7af54a8c9c879e36192ec4ed689e5bbf82d`에 동결했고 Git 변환 전 source 38개와
artifact/설정 10개를 별도로 보존했다. app은 348,352 bytes, SHA-256
`f29c45ff3a570fbc1d2b92aee6ad224f985f1c951821479ca0d901201c3f9c41`이다.
Python 5개·C 실행 파일 4개는 통과했지만 기본 collector의 usage 5개/reset 2개 payload는 공통 기준과 다르다.
공통 frame encoder는 byte 단위로 일치한다. 마지막 native 성공 build 뒤 firmware 변경이 없으며
운영자 source 수정·firmware 재빌드는 없다.

04:14 KST COM3의 NVS 24K만 초기화하고 동결 app/bootloader/partition을 업로드해 hash 검증을 마쳤다.
공통 seq 0 전송은 Write timeout으로 실패했고 bytes_written은 unknown, raw serial은 0 bytes다.
seq 1은 시도하지 않았다. capture 도구의 sent-frames는 write 이전 시도 bytes이므로 전달 증거가 아니다.
후보는 UART_NUM_0를 읽으며 기본 UART console을 설정했다. USB COM3 경로와 불일치는 가능한 원인으로
기록하되 빈 로그만으로 원인을 확정하거나 후보 대신 설정을 고치지 않았다.

사용자가 해당 펌웨어의 `KakaoTalk_20261005_041710515.mp4` 영상을 제공했다.
48.12초/23,640,439 bytes, SHA-256 `7f21cd0b20139ede278a2c75d1e15bd487463d79b6049adbd3f5eb3e93f11aaa`를
원본 보존했고 48개 nominal 1fps frame·contact 4개·읽을 수 있는 8개 frame을 검토했다.
LCD에는 WAITING FOR USB DATA, 글로벌 NO RECENT RESET RECORD, 진단 Sequence NONE/cache 0이 보인다.
화면 순환·시작 화면 복귀는 보이지만 실제 사용량·reset 데이터와 정상 수신 후 BOOT 탐색은 미입증이다.
21.5~22.5초 부근 조작 중 화면 공백의 원인은 미확정이며, 31초 부근 USB 제거는 의도적 전원 차단이다.
이를 연속 30초 무깜박임·자발 재부팅·powered-link 복구·정밀 지연·IMU 합격으로 바꾸지 않는다.

[최종 RM](evidence/20261005-antigravity-cli-agy-flash-r01/evaluation-final-20261005/reference-review.json)은
RM1 pass/RM2 partial/RM3 fail/RM4 partial/RM5 partial, reference fail/product_pass false다.
후보 선택 문서는 제출됐으며, 최종 result JSON은 누락 상태를 유지한다.
최종 package `C:/meter-run-packages-20261005/agy-flash-r01-final`의 manifest SHA-256은
`c800ac8aabdebc10961d7ae7ac9dd4a5fceb47f13fba984afc45552054b1b426`이다.
[독립 복원](evidence/20261005-antigravity-cli-agy-flash-r01/evaluation-final-20261005/restore-audit.json)은
430개 파일·57개 입력·raw source/artifact·동결 Git blob·영상·정책·RM·원본 비용을 package의 operator ZIP
validator로 검증했다. 원래 run/checkout을 읽지 않았으며 Git 텍스트 줄바꿈 차이는 별도 원본 bytes와 blob으로 확인했다.
result_valid는 false다. 한 번만 가능한 RM review 뒤 변경은 operator evidence 연결뿐이며 원본 terminal을 보존한다.

[네 번째 비용 snapshot](comparison-checkpoint-04.md)은 종료된 3개 시도의 비용을 모두 포함한다.
AGY 최초 평가는 완료됐지만 series는 아직 완료되지 않았다. 필요한 후속은 같은 모델/profile/권한에서
자기 직전 결과의 관측·기대·근거만 제공하고 최대 3회 AND 누적 7,200초 안에서 수행한다.

## 2026-10-05 AGY Flash 후속 1회차 시작

`20261005-antigravity-cli-agy-flash-r02`를 04:34:51.469 KST 시작했다. 같은 AGY
`gemini-3.8-flash-medium`·request-review·profile·공통 입력을 유지한다.
`C:/meter-followups-20261005/20261005-antigravity-cli-agy-flash-r02/checkout`의 독립 Git clone에서
자기 최초 동결 source만 이어간다. [후속 준비](evidence/20261005-antigravity-cli-agy-flash-r02/launch-20261005/followup-preparation.json)는
관측·기대·원본 근거 hash·남은 7,200초와 3회를 연결하며 운영자 구현 방법·제품 patch를 포함하지 않는다.
이번 실행도 후속 누적 예산에 포함하고 최초 environment_failed의 비용·제출 누락·최종 package는 유지한다.

CLI/SDK·clean 준비 checkout·57개 공통 입력/후속 고정 근거·전역 파일·native MCP/plugins/custom agents·
모델 목록을 재확인했다. 새 receipt SHA-256은
`f827db5266b8a27d654c1fdbbd08ef6eedccfb38c2643e2daf544748823ad81b`다.
원본 capability는 10월 4일의 증거이며 이번 preflight의 모델/제품 호출은 0회다.
[native 시작 관측](evidence/20261005-antigravity-cli-agy-flash-r02/launch-20261005/native-start-observation.json)은
지정 모델·request-review·새 후보 cwd와 당시 raw prefix를 검증한다.
[launcher](evidence/20261005-antigravity-cli-agy-flash-r02/launch-20261005/experiment-launch.json)는
PID 30356이며 대화와 별도로 동결 runner의 한도를 적용한다. 전역 AGY scope는 자식 종료 후 복원한다.
후보에게 serial/flash 접근이나 실행 중 추가 피드백을 제공하지 않으며, 보드는 평가한 최초 펌웨어를 유지한다.
실행 중의 policy pending과 비용 null은 최종 판정이 아니다. 재개 시 [현재 계측](progress.json)·원본 manifest/ledger·
native process/owner부터 확인하고 같은 후속을 다시 호출하지 않는다.

## 2026-10-05 AGY Flash 후속 1회차 종료 확인

사용자의 진행 상황 확인 요청 중 04:59:40.678 KST에 `20261005-antigravity-cli-agy-flash-r02`가
completed·exit code 0으로 종료됐다. 실행 시간은 1,489.219초(24분 49.219초)이며
input 1,472,560·output 140,404·정규화 합계 1,612,964 token, cached 22,864,333·reasoning 90,823을
원본 정의대로 보존했다. tool calls 177이며 failed_commands·user_interventions의 원본 null은 유지한다.

[종료 상태](evidence/20261005-antigravity-cli-agy-flash-r02/terminal-status-20261005/terminal-status.json)와
[제출 JSON](evidence/20261005-antigravity-cli-agy-flash-r02/terminal-status-20261005/candidate-submissions/results/20261005-antigravity-cli-agy-flash-r02/end-to-end-result.json)을 보존했다.
후보 로그에는 USB Serial/JTAG 수신·legacy collector·화면/입력 로그 보완, firmware build 완료,
Python 6개 통과와 결과 validator VALID가 있다. 최종 제출물의 hardware는 not_run, product_pass는 false다.
이 로그를 실물 동작이나 운영자 독립 검증의 근거로 바꾸지 않는다. 새 펌웨어 업로드는 아직 하지 않았다.

**C 시험 근거 문제:** 최종 r02 `build-host/CTestTestfile.cmake`가 r01 checkout의 실행 파일 4개를
직접 호출한다. cache와 build.ninja의 경로 변경만으로 이 파일은 갱신되지 않았다.
따라서 r02 로그의 CTest 4/4 통과는 이번 수정 코드의 검증이 아니다.
이전 cache 경로로 수행한 빌드가 최초 checkout의 `build-host/.ninja_log`를 변경한 것도 기록했다.
최초 펌웨어/설정 원본 10개의 hash는 그대로이며 기존 raw snapshot·source bundle·독립 package는 보존한다.
빌드/source/artifact 연결과 접근 범위의 전체 감사는 아직 하지 않았으므로 최종 정책 판정은 pending이다.

종료 원본 manifest SHA-256은 `54ee10e9988cb39a07de64bc8528895c9a2b8f0b6693c301ed42019a1c8f1062`다.
manifest·ledger·raw 로그·41개 source·10개 artifact/설정 원본을 복사했고 manifest/ledger는 변경하지 않았다.
실제 AGY process 부재와 전역 settings/instructions/hooks의 복원 hash·owner 부재도 독립 확인했다.
이번 확인은 운영자 코드 수정·firmware 재빌드·보드 접근 없이 수행했다.

다음 단계는 terminal 구현의 Git 동결, 정책 및 빌드/시험 근거 검토, 동결 validator와 공통 fixture의
독립 검증, 이후 운영자 업로드·실물/RM 평가다. 후속 잔여 5,710.781초·2회를 이번 종료 비용에서 계산하며
같은 회차를 재시작하지 않는다. 현재 series 평가와 다음 회차 판단 전에 AGY Pro를 시작하지 않는다.

## 2026-10-05 AGY Flash 후속 1회차 동결·독립 검증·업로드

사용자가 현재 진행 단계와 업로드/촬영 절차를 확인해, [후속 평가 계획](../../docs/plans/2026-10-05-agy-flash-followup-evaluation.md)에 따라 평가를 이어갔다.
종료 raw source 41개·artifact/설정 10개를 기존 사본과 대조하고 구현을
`94018f1785a590e1514ef1b5145c40f0c03ffca3`으로 동결·bundle 보존했다. terminal manifest/ledger는 변경하지 않았다.

[정책 review](evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-stage-20261005/policy-review.json)는
invalid_for_comparison이다. native CTest 3회가 r01의 실행 파일 4개를 호출했고 inherited cache를 사용한
build가 이전 checkout에 접근했다. 후속 prompt의 이전 run 접근 제한을 충족하지 못했다.
운영 도구가 추적된 build 출력/절대 경로를 clone에 승계한 기여를 기록하며 후보의 의도를 추정하지 않는다.
이 회차의 품질을 같은 조건 순위에 넣지 않고 전체 비용·실물 결과는 보존한다.
누락 파일 오류 3건은 permission denial이 아니며 stop-on-denial 위반으로 분류하지 않는다. 실행 중 운영자 개입 감사는 0회이며 원본 telemetry의 null은 유지한다.

[독립 host 검증](evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-stage-20261005/operator-observation/host-checks.json)은
동결 operator validator로 제출 JSON을 검증했고 Python 6개 시험이 통과했다. r02 실행 파일 4개를 직접 실행한 기록도 보존했다.
원래 CTest는 r01 실행 파일을 사용하므로 이번 source 증거로 쓰지 않는다. 대신 같은 LLVM/MinGW compiler로
`C:/meter-host-evaluations-20261005/agy-flash-r02`에 host만 새로 빌드해 C 시험 4개를 통과했다.
이 별도 host 검증은 제출 파일·원본 로그·정책 판정을 수정하지 않는다. firmware를 운영자가 다시 빌드하지 않았다.

ESP-IDF project/compile database가 현재 r02 checkout을 가리키고 마지막 후보 build 이후 firmware source 수정이 없음을 확인했다.
[실제 collector](evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-stage-20261005/operator-observation/common-stimulus-check.json)는
default 5 usage/2 reset, legacy 1 usage/2 reset이며 모두 공통 payload와 다르다. legacy의 percent_remaining은 58%/82%지만
provider/agent/snapshot identity, stale/error/reset 의미 등이 다르다. 고정 payload를 넣은 encoder의 seq 0·1 wire 일치는 별도다.

[하드웨어 슬롯](evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-stage-20261005/operator-observation/hardware-slot.json)은
COM3의 VID303A/PID1001·보드 serial을 확인하고 NVS 0x9000/0x6000만 초기화했다.
05:38:52.012 KST에 원본 bootloader/partition/app의 업로드와 esptool hash 검증을 마쳤다.
app 343,856 bytes SHA-256은 `3fe7cc55c2a0af238b869cc635571ce38584145f206e97f47154fb81637ed467`이다.

[공통 capture](evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-stage-20261005/operator-observation/reference-capture-r1/capture.json)는
seq 0·1 각각 bytes_written 1,543이며 write timeout은 없었다. 실제 14,632-byte serial에는
Frame accepted 기록이 없고 [LoadProhibited panic과 Rebooting](evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-stage-20261005/operator-observation/panic-source-review.json)이 각각 2회 있다.
원본 ELF로 backtrace를 해석하면 gdma_default_tx_isr와 frame parser/serial 수신 호출 경로가 보인다.
이 symbol 관측만으로 정확한 원인을 확정하지 않으며 운영자가 후보 source를 고치거나 재시도하지 않았다.
PC 쓰기 완료는 장치 수락이나 화면 표시의 증거가 아니다.

현재 보드에는 이 후속 원본이 있으며 serial을 닫고 사용자 광학/BOOT 관측을 기다린다.
촬영 대상·LCD 문구/비율·방향/잘림·30초 유지·BOOT 3회 조작과 복귀를 영상에 연결한다.
화면이 비거나 깜박임/재부팅·무반응이 있으면 그 결과를 보존한다. 영상 관측 전 RM review를 적용하지 않았다.
후속 잔여 5,710.781초·2회, 원본 비용과 최초 판정은 유지하며 추가 후보 호출은 하지 않았다.

[평가 단계 snapshot](evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-stage-20261005/snapshot-inventory.json)은 123개 파일/hash를 보존한다.
공개 사본 복사 중 Windows 260-character 경로 제한 오류 1건이 있었으며 기존 부분 사본의 bytes를 대조하고 extended path로 보완했다.
오류·복구를 sidecar에 남겼고 모델 호출·제품 수정·업로드 재시도는 없다. 최종 RM와 package의 독립 복원은 영상 이후다.
