# 다음 동일 조건 비교 준비 상태

확인일: 2026-10-06. 상태: **Codex Sol 후속 2회차의 구현·제출·관측·정식 RM·최종 보존 검증을 완료했다. RM1~RM5는 관측상 pass이며 ledger reached로 Sol series를 종료했다. 정책 invalid_for_comparison으로 품질·적격 reference-cost 집계에서는 제외하고 product_pass false를 유지한다. 최종483개 파일의 독립 복원으로 원본 source·artifact·비용·영상을 검증했다. 남은6,127.751초·1회는 미사용 예산이며 추가 호출은 허용되지 않는다. 후보 시작·종료 각11회, 독립 series 종료3개/15개다. Pro 종료·Flash 보류·Luna 미시작을 유지한다.**
실제 실행 원본과 재개 상태는 [정식 실행 기록](../../results/formal-comparison-20261004/report.md)을 따른다. 준비 단계의 0회 기록은 당시 원본으로 보존한다.

이 문서는 다음 비교의 현재 상태를 관리한다. 과거 판정·evidence·동결 commit/tag는 보존한다.
아래 시작·대기·남은 작업 표현은 각 관측 시점의 기록이며 최신 상태는 위 상태와 마지막 갱신을 따른다.
2026-10-02의 6개 모델 준비 완료 판정은 [당시 보고서](../../results/experiment-preparation-20261002/report.md)의 조건에만 적용된다.
2026-10-03의 보류 권고와 E1~E5 원본은 [실행 경계 검토](../../results/experiment-execution-review-20261003/report.md)에 남긴다.
이번 보완의 실제 근거는 [선행 작업 결과](../../results/experiment-launch-preparation-20261004/report.md)와
[작업 계획](../plans/2026-10-03-formal-comparison-launch-prerequisites.md)을 따른다.

## 현재 비교 대상과 공통 조건

사용자 결정에 따라 Claude는 이번 비교에서 제외한다. Claude Code 구독이 없고 AGY의 기존
Opus 4.6 호출도 거부됐다. 실패 원본과 비용은 보존하며 Opus 5.5로 대체하지 않는다.
활성 목록의 원본은 [comparison-targets.json](../../experiments/config/next-profiles-20261003/comparison-targets.json)이다.

| 표면 | 모델·effort | 실제 준비 검증 |
|---|---|---|
| Codex | `gpt-6-sol` medium | 9개 capability 통과 |
| Codex | `gpt-6-luna` max | 9개 capability 통과 |
| OpenCode | `opencode/muse-spark-1.3-contributor-free` | 9개 capability 통과, 최종 권한 수정 후 재확인 |
| AGY | `gemini-3.8-flash-medium` | 9개 capability 통과 |
| AGY | `gemini-3.1-pro-high` | 9개 capability 통과 |

- 목표: synthetic fixture 기반 Version 2 E2E. 실제 계정 수집은 별도 owner-only 통합이다.
- 기준 도달: [reference-match RM1~RM5](reference-match-matrix.md). 전체 `product_pass`는 별도다.
- 예산: 최초 7,200초, 후속 최대 3회 AND 후속 누적 7,200초. 자기 직전 결과에서만 이어간다.
- 독립 반복: 5개 조합×3개 블록=15개 최초 series. 후속 최대 45회, 후보 시간 상한 60시간.
- 접근: `prompt-and-log`, `read_isolation: not_enforced`, `builtin-only-v1`. 후보에게 serial/flash와 다른 후보 구현 접근을 허용하지 않는다.
- 보드 사실·고정 제조사 source를 동일 제공한다. BSP 작성도 후보 비용에 포함한다.

[운영 계약](comparison-operating-contract.md), [격리 정책](isolation-policy.md),
[프로필 목록](../../experiments/config/next-profiles-20261003/README.md)이 상세 조건의 원본이다.
전체 제품 합격을 후보 시작의 전제조건으로 삼지 않는다.

## 보류 사유의 보완 상태

| 항목 | 반영한 동작 | 검증 |
|---|---|---|
| E1 정책 준수와 비교 적격성 | 신규 benchmark의 필수 `policy-review.json`; eligible만 품질·순위·RM 도달에 인정 | run/profile/input/raw 로그·검토 근거 결합, 변조·누락 제외, 전체 실패 비용 보존 |
| E2 fresh 후속 과제 연결 | 최초 공통 task 전문·새 ID·잔여 예산 재전달, 자기 증거 상대 경로·hash 고정 | task·증거 변조 차단, 독립 복원, Windows 줄바꿈 변환 시 원본 bytes 보존 |
| E3 native 권한 | 정상 상대 py_compile 허용, 탭 명령 차단, ref 이력 조회 제거, SDK/vendor edit 거부 | 선언 회귀·native 실효 config·실제 정상 도구 실행 |
| E4 실행 문법 | `benchmark.py run <directory> --receipt ...`; AGY 옵션을 action 앞에 배치 | 실제 parser와 대조 |
| E5 AGY 전역 설정 | root 단위 OS lock·owner journal, child 종료 확인 후 원본 복원 | 경합·중단·실패 복구 회귀, 실제 probe 전후 bytes 동일 |
| 평가 baseline 보존 | operator ZIP/profile을 후보 checkout 밖에 보존, 복원 시 입력·평가 hash 재계산 | package 독립 복원 시험 |
| Codex hook | 전역 hook inventory 확인 후 비교 profile에서 `--disable hooks` | native `hooks=false`, 최종 조건의 모델 재검증 |

