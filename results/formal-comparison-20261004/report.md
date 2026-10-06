# 정식 동일 조건 비교 실행 기록

상태: 2026-10-07 Luna 후속2 평가 완료: build·COM3 원본 실행은 RM1 pass, 공통 host 경로·USB 첫 수신과 완전한 수락 미확인을 구분해 RM2 partial이다. 38.55초 영상에서 글자 출력은 생겼지만 회전·중복·잘림으로58%/82%와 세 정보 화면을 읽을 수 없어 RM3/RM4 fail이다. 사용자는 BOOT와 RESET 모두 눌렀다고 확인했으며 정확한 조작 시점/횟수가 없어 분리된 BOOT 순환은 RM5 not_run이다. 화면 변화가 자동 재부팅이라는 추정은 하지 않는다. Reference fail·product_pass false, 이번 정책 eligible·과거 series invalid를 유지한다. 최종575파일 package 독립 검증 완료; native 사용량 한도 종료·token null·전체 coverage13/14·알려진57,517,475 token을 보존한다. 정상 가독 화면 미도달이므로 기존 승인 범위의 마지막 후속3을 준비할 수 있다. 잔여2,965.735초·최대1회이며 timeout 상한floor2,965초다. 아직 마지막 후보 호출은 없다.
독립 series 종료3/15이며 전체 비교는 미완료다. 아래 기록은 각 당시 관측이며 최신 상태는 위 상태와 마지막 갱신을 따른다.
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

## 2026-10-05 AGY Flash 후속 1회차 최종 평가·사용자 요청 대기

사용자가 이번 펌웨어의 `KakaoTalk_20261005_054708010.mp4` 영상을 제공하며 다음 모델로 넘어가지 말고 기다리도록 지시했다.
현재 회차의 평가와 증거 보존만 마쳤으며 추가 AGY 회차·AGY Pro·Codex 호출, 재업로드나 재전송은 하지 않았다.
이 기록은 위 평가 대기 시점 이후의 상태이며 과거 원본 판정과 snapshot은 유지한다.

영상은 46.3초·22,018,701 bytes, SHA-256 `e759b25d693b0d4774e463bfcb60b9b71c9a5b6f067945770ccf5d8c6bc3672b`다.
원본은 run의 `operator-observation/user-video-01/source.mp4`에 보존했고 공개 snapshot에는 metadata·검토·contact 4개·읽을 수 있는 frame 12개를 연결했다.
[영상 검토](evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-final-20261005/operator-observation/user-video-01/video-review.json)에서
대시보드→글로벌 리셋→진단→대시보드 순환이 두 차례 보인다. WAITING FOR USB DATA, NO RECENT RESET RECORD,
Sequence NONE·사용량/리셋 cache 0이 남아 있고 58%/82%·실제 리셋 값은 표시되지 않는다.
일부 전환에서 제목과 본문이 서로 다른 화면으로 보인다. 영상 중 Uptime 421초와 뒤의 3초는 재시작을 나타내지만
가림·조작 구간 때문에 원인은 미확정이다. 이를 자발 재부팅으로 단정하거나 개별 BOOT/IMU trigger와 연속 30초 무깜박임·정밀 지연을 합격 처리하지 않는다.

[최종 RM review](evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-final-20261005/reference-review.json)를 한 번 적용했다.
RM1 pass/RM2 partial/RM3 fail/RM4 partial/RM5 partial이며 reference fail/product_pass false다.
이전 회차 경로 접근의 invalid_for_comparison 판정은 유지한다. 원본 terminal 비용·실행 상태·후보 제출물은 고치지 않았다.
추가 operator evidence와 새 host 검증 artifact 9개는 sidecar로 구분해 기록했으며 제품 source/firmware를 수정하지 않았다.

최종 package `C:/meter-run-packages-20261005/agy-flash-r02-final`의 manifest SHA-256은
`b0e2880fc7c786ae338b9d1870ccd4c3510bf9afb3f5881089ff4d23515f244c`다.
[독립 복원 감사](evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-final-20261005/restore-audit.json)는 원본 checkout을 사용하지 않고
package의 동결 operator ZIP으로 501개 파일·57개 입력·41개 source·10개 artifact/설정 사본·Git blob·영상·비용·정책·최종 RM·대기 지시를 검증했다.
복원 경로를 반영한 결과 manifest/JSON 2개 변경과 raw 원본 보존을 구분했다. `result_valid: true`는 제출 형식과 증거 검증이며 제품 합격이 아니다.
[공개 최종 snapshot](evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-final-20261005/snapshot-inventory.json)은 40개 파일의 hash를 연결한다.

[비용 checkpoint 05](comparison-checkpoint-05.md)는 종료된 4회 비용을 포함하고 후속을 독립 반복으로 집계하지 않는다.
AGY Flash 최초+후속의 실제 시간은 2,252.032초·정규화 token 2,965,922다. 최초 결과와 각 회차 비용은 별도로 보존한다.
후속 잔여 5,710.781초·2회는 그대로이며 이번 사용자 보류를 series 완료나 예산 소진으로 기록하지 않는다.
독립 series 완료는 OpenCode 1개/예정 15개, 후보 호출은 시작 4회·종료 4회다.

[대기 지시](evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-final-20261005/operator-user-hold.json)와 [현재 계측](progress.json)에 따라
추가 수정 회차와 다음 모델은 사용자 재개 지시 전까지 시작하지 않는다. 보드는 05:38:52 KST에 올린 동일 원본 펌웨어를 유지하며 serial은 닫았다.
현재 회차를 재호출하거나 남은 예산을 초기화하지 않는다.

## 2026-10-05 다음 모델 진행 재개·AGY Pro 최초 실패와 후속 1회차

사용자의 “다음 모델 ㄱㄱ”에 따라 첫 블록의 다음 `gemini-3.1-pro-high`로 진행했다.
이는 위 Flash 대기의 후속 지시이며 [기존 대기 원본](evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-final-20261005/operator-user-hold.json)은 유지한다.
Flash 후속 잔여 5,710.781초·2회는 보류하고 다음 [독립 Pro 예약](reservations-20261005/renewal.json)을 사용했다.
별도 브랜치 `experiment/antigravity/antigravity-cli/agy-pro`에는 공통 입력 57개와 실행 문맥만 있으며 Flash 구현·결과를 제공하지 않았다.
같은 날짜의 미시작 예약·개별 ledger·baseline/profile/receipt·CLI 1.2.14·ESP-IDF 5.3.2·native inventory와 scope를 재검증했다.
제품 호출 전 model catalog는 확인했으며 새 connectivity/entitlement probe로 별도 모델 호출을 하지 않았다.

Pro 최초 `20261005-antigravity-cli-agy-pro-r01`은 22:15:28.585~22:16:36.793 KST, 68.203초다.
input 84,301·output 5,560·정규화 89,861 token, cached 167,271·reasoning 4,593은 원본 필드대로 보존했다.
실제 [native 로그](evidence/20261005-antigravity-cli-agy-pro-r01/evaluation-final-20261005/stdout.jsonl)는 지정 모델·request-review·Pro cwd,
자기 입력 파일 읽기 10회와 첫 command의 거부를 기록한다. 거부된 명령은 `mkdir -p firmware/main pc firmware/components/state_machine scripts tests`다.
raw line 29의 denial 뒤에는 native result 외 새 assistant/tool 행동이 없으며 Git 작업 트리도 변경되지 않았다.
native result의 SUCCESS/exit 0과 달리 동결 runner는 environment_failed로 판정했다.
실행 중 운영자 구현 피드백·후보 대신 source 수정·권한 완화·동일 최초 재호출은 없었다.

[정책 review](evidence/20261005-antigravity-cli-agy-pro-r01/evaluation-final-20261005/policy-review.json)는 eligible이며
[RM review](evidence/20261005-antigravity-cli-agy-pro-r01/evaluation-final-20261005/reference-review.json)는 RM1 fail/RM2~RM5 not_run, reference fail/product_pass false다.
코드·host 시험·firmware·선택 문서·최종 JSON은 없고 Pro 업로드도 없다. 후보 local baseline commit
`ba5609db6fbf6392166586e50341c6e14a26112f`를 그대로 동결·bundle로 보존했다. 설치된 Flash 화면을 Pro 동작으로 평가하지 않는다.
global settings/instructions/hooks 원본 hash 복원·owner/native process 부재도 확인했다.

최초 315개 package는 등록된 evidence만 수집하므로 별도 보존했던 terminal-originals가 없어 확장 복원 감사에서 FileNotFoundError가 발생했다.
원본 package/restore/오류를 보존하고 [운영 보관 정정](evidence/20261005-antigravity-cli-agy-pro-r01/evaluation-final-20261005/operator-package-coverage-correction.json)으로
operator.evidence에 원본·복원 sidecar만 추가했다. RM review를 다시 적용하거나 비용·제품·권한·baseline을 바꾸지 않았다.
최종 `C:/meter-run-packages-20261005/agy-pro-r01-final-v2` manifest SHA-256은
`66d9141c9c1945fb214587680c3d84e9b1dd20eae2163f4aec372bafb98ff746`이다.
[독립 복원 감사](evidence/20261005-antigravity-cli-agy-pro-r01/evaluation-final-20261005/restore-audit.json)는 338개 파일·57개 입력·raw terminal/비용·정책/RM·동결 Git를
package의 자체 operator ZIP에서 추출한 validator로 검증했다. 최종 제출 누락과 `result_valid: false`를 유지한다.
[공개 최초 snapshot](evidence/20261005-antigravity-cli-agy-pro-r01/evaluation-final-20261005/snapshot-inventory.json)은 50개 파일/hash를 보존한다.

