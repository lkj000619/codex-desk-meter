# 정식 동일 조건 비교 실행 기록

상태: 첫 블록 OpenCode Muse 최초 결과의 화면 실패·기준 미도달을 기록하고 후속 1회차 실행 중. 후속 시작 23:30:48 KST.
후보 실행 시작 2회(최초 1·후속 1)·종료 1회. 최초 정책은 `invalid_for_comparison`, RM은 미도달, `product_pass`는 false다. 나머지 모델은 미시작이다.
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

## 재개 시 확인 순서

manifest·ledger 상태와 launcher PID의 실행 여부를 먼저 확인한다. running 후보를 다시 실행하지 않는다.
terminal 상태이면 실제 비용·raw 로그를 검토하고 결과 동결·정책 review·실물/RM 관측으로 이어간다.
강제 중단이 있었다면 기존 reconcile 절차로 종료 비용을 연결한다.
다른 날의 미시작 최초 예약은 새 ID·ledger·receipt로 준비하며 기존 기록을 보존한다.