정책 검토는 운영자의 판단 기록이며 로그가 자동으로 준수를 입증하지 않는다. review digest는 변조 검사다.
기록 부족은 `unverified`, 위반은 `invalid_for_comparison`으로 품질 비교에서 제외하고 비용·사유를 남긴다.
과거 flag 없는 실행에는 새 gate를 소급 적용하지 않는다.
native command map과 지침도 OS 격리를 보장하지 않는다. AGY 공개 SDK view가 요청한 줄 범위보다
넓었던 사실과 native 비동기 도구 사용은 실제 로그에 남겼으며, 본 비교에서 별도 정책 검토한다.

## 동결과 후보 입력

새 baseline tag `comparison-baseline-20261004`는 `272875140d1998d458e26fdb2f6deab5e5d8f7b5`에 동결했다.
[freeze 기록](../../results/experiment-launch-preparation-20261004/freeze.json)에 5개 준비 ID·독립 ledger·receipt hash·후보 commit/tree·입력/평가 hash를 연결했다.
전체 회귀 220개 중 219개 통과·symlink 권한 제한 skip 1개·실패 0개다.
[독립 복원](../../results/experiment-launch-preparation-20261004/restore-audit.json)은 package 294개 파일·동결 source 949개와
5개 원본 후보 commit·57개 입력·receipt·ledger·operator baseline을 확인했다. 과거 `85ba108`과 tag·receipt·package는 변경하지 않았다.

후보 allowlist는 57개/필수 MD 3개다. E3 변경으로 이번 비교의
`experiments/config/agy-pilot-permissions.json` 1개에서 git log 허용 규칙을 제거했다.
나머지 56개 archive bytes가 이전 baseline과 같음을 [대조 기록](../../results/experiment-launch-preparation-20261004/baseline-input-review.json)으로 확인했고 활성 5개 모두 같은 새 입력을 받는다.
이 정정은 2026-10-03 계획의 “57개 모두 동일” 조건에만 적용한다. 제품 계약·fixture·공통 과제는 유지한다.

runner는 allowlist만 후보에 복사하고 운영·평가·과거 구현·결과를 제외한다.
`candidate-inputs.json`과 `.benchmark-inputs/` 사본을 실행 전후 검사한다.
후속 clone과 package 복원에서는 Git 줄바꿈 변환과 별개로 고정 입력의 원본 bytes를 보존한다.
새 제품 파일의 작성은 허용한다.

## 실제 시작과 평가 순서

첫 블록은 seed 1로 순서를 고정하고 5개의 개별 ID·ledger·새 receipt를 준비했다.
블록 2·3은 seed 2·3을 사용하며 실제 시작일에 새 ID를 생성한다. 각 모델/독립 반복의 ledger를 분리한다.
기본 순서는 series 실행→결과 동결→운영자 실물 관측→RM·정책 review→필요한 후속→다음 대상이다.
한 보드의 flash·serial·광학 관측은 하나씩 수행한다. provider 사용량과 보드 시간은 시작 직전에 확인한다.

최초 준비 시에는 COM1만 열거됐으나 2026-10-04 22:37 KST 재확인에서 COM3의
`USB VID_303A/PID_1001` 장치와 PnP 정상 상태를 확인했다.
[재연결 근거](../../results/experiment-launch-preparation-20261004/hardware-reconnected-20261004.json)에 기록했고
5개 prepared series의 날짜·상태·입력·receipt·ledger·CLI 버전도 재검증했다.
실물 평가 직전에 포트 재열거·점유 상태를 다시 확인한다. 이번 확인에서는 serial open이나 flash를 수행하지 않았다.
연결·수신·화면·BOOT·단절 복구를 실제 확인하기 전에는 `not_run`을 유지한다.
후보가 기능을 구현하지 못한 결과는 실패·미도달로 보존한다.

실행과 평가 명령은 [도구 안내](comparison-tooling.md)를 따른다. prepared 상태의 예약은 모델 실행이 아니다.
예약 ID는 해당 KST 날짜에만 유효하다. 다음 날에는 같은 동결 baseline에서 새 ID·ledger를 만들고
CLI/model/settings/environment를 재확인해 새 run-bound receipt를 연결한다.
2026-10-02 ID와 GPT-5.6 receipt는 이번 비교에 재사용하지 않는다.