기존 허용 후속 절차로 `20261005-antigravity-cli-agy-pro-r02`를 자기 직전 source와 실패 기록만 연결해 준비했다.
[시작 근거](evidence/20261005-antigravity-cli-agy-pro-r02/launch-20261005/native-start-observation.json)는 22:29:17.275 KST의 실제
동일 Pro model·request-review·후속 cwd를 확인한다. launcher PID는 15328이며 대화와 독립된 process가 최대 시간을 적용한다.
새 receipt SHA-256은 `758da98249d099b97aa7752ed6d2f4f57ea606d829f47b933f38811586f2e7a3`다.
후속 최대 3회 AND 누적 7,200초에 이번 회차를 포함한다. 원본 최초 비용과 정책 적격성은 그대로이고
후속 terminal 정책·제품/RM·최종 비용은 아직 미판정이다. Native 시작 prefix를 최종 성공 로그로 사용하지 않는다.

보드는 Flash r02의 같은 원본 펌웨어를 유지한다. 현재 후보에게 serial/flash·실행 중 구현 피드백을 제공하지 않는다.
Pro 종료 후 동결·제출·정책·host·실물/RM 순서로 평가하며 그전에 Codex를 함께 시작하지 않는다.
재개 시 [현재 계측](progress.json)·Pro manifest/ledger·scope owner·실제 launcher/child부터 확인하고 같은 후보를 재호출하지 않는다.

## 2026-10-05 AGY Pro 후속 1·2회차 평가·마지막 후속 시작

후속 1회차 r02는 22:30:38.899 KST에 native `Copy-Item`의 제조사 sdkconfig.defaults 복사 요청이 거부돼 종료했다.
40개 raw event를 검토했으며 일반 write_to_file 인자 누락 오류를 권한 거부로 분류하지 않는다. 허용된 own checkout·SDK/manufacturer 참조와 own built-in task status만 사용했고 마지막 거부 뒤에는 새 assistant/tool 행동이 없다.
81.625초·정규화 94,452 token, input 90,024·output 4,428·cached 456,502·reasoning 2,842를 원본으로 보존했다.
firmware/CMakeLists.txt의 raw 446 bytes를 Git 동결 `5e1b658783da67995f4330ed1fafa98b842270cc`와 연결했다.
정책 eligible·RM1 fail/RM2~RM5 not_run이며 펌웨어·최종 JSON·선택 문서는 없다.
[346개 파일의 독립 복원](evidence/20261005-antigravity-cli-agy-pro-r02/evaluation-final-20261005/restore-audit.json)은 package manifest
`fe266ea2f3bfd5a81fec10158a82f0c290ec1909d976ee169d467e27c8a2947d`와 원본 비용·57개 입력·raw source·Git blob을 확인했다.
최초 audit의 raw LF/복원 CRLF byte 비교 실패는 [정정 기록](evidence/20261005-antigravity-cli-agy-pro-r02/evaluation-final-20261005/agy-pro-r02-final-audit-correction.json)으로 보존한다.
446-byte raw와 457-byte Git 복원은 11개 줄바꿈만 다르며 내용과 동결 Git blob `96c31fa432e7adcb909d75d44ab9c29f1e552056`이 같다. 원본 candidate source나 비용을 고친 것이 아니다.

후속 2회차 r03는 22:45:47.858 KST 시작 후 51.875초에 native `Get-ChildItem -Path <자기 firmware 경로> -Recurse`가 거부돼 종료했다.
31개 raw event에는 declared manufacturer source view와 own file write, 기존 CMakeLists overwrite 인자 오류가 있다.
마지막 거부 후 새 행동은 없으며 정책 eligible·RM1 fail/RM2~RM5 not_run이다.
정규화 70,679 token, input 67,351·output 3,328·cached 199,768·reasoning 1,682를 보존했다.
partial source는 CMakeLists와 sdkconfig.defaults 2개이며 commit `8059dbf481d7a394a985d8757b0b331fc625b40a`에 동결했다.
[349개 파일의 독립 복원](evidence/20261005-antigravity-cli-agy-pro-r03/evaluation-final-20261005/restore-audit.json)은 manifest
`5318af334e9a71af67c29c111d64a820ce99330a79183dbce9d2de94c0ebfce6`와 57개 입력·원본 비용·raw partial source/Git를 검증했다.
두 회차 모두 최종 제출물·펌웨어가 없어 `result_valid: false`이며 Pro 업로드/광학 관측은 없다.

종료 전 마지막 단계만 추적하던 startup 문서는 위 시점별 종료 원본과 구분한다.
Windows 준비 helper stderr의 Git LF/CRLF 경고가 PowerShell에서 exit 1로 표시돼도 새 prepared run·ledger·launcher AST를 검사해 성공한 예약을 다시 생성하지 않았다.
r02 공개 사본 수집 중 변수 누락은 partial bytes를 대조한 뒤 보완했으며 모델 호출·RM review를 반복하지 않았다.
이 운영 기록의 오류·보완은 제품 코드·권한·baseline·후보 비용과 별개다.

[남은 후속 계획](../../docs/plans/2026-10-05-agy-pro-remaining-followups.md)에 따라 마지막 r04를 자기 직전 source·관측만 연결해 준비했다.
[Native 시작](evidence/20261005-antigravity-cli-agy-pro-r04/launch-20261005/native-start-observation.json)은 22:50:11.286 KST에
동일 Pro model·request-review·r04 cwd를 확인한다. launcher PID 30748, 새 receipt SHA-256
`87f324a701a3f6dd1caa25c9c76d55817dcc91841042abb275e2f2317a4a8522`다.
후속 잔여 7,066.5초·1회에서 timeout 7,066초를 적용했다. r04 종료 후에는 남는 시간과 무관하게 최대 3회에 도달해 추가 회차를 생성하지 않는다.
현재 terminal 비용·정책/RM·제출·하드웨어 결과는 미판정이다. 현재 native log prefix는 최종 성공 증거가 아니다.

## 2026-10-05 AGY Pro 최종 회차 평가·회차 한도 종료

위 r04 시작 이후 22:58:07.087 KST에 마지막 회차가 종료됐다. 실제 475.797초·정규화 405,997 token이며
input 378,169·output 27,828·cached 1,198,725·reasoning 18,184를 원본으로 보존했다.
96개 raw event를 모두 검토했다. 같은 Pro model·request-review·자기 checkout/고정 입력만 사용했고
마지막 `Get-FileHash -Algorithm SHA256 firmware/main/meter_state.c, firmware/main/meter_state.h, docs/compile-link-evidence.md`가 거부됐다.
그 뒤 새 assistant/tool 행동은 없으므로 정책은 eligible이다. 권한·profile·task를 바꾸거나 구현을 대신 수정하지 않았다.

후보는 C state module·header·host driver와 빌드/링크 설명을 작성했고 `test_meter_parser.exe` 177,664 bytes를 빌드했다.
이는 partial host adapter이며 CMake의 compiler ABI `.bin` 2개도 firmware artifact로 분류하지 않는다.
실제 firmware app/ELF·PC collector/sender·최종 result JSON·선택 문서가 없어 Pro 업로드와 광학/BOOT 관측은 없다.
자신의 source 7개와 host build artifact/config 6개를 raw bytes로 보존하고 commit
`ef6aa727fa3539454708f223d965a1cb40197a56`에 동결했다. RM review는 한 번 적용했고 RM1 fail/RM2~RM5 not_run,
reference fail/product_pass false다. 이미 설치된 Flash 펌웨어는 Pro 결과로 평가하지 않는다.

[최종 독립 복원](evidence/20261005-antigravity-cli-agy-pro-r04/evaluation-final-20261005/restore-audit.json)은
`C:/meter-run-packages-20261005/agy-pro-r04-final`의 361개 파일을 자체 operator ZIP의 동결 validator로 검사했다.
manifest SHA-256은 `aaf375f63861eb47e9e65ce71429e52badb13936cf2e22dba0556e3218048da3`다.
57개 입력·raw source/host artifact·Git blob·원본 terminal/비용·정책/RM·제출 누락과 `result_valid: false`를 유지한다.