현재 첫 블록 순서는 **OpenCode Muse→AGY Flash→AGY Pro→Codex Sol→Codex Luna**다.
준비 당시 5개 예약은 모두 prepared·시작 시각 null·소비 시간 null이었다.
첫 OpenCode 최초 실행은 completed(1,024.64초)이며 첫 후속은 timeout이다. AGY Flash 최초는 environment_failed(762.813초)로 종료됐고 평가·독립 복원을 마쳤다. 후속 1회차도 completed(1,489.219초)로 종료됐으며 최종 평가·독립 복원을 마쳤다. Flash 남은 후속은 보류하며 완료된 series로 집계하지 않는다. AGY Pro 최초(68.203초)·후속 1회차(81.625초)·후속 2회차(51.875초)·후속 3회차(475.797초)는 모두 environment_failed이고 최종 평가·보존을 마쳤다. Pro는 최대 후속 회차로 종료했다. Codex Sol/Luna는 미시작이다. 현재 후보 호출은 시작 8회·종료 8회, 완료한 독립 series는 OpenCode·Pro 2개/예정 15개다. 종료 code 0과 host 시험 통과 로그를 제품 합격으로 해석하지 않는다.
제출물은 `e14689fea0cee5c0bd1e3812f7bd5dfbd122d5db`에 동결했고, 정책 review는 `invalid_for_comparison`이다.
COM3의 원본 공통 frame 수신과 실제 성공 로그를 대조했고 사용자 사진에서 값 표시 부재를 확인했다.
최초 RM은 RM1 pass/RM2 partial/RM3 fail/RM4·RM5 not_run으로 기준 미도달이다. BOOT·연속 유지·정밀 지연은 미측정이다.
자신의 첫 동결 결과에서 후속 `20261004-opencode-cli-opencode-muse-r02`를 시작했고, 최초의 부적격·실패·비용은 보존한다.
2026-10-05 01:30:48 KST 후속 회차가 고정 한도로 종료됐다. 실제 7,200.156초를 기록해
후속 누적 7,200초 예산을 소진했으므로 추가 수정 회차는 시작할 수 없다. 최종 result JSON·선택 문서는 없다.
종료 후 남은 구현을 `354c6475345cb521c92f92e3dce448b0dc5ef58b`에 동결했고 정책은 부적격이다.
Python 28개·host 실행 파일 6개는 통과했지만 기준 시각의 실제 collector는 `STALE_THRESHOLD_EXCEEDED`로
legacy 입력을 거부한다. 같은 동결 artifact를 COM3에 업로드하고 seq 0·1 수락을 확인했다.
2026-10-05 02:50 KST 사용자 요청으로 같은 artifact를 다시 업로드하고 공통 seq 0·1 수락을 확인했다.
제공된 66.57초 영상은 재업로드 전에 저장된 자료다. 사용량 58%·세 종류 화면 전환을 관측했지만
주간 82%·실제 글로벌 리셋 값은 보이지 않는다.
사용자가 최초 후속 업로드 이후 촬영했음을 확인해 최종 RM review를 적용했다.
RM1·RM5 pass, RM2·RM3·RM4 partial이며 기준 미도달이다. 당시 [영상 검토 초안](../../results/formal-comparison-20261004/evidence/20261004-opencode-cli-opencode-muse-r02/operator-observation/user-video-01/video-review.json)과
[확인된 최종 검토](../../results/formal-comparison-20261004/review-finalization-20261005/confirmed-video-review.json)를 구분해 보존한다.
회차·예산을 초기화하거나 최종 제출물을 운영자가 대신 작성하지 않는다.
이번 전송은 operator replay다. 후보 collector의 공통 fixture 연결 문제와 미측정 광학 지연은 [실행 기록](../../results/formal-comparison-20261004/report.md)에 남긴다.
현재 증거 문서의 후속 commit과 비교 baseline을 혼동하지 않는다. 다음 날짜의 새 prepare는
동결된 깨끗한 operator checkout `C:/meter-operator-20261004`에서 수행한다.
당일 준비 도우미는 10월 4일의 실제 근거를 사용한 기록용이며 다음 날 그대로 실행해 현재 환경 확인을 대신하지 않는다.

2026-10-05 00:26 KST에 아직 시작하지 않은 AGY Flash/Pro·Codex Sol/Luna의 예약만 새 날짜로
갱신했다. [새 예약](../../results/formal-comparison-20261004/reservations-20261005/renewal.json)과
[현재 환경 확인](../../results/formal-comparison-20261004/reservations-20261005/current/current-checks.json)을 따른다.
갱신 중 모델/제품 구현 호출은 없었으며 당시 실행 중이던 OpenCode series·후속 예산은 변경하지 않았다.
이전 prepared 예약은 보존했고 동결 baseline/profile/입력도 같다. 실제 capability 원본은 10월 4일,
현재 CLI/SDK/native 설정·AGY 모델 목록과 전역 파일 복원 확인은 10월 5일의 별도 근거다.

```powershell
python -X utf8 -m unittest discover -s scripts/tests -v
python -X utf8 scripts/validate-end-to-end-result.py --matrix experiments/fixtures/provider-fixture-matrix.json
python -X utf8 scripts/benchmark.py check --baseline comparison-baseline-20261004 --profile experiments/config/next-profiles-20261003/codex-sol.json
```

`check`는 동결 입력을 검사하며 모델 호출이나 ID 예약을 수행하지 않는다.
첫 제품 terminal source·정책/RM·사진·계측 원본을 별도 archive에서 독립 복원했다.
동결 일반 포장 도구는 `firmware/build/`를 수집하지 못해 거부됐으며, 원본 보존 archive의 1,807개 파일·동결 tree·입력·정책·결과 검증 성공과 구분한다.
2026-10-05 종료 후 수집 도구의 경로 지원을 보완해 새 일반 package 348개 파일을 독립 복원했다.
동결 operator ZIP에서 추출한 validator로 57개 입력·artifact·정책·결과를 재검증했다.
원본 거부·원본 보존 archive·후보 부적격 판정은 유지한다. 동결 runner·입력·평가 기준은 변경하지 않았다.
적용 범위와 근거는 [보완 계획](../plans/2026-10-04-evidence-artifact-layout-remediation.md)과 [실행 기록](../../results/formal-comparison-20261004/report.md)을 따른다.

후속 timeout의 관측 전 보존본도 396개 파일·57개 입력·46개 source 사본·9개 artifact 사본을
동결 validator로 독립 복원 검증했다. 원본 terminal/ledger는 바꾸지 않았고 파생 포장 manifest의
변경 필드는 동결 commit·추가 evidence뿐이다. 최종 제출 누락으로 `result_valid: false`이며
이 보존 검증을 제품 합격이나 최종 RM review 완료로 해석하지 않는다.
[복구 계획](../plans/2026-10-05-timeout-evidence-recovery.md)과 [복원 감사](../../results/formal-comparison-20261004/timeout-preservation-20261005/restore-audit.json)를 따른다.