최초 운영자 host 시험 29건은 기본 PATH에 LLVM/MinGW runtime DLL 경로가 없어 모두 exit `0xC0000135`였다.
그 [초기 기록](evidence/20261005-antigravity-cli-agy-pro-r04/evaluation-final-20261005/operator-host-checks.json)은 원본 package에 보존했다.
이 loader 오류를 candidate 의미 검사 29건 실패로 해석하지 않는다.
[보완 host 검증](evidence/20261005-antigravity-cli-agy-pro-r04/evaluation-final-20261005/post-package-host-runtime-check.json)은
원본 checkout을 사용하지 않고 독립 복원된 같은 executable·동결 fixture/evaluator와 CMakeCache에 기록된 compiler DLL 경로로 실행했다.
process-local PATH만 보완해 29개 중 12 pass/17 fail이며 executable/source/후보 비용은 그대로다.
검증 대상은 partial state module와 mock normalizer다. 실제 firmware·collector·device의 동작으로 확장하지 않는다.
이 보완 시험과 series 종료 metadata는 main package의 hash를 연결한 별도 후속 operator 근거이며 원본 package를 다시 쓰지 않았다.

[Series 종료](evidence/20261005-antigravity-cli-agy-pro-r04/evaluation-final-20261005/operator-series-completion.json)는
최초 1회+후속 3회, 총 677.5초(11분 17.5초)·정규화 660,989 token, 후속 누적 609.297초다.
후속 시간은 6,590.703초 남지만 회차가 0이므로 derived state는 remediation_round_limit_reached다.
동결 manager가 fail-reviewed ledger를 active로 두는 원본은 유지하며 최대 3회 guard 때문에 추가 prepare는 허용하지 않는다.
회차/예산 초기화·대체 최초 호출·권한 완화는 없다. 전역 settings/instructions/hooks 복원과 native owner/process 부재를 확인했다.

[비용 checkpoint 07](comparison-checkpoint-07.md)은 전체 종료 8회와 모든 실패 비용을 포함한다.
Pro의 네 environment_failed를 일반 모델 코딩 능력의 품질 순위로 해석하지 않는다. 후속은 독립 반복으로 집계하지 않는다.
현재 독립 series 종료는 OpenCode·Pro 2개/예정 15개이며 Flash는 남은 5,710.781초·2회를 보류 상태로 보존한다.
이번 사용자 지시의 다음 대상 Pro 처리는 마쳤고 다음 순서 Codex Sol/Luna는 미시작이다. 현재 board upload는 Flash r02 원본 그대로이며 serial을 열지 않았다.

## 2026-10-05 Codex Sol 최초 실험 시작

사용자의 “그럼 다음 모델로 넘어가자”로 다음 `gpt-6-sol`·medium의 독립 최초 실험을 시작했다.
[실행 계획](../../docs/plans/2026-10-05-codex-sol-initial-launch.md)의 시작 완료는 제품 구현 완료가 아니다.
같은 날짜의 미실행 run `20261005-codex-cli-gpt-6-sol-r01`과 별도 ledger·브랜치
`experiment/openai/codex-cli/gpt-6-sol`·clean commit `95e7e431cda7dc507668c8b7eea986b41204f57c`를 검증했다.
제품 코드 없는 공통 입력 57개·baseline `272875140d1998d458e26fdb2f6deab5e5d8f7b5`·동결 profile을 유지한다.
Pro/Flash의 구현·결과·피드백은 후보에게 제공하지 않는다.

CLI `codex-cli 0.159.2`·ESP-IDF 5.3.2·compiler/ninja/git·native skills/features와 hook 비활성화를 현재 재확인했다.
새 run-bound receipt SHA-256은 `293133d0da30b36dbc3c9a5644cbb617c38567422243615a7e52c6bfa6dc725c`다.
2026-10-04 capability 증거를 보존하고 현재 준비에서 모델 turn은 0회였다.
Native app-server inventory는 같은 확장 override를 쓰지만 exec `--ignore-user-config`와 설정 계층이 다르다는 범위를 기록한다.
외부 plugin/app/memory/hook과 발견된 사용자 skill은 동결 profile대로 비활성화하고 global 설정은 바꾸지 않는다.

[실제 시작](evidence/20261005-codex-cli-gpt-6-sol-r01/launch-20261005/native-start-observation.json)은
23:56:01.520 KST·launcher PID 10236·candidate PID 22140·thread `01a10c90-8a40-7f00-98e5-d8627a20ba62`다.
[실제 process](evidence/20261005-codex-cli-gpt-6-sol-r01/launch-20261005/process-at-start.json)의 argv가
명시된 `gpt-6-sol`·medium·권한·확장 비활성화와 정확히 일치한다. JSONL이 resolved model/cwd를 방출하지 않으므로 이를 native 검증했다고 추정하지 않는다. Runner의 Popen cwd와 explicit argv만 기록한다.
[공개 snapshot](evidence/20261005-codex-cli-gpt-6-sol-r01/launch-20261005/snapshot-inventory.json)은 22개 파일의 원본 bytes/hash를 보존한다.

최초 최대 7,200초의 runner는 대화와 독립해 실행 중이다. 이후 날짜 변경은 시작된 이 회차를 재예약하거나 중복 호출할 이유가 아니다.
종료 후 원본 source·계측·제출을 동결하고 정책·host·제품/RM를 평가한다. 업로드 가능한 ESP32 artifact가 있어야 COM3와 사용자 영상 관측으로 이어간다. 실행 중 운영자 구현 수정·피드백·serial/flash는 없다.
현재 제품·정책·RM·최종 비용은 미판정이며 성공으로 집계하지 않는다. 호출 시작 9회·종료 8회, 독립 series 종료 2개/15개다.
Pro 종료와 Flash 잔여 5,710.781초·2회·보드 원본은 보존하고 Codex Luna는 함께 시작하지 않는다.

## 2026-10-06 Codex Sol 최초 평가·실물 관측 완료

위 시작 기록 이후 최초가 00:37:01.691 KST에 completed·exit 0으로 종료됐다.
실제 2,460.156초(41분 0.156초), tool 124개(명령 81·파일 변경 43), 일반 명령/빌드/시험 오류 5개다.
260개 raw event를 검토했고 권한 거부·serial/flash·온라인 접근·다른 후보 구현 접근·실행 중 구현 피드백은 관측되지 않았다.
정책은 [eligible](evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/policy-review.json)이다.
원본 개입 계측 null과 운영자 감사 0회를 구분한다. OS 읽기 격리는 미강제이며 native resolved model/cwd 미방출 한계는 유지한다.

원본 token은 input 11,987,074·output 54,062·cached 11,815,680이다. Codex cached는 input에 포함되며
고정 정규화 total은 input+output=12,041,136이다. Reasoning/provider total은 null이다.
이 수치를 전부 새로 소비한 uncached token이나 금전 비용으로 해석하지 않으며 AGY의 cache 정의와 직접 비용 순위를 만들지 않는다.
[비용 checkpoint 08](comparison-checkpoint-08.md)은 종료 9회의 실패·timeout·환경 실패 비용도 모두 포함한다.
독립 반복은 아직 모델별 3개를 충족하지 않았고 후속 5회는 반복 수에 포함하지 않는다.

[Source 동결](evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/operator-source-freeze.json)은
`2257fffaa5316773d08fe3353356112c7002159d`이며 raw source 22개·artifact/config 21개를 보존했다.
마지막 firmware build raw line 248 뒤 firmware source 변경이 없다. App 309,936 bytes,
SHA-256 `cefa0a2be742f4260ffcc8f3b83e2d35314e4caf8fb2a915a10a9a552fde6d78`와 ELF/map/bootloader/partition이 존재한다.
후보의 최종 JSON·선택 문서가 있으며 제출 형식 검증은 통과한다. 운영자는 후보 JSON을 실물 판정으로 덮어쓰지 않았다.

별도 복원본의 [host 검사](evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/operator-observation/independent-host-checks/host-checks.json)는
Python 5개·C receiver/state·idle backlight·Python frame→production C 자체 시험을 통과했다.
기록된 compiler runtime만 process-local PATH에 넣고 보관 executable을 직접 실행했으며 CTest의 이전 절대 경로를 사용하거나 firmware를 재빌드하지 않았다.
[공통 입력 검사](evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/operator-observation/independent-host-checks/common-stimulus-check.json)는
encoder가 기준 wire와 byte 단위로 일치하지만 C receiver가 두 frame을 SCHEMA_INVALID로 거부함을 보여준다.
Legacy personal-usage collector도 SCHEMA_INVALID이며 공통 payload와 다르다. Modern provider fixture의 valid/invalid 17건 일치는
공통 입력 실패나 legacy 29건 oracle 통과를 대신하지 않는다. Source 생성 시각을 새 fixture freshness로 해석하지 않는다.

[업로드](evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/operator-observation/hardware-slot.json)는
00:57:03.118 KST에 완료됐다. 독립 복원된 동일 binary를 COM3에 올리고 NVS 0x9000/0x6000만 초기화했다.
같은 reference UTC·seq 0/1·5초 간격을 유지했고 [raw 장치 로그 검토](evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/operator-observation/receiver-source-review.json)에서
두 frame의 SCHEMA_INVALID 거부와 수락 0건을 확인했다. `rejected seq=0`의 0은 유지된 state이며 수락 sequence가 아니다.
PC 쓰기/프로세스 exit 0을 장치 수락으로 표시하지 않는다. 현재 보드는 이 Sol 최초 artifact이며 이전 Flash 펌웨어가 아니다.

사용자가 제공한 `KakaoTalk_20261006_010228392.mp4`는 12.9초·6,424,763 bytes,
SHA-256 `af49e2ea86ad0cd0576dc1669095d698b061801a0f0faa67d21a370ac5f88fa4`다.
[영상 검토](evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/operator-observation/user-video-01/video-review.json)는
파란/어두운 패널과 가로 cyan/blue/red 띠, 읽을 수 있는 제목·숫자·정보 화면 부재를 확인했다.
[사용자 관측](evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/operator-observation/user-video-01/capture-identity-confirmation.json)은
BOOT를 짧게 3번과 길게 눌러도 반응이 없었다는 보고다. 영상 저장은 업로드 이후이며 정확한 촬영 UTC는 미확정이다.
짧은 영상으로 30초 연속 유지·정밀 지연·자발적 재부팅·선택 backlight 기능을 합격 처리하지 않는다.

| 최초 RM | 판정 | 근거 |
|---|---|---|
| RM1 | pass | 실제 IDF build·동일 artifact 업로드·장치 receiver 실행 |
| RM2 | fail | 공통 collector 오류와 host/실제 장치의 두 frame 거부 |
| RM3 | fail | 58%/82%를 포함한 글자·숫자 부재 |
| RM4 | fail | 사용량·글로벌 리셋·진단 정보 화면 부재 |
| RM5 | fail | 사용자 BOOT 3회·길게 누르기 무반응, 정보 탐색·복귀 부재 |

[최종 RM](evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/reference-review.json)은 한 번 적용했다.
Reference fail/product_pass false이며 completed·유효 제출·정책 eligible과 구분한다.
[최종 독립 감사](evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/restore-audit.json)는
453개 파일·57개 입력·raw source/artifact·원본 비용·정책/RM·영상·BOOT 보고를 package의 동결 validator로 검증했다.
최종 package manifest SHA-256은 `93a87074e0f324da7c95e237244870d0a8deebc6be4f3e89b52fb95095acb60e`다.
`result_valid: true`는 제출 형식/증거 연결이며 제품 합격이 아니다. 관측 전 395개 package와 시작 snapshot도 원본 그대로다.

2026-10-06 운영 정정은 이 Sol 최초 보존·다음 후속 준비에만 적용한다.
[Audit 기록](evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/operator-observation/pre-observation-preservation/operator-audit-notes.json)은
무해한 CONFIG_ESPTOOLPY를 command esptool로 잘못 매칭했던 helper assertion과 restored metadata 경로 remap 감사 오류를 보존한다.
[최종 감사 정정](evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/final-audit-correction.json)은
복원 종료 전 조기 감사의 FileNotFoundError를 보존하고 종료 후 새 extraction directory에서 같은 검증을 통과했음을 기록한다.
원본 terminal guard로 RM를 적용하기 위한 [metadata 연결](evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/operator-observation/reference-review-binding/binding-note.json)은
보존된 terminal bytes와 평가 전 operator metadata를 따로 유지하며 execution/measurement·ledger terminal hash·source를 바꾸지 않았다.

실험 manifest의 branch label `experiment/openai/codex-cli/gpt-6-sol`과 실제 local Git branch `master`는 구분한다.
후보는 root 운영 저장소와 별도 저장소에서 동결 commit으로 격리했으며 이름만으로 named branch를 확인했다고 추정하지 않는다.
동결 commit에는 생성 build/build-host 파일 1,413개가 추적돼 있다. 다음 준비 사본에서만 출력을 제외하고
입력·자기 source 동일성·현재 receipt를 확인한 뒤 후속을 시작한다. 원본 freeze/package는 수정하지 않는다.
후속은 아직 0회·잔여 7,200초·3회다. User keep going은 이 series 처리를 계속하며 Pro 종료·Flash 보류·Luna 미시작은 유지한다.

## 2026-10-06 Codex Sol 후속 1회차 시작

[후속 계획](../../docs/plans/2026-10-06-codex-sol-followup-execution.md)에 따라 `20261006-codex-cli-gpt-6-sol-r01`을
ledger round 1로 준비했다. 날짜 뒤 r01은 당일 예약 번호이며 자기 최초 `20261005-codex-cli-gpt-6-sol-r01`에 이어지는 후속이다.
피드백은 자기 직전 commit·RM2~RM5 관측·고정 기대·evidence 6개·남은 7,200초/3회만 제공한다.
다른 구현이나 운영자 제품 patch·해결 방법은 제공하지 않았다.

[새 사본 보완](evidence/20261006-codex-cli-gpt-6-sol-r01/launch-20261006/operator-generated-output-cleanup.json)은
추적된 build/build-host 출력 1,413개를 새 checkout에서만 제외했다.
남은 product source 18개는 직전 Git blob과 줄바꿈 정규화 내용이 동일하고 고정 입력 57개를 검증했다.
새 prepared commit `3a01a5012180cec2b32bba18fa4287a79a35de69`와 local Git exclude를 기록하며 이전 freeze/package·판정·비용·global 설정·profile·권한은 바꾸지 않는다.
이는 기존 Flash 캐시 승계의 운영 도구 문제를 다음 사본에서 방지하는 정정이며 과거 부적격 판정을 소급 복구하지 않는다.

[실제 시작](evidence/20261006-codex-cli-gpt-6-sol-r01/launch-20261006/native-start-observation.json)은
03:34:01.746 KST·launcher PID 7656·candidate PID 14396·thread `01a10d58-20e1-7eb2-93f7-97fb84a5eb89`다.
동일 CLI/SDK/native inventory·explicit gpt-6-sol/medium/process argv를 확인했다. Native resolved model/cwd 미방출 한계는 유지한다.
Receipt SHA-256 `16c93563e8187b59c6488c00a33209adbd38ebc8e26448e73067bb2cb6007132`와
[시작 snapshot](evidence/20261006-codex-cli-gpt-6-sol-r01/launch-20261006/snapshot-inventory.json)의 32개 raw 파일을 보존한다.
최대 7,200초 독립 runner로 구현 중이며 최종 실제 시간으로 후속 예산을 차감한다.
추가 회차는 2회 남지만 현재 회차 종료·평가 전에는 시작하지 않는다. 현재 보드는 최초 artifact이며 후보 실행 중 serial/flash·구현 피드백은 없다.

## 2026-10-06 Sol 후속 1회차 최종 평가와 최초 정책 정정

후속 1회차는 03:41:31.431 KST에 completed/exit0으로 종료됐다. 원본 비용 449.687초, 78도구 호출(62명령·16파일변경), 실패 명령4개를 보존한다.
Input 3,847,656·output14,468·정규화 합계3,862,124 token이며 cached3,694,208은 input에 포함된다.
Raw JSONL의 reasoning_output_tokens2,880은 별도 보존하고 동결 adapter의 reasoning/provider_total null을 변경하지 않는다.
동결 commit `3a09f26f2f375f4f45bebb79eb5902667a3ccb1a`, app SHA-256 `78bb997794c7a30534f90d9eadb1cafd061de2338c06832f88ebb63d8e4098eb`다.

독립 복원에서 기존 Python6개·C receiver/state/CRC·idle backlight·Python→production C 시험이 통과했다.
Encoder는 고정 frame과 동일하며 host 및 03:50 KST 업로드한 실제 장치 모두 frame0·1을 수락했다.
수집 payload의 글로벌 리셋 오류 코드 두 곳만 SOURCE_STALE/reference null로 다르고 나머지 값은 동일하다.
실물 송신은 operator_replay이므로 전체 후보 collector→device 경로 통과로 확대하지 않는다. Modern17개는 validity 확인이며 full29개 oracle이나 정식 GUI 채점과 다르다.

사용자의 [원본 사진·보고](evidence/20261006-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/operator-observation/user-photo-01/capture-identity-confirmation.json)를 이번 artifact에 연결했다.
어두운 화면에 가로 색 띠만 있고 읽을 수 있는 제목·숫자·문구가 없다. 버튼으로 정보가 바뀌지 않는다.
사용자가 RESET을 눌러 같은 화면으로 재부팅했으며 자동 재부팅·30초 연속 유지·정밀 지연은 입증되지 않았다.
[최종 RM](evidence/20261006-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/reference-review.json)은 RM1 pass/RM2 partial/RM3~RM5 fail·reference fail/product_pass false다.
[459개 파일 독립 감사](evidence/20261006-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/restore-audit.json)와
[87개 파일 공개 목록](evidence/20261006-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/snapshot-inventory.json)을 보존한다. Package SHA-256은 `3deaa018dfebcec8d81b8be8f1a94439fd2c68e9bdec4ab0393a94204f408540`다.