영상 확인·최종 RM 판정을 포함한 최종 package 430개 파일도 새 경로에서 독립 복원하고 동결 validator로 재검증했다.
[최종 복원](../../results/formal-comparison-20261004/review-finalization-20261005/restore-audit.json)은 제출 누락과
`result_valid: false`·정책 부적격·기준 미도달을 유지한다. [종료 기록](../../results/formal-comparison-20261004/review-finalization-20261005/series-completion.json)의
derived state는 budget_exhausted다. 동결 도구의 ledger가 fail review 뒤 active를 유지하지만 prepare-next의 예산 guard가 추가 실행을 거부한다.
다음 AGY Flash는 현재 환경·native 설정·모델 ID·receipt를 재확인해 시작했고 [launch](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r01/launch-20261005/experiment-launch-attempt2.json)를 보존했다.
모델 호출 전 런처의 CLI 인자 오류 1건은 준비 오류로 구분하며 후보 비용·회차를 초기화한 일이 아니다.

2026-10-05 AGY 종료 후 적용 범위: 현재 AGY Flash 최초 실행의 평가 상태만 갱신한다.
마지막 native `Test-Path build-host/test_meter_parser.exe, build-host/link_evidence.txt`가 거부됐으며
이후 도구 이벤트 없이 종료했다. [정책 review](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r01/terminal-20261005/policy-review.json)는 eligible이고 environment_failed·최종 JSON 누락은 별도로 유지한다.
구현 `29e1d7af54a8c9c879e36192ec4ed689e5bbf82d`와 app SHA-256
`f29c45ff3a570fbc1d2b92aee6ad224f985f1c951821479ca0d901201c3f9c41`를 동결했다.
Python 5개·C 실행 파일 4개는 통과했지만 실제 collector payload는 공통 기준과 다르다.
업로드는 hash 검증까지 성공했다. [capture](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r01/terminal-20261005/operator-observation/reference-capture-r1/capture.json)는 seq 0 write timeout·수신 로그 0 bytes이며 seq 1은 시도하지 않았다.
사용자가 해당 펌웨어의 48.12초 영상을 제공해 촬영 대상을 확인했다. 대시보드는 WAITING FOR USB DATA,
글로벌 화면은 NO RECENT RESET RECORD, 진단은 Sequence NONE·cache 0이다. 화면 순환은 보이지만
정상 fixture 수신·실제 사용량 탐색과 개별 BOOT/IMU trigger·연속 30초 무깜박임은 입증되지 않았다.
[최종 RM](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r01/evaluation-final-20261005/reference-review.json)은 RM1 pass/RM2 partial/RM3 fail/RM4 partial/RM5 partial, 기준 미도달이다.
[독립 복원](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r01/evaluation-final-20261005/restore-audit.json)은 430개 파일·57개 입력·38개 source·10개 artifact/설정 원본·영상과 비용을 package의 동결 validator로 검증했다.
원본 terminal/ledger·시작/종료 snapshot·제출 누락은 유지했다. 최초 실행을 다시 시작하지 않으며 후속 준비·현재 실행은 [현재 계측](../../results/formal-comparison-20261004/progress.json)을 따른다.

AGY 후속 `20261005-antigravity-cli-agy-flash-r02`는 별도 checkout에서 자기 동결 source만 이어간다.
[시작 관측](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r02/launch-20261005/native-start-observation.json)에서
동일 모델·request-review·새 cwd를 확인했다. 같은 profile·공통 입력·거부 시 종료 규칙을 유지하고,
자기 관측·기대·hash 근거만 전달했다. 후속 누적 7,200초·최대 3회 한도에 이번 회차를 포함한다.
2026-10-05 04:59:40.678 KST 후속이 종료됐다. [종료 확인](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r02/terminal-status-20261005/terminal-status.json)은
1,489.219초·정규화 token 1,612,964·177 tool calls와 제출물 존재, 전역 설정/지침/hook 원본 복원을 확인했다.
Python 6개와 결과 validator 통과는 후보 로그의 관측이며 아직 운영자 독립 검증이 아니다.
최종 `build-host/CTestTestfile.cmake`가 r01 실행 파일 4개를 가리킨다. r02 CTest 통과를 r02 코드 검증에 사용하지 않는다.
이전 checkout의 `.ninja_log` 변경은 기록했고 최초 펌웨어/설정 10개 원본 hash는 그대로다. 최초 raw snapshot·bundle·독립 package를 보존한다.
후속 terminal manifest/ledger·41개 source·10개 artifact/설정을 보존했으며 후보 코드 수정·재빌드·보드 접근은 하지 않았다.
후속 누적 잔여 시간은 5,710.781초, 잔여 회차는 2회이나 다음 실행 판단은 현재 회차의 동결·정책/빌드 근거 검토·실물/RM 평가 이후다.
위 04:59 종료 확인 시점의 pending 기록은 원본으로 보존한다. 2026-10-05 후속 평가의 현재 상태는 다음과 같다.