정책은 기존 과제의 shell pipeline 금지 위반4건으로 invalid_for_comparison이다. Final Git 권한 거부 뒤 추가 도구 조작은 없어 종료 규칙을 지켰지만 별도의 파이프 위반이 남는다.
최초에도 명백한 파이프7건이 있으며 운영자 최초 검토에서 누락했다. [2026-10-06 정정](evidence/20261005-codex-cli-gpt-6-sol-r01/policy-correction-20261006/correction-note.json)과
[15개 파일 목록](evidence/20261005-codex-cli-gpt-6-sol-r01/policy-correction-20261006/snapshot-inventory.json)으로 현재 최초 및 Sol series의 품질·reference-cost 적격성을 invalid로 정정했다.
최초 eligible review·453개 파일 package·commit·RM·원본 비용은 그대로다. AST는 조회 명령의 실제 pipeline만 판별하고 따옴표 안 regex의 `|`와 해석이 불명확한 최초 line175는 확정 건수에서 제외했다. 캡처한 명령을 실행하지 않았다.

[Checkpoint09](comparison-checkpoint-09.md)는 후보10회와 정규화 총20,179,804 token을 기록하며 checkpoint08의 원본과 비용 정의를 보존한다.
Sol 최초+후속 누적2,909.843초·15,903,260 token은 비용 기록이며 품질 순위를 뜻하지 않는다.
후속 잔여6,750.313초·2회로 [남은 후속 계획](../../docs/plans/2026-10-06-codex-sol-remaining-followups.md)을 따른다. 다음 새 사본에서는 추적된 생성 bytecode도 제외하고 실제 source·입력·profile 동일성을 검증한다.

## 2026-10-06 Sol 후속 2회차 시작

Run `20261006-codex-cli-gpt-6-sol-r02`/ledger round2는 자신의 직전 commit `3a09f26f2f375f4f45bebb79eb5902667a3ccb1a`와 관측만 이어간다.
새 prepared commit `e2a741d6360304c8d5e1542bc4444fc9a0fac2da`에서 생성 bytecode3개만 제외하고 제품 source18개의 Git blob·내용과 고정 입력57개를 검증했다.
Local Git exclude에 생성 build/build-host/bytecode만 추가했으며 기존 source·비용·evidence·baseline·global 설정·권한은 바꾸지 않았다.
[실제 시작](evidence/20261006-codex-cli-gpt-6-sol-r02/launch-20261006/native-start-observation.json)은 04:08:53.442 KST, thread `01a10d78-0ba5-7ff3-8dd5-260f62b6ea53`, candidate PID31768, launcher PID21872다.
같은 CLI/SDK/native inventory와 actual argv의 explicit gpt-6-sol/medium을 확인했다. Receipt SHA-256 `c48f1673534bd1eb274892e5fb3dbc7cfeb452b5a9f952ebc08759d8717d0707`과
[35개 파일 시작 목록](evidence/20261006-codex-cli-gpt-6-sol-r02/launch-20261006/snapshot-inventory.json)을 보존한다. Resolved model/cwd를 native JSONL이 방출하지 않는 한계는 그대로다.
이번 최대6,750초/누적 후속7,200초/최대3회를 유지한다. 현재 호출 이후 추가 회차는 최대1회이며 시간은 종료 시 차감한다. 현재 보드는 후속1이다. 후보 실행 중 구현 피드백·serial/flash를 제공하지 않는다.

## 2026-10-06 Sol 후속 2회차 종료·독립 검증·실물 관측 대기

04:19:16.016 KST completed/exit0으로 구현·제출이 종료됐다. 원본622.562초·75도구 호출(64명령·11파일변경)·실패 명령4개를 기록한다.
Input6,489,180·output20,973·정규화합계6,510,153 token, cached6,330,752은 input에 포함된다. Raw reasoning_output_tokens7,547과 adapter reasoning/provider_total null을 각각 보존한다.
동결 commit `09ecdaf1645511033b4efda40bb2a9e3b96ae8f7`, 마지막 성공 build raw line150 이후 firmware source 변경은 없다.
공통 과제의 파이프 금지 위반9건으로 정책 invalid_for_comparison이다. 권한 거부는 없으며 자체 인계 문서도 파이프 위반을 인정한다. 원본 실행·비용·제품 관측은 유지한다.

[관측 전 package의 독립 감사](evidence/20261006-codex-cli-gpt-6-sol-r02/post-terminal-awaiting-optical-20261006/restore-audit.json)는418개 파일·source22/artifact21·입력57과 raw cost를 검증했다.
Package SHA-256 `4c7d8e5093983f7b180ed02c911eac2d6682d5b8ccf558f5515543a71ef5ff43`다. 자체 format validator의 result_valid true는 제품 합격이 아니다.
독립 Python6개·생산 C state/CRC·idle backlight·collector→production C 시험이 통과했고 collector payload도 고정 common payload와 이제 동일하다.
Modern17개 validity 확인은 full29개 oracle이나 정식 GUI 점수가 아니다. 원본 실패 CTest2건과 직접 Python import 실패, rg 부재도 유지한다.

[실물 기록](evidence/20261006-codex-cli-gpt-6-sol-r02/post-terminal-awaiting-optical-20261006/operator-observation/hardware-slot.json)은04:21:15.401963 KST 같은 artifact를 COM3에 업로드하고 frame0·1 수락을 확인한다.
App SHA-256 `486cd84ba91af26fd86ea8642c166c4708b7e3537806cf18f93d9579c23c0377`, NVS0x9000/0x6000만 초기화, 전체 flash erase·운영자 rebuild는 없었다. Serial은 닫았다.
현재 LCD·BOOT·30초 유지 관측을 요청했고 [광학 대기](evidence/20261006-codex-cli-gpt-6-sol-r02/post-terminal-awaiting-optical-20261006/operator-observation/optical-observation-pending.json)로 기록한다.
후속1 사진·수동 RESET 보고는 새 firmware 증거가 아니다. 정식 RM review·최종 package/평가와 Sol series 종료는 아직 미완료다.

[76개 파일 snapshot](evidence/20261006-codex-cli-gpt-6-sol-r02/post-terminal-awaiting-optical-20261006/snapshot-inventory.json)과 [checkpoint10](comparison-checkpoint-10.md)을 보존했다.
후보11회 정규화합계26,689,957 token, Sol 최초+후속2회 누적3,532.405초·22,413,413 token, 남은 후속6,127.751초·1회다.
비용과 정책 부적격을 유지하고 이번 관측·RM 완료 전 후속3이나 Luna를 시작하지 않는다. 과거 snapshot·원본 판정·동결 ref는 변경하지 않았다.

## 2026-10-06 Sol 후속 2회차 최종 평가·series 종료

위 광학 대기는 당시 상태다. 사용자가 제공한 `KakaoTalk_20261006_042359926.mp4`의63.3초·30,937,062 bytes와 SHA-256
`556c295353c13fa061c7da118ee007891c4b82a42f9aff66eb410557aca779ac`를04:21 업로드 원본 artifact에 연결했다.
[영상 검토](evidence/20261006-codex-cli-gpt-6-sol-r02/evaluation-final-20261006/operator-observation/user-video-01/video-review.json)는 전체63개 표본·6개 contact sheet와 선택 원본을 검토한 근거다.
수동 RESET 전에는 USED42/LEFT58·USED18/LEFT82, 글로벌 리셋 timestamp·elapsed·출처와 진단 정보를 읽을 수 있다.
BOOT 조작으로 GLOBAL RESET→STATUS→USAGE→GLOBAL RESET의 세 화면 순환·복귀를 확인했고 RESET 뒤 빈 상태에서도 탐색이 이어진다.
약18초의 WAITING 전환은 사용자가 직접 RST를 눌렀다고 확인했다. 자동 재부팅이나 BOOT 탐색 실패로 집계하지 않는다.
20.5~30.5초 표본은 켜진 화면에 읽을 수 있는 글자가 없으며 원인은 미확정이다. 영상 길이를30초 연속 정상 표시의 증명으로 사용하지 않는다.

[최종 RM](evidence/20261006-codex-cli-gpt-6-sol-r02/evaluation-final-20261006/reference-review.json)은 한 번 적용했으며 RM1~RM5 pass·reference pass다.
정책 파이프9건과 최초/후속1의 위반으로 series 품질 invalid_for_comparison·적격 reference-cost 제외를 유지한다.
전체29개 oracle·정식 GUI/선택 기능·정밀 지연·30초 연속 정상 데이터 표시는 미검증으로 남겨 product_pass false다.
[483개 파일 독립 감사](evidence/20261006-codex-cli-gpt-6-sol-r02/evaluation-final-20261006/restore-audit.json)는57개 입력·source22/artifact21·동결 commit·원본 비용·영상·정책/RM를 검증했다.
Package manifest SHA-256은 `a72afc82d487005b05a403940419a5f0bdabcf0e1e79b4953d7eb56784b29a82`이며 [공개 목록](evidence/20261006-codex-cli-gpt-6-sol-r02/evaluation-final-20261006/snapshot-inventory.json)은109개 파일의 원본 bytes/hash를 보존한다.
기존418개 관측 전 package·76개 pending snapshot·최초/후속1 판정·동결 ref는 변경하지 않았다. 후보 재호출·재빌드·추가 업로드는 없다.

[Series 종료](evidence/20261006-codex-cli-gpt-6-sol-r02/evaluation-final-20261006/operator-series-completion.json)는 ledger reached다.
최초1회·후속2회 누적3,532.405초·22,413,413 token이며 후속 누적1,072.249초다. 미사용6,127.751초·1회로 추가 호출을 만들지 않는다.
[Checkpoint11](comparison-checkpoint-11.md)은 실제11회 정규화26,689,957 token과 모든 실패·부적격 비용을 유지한다. Cached는input에 포함되며 원본reasoning과 adapter null의 정의를 변경하지 않는다.
마지막 관측 보드는 수동 RESET 뒤 WAITING 상태이며 이후 데이터 재전송은 없다. Serial은 닫았고 영상 이후 현재 화면을 새로 관측하지 않았다.
전체 비교는 종료3/15 series로 미완료다. Pro 종료·Flash 보류·Luna 미시작을 유지한다.

## 2026-10-06 Codex Luna 최초 실험 시작

사용자의 “luna 시작하자”에 따라 block1/seed1의 마지막 대상 Luna를 시작했다. [계획](../../docs/plans/2026-10-06-codex-luna-initial-launch.md)과
[25개 파일 시작 목록](evidence/20261006-codex-cli-gpt-6-luna-r01/launch-20261006/snapshot-inventory.json)에 준비·실제 시작 원본을 보존했다.
10월5일의 미실행 예약은 유지하고 `20261006-codex-cli-gpt-6-luna-r01`·새 ledger·단일 최초 commit의 독립 저장소를 생성했다.
준비 commit `d9579af28c8952b963454e9e2d32b8322d7ed472`, manifest branch label `experiment/openai/codex-cli/gpt-6-luna`와 local master를 구분한다. 제품 구현·build 출력·다른 후보 Git 이력이 없는57개 입력을 확인했다.
[현재 확인](evidence/20261006-codex-cli-gpt-6-luna-r01/launch-20261006/operator-launch-preflight/current-checks.json)은 CLI0.159.2·ESP-IDF5.3.2·기존 native 설정·hook 비활성화와 모델 호출0회를 기록한다.
Capability 원본은10월4일이며 model entitlement를 새 probe로 재검증했다고 표시하지 않는다. 같은 frozen profile의 fresh receipt SHA-256은 `44ba7ad2e5ad8c6f01784531cfbea792b783f58e1df4201cb2c350d9eff7204b`다.
[실제 시작](evidence/20261006-codex-cli-gpt-6-luna-r01/launch-20261006/native-start-observation.json)은10:10:26.658 KST·thread `01a10ec3-0ebc-75f1-8060-d2ee9aff0262`·candidate PID7052·launcher PID8376다.
Process argv의 explicit gpt-6-luna/max·권한·확장 비활성화가 profile과 일치한다. JSONL에 없는 실효 model/cwd를 검증했다고 추정하지 않는다.
별도 runner의 최초 최대7,200초를 적용하며 대화의 토큰 만료로 같은 후보를 재실행하지 않는다. 종료 후 source·비용·제출·정책·host·제품/RM를 평가하고 genuine 원본 artifact가 있으면 업로드·실물 관측한다.
현재 제품·정책·RM·최종 비용은 pending이다. [Checkpoint11](comparison-checkpoint-11.md)은 이전 종료11회만 집계한다. 후보 실행 중 운영자 구현 수정·피드백·serial/flash는 없으며 이전 Sol 화면은 Luna 근거가 아니다.
Sol·Pro 종료와 Flash 보류 예산·과거 판정·원본 비용은 유지한다. 다음 독립 series나 모델을 동시에 시작하지 않는다.

## 2026-10-06 Luna 최초 종료 확인

상태 요청에 따라 manifest·ledger·실제 process·raw final response·제출 파일을 확인했다.11:02:01.091 KST completed/exit0이며 실행 중인 Luna process는 없다.
[종료 snapshot](evidence/20261006-codex-cli-gpt-6-luna-r01/terminal-status-20261006/snapshot-inventory.json)의12개 파일은 원본 manifest/ledger·stdout/stderr·command audit·제출 문서와 비용을 보존한다.
같은 최초를 다시 호출하거나 원본 manifest·ledger를 덮어쓰지 않았다. 최종 runner 시작 시각01:10:26.660Z와 기존 launch 기록01:10:26.658Z의2ms 차이도 원본 그대로 구분한다.
실제 실행3,094.422초·157도구 호출·실패 명령11개, input17,277,453/output136,034/정규화17,413,487 token이다. Cached16,845,056은input에 포함되며 raw reasoning67,420과 동결 adapter reasoning/provider_total null을 유지한다.
결과JSON·선택 문서·검증 기록이 있으며 결과가 참조하는 `.benchmark-inputs/e2e-evaluation-manifest.json`도 존재한다. Manifest 기본 outputs 경로의 별도 evaluation file 누락을 실제 참조 파일의 누락으로 해석하지 않는다.
App `build-idf/codex_desk_meter.bin`은316,272 bytes, SHA-256 `3af7fd933b743ea7b16ba02627617e3adb3be0d5273eb9deb184f1be9c9d51d6`로 후보 제출 해시와 일치한다.
후보는 Python11개/CTest3개·validator 통과를 보고했으며 실물 시험 not_run·product_pass false를 제출했다. 읽기 명령결합 제한의 예외1건도 자체 보고했으므로 정식 정책 검토가 필요하다. 자체 시험 보고와 독립 평가를 구분한다.
현재 source/artifact 동결·독립 host·정책·제품/RM는 미완료다. Luna 펌웨어 업로드와 serial 전송은 없으며 보드의 Sol 화면은 Luna 근거가 아니다.
후속0회·잔여7,200초/3회를 유지하되 최초 평가 전 추가 호출은 하지 않는다. 현재 실행 종료12회와 checkpoint11의 종료11회 집계 범위를 구분한다. Sol/Pro 종료·Flash 보류·과거 원본은 보존한다.

## 2026-10-06 Luna 최초 원본 검증·COM3 재업로드·검은 화면 평가

사용자의 업로드 지시에 따라 [평가 계획](../../docs/plans/2026-10-06-codex-luna-initial-evaluation.md)을 수행했다.
동결 commit `c0d5d61160664923e0494302fae180089d02d247`의 source33개/artifact19개·original terminal manifest/ledger·raw333 events·비용을 보존했다.
마지막 성공 IDF build는raw line292이며 이후 firmware source 변경이 없다. 원본 app316,272 bytes·SHA-256 `3af7fd933b743ea7b16ba02627617e3adb3be0d5273eb9deb184f1be9c9d51d6`를 그대로 사용했다.
전체134개 명령·23개 파일변경을 검토하고 [정책 판정](evidence/20261006-codex-cli-gpt-6-luna-r01/evaluation-20261006/policy-review.json)을 연결했다.
파이프8호출(raw16/202/239/241/284/311/313/321)과 세미콜론 결합1호출(raw266·조회3문장)이 변경 없는 common task를 위반해 invalid_for_comparison이다. 따옴표 안 regex alternation·native 실행 wrapper를 위반 건수로 세지 않았으며 캡처한 명령은 실행하지 않았다.
실패11명령에는 rg 부재·process267·offline registry 의존성·컴파일·직접 Python import 문제가 있다. Original failures, raw reasoning67,420과 adapter null·cached input 포함 정의를 그대로 보존했다.

기존 운영자 artifact-path 수집 보완을 재사용해 후보가 선언한 `build-idf/`의 app/ELF/map/bootloader/partition을 같은 디렉터리에서 보관했다. 동결 operator checkout·validators·후보 입력·source·profile·권한을 바꾸지 않았다.
404개 관측 전 package를 독립 복원하고 package ZIP의 동결 validator로 재검증했다. Restored Python11개·archived 생산 C parser/state/idle-dim 실행 파일3개가 통과했으며 CTest의 원본 경로나 후보 checkout을 사용하지 않았다.
공통 frame0/1의 candidate encoder bytes는 정확히 일치한다. [수집기 한계](evidence/20261006-codex-cli-gpt-6-luna-r01/evaluation-20261006/operator-observation/host-semantic-limitations.json)에 common legacy payload8개 필드 차이와 modern validity16/17을 남겼다.
`available-over-stale-threshold.json`을 collector가 stale로 보정해 허용하는 기존 동작과 frozen invalid 기대의 차이를 보존했다. Full29 oracle·임의 common-frame 생산 C 입력 seam·실물 idle-dim·PC GUI의 통과를 주장하지 않는다.