- [평가 계획](../plans/2026-10-05-agy-flash-followup-evaluation.md)에 따라 구현을 `94018f1785a590e1514ef1b5145c40f0c03ffca3`으로 동결했다. app SHA-256은 `3fe7cc55c2a0af238b869cc635571ce38584145f206e97f47154fb81637ed467`이다.
- [정책 review](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-stage-20261005/policy-review.json)는 invalid_for_comparison이다. 이전 회차 실행 파일과 checkout을 실제 사용했으며, 추적된 build 출력의 절대 경로가 후속 clone에 승계된 운영 도구 기여도 함께 기록했다. 누락 파일 오류 3건을 권한 거부로 잘못 분류하지 않는다.
- [독립 host 검증](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-stage-20261005/operator-observation/host-checks.json)은 제출 JSON·Python 6개·별도 새 host build의 C 시험 4개를 통과했다. 원래 CTest 기록의 잘못된 경로를 수정하거나 정식 비교 적격성을 복구한 것이 아니다.
- 실제 default/legacy collector는 공통 payload와 다르다. legacy는 58%/82%를 만들지만 identity·stale/error/reset 의미가 다르며 encoder-only wire 일치와 구분한다.
- [업로드 슬롯](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-stage-20261005/operator-observation/hardware-slot.json)은 05:38:52.012 KST 업로드 완료다. 원본 app/bootloader/partition을 사용했고 firmware를 운영자가 재빌드하지 않았다.
- [capture](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-stage-20261005/operator-observation/reference-capture-r1/capture.json)는 seq 0·1 각각 1,543 bytes_written이다. [실제 오류](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-stage-20261005/operator-observation/panic-source-review.json)는 LoadProhibited panic·재부팅 2회와 수락 로그 0건이다. PC 쓰기 완료를 성공 수신이나 화면 표시로 해석하지 않는다.

위 업로드 시점에는 사용자 영상과 최종 평가가 남아 있었다. 다음 기록은 2026-10-05 사용자가 제공한 이번 후속 영상과 대기 지시에만 적용한다.

- `KakaoTalk_20261005_054708010.mp4`의 원본 46.3초·22,018,701 bytes와 SHA-256 `e759b25d693b0d4774e463bfcb60b9b71c9a5b6f067945770ccf5d8c6bc3672b`를 보존했다. [영상 검토](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-final-20261005/operator-observation/user-video-01/video-review.json)에서 세 종류 화면 순환과 대시보드 복귀를 확인했지만 WAITING FOR USB DATA·NO RECENT RESET RECORD·Sequence NONE/cache 0이 남아 있다. 사용량 58%/82%와 실제 리셋 값은 보이지 않는다.
- 영상의 Uptime은 421초에서 3초로 바뀌지만 보드가 가려진 구간과 조작이 있어 재시작 원인은 미확정이다. 개별 BOOT/IMU trigger, 연속 30초 무깜박임과 정밀 지연을 합격 처리하지 않는다. 업로드 직후 serial의 panic 2회와 영상 관측을 구분한다.
- [최종 RM](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-final-20261005/reference-review.json)은 한 번 적용했으며 RM1 pass/RM2 partial/RM3 fail/RM4 partial/RM5 partial, reference fail/product_pass false다. 이전 회차 접근의 정책 부적격과 원본 비용은 그대로다.
- [최종 독립 복원](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-final-20261005/restore-audit.json)은 package 501개 파일·57개 입력·41개 raw source·10개 artifact/설정 원본·영상·최종 판정·비용·대기 지시를 package의 동결 operator ZIP으로 검증했다. `result_valid: true`는 제출 형식과 증거의 검증이며 제품 합격이 아니다. 최종 package manifest SHA-256은 `b0e2880fc7c786ae338b9d1870ccd4c3510bf9afb3f5881089ff4d23515f244c`다.

**사용자 재개 지시를 기다린다.** [대기 원본](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-flash-r02/evaluation-final-20261005/operator-user-hold.json)에 따라 추가 AGY 회차와 다음 모델을 시작하지 않는다. 현재 후속 원본 펌웨어를 유지하고 serial은 닫았다. 같은 회차 재호출·예산 초기화 없이 후속 잔여 5,710.781초·2회를 보존한다. 전체 비교는 사용자 요청으로 보류이며 현재 회차 평가 완료와 전체 series 완료를 구분한다.

위 대기는 당시 원본이다. 2026-10-05 사용자의 “다음 모델 ㄱㄱ”는 다음 AGY Pro 진행을 재개한다.
[전환 기록](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r01/evaluation-final-20261005/operator-next-model-decision.json)에 적용 범위를 남겼으며 Flash의 추가 회차는 보류한다. 기존 대기 파일·판정·비용·package를 수정하지 않는다.

- Pro의 [최초 평가](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r01/evaluation-final-20261005/operator-observation/terminal-verification.json)는 22:15:28.585~22:16:36.793 KST, 68.203초·정규화 89,861 token이다. 첫 `mkdir -p firmware/main pc firmware/components/state_machine scripts tests`가 거부돼 즉시 종료했다. 실제 native model/cwd/request-review를 확인했으며 다른 후보 구현 접근·실행 중 구현 피드백은 없다.
- [정책 review](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r01/evaluation-final-20261005/policy-review.json)는 eligible이다. [최종 RM](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r01/evaluation-final-20261005/reference-review.json)은 RM1 fail/RM2~RM5 not_run이며 코드·펌웨어·선택 문서·최종 JSON이 없다. Pro 업로드나 관측을 하지 않았고 기존 Flash 화면을 Pro 근거로 쓰지 않는다.
- [독립 복원](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r01/evaluation-final-20261005/restore-audit.json)은 338개 파일·57개 입력·raw terminal/비용·정책/RM·동결 source를 package의 동결 validator로 검증했다. 제출 누락으로 `result_valid: false`다. 보관 사본의 evidence 등록 누락을 보완한 [운영 정정](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r01/evaluation-final-20261005/operator-package-coverage-correction.json)은 최초 315개 archive와 복원 감사 오류를 보존하며 제품·권한·후보 비용을 바꾸지 않는다.
- [후속 시작](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r02/launch-20261005/native-start-observation.json)은 22:29:17.275 KST다. [후속 계획](../plans/2026-10-05-agy-pro-followup-execution.md)에 따라 별도 checkout에서 자기 직전 commit `ba5609db6fbf6392166586e50341c6e14a26112f`와 고정 관측만 전달했다. 이전 회차의 build cache는 없으며 같은 profile·57개 입력·native 권한·거부 시 종료 규칙을 유지한다. 현재 회차를 후속 최대 3회/누적 7,200초에 포함하며 최종 실제 경과 시간으로 차감한다.

현재 보드는 Flash 후속 원본 그대로이고 serial은 닫았다. Pro가 종료한 뒤 source와 비용을 동결하고 제출물·정책·host·실물/RM를 검토한다. 실행 중 회차를 다시 호출하거나 Codex를 함께 시작하지 않는다. 실행·재개 상태는 [현재 계측](../../results/formal-comparison-20261004/progress.json)을 먼저 확인한다.

2026-10-05 남은 Pro 후속의 현재 갱신: 위 후속 1회차 시작 시점의 pending은 당시 기록이다.
[후속 1회차 최종 복원](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r02/evaluation-final-20261005/restore-audit.json)은 346개 파일·57개 입력·원본 비용·partial CMakeLists와 동결 Git blob을 검증했다. 종료는 22:30:38.899 KST이며 native Copy-Item 거부 후 행동을 멈췄다. Raw LF와 Git 복원 CRLF의 차이는 동일한 내용·Git blob으로 검증했고 최초 audit 오류는 보존했다.
[후속 2회차 최종 복원](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r03/evaluation-final-20261005/restore-audit.json)은 349개 파일·57개 입력·partial source 2개·원본 비용을 검증했다. 종료는 22:46:39.732 KST이며 native Get-ChildItem 거부 후 멈췄다. 두 회차 모두 정책 eligible·RM1 fail/RM2~RM5 not_run, `result_valid: false`이며 펌웨어·최종 제출물이 없다.
[남은 후속 계획](../plans/2026-10-05-agy-pro-remaining-followups.md)에 따라 마지막 r04를 새 receipt·별도 checkout에서 자기 직전 commit `8059dbf481d7a394a985d8757b0b331fc625b40a`와 고정 근거만 이어갔다.
[실제 시작](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r04/launch-20261005/native-start-observation.json)은 22:50:11.286 KST, 동일 Pro model/cwd/request-review다. 실행 전 잔여 7,066.5초·1회에서 timeout 7,066초를 적용한다. 이 회차 종료 뒤에는 후속 최대 3회에 도달하므로 시간을 남겨도 추가 회차를 생성하지 않는다. 아직 이 회차의 terminal 비용·정책/RM는 미판정이다.

2026-10-05 Pro 종료 갱신: 위 r04 시작 시점의 pending은 당시 기록이다. 마지막 r04는 22:58:07.087 KST에
`Get-FileHash -Algorithm SHA256 <자기 source 3개>`의 native 거부로 종료했으며 그 뒤 도구/assistant 행동은 없다.
475.797초·정규화 405,997 token, partial source 7개와 PC executable을 보존했다. Firmware app/ELF는 없다.
[최종 독립 복원](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r04/evaluation-final-20261005/restore-audit.json)은 361개 파일·57개 입력·raw source/host artifact·Git·비용·정책/RM를 package의 동결 validator로 검증했다. `result_valid: false`·정책 eligible·RM1 fail/RM2~RM5 not_run을 유지한다.
[별도 host 검증](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r04/evaluation-final-20261005/post-package-host-runtime-check.json)은 독립 복원본의 같은 executable과 기록된 compiler DLL 경로로 29개 중 12 pass/17 fail이다. 최초 운영자 PATH의 DLL loader 오류 29건을 보존하며 이를 의미 검사 실패로 집계하지 않는다. 이 검증은 partial C state와 mock normalizer이며 실제 firmware·collector·device 합격을 뜻하지 않는다.
[Series 종료](../../results/formal-comparison-20261004/evidence/20261005-antigravity-cli-agy-pro-r04/evaluation-final-20261005/operator-series-completion.json)는 `remediation_round_limit_reached`다. 후속 누적 609.297초·잔여 6,590.703초지만 잔여 회차 0으로 추가 실행은 없다. Native scope/owner는 복원·해제됐다. Pro 업로드를 하지 않아 보드는 기존 Flash 원본으로 기록하며 다음 Codex Sol/Luna는 아직 시작하지 않았다.
총 677.5초·정규화 660,989 token은 [비용 checkpoint 07](../../results/formal-comparison-20261004/comparison-checkpoint-07.md)에 모든 실패와 함께 남긴다. 환경 실패를 모델의 일반 코딩 품질 순위로 해석하지 않는다. 전체 비교는 15개 독립 series 중 2개 종료이며 미완료다.

2026-10-05 다음 모델 갱신: 사용자의 “그럼 다음 모델로 넘어가자”에 따라 [Codex Sol 계획](../plans/2026-10-05-codex-sol-initial-launch.md)으로 진행했다.
`20261005-codex-cli-gpt-6-sol-r01`의 [시작 snapshot](../../results/formal-comparison-20261004/evidence/20261005-codex-cli-gpt-6-sol-r01/launch-20261005/snapshot-inventory.json)은 22개 파일의 원본 bytes/hash를 보존한다.
동결 profile·CLI 0.159.2·ESP-IDF 5.3.2·공통 입력·native feature/skill inventory를 재확인했으며 준비 중 모델 호출은 0회다.
실제 최초 시작은 23:56:01.520 KST, launcher PID 10236·candidate PID 22140·thread `01a10c90-8a40-7f00-98e5-d8627a20ba62`다.
실제 process argv는 explicit `-m gpt-6-sol`·medium·동결 권한/확장 비활성화와 일치한다. Codex JSONL은 resolved model/cwd를 방출하지 않으므로 별도 native 확인으로 추정하지 않는다. Native inventory도 exec의 ignore-user-config와 설정 계층이 다르다는 범위를 유지한다.
최초 7,200초의 독립 runner가 실행 중이며 종료 후 source·제출·원본 비용을 동결하고 정책·host·제품/RM를 검토한다. Genuine ESP32 firmware가 있어야 COM3 업로드·실물 평가로 이어간다. 후보 실행 중 구현 피드백·source 수정·serial/flash는 없다.
현재 제품·정책·RM 판정은 pending이며 앞선 Pro/Flash 결과를 Sol 결과로 쓰지 않는다. 재개할 때 [현재 계측](../../results/formal-comparison-20261004/progress.json)·개별 manifest/ledger·실제 process부터 확인하고 같은 최초 호출을 반복하지 않는다.