11:27:50.352863 KST COM3 최초 기록 쓰기가 성공했다. 사용자가 “esp32 com3에 연결하지않았었음”이라고 재업로드를 요청해, 그 로그를 보존하면서 당시 관측 대상과의 물리적 연결을 미확인으로 기록했다.
[재업로드 원본](evidence/20261006-codex-cli-gpt-6-luna-r01/evaluation-20261006/operator-observation/hardware-attempt-02/frozen-artifact-upload-stdout.txt)은21:03:05.479794 KST COM3·ESP32-S3 rev0.2·USB Serial/JTAG·MAC `28:84:85:B0:85:18`과 세 이미지의 `Hash of data verified.`를 기록한다.
두 번 모두 같은 동결 펌웨어이며 NVS0x9000/0x6000만 공통 초기화했다. 전체 flash erase·후보 재호출·운영자 source 수정·rebuild는 없다.
[현재 capture](evidence/20261006-codex-cli-gpt-6-luna-r01/evaluation-20261006/operator-observation/hardware-attempt-02/reference-capture-r1/capture.json)는 공통 seq0/1을 각1,543 bytes 쓰고 serial을 닫았다. Capture0 bytes·수락/거부 marker 부재로 실제 수신 여부는 미확인이다. UART0 primary·USB Serial/JTAG secondary 설정은 함께 남겼고 무응답 원인은 확정하지 않는다.

사용자는 재업로드 관측 질문에 [“lcd에서는 검은 화면만 나옴”](evidence/20261006-codex-cli-gpt-6-luna-r01/evaluation-20261006/operator-observation/hardware-attempt-02/user-black-screen-report.json)이라고 답했다. COM3 업로드 성공은 로그로 확인하지만 application 정상 기동이나 LCD 정상 출력은 이 기록에서 확인되지 않는다.
[제한된 최초 RM](evidence/20261006-codex-cli-gpt-6-luna-r01/evaluation-20261006/reference-review.json)은 원본 terminal digest를 사용하는 frozen guard로 한 번 적용했다. RM1/2 partial·RM3 fail·RM4/5 not_run, reference fail·product_pass false다.
BOOT 조작·RESET·30초 연속 유지·자동 재부팅·검은 화면의 원인·영상/사진 관측을 만들어내지 않는다. Ledger active·후속0회·잔여7,200초/3회로 유지하며 후속이나 다른 모델을 시작하지 않았다.

[최종 독립 감사](evidence/20261006-codex-cli-gpt-6-luna-r01/evaluation-20261006/restore-audit.json)는464개 inventory 파일·source33/artifact19·입력57·원본 비용·정책/RM·현재 업로드·사용자 보고 결합을 확인했다. Package SHA-256은 `57ad97f136d462b95093bd562d8a9af176e91bfee20e6ae826c36d68cebd0764`다.
[125개 파일 공개 목록](evidence/20261006-codex-cli-gpt-6-luna-r01/evaluation-20261006/snapshot-inventory.json)은 원본 bytes/hash를 보존한다. 이전404/435/454개 package·launch/terminal snapshot·과거 판정·동결 ref는 그대로다.
[Checkpoint12](comparison-checkpoint-12.md)는 실제12회·정규화44,103,444 token을 기록하며 모든 실패/부적격 비용과 checkpoint11까지의 원본을 유지한다. 전체 series 종료3/15·Sol/Pro 종료·Flash 보류는 유지한다.

## 2026-10-06 Luna 검은 화면 추가 원인 분석 완료

사용자의 “원인 분석 시작”에 따라 [진단 계획](../../docs/plans/2026-10-06-codex-luna-black-screen-diagnosis.md)을 수행하고 [분석 보고서](luna-black-screen-diagnosis-20261006.md)에 결과를 기록했다.
같은 COM3·MAC과 원본 app/ELF 결합을 확인했다. Native reset부터5,859 bytes를 받아 정상 flash boot·PSRAM 검사·LCD 초기화 함수 완료·USB 수신 준비를 확인했으며, 첫 진단 전송에서는 생산 수신기의 frame0 수락 로그도 확보했다. 사용자는 첫 리셋 후 계속 검은 화면이라고 확인했다.
제조사 드라이버/원본 ELF에서 초기 명령 전송·IO 삭제 이후 LCD를 다시 물리 리셋하고 명령을 재전송하지 않는 결함을 확인했다. ST7701S MADCTL의 지원 근거 없는 D5 축 교환 가정과 물리 RGB timing320×820→820×320 변경도 확인했다. 첫 결함은 유력 원인이며 각각의 수정 후 인과 검증은 미실행이다.
첫 capture의 frame1은 Write timeout, 두 번째 리셋 후 capture는 두 host write 완료·수락 로그 부재다. Frame1·전송 불안정 원인·BOOT·30초 실물 유지의 미확인을 보존한다. 원래 공통 평가의0-byte capture나 기존 최초 RM를 덮어쓰지 않았다.
[별도 진단 snapshot](evidence/20261006-codex-cli-gpt-6-luna-r01/diagnosis-20261006/snapshot-inventory.json)에 source/hash·ELF disassembly·로그·stimulus·진단 reset2회·사용자 보고를 보존한다. Source 수정·rebuild·flash write·후보 호출0회이며 마지막 serial은 닫았다. 같은 Luna 최초 펌웨어가 남아 있고 마지막 전송의 실제 수락은 미확인이다.
기존 최초 reference fail·product_pass false·policy invalid·원본 package와12회/44,103,444 token·series3/15·Luna 후속0회/잔여7,200초·3회는 그대로다. 정식 후보 후속에는 운영자 patch/수정 방법을 중립 관측처럼 전달하지 않는다. 다음 작업은 별도로 식별한 수정과 실물 검증이며 이번 분석에서 시작하지 않았다.

## 2026-10-06 Luna 후속 1회차 시작

2026-10-06 문서 정정: 이 시작 단락의 한글 인코딩 깨짐을 수정했다. 당시 시작 시각·source·호출 수·예산은 바꾸지 않았다. 이전 문구는 Git 이력에 보존한다.

사용자의 “codex luna 후속 조치 진행 ㄱㄱ”에 따라21:52:33.768 KST에 시작했다. 자기 동결 commit `c0d5d61160664923e0494302fae180089d02d247`을 별도 clone에서 이어받았고 로컬 branch는 detached다. run ID의r02와 ledger round1을 구분한다. 제품 source29개와 고정 입력57개·profile·원본 runner/operator baseline을 확인했으며 이전 build/build-idf/build-host/sdkconfig를 상속하지 않았다. 자신의 관측·고정 요구사항만 제공했고 운영자 진단의 수정 방법·새 datasheet·다른 후보 source는 전달하지 않았다.

[시작 증거](evidence/20261006-codex-cli-gpt-6-luna-r02/launch-20261006/snapshot-inventory.json)는43개 파일로 native PID14732·thread·gpt-6-luna/max argv·CLI0.159.2·ESP-IDF5.3.2·fresh ephemeral 권한을 보존한다. 첫 launcher 경로 누락 오류는 모델 호출 전에 발생했다. 오류를 보존하고 올바른 경로로 재시작했으며 실제 후보 호출은1회다. 시작 당시 잔여 시간7,200초·후속1회 사용/추가 최대2회, 보드는 이전 Luna 최초 artifact였고 실행 중 serial/flash·구현 피드백은 없었다.

## 2026-10-06 Luna 후속 1회차 평가 완료

[계획](../../docs/plans/2026-10-06-codex-luna-followup-execution.md)의 구현·제출·동결·독립 복원·가능한 실물 관측을 완료했다. 실제 terminal21:52:33.769~22:42:20.773 KST, 2,987초·exit0이다. 시작 snapshot과 terminal의1ms 차이를 원본대로 보존했다. Raw545 events·명령229개·파일변경35개, 계측 tool264/실패명령13을 기록한다. 원시 input13,274,009·output140,022·정규화13,414,031 token이며 cached12,811,008은 input에 포함된다. Raw reasoning94,200과 frozen adapter null은 별개로 유지한다. 실행 중 운영자 개입은 감사상0회이며 원래 계측 null을 바꾸지 않았다.

동결 commit `e68356829715793dc31dd188bc2a9f528f6fcbd2`, source38개/artifact20개, 마지막 성공 build raw533행 뒤 firmware source 변경은 없다. [정책 검토](evidence/20261006-codex-cli-gpt-6-luna-r02/evaluation-20261006/policy-review.json)는 실제 파이프2호출(raw39/288)로 invalid_for_comparison이다. 따옴표 안 regex alternation·native wrapper·실행되지 않은 parse error를 실제 결합 호출로 세지 않았다. 원본 비용·제품 관측을 보존하고 적격 품질/reference-cost에서 제외한다.

[Host 검증](evidence/20261006-codex-cli-gpt-6-luna-r02/evaluation-20261006/operator-observation/host-semantic-review.json)은 독립 복원의 Python22개·원본 C 실행 파일3개를 확인한다. 후보의21개 보고는 원본대로 보존한다. Common collector payload/encoder frame0/1이 정확히 일치하고 production C CLI가 두 frame을 수락한다. Provider validity17/17도 기대와 같다. 자체29개 wire/schema 시험은 고정 operator29 pipeline 시험과 구분하며 후자·정식 GUI·실물 idle-dim은 미실행이다. 최초 audit의21개 예상 guard 오류·통과 로그는 보존하고 추가 suite 실행 없이 실제22개를 검증했다.