2026-10-06 최초 종료·평가 갱신: 위 시작 시점의 pending은 당시 기록이다.
[평가 계획](../plans/2026-10-06-codex-sol-initial-evaluation.md)에 따라 completed·2,460.156초·원본 계측을 보존했다.
정책 eligible이며 자체 host 시험 통과와 공통 collector/host/device의 SCHEMA_INVALID 실패를 구분한다.
같은 동결 app을 00:57:03 KST에 COM3에 올렸고 공통 seq 0/1 수락은 0건이다.
12.9초 영상은 글자·숫자 없이 색 띠가 나타나며 사용자는 BOOT 짧게 3회·길게 누르기에도 무반응이라고 확인했다.
[최초 RM](../../results/formal-comparison-20261004/evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/reference-review.json)은 RM1 pass/RM2~RM5 fail·reference fail/product_pass false다.
30초 연속 유지와 정밀 지연은 미측정이다.

[최종 독립 감사](../../results/formal-comparison-20261004/evidence/20261005-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/restore-audit.json)는
453개 파일·57개 입력·source 22개·artifact/config 21개·원본 비용·영상·판정을 검증했다.
Commit `2257fffaa5316773d08fe3353356112c7002159d`, package manifest SHA-256 `93a87074e0f324da7c95e237244870d0a8deebc6be4f3e89b52fb95095acb60e`다.
제출 형식 `result_valid: true`와 제품 합격은 다르다. Input 11,987,074에는 cached 11,815,680이 포함되며 output 54,062를 합친
정규화 12,041,136을 모두 uncached 소비나 provider 간 금전 순위로 해석하지 않는다.

2026-10-06 운영 정정은 최초 원본을 보존한다. Manifest experiment branch label과 실제 별도 저장소 local branch master를 구분한다.
이전 operator 감사의 경로 remap/조기 검사 오류를 원본·보완 sidecar로 남겼고 후보 source·비용·실행을 바꾸지 않았다.
동결 commit에 생성된 build/build-host 출력 1,413개가 추적돼 있어 새 후속 준비 사본에서만 제거하고 source 동일성을 검증해야 한다.
후속은 0회·잔여 7,200초·3회이며 현재 보드는 Sol 최초다. User keep going에 따라 해당 series를 계속한다.
Pro 회차 한도·Flash 잔여 5,710.781초/2회 보류·기존 결과는 보존하고 Codex Luna는 아직 시작하지 않는다.

2026-10-06 후속 1회차 시작 갱신: [후속 계획](../plans/2026-10-06-codex-sol-followup-execution.md)의
`20261006-codex-cli-gpt-6-sol-r01`은 ledger round 1이다. 날짜 뒤 r01은 당일 예약 번호이며 새로운 최초 호출이 아니다.
자기 최초 commit `2257fffaa5316773d08fe3353356112c7002159d`와 관측 6개만 전달했다.
[새 사본 보완](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r01/launch-20261006/operator-generated-output-cleanup.json)은
build/build-host 출력 1,413개만 제외하고 제품 source 18개의 Git blob·내용/입력 동일성을 증명한다.
Local Git exclude만 보완했고 원본 freeze/package·공통 입력·권한·global 설정은 바꾸지 않았다.
[실제 시작](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r01/launch-20261006/native-start-observation.json)은
03:34:01.746 KST, thread `01a10d58-20e1-7eb2-93f7-97fb84a5eb89`와 explicit gpt-6-sol/medium의 process argv를 확인한다.
같은 CLI/SDK/native inventory를 재확인했고 receipt SHA-256은 `16c93563e8187b59c6488c00a33209adbd38ebc8e26448e73067bb2cb6007132`다.
이번 예약은 최대 7,200초이며 최종 실제 시간으로 후속 누적 예산을 차감한다. 남은 추가 회차는 2회지만 현재 회차 종료·평가 전에는 시작하지 않는다.
후속 구현 중 피드백·serial/flash는 없고 최초 보드를 후속 성공 근거로 쓰지 않는다. 재개 시 현재 manifest/ledger/process를 먼저 확인한다.

## 2026-10-06 Sol 후속 1회차 완료와 정책 정정

[최종 RM](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/reference-review.json)은
RM1 pass/RM2 partial/RM3~RM5 fail, reference fail/product_pass false다. 종료는 03:41:31.431 KST, 449.687초·정규화 3,862,124 token이다.
03:50 KST 같은 동결 artifact 업로드 후 실제 frame 0·1 수락을 확인했다. [사진 관측](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/operator-observation/user-photo-01/photo-review.json)은
값·정보·버튼 탐색 부재를 확인한다. 사용자 RESET은 수동 재부팅이며 30초 유지·자동 재부팅은 미검증이다.
[독립 감사](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r01/evaluation-final-20261006/restore-audit.json)는 459개 파일·source22/artifact21·입력57·원본 비용을 검증했다.

적용 범위가 최초와 Sol series의 동일 조건 품질·reference-cost 집계인 [정책 정정](../../results/formal-comparison-20261004/evidence/20261005-codex-cli-gpt-6-sol-r01/policy-correction-20261006/correction-note.json)은
최초 원본 eligible·commit/package·RM·비용을 보존하고 현재 적격성만 invalid_for_comparison으로 정정한다.
기존 공통 과제가 금지한 shell pipeline을 최초 7건·후속 4건 확인했다. 최초 운영자 검토에서 이 항목을 놓쳤다.
정책 부적격이어도 실패 비용과 제품 관측은 남긴다. [비용 checkpoint09](../../results/formal-comparison-20261004/comparison-checkpoint-09.md)는
checkpoint08의 원본을 보존한 후속 집계다. [남은 후속 계획](../plans/2026-10-06-codex-sol-remaining-followups.md)에 따라 잔여 6,750.313초·2회 안에서 자신의 직전 결과만 이어간다.

## 2026-10-06 Sol 후속 2회차 실제 시작

[시작 snapshot](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r02/launch-20261006/snapshot-inventory.json)은 run `20261006-codex-cli-gpt-6-sol-r02`/round2,
04:08:53.442 KST 시작·thread `01a10d78-0ba5-7ff3-8dd5-260f62b6ea53`·같은 explicit gpt-6-sol/medium actual argv·새 receipt를 보존한다.
새 사본에서 생성 bytecode3개만 제외하고 제품 source18개의 Git blob/내용·고정 입력57개·profile 동일성을 검증했다. 새 prepared commit은 `e2a741d6360304c8d5e1542bc4444fc9a0fac2da`다.
이번 최대6,750초·현재 호출 후 추가 최대1회이며 실제 시간은 종료 후 차감한다. 현재 회차의 제품·비용·RM는 pending이고 series 품질 invalid는 유지한다.
현재 보드는 후속1 artifact이며 현재 후속2 성공 근거로 사용하지 않는다. 이전 두 회차를 재실행하거나 실행 중 구현 피드백·serial/flash를 제공하지 않는다.

## 2026-10-06 Sol 후속 2회차 제출·업로드 완료, 광학 대기

위 시작 이후 후속2가 04:19:16.016 KST 종료됐고 [관측 대기 snapshot](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r02/post-terminal-awaiting-optical-20261006/snapshot-inventory.json)에
원본 비용·정책·동결 source·host 시험·업로드/수신 근거76개 파일을 보존했다. [독립 복원](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r02/post-terminal-awaiting-optical-20261006/restore-audit.json)은
418개 파일과 source22/artifact21·고정 입력57·실행 원본을 검증했다. Commit `09ecdaf1645511033b4efda40bb2a9e3b96ae8f7`, app SHA-256 `486cd84ba91af26fd86ea8642c166c4708b7e3537806cf18f93d9579c23c0377`다.
실제 보드는 후속2로 바뀌었으며 04:21:15 KST 업로드 후 공통 frame0·1을 수락했다. 이전 사진·RESET 보고를 새 artifact 판정으로 재사용하지 않는다.
새 LCD/BOOT/연속 유지 관측을 요청했으며 RM review는 아직 적용하지 않았다. 구현·제출 완료와 평가 완료는 다르다.
[Checkpoint10](../../results/formal-comparison-20261004/comparison-checkpoint-10.md)은 후보11회·정규화26,689,957 token을 기록한다. Sol 누적3,532.405초·22,413,413 token과
후속 잔여6,127.751초·1회를 유지하고 관측/정식 평가 전 추가 호출을 시작하지 않는다. 전체 비교·제품 합격·Sol series 종료를 선언하지 않는다.

## 2026-10-06 Sol 후속 2회차 평가 완료·series 종료

위 광학 대기는 당시 기록이다. 새63.3초 영상과 사용자의 “RESET(RST)을 직접 누름” 확인을 이번04:21 업로드 artifact에 연결했다.
[최종 RM](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r02/evaluation-final-20261006/reference-review.json)은 RM1~RM5 pass다.
5시간 남은58%·주간 남은82%, 실제 글로벌 리셋·진단 정보와 BOOT로 세 화면 순환·복귀를 확인했다.
약18초의 데이터 소실은 수동 RESET 이후이며 자동 재부팅으로 판정하지 않는다. 이후20.5~30.5초 표본에는 읽을 수 있는 글자가 없고 원인은 미확정이다.
30초 연속 정상 데이터 표시·정밀 지연·전체29개 oracle·정식 GUI/선택 기능 검증은 미완료이므로 product_pass false를 유지한다.
[최종 독립 감사](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r02/evaluation-final-20261006/restore-audit.json)는483개 파일·입력57개·source22/artifact21·원본 비용·정책·영상·RM를 검증했다.
Package SHA-256은 `a72afc82d487005b05a403940419a5f0bdabcf0e1e79b4953d7eb56784b29a82`다. 재빌드·후보 재호출·추가 업로드 없이 검증했다.
[종료 기록](../../results/formal-comparison-20261004/evidence/20261006-codex-cli-gpt-6-sol-r02/evaluation-final-20261006/operator-series-completion.json)은 ledger reached이며 추가 후속을 허용하지 않는다.
[Checkpoint11](../../results/formal-comparison-20261004/comparison-checkpoint-11.md)은 실제11회 비용과 Sol 관측 도달 누적3,532.405초·22,413,413 token을 보존한다. 이는 정책 적격 도달 비용이 아니다.
Sol series 품질 invalid·최초 날짜 있는 정정·과거 원본 판정을 유지한다. 독립 series 종료3/15로 전체 비교는 미완료이며 Codex Luna는 시작하지 않았다.