[COM3 업로드](evidence/20261006-codex-cli-gpt-6-luna-r02/evaluation-20261006/operator-observation/hardware-slot.json)는22:51:05.542647 KST에 MAC `28:84:85:B0:85:18` 보드의 세 이미지 해시를 확인했다. App SHA-256 `8861e741f3acdb3c511b399f2e92b96f70904f7000faf01b43266016ecea9fd5`이며 원본 `build/` artifact를 사용했다. NVS0x9000/0x6000만 초기화했고 운영자 source 변경·rebuild·전체 flash erase는 없다. 첫 capture0 bytes를 보존했다.

[추가 reset capture](evidence/20261006-codex-cli-gpt-6-luna-r02/evaluation-20261006/operator-observation/hardware-post-upload-reset/runtime-source-binding.json)는22:54:32.187074 KST의 native reset1회 후5,938 bytes를 받았다. 원본 ELF SHA prefix81c1bd1d2·정상 boot·PSRAM 검사·USB ready를 확인했다. PSRAM marker를 false로 잘못 기록한 것은 [날짜 있는 정정](evidence/20261006-codex-cli-gpt-6-luna-r02/evaluation-20261006/operator-observation/hardware-post-upload-reset/runtime-observation-correction.json)으로 원본 로그와 연결했다. 두 공통 frame의 host 쓰기는 각각1,543 bytes/5초 간격 완료됐지만 accepted/rejected 로그가 없어 장치 수락은 미확인이다. Serial은 닫았다.

사용자의 [“검은 화면이 계속됨”](evidence/20261006-codex-cli-gpt-6-luna-r02/evaluation-20261006/operator-observation/user-black-screen-report.json)을 현재 followup1 upload/reset에 연결했다. [한 번 적용한 후속 RM](evidence/20261006-codex-cli-gpt-6-luna-r02/evaluation-20261006/reference-review.json)은 RM1 pass·RM2 partial·RM3 fail·RM4/5 not_run, reference fail·product_pass false다. BOOT 조작·30초 유지·수동 RESET·자동 재부팅·검은 화면 원인은 보고되지 않아 추정하지 않는다. 최초 진단 결함을 후속 source의 원인으로 자동 이월하지 않는다.

[최종 독립 감사](evidence/20261006-codex-cli-gpt-6-luna-r02/evaluation-20261006/restore-audit.json)는535개 inventory 파일·입력57개·원본 source/artifact/비용·정책/RM·현재 업로드와 사용자 보고를 package의 동결 validator로 확인했다. Package SHA-256 `28d3acfcf1c888850d1892710b5420ca52dea706f0542f0b462d19aeb3d68ede`이며 [공개 snapshot](evidence/20261006-codex-cli-gpt-6-luna-r02/evaluation-20261006/snapshot-inventory.json)은131개 파일을 원본 bytes/hash로 보존한다. 관측 전470개 package·시작43개 snapshot·최초464개 package·진단과 과거 판정/commit/tag는 유지한다.

[Checkpoint13](comparison-checkpoint-13.md)은13회·정규화57,517,475 token의 실패·부적격 비용을 포함한다. Luna series30,827,518 token·6,081.422초, 후속1회2,987초를 차감해4,213초(70분13초)/최대2회가 남았다. Ledger active는 기준 미도달에 대한 frozen manager 원래 상태다. 추가 호출은 준비·시작하지 않았으며 다음 자기 후속은 관측 피드백·source·fresh preflight의 정상 gate가 필요하다. Series 종료3/15·Sol/Pro 종료·Flash 보류와 checkpoint12까지를 보존한다.

## 2026-10-06 Luna 후속2회차 시작

사용자는 LCD 화면이 나올 때까지 잔여70분13초·최대2회 안에서 추가 실험을 요청했다. [남은 후속 계획](../../docs/plans/2026-10-06-codex-luna-remaining-followups.md)에 따라 자기 직전 commit `e68356829715793dc31dd188bc2a9f528f6fcbd2`에서 별도 checkout을 준비했다. 제품 source33개 Git blob·입력57개와 생성 build/sdkconfig 미상속을 확인했다. 관측 피드백은 정상 boot/USB ready·계속 검은 화면·장치 수락 미확인·host 개선·자기 파이프 위반으로 제한했고 운영자 진단의 수정 방법은 제공하지 않았다.

[실제 시작](evidence/20261006-codex-cli-gpt-6-luna-r03/launch-20261006/native-start-observation.json)은23:50:45.750 KST, native PID34648·thread `01a111b2-14c5-7ab3-97a7-54b3b4de34ff`다. Frozen gpt-6-luna/max argv·CLI0.159.2·ESP-IDF5.3.2·native 설정을 확인하고 새 run-bound receipt로 호출했다. [시작 snapshot](evidence/20261006-codex-cli-gpt-6-luna-r03/launch-20261006/snapshot-inventory.json)은36개 파일과 관측 피드백·원시 시작 로그를 보존한다. 시작 snapshot 생성기의 문자열 guard 오탐만 수정했으며 실행 중 후보 재호출·source 변경·구현 피드백은 없다.

Timeout4,213초는 이 호출을 포함한 누적 잔여다. 후속2회차 시작 뒤 마지막 최대1회가 남으며 실제 종료 시간을 차감한 뒤만 사용할 수 있다. 이번 회차를 먼저 동결·독립 검증·원본 업로드·평가한다. LCD 출력이 미도달이고 시간이 남으면 마지막 회차를 이어가는 것까지 사용자 지시에 포함된다. LCD 가시 출력과 전체 RM/product 합격을 구분하고 관측 없이 다음 실패를 추정하지 않는다.

후보 시작14회·종료13회, 비용 checkpoint13은 이전13회57,517,475 token만 포함한다. 현재 비용·정책·제출·제품/RM은 아직 미확정이다. 보드는22:51 KST 업로드한 후속1 원본이며 실행 중 serial/flash를 사용하지 않는다. 최초와 후속1의 모든 판정·535/464개 package·진단·과거 비용과 series 종료3/15·Sol/Pro 종료·Flash 보류를 보존한다.

## 2026-10-07 Luna 후속2 종료·원본 업로드

2026-10-07: Luna 후속2 `20261006-codex-cli-gpt-6-luna-r03`는00:11:33.017 KST native 사용량 한도로 environment_failed 종료했다. 제출 JSON·빌드가 남아 source commit `91f7de60328b7db9a9d04acef60ac45eafb3685a`를 동결하고455파일 독립 복원·Python22/C3·공통 host 경로를 확인했다. COM3에02:19 KST 원본 업로드,02:20 KST 같은 app 리셋·재전송을 완료했고 ELF 일치 boot·PSRAM·USB 첫64byte 수신을 확인했다. 완전한 frame0/1 수락·LCD/BOOT/30초는 미확인으로 사용자 실물 관측과 RM 평가를 기다린다. 실제1,247.265초 차감 후 잔여2,965.735초(49분25.735초)·최대1회, 다음 호출은 관측 후 LCD 출력 미도달일 때만 가능하다. 이번 정책은 eligible이나 series는 과거 invalid 판정 때문에 품질·reference-cost 부적격이다. 후보 시작/종료14회·token coverage13/14, 알려진 합계57,517,475 token·전체 합계 미상(null), Luna series coverage2/3·알려진30,827,518 token이다. Sol/Pro 종료·Flash 보류·과거 판정/비용을 보존한다.

[동결 원본과 관측](evidence/20261006-codex-cli-gpt-6-luna-r03/observation-awaiting-20261007/snapshot-inventory.json) · [원본 native 종료 사유](evidence/20261006-codex-cli-gpt-6-luna-r03/observation-awaiting-20261007/operator-observation/native-terminal-failure-review.json) · [비용14](comparison-checkpoint-14.md).

## 2026-10-07 Luna 후속2 영상 평가·마지막 후속 조건

2026-10-07 Luna 후속2 평가 완료: build·COM3 원본 실행은 RM1 pass, 공통 host 경로·USB 첫 수신과 완전한 수락 미확인을 구분해 RM2 partial이다. 38.55초 영상에서 글자 출력은 생겼지만 회전·중복·잘림으로58%/82%와 세 정보 화면을 읽을 수 없어 RM3/RM4 fail이다. 사용자는 BOOT와 RESET 모두 눌렀다고 확인했으며 정확한 조작 시점/횟수가 없어 분리된 BOOT 순환은 RM5 not_run이다. 화면 변화가 자동 재부팅이라는 추정은 하지 않는다. Reference fail·product_pass false, 이번 정책 eligible·과거 series invalid를 유지한다. 최종575파일 package 독립 검증 완료; native 사용량 한도 종료·token null·전체 coverage13/14·알려진57,517,475 token을 보존한다. 정상 가독 화면 미도달이므로 기존 승인 범위의 마지막 후속3을 준비할 수 있다. 잔여2,965.735초·최대1회이며 timeout 상한floor2,965초다. 아직 마지막 후보 호출은 없다.

[최종 RM](evidence/20261006-codex-cli-gpt-6-luna-r03/evaluation-20261007/reference-review.json) · [독립 복원](evidence/20261006-codex-cli-gpt-6-luna-r03/evaluation-20261007/restore-audit.json). 전체14회 후보 종료·독립 series 종료3/15로 비교는 미완료다.
